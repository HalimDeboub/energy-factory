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
    num_ctx=2048,
    num_predict=300,   # 👈 add this
    request_timeout=120.0,
        ).with_retry(stop_after_attempt=2)
        
        # ✅ CORRECT PROMPT: MUST include MessagesPlaceholder for history injection
        # app/tools/rag_pipeline.py → EnergyRAG.__init__()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """SYSTEM STATE:
• Fresh data available: {has_fresh_data}
You are EcoBot, an energy expert.

Your task is to extract and report factual values from the  context. 
DO NOT invent, estimate, or use placeholders always mention the date of the data you are using also the time.

-------------------
RULES
-------------------

1. STRICT LAYER SELECTION:
- "today/current/now" → ONLY use IMMEDIATE or TODAY section do not mention the other sections unless explicitly asked for them
- "yesterday" → ONLY use YESTERDAY section do not mention the other sections unless explicitly asked for them
- "last week/7 days" → ONLY use SHORT TERM HISTORICAL BASELINE do not mention the other sections unless explicitly asked for them
- "last month/30 days" → ONLY use LONG TERM HISTORICAL BASELINE do not mention the other sections unless explicitly asked for them
- NEVER use other sections unless explicitly asked for them

2. DATA EXTRACTION (CRITICAL):
- Extract real values exactly as written in the context
- Fields to extract when available:
  • timestamp
  • consumption (MW)
  • peak demand (MW + time)
  • nuclear production (MW)
  • wind (MW)
  • solar (MW)
  • renewable share (%)
  • CO2 intensity (g/kWh)

- If a field is missing → say: "Data not available"

- NEVER output placeholders like "X MW", "hh:mm", etc.

3. FRESHNESS:
- If fresh data = false:
  → "Data not updated for X minutes"

- If real-time missing:
  → "⚠️ Real-time data not yet published (last measurement: X minutes ago). Next RTE update in ~15 min."

4. OUT-OF-SCOPE:
- Beyond 90 days:
  → "Detailed historical data beyond 90 days is available in this reports section."

5. RESPONSE FORMAT:

- Use ONLY real extracted values
- Format example:

"At 14:30 pm on 20 April 2026 , the consumption was 52,300 MW. 
Peak demand reached 58,200 MW at 19:10. 
Nuclear production was 41,000 MW. 
Wind generated 5,200 MW and solar 3,100 MW. 
Renewables contributed 18%. 
CO₂ intensity was 45 g/kWh."

- If any value missing → replace sentence with:
  "Data not available"

6. NEVER:
- invent numbers
- use placeholders
- mention other layers
- explain reasoning
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