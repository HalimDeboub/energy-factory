import requests
import json
from datetime import datetime, timedelta
import pytz
from app.config.config import (
    RTE_API_URL_V2,
    API_QUOTA_LIMIT,
    API_CALLS_TRACKING,
    TIMEZONE,
    CRITICAL_FIELDS
)
from app.database.database import EnergyDatabase

class RTEDataFetcher:
    def __init__(self):
        self.db = EnergyDatabase()
        self.calls_log = self._load_calls_log()
        self.tz = pytz.timezone(TIMEZONE)
    
    def _load_calls_log(self):
        if API_CALLS_TRACKING.exists():
            return json.loads(API_CALLS_TRACKING.read_text())
        return {"month": datetime.now().month, "count": 0}
    
    def _save_calls_log(self):
        API_CALLS_TRACKING.write_text(json.dumps(self.calls_log))
    
    def _within_quota(self):
        now = datetime.now()
        if now.month != self.calls_log["month"]:
            self.calls_log = {"month": now.month, "count": 0}
            self._save_calls_log()
        return self.calls_log["count"] < API_QUOTA_LIMIT
    
    def fetch_latest(self):
        if not self._within_quota():
            print("⚠️ API quota exhausted - using cached data only")
            return False

        # 🔑 CRITICAL: Use UTC timestamps WITH SINGLE QUOTES (ODSQL requirement)
        now = datetime.now(self.tz)

        # ✅ ALWAYS FETCH LAST 10 DAYS
        cutoff = now - timedelta(days=10)

        # Convert to UTC for filtering (API expects UTC in WHERE clause)
        cutoff_utc = cutoff.astimezone(pytz.UTC)

        # ✅ CORRECT ODSQL SYNTAX: Single quotes around timestamp, UTC with Z
        # Example: date_heure >= '2026-02-02T15:34:40Z'
        where_clause = (
            f"date_heure >= '{cutoff_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}'"
        )

        params = {
            "limit": 100,  # ~240 hourly records for 10 days → safe margin
            "order_by": "date_heure asc",
            "where": where_clause
        }

        try:
            print(f"📡 Fetching data since {cutoff.strftime('%Y-%m-%d %H:%M')} Paris time...")
            response = requests.get(RTE_API_URL_V2, params=params, timeout=15)
            response.raise_for_status()

            self.calls_log["count"] += 1
            self._save_calls_log()

            records = response.json().get("results", [])
            if not records:
                print("❌ API returned 0 records")
                return False

            # 🔍 DEBUG: Show actual timestamps from API
            newest = records[0].get("date_heure", "")
            oldest = records[-1].get("date_heure", "")
            print(
                f"✅ API returned {len(records)} records | "
                f"Range: {oldest[:19]} → {newest[:19]}"
            )

            # =========================
            # PROCESSING & VALIDATION
            # =========================
            processed = []
            skipped_none = 0
            skipped_too_recent = 0

            # Only store ≥4h old measurements (real data, not forecasts)
            measurement_ready_cutoff = now - timedelta(hours=4)

            for r in records:
                raw_ts = r.get("date_heure", "").strip()
                if not raw_ts or ('+' not in raw_ts and not raw_ts.endswith('Z')):
                    continue

                # Parse timestamp
                try:
                    record_time = datetime.fromisoformat(
                        raw_ts.replace('Z', '+00:00')
                    ).astimezone(self.tz)
                except Exception:
                    continue

                # ✅ FILTER 1: Skip too-recent records (<4h)
                if record_time > measurement_ready_cutoff:
                    skipped_too_recent += 1
                    continue

                # ✅ FILTER 2: Skip records missing critical values
                consommation = r.get("consommation")
                nucleaire = r.get("nucleaire")
                if consommation is None or nucleaire is None:
                    skipped_none += 1
                    continue

                # Build clean record (flat structure in v2.1)
                record = {"date_heure": raw_ts}
                for field in CRITICAL_FIELDS[1:]:
                    record[field] = r.get(field)

                processed.append(record)

            # =========================
            # STORE RESULTS
            # =========================
            stored_count = self.db.store_records(processed)
            total_count = self.db.get_record_count()

            print(
                f"💾 Stored {stored_count} valid records | "
                f"Skipped: {skipped_too_recent} (too recent) + "
                f"{skipped_none} (incomplete) | "
                f"DB total: {total_count}"
            )

            # Show latest stored record
            latest = self.db.get_latest_record()
            if latest and latest.get("consommation"):
                print(
                    f"✅ Latest valid record: {latest['date_heure']} | "
                    f"Conso: {latest['consommation']} MW"
                )
            else:
                print("⚠️ No valid records stored (all were forecasts/incomplete)")

            return stored_count > 0

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP {e.response.status_code} error")
            print(f"   URL: {e.request.url}")
            print(f"   Response: {e.response.text[:300]}")
            print(f"   Where clause used: {where_clause}")
            return False

        except Exception as e:
            print(f"✗ API fetch failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False