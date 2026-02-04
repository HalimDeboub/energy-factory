# find_imports.py (run this in your root directory)
import langchain.agents
import inspect

print("LangChain version:", langchain.__version__)
print("\nAvailable in langchain.agents:")

# List everything in langchain.agents
for item in dir(langchain.agents):
    if not item.startswith('_'):
        print(f"  - {item}")

print("\n" + "="*50)
print("Checking submodules...")

# Check submodules
try:
    import langchain.agents.agent_executor
    print("✓ langchain.agents.agent_executor exists")
except ImportError:
    print("✗ langchain.agents.agent_executor does NOT exist")

try:
    import langchain.agents.react
    print("✓ langchain.agents.react exists")
except ImportError:
    print("✗ langchain.agents.react does NOT exist")

# Look for AgentExecutor anywhere
print("\n" + "="*50)
print("Searching for AgentExecutor class...")

import pkgutil
import langchain

def find_class(module, class_name):
    for _, name, ispkg in pkgutil.iter_modules(module.__path__):
        if not ispkg:
            try:
                full_name = f"{module.__name__}.{name}"
                submodule = __import__(full_name, fromlist=[''])
                if hasattr(submodule, class_name):
                    print(f"✓ Found {class_name} in {full_name}")
                    return getattr(submodule, class_name)
            except:
                continue
    return None

# Search in langchain.agents
agent_executor_class = find_class(langchain.agents, 'AgentExecutor')
if not agent_executor_class:
    print("✗ Could not find AgentExecutor in langchain.agents")