# simple_test.py (in root directory)
import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("Testing LangChain 1.2.4 setup")
print("=" * 50)

# First, let's check what imports work
import langchain
print(f"LangChain version: {langchain.__version__}")

# Check available modules in langchain.agents
print("\nChecking langchain.agents module structure...")
import importlib

# Try to see what's in langchain.agents
module = importlib.import_module('langchain.agents')
contents = [x for x in dir(module) if not x.startswith('_')]
print(f"Available in langchain.agents: {contents}")

# Try specific imports
print("\nTrying specific imports...")

# 1. AgentExecutor
try:
    from langchain.agents.agent_executor import AgentExecutor
    print("✓ AgentExecutor found in langchain.agents.agent_executor")
    AGENT_EXECUTOR_LOCATION = "langchain.agents.agent_executor"
except ImportError:
    try:
        from langchain.agents import AgentExecutor
        print("✓ AgentExecutor found in langchain.agents")
        AGENT_EXECUTOR_LOCATION = "langchain.agents"
    except ImportError:
        print("✗ AgentExecutor not found")
        AGENT_EXECUTOR_LOCATION = None

# 2. create_react_agent
try:
    from langchain.agents.react.base import create_react_agent
    print("✓ create_react_agent found in langchain.agents.react.base")
    CREATE_AGENT_LOCATION = "langchain.agents.react.base"
except ImportError:
    try:
        from langchain.agents import create_react_agent
        print("✓ create_react_agent found in langchain.agents")
        CREATE_AGENT_LOCATION = "langchain.agents"
    except ImportError:
        print("✗ create_react_agent not found")
        CREATE_AGENT_LOCATION = None

print("\n" + "=" * 50)
print("RECOMMENDED IMPORTS FOR YOUR CODE:")
print("=" * 50)

if AGENT_EXECUTOR_LOCATION:
    print(f"Use: from {AGENT_EXECUTOR_LOCATION} import AgentExecutor")
else:
    print("AgentExecutor: Use fallback class")

if CREATE_AGENT_LOCATION:
    print(f"Use: from {CREATE_AGENT_LOCATION} import create_react_agent")
else:
    print("create_react_agent: Use fallback function")

print("\n" + "=" * 50)