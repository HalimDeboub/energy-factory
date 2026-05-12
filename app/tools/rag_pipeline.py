# from typing import Dict, Any, Optional
# from langchain_ollama import OllamaLLM
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # 🔑 Critical for memory
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnableLambda
# from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain_core.chat_history import BaseChatMessageHistory
# from langchain_community.chat_message_histories import ChatMessageHistory
# from datetime import datetime  # 🔑 For diagnostics
# import pytz
# from app.config.config import OLLAMA_HOST, OLLAMA_MODEL
# from app.tools.context_builder import ContextBuilder
#  # For monitoring and debugging

# class EnergyRAG:
#     def __init__(self):
#         self.context_builder = ContextBuilder()
        
        
#         # LLM with retries
#         self.llm = OllamaLLM(
#           base_url=OLLAMA_HOST,
#     model=OLLAMA_MODEL,
#     temperature=0.3,
#     num_ctx=2048,
#     num_predict=300,   # 👈 add this
#     request_timeout=120.0,
#         ).with_retry(stop_after_attempt=2)
        
#         # ✅ CORRECT PROMPT: MUST include MessagesPlaceholder for history injection
#         # app/tools/rag_pipeline.py → EnergyRAG.__init__()
#         self.prompt = ChatPromptTemplate.from_messages([
#             ("system", """SYSTEM STATE:
# • Fresh data available: {has_fresh_data}
# You are EcoBot, an energy expert.

# Your task is to extract and report factual values from the  context. 
# DO NOT invent, estimate, or use placeholders always mention the date of the data you are using also the time.

# -------------------
# RULES
# -------------------

# 1. STRICT LAYER SELECTION:
# - "today/current/now" → ONLY use IMMEDIATE or TODAY section do not mention the other sections unless explicitly asked for them
# - "yesterday" → ONLY use YESTERDAY section do not mention the other sections unless explicitly asked for them
# - "last week/7 days" → ONLY use SHORT TERM HISTORICAL BASELINE do not mention the other sections unless explicitly asked for them
# - "last month/30 days" → ONLY use LONG TERM HISTORICAL BASELINE do not mention the other sections unless explicitly asked for them
# - NEVER use other sections unless explicitly asked for them

# 2. DATA EXTRACTION (CRITICAL):
# - Extract real values exactly as written in the context
# - Fields to extract when available:
#   • timestamp
#   • consumption (MW)
#   • peak demand (MW + time)
#   • nuclear production (MW)
#   • wind (MW)
#   • solar (MW)
#   • renewable share (%)
#   • CO2 intensity (g/kWh)

# - If a field is missing → say: "Data not available"

# - NEVER output placeholders like "X MW", "hh:mm", etc.

# 3. FRESHNESS:
# - If fresh data = false:
#   → "Data not updated for X minutes"

# - If real-time missing:
#   → "⚠️ Real-time data not yet published (last measurement: X minutes ago). Next RTE update in ~15 min."

# 4. OUT-OF-SCOPE:
# - Beyond 90 days:
#   → "Detailed historical data beyond 90 days is available in this reports section."

# 5. RESPONSE FORMAT:

# - Use ONLY real extracted values
# - Format example:

# "At 14:30 pm on 20 April 2026 , the consumption was 52,300 MW. 
# Peak demand reached 58,200 MW at 19:10. 
# Nuclear production was 41,000 MW. 
# Wind generated 5,200 MW and solar 3,100 MW. 
# Renewables contributed 18%. 
# CO₂ intensity was 45 g/kWh."

# - If any value missing → replace sentence with:
#   "Data not available"

# 6. NEVER:
# - invent numbers
# - use placeholders
# - mention other layers
# - explain reasoning
# {context}"""),
#             MessagesPlaceholder(variable_name="chat_history"),  # 🔑 REQUIRED for memory injection
#             ("human", "Question de l'utilisateur :\n{input}")
#         ])
        
#         # ✅ UNIVERSAL FIX: Avoid assign() entirely - works in ALL LangChain versions
#        # app/tools/rag_pipeline.py → inside EnergyRAG.__init__()
#         def add_context(inputs: Dict[str, Any]) -> Dict[str, Any]:
#             """Add RTE context to input dict (version-agnostic)"""
#             # 🔑 CRITICAL: Chain already passes {"input": "..."} - just pass through to context builder
#             inputs["context"] = self.context_builder.build_for_query(inputs)  # ← Pass entire dict
#             return inputs


        
#         # Base chain WITHOUT memory (context retrieval only)
#        # Inside EnergyRAG.__init__() - AFTER base_chain definition
#         self.base_chain = (
#             RunnableLambda(add_context).with_config(run_name="ContextRetrieval")  # 🔑 ADD THIS
#             | self.prompt.with_config(run_name="PromptFormatting")  # 🔑 ADD THIS
#             | self.llm.with_config(run_name="LLMGeneration")  # 🔑 ADD THIS
#             | StrOutputParser().with_config(run_name="OutputParsing")
#         )
        
