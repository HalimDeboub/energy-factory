# app/workflows/energy_graph.py
from typing import TypedDict
from langgraph.graph import StateGraph, END

# Define state
class AgentState(TypedDict):
    query: str
    result: str
    agent_used: str

class EnergyWorkflow:
    def __init__(self):
        # Import agents here to avoid circular imports
        from app.agents.data_analyst import DataAnalystAgent
        from app.agents.renewable_expert import RenewableExpertAgent
        
        self.data_analyst = DataAnalystAgent()
        self.renewable_expert = RenewableExpertAgent()
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("data_analyst", self.data_analyst_node)
        workflow.add_node("renewable_expert", self.renewable_expert_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self.route_to_agent,
            {
                "data_analyst": "data_analyst",
                "renewable_expert": "renewable_expert"
            }
        )
        
        # End after agent
        workflow.add_edge("data_analyst", END)
        workflow.add_edge("renewable_expert", END)
        
        self.app = workflow.compile()
    
    def supervisor_node(self, state: AgentState):
        """Route query to appropriate agent"""
        query = state['query'].lower()
        
        # Simple routing logic
        if any(word in query for word in ['solar', 'wind', 'renewable', 'green', 'clean']):
            return {"agent_used": "renewable_expert"}
        else:
            return {"agent_used": "data_analyst"}
    
    def route_to_agent(self, state: AgentState):
        """Determine which agent to use"""
        return state['agent_used']
    
    def data_analyst_node(self, state: AgentState):
        """Execute data analyst agent"""
        result = self.data_analyst.analyze(state['query'])
        return {
            "result": result,
            "agent_used": "data_analyst"
        }
    
    def renewable_expert_node(self, state: AgentState):
        """Execute renewable expert agent"""
        result = self.renewable_expert.analyze(state['query'])
        return {
            "result": result,
            "agent_used": "renewable_expert"
        }
    
    def run(self, query: str):
        """Execute workflow with query"""
        initial_state = AgentState(
            query=query,
            result="",
            agent_used=""
        )
        return self.app.invoke(initial_state)