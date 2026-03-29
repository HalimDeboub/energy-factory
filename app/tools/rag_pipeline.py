from typing import Dict, Any, Optional
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # 🔑 Critical for memory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime  # 🔑 For diagnostics
import pytz
from app.config.config import OLLAMA_HOST, OLLAMA_MODEL
from app.tools.context_builder import ContextBuilder
 # For monitoring and debugging

class EnergyRAG:
    def __init__(self):
        self.context_builder = ContextBuilder()
        
        
        # LLM with retries
        self.llm = OllamaLLM(
            base_url=OLLAMA_HOST,
            model=OLLAMA_MODEL,
            temperature=0.3,
            num_ctx=4096,
            request_timeout=120.0,
        ).with_retry(stop_after_attempt=2)
        
        # ✅ CORRECT PROMPT: MUST include MessagesPlaceholder for history injection
        # app/tools/rag_pipeline.py → EnergyRAG.__init__()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un expert énergétique français. Analyse les COUCHES DE CONTEXTE RTE ci-dessous pour répondre avec précision.

        État du système :
• Données fraîches : {has_fresh_data}  ← STATE FLAG
    
Instructions :
- SI données fraîches = false → Dis "Données non mises à jour depuis X min"
- N'INVENTE JAMAIS de chiffres pour l'heure actuelle si données non fraîches
- Utilise uniquement les données fournies dans "Contexte RTE"
- Si données réelles indisponibles → dis EXACTEMENT :
   "⚠️ Données temps réel non encore publiées (dernière mesure: il y a X min). 
    Prochaine mise à jour RTE dans ~15 min."
-  N'UTILISE JAMAIS "désolé" ou "je ne peux pas"
- Pour comparaisons → dis "Comparaison indisponible : données historiques non fournies"


        COUCHES DE CONTEXTE FOURNIES :
        {context}"""),
            MessagesPlaceholder(variable_name="chat_history"),  # 🔑 REQUIRED for memory injection
            ("human", "Question de l'utilisateur :\n{input}")
        ])
        
        # ✅ UNIVERSAL FIX: Avoid assign() entirely - works in ALL LangChain versions
       # app/tools/rag_pipeline.py → inside EnergyRAG.__init__()
        def add_context(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Add RTE context to input dict (version-agnostic)"""
            # 🔑 CRITICAL: Chain already passes {"input": "..."} - just pass through to context builder
            inputs["context"] = self.context_builder.build_for_query(inputs)  # ← Pass entire dict
            return inputs


        
        # Base chain WITHOUT memory (context retrieval only)
       # Inside EnergyRAG.__init__() - AFTER base_chain definition
        self.base_chain = (
            RunnableLambda(add_context).with_config(run_name="ContextRetrieval")  # 🔑 ADD THIS
            | self.prompt.with_config(run_name="PromptFormatting")  # 🔑 ADD THIS
            | self.llm.with_config(run_name="LLMGeneration")  # 🔑 ADD THIS
            | StrOutputParser().with_config(run_name="OutputParsing")
        )
        
        # In-memory session store (per user/conversation)
        self.chat_histories: Dict[str, BaseChatMessageHistory] = {}
    
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for session"""
        if session_id not in self.chat_histories:
            print(f"🆕 Created new session: {session_id}")
            self.chat_histories[session_id] = ChatMessageHistory()
        else:
            hist = self.chat_histories[session_id]
            print(f"💬 Session {session_id} has {len(hist.messages)} message(s) in history")
        return self.chat_histories[session_id]
    
    def query(self, user_query: str, session_id: str = "default", time_intent: Optional[str] = None) -> str:
        
        """
        Query with conversation memory.
        Memory is ACTIVE when session_id is provided (same session_id = same conversation).
        """
        try:
            has_fresh_data = False  # Default safe state
            age_min = None
            latest = None
            metadata = {
                "session_id": session_id,
                "has_fresh_data": has_fresh_data,
                "data_age_min": round(age_min, 1) if latest else None,
                "db_record_count": self.context_builder.summarizer.db.get_record_count(),
                "time_intent": time_intent or "auto"
            }
           
                        
                        
            
            
            # ✅ CRITICAL: Wrap chain WITH MEMORY on EVERY call
            chain_with_memory = RunnableWithMessageHistory(
                self.base_chain,
                self.get_session_history,
                input_messages_key="input",        # Must match prompt's {input}
                output_messages_key="output",       # Default - saves AI response
                history_messages_key="chat_history",  # Must match MessagesPlaceholder name
            )
            
            # ✅ Inputs MUST use "input" key (required by RunnableWithMessageHistory)
            inputs = {"input": user_query}
            if time_intent:
                inputs["time_intent"] = time_intent
            
            latest = self.context_builder.summarizer.db.get_latest_record()
            if latest:
                record_time = datetime.fromisoformat(latest["date_heure"].replace('Z','+00:00'))
                age_min = (datetime.now(pytz.timezone("Africa/Algiers")) - record_time.astimezone(pytz.timezone("Africa/Algiers"))).total_seconds() / 60
                has_fresh_data = age_min < 420  # Fresh if <2h old
            else:
                has_fresh_data = False
            print(has_fresh_data, age_min)

            # Inject state into prompt
            inputs["has_fresh_data"] = has_fresh_data
            # ✅ Invoke with session config - THIS TRIGGERS history save/load
            print(f"🔍 Querying with session '{session_id}': '{user_query[:50]}...'")
            result = chain_with_memory.invoke(
                inputs,
                config={"configurable": {"session_id": session_id},
                        "metadata": metadata}
                
            )
            print(f"✅ Response: '{result[:60]}...'")
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            print(f"❌ RAG error [{error_type}]: {str(e)[:150]}")
            import traceback; traceback.print_exc()
            return (
                f"⚠️ Erreur système ({error_type}). Réessayez dans 1 minute.\n"
                f"(Débogage: {str(e)[:60]})"
            )