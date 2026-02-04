# app/workflows/simple_workflow.py
from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.agents.simple_agent import SimpleEnergyAgent

class AgentState(TypedDict):
    query: str
    result: str
    agent_used: str

class SimpleEnergyWorkflow:
    def __init__(self):
        # Create agents
        self.data_analyst = SimpleEnergyAgent(agent_type="data_analyst")
        self.renewable_expert = SimpleEnergyAgent(agent_type="renewable_expert")
        
        # Build graph
        workflow = StateGraph(AgentState)
        
        workflow.add_node("router", self.router_node)
        workflow.add_node("data_analyst", self.data_analyst_node)
        workflow.add_node("renewable_expert", self.renewable_expert_node)
        
        workflow.set_entry_point("router")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "router",
            self.route_query,
            {
                "data_analyst": "data_analyst",
                "renewable_expert": "renewable_expert"
            }
        )
        
        workflow.add_edge("data_analyst", END)
        workflow.add_edge("renewable_expert", END)
        
        self.app = workflow.compile()
    
    def router_node(self, state: AgentState):
        """Route the query"""
        query = state['query'].lower()
        
        # Simple routing logic
        renewable_keywords = ['solar', 'wind', 'renewable', 'green', 'hydro', 'clean']
        if any(keyword in query for keyword in renewable_keywords):
            return {"agent_used": "renewable_expert"}
        else:
            return {"agent_used": "data_analyst"}
    
    def route_query(self, state: AgentState):
        """Determine next node"""
        return state['agent_used']
    
    def data_analyst_node(self, state: AgentState):
        """Data analyst analysis"""
        result = self.data_analyst.analyze(state['query'])
        return {
            "result": f"[Data Analyst] {result}",
            "agent_used": "data_analyst"
        }
    
    def renewable_expert_node(self, state: AgentState):
        """Renewable expert analysis"""
        result = self.renewable_expert.analyze(state['query'])
        return {
            "result": f"[Renewable Expert] {result}",
            "agent_used": "renewable_expert"
        }
    
    def run(self, query: str):
        """Execute workflow"""
        try:
            result = self.app.invoke({
                "query": query,
                "result": "",
                "agent_used": ""
            })
            return result
        except Exception as e:
            return {
                "result": f"Error in workflow: {str(e)}",
                "agent_used": "error"
            }