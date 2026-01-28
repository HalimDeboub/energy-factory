# app/agents/renewable_expert.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
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
        
        # Create prompt
        prompt_template = """You are a Renewable Energy Expert specializing in France's electricity grid.
        
        Available tools:
        {tools}
        
        Use this format:
        Question: {input}
        Thought: {agent_scratchpad}
        """
        
        self.prompt = PromptTemplate.from_template(prompt_template)
        
        # Create agent
        agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=self.prompt)
        
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def analyze(self, query: str):
        """Execute agent with query"""
        try:
            result = self.agent_executor.invoke({"input": query})
            return result['output']
        except Exception as e:
            return f"Error in analysis: {str(e)}"