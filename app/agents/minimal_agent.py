# app/agents/minimal_agent.py - MINIMAL WORKING VERSION
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# For LangChain 1.2.4, use these imports:
try:
    # Try the most common locations
    from langchain.agents.agent_executor import AgentExecutor
    from langchain.agents.react.base import create_react_agent
    print("✓ Using standard LangChain 1.2.4 imports")
except ImportError:
    # Fallback
    print("⚠️ Using fallback imports")
    
    class AgentExecutor:
        def __init__(self, agent, tools, **kwargs):
            self.agent = agent
            self.tools = tools
        def invoke(self, inputs):
            return {"output": f"Analyzed: {inputs.get('input', 'unknown')}"}
    
    def create_react_agent(llm, tools, prompt):
        class SimpleAgent:
            def __init__(self, tools):
                self.tools = tools
            def run(self, input_text):
                return f"Simple analysis: {input_text}"
        return SimpleAgent(tools)

from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

class MinimalDataAnalyst:
    def __init__(self):
        # Simple tools
        self.tools = [
            Tool(
                name="get_energy_data",
                func=self._get_energy_data,
                description="Get energy data from France"
            )
        ]
        
        # Simple prompt
        prompt = PromptTemplate.from_template("Analyze: {input}")
        
        # Create agent
        agent = create_react_agent(
            llm=self._get_mock_llm(),
            tools=self.tools,
            prompt=prompt
        )
        
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )
    
    def _get_mock_llm(self):
        """Mock LLM for testing"""
        class MockLLM:
            def invoke(self, text):
                return "Mock LLM response"
        return MockLLM()
    
    def _get_energy_data(self, query=""):
        """Mock data function"""
        return "France electricity: 50000 MW total, Nuclear: 30000 MW"
    
    def analyze(self, query):
        try:
            result = self.executor.invoke({"input": query})
            return result['output']
        except Exception as e:
            return f"Analysis: {query} (Error: {str(e)})"

# Test the agent
if __name__ == "__main__":
    agent = MinimalDataAnalyst()
    print(agent.analyze("What is France's energy production?"))