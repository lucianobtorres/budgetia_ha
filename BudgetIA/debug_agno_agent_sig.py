import inspect
from agno.agent import Agent

print("--- Inspecting Agno Agent ---")
sig = inspect.signature(Agent.__init__)
for name, param in sig.parameters.items():
    print(f"{name}: {param.default}")
