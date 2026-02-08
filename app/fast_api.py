from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.tools.rag_pipeline import EnergyRAG
from datetime import datetime  # 🔑 CRITICAL: Was missing!

app = FastAPI(title="🇫🇷 French Energy RAG API")
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
        raise HTTPException(
            status_code=500,
            detail=f"RAG failed: {str(e)[:100]}"
        )

@app.get("/health")
async def health():
    return {"status": "healthy", "eco2mix_api": "operational"}