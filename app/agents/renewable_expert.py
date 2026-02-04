# app/agents/renewable_expert.py - FIXED FOR LANGCHAIN 1.2.4
# Try different import patterns
try:
    from langchain.agents.agent_executor import AgentExecutor
except ImportError:
    try:
        from langchain.agents import AgentExecutor
    except ImportError:
        raise ImportError("Could not import AgentExecutor")

try:
    from langchain.agents import create_tool_calling_agent
except ImportError:
    try:
        from langchain.agents.react.base import create_react_agent as create_tool_calling_agent
    except ImportError:
        raise ImportError("Could not find create_tool_calling_agent or create_react_agent")

from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from app.llm_setup import LLMFactory
from app.tools.data_tools import Eco2mixDataTools

class RenewableExpertAgent:
    def __init__(self):
        llm_factory = LLMFactory()
        self.llm = llm_factory.get_llm(temperature=0.1)
        self.data_tools = Eco2mixDataTools()
        
        # Define tools
        self.tools = [
            Tool(
                name="get_real_time_data",
                func=self.data_tools.get_real_time_data,
                description="Get real-time energy data from France's grid"
            ),
            Tool(
                name="get_energy_mix",
                func=self.data_tools.get_energy_mix,
                description="Get energy mix percentages for a specific date"
            )
        ]
        
        # Create prompt for LangChain 1.x
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Renewable Energy Expert specializing in France's electricity grid.
            Focus on solar, wind, hydro, and other renewable sources.
            Analyze trends, provide insights about renewable energy adoption and impact."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        # Create agent using new API
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            early_stopping_method="generate"
        )
    
    def analyze(self, query: str):
        """Execute agent with query"""
        try:
            result = self.agent_executor.invoke({"input": query})
            return result['output']
        except Exception as e:
            return f"Error in analysis: {str(e)}"