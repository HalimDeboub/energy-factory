from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime

class Company(BaseModel):
    id: str
    name: str
    sector: str = "Energy"
    created_at: datetime = datetime.now()

class User(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    company_id: str
    role: str = "viewer"  # admin, viewer, analyst
    hashed_password: str
    created_at: datetime = datetime.now()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    company_id: Optional[str] = None

class SourceMapping(BaseModel):
    external_field: str
    internal_field: str

class DataSource(BaseModel):
    id: str
    name: str
    type: str  # rest_api, iot, database
    url: Optional[str] = None
    enabled: bool = True
    persist_data: bool = False
    field_mapping: Dict[str, str] = {}
    company_id: str
