# app/providers/data/dynamic_api_provider.py
#
# ═══════════════════════════════════════════════════════════════════════════
# DYNAMIC API PROVIDER — No-Code Adapter
# ═══════════════════════════════════════════════════════════════════════════

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz
import requests
from app.core.base import BaseDataProvider
from app.config.sources import CONFIG_PATH
from app.config.config import TIMEZONE
from app.database.database import EnergyDatabase


class DynamicAPIProvider(BaseDataProvider):
    """
    A provider that instantiates multiple data sources based on a JSON config.
    Allows non-tech users to add sources via a UI.
    """

    def __init__(self, source_id: str = None):
        self.db = EnergyDatabase()
        self.tz = pytz.timezone(TIMEZONE)
        self._sources = self._load_config()
        self._active_source = None
        
        if source_id:
            self._active_source = next((s for s in self._sources if s['id'] == source_id), None)

    def _load_config(self) -> List[Dict]:
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return data.get("data_sources", [])
        except Exception as e:
            print(f" [DynamicAPI] Could not load config: {e}")
            return []

    @property
    def provider_name(self) -> str:
        return self._active_source['name'] if self._active_source else "Dynamic API Manager"

    @property
    def company_id(self) -> str:
        return self._active_source.get('company_id', 'system_global') if self._active_source else 'system_global'

    @property
    def supported_topics(self) -> List[str]:
        return self._active_source.get('metrics', []) if self._active_source else []

    @property
    def is_persistent(self) -> bool:
        return self._active_source.get('persist_data', False) if self._active_source else False

    def get_schema_mapping(self) -> Dict[str, str]:
        return self._active_source.get('field_mapping', {}) if self._active_source else {}

    def get_latest_timestamp(self) -> Optional[str]:
        if not self._active_source:
            return None
        return datetime.now(self.tz).isoformat()

    def test_connection(self) -> Dict[str, Any]:
        if not self._active_source or not self._active_source.get('url'):
            return {"status": "error", "message": "No URL configured for this source"}
        
        try:
            headers = self._active_source.get('headers', {})
            resp = requests.get(self._active_source['url'], headers=headers, timeout=5)
            if resp.ok:
                return {"status": "ok", "message": f"Connected to {self.provider_name}", "latency_ms": int(resp.elapsed.total_seconds() * 1000)}
            else:
                return {"status": "error", "message": f"API returned {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        if not self._active_source or not self._active_source.get('url'):
            return []
        try:
            headers = self._active_source.get('headers', {})
            resp = requests.get(self._active_source['url'], headers=headers, timeout=10)
            if resp.ok:
                data = resp.json()
                if isinstance(data, list): return data
                for key in ['results', 'records', 'data', 'items']:
                    if isinstance(data.get(key), list): return data[key]
                # Single object response (most common for telemetry APIs)
                if isinstance(data, dict):
                    return [data]
            return []
        except Exception as e:
            print(f"[DynamicAPI] Fetch failed for {self.provider_name}: {e}")
            return []

    def _normalize_record(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply field_mapping to translate external field names into
        the universal internal schema (UNIVERSAL_SCHEMA).
        """
        mapping = self.get_schema_mapping()
        normalized = {"timestamp": None}

        # Reverse the mapping: internal_key -> external_key
        for internal_key, external_key in mapping.items():
            value = raw.get(external_key)
            if value is not None:
                normalized[internal_key] = value

        # Auto-detect timestamp if not mapped
        if not normalized.get("timestamp"):
            for ts_key in ["timestamp", "recorded_at", "ts", "sample_time",
                           "event_time", "reading_time", "utc_time", "date_heure"]:
                if raw.get(ts_key):
                    normalized["timestamp"] = raw[ts_key]
                    break

        return normalized

    def ingest(self) -> list:
        """
        Fetch and normalize external data to the universal schema.

        - If persist_data=True  → normalize + store in energy_readings DB
        - If persist_data=False → normalize only, return for live context (no DB write)

        Returns list of normalized records (useful for live context even when not persisted).
        """
        raw_records = self.fetch_raw_data()
        if not raw_records:
            return []

        normalized_records = []
        persist = self.is_persistent
        source_id = self._active_source.get('id', 'unknown') if self._active_source else 'unknown'

        for raw in raw_records:
            normalized = self._normalize_record(raw)
            if normalized.get("timestamp"):
                normalized_records.append(normalized)
                if persist:
                    self.db.store_universal_reading(normalized, source_id, self.company_id)

        return normalized_records

    def fetch_context(self, layers: List[str], topics: List[str]) -> str:
        if not self._active_source:
            return ""

        source_id = self._active_source.get('id', 'unknown')
        persist = self.is_persistent
        output = [f"### SOURCE: {self.provider_name} ###"]

        field_labels = {
            "consumption_mw": ("Total Consumption", "MW"),
            "solar_mw": ("Solar Generation", "MW"),
            "wind_mw": ("Wind Generation", "MW"),
            "hydro_mw": ("Hydro Generation", "MW"),
            "gas_mw": ("Gas Generation", "MW"),
            "nuclear_mw": ("Nuclear Generation", "MW"),
            "biomass_mw": ("Biomass Generation", "MW"),
            "storage_mw": ("Storage", "MW"),
            "grid_exchange_mw": ("Grid Exchanges", "MW"),
            "carbon_intensity_g_kwh": ("CO2 Intensity", "g/kWh"),
            "total_production_mw": ("Total Production", "MW"),
            "availability_pct": ("Availability", "%"),
            "forecast_mw": ("Forecast", "MW"),
        }

        def format_record(record: dict) -> str:
            lines = []
            for field, (label, unit) in field_labels.items():
                val = record.get(field)
                if val is not None:
                    lines.append(f"- {label}: {round(val, 2)} {unit}")
            return "\n".join(lines)

        if persist:
            # ── Persist mode: fetch fresh data, store it, query DB for context ──
            fresh = self.ingest()
            stored_note = f"[Ingested {len(fresh)} new reading(s)]" if fresh else ""

            latest = self.db.get_latest_universal_reading(self.company_id, source_id)
            if latest:
                if stored_note:
                    output.append(stored_note)
                output.append("LAYER: Latest Reading (Stored)")
                output.append(format_record(latest))

            # Historical context
            if "today" in layers or "last_7_days" in layers:
                hours = 24 if "today" in layers else 168
                records = self.db.get_universal_readings(self.company_id, source_id, hours=hours)
                if records:
                    consumptions = [r.get("consumption_mw") for r in records if r.get("consumption_mw")]
                    solars = [r.get("solar_mw") for r in records if r.get("solar_mw")]
                    winds = [r.get("wind_mw") for r in records if r.get("wind_mw")]
                    co2s = [r.get("carbon_intensity_g_kwh") for r in records if r.get("carbon_intensity_g_kwh")]
                    output.append(f"LAYER: {hours}h History ({len(records)} readings)")
                    if consumptions:
                        output.append(f"- Peak Consumption: {max(consumptions):.0f} MW | Avg: {sum(consumptions)/len(consumptions):.0f} MW")
                    if solars:
                        output.append(f"- Peak Solar: {max(solars):.0f} MW | Avg: {sum(solars)/len(solars):.0f} MW")
                    if winds:
                        output.append(f"- Peak Wind: {max(winds):.0f} MW")
                    if co2s:
                        output.append(f"- Avg CO2 Intensity: {sum(co2s)/len(co2s):.1f} g/kWh")
        else:
            # ── Live-only mode: fetch now, use directly, no DB ─────────────────
            live_records = self.ingest()  # returns normalized, does NOT store
            if live_records:
                output.append("LAYER: Live Snapshot (not stored)")
                output.append(format_record(live_records[0]))
            else:
                output.append("(No live data available at this moment)")

        return "\n".join(output)


