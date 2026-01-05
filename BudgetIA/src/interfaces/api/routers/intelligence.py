from fastapi import APIRouter, Depends
from pydantic import BaseModel
import os
import importlib
import inspect
from typing import Any

from core.user_config_service import UserConfigService
from interfaces.api.dependencies import get_user_config_service

# Importar BaseTool para verificação
from core.base_tool import BaseTool
from core.logger import get_logger

# Importar jobs para listar observadores ativos
from application.proactive_jobs import get_default_rules
from finance.tool_loader import TOOL_TRANSLATIONS # Importar Traduções Shared

logger = get_logger("API_Intelligence")
router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

class ToolInfo(BaseModel):
    name: str
    description: str
    label: str | None = None
    is_essential: bool

class ObserverInfo(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool
    config: dict

@router.get("/tools", response_model=list[ToolInfo])
def get_available_tools():
    """
    Lista todas as ferramentas disponíveis no sistema para a 'Vitrine de Ferramentas'.
    Lê dinamicamente do diretório de tools.
    """
    tools_list = []
    tools_dir = os.path.join("src", "finance", "tools")
    
    # Lista de essenciais (Hardcoded por enquanto, idealmente viria do tool_loader)
    ESSENTIAL_TOOLS = [
        "add_transaction_tool", "view_data_tool", "calculate_balance_tool",
        "check_budget_status_tool", "delete_transaction_tool", "update_transaction_tool",
        "generate_monthly_summary_tool", "register_ai_insight_tool", "define_budget_tool"
    ]

    try:
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module_name = f"finance.tools.{module_name}"
                
                try:
                    module = importlib.import_module(full_module_name)
                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        
                        if (isinstance(attribute, type) and 
                            issubclass(attribute, BaseTool) and 
                            attribute is not BaseTool):
                            
                            tool_class = attribute
                            # Instanciar sem argumentos só para pegar metadados falharia se tiver dependências obrigatórias no init.
                            # Melhor pegar atributos de classe se possível ou inspecionar.
                            
                            # Tentar pegar atributos de classe
                            name = getattr(tool_class, "name", module_name)
                            desc = getattr(tool_class, "description", "Sem descrição.")
                            # Tentar pegar label (injetado ou estático)
                            # Nota: ToolInfo vem da classe, label injetado no loader é na instância.
                            # Mas aqui estamos lendo a classe estaticamente. 
                            # Precisamos replicar a lógica do loader ou, melhor, carregar via loader?
                            # O loader retorna instâncias. Aqui estamos listando arquivos.
                            # Se quisermos consistência, devemos usar o MAPA aqui também ou usar o label da classe se adicionamos.
                            # Adicionei label ao BaseTool, então podemos tentar ler.
                            label = getattr(tool_class, "label", None)
                            
                            # Map/Fallback logic
                            tool_name_key = name.replace("_tool", "")
                            if name in TOOL_TRANSLATIONS:
                                label = TOOL_TRANSLATIONS[name]
                            elif tool_name_key in TOOL_TRANSLATIONS:
                                label = TOOL_TRANSLATIONS[tool_name_key]
                            else:
                                label = getattr(tool_class, "label", name.replace("_", " ").title())

                            tools_list.append(ToolInfo(
                                name=name,
                                description=desc,
                                label=label,
                                is_essential=module_name in ESSENTIAL_TOOLS
                            ))
                            break # Encontrou a classe da tool neste arquivo
                            
                except Exception as e:
                    logger.warning(f"Erro ao inspecionar ferramenta {filename}: {e}")
                    continue
                    
        return sorted(tools_list, key=lambda x: x.name)
        
    except Exception as e:
        logger.error(f"Erro ao listar ferramentas: {e}")
        return []

@router.get("/observers", response_model=list[ObserverInfo])
def get_active_observers(
    user_config_service: UserConfigService = Depends(get_user_config_service)
):
    """
    Lista os Observadores Proativos (Regras) que estão rodando em background.
    """
    observers = []
    
    try:
        # Instanciar regras padrão hardcoded (agora incluindo as que dependem de config/memoria)
        rules = get_default_rules(user_config_service)
        logger.info(f"OBSERVERS: Regras padrão carregadas: {[r.rule_name for r in rules]}")
        
        # Mapa de Traduções para Observadores
        OBSERVER_TRANSLATIONS = {
            # Keys must match rule.rule_name properties
            'transport_missing': 'Monitor de Transporte',
            'budget_overrun': 'Alerta de Orçamento Estourado',
            'subscription_auditor': 'Auditor de Assinaturas',
            'recurring_expense_monitor': 'Monitor de Gastos Recorrentes',
            'expense_anomaly': 'Detector de Anomalias',
            # Fallbacks for class names just in case
            'TransportMissingRule': 'Monitor de Transporte',
            'BudgetOverrunRule': 'Alerta de Orçamento Estourado',
            'SubscriptionAuditorRule': 'Auditor de Assinaturas'
        }

        for r in rules:
            try:
                display_name = getattr(r, "display_name", None)
                if not display_name:
                     # Fallback translation
                     base_name = OBSERVER_TRANSLATIONS.get(r.rule_name, r.rule_name.replace("_", " ").title())
                     display_name = base_name

                observers.append(ObserverInfo(
                    id=r.rule_name,
                    name=display_name,
                    description=r.__doc__.strip() if r.__doc__ else "Monitoramento financeiro inteligente.",
                    is_active=True,
                    config={} # TODO: Expose actual rule config
                ))
            except Exception as e:
                logger.error(f"Erro ao processar regra {type(r)}: {e}")

        logger.info(f"OBSERVERS: Retornando {len(observers)} observadores.")
        return observers
    except Exception as e:
        logger.error(f"Erro ao listar observadores: {e}")
        return []

class SubscriptionKeywordsUpdate(BaseModel):
    keywords: list[str]

@router.get("/subscription-keywords", response_model=list[str])
async def get_subscription_keywords(
    user_config_service: UserConfigService = Depends(get_user_config_service)
) -> Any:
    """Retorna a lista de palavras-chave do Auditor de Assinaturas."""
    config = user_config_service.load_config()
    keywords = config.get("comunicacao", {}).get("subscription_keywords")
    
    if not keywords:
        from application.notifications.rules.audit.subscription_auditor_rule import SubscriptionAuditorRule
        return SubscriptionAuditorRule.DEFAULT_KEYWORDS
        
    return keywords

@router.post("/subscription-keywords")
async def update_subscription_keywords(
    update: SubscriptionKeywordsUpdate,
    user_config_service: UserConfigService = Depends(get_user_config_service)
) -> Any:
    """Atualiza a lista de palavras-chave do Auditor de Assinaturas."""
    try:
        user_config_service.save_comunicacao_field("subscription_keywords", update.keywords)
        return {"status": "success", "message": "Palavras-chave atualizadas com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao salvar keywords: {e}")
        return {"status": "error", "message": str(e)}
@router.post("/learn")
async def trigger_learning(
    user_config_service: UserConfigService = Depends(get_user_config_service),
    llm_orchestrator: Any = Depends(lambda: None), # TODO: Fix Dependency Injection for LLM
    # Precisamos do LLMOrchestrator e PlanilhaManager.
    # O PlanilhaManager geralmente é criado per request ou singleton.
    # Vamos usar os dependencies existentes se houver, ou instanciar.
):
    """
    Aciona o processo de aprendizado (Behavior Analyst) manualmente.
    """
    # NOTE: Para simplificar, vamos importar as dependencias aqui se não tivermos injections globais no router
    # Idealmente, teriamos get_llm_orchestrator e get_planilha_manager
    
    from interfaces.api.dependencies import get_llm_orchestrator, get_planilha_manager
    
    # Resolver dependencias manualmente (ou usar Depends na assinatura e corrigir imports)
    # Como não tenho certeza se get_llm_orchestrator está exportado/pronto, vou tentar importar.
    # Se falhar, instanciamos.
    
    try:
        llm = get_llm_orchestrator(user_config_service)
        # O get_planilha_manager geralmente precisa de user_id/config
        pm = get_planilha_manager(user_config_service)
        
        from application.proactive_jobs import run_behavior_learning_job
        result = await run_behavior_learning_job(user_config_service, llm, pm)
        return result
        
    except Exception as e:
        logger.error(f"Erro no endpoint /learn: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/clean")
async def trigger_cleaning(
    user_config_service: UserConfigService = Depends(get_user_config_service),
    llm_orchestrator: Any = Depends(lambda: None),
):
    """
    Aciona o Faxineiro de Dados (Data Sanitizer).
    Varre transações 'Outros' e tenta categorizar via IA.
    """
    from interfaces.api.dependencies import get_llm_orchestrator, get_planilha_manager
    
    try:
        llm = get_llm_orchestrator(user_config_service)
        pm = get_planilha_manager(user_config_service)
        
        from application.proactive_jobs import run_data_sanitizer_job
        result = await run_data_sanitizer_job(user_config_service, llm, pm)
        return result
        
    except Exception as e:
        logger.error(f"Erro no endpoint /clean: {e}")
        return {"status": "error", "message": str(e)}
