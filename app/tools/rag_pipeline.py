from typing import Dict, Any, Optional
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.config.config import OLLAMA_HOST, OLLAMA_MODEL
from app.tools.context_builder import ContextBuilder

class EnergyRAG:
    def __init__(self):
        self.context_builder = ContextBuilder()
        
        # SOLVES: Transient Ollama failures (Docker networking flakiness)
        self.llm = OllamaLLM(
            base_url=OLLAMA_HOST,
            model=OLLAMA_MODEL,
            temperature=0.3,
            num_ctx=4096,
            request_timeout=120.0,
        ).with_retry(  # ← Auto-retry on connection errors
            stop_after_attempt=2,
        )
        
        # SOLVES: Clear system instructions + human-readable context separation
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un expert énergétique français. Réponds STRICTEMENT en français.

Consignes critiques :
1. Cite TOUJOURS l'heure exacte des données (ex: "À 19:30")
2. Précise "données temps réel préliminaires RTE éCO2mix (H-2)"
3. N'invente JAMAIS de chiffres – utilise uniquement le contexte fourni
4. Si données absentes : dis "Données indisponibles pour cet horaire" (pas de spéculations)"""),
            ("human", "Contexte RTE :\n{context}\n\nQuestion :\n{query}"),
        ])
        
        # SOLVES: Integrated context retrieval (no manual context building per query)
        def retrieve_context(inputs: Dict[str, Any]) -> str:
            """LangChain-compatible context retrieval"""
            query = inputs["query"]
            time_intent = inputs.get("time_intent")  # Optional
            return self.context_builder.build_for_query(query, time_intent)
        
        # 🔑 SINGLE REUSABLE CHAIN (enables LangSmith tracing)
        self.chain = (
            RunnablePassthrough.assign(
                context=RunnableLambda(retrieve_context)
            )
            | self.prompt
            | self.llm
            | StrOutputParser()  # ← Clean string output (no Ollama metadata)
        )
    
    def query(self, user_query: str, time_intent: Optional[str] = None) -> str:
        """Production-ready query with graceful error handling"""
        try:
            inputs = {"query": user_query}
            if time_intent:
                inputs["time_intent"] = time_intent
            
            # LangSmith auto-traces this if env vars set
            return self.chain.invoke(inputs)
            
        except Exception as e:
            # SOLVES: Don't crash on Ollama downtime – degrade gracefully
            error_type = type(e).__name__
            user_msg = (
                f"⚠️ Données énergétiques temporairement indisponibles ({error_type}).\n"
                "→ Dernières données RTE stockées il y a moins de 15 min restent consultables.\n"
                "→ Réessayez dans 1 minute ou consultez https://www.rte-france.com/eco2mix"
            )
            print(f"RAG error [{error_type}]: {str(e)[:150]}")
            return user_msg