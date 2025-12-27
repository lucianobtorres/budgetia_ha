
from typing import Type
from pydantic import BaseModel, Field

from core.tools.base_tool import BaseTool
from core.memory.memory_service import MemoryService

# --- Input Schemas ---

class LearnFactInput(BaseModel):
    category: str = Field(..., description="Category of the fact (e.g., 'preference', 'goal', 'transporte', 'alimentacao').")
    fact: str = Field(..., description="The information to remember about the user.")

class UpdateFactInput(BaseModel):
    old_fact_snippet: str = Field(..., description="A unique snippet of the OLD fact to be replaced.")
    new_fact: str = Field(..., description="The NEW updated fact.")

class ForgetFactInput(BaseModel):
    fact_snippet: str = Field(..., description="A unique snippet of the fact to forget.")

class SearchMemoryInput(BaseModel):
    query: str = Field(..., description="Keywords to search for in the user's memory.")

# --- Tool Implementations ---

class LearnFactTool(BaseTool): # type: ignore[misc]
    name: str = "learn_user_fact"
    description: str = (
        "Use this tool to REMEMBER a new fact or preference about the user long-term. "
        "Example: User says 'I like vegan food', you call learn_user_fact('preference', 'likes vegan food')."
    )
    args_schema: Type[BaseModel] = LearnFactInput

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    def run(self, category: str, fact: str) -> str:
        return self.memory_service.add_fact(category, fact) # type: ignore[no-any-return]

class UpdateFactTool(BaseTool): # type: ignore[misc]
    name: str = "update_user_fact"
    description: str = (
        "Use this tool to UPDATE an existing fact when the user changes their mind. "
        "Example: User says 'Actually I prefer car now', you call update_user_fact('prefer metro', 'prefers car')."
    )
    args_schema: Type[BaseModel] = UpdateFactInput

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    def run(self, old_fact_snippet: str, new_fact: str) -> str:
        return self.memory_service.update_fact(old_fact_snippet, new_fact) # type: ignore[no-any-return]

class ForgetMemoryTool(BaseTool): # type: ignore[misc]
    name: str = "forget_user_fact"
    description: str = (
        "Use this tool to DELETE a fact that is no longer true or relevant. "
        "Example: User says 'Forget that I like sushi', you call forget_user_fact('sushi')."
    )
    args_schema: Type[BaseModel] = ForgetFactInput

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    def run(self, fact_snippet: str) -> str:
        return self.memory_service.forget_fact(fact_snippet)

class StoreMemoryTool(BaseTool): # type: ignore[misc]
    name: str = "search_user_memory"
    description: str = (
        "Use this tool to explicitely SEARCH for facts about the user if they are not in your context. "
        "Useful for questions like 'Do you remember my car brand?'."
    )
    args_schema: Type[BaseModel] = SearchMemoryInput

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    def run(self, query: str) -> str:
        facts = self.memory_service.search_facts(query)
        if not facts:
            return "No matching memories found."
        
        return "\n".join([f"- [{f['category']}] {f['content']}" for f in facts])
