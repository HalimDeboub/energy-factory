# app/providers/data/dynamic_db_provider.py
#
# ═══════════════════════════════════════════════════════════════════════════
# DYNAMIC DATABASE PROVIDER — SQL / SCADA Adapter
# ═══════════════════════════════════════════════════════════════════════════

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz
import sqlite3
# Try to import sqlalchemy for broader DB support, fallback to sqlite if missing
try:
    import sqlalchemy
    from sqlalchemy import create_engine, text
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

from app.core.base import BaseDataProvider
from app.config.sources import CONFIG_PATH
from app.config.config import TIMEZONE
from app.database.database import EnergyDatabase


class DynamicDBProvider(BaseDataProvider):
    """
    A provider that connects to external databases (SCADA, SQL)
    and maps their tables to the universal energy schema.
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
            if not os.path.exists(CONFIG_PATH): return []
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return data.get("data_sources", [])
        except Exception:
            return []

    @property
    def provider_name(self) -> str:
        return self._active_source['name'] if self._active_source else "Dynamic DB Manager"

    @property
    def company_id(self) -> str:
        return self._active_source.get('company_id', 'system_global') if self._active_source else 'system_global'

    @property
    def is_persistent(self) -> bool:
        return self._active_source.get('persist_data', False) if self._active_source else False

    def get_schema_mapping(self) -> Dict[str, str]:
        return self._active_source.get('field_mapping', {}) if self._active_source else {}

    def test_connection(self) -> Dict[str, Any]:
        if not self._active_source or not self._active_source.get('connection_string'):
            return {"status": "error", "message": "No connection string configured"}
        
        conn_str = self._active_source['connection_string']
        try:
            if not HAS_SQLALCHEMY and not conn_str.startswith("sqlite"):
                return {"status": "error", "message": "SQLAlchemy required for non-sqlite DBs"}
            
            if conn_str.startswith("sqlite"):
                path = conn_str.replace("sqlite:///", "")
                conn = sqlite3.connect(path)
                conn.close()
            else:
                engine = create_engine(conn_str)
                with engine.connect() as conn:
                    pass
            return {"status": "ok", "message": f"Successfully connected to {self.provider_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        if not self._active_source or not self._active_source.get('connection_string'):
            return []
        
        conn_str = self._active_source['connection_string']
        query = self._active_source.get('url', "") # In DB type, 'url' is used for table name or query
        
        if not query: return []

        try:
            results = []
            if conn_str.startswith("sqlite"):
                path = conn_str.replace("sqlite:///", "")
                with sqlite3.connect(path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    if "SELECT" in query.upper():
                        cursor.execute(query)
                    else:
                        cursor.execute(f"SELECT * FROM {query} ORDER BY 1 DESC LIMIT 10")
                    results = [dict(row) for row in cursor.fetchall()]
            elif HAS_SQLALCHEMY:
                engine = create_engine(conn_str)
                with engine.connect() as conn:
                    if "SELECT" in query.upper():
                        res = conn.execute(text(query))
                    else:
                        res = conn.execute(text(f"SELECT * FROM {query} ORDER BY 1 DESC LIMIT 10"))
                    results = [dict(row._asdict()) for row in res.fetchall()]
            return results
        except Exception as e:
            print(f"[DynamicDB] Fetch failed for {self.provider_name}: {e}")
            return []

    def _normalize_record(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        mapping = self.get_schema_mapping()
        normalized = {"timestamp": None}
        for internal_key, external_key in mapping.items():
            value = raw.get(external_key)
            if value is not None:
                normalized[internal_key] = value
        
        if not normalized.get("timestamp"):
            for ts_key in ["timestamp", "recorded_at", "ts", "sample_time", "date_heure"]:
                if raw.get(ts_key):
                    normalized["timestamp"] = raw[ts_key]
                    break
        return normalized

    def ingest(self) -> list:
        raw_records = self.fetch_raw_data()
        if not raw_records: return []

        normalized_records = []
        persist = self.is_persistent
        source_id = self._active_source.get('id', 'unknown')
        
        for raw in raw_records:
            normalized = self._normalize_record(raw)
            if normalized.get("timestamp"):
                normalized_records.append(normalized)
                if persist:
                    self.db.store_universal_reading(normalized, source_id, self.company_id)
        return normalized_records

    def fetch_context(self, layers: List[str], topics: List[str]) -> str:
        if not self._active_source: return ""
        source_id = self._active_source.get('id', 'unknown')
        persist = self.is_persistent
        output = [f"### SOURCE (DB): {self.provider_name} ###"]

        field_labels = {
            "consumption_mw": ("Total Consumption", "MW"),
            "solar_mw": ("Solar Generation", "MW"),
            "wind_mw": ("Wind Generation", "MW"),
            "carbon_intensity_g_kwh": ("CO2 Intensity", "g/kWh"),
        }

        def format_record(record: dict) -> str:
            lines = []
            for field, (label, unit) in field_labels.items():
                val = record.get(field)
                if val is not None:
                    lines.append(f"- {label}: {round(val, 2)} {unit}")
            return "\n".join(lines)

        if persist:
            fresh = self.ingest()
            latest = self.db.get_latest_universal_reading(self.company_id, source_id)
            if latest:
                output.append("LAYER: Latest Reading (Stored)")
                output.append(format_record(latest))
        else:
            live = self.ingest()
            if live:
                output.append("LAYER: Live Query Snapshot")
                output.append(format_record(live[0]))
        
        return "\n".join(output)
import os
