# Test script - test_agents.py
from app.workflows.energy_graph import EnergyWorkflow

workflow = EnergyWorkflow()

# Test queries
test_queries = [
    "What is the current energy mix in France?",
    "How much renewable energy is being produced right now?",
    "What's the carbon intensity of France's grid today?"
]

for query in test_queries:
    print(f"\n{'='*50}")
    print(f"Query: {query}")
    result = workflow.run(query)
    print(f"Result: {result['analysis_results']}")