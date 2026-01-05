import json
import os
from datetime import datetime
from typing import Any
# import fcntl  -- REMOVED for Windows compatibility
# Note: On Windows specifically, fcntl is not available. 
# We will implement a simple file lock using a context manager or just rely on atomic writes for now since it's single user primarily.

class MemoryService:
    """
    Service responsible for managing Long-Term Memory (User Facts).
    Stores data in a JSON file: data/users/{username}/memory.json
    """

    def __init__(self, user_data_dir: str):
        self.memory_file = os.path.join(user_data_dir, "memory.json")
        self._ensure_memory_file()

    def _ensure_memory_file(self) -> None:
        """Creates the memory file if it doesn't exist."""
        if not os.path.exists(self.memory_file):
            self._save_memory([])

    def _load_memory(self) -> list[dict[str, Any]]:
        """Loads all facts from the JSON file."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data: list[dict[str, Any]] = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_memory(self, memory: list[dict[str, Any]]) -> None:
        """Saves facts to the JSON file atomically."""
        temp_file = self.memory_file + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4, ensure_ascii=False)
        os.replace(temp_file, self.memory_file)

    def add_fact(self, category: str, content: str, source: str = "user", metadata: dict[str, Any] | None = None) -> str:
        """Adds a new fact to the memory."""
        memory = self._load_memory()
        
        # Check if identical fact exists
        for fact in memory:
            if fact["category"] == category and fact["content"] == content:
                # Update metadata if provided? For now, just skip unique duplicates.
                return "Fact already known."

        new_fact = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "category": category,
            "content": content,
            "source": source,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        memory.append(new_fact)
        self._save_memory(memory)
        return f"Fact added: [{category}] {content}"

    def update_fact(self, old_content_snippet: str, new_content: str) -> str:
        """
        Updates a fact by searching for a snippet of the old content.
        This allows the agent to say 'Replace the fact about Uber...'.
        """
        memory = self._load_memory()
        updated = False
        
        for fact in memory:
            if old_content_snippet.lower() in fact["content"].lower():
                fact["content"] = new_content
                fact["updated_at"] = datetime.now().isoformat()
                updated = True
                # We stop at the first match for safety, or we could ask for ID.
                # Ideally the agent should be precise.
                break
        
        if updated:
            self._save_memory(memory)
            return f"Fact updated to: {new_content}"
        else:
            return "Could not find a matching fact to update."

    def forget_fact(self, content_snippet: str) -> str:
        """Removes a fact that matches the snippet."""
        memory = self._load_memory()
        original_len = len(memory)
        
        # Filter out matching facts
        memory = [f for f in memory if content_snippet.lower() not in f["content"].lower()]
        
        if len(memory) < original_len:
            self._save_memory(memory)
            return "Fact(s) forgotten."
        else:
            return "No matching fact found to forget."

    def search_facts(self, query: str = "") -> list[dict[str, Any]]:
        """
        Searches facts by keyword or returns all if query is empty.
        Simple keyword matching for now (Phase 1).
        """
        memory = self._load_memory()
        if not query:
            return memory
        
        return [
            f for f in memory 
            if query.lower() in f["content"].lower() or query.lower() in f["category"].lower()
        ]

    def get_context_string(self) -> str:
        """Returns a formatted string of all memories for the System Prompt."""
        memory = self._load_memory()
        if not memory:
            return "No known facts about the user yet."
        
        lines = ["User Memories:"]
        for f in memory:
            lines.append(f"- [{f['category']}] {f['content']}")
        return "\n".join(lines)
