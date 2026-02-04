# app/agents/policy_analyst.py
from app.tools.rag_tools import EnergyRAGTools

class PolicyAnalystAgent:
    def __init__(self):
        llm_factory = LLMFactory()
        self.llm = llm_factory.get_llm(temperature=0.2)
        self.rag_tools = EnergyRAGTools()
        
        self.tools = [
            Tool(
                name="search_energy_policies",
                func=self.rag_tools.search_energy_policies,
                description="Search energy policy documents"
            ),
            Tool(
                name="get_regulatory_framework",
                func=self.rag_tools.get_regulatory_framework,
                description="Get information about energy regulations"
            )
        ]