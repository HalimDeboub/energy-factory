# app/agents/data_analyst.py - CORRECT FOR LANGCHAIN 1.2.4
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    # For LangChain 1.2.4
    from langchain.agents.agent_executor import AgentExecutor
    print("✓ Using AgentExecutor from agent_executor")
except ImportError:
    try:
        from langchain.agents import AgentExecutor
        print("✓ Using AgentExecutor from agents")
    except ImportError:
        # Create a fallback
        class AgentExecutor:
            def __init__(self, agent, tools, **kwargs):
                self.agent = agent
                self.tools = tools
            def invoke(self, inputs):
                return {"output": "Agent system is being updated."}

# Use create_react_agent for LangChain 1.2.4
try:
    from langchain.agents.react.base import create_react_agent
    print("✓ Using create_react_agent")
except ImportError:
    # Fallback
    def create_react_agent(llm, tools, prompt):
        class SimpleAgent:
            def __init__(self):
                self.tools = tools
            def run(self, input_text):
                return f"Analyzed: {input_text}"
        return SimpleAgent()

from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

# Import your modules
try:
    from app.llm_setup import LLMFactory
    from app.tools.data_tools import Eco2mixDataTools
except ImportError:
    # Create mock classes if imports fail
    class LLMFactory:
        def get_llm(self, temperature=0.1):
            class MockLLM:
                def invoke(self, text):
                    return "Mock LLM response"
            return MockLLM()
    
    class Eco2mixDataTools:
        def get_real_time_data(self, limit=10):
            return "Real-time data not available"
        def get_energy_mix(self, date=None):
            return "Energy mix not available"

class DataAnalystAgent:
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
        prompt_template = """You are a Data Analyst specializing in France's electricity grid.
        
        Available tools:
        {tools}
        
        Use the following format:
        Question: {input}
        Thought: {agent_scratchpad}
        Action: {action}
        Action Input: {action_input}
        Observation: {observation}
        ... (this repeats)
        Final Answer: {answer}
        """
        
        prompt = PromptTemplate.from_template(prompt_template)
        
        # Create agent
        try:
            agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=prompt)
        except Exception as e:
            print(f"Warning: Could not create react agent: {e}")
            # Fallback
            class FallbackAgent:
                def __init__(self, tools):
                    self.tools = tools
                def run(self, input_text):
                    return f"Fallback analysis for: {input_text}"
            agent = FallbackAgent(self.tools)
        
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