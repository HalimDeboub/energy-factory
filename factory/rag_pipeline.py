from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from config import OLLAMA_HOST, OLLAMA_MODEL
from context_builder import ContextBuilder

class EnergyRAG:
    def __init__(self):
        self.llm = OllamaLLM(
            base_url=OLLAMA_HOST,
            model=OLLAMA_MODEL,
            temperature=0.3,
            num_ctx=4096  # Critical for handling time-series context
        )
        self.context_builder = ContextBuilder()
        self.prompt = ChatPromptTemplate.from_template(
            """Tu es un expert énergétique français. Réponds en français avec précision.

Contexte des données RTE éCO2mix (source officielle) :
{context}

Question de l'utilisateur :
{query}

Consignes :
1. Cite toujours l'heure exacte des données utilisées
2. Précise que les données sont "temps réel préliminaires" (non consolidées)
3. Si les données sont absentes pour l'heure demandée, dis-le clairement
4. N'invente jamais de chiffres - utilise uniquement le contexte fourni
5. Pour les tendances, compare uniquement les données du contexte (pas de spéculations)

Réponse :"""
        )
    
    def query(self, user_query, time_intent=None):
        context = self.context_builder.build_for_query(user_query, time_intent)
        chain = self.prompt | self.llm
        print(context)
        return chain.invoke({"context": context, "query": user_query})