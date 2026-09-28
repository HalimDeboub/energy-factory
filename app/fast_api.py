from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from app.tools.rag_pipeline import EnergyRAG
from datetime import datetime
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Any
from contextlib import contextmanager
import sqlite3
import pytz

load_dotenv() 
import os

# Verify LangSmith is configured
# if os.getenv("LANGCHAIN_TRACING_V2") != "true":
#     print(" LANGCHAIN_TRACING_V2 not enabled! Traces won't appear in LangSmith")
# if not os.getenv("LANGCHAIN_API_KEY"):
#     print(" LANGCHAIN_API_KEY missing! Get key: https://smith.langchain.com/settings")

app = FastAPI(title="🇫🇷 Energy RAG API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_PATH = "app\\database\\energy_data.db"  # Update this path to match your database location

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

rag = EnergyRAG()

import asyncio
from app.core.ingestor import UnifiedIngestor
from app.config.config import FETCH_INTERVAL_MINUTES

async def ingestion_loop():
    """Background loop to sync all providers periodically"""
    ingestor = UnifiedIngestor()
    while True:
        try:
            print(" [System] Starting automated ingestion sync...")
            # Sync everything currently loaded in the RAG dispatcher
            ingestor.sync_all(rag.dispatcher.data_providers)
            print(f" [System] Sync complete. Sleeping for {FETCH_INTERVAL_MINUTES}m")
        except Exception as e:
            print(f" [System] Ingestion loop error: {e}")
        
        await asyncio.sleep(FETCH_INTERVAL_MINUTES * 60)

@app.on_event("startup")
async def startup_event():
    # Start the ingestion loop in the background
    asyncio.create_task(ingestion_loop())

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: str = "streamlit_default"  # ← Enables conversation memory
    time_intent: str | None = None

class InsightsMetrics(BaseModel):
    co2_saved_kg: float
    current_consumption_kwh: float
    solar_efficiency_percent: float
    period: str
    timestamp: str

class InsightsMetricsResponse(BaseModel):
    status: str
    metrics: InsightsMetrics

class DataSourceConfig(BaseModel):
    id: str
    name: str
    type: str  # "rest_api", "iot", "database", "document"
    enabled: bool
    url: str | None = None
    topic: str | None = None
    connection_string: str | None = None
    metrics: List[str] = []
    field_mapping: Dict[str, str] = {}
    persist_data: bool = False
    headers: Dict[str, str] = {}

class SourcesResponse(BaseModel):
    data_sources: List[DataSourceConfig]
    knowledge_sources: List[Any]

class EnergyDataPoint(BaseModel):
    time: str
    # Legacy names for UI compat
    consommation: float
    nucleaire: float | None = None
    eolien: float | None = None
    solaire: float | None = None
    hydraulique: float | None = None
    gaz: float | None = None
    # Universal names
    consumption_mw: float | None = None
    nuclear_mw: float | None = None
    wind_mw: float | None = None
    solar_mw: float | None = None
    hydro_mw: float | None = None
    gas_mw: float | None = None
    biomass_mw: float | None = None
    taux_co2: float | None = None
    carbon_intensity_g_kwh: float | None = None

class EnergyHistoryResponse(BaseModel):
    status: str
    data: List[EnergyDataPoint]
    period: str

class EnergyMix(BaseModel):
    # Legacy
    nucleaire: float
    eolien: float
    solaire: float
    hydraulique: float
    gaz: float
    # Universal
    nuclear_mw: float | None = None
    wind_mw: float | None = None
    solar_mw: float | None = None
    hydro_mw: float | None = None
    gas_mw: float | None = None
    biomass_mw: float | None = None
    # Common
    total_production: float
    consommation: float
    taux_co2: float
    timestamp: str

class EnergyHistoryResponse(BaseModel):
    status: str
    data: List[EnergyDataPoint]
    period: str

class EnergyMix(BaseModel):
    nucleaire: float
    eolien: float
    solaire: float
    hydraulique: float
    gaz: float
    total_production: float
    consommation: float
    taux_co2: float
    timestamp: str

class EnergyMixResponse(BaseModel):
    status: str
    mix: EnergyMix

# ── Auth & Identity Models ───────────────────────────────────────────
from app.database.models import User, Company, Token
from app.core.auth import get_password_hash, verify_password, create_access_token
from app.database.auth_db import AuthDatabase
import uuid

auth_db = AuthDatabase()

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: str
    sector: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/register", response_model=Token)
async def register(req: RegisterRequest):
    # Check if user exists
    if auth_db.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 1. Create Company
    company_id = str(uuid.uuid4())
    company = Company(id=company_id, name=req.company_name, sector=req.sector)
    auth_db.create_company(company)
    
    # 2. Create User
    user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(req.password)
    user = User(
        id=user_id,
        email=req.email,
        full_name=req.full_name,
        company_id=company_id,
        role="admin",
        hashed_password=hashed_pwd
    )
    auth_db.create_user(user)
    
    # 3. Issue Token
    access_token = create_access_token(data={"sub": user.email, "company_id": company_id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(req: LoginRequest):
    user = auth_db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["email"], "company_id": user["company_id"]})
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordBearer
from app.core.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload  # Returns {"sub": email, "company_id": cid}

# Existing endpoints
@app.post("/analyze-energy")
async def analyze_energy(req: QueryRequest, user: dict = Depends(get_current_user)):
    try:
        # Use company_id from token to isolate RAG context (future enhancement)
        company_id = user.get("company_id")
        
        answer = rag.query(
            user_query=req.query,
            session_id=req.session_id,
            time_intent=req.time_intent,
            company_id=company_id
        )
        return {
            "status": "success",
            "analysis": answer,
            "company_id": company_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f" Error in /analyze-energy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG failed: {str(e)[:100]}"
        )

@app.get("/health")
async def health():
    return {"status": "healthy", "eco2mix_api": "operational"}

@app.get("/debug/state-check")
async def state_check():
    """Verify modular framework state"""
    try:
        data_providers = [p.provider_name for p in rag.dispatcher.data_providers]
        knowledge_providers = [p.provider_name for p in rag.dispatcher.knowledge_providers]
        
        # Get latest timestamp across ALL data providers
        latest_ts = "N/A"
        all_timestamps = []
        for p in rag.dispatcher.data_providers:
            ts = p.get_latest_timestamp()
            if ts:
                all_timestamps.append(ts)
        
        if all_timestamps:
            # Sort as strings (ISO8601) and take the last one
            latest_ts = sorted(all_timestamps)[-1]

        return {
            "status": "ready",
            "framework": "Modular Energy RAG v2",
            "active_data_providers": data_providers,
            "active_knowledge_providers": knowledge_providers,
            "latest_data_sync": latest_ts,
            "cache_stats": rag.cache.stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/sources", response_model=SourcesResponse)
async def get_sources(user: dict = Depends(get_current_user)):
    """List registered data and knowledge sources for the user's company"""
    from app.config.sources import CONFIG_PATH
    import json
    
    company_id = user.get("company_id")
    
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            full_config = json.load(f)
            # Filter sources by company_id
            data_sources = [s for s in full_config.get("data_sources", []) if s.get("company_id") == company_id or s.get("company_id") == "system_global"]
            knowledge_sources = [s for s in full_config.get("knowledge_sources", []) if s.get("company_id") == company_id]
            return {"data_sources": data_sources, "knowledge_sources": knowledge_sources}
    return {"data_sources": [], "knowledge_sources": []}

@app.post("/sources")
async def add_source(source: DataSourceConfig, user: dict = Depends(get_current_user)):
    """Add a new data or knowledge source dynamically"""
    from app.config.sources import CONFIG_PATH
    import json
    
    company_id = user.get("company_id")
    config = {"data_sources": [], "knowledge_sources": []}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    
    source_data = source.dict()
    source_data["company_id"] = company_id
    
    # Route to right collection based on type
    if source_data.get("type") == "document":
        # Transform to knowledge source format
        ks = {
            "id": source_data["id"],
            "name": source_data["name"],
            "type": "pdf", # or auto-detect
            "path": source_data["url"],
            "enabled": True,
            "company_id": company_id
        }
        config['knowledge_sources'].append(ks)
    else:
        config['data_sources'].append(source_data)
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
        
    return {"status": "success", "message": f"Source '{source.name}' provisioned for company {company_id}"}

@app.delete("/sources/{source_id}")
async def delete_source(source_id: str, user: dict = Depends(get_current_user)):
    """Remove a source registered for the user's company"""
    from app.config.sources import CONFIG_PATH
    import json
    
    company_id = user.get("company_id")
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(status_code=404, detail="Config file not found")
        
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    # Filter out the source if it belongs to this company
    original_len = len(config.get("data_sources", [])) + len(config.get("knowledge_sources", []))
    config["data_sources"] = [s for s in config.get("data_sources", []) if not (s.get("id") == source_id and s.get("company_id") == company_id)]
    config["knowledge_sources"] = [s for s in config.get("knowledge_sources", []) if not (s.get("id") == source_id and s.get("company_id") == company_id)]
    
    new_len = len(config.get("data_sources", [])) + len(config.get("knowledge_sources", []))
    
    if original_len == new_len:
        raise HTTPException(status_code=404, detail="Source not found or unauthorized")
        
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
        
    return {"status": "success", "message": f"Source {source_id} removed"}

@app.post("/sources/{source_id}/test")
async def test_source_connection(source_id: str):
    """Trigger a live connection test for a specific provider"""
    # 1. Find provider in the active dispatcher
    provider = next((p for p in rag.dispatcher.data_providers if p.provider_name.lower().replace(" ", "_") == source_id or getattr(p, '_active_source', {}).get('id') == source_id), None)
    
    if not provider:
        # Fallback to RTE if ID matches (special case for hardcoded provider)
        if source_id == "rte_france" or source_id == "rte_france_(eco2mix)":
             provider = next((p for p in rag.dispatcher.data_providers if "RTE" in p.provider_name), None)

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found or not initialized")
    
    return provider.test_connection()

@app.post("/sources/discover")
async def discover_source_fields(req: Dict[str, str]):
    """
    Fetch a sample record from a URL and suggest mappings to internal standards.
    """
    url = req.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        import requests
        resp = requests.get(url, timeout=10)
        if not resp.ok:
            return {"status": "error", "message": f"API returned {resp.status_code}"}
        
        data = resp.json()
        
        # Extract a sample record
        sample = {}
        if isinstance(data, list) and len(data) > 0:
            sample = data[0]
        elif isinstance(data, dict):
            for key in ['results', 'records', 'data', 'items']:
                if isinstance(data.get(key), list) and len(data[key]) > 0:
                    sample = data[key][0]
                    break
            if not sample:
                sample = data
        
        if not isinstance(sample, dict):
            return {"status": "error", "message": "Could not extract a structured sample record"}

        # Heuristic Mapping Logic
        mapping_suggestions = {}
        keywords = {
            "consumption_mw": ["consumption", "load", "conso", "demand", "usage"],
            "nuclear_mw": ["nuclear", "nuc"],
            "solar_mw": ["solar", "pv", "sun"],
            "wind_mw": ["wind", "eol"],
            "hydro_mw": ["hydro", "water", "barrage"],
            "gas_mw": ["gas", "gaz"],
            "biomass_mw": ["biomass", "bio"],
            "storage_mw": ["storage", "battery", "batterie", "pumped"],
            "grid_exchange_mw": ["exchange", "export", "import", "interconnection"],
            "carbon_intensity_g_kwh": ["co2", "carbon", "emission", "intensity"],
            "total_production_mw": ["production", "generation", "total_gen"],
            "capacity_mw": ["capacity", "installed", "max_power"],
            "availability_pct": ["availability", "uptime", "ready"],
            "peak_load_mw": ["peak", "max_demand"],
            "forecast_mw": ["forecast", "prediction", "prev"],
            "timestamp": ["date", "time", "timestamp", "ts", "period"]
        }

        for internal_key, syns in keywords.items():
            for field in sample.keys():
                field_lower = field.lower()
                if any(s in field_lower for s in syns):
                    mapping_suggestions[internal_key] = field
                    break

        return {
            "status": "success",
            "fields": list(sample.keys()),
            "sample_data": sample,
            "suggested_mapping": mapping_suggestions
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/performance")
async def get_performance_stats():
    """Get cache hits, misses, and average latency"""
    return {
        "cache": rag.cache.stats,
        "logs_path": "logs/query_log.jsonl"
    }

# NEW: Insights endpoints
@app.get("/insights/metrics", response_model=InsightsMetricsResponse)
async def get_insights_metrics(user: dict = Depends(get_current_user)):
    """
    Get key energy metrics from universal energy_readings table.
    Falls back to legacy energy_data (RTE) if no universal data exists.
    """
    try:
        company_id = user.get("company_id")
        with get_db() as conn:
            cursor = conn.cursor()

            # Try universal table first
            cursor.execute("""
                SELECT consumption_mw, solar_mw, wind_mw, hydro_mw,
                       carbon_intensity_g_kwh, nuclear_mw
                FROM energy_readings
                WHERE company_id = ? OR company_id = 'system_global'
                ORDER BY timestamp DESC LIMIT 1
            """, (company_id,))
            latest = cursor.fetchone()

            # Fallback to legacy RTE table
            if not latest:
                cursor.execute("""
                    SELECT consommation as consumption_mw, solaire as solar_mw,
                           taux_co2 as carbon_intensity_g_kwh, nucleaire as nuclear_mw,
                           eolien as wind_mw, hydraulique as hydro_mw
                    FROM energy_data
                    WHERE company_id = ? OR company_id = 'system_global'
                    ORDER BY date_heure DESC LIMIT 1
                """, (company_id,))
                latest = cursor.fetchone()

            if not latest:
                return {
                    "status": "success",
                    "metrics": {
                        "co2_saved_kg": 0.0,
                        "current_consumption_kwh": 0.0,
                        "solar_efficiency_percent": 0.0,
                        "period": "latest",
                        "timestamp": datetime.now().isoformat()
                    }
                }

            consumption = latest["consumption_mw"] or 0
            solar = latest["solar_mw"] or 0
            wind = latest["wind_mw"] or 0
            hydro = latest["hydro_mw"] or 0
            co2 = latest["carbon_intensity_g_kwh"] or 0

            # Get average CO2 for comparison
            cursor.execute("""
                SELECT AVG(carbon_intensity_g_kwh) as avg_co2 FROM energy_readings
                WHERE timestamp >= datetime('now', '-30 days') AND carbon_intensity_g_kwh IS NOT NULL
            """)
            avg_res = cursor.fetchone()
            avg_co2 = avg_res["avg_co2"] if avg_res and avg_res["avg_co2"] else co2 or 100

            co2_saved = max(0, (avg_co2 - co2) * consumption / 1000)
            solar_efficiency = round(solar / max(consumption, 1) * 100, 2)

            return {
                "status": "success",
                "metrics": {
                    "co2_saved_kg": round(co2_saved, 2),
                    "current_consumption_kwh": round(consumption, 2),
                    "solar_efficiency_percent": solar_efficiency,
                    "period": "latest",
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        print(f"Error in /insights/metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/insights/history", response_model=EnergyHistoryResponse)
async def get_energy_history(hours: int = 24, user: dict = Depends(get_current_user)):
    """
    Get historical energy data from universal energy_readings table.
    Falls back to legacy energy_data if no universal data available.
    """
    try:
        company_id = user.get("company_id")
        with get_db() as conn:
            cursor = conn.cursor()

            # Try universal table
            cursor.execute("""
                SELECT timestamp as time, consumption_mw, solar_mw, wind_mw,
                       hydro_mw, gas_mw, nuclear_mw, carbon_intensity_g_kwh as taux_co2
                FROM energy_readings
                WHERE (company_id = ? OR company_id = 'system_global')
                AND timestamp >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp ASC
            """, (company_id, hours))
            rows = cursor.fetchall()

            if not rows:
                # Fallback to legacy RTE table
                cursor.execute("""
                    SELECT date_heure as time,
                           consommation as consumption_mw,
                           nucleaire as nuclear_mw, eolien as wind_mw,
                           solaire as solar_mw, hydraulique as hydro_mw,
                           gaz as gas_mw, taux_co2
                    FROM energy_data
                    WHERE (company_id = ? OR company_id = 'system_global')
                    AND date_heure >= datetime('now', '-' || ? || ' hours')
                    ORDER BY date_heure ASC
                """, (company_id, hours))
                rows = cursor.fetchall()

            return {
                "status": "success",
                "data": [
                    {
                        "time": row["time"],
                        # Legacy
                        "consommation": round(row["consumption_mw"] or 0, 2),
                        "eolien": row["wind_mw"],
                        "solaire": row["solar_mw"],
                        "hydraulique": row["hydro_mw"],
                        "gaz": row["gas_mw"],
                        "nucleaire": row["nuclear_mw"],
                        "taux_co2": row["taux_co2"],
                        # Universal
                        "consumption_mw": round(row["consumption_mw"] or 0, 2),
                        "wind_mw": row["wind_mw"],
                        "solar_mw": row["solar_mw"],
                        "hydro_mw": row["hydro_mw"],
                        "gas_mw": row["gas_mw"],
                        "nuclear_mw": row["nuclear_mw"],
                        "carbon_intensity_g_kwh": row["taux_co2"]
                    }
                    for row in rows
                ],
                "period": f"last_{hours}h"
            }
    except Exception as e:
        print(f"Error in /insights/history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/insights/energy-mix", response_model=EnergyMixResponse)
async def get_energy_mix(user: dict = Depends(get_current_user)):
    """
    Get current energy mix from universal energy_readings.
    Falls back to legacy energy_data if no universal data available.
    """
    try:
        company_id = user.get("company_id")
        with get_db() as conn:
            cursor = conn.cursor()

            # Try universal table
            cursor.execute("""
                SELECT nuclear_mw, wind_mw, solar_mw, hydro_mw, gas_mw,
                       biomass_mw, storage_mw, consumption_mw, carbon_intensity_g_kwh, timestamp
                FROM energy_readings
                WHERE company_id = ? OR company_id = 'system_global'
                ORDER BY timestamp DESC LIMIT 1
            """, (company_id,))
            row = cursor.fetchone()

            if row:
                consumption = row["consumption_mw"] or 1
                return {
                    "status": "success",
                    "mix": {
                        "nucleaire": row["nuclear_mw"] or 0,
                        "eolien": row["wind_mw"] or 0,
                        "solaire": row["solar_mw"] or 0,
                        "hydraulique": row["hydro_mw"] or 0,
                        "gaz": row["gas_mw"] or 0,
                        "total_production": round((row["nuclear_mw"] or 0) + (row["wind_mw"] or 0)
                                                  + (row["solar_mw"] or 0) + (row["hydro_mw"] or 0)
                                                  + (row["gas_mw"] or 0) + (row["biomass_mw"] or 0), 2),
                        "consommation": consumption,
                        "taux_co2": row["carbon_intensity_g_kwh"] or 0,
                        "timestamp": row["timestamp"] or datetime.now().isoformat()
                    }
                }

            # Fallback legacy RTE table
            cursor.execute("""
                SELECT nucleaire, eolien, solaire, hydraulique, gaz, consommation, taux_co2
                FROM energy_data
                WHERE company_id = ? OR company_id = 'system_global'
                ORDER BY date_heure DESC LIMIT 1
            """, (company_id,))
            row = cursor.fetchone()

            if not row:
                return {
                    "status": "success",
                    "mix": {
                        "nucleaire": 0.0, "eolien": 0.0, "solaire": 0.0,
                        "hydraulique": 0.0, "gaz": 0.0, "total_production": 0.0,
                        "consommation": 0.0, "taux_co2": 0.0,
                        "timestamp": datetime.now().isoformat()
                    }
                }

            consumption = row["consommation"] or 1
            return {
                "status": "success",
                "mix": {
                    "nucleaire": row["nucleaire"] or 0,
                    "eolien": row["eolien"] or 0,
                    "solaire": row["solaire"] or 0,
                    "hydraulique": row["hydraulique"] or 0,
                    "gaz": row["gaz"] or 0,
                    "total_production": consumption,
                    "consommation": consumption,
                    "taux_co2": row["taux_co2"] or 0,
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        print(f"Error in /insights/energy-mix: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/reports/ai-summary")
async def get_ai_summary(user: dict = Depends(get_current_user)):
    """Generate an AI-driven summary of the last 24 hours of energy data"""
    try:
        # 1. Get data for the last 24h
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(consommation) as avg_cons, MAX(consommation) as max_cons,
                       SUM(solaire) as total_solar, AVG(taux_co2) as avg_co2
                FROM energy_data
                WHERE (company_id = ? OR company_id = 'system_global')
                AND date_heure >= datetime('now', '-24 hours')
            """, (user.get("company_id"),))
            summary_stats = cursor.fetchone()

        # 2. Construct a prompt for the RAG
        stats_text = (
            f"Last 24h Stats:\n"
            f"- Average Consumption: {round(summary_stats['avg_cons'] or 0, 2)} MW\n"
            f"- Peak Demand: {round(summary_stats['max_cons'] or 0, 2)} MW\n"
            f"- Total Solar Contribution: {round(summary_stats['total_solar'] or 0, 2)} MW\n"
            f"- Average CO2 Intensity: {round(summary_stats['avg_co2'] or 0, 2)} g/kWh"
        )

        query = f"Provide a professional executive summary of the following energy performance: {stats_text}. Mention trends and recommendations for the transition."
        
        answer = rag.query(
            user_query=query,
            session_id="reporting_agent",
            company_id=user.get("company_id", "system_global")
        )

        return {
            "status": "success",
            "summary": answer,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f" Error generating AI report: {str(e)}")
        return {"status": "error", "message": "Failed to generate AI report"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.fast_api:app", host="0.0.0.0", port=9000, reload=True)