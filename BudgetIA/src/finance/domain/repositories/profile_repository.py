from abc import ABC, abstractmethod

from ..models.profile import UserProfile


class IProfileRepository(ABC):
    """
    Interface para o repositório de Perfil do Usuário.
    """

    @abstractmethod
    def get_profile(self) -> UserProfile:
        """Recupera o perfil completo do usuário."""
        pass

    @abstractmethod
    def save_profile(self, profile: UserProfile) -> None:
        """Salva todas as alterações do perfil."""
        pass

    @abstractmethod
    def ensure_fields(self, fields: list[str]) -> None:
        """Garante a existência de campos básicos no armazenamento."""
        pass
