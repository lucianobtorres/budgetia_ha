"""
HAAuthService: Valida tokens do Home Assistant via Supervisor API.

Contexto:
- Quando o BudgetIA roda como um Add-on do HA, a variável `SUPERVISOR_TOKEN`
  é injetada automaticamente pelo Supervisor.
- Isso nos permite verificar se um token de Longa Duração do HA é válido
  chamando a API interna do Supervisor.
- Fora do ambiente HA (ex: desenvolvimento local), essa validação não está
  disponível, então o sistema cai no JWT padrão.
"""
import os
from dataclasses import dataclass
from typing import Optional

import httpx

from core.logger import get_logger
from interfaces.api.utils.security import load_users

logger = get_logger("HAAuth")

SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN")
SUPERVISOR_AUTH_URL = "http://supervisor/auth"


def is_running_as_ha_addon() -> bool:
    """Detecta se a aplicação está rodando como um Add-on do HA."""
    return bool(SUPERVISOR_TOKEN)


@dataclass
class HAUserInfo:
    """Informações do usuário retornadas pelo Supervisor."""
    ha_username: str
    display_name: str
    is_admin: bool


async def validate_ha_token(bearer_token: str) -> Optional[HAUserInfo]:
    """
    Verifica se um Bearer token é um token válido do Home Assistant.

    Chama o endpoint de autenticação do Supervisor (`http://supervisor/auth`)
    com o token do usuário no header `Authorization`.

    Returns:
        HAUserInfo se válido, None caso contrário.
    """
    if not SUPERVISOR_TOKEN:
        logger.warning("HAAuth: SUPERVISOR_TOKEN não configurado. Impossível validar token do HA.")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                SUPERVISOR_AUTH_URL,
                headers={
                    # O Supervisor usa o seu próprio token para autenticar a chamada
                    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
                    # O token do usuário final é passado nesse header customizado
                    "X-Supervisor-Token": bearer_token,
                },
                timeout=5.0,
            )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"HAAuth: Token HA validado para usuário '{data.get('username')}'")
            return HAUserInfo(
                ha_username=data.get("username", "ha_user"),
                display_name=data.get("name", "HA User"),
                is_admin=data.get("is_admin", False),
            )
        else:
            logger.debug(f"HAAuth: Token HA inválido ou expirado. Status: {response.status_code}")
            return None

    except httpx.RequestError as e:
        logger.error(f"HAAuth: Erro ao contactar Supervisor: {e}")
        return None


def resolve_ha_user_to_budgetia(ha_username: str) -> Optional[str]:
    """
    Tenta mapear o nome de usuário do HA para um usuário do BudgetIA.

    Estratégia (em ordem de prioridade):
    1. Procura um campo `ha_username` no users.yaml que corresponda.
    2. Procura um usuário cujo `username` ou `email` seja igual ao HA username.
    3. Se só existir UM usuário no sistema, usa ele como padrão (caso Single-User).

    Returns:
        O username do BudgetIA correspondente, ou None se não encontrado.
    """
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})

    if not users:
        return None

    # Estratégia 1: Campo explícito ha_username
    for username, info in users.items():
        if info.get("ha_username") == ha_username:
            logger.info(f"HAAuth: Mapeamento explícito HA '{ha_username}' -> BudgetIA '{username}'")
            return username

    # Estratégia 2: username ou email coincide
    for username, info in users.items():
        if username == ha_username or info.get("email", "").split("@")[0] == ha_username:
            logger.info(f"HAAuth: Mapeamento por nome/email HA '{ha_username}' -> BudgetIA '{username}'")
            return username

    # Estratégia 3: Sistema single-user - retorna o único usuário (admin de preferência)
    if len(users) == 1:
        only_user = list(users.keys())[0]
        logger.info(f"HAAuth: Sistema single-user. HA '{ha_username}' -> BudgetIA '{only_user}'")
        return only_user

    # Estratégia 4: Retorna o primeiro admin encontrado como fallback
    for username, info in users.items():
        if info.get("role") == "admin":
            logger.warning(f"HAAuth: Fallback para admin '{username}' para HA user '{ha_username}'")
            return username

    logger.warning(f"HAAuth: Não foi possível mapear '{ha_username}' para nenhum usuário do BudgetIA.")
    return None
