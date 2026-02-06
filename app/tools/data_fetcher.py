import requests
import json
from datetime import datetime
from app.config.config import (
    RTE_API_URL, RTE_DATASET, API_QUOTA_LIMIT, API_CALLS_TRACKING, CRITICAL_FIELDS
)
from app.database.database import EnergyDatabase

class RTEDataFetcher:
    def __init__(self):
        self.db = EnergyDatabase()
        self.calls_log = self._load_calls_log()
    
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
    
    def _check_quota_warning(self):
        """Warn at 80% quota usage (before hitting hard limit)"""
        used = self.calls_log["count"]
        if used > API_QUOTA_LIMIT * 0.8:
            days_left = 30 - datetime.now().day
            daily_budget = (API_QUOTA_LIMIT - used) / max(days_left, 1)
            print(f"⚠️ QUOTA WARNING: {used}/{API_QUOTA_LIMIT} calls used ({used/API_QUOTA_LIMIT:.0%})")
            print(f"   → Reduce fetch frequency to {max(20, int(1440/daily_budget))} min to avoid lockout")

    def fetch_latest(self):
        """Fetch with FULL timestamp preservation"""
        if not self._within_quota():
            print("⚠️ API quota exhausted - using cached data only")
            return False
        
        params = {
            "dataset": RTE_DATASET,
            "rows": 100,
            "sort": "-date_heure",
            "timezone": "Europe/Paris"
        }
        
        try:
            response = requests.get(RTE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            self.calls_log["count"] += 1
            self._save_calls_log()
            records = response.json()["records"]
            # CRITICAL: Skip storage if API returns empty/malformed data
            if not records or len(records) < 10:  # <10 = likely error
                print(f"⚠️ Skipping fetch: API returned {len(records)} records (expected >10)")
                print(f"   Response keys: {list(records.keys())}")
                return False  # Preserve existing cache instead of overwriting with junk
            
            
            processed = []
            for r in records:
                fields = r["fields"]
                # CRITICAL FIX: Preserve FULL timestamp with timezone
                raw_ts = fields.get("date_heure", "").strip()
                if not raw_ts:
                    continue
                
                # Keep ONLY critical fields + FULL timestamp
                record = {"date_heure": raw_ts}
                for field in CRITICAL_FIELDS[1:]:  # Skip date_heure already set
                    record[field] = fields.get(field)
                processed.append(record)
            
            self.db.store_records(processed)
            print(f"✓ Fetched {len(processed)} records at {datetime.now():%H:%M:%S}")
            self.db.debug_print_latest()  # Verify storage worked
            return True
            
        except Exception as e:
            print(f"✗ API fetch failed: {e}")
            import traceback; traceback.print_exc()
            return False