from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from rag_pipeline import EnergyRAG
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



app = FastAPI(
    title="Local RAG API",
    description="A local Retrieval-Augmented Generation API for energy data analysis",
    version="1.0.0"
)
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


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Local RAG API for Energy Data Analysis"} 


@app.post("/analyze")
async def analyze_query(query: str):
    # Placeholder for RAG analysis logic
    # In a real implementation, this would involve retrieving relevant documents
    # and generating a response using a language model.
    return {
        "query": query,
        "analysis": "This is a placeholder response for the query analysis."
    }   
@app.post("/analyze-energy")  
async def analyze_energy(query: Query):
    try:
       rag = EnergyRAG()
       result = rag.query(query.query)
       return {
              "status": "success",
              "query": query.query,
              "analysis": result,
              "timestamp": datetime.now().isoformat()}
        
        # return {
        #     "status": "success",
        #     "query": query.query,
        #     "analysis": result.get("result+++", ""),
        #     "agent_used": result.get("agent_used", "unknown"),
        #     "timestamp": datetime.now().isoformat()
        # }
    except Exception as e:
        logger.error(f"Error+++: {e}")
        return {"status": "error", "message": str(e)}
