# src/app/chat_history_manager.py

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
