# app/agents/langgraph_agent.py
"""Agent using LangGraph directly (works with LangChain 1.x)"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import operator
import requests

# Define state
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    query: str
    result: str

# Define tools
@tool
def get_energy_data_tool(query: str = "") -> str:
    """Get current energy data from France's grid"""
    try:
        response = requests.get(
            "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records",
            params={"limit": 1, "order_by": "date desc"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                latest = data['results'][0]
                return f"""
Latest Energy Data from France:
- Timestamp: {latest.get('date', 'N/A')}
- Production: {latest.get('production', 0)} MW
- Consumption: {latest.get('consommation', 0)} MW
- Nuclear: {latest.get('nucleaire', 0)} MW
- Wind: {latest.get('eolien', 0)} MW
- Solar: {latest.get('solaire', 0)} MW
- Hydro: {latest.get('hydraulique', 0)} MW
- CO2 Intensity: {latest.get('taux_co2', 0)} g/kWh
"""
        return "No data available"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def analyze_energy_mix(query: str = "") -> str:
    """Analyze the energy mix"""
    try:
        response = requests.get(
            "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records",
            params={"limit": 1, "order_by": "date desc"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                latest = data['results'][0]
                nuclear = latest.get('nucleaire', 0)
                wind = latest.get('eolien', 0)
                solar = latest.get('solaire', 0)
                hydro = latest.get('hydraulique', 0)
                total = nuclear + wind + solar + hydro
                
                if total > 0:
                    return f"""
Energy Mix Analysis:
- Nuclear: {nuclear} MW ({(nuclear/total*100):.1f}%)
- Wind: {wind} MW ({(wind/total*100):.1f}%)
- Solar: {solar} MW ({(solar/total*100):.1f}%)
- Hydro: {hydro} MW ({(hydro/total*100):.1f}%)
Total Renewables: {wind + solar + hydro} MW
"""
        return "Cannot analyze energy mix"
    except Exception as e:
        return f"Error: {str(e)}"

class LangGraphDataAnalyst:
    def __init__(self):
        self.tools = [get_energy_data_tool, analyze_energy_mix]
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        workflow.add_node("get_data", self.get_data_node)
        workflow.add_node("analyze", self.analyze_node)
        
        workflow.set_entry_point("get_data")
        workflow.add_edge("get_data", "analyze")
        workflow.add_edge("analyze", END)
        
        self.app = workflow.compile()
    
    def get_data_node(self, state: AgentState):
        """Get energy data"""
        data = get_energy_data_tool.invoke(state['query'])
        return {
            "messages": [HumanMessage(content=f"Data retrieved: {data}")],
            "result": data
        }
    
    def analyze_node(self, state: AgentState):
        """Analyze the data"""
        if "mix" in state['query'].lower():
            analysis = analyze_energy_mix.invoke(state['query'])
        else:
            analysis = f"Analysis of '{state['query']}': {state['result']}"
        
        return {
            "messages": [HumanMessage(content=f"Analysis: {analysis}")],
            "result": analysis
        }
    
    def analyze(self, query: str):
        """Execute analysis"""
        try:
            result = self.app.invoke({
                "messages": [],
                "query": query,
                "result": ""
            })
            return result['result']
        except Exception as e:
            return f"Error: {str(e)}"