#         # In-memory session store (per user/conversation)
#         self.chat_histories: Dict[str, BaseChatMessageHistory] = {}
    
#     def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
#         """Get or create chat history for session"""
#         if session_id not in self.chat_histories:
#             print(f"🆕 Created new session: {session_id}")
#             self.chat_histories[session_id] = ChatMessageHistory()
#         else:
#             hist = self.chat_histories[session_id]
#             print(f"💬 Session {session_id} has {len(hist.messages)} message(s) in history")
#         return self.chat_histories[session_id]
    
#     def query(self, user_query: str, session_id: str = "default", time_intent: Optional[str] = None) -> str:
        
#         """
#         Query with conversation memory.
#         Memory is ACTIVE when session_id is provided (same session_id = same conversation).
#         """
#         try:
#             has_fresh_data = False  # Default safe state
#             age_min = None
#             latest = None
#             metadata = {
#                 "session_id": session_id,
#                 "has_fresh_data": has_fresh_data,
#                 "data_age_min": round(age_min, 1) if latest else None,
#                 "db_record_count": self.context_builder.summarizer.db.get_record_count(),
#                 "time_intent": time_intent or "auto"
#             }
           
                        
                        
            
            
#             # ✅ CRITICAL: Wrap chain WITH MEMORY on EVERY call
#             chain_with_memory = RunnableWithMessageHistory(
#                 self.base_chain,
#                 self.get_session_history,
#                 input_messages_key="input",        # Must match prompt's {input}
#                 output_messages_key="output",       # Default - saves AI response
#                 history_messages_key="chat_history",  # Must match MessagesPlaceholder name
#             )
            
#             # ✅ Inputs MUST use "input" key (required by RunnableWithMessageHistory)
#             inputs = {"input": user_query}
#             if time_intent:
#                 inputs["time_intent"] = time_intent
            
#             latest = self.context_builder.summarizer.db.get_latest_record()
#             if latest:
#                 record_time = datetime.fromisoformat(latest["date_heure"].replace('Z','+00:00'))
#                 age_min = (datetime.now(pytz.timezone("Africa/Algiers")) - record_time.astimezone(pytz.timezone("Africa/Algiers"))).total_seconds() / 60
#                 has_fresh_data = age_min < 420  # Fresh if <2h old
#             else:
#                 has_fresh_data = False
           

#             # Inject state into prompt
#             inputs["has_fresh_data"] = has_fresh_data
           
#             # ✅ Invoke with session config - THIS TRIGGERS history save/load
#             print(f"🔍 Querying with session '{session_id}': '{user_query[:50]}...'")
#             result = chain_with_memory.invoke(
#                 inputs,
#                 config={"configurable": {"session_id": session_id},
#                         "metadata": metadata}
                
#             )
#             print(f"✅ Response: '{result[:60]}...'")
#             return result
            
#         except Exception as e:
#             error_type = type(e).__name__
#             print(f"❌ RAG error [{error_type}]: {str(e)[:150]}")
#             import traceback; traceback.print_exc()
#             return (
#                 f"⚠️ Erreur système ({error_type}). Réessayez dans 1 minute.\n"
#                 f"(Débogage: {str(e)[:60]})"
#             )
from typing import Dict, Any, Optional
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from datetime import datetime
import pytz

from app.config.config import OLLAMA_HOST, OLLAMA_MODEL, FETCH_INTERVAL_MINUTES
from app.core.dispatcher import ContextDispatcher
from app.providers.data.rte_provider import RTEDataProvider
from app.providers.knowledge.pdf_provider import PDFKnowledgeProvider
from app.agents.time_intent_parser import TimeIntentParser, FALLBACK_INTENT
from app.tools.response_cache import ResponseCache
from app.tools.query_logger import QueryLogger, QueryTimer
from app.agents.topic_intent_parser import TopicIntentParser


class EnergyRAG:
    def __init__(self):
        # ── Data & Knowledge Providers ────────────────────────────────────
        # These are the "Sources" our tool can talk to.
        # To add a new country or source, just add a new provider here.
        self.dispatcher = ContextDispatcher(
            data_providers=[RTEDataProvider()],
            knowledge_providers=[PDFKnowledgeProvider()]
        )

        self.llm = OllamaLLM(
            base_url=OLLAMA_HOST,
            model=OLLAMA_MODEL,
            temperature=0.3,
            num_ctx=2048,
            num_predict=300,
            request_timeout=120.0,
        ).with_retry(stop_after_attempt=2)

        # Time intent parser — resolves WHEN (which time layers to retrieve)
        self.intent_parser = TimeIntentParser(self.llm)

        # Topic intent parser — resolves WHAT (which energy metrics to focus on)
        # Keyword-based like TimeIntentParser, so zero extra LLM calls.
        self.topic_parser = TopicIntentParser()

        # ── Response cache ────────────────────────────────────────────────
        # TTL matches the data refresh interval so the cache is always
        # invalidated as soon as new eco2mix data arrives.
        self.cache = ResponseCache(ttl_minutes=FETCH_INTERVAL_MINUTES)

        # ── Query logger ──────────────────────────────────────────────────
        # Writes one NDJSON record per query to logs/query_log.jsonl.
        self.logger = QueryLogger()

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """\
You are EcoBot, a Global Energy AI Analyst. 

Your role is to provide precise, data-driven insights based on the provided energy context.
The context is gathered from multiple providers (real-time data, historical trends, and documentation).

RULES:
1. Use ONLY the data found in the context — never invent numbers.
2. Always mention the SOURCE and the exact TIMESTAMP of any figure you cite.
3. If data is missing for a requested topic, say "Data not available in the current source."
4. Maintain an objective, professional tone.

{focus_hint}

--- ENERGY CONTEXT ---
{context}
--- END CONTEXT ---
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        # ── Context injection step (runs inside the LangChain chain) ──────
        #
        # CONCEPT — Why is this a closure?
        # add_context is defined INSIDE __init__ so it closes over `self`.
        # That lets it access self.context_builder and self.intent_parser
        # without being passed as explicit arguments — LangChain's
        # RunnableLambda only passes the `inputs` dict.
        #
        # At this point intent is already resolved (done in query() before
        # the chain is invoked) and stored in inputs["_intent"].  We just
        # pop it here and use it to build the context.
        def add_context(inputs: Dict[str, Any]) -> Dict[str, Any]:

            # Pop the pre-resolved intent injected by query().
            # We pop (not get) so it is NOT forwarded to the prompt template
            # — the prompt only knows about {context} and {input}.
            intent = inputs.pop("_intent", None)

            if intent is None:
                # Fallback: should not happen in normal flow, but be safe
                intent = self.intent_parser.parse(inputs["input"])

            inputs["intent"] = intent

            # Build HYBRID context using the Dispatcher
            # It will automatically combine numbers (RTE) and words (PDFs)
            inputs["context"] = self.dispatcher.build_hybrid_context(
                query=inputs["input"],
                time_layers=intent.get("time_range", []),
                topics=intent.get("topics", [])
            )

            return inputs

        self.base_chain = (
            RunnableLambda(add_context)
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

        self.chat_histories: Dict[str, BaseChatMessageHistory] = {}

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = ChatMessageHistory()
        return self.chat_histories[session_id]

    def query(self, user_query: str, session_id: str = "default", time_intent: Optional[str] = None) -> str:
        """
        Query the energy RAG pipeline with conversation memory and response caching.

        ── Flow ──────────────────────────────────────────────────────────────

        1. Parse temporal intent  →  which time layers are needed
        2. Get latest DB timestamp  →  used as the cache version key
        3. Check cache  →  if HIT return instantly (no LLM call)
        4. Cache MISS  →  run full chain (context build + LLM inference)
        5. Store result in cache  →  next identical query will be instant

        WHY parse intent BEFORE the chain?
        The cache lookup needs the resolved layers as part of the cache key.
        If we parsed inside add_context() (inside the chain) we would not
        know the layers until AFTER the LLM already ran — too late to check.
        So we parse early, pass the result into inputs["_intent"], and
        add_context() reuses it instead of parsing again.

        Args:
            user_query:  Raw user question (English / French / Arabic).
            session_id:  Same session_id = shared conversation memory.
            time_intent: Unused — kept for FastAPI compatibility.

        Returns:
            EcoBot's answer as a string.
        """
        # QueryTimer is a context manager that measures wall-clock elapsed time.
        # We start it here so it covers the ENTIRE request including cache checks
        # and the LLM call — giving us true end-to-end latency per query.
        timer = QueryTimer()

        # Pre-declare variables so the except/finally blocks can always access them
        # even if an error occurs before they are assigned inside the try block.
        intent            = {**FALLBACK_INTENT}
        selected_layers   = ["today"]
        cache_hit         = False
        result            = None

        try:
            print(f"\n🔍 [RAG] session='{session_id}' | query='{user_query[:60]}'")

            with timer:

                # ── Step 1a: Resolve TEMPORAL intent (when?) ───────────────
                intent = self.intent_parser.parse(user_query)

                if intent["confidence"] < TimeIntentParser.CONFIDENCE_THRESHOLD:
                    print(
                        f"⚠️ [RAG] Low confidence ({intent['confidence']:.2f}), "
                        f"falling back to ['today']"
                    )
                    intent = {**FALLBACK_INTENT}

                selected_layers = list(
                    set(intent["time_range"]) | set(intent["compare_with"])
                )

                # ── Step 1b: Resolve TOPIC intent (what?) ──────────────────
                # Runs in microseconds — pure keyword matching, no LLM call.
                # Returns a focus_hint string that gets injected into the prompt.
                topic_result = self.topic_parser.parse(user_query)
                focus_hint   = topic_result["focus_hint"]  # may be empty string

                # ── Step 2: Get the current data version ──────────────────
                # We ask the primary data provider for its latest timestamp.
                # If this changes, the cache is considered stale.
                data_ts = ""
                if self.dispatcher.data_providers:
                    data_ts = self.dispatcher.data_providers[0].get_latest_timestamp()

                # ── Step 3: Cache lookup ───────────────────────────────────
                # Cache key includes topic so "nuclear now" and "wind now"
                # are cached separately even though they use the same layers.
                cache_key_layers = selected_layers + topic_result["topics"]
                cached_answer = self.cache.get(user_query, cache_key_layers, data_ts)
                if cached_answer is not None:
                    cache_hit = True
                    result    = cached_answer
                    print(f"⚡ [RAG] Serving from cache. Stats: {self.cache.stats}")

                else:
                    # ── Step 4: Cache MISS — run the full LLM pipeline ────
                    print(f"🤖 [RAG] Cache miss — running LLM (layers={selected_layers}, topics={topic_result['topics']})")

                    chain_with_memory = RunnableWithMessageHistory(
                        self.base_chain,
                        self.get_session_history,
                        input_messages_key="input",
                        history_messages_key="chat_history",
                    )

                    # ── What flows into the chain: ──────────────────────
                    # • input       → the user's question (required by LangChain)
                    # • _intent     → pre-resolved time intent (popped by add_context)
                    # • focus_hint  → topic focus instruction (read by the prompt template)
                    inputs = {
                        "input":      user_query,
                        "_intent":    intent,
                        "focus_hint": focus_hint,   # ← NEW: injected into {focus_hint} in prompt
                    }

                    result = chain_with_memory.invoke(
                        inputs,
                        config={"configurable": {"session_id": session_id}},
                    )

                    # ── Step 5: Store in cache ─────────────────────────────
                    self.cache.set(user_query, cache_key_layers, str(result), data_ts)

            # ── Step 6: Log the successful query ──────────────────────────
            # This runs AFTER the timer context, so timer.elapsed_ms is ready.
            self.logger.log(
                session_id        = session_id,
                query             = user_query,
                layers            = selected_layers,
                intent_confidence = intent["confidence"],
                cache_hit         = cache_hit,
                latency_ms        = timer.elapsed_ms,
                status            = "ok",
                answer            = str(result),
            )

            print(f"✅ [RAG] Done in {timer.elapsed_ms} ms | cache_hit={cache_hit} | Stats: {self.cache.stats}")
            return result

        except Exception as exc:
            import traceback
            print(f"❌ [RAG] Error [{type(exc).__name__}]: {exc}")
            traceback.print_exc()

            # Log the error — use elapsed_ms=0 if timer never started
            try:
                elapsed = timer.elapsed_ms
            except AttributeError:
                elapsed = 0

            self.logger.log(
                session_id        = session_id,
                query             = user_query,
                layers            = selected_layers,
                intent_confidence = intent["confidence"],
                cache_hit         = False,
                latency_ms        = elapsed,
                status            = "error",
                error             = f"{type(exc).__name__}: {str(exc)[:200]}",
            )

            return (
                f"⚠️ System error ({type(exc).__name__}). "
                "Please try again in a moment."
            )

    @property
    def cache_stats(self) -> Dict:
        """Expose cache statistics — useful for a /stats FastAPI endpoint."""
        return self.cache.stats

    @property
    def log_stats(self) -> Dict:
        """
        Expose query log statistics — wire to a FastAPI /stats endpoint.

        Returns metrics like:
          cache_hit_rate, avg_latency_ms, p95_latency_ms, top_layers, error_rate
        """
        return self.logger.stats()

    def get_logs(self, last_n: int = 50) -> list:
        """Return the last N log records (newest last)."""
        all_logs = self.logger.read_all()
        return all_logs[-last_n:]