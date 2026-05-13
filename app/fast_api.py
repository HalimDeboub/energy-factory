from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
#     print("⚠️ LANGCHAIN_TRACING_V2 not enabled! Traces won't appear in LangSmith")
# if not os.getenv("LANGCHAIN_API_KEY"):
#     print("⚠️ LANGCHAIN_API_KEY missing! Get key: https://smith.langchain.com/settings")

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
    type: str  # "rest_api", "iot", "database"
    enabled: bool
    url: str | None = None
    topic: str | None = None
    connection_string: str | None = None
    metrics: List[str] = []

class SourcesResponse(BaseModel):
    data_sources: List[DataSourceConfig]
    knowledge_sources: List[Any]

class EnergyDataPoint(BaseModel):
    time: str
    consommation: float
    nucleaire: float | None = None
    eolien: float | None = None
    solaire: float | None = None
    hydraulique: float | None = None
    gaz: float | None = None
    taux_co2: float | None = None

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

# Existing endpoints
@app.post("/analyze-energy")
async def analyze_energy(req: QueryRequest):
    try:
        # 🔑 CORRECT CALL: Uses "input" key internally (handled by query() method)
        answer = rag.query(
            user_query=req.query,
            session_id=req.session_id,  # ← Enables multi-turn memory
            time_intent=req.time_intent
        )
        return {
            "status": "success",
            "analysis": answer,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error in /analyze-energy: {str(e)}")
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
async def get_sources():
    """List all registered data and knowledge sources"""
    from app.config.sources import CONFIG_PATH
    import json
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {"data_sources": [], "knowledge_sources": []}

@app.post("/sources")
async def add_source(source: DataSourceConfig):
    """Add a new data source dynamically via the UI"""
    from app.config.sources import CONFIG_PATH
    import json
    
    config = {"data_sources": [], "knowledge_sources": []}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    
    # Check if ID already exists
    if any(s['id'] == source.id for s in config['data_sources']):
         raise HTTPException(status_code=400, detail="Source ID already exists")

    config['data_sources'].append(source.dict())
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
        
    return {"status": "success", "message": f"Source '{source.name}' added successfully"}

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

@app.get("/performance")
async def get_performance_stats():
    """Get cache hits, misses, and average latency"""
    return {
        "cache": rag.cache.stats,
        "logs_path": "logs/query_log.jsonl"
    }

# NEW: Insights endpoints
@app.get("/insights/metrics", response_model=InsightsMetricsResponse)
async def get_insights_metrics():
    """
    Get key energy metrics: CO2 saved, energy usage, and solar output
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get latest record for current metrics
            cursor.execute("""
                SELECT consommation, solaire, taux_co2, nucleaire, eolien, hydraulique
                FROM energy_data
                ORDER BY date_heure DESC
                LIMIT 1
            """)
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
            
            # Calculate renewable energy (excluding nuclear)
            renewable_energy = (latest["solaire"] or 0) + (latest["eolien"] or 0) + (latest["hydraulique"] or 0)
            
            # Get average CO₂ rate for comparison (last 7 days)
            cursor.execute("""
                SELECT AVG(taux_co2) as avg_co2
                FROM energy_data
                WHERE date_heure >= datetime('now', '-30 days')
                AND taux_co2 IS NOT NULL
            """)
            avg_result = cursor.fetchone()
            avg_co2 = avg_result["avg_co2"] if avg_result and avg_result["avg_co2"] else 100
            
            # Calculate CO₂ saved (compared to average)
            current_co2 = latest["taux_co2"] or avg_co2
            co2_saved = max(0, (avg_co2 - current_co2) * (latest["consommation"] or 0) / 1000)
            
            return {
                "status": "success",
                "metrics": {
                    "co2_saved_kg": round(co2_saved, 2),
                    "current_consumption_kwh": round(latest["consommation"] or 0, 2),
                    "solar_efficiency_percent": round((latest["solaire"] or 0) / (latest["consommation"] or 1) * 100, 2),
                    "period": "latest",
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        print(f"❌ Error in /insights/metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/insights/history", response_model=EnergyHistoryResponse)
async def get_energy_history(hours: int = 24):
    """
    Get historical energy consumption and renewable energy data
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    date_heure,
                    consommation,
                    nucleaire,
                    eolien,
                    solaire,
                    hydraulique,
                    gaz,
                    taux_co2
                FROM energy_data
                WHERE date_heure >= datetime('now', '-' || ? || ' hours')
                ORDER BY date_heure ASC
            """, (hours,))
            
            rows = cursor.fetchall()
            
            return {
                "status": "success",
                "data": [
                    {
                        "time": row["date_heure"],
                        "consommation": round(row["consommation"] or 0, 2),
                        "nucleaire": row["nucleaire"],
                        "eolien": row["eolien"],
                        "solaire": row["solaire"],
                        "hydraulique": row["hydraulique"],
                        "gaz": row["gaz"],
                        "taux_co2": row["taux_co2"]
                    }
                    for row in rows
                ],
                "period": f"last_{hours}h"
            }
    except Exception as e:
        print(f"❌ Error in /insights/history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/insights/energy-mix", response_model=EnergyMixResponse)
async def get_energy_mix():
    """
    Get current energy mix breakdown by source
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    nucleaire,
                    eolien,
                    solaire,
                    hydraulique,
                    gaz,
                    consommation,
                    taux_co2
                FROM energy_data
                ORDER BY date_heure DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "success",
                    "mix": {
                        "nucleaire": 0.0,
                        "eolien": 0.0,
                        "solaire": 0.0,
                        "hydraulique": 0.0,
                        "gaz": 0.0,
                        "total_production": 0.0,
                        "consommation": 0.0,
                        "taux_co2": 0.0,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            total_consumption = row["consommation"] or 1
            
            sources = [
                {"name": "Nuclear", "value": row["nucleaire"] or 0},
                {"name": "Wind", "value": row["eolien"] or 0},
                {"name": "Solar", "value": row["solaire"] or 0},
                {"name": "Hydro", "value": row["hydraulique"] or 0},
                {"name": "Gas", "value": row["gaz"] or 0},
            ]
            
            # Calculate percentages
            result = []
            for source in sources:
                if source["value"] > 0:
                    result.append({
                        "name": source["name"],
                        "value": round(source["value"], 2),
                        "percentage": round((source["value"] / total_consumption) * 100, 2)
                    })
            
            return {
                "status": "success",
                "mix": {
                    "nucleaire": row["nucleaire"] or 0,
                    "eolien": row["eolien"] or 0,
                    "solaire": row["solaire"] or 0,
                    "hydraulique": row["hydraulique"] or 0,
                    "gaz": row["gaz"] or 0,
                    "total_production": total_consumption,
                    "consommation": total_consumption,
                    "taux_co2": row["taux_co2"] or 0,
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        print(f"❌ Error in /insights/energy-mix: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/reports/ai-summary")
async def get_ai_summary():
    """Generate an AI-driven summary of the last 24 hours of energy data"""
    try:
        # 1. Get data for the last 24h
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(consommation) as avg_cons, MAX(consommation) as max_cons,
                       SUM(solaire) as total_solar, AVG(taux_co2) as avg_co2
                FROM energy_data
                WHERE date_heure >= datetime('now', '-24 hours')
            """)
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
            session_id="reporting_agent"
        )

        return {
            "status": "success",
            "summary": answer,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error generating AI report: {str(e)}")
        return {"status": "error", "message": "Failed to generate AI report"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True)