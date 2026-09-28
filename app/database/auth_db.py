import sqlite3
import json
from typing import Optional, List, Dict
from app.database.models import User, Company
from app.config.config import BASE_DIR

AUTH_DB_PATH = BASE_DIR / "app/database/identity.db"

class AuthDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(AUTH_DB_PATH, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                company_id TEXT,
                role TEXT,
                hashed_password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)
        self.conn.commit()

    def create_company(self, company: Company):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO companies (id, name, sector) VALUES (?, ?, ?)",
            (company.id, company.name, company.sector)
        )
        self.conn.commit()

    def create_user(self, user: User):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (id, email, full_name, company_id, role, hashed_password) VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, user.email, user.full_name, user.company_id, user.role, user.hashed_password)
        )
        self.conn.commit()

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "email": row[1],
            "full_name": row[2],
            "company_id": row[3],
            "role": row[4],
            "hashed_password": row[5]
        }
    
    def get_company(self, company_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "sector": row[2]}
