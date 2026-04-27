from typing import Any

from finance.domain.models.profile import UserProfile
from finance.domain.repositories.profile_repository import IProfileRepository


class UpdateProfileUseCase:
    """
    Caso de Uso: Atualizar o Perfil Financeiro do Usuário.
    """

    def __init__(self, repository: IProfileRepository):
        self._repository = repository

    def execute(self, updates: dict[str, Any]) -> UserProfile:
        """
        Executa a atualização do perfil com base em um dicionário de mudanças.
        """
        # 1. Carrega o perfil atual
        profile = self._repository.get_profile()

        # 2. Mapeia e aplica as atualizações
        # Nota: 'updates' pode vir com chaves em snake_case (API) ou nomes da planilha (Legado)
        # Vamos normalizar para snake_case para a lógica da entidade

        legacy_mapping = {
            "Renda Mensal Média": "renda_mensal",
            "Principal Objetivo": "objetivo_principal",
            "Tolerância a Risco": "tolerancia_risco",
        }

        for key, value in updates.items():
            # Traduz nome de coluna legado para campo da entidade se necessário
            target_field = legacy_mapping.get(key, key)

            if hasattr(profile, target_field) and target_field != "outros_campos":
                setattr(profile, target_field, value)
            else:
                # Se não é um campo fixo, vai para o dicionário de campos dinâmicos
                profile.outros_campos[target_field] = value

        # 3. Persiste via repositório
        self._repository.save_profile(profile)
        return profile
