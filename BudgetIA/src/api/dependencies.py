from functools import lru_cache

from fastapi import Depends, HTTPException, Header
from core.user_config_service import UserConfigService
from finance.factory import FinancialSystemFactory
from finance.planilha_manager import PlanilhaManager
from finance.storage.excel_storage_handler import ExcelHandler
from core.llm_manager import LLMOrchestrator
from core.agent_runner_interface import AgentRunner
from agent_implementations.factory import AgentFactory

# Por enquanto, assumimos um usuário único local (o mesmo do Streamlit)
# Em uma versão real, isso viria de um JWT Token no Header
DEFAULT_USERNAME = "default_user" 

# --- CACHE DE SISTEMAS FINANCEIROS ---
# Mapeia user_id -> PlanilhaManager
# Isso garante que não abrimos múltiplos handlers para a mesma planilha
_managers_cache: dict[str, PlanilhaManager] = {} 

# @lru_cache # Cache removido pois agora depende do Header dinâmico
def get_user_config_service(
    x_user_id: str = Header(default=DEFAULT_USERNAME)
) -> UserConfigService:
    """Dependency que fornece o Config Service (baseado no Header)."""
    # Debug para confirmar quem está chamando
    print(f"--- API Dependency: Criando ConfigService para user='{x_user_id}' ---")
    return UserConfigService(username=x_user_id)

def get_planilha_manager(
    config_service: UserConfigService = Depends(get_user_config_service)
) -> PlanilhaManager:
    """
    Dependency que fornece uma instância válida do PlanilhaManager.
    """
    # 1. Recupera onde está o arquivo
    path_str = config_service.get_planilha_path()
    
    if not path_str:
        raise HTTPException(
            status_code=503, 
            detail="Serviço indisponível: Planilha não configurada para este usuário."
        )

    # 2. Verifica Cache
    user_id = config_service.username 
    
    cache_key = f"{user_id}:{path_str}"
    
    if cache_key in _managers_cache:
        # Debug:
        # print(f"--- API: Usando Manager em Cache para {cache_key} ---")
        return _managers_cache[cache_key]

    # 3. Cria o Handler de Storage (Local)
    storage_handler = ExcelHandler(file_path=path_str)

    # 4. Usa a Factory existente para montar tudo (Repositories, Services, Context)
    manager = FinancialSystemFactory.create_manager(
        storage_handler=storage_handler,
        config_service=config_service
    )
    
    # Debug:
    print(f"--- API: Novo Manager Criado para {cache_key} ---")
    _managers_cache[cache_key] = manager
    
    return manager

from core.llm_factory import LLMProviderFactory
from core.llm_enums import LLMProviderType
import config

# --- CACHE GLOBAL SIMPLIFICADO (Para MVP RAM) ---
_global_llm_orchestrator: LLMOrchestrator | None = None

def get_llm_orchestrator(
    config_service: UserConfigService = Depends(get_user_config_service)
) -> LLMOrchestrator:
    """Retorna o orquestrador de LLM (Singleton no processo)."""
    global _global_llm_orchestrator
    if _global_llm_orchestrator is None:
        # Inicializa se não existir - Cria o provedor padrão (Gemini)
        print("--- API Dependency: Inicializando LLMOrchestrator padrão ---")
        try:
             primary_provider = LLMProviderFactory.create_provider(
                LLMProviderType.GEMINI, default_model=config.DEFAULT_GEMINI_MODEL
            )
             _global_llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
             # Garante que carrega o modelo
             _global_llm_orchestrator.get_configured_llm()
        except Exception as e:
             print(f"ERRO CRÍTICO ao iniciar LLM: {e}")
             raise HTTPException(status_code=500, detail=f"Erro ao iniciar IA: {e}")
             
    return _global_llm_orchestrator

# --- CACHE DE AGENTES ---
# Mapeia user_id -> AgentRunner
_agents_cache: dict[str, AgentRunner] = {}

def get_agent_runner(
    config_service: UserConfigService = Depends(get_user_config_service),
    llm_orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator),
    plan_manager: PlanilhaManager = Depends(get_planilha_manager)
) -> AgentRunner:
    """
    Retorna o AgentRunner inicializado, compartilhando o mesmo PlanilhaManager
    que os endpoints de dados e dashboard.
    """
    user_id = config_service.username
    
    if user_id in _agents_cache:
        return _agents_cache[user_id]

    print(f"--- API: Criando Novo Agente para user='{user_id}' ---")
    try:
        # Cria o agente usando a Factory, injetando o Manager COMPARTILHADO
        agent = AgentFactory.create_agent(
            llm_orchestrator=llm_orchestrator,
            plan_manager=plan_manager,
            config_service=config_service # NEW
        )
        
        if not agent:
             raise HTTPException(status_code=500, detail="Falha ao criar Agente Financeiro.")
             
        _agents_cache[user_id] = agent
        return agent
    except Exception as e:
        print(f"Erro ao inicializar agente na API: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")
from app.services.notification_service import NotificationService
from app.services.presence_service import PresenceService

# ...

def get_notification_service(
    config_service: UserConfigService = Depends(get_user_config_service)
) -> NotificationService:
    """Dependency para o serviço de notificações persistentes."""
    return NotificationService(config_service)

def get_presence_service() -> PresenceService:
    """Dependency para o serviço de presença (Singleton state)."""
    return PresenceService()
