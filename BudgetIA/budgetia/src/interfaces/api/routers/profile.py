from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Body
from interfaces.api.dependencies import get_planilha_manager, get_user_config_service
from finance.planilha_manager import PlanilhaManager
from core.user_config_service import UserConfigService
from core.google_auth_service import GoogleAuthService
from config import NomesAbas, PROFILE_DESIRED_FIELDS, ColunasPerfil

router = APIRouter(prefix="/profile", tags=["Perfil"])

@router.get("/")
def get_profile(
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> list[dict[str, Any]]:
    """
    Retorna os dados do perfil financeiro.
    """
    try:
        manager.ensure_profile_fields(PROFILE_DESIRED_FIELDS)
        df = manager.visualizar_dados(NomesAbas.PERFIL_FINANCEIRO)
        if df is None or df.empty:
            return []
        
        # Sanitização simples para JSON
        df = df.fillna("")
        return df.to_dict(orient="records") # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/bulk")
def update_profile_bulk(
    itens: list[dict[str, Any]] = Body(...),
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    """
    Atualiza o perfil.
    """
    try:
        if not itens:
            return {"message": "Nenhuma alteração enviada."}
            
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            df_new = pd.DataFrame(itens)
            
            # Limpeza essencial
            if ColunasPerfil.CAMPO in df_new.columns:
                df_new = df_new.dropna(subset=[ColunasPerfil.CAMPO])
            
            manager.update_dataframe(NomesAbas.PERFIL_FINANCEIRO, df_new)
            manager.save()
        
        return {"message": "Perfil atualizado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar perfil: {e}")

# --- MEMORY (BRAIN) ENDPOINTS ---
from core.memory.memory_service import MemoryService
from interfaces.api.dependencies import get_memory_service

@router.get("/memory")
def get_memory_facts(
    service: MemoryService = Depends(get_memory_service)
) -> list[dict[str, Any]]:
    """Retorna fatos aprendidos pela IA."""
    try:
        return service._load_memory() # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/memory/{fact_content}")
def delete_memory_fact(
    fact_content: str,
    service: MemoryService = Depends(get_memory_service)
) -> dict[str, str]:
    """Esquece um fato específico."""
    try:
        # Nota: O endpoint receberá o content codificado na URL, mas FastAPI decodifica.
        # Precisamos garantir que removemos exatamente o conteúdo.
        service.forget_fact(fact_content)
        return {"message": "Fato esquecido."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- RULES (WATCHDOG) ENDPOINTS ---
from application.notifications.rule_repository import RuleRepository
from interfaces.api.dependencies import get_rule_repository

@router.get("/rules")
def get_watchdog_rules(
    repo: RuleRepository = Depends(get_rule_repository)
) -> list[dict[str, Any]]:
    """Retorna regras ativas de monitoramento."""
    try:
        return repo._load_rules_data() # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/rules/{rule_id}")
def delete_watchdog_rule(
    rule_id: str,
    repo: RuleRepository = Depends(get_rule_repository)
) -> dict[str, str]:
    """Remove uma regra de monitoramento."""
    try:
        repo.remove_rule(rule_id)
        return {"message": "Regra removida."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
def reset_account(
    fast_track: bool = Body(False, embed=True),
    config_service: UserConfigService = Depends(get_user_config_service)
) -> dict[str, str]:
    """
    ZONA DE PERIGO: Reseta a conta do usuário.
    
    Args:
        fast_track (bool): Se True, define o status para SPREADSHEET_ACQUISITION,
                           pulando a introdução (Welcome).
    """
    try:
        config_service.clear_config()
        
        if fast_track:
            # define o status para pular a introdução
            from initialization.onboarding.state_machine import OnboardingState
            config_service.save_onboarding_state(OnboardingState.SPREADSHEET_ACQUISITION.name)
            # Precisamos salvar como status também para consistência
            # O Orchestrator lê de onboarding_status (persistido via .name)
            # O UserConfigService.save_onboarding_state salva na chave 'onboarding_state'
            # Vamos garantir que salvamos onde o Orchestrator lê.
            # Olhando o código do Orchestrator:
            # saved_status = config_service.get_onboarding_status() -> lê de 'onboarding_status'
            # Então devemos injetar lá.
            
            # Pequeno fix: O metodo save_onboarding_state salva na key 'onboarding_state', 
            # mas o Orchestrator le de 'onboarding_status'. 
            # O Orchestrator persiste via config_data["onboarding_status"] = new_state.name
            # Vamos fazer manualmente aqui para garantir.
            
            data = config_service.load_config()
            data["onboarding_status"] = OnboardingState.SPREADSHEET_ACQUISITION.name
            config_service.save_config(data)

        return {"message": "Conta resetada com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- COMMUNICATION SETTINGS ENDPOINTS ---

@router.get("/settings/communication")
def get_communication_settings(
    config_service: UserConfigService = Depends(get_user_config_service)
) -> dict[str, Any]:
    """Retorna as configurações de comunicação (Telegram, Whatsapp, etc)."""
    try:
        return config_service.get_comunicacao_config() # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/communication")
def update_communication_settings(
    settings: dict[str, Any] = Body(...),
    config_service: UserConfigService = Depends(get_user_config_service)
) -> dict[str, str]:
    """
    Atualiza as configurações de comunicação.
    Recebe um dict com os campos a serem atualizados (ex: {"telegram_chat_id": "123"}).
    """
    try:
        # Carrega config atual
        current = config_service.load_config()
        if "comunicacao" not in current:
            current["comunicacao"] = {}
        
        # Atualiza campos
        for key, value in settings.items():
            current["comunicacao"][key] = value
            
        # Salva
        config_service.save_config(current)
        return {"message": "Configurações de comunicação atualizadas."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- GOOGLE DRIVE SETTINGS ENDPOINTS ---

@router.get("/settings/google-drive")
def get_google_drive_status(
    config_service: UserConfigService = Depends(get_user_config_service)
) -> dict[str, Any]:
    """Retorna status da conexão e consentimento do Google Drive."""
    try:
        auth_service = GoogleAuthService(config_service)
        credentials = auth_service.get_user_credentials()
        has_consent = config_service.get_backend_consent()
        planilha_path = config_service.get_planilha_path()
        is_google_sheet = planilha_path and "docs.google.com" in planilha_path

        return {
            "has_credentials": bool(credentials),
            "backend_consent": has_consent,
            "is_google_sheet": bool(is_google_sheet),
            "planilha_path": planilha_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/google-drive/share")
def share_google_drive(
    config_service: UserConfigService = Depends(get_user_config_service)
) -> dict[str, str]:
    """Habilita recursos de backend (compartilha planilha)."""
    try:
        auth_service = GoogleAuthService(config_service)
        planilha_path = config_service.get_planilha_path()
        
        if not planilha_path or "docs.google.com" not in planilha_path:
            raise HTTPException(status_code=400, detail="Planilha atual não é Google Sheets.")
            
        file_id = auth_service._extract_file_id_from_url(planilha_path)
        if not file_id:
             raise HTTPException(status_code=400, detail="ID do arquivo não encontrado.")

        success, msg = auth_service.share_file_with_service_account(file_id)
        if success:
            config_service.save_backend_consent(True)
            return {"message": f"Habilitado! {msg}"}
        else:
            raise HTTPException(status_code=500, detail=msg)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/google-drive/revoke")
def revoke_google_drive(
    config_service: UserConfigService = Depends(get_user_config_service)
) -> dict[str, str]:
    """Desabilita recursos de backend (revoga compartilhamento)."""
    try:
        auth_service = GoogleAuthService(config_service)
        planilha_path = config_service.get_planilha_path()
        
        if not planilha_path:
             # Se não tem planilha, apenas remove consentimento
             config_service.save_backend_consent(False)
             return {"message": "Desabilitado."}
             
        file_id = auth_service._extract_file_id_from_url(planilha_path)
        if file_id:
             # Tenta revogar, mas se falhar (ex: usuario ja removeu manual), nao deve impedir
             auth_service.revoke_file_sharing_from_service_account(file_id)
        
        config_service.save_backend_consent(False)
        return {"message": "Desabilitado recursos de backend."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
