from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.tools.rag_pipeline import EnergyRAG
from datetime import datetime
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import List
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
    """Verify state flags compute correctly"""
    rag = EnergyRAG()
    latest = rag.context_builder.summarizer.db.get_latest_record()
    
    # Replicate EXACT logic from query() method
    has_fresh_data = False
    age_min = None
    if latest and latest.get("date_heure"):
        try:
            record_time = datetime.fromisoformat(latest["date_heure"].replace('Z','+00:00'))
            age_min = (datetime.now(pytz.timezone("Africa/Algiers")) - 
                      record_time.astimezone(pytz.timezone("Africa/Algiers"))).total_seconds() / 60
            has_fresh_data = age_min < 120
        except:
            pass
    
    return {
        "has_fresh_data": has_fresh_data,
        "data_age_min": round(age_min, 1) if age_min else None,
        "latest_record": latest,
        "db_record_count": rag.context_builder.summarizer.db.get_record_count()
    }

# NEW: Insights endpoints
@app.get("/insights/metrics", response_model=InsightsMetricsResponse)
async def get_insights_metrics():
    """
    Get key energy metrics: CO₂ saved, energy usage, and solar output
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True)