# app/main.py - UPDATED WITH NULL HANDLING
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import traceback
import logging
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="France Energy AI Analyst API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    query: str

def safe_get(data, key, default=0):
    """Safely get value from dict, handling None/null"""
    value = data.get(key)
    if value is None:
        return default
    try:
        # Try to convert to float if it's a string number
        return float(value)
    except (ValueError, TypeError):
        return default

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "France Energy AI",
        "endpoints": {
            "GET /": "This page",
            "POST /analyze": "Analyze energy query",
            "GET /health": "Health check",
            "GET /data": "Get raw energy data"
        }
    }

@app.post("/analyze")
async def analyze_energy(query: Query):
    """Main endpoint for energy analysis"""
    try:
        logger.info(f"Received query: {query.query}")
        
        # Get real data from eco2mix API
        api_url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records"
        params = {"limit": 1, "order_by": "date desc"}
        
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"API returned status {response.status_code}",
                "query": query.query
            }
        
        data = response.json()
        
        if not data.get('results'):
            return {
                "status": "error",
                "message": "No data available from API",
                "query": query.query
            }
        
        latest = data['results'][0]
        
        # Extract data with safe handling of nulls
        production = safe_get(latest, 'production')
        consumption = safe_get(latest, 'consommation')
        nuclear = safe_get(latest, 'nucleaire')
        wind = safe_get(latest, 'eolien')
        solar = safe_get(latest, 'solaire')
        hydro = safe_get(latest, 'hydraulique')
        gas = safe_get(latest, 'gaz')
        carbon_intensity = safe_get(latest, 'taux_co2')
        timestamp = latest.get('date', 'N/A')
        
        # Simple analysis based on query
        query_lower = query.query.lower()
        
        if "nuclear" in query_lower:
            total = production if production > 0 else 1  # Avoid division by zero
            percent = (nuclear / total) * 100 if total > 0 else 0
            analysis = f"Nuclear power provides {percent:.1f}% of France's electricity ({nuclear} MW out of {production} MW total)."
        
        elif "wind" in query_lower:
            total = production if production > 0 else 1
            percent = (wind / total) * 100 if total > 0 else 0
            analysis = f"Wind power provides {percent:.1f}% of France's electricity ({wind} MW out of {production} MW total)."
        
        elif "solar" in query_lower:
            total = production if production > 0 else 1
            percent = (solar / total) * 100 if total > 0 else 0
            analysis = f"Solar power provides {percent:.1f}% of France's electricity ({solar} MW out of {production} MW total)."
        
        elif "renewable" in query_lower or "green" in query_lower:
            renewables = wind + solar + hydro
            total = production if production > 0 else 1
            percent = (renewables / total) * 100 if total > 0 else 0
            analysis = f"Renewables provide {percent:.1f}% of electricity: Wind: {wind} MW, Solar: {solar} MW, Hydro: {hydro} MW."
        
        elif "mix" in query_lower:
            total = nuclear + wind + solar + hydro + gas
            if total > 0:
                analysis = f"Energy mix:\n"
                analysis += f"- Nuclear: {(nuclear/total*100):.1f}% ({nuclear} MW)\n"
                analysis += f"- Wind: {(wind/total*100):.1f}% ({wind} MW)\n"
                analysis += f"- Solar: {(solar/total*100):.1f}% ({solar} MW)\n"
                analysis += f"- Hydro: {(hydro/total*100):.1f}% ({hydro} MW)\n"
                analysis += f"- Gas: {(gas/total*100):.1f}% ({gas} MW)\n"
                analysis += f"Total: {total} MW"
            else:
                analysis = "No production data available."
        
        elif "carbon" in query_lower or "co2" in query_lower:
            analysis = f"Carbon intensity: {carbon_intensity} gCO₂/kWh"
            if carbon_intensity < 50:
                analysis += " (Very low carbon)"
            elif carbon_intensity < 100:
                analysis += " (Low carbon)"
            else:
                analysis += " (Moderate carbon)"
        
        elif "consumption" in query_lower:
            analysis = f"Consumption: {consumption} MW, Production: {production} MW"
            balance = production - consumption
            if balance > 0:
                analysis += f" (Exporting {balance} MW)"
            else:
                analysis += f" (Importing {-balance} MW)"
        
        else:
            analysis = f"France's electricity: Production {production} MW, Consumption {consumption} MW. "
            analysis += f"Nuclear: {nuclear} MW, Wind: {wind} MW, Solar: {solar} MW."
        
        return {
            "status": "success",
            "query": query.query,
            "analysis": analysis,
            "data": {
                "timestamp": timestamp,
                "production_MW": production,
                "consumption_MW": consumption,
                "nuclear_MW": nuclear,
                "wind_MW": wind,
                "solar_MW": solar,
                "hydro_MW": hydro,
                "gas_MW": gas,
                "carbon_intensity": carbon_intensity
            }
        }
        
    except Exception as e:
        logger.error(f"Error in /analyze: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": str(e),
            "query": query.query if 'query' in locals() else "Unknown"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check eco2mix API
        api_url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records"
        api_response = requests.get(api_url, params={"limit": 1}, timeout=10)
        api_ok = api_response.status_code == 200
        
        return {
            "status": "healthy" if api_ok else "degraded",
            "service": "energy-ai-analyst",
            "eco2mix_api": "connected" if api_ok else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "energy-ai-analyst",
            "error": str(e)
        }

@app.get("/data")
async def get_data(limit: int = 3):
    """Get raw energy data with null handling"""
    try:
        api_url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records"
        response = requests.get(api_url, params={"limit": limit, "order_by": "date desc"})
        
        if response.status_code != 200:
            return {"status": "error", "message": f"API error: {response.status_code}"}
        
        data = response.json()
        
        # Process data to handle nulls
        processed_results = []
        for record in data.get('results', []):
            processed = {}
            for key, value in record.items():
                processed[key] = value if value is not None else 0
            processed_results.append(processed)
        
        return {
            "status": "success",
            "count": len(processed_results),
            "data": processed_results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    logger.info("Starting France Energy AI API...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")