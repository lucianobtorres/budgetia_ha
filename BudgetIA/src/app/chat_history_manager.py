# src/app/chat_history_manager.py
import json
import os

import streamlit as st


class BaseHistoryManager:
    """Interface para um gerenciador de histórico de chat."""

    def get_history(self) -> list[dict[str, str]]:
        raise NotImplementedError

    def add_message(self, role: str, content: str) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class StreamlitHistoryManager(BaseHistoryManager):
    """
    Implementação de um gerenciador de histórico que usa
    o st.session_state como backend.
    """

    def __init__(self, session_key: str):
        self.session_key = session_key
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []

    def get_history(self) -> list[dict[str, str]]:
        return st.session_state.get(self.session_key, [])

    def add_message(self, role: str, content: str) -> None:
        st.session_state[self.session_key].append({"role": role, "content": content})

    def clear(self) -> None:
        st.session_state[self.session_key] = []


class JsonHistoryManager(BaseHistoryManager):
    """
    Implementação de um gerenciador de histórico que usa
    um arquivo JSON como backend.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_file(self) -> list[dict[str, str]]:
        try:
            with open(self.file_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    def _write_file(self, history: list[dict[str, str]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(
                f"ERRO (JsonHistoryManager): Falha ao escrever no histórico {self.file_path}: {e}"
            )

    def get_history(self) -> list[dict[str, str]]:
        return self._read_file()

    def add_message(self, role: str, content: str) -> None:
        history = self._read_file()
        history.append({"role": role, "content": content})
        self._write_file(history)

    def clear(self) -> None:
        self._write_file([])
