# app/agents/supervisor.py
from langchain_core.prompts import ChatPromptTemplate
from app.llm_setup import LLMFactory

class SupervisorAgent:
    def __init__(self):
        llm_factory = LLMFactory()
        self.llm = llm_factory.get_llm(temperature=0)
        
    def route_query(self, query: str) -> str:
        """Determine which agent should handle the query"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a supervisor that routes energy questions to the right expert.
            Available agents:
            1. data_analyst - For general data, production, consumption, energy mix
            2. renewable_expert - For solar, wind, hydro, renewable energy questions
            3. forecaster - For predictions, forecasts, trends
            4. policy_analyst - For policy, regulations, environmental impact
            
            Return only the agent name."""),
            ("human", "{query}")
        ])
        
        chain = prompt | self.llm
        return chain.invoke({"query": query}).content.strip().lower()