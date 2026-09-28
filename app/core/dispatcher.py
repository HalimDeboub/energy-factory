# app/core/dispatcher.py
#
# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT DISPATCHER — The Hybrid RAG Hub
# ═══════════════════════════════════════════════════════════════════════════
#
# This is the central hub that orchestrates multiple data sources.
# It receives the user query and intent, then decides which providers to
# consult to build the perfect context for the LLM.
#
# ═══════════════════════════════════════════════════════════════════════════

from typing import List, Dict, Any, Optional
from app.core.base import BaseDataProvider, BaseKnowledgeProvider


class ContextDispatcher:
    """
    Orchestrates multiple Data and Knowledge providers to build a hybrid context.
    """

    def __init__(
        self, 
        data_providers: List[BaseDataProvider] = None,
        knowledge_providers: List[BaseKnowledgeProvider] = None
    ):
        self.data_providers = data_providers or []
        self.knowledge_providers = knowledge_providers or []

    def build_hybrid_context(
        self, 
        query: str, 
        time_layers: List[str], 
        topics: List[str],
        company_id: str = "system_global"
    ) -> str:
        """
        Gathers context from all relevant sources and combines them.
        """
        context_parts = []

        # ── Part 1: Gather Numerical Data ─────────────────────────────────
        if time_layers or topics:
            for dp in self.data_providers:
                # Security Check: Only fetch if provider belongs to company or is system_global
                if dp.company_id != "system_global" and dp.company_id != company_id:
                    continue

                try:
                    data_context = dp.fetch_context(time_layers, topics)
                    if data_context:
                        context_parts.append(data_context)
                except Exception as e:
                    print(f" [Dispatcher] Provider {dp.provider_name} failed: {e}")

        # ── Part 2: Gather Documentation/Knowledge ────────────────────────
        # We always check knowledge providers if the query seems conceptual
        # or doesn't have clear numerical time layers.
        # (Simplified logic: always call them for now, top_k=2 for brevity)
        for kp in self.knowledge_providers:
            knowledge_context = kp.query_knowledge(query)
            if knowledge_context:
                context_parts.append(knowledge_context)

        if not context_parts:
            return "⚠️ No relevant data or documentation found for this query."

        return "\n\n" + ("\n" + "="*40 + "\n").join(context_parts)
