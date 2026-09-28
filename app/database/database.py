import sqlite3
from datetime import datetime, timedelta
import pytz
from app.config.config import DB_PATH, CRITICAL_FIELDS, TIMEZONE

class EnergyDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.tz = pytz.timezone(TIMEZONE)
        self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()

        # ── Legacy table (RTE-specific, kept for backward compat) ─────────────
        legacy_cols = ", ".join([
            f"{field} TEXT" if field == "date_heure" else f"{field} REAL"
            for field in ["date_heure","consommation","nucleaire","eolien",
                          "solaire","hydraulique","gaz","taux_co2","ech_physiques"]
        ])
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS energy_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL DEFAULT 'system_global',
                source_id TEXT NOT NULL DEFAULT 'rte_default',
                {legacy_cols},
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Universal table (source-agnostic, all new providers write here) ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS energy_readings (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id             TEXT    NOT NULL DEFAULT 'system_global',
                source_id              TEXT    NOT NULL DEFAULT 'unknown',
                timestamp              TEXT,            -- ISO8601 with tz
                consumption_mw         REAL,            -- Total load (MW)
                solar_mw               REAL,            -- Solar PV (MW)
                wind_mw                REAL,            -- Wind (MW)
                hydro_mw               REAL,            -- Hydro (MW)
                gas_mw                 REAL,            -- Gas / CCGT (MW)
                nuclear_mw             REAL,            -- Nuclear (MW)
                biomass_mw             REAL,            -- Biomass (MW)
                storage_mw             REAL,            -- Battery storage (MW)
                grid_exchange_mw       REAL,            -- Cross-border (MW)
                carbon_intensity_g_kwh REAL,            -- CO2 g/kWh
                total_production_mw    REAL,            -- Sum of all gen
                capacity_mw            REAL,            -- Installed capacity
                availability_pct       REAL,            -- % capacity available
                peak_load_mw           REAL,            -- Period peak demand
                forecast_mw            REAL,            -- Day-ahead forecast
                fetched_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for fast multi-tenant time-range queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_comp_source_ts
            ON energy_readings(company_id, source_id, timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comp_source_date
            ON energy_data(company_id, source_id, date_heure DESC)
        """)

        # Robust column check for legacy table
        cursor.execute("PRAGMA table_info(energy_data)")
        existing_cols = [c[1] for c in cursor.fetchall()]
        if "company_id" not in existing_cols:
            cursor.execute("ALTER TABLE energy_data ADD COLUMN company_id TEXT DEFAULT 'system_global'")
        if "source_id" not in existing_cols:
            cursor.execute("ALTER TABLE energy_data ADD COLUMN source_id TEXT DEFAULT 'rte_default'")

        self.conn.commit()

    
    
        # app/database.py → EnergyDatabase.store_records()
    # ── Universal Schema Methods (new energy_readings table) ─────────────────

    def store_universal_reading(self, record: dict, source_id: str, company_id: str) -> bool:
        """
        Store one normalized record into the universal energy_readings table.
        record keys must match UNIVERSAL_SCHEMA field names.
        Skips duplicates based on (company_id, source_id, timestamp).
        """
        cursor = self.conn.cursor()
        ts = record.get("timestamp", "")
        if not ts:
            return False

        cursor.execute(
            "SELECT 1 FROM energy_readings WHERE company_id=? AND source_id=? AND timestamp=?",
            (company_id, source_id, ts)
        )
        if cursor.fetchone():
            return False  # duplicate

        cursor.execute("""
            INSERT INTO energy_readings (
                company_id, source_id, timestamp,
                consumption_mw, solar_mw, wind_mw, hydro_mw, gas_mw, nuclear_mw,
                biomass_mw, storage_mw, grid_exchange_mw, carbon_intensity_g_kwh,
                total_production_mw, capacity_mw, availability_pct,
                peak_load_mw, forecast_mw
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            company_id, source_id, ts,
            record.get("consumption_mw"),
            record.get("solar_mw"),
            record.get("wind_mw"),
            record.get("hydro_mw"),
            record.get("gas_mw"),
            record.get("nuclear_mw"),
            record.get("biomass_mw"),
            record.get("storage_mw"),
            record.get("grid_exchange_mw"),
            record.get("carbon_intensity_g_kwh"),
            record.get("total_production_mw"),
            record.get("capacity_mw"),
            record.get("availability_pct"),
            record.get("peak_load_mw"),
            record.get("forecast_mw"),
        ))
        self.conn.commit()
        return True

    def get_universal_readings(self, company_id: str, source_id: str = None,
                                hours: int = 24) -> list:
        """Fetch recent records from energy_readings for a given company."""
        cursor = self.conn.cursor()
        query = """
            SELECT * FROM energy_readings
            WHERE company_id = ?
            AND timestamp >= datetime('now', ? || ' hours')
        """
        params = [company_id, f"-{hours}"]
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        query += " ORDER BY timestamp ASC"
        cursor.execute(query, params)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_latest_universal_reading(self, company_id: str, source_id: str = None) -> dict:
        """Get the most recent record from energy_readings."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM energy_readings WHERE company_id = ?"
        params = [company_id]
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        query += " ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not row:
            return {}
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))

    # ── Legacy Methods (energy_data table — RTE backward compat) ─────────────


    def store_records(self, records, source_id: str, company_id: str):
        """Store records with duplicate prevention for a specific source and company."""
        cursor = self.conn.cursor()
        placeholders = ", ".join(["?"] * (len(CRITICAL_FIELDS) + 2))
        cols = "company_id, source_id, " + ", ".join(CRITICAL_FIELDS)
        stored_count = 0
        
        for record in records:
            raw_ts = record.get("date_heure", "")
            if not raw_ts:
                continue
            
            if '+' not in raw_ts and not raw_ts.endswith('Z'):
                continue
            
            # Skip duplicates using RAW timestamp, source_id, AND company_id
            cursor.execute(
                "SELECT 1 FROM energy_data WHERE company_id = ? AND source_id = ? AND date_heure = ?", 
                (company_id, source_id, raw_ts)
            )
            if cursor.fetchone():
                continue
            
            values = [company_id, source_id] + [raw_ts if field == "date_heure" else record.get(field) for field in CRITICAL_FIELDS]
            cursor.execute(f"INSERT INTO energy_data ({cols}) VALUES ({placeholders})", values)
            stored_count += 1
        
        self.conn.commit()
        return stored_count
    



    def get_latest_record(self, company_id: str, source_id: str = None):
        """Get absolute latest record for a specific company."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM energy_data WHERE company_id = ?"
        params = [company_id]
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        
        query += " ORDER BY date_heure DESC LIMIT 1"
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not row:
            return None
        
        # id(0), company_id(1), source_id(2), fields(3...N), fetched_at(-1)
        record = dict(zip(CRITICAL_FIELDS, row[3:-1]))
        record['company_id'] = row[1]
        record['source_id'] = row[2]
        record['_debug_fetched_at'] = row[-1]
        return record
    
    def get_time_range(self, company_id: str, start_dt, end_dt, source_id: str = None):
        """Time-range query with strict company isolation."""
        cursor = self.conn.cursor()
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()
        
        query = "SELECT * FROM energy_data WHERE company_id = ? AND date_heure BETWEEN ? AND ?"
        params = [company_id, start_iso, end_iso]
        
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
            
        query += " ORDER BY date_heure ASC"
        cursor.execute(query, params)
        
        return [dict(zip(CRITICAL_FIELDS, row[3:-1])) for row in cursor.fetchall()]
    
    
    def get_all(self):
        """Time-range query using ISO8601 string comparison (safe in SQLite)"""
        cursor = self.conn.cursor()
      
        cursor.execute("""
            SELECT * FROM energy_data 
             ASC
        """)
        
        return [dict(zip(CRITICAL_FIELDS, row[1:-1])) for row in cursor.fetchall()]
    
    def debug_print_latest(self):
        """Diagnostic tool - run after fetch to verify storage"""
        record = self.get_latest_record()
        if record:
            print(f" Latest record stored: {record['date_heure']}")
            print(f"   Consommation: {record.get('consommation')} MW")
            print(f"   Fetched at: {record['_debug_fetched_at']}")
        else:
            print(" No records in database!")
            
    def get_today_records(self):
        """Get all records from today (00:00 to now)"""
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_time_range(start, now)

    def get_yesterday_same_hour(self, target_hour: int, window_minutes: int = 30):
        """Get records from yesterday around same hour (±window_minutes)"""
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=target_hour, minute=0, second=0, microsecond=0) - timedelta(minutes=window_minutes)
        end = yesterday.replace(hour=target_hour, minute=0, second=0, microsecond=0) + timedelta(minutes=window_minutes)
      #   print(start, end)
        return self.get_time_range(start, end)

    def get_historical_same_hour(self, target_hour: int, days_back: int = 10):
        """Get records for same hour over last N days (for baseline)"""
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        records = []
        for days_ago in range(1, days_back + 1):
            target_date = now - timedelta(days=days_ago)
            start = target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0) - timedelta(minutes=15)
            end = target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0) + timedelta(minutes=15)
            hourly_records = self.get_time_range(start, end)
            if hourly_records:
                # Take closest record to exact hour
                closest = min(hourly_records, key=lambda r: abs(
                    datetime.fromisoformat(r["date_heure"].replace('Z','+00:00')).hour - target_hour
                ))
                records.append(closest)
        return records

    def get_record_count(self):
        """Return total records in database (for diagnostics)"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM energy_data")
        return cursor.fetchone()[0]
    
    
  