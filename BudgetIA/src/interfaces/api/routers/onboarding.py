from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Any, List, Optional
import shutil
from pathlib import Path
import config
from typing import IO

from interfaces.api.dependencies import get_onboarding_orchestrator
from initialization.onboarding.orchestrator import OnboardingOrchestrator, OnboardingState
from initialization.onboarding.file_handlers import AcquisitionResult

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

class ChatInput(BaseModel):
    text: str
    context: Optional[dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    state: str
    ui_options: List[str]
    progress: float
    is_analysis_complete: bool = False # NEW
    initial_message: Optional[str] = None
    google_files_list: Optional[List[dict[str, Any]]] = None # List of {id, name}

class GoogleAuthInput(BaseModel):
    code: str
    redirect_uri: Optional[str] = None

@router.get("/state")
def get_state(
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
) -> dict[str, Any]:
    """Retorna o estado atual do onboarding."""
    return {
        "state": orchestrator.get_current_state().name,
        "progress": orchestrator.get_progress(),
        "ui_options": orchestrator.get_ui_options(),
        "is_analysis_complete": orchestrator.is_translation_analysis_complete(),
        "initial_message": orchestrator.get_initial_message()
    }

@router.get("/status/{username}")
def get_status(
    username: str,
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
) -> dict[str, str]:
    """
    Retorna o status simples (START, DOING, COMPLETE, ERROR) 
    para decisão de roteamento do frontend.
    """
    # Se o ConfigService diz que está configurado, retorna COMPLETE
    if orchestrator.config_service.is_configured():
        return {"status": "COMPLETE"}
    
    # Caso contrário, retorna o estado atual mapeado ou o nome direto
    state = orchestrator.get_current_state().name
    return {"status": state}

@router.post("/chat", response_model=ChatResponse)
def chat(
    input_data: ChatInput,
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
) -> dict[str, Any]:
    """Envia mensagem para o agente de onboarding."""
    response_text = orchestrator.process_user_input(input_data.text, extra_context=input_data.context)
    
    files_list = None
    if "[UI_ACTION:show_file_selection]" in response_text:
        try:
            files_list = orchestrator.get_google_auth_service().list_google_drive_files()
        except Exception as e:
            response_text += f"\n(Erro ao listar arquivos: {str(e)})"

    return {
        "message": response_text,
        "state": orchestrator.get_current_state().name,
        "ui_options": orchestrator.get_ui_options(),
        "progress": orchestrator.get_progress(),
        "is_analysis_complete": orchestrator.is_translation_analysis_complete(),
        "initial_message": None,
        "google_files_list": files_list
    }

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
) -> dict[str, Any]:
    """Recebe upload de planilha e aciona o fluxo de aquisição."""
    try:
        # Salva arquivo temporariamente
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        save_path = temp_dir / (file.filename or "uploaded_file")
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Objeto Mock compatível com streamlit uploaded_file
        class MockFile:
            def __init__(self, path: Path, name: str) -> None:
                self.path = path
                self.name = name
            def getbuffer(self) -> bytes:
                with open(self.path, "rb") as f:
                    return f.read()

        orchestrator._context["uploaded_file"] = MockFile(save_path, file.filename or "uploaded_file")
        
        response_text = orchestrator.process_user_input("fiz o upload do arquivo")
        
        return {
            "message": response_text,
            "state": orchestrator.get_current_state().name,
            "ui_options": orchestrator.get_ui_options(),
            "progress": orchestrator.get_progress(),
            "is_analysis_complete": orchestrator.is_translation_analysis_complete()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.get("/google-auth-url")
def get_google_auth_url(
    redirect_uri: Optional[str] = None,
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
) -> dict[str, str]:
    """Gera a URL de autorização do Google."""
    auth_service = orchestrator.get_google_auth_service()
    current_state = orchestrator.get_current_state().name
    
    url = auth_service.generate_authorization_url(
        current_onboarding_state=current_state,
        redirect_uri=redirect_uri
    )
    return {"url": url}

@router.post("/google-auth", response_model=ChatResponse)
def google_auth(
    data: GoogleAuthInput,
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
) -> dict[str, Any]:
    """Recebe código de auth do Google e processa."""
    orchestrator._context["google_auth_code"] = data.code
    
    if data.redirect_uri:
        orchestrator._context["redirect_uri"] = data.redirect_uri
        
    response_text = orchestrator.process_user_input("Google Sheets")

    files_list = None
    if "[UI_ACTION:show_file_selection]" in response_text:
        try:
            files_list = orchestrator.get_google_auth_service().list_google_drive_files()
        except Exception as e:
             response_text += f"\n(Erro ao listar arquivos: {str(e)})"
    
    return {
        "message": response_text,
        "state": orchestrator.get_current_state().name,
        "ui_options": orchestrator.get_ui_options(),
        "progress": orchestrator.get_progress(),
        "is_analysis_complete": orchestrator.is_translation_analysis_complete(),
        "google_files_list": files_list
    }

@router.post("/reset")
def reset_onboarding(
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
) -> dict[str, str]:
    """Reseta o estado do onboarding."""
    orchestrator.reset_config()
    return {"message": "Onboarding resetado."}
