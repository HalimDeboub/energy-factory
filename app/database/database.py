import sqlite3
from datetime import datetime
import pytz
from app.config.config import DB_PATH, CRITICAL_FIELDS, TIMEZONE

class EnergyDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.tz = pytz.timezone(TIMEZONE)
        self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()
        # Store date_heure as ISO8601 WITH timezone offset (critical fix)
        cols = ", ".join([
            f"{field} TEXT" if field == "date_heure" else f"{field} INTEGER"
            for field in CRITICAL_FIELDS
        ])
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS energy_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {cols},
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_heure ON energy_data(date_heure DESC)")
        self.conn.commit()
    
    
        # app/database.py → EnergyDatabase.store_records()

    def store_records(self, records):
        """Store records with duplicate prevention. Returns count of NEW records."""
        cursor = self.conn.cursor()
        placeholders = ", ".join(["?"] * len(CRITICAL_FIELDS))
        cols = ", ".join(CRITICAL_FIELDS)
        stored_count = 0
        
        for record in records:
            raw_ts = record.get("date_heure", "")
            if not raw_ts:
                continue
            
            # ✅ CRITICAL: NO NORMALIZATION - store EXACTLY as received
            # Only validate it has timezone info for debugging
            if '+' not in raw_ts and not raw_ts.endswith('Z'):
                print(f"⚠️ Skipping record with naive timestamp (no TZ): {raw_ts}")
                continue
            
            # Skip duplicates using RAW timestamp string
            cursor.execute("SELECT 1 FROM energy_data WHERE date_heure = ?", (raw_ts,))
            if cursor.fetchone():
                continue  # Already exists → skip
            
            values = [raw_ts if field == "date_heure" else record.get(field) for field in CRITICAL_FIELDS]
            cursor.execute(f"INSERT INTO energy_data ({cols}) VALUES ({placeholders})", values)
            stored_count += 1
        
        self.conn.commit()
        return stored_count  # Returns int (never None)
    



    def get_latest_record(self):
        """Get absolute latest record (no time filtering)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM energy_data 
            ORDER BY date_heure DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        
        # Return full record with timezone-aware datetime for debugging
        record = dict(zip(CRITICAL_FIELDS, row[1:-1]))
        record['_debug_fetched_at'] = row[-1]
        return record
    
    def get_time_range(self, start_dt, end_dt):
        """Time-range query using ISO8601 string comparison (safe in SQLite)"""
        cursor = self.conn.cursor()
        # Convert to ISO8601 strings WITH timezone for reliable comparison
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()
        
        cursor.execute("""
            SELECT * FROM energy_data 
            WHERE date_heure BETWEEN ? AND ?
            ORDER BY date_heure ASC
        """, (start_iso, end_iso))
        
        return [dict(zip(CRITICAL_FIELDS, row[1:-1])) for row in cursor.fetchall()]
    
    
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
            print(f"✅ Latest record stored: {record['date_heure']}")
            print(f"   Consommation: {record.get('consommation')} MW")
            print(f"   Fetched at: {record['_debug_fetched_at']}")
        else:
            print("❌ No records in database!")
            
    # app/database.py → EnergyDatabase class
    def get_record_count(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM energy_data")
        return cursor.fetchone()[0]

    
    
    
    
    # def _validate_timestamp(self, ts: str) -> str:
    #   """Reject naive timestamps BEFORE storage (fail fast)"""
    #   if not ts or ('+' not in ts and not ts.endswith('Z')):
    #     raise ValueError(
    #         f"❌ CRITICAL: Timestamp missing timezone! Got: '{ts}'. "
    #         "This breaks all time queries. Fix data_fetcher.py truncation."
    #     )
    #   return ts.replace('Z', '+00:00')