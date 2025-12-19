print("1. Importing agno...")
try:
    import agno
    print(f"   Success: {agno.__version__ if hasattr(agno, '__version__') else 'No version'}")
except ImportError as e:
    print(f"   FAIL: {e}")

print("2. Importing agno.agent...")
try:
    from agno.agent import Agent
    print("   Success")
except ImportError as e:
    print(f"   FAIL: {e}")

print("3. Importing agno.models.google...")
try:
    from agno.models.google import Gemini
    print("   Success")
except ImportError as e:
    print(f"   FAIL: {e}")

print("4. Importing agno.tools Function...")
try:
    from agno.tools import Function
    print("   Success")
except ImportError as e:
    print(f"   FAIL: {e}")
