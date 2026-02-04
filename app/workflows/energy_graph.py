# app/workflows/energy_graph.py - WITH PROPER ERROR HANDLING
from typing import TypedDict
from langgraph.graph import StateGraph, END
import sys

class AgentState(TypedDict):
    query: str
    result: str
    agent_used: str

class EnergyWorkflow:
    def __init__(self):
        # Don't import agents in __init__ - do it lazily
        self.data_analyst = None
        self.renewable_expert = None
        self.agents_available = False
        
        # Check if we can import agents
        try:
            # Try to import one agent to check availability
            from app.agents.data_analyst import DataAnalystAgent
            self.agents_available = True
            print("✓ Agents are available")
        except ImportError as e:
            print(f"⚠️ Agents not available: {e}")
            print("Using fallback workflow")
            self.agents_available = False
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        if self.agents_available:
            # Add nodes with real agents
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
        else:
            # Simple fallback graph
            workflow.add_node("fallback", self.fallback_node)
            workflow.set_entry_point("fallback")
            workflow.add_edge("fallback", END)
        
        self.app = workflow.compile()
    
    def _get_data_analyst(self):
        """Lazy load data analyst agent"""
        if self.data_analyst is None and self.agents_available:
            try:
                from app.agents.data_analyst import DataAnalystAgent
                self.data_analyst = DataAnalystAgent()
            except Exception as e:
                print(f"Error loading DataAnalystAgent: {e}")
                self.agents_available = False
        return self.data_analyst
    
    def _get_renewable_expert(self):
        """Lazy load renewable expert agent"""
        if self.renewable_expert is None and self.agents_available:
            try:
                from app.agents.renewable_expert import RenewableExpertAgent
                self.renewable_expert = RenewableExpertAgent()
            except Exception as e:
                print(f"Error loading RenewableExpertAgent: {e}")
                self.agents_available = False
        return self.renewable_expert
    
    def supervisor_node(self, state: AgentState):
        """Route query to appropriate agent"""
        query = state['query'].lower()
        
        # Simple routing logic
        if any(word in query for word in ['solar', 'wind', 'renewable', 'green', 'clean', 'hydro']):
            return {"agent_used": "renewable_expert"}
        else:
            return {"agent_used": "data_analyst"}
    
    def route_to_agent(self, state: AgentState):
        """Determine which agent to use"""
        return state['agent_used']
    
    def data_analyst_node(self, state: AgentState):
        """Execute data analyst agent"""
        if not self.agents_available:
            return {"result": "Data analyst agent not available", "agent_used": "fallback"}
        
        agent = self._get_data_analyst()
        if agent:
            result = agent.analyze(state['query'])
            return {
                "result": result,
                "agent_used": "data_analyst"
            }
        else:
            return {"result": "Could not initialize data analyst", "agent_used": "fallback"}
    
    def renewable_expert_node(self, state: AgentState):
        """Execute renewable expert agent"""
        if not self.agents_available:
            return {"result": "Renewable expert agent not available", "agent_used": "fallback"}
        
        agent = self._get_renewable_expert()
        if agent:
            result = agent.analyze(state['query'])
            return {
                "result": result,
                "agent_used": "renewable_expert"
            }
        else:
            return {"result": "Could not initialize renewable expert", "agent_used": "fallback"}
    
    def fallback_node(self, state: AgentState):
        """Fallback analysis when agents are not available"""
        return {
            "result": "Agent system is being updated. Please check back soon!",
            "agent_used": "fallback"
        }
    
    def run(self, query: str):
        """Execute workflow with query"""
        initial_state = AgentState(
            query=query,
            result="",
            agent_used=""
        )
        return self.app.invoke(initial_state)