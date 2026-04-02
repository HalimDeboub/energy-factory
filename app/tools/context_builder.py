# app/tools/context_builder.py
from app.tools.context_summarizer import ContextSummarizer

class ContextBuilder:
    def __init__(self):
        self.summarizer = ContextSummarizer()
    
    def build_for_query(self, inputs: str | dict, time_intent: str | None = None) -> str:
        """
        DELEGATE to summarizer – NO time intent parsing here!
        Works for ANY query phrasing because summarizer always provides rich context.
        """
        
        
        
        # Handle both direct string calls AND chain dict inputs
        if isinstance(inputs, dict):
            query = inputs.get("input", "")  # LangChain requires "input" key
        else:
            query = str(inputs)
        
        if not query.strip():
            return "⚠️ Question vide"
        context = self.summarizer.build_context(query)
        
        print(context)  # Debug: See full context returned by summarizer
        # ✅ CRITICAL: No parsing – just pass query to summarizer
        return context if context else "⚠️ Contexte indisponible"