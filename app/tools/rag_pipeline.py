from typing import Dict, Any, Optional
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # 🔑 Critical for memory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime  # 🔑 For diagnostics

from app.config.config import OLLAMA_HOST, OLLAMA_MODEL
from app.tools.context_builder import ContextBuilder

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
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un expert énergétique français. Réponds STRICTEMENT en français.

Consignes :
1. Cite TOUJOURS l'heure exacte des données (ex: "À 19:30")
2. Précise "données RTE éCO2mix (H-2)"
3. N'invente JAMAIS de chiffres – utilise uniquement le contexte fourni"""),
            MessagesPlaceholder(variable_name="chat_history"),  # 🔑 REQUIRED for memory
            ("human", "Contexte RTE :\n{context}\n\nQuestion :\n{input}")  # 🔑 MUST be "input"
        ])
        
        # ✅ UNIVERSAL FIX: Avoid assign() entirely - works in ALL LangChain versions
       # app/tools/rag_pipeline.py → inside EnergyRAG.__init__()
        def add_context(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Add RTE context to input dict (version-agnostic)"""
            # 🔑 CRITICAL: Chain already passes {"input": "..."} - just pass through to context builder
            inputs["context"] = self.context_builder.build_for_query(inputs)  # ← Pass entire dict
            return inputs


        
        # Base chain WITHOUT memory (context retrieval only)
        self.base_chain = (
            RunnableLambda(add_context)
            | self.prompt
            | self.llm
            | StrOutputParser()  # Clean string output for history saving
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
            
            # ✅ Invoke with session config - THIS TRIGGERS history save/load
            print(f"🔍 Querying with session '{session_id}': '{user_query[:50]}...'")
            result = chain_with_memory.invoke(
                inputs,
                config={"configurable": {"session_id": session_id}}
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