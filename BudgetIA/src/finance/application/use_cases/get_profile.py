from finance.domain.models.profile import UserProfile
from finance.domain.repositories.profile_repository import IProfileRepository


class GetProfileUseCase:
    """
    Caso de Uso: Recuperar o Perfil Financeiro do Usuário.
    """

    def __init__(self, repository: IProfileRepository):
        self._repository = repository

    def execute(self) -> UserProfile:
        return self._repository.get_profile()
