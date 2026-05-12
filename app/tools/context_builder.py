# # app/tools/context_builder.py
# from app.tools.context_summarizer import ContextSummarizer

# class ContextBuilder:
#     def __init__(self):
#         self.summarizer = ContextSummarizer()
    
#     def build_for_query(self, inputs: str | dict, time_intent: str | None = None) -> str:
#         """
#         DELEGATE to summarizer – NO time intent parsing here!
#         Works for ANY query phrasing because summarizer always provides rich context.
#         """
        
        
        
#         # Handle both direct string calls AND chain dict inputs
#         if isinstance(inputs, dict):
#             query = inputs.get("input", "")  # LangChain requires "input" key
#         else:
#             query = str(inputs)
        
#         if not query.strip():
#             return "⚠️ Question vide"
#         context = self.summarizer.build_context(query)
        
#         print(context)  # Debug: See full context returned by summarizer
#         # ✅ CRITICAL: No parsing – just pass query to summarizer
#         return context if context else "⚠️ Contexte indisponible"
# app/tools/context_builder.py

from typing import Dict, Any
from app.tools.context_summarizer import ContextSummarizer


class ContextBuilder:
    def __init__(self):
        self.summarizer = ContextSummarizer()

    def build_for_query(self, inputs: Dict[str, Any], intent: Dict[str, Any]) -> str:
        query = inputs.get("input", "")

        # Merge time + comparison layers
        layers = set(intent.get("time_range", []))
        layers.update(intent.get("compare_with", []))

        if not layers:
            layers = {"today"}

        context = self.summarizer.build_context(query, list(layers))

        print(f"🧠 Selected layers: {layers}")
        print(f"📦 Context built:\n{context[:300]}...\n")

        return context if context else "⚠️ Contexte indisponible"