# # test_fix.py
# import sys
# import os

# # Add project root to path
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# print("Testing LangChain 1.2.4 imports...")

# # Test AgentExecutor import
# try:
#     from langchain.agents.agent_executor import AgentExecutor
#     print("✓ AgentExecutor found in langchain.agents.agent_executor")
# except ImportError:
#     try:
#         from langchain.agents import AgentExecutor
#         print("✓ AgentExecutor found in langchain.agents")
#     except ImportError as e:
#         print(f"✗ AgentExecutor not found: {e}")

# # Test create_tool_calling_agent import
# try:
#     from langchain.agents import create_tool_calling_agent
#     print("✓ create_tool_calling_agent found")
# except ImportError as e:
#     print(f"✗ create_tool_calling_agent not found: {e}")

# # Test if we can create a simple agent
# print("\nTesting agent creation...")# test_fix.py (in energy-ai-factory root directory)
# import sys
# import os

# # Add current directory to Python path
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# print("Testing LangChain 1.2.4 imports...")
# print(f"Current directory: {os.getcwd()}")
# print(f"Python path: {sys.path}")

# # Test AgentExecutor import
# try:
#     from langchain.agents.agent_executor import AgentExecutor
#     print("✓ AgentExecutor found in langchain.agents.agent_executor")
# except ImportError as e:
#     print(f"✗ AgentExecutor not in agent_executor: {e}")
#     try:
#         from langchain.agents import AgentExecutor
#         print("✓ AgentExecutor found in langchain.agents")
#     except ImportError as e:
#         print(f"✗ AgentExecutor not found anywhere: {e}")

# # List what's actually in langchain.agents
# print("\nChecking langchain.agents contents:")
# import langchain.agents
# print(dir(langchain.agents)[:20])  # First 20 items

# # Check if create_react_agent exists
# try:
#     from langchain.agents.react.base import create_react_agent
#     print("✓ create_react_agent found in langchain.agents.react.base")
# except ImportError as e:
#     print(f"✗ create_react_agent not found: {e}")
# try:
#     from app.agents.data_analyst import DataAnalystAgent
#     agent = DataAnalystAgent()
#     print("✓ DataAnalystAgent created successfully")
    
#     # Test a simple query
#     result = agent.analyze("What is the current energy production?")
#     print(f"✓ Agent test result: {result[:100]}...")
# except Exception as e:
#     print(f"✗ Error creating agent: {e}")
#     import traceback
#     traceback.print_exc()


import sys
sys.path.insert(0, '.')
from app.agents.simple_agent import SimpleEnergyAgent
agent = SimpleEnergyAgent()
print(agent.analyze('What is the nuclear production in France?'))