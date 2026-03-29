from dotenv import load_dotenv
load_dotenv()  # Load .env

import os
print("✅ LANGCHAIN_TRACING_V2:", os.getenv("LANGCHAIN_TRACING_V2"))
print("✅ LANGCHAIN_API_KEY:", "SET" if os.getenv("LANGCHAIN_API_KEY") else "MISSING")
print("✅ LANGCHAIN_PROJECT:", os.getenv("LANGCHAIN_PROJECT"))

# Test actual trace
from langchain_core.runnables import RunnableLambda
chain = RunnableLambda(lambda x: x * 2).with_config(run_name="TestTrace")
print("✅ Test trace result:", chain.invoke(5))
print("\n✅ Check LangSmith dashboard NOW: https://smith.langchain.com")
print("   → Project:", os.getenv("LANGCHAIN_PROJECT", "default"))