from enum import Enum


class LLMProviderType(str, Enum):
    """
    Enum para os tipos de provedores de LLM suportados.
    """

    GEMINI = "gemini"
    GROQ = "groq"
    # OPENAI = "openai" # Futuro
    # CLAUDE = "claude" # Futuro
