from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.tools.rag_pipeline import EnergyRAG
from datetime import datetime  # 🔑 CRITICAL: Was missing!
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
load_dotenv() 
import os
# Verify LangSmith is configured
if os.getenv("LANGCHAIN_TRACING_V2") != "true":
    print("⚠️ LANGCHAIN_TRACING_V2 not enabled! Traces won't appear in LangSmith")
if not os.getenv("LANGCHAIN_API_KEY"):
    print("⚠️ LANGCHAIN_API_KEY missing! Get key: https://smith.langchain.com/settings")
app = FastAPI(title="🇫🇷 French Energy RAG API")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
rag = EnergyRAG()

class QueryRequest(BaseModel):
    query: str
    session_id: str = "streamlit_default"  # ← Enables conversation memory
    time_intent: str | None = None

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
            age_min = (datetime.now(pytz.timezone("Europe/Paris")) - 
                      record_time.astimezone(pytz.timezone("Europe/Paris"))).total_seconds() / 60
            has_fresh_data = age_min < 120
        except:
            pass
    
    return {
        "has_fresh_data": has_fresh_data,
        "data_age_min": round(age_min, 1) if age_min else None,
        "latest_record": latest,
        "db_record_count": rag.context_builder.summarizer.db.get_record_count()
    }