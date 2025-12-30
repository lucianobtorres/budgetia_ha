from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from interfaces.api.utils.jwt import decode_access_token

from infrastructure.agents.factory import AgentFactory
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from finance.factory import FinancialSystemFactory
from finance.planilha_manager import PlanilhaManager
from finance.storage.excel_storage_handler import ExcelStorageHandler
from core.logger import get_logger

logger = get_logger("API_Deps")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- CACHE DE SISTEMAS FINANCEIROS ---
# Mapeia user_id -> PlanilhaManager
# Isso garante que não abrimos múltiplos handlers para a mesma planilha
_managers_cache: dict[str, PlanilhaManager] = {}


# @lru_cache # Cache removido pois agora depende do Header dinâmico
def get_user_config_service(
    token: str = Depends(oauth2_scheme),
) -> UserConfigService:
    """Dependency que valida o JWT e retorna o Config Service."""
    payload = decode_access_token(token)
    
    if payload is None:
         logger.warning("Payload é None (Token inválido ou expirado)")
         # Tenta debug da string do token se possível
 
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou expiradas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        logger.warning("Claim 'sub' ausente no payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: sub ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Debug para confirmar quem está chamando
    logger.debug(f"Acesso AUTENTICADO para user='{username}'")
    return UserConfigService(username=username)


def get_planilha_manager(
    config_service: UserConfigService = Depends(get_user_config_service),
) -> PlanilhaManager:
    """
    Dependency que fornece uma instância válida do PlanilhaManager.
    """
    # 1. Recupera onde está o arquivo
    path_str = config_service.get_planilha_path()

    if not path_str:
        raise HTTPException(
            status_code=503,
            detail="Serviço indisponível: Planilha não configurada para este usuário.",
        )

    # 2. Verifica Cache
    user_id = config_service.username

    cache_key = f"{user_id}:{path_str}"

    if cache_key in _managers_cache:
        # Debug:

        return _managers_cache[cache_key]

    # 3. Obtém credenciais de usuário (se houver) para acesso ao GSheets
    from core.google_auth_service import GoogleAuthService
    auth_service = GoogleAuthService(config_service)
    user_credentials = auth_service.get_user_credentials()

    if user_credentials:
        logger.info("Injetando credenciais de usuário para acesso à planilha")

    # 4. Cria o Handler de Storage (Local, Google Sheets ou Google Drive Excel)
    from finance.storage.storage_factory import StorageHandlerFactory

    try:
        storage_handler = StorageHandlerFactory.create_handler(path_str, credentials=user_credentials)
        logger.info(f"Handler de Storage criado: {type(storage_handler).__name__} para {path_str}")
    except ValueError as e:
        logger.error(f"Falha ao criar handler de storage: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro de configuração de storage: {str(e)}"
        )

    # 4. Usa a Factory existente para montar tudo (Repositories, Services, Context)
    manager = FinancialSystemFactory.create_manager(
        storage_handler=storage_handler, config_service=config_service
    )

    # Debug:
    logger.debug(f"Novo Manager Criado para {cache_key}")
    _managers_cache[cache_key] = manager

    return manager


import config
from core.llm_enums import LLMProviderType
from core.llm_factory import LLMProviderFactory

# --- CACHE GLOBAL SIMPLIFICADO (Para MVP RAM) ---
_global_llm_orchestrator: LLMOrchestrator | None = None


def get_llm_orchestrator(
    config_service: UserConfigService = Depends(get_user_config_service),
) -> LLMOrchestrator:
    """Retorna o orquestrador de LLM (Singleton no processo)."""
    global _global_llm_orchestrator
    if _global_llm_orchestrator is None:
        # Inicializa se não existir
        provider_name = config.LLM_PROVIDER
        logger.info(
            f"Inicializando LLMOrchestrator com Provider='{provider_name}'"
        )
        try:
            primary_provider = None
            fallback_providers = []

            # 1. Configura Provedor Primário baseado na ENV
            if provider_name == config.LLMProviders.GROQ:
                primary_provider = LLMProviderFactory.create_provider(
                    LLMProviderType.GROQ,
                    default_model=config.LLMModels.DEFAULT_GROQ,
                )
                # Fallback: Gemini
                fallback_providers.append(
                    LLMProviderFactory.create_provider(
                        LLMProviderType.GEMINI,
                        default_model=config.LLMModels.DEFAULT_GEMINI,
                    )
                )

            elif provider_name == config.LLMProviders.GEMINI:
                primary_provider = LLMProviderFactory.create_provider(
                    LLMProviderType.GEMINI,
                    default_model=config.LLMModels.DEFAULT_GEMINI,
                )
                # Fallback: Groq (se tiver chave)
                try:
                    fallback_providers.append(
                         LLMProviderFactory.create_provider(
                            LLMProviderType.GROQ,
                            default_model=config.LLMModels.DEFAULT_GROQ,
                        )
                    )
                except Exception:
                    logger.warning("Falha ao configurar Groq como fallback (possivelmente sem chave).")

            elif provider_name == config.LLMProviders.OPENAI:
                 # TODO: Implementar OpenAI Provider na Factory se usarmos
                 # Por enquanto, fallback para Gemini
                 logger.warning("OpenAI Provider selecionado mas init pendente. Usando Gemini.")
                 primary_provider = LLMProviderFactory.create_provider(
                    LLMProviderType.GEMINI,
                    default_model=config.LLMModels.DEFAULT_GEMINI,
                )
            else:
                # Default safety net
                logger.warning(f"Provider '{provider_name}' desconhecido. Usando Gemini Default.")
                primary_provider = LLMProviderFactory.create_provider(
                    LLMProviderType.GEMINI,
                    default_model=config.LLMModels.DEFAULT_GEMINI,
                )

            _global_llm_orchestrator = LLMOrchestrator(
                primary_provider=primary_provider,
                fallback_providers=fallback_providers,
            )

            # Força carregamento e checagem de saúde
            _global_llm_orchestrator.get_configured_llm()

        except Exception as e:
            logger.critical(f"ERRO CRÍTICO ao iniciar LLM: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao iniciar IA: {e}")

    return _global_llm_orchestrator


# --- CACHE DE AGENTES ---
# Mapeia user_id -> AgentRunner
_agents_cache: dict[str, AgentRunner] = {}


def get_agent_runner(
    config_service: UserConfigService = Depends(get_user_config_service),
    llm_orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator),
    plan_manager: PlanilhaManager = Depends(get_planilha_manager),
) -> AgentRunner:
    """
    Retorna o AgentRunner inicializado, compartilhando o mesmo PlanilhaManager
    que os endpoints de dados e dashboard.
    """
    user_id = config_service.username

    if user_id in _agents_cache:
        return _agents_cache[user_id]

    logger.info(f"Criando Novo Agente para user='{user_id}'")
    try:
        # Cria o agente usando a Factory, injetando o Manager COMPARTILHADO
        agent = AgentFactory.create_agent(
            llm_orchestrator=llm_orchestrator,
            plan_manager=plan_manager,
            config_service=config_service,  # NEW
        )

        if not agent:
            raise HTTPException(
                status_code=500, detail="Falha ao criar Agente Financeiro."
            )

        _agents_cache[user_id] = agent
        return agent
    except Exception as e:
        logger.error(f"Erro ao inicializar agente na API: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


from application.notifications.rule_repository import RuleRepository
from application.services.notification_service import NotificationService
from application.services.presence_service import PresenceService
from application.services.push_notification_service import PushNotificationService

# ...
from core.memory.memory_service import MemoryService


def get_push_notification_service(
    config_service: UserConfigService = Depends(get_user_config_service),
) -> PushNotificationService:
    """Dependency para o serviço de Push Notifications."""
    # Usa o diretório do usuário para salvar as inscrições (ou global data/ se preferir)
    # Por segurança, vamos salvar no data/users/{user}/push.json para isolamento?
    # O PushService atual recebe um 'Path' e salva 'push_subscriptions.json' lá.
    return PushNotificationService(config_service.config_dir)


def get_notification_service(
    config_service: UserConfigService = Depends(get_user_config_service),
    push_service: PushNotificationService = Depends(get_push_notification_service),
) -> NotificationService:
    """Dependency para o serviço de notificações persistentes."""
    return NotificationService(config_service, push_service)


def get_presence_service() -> PresenceService:
    """Dependency para o serviço de presença (Singleton state)."""
    return PresenceService()


def get_memory_service(
    config_service: UserConfigService = Depends(get_user_config_service),
) -> MemoryService:
    """Dependency para o serviço de memória (Brain)."""
    user_dir = config_service.get_user_dir()
    return MemoryService(user_dir)


def get_rule_repository(
    config_service: UserConfigService = Depends(get_user_config_service),
) -> RuleRepository:
    """Dependency para o repositório de regras (Watchdog)."""
    user_dir = config_service.get_user_dir()
    return RuleRepository(user_dir)


from initialization.onboarding.orchestrator import OnboardingOrchestrator

# --- CACHE DE ONBOARDING ---
_onboarding_cache: dict[str, OnboardingOrchestrator] = {}


def get_onboarding_orchestrator(
    config_service: UserConfigService = Depends(get_user_config_service),
    llm_orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator),
) -> OnboardingOrchestrator:
    """Retorna o orquestrador de onboarding (Stateful per session/user)."""
    user_id = config_service.username

    if user_id not in _onboarding_cache:
        logger.info(
            f"Criando Novo Onboarding Orchestrator para user='{user_id}'"
        )
        orchestrator = OnboardingOrchestrator(config_service, llm_orchestrator)
        _onboarding_cache[user_id] = orchestrator

    return _onboarding_cache[user_id]
