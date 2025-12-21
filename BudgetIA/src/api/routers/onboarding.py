from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import shutil
from pathlib import Path
import config
from typing import IO

from api.dependencies import get_onboarding_orchestrator
from initialization.onboarding.orchestrator import OnboardingOrchestrator, OnboardingState
from initialization.onboarding.file_handlers import AcquisitionResult

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

class ChatInput(BaseModel):
    text: str

class ChatResponse(BaseModel):
    message: str
    state: str
    ui_options: List[str]
    progress: float
    initial_message: Optional[str] = None
    google_files_list: Optional[List[dict]] = None # List of {id, name}

class GoogleAuthInput(BaseModel):
    code: str
    redirect_uri: Optional[str] = None

@router.get("/state")
def get_state(
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
):
    """Retorna o estado atual do onboarding."""
    return {
        "state": orchestrator.get_current_state().name,
        "progress": orchestrator.get_progress(),
        "ui_options": orchestrator.get_ui_options(),
        "initial_message": orchestrator.get_initial_message()
    }

@router.post("/chat", response_model=ChatResponse)
def chat(
    input_data: ChatInput,
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
):
    """Envia mensagem para o agente de onboarding."""
    response_text = orchestrator.process_user_input(input_data.text)
    
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
        "initial_message": None,
        "google_files_list": files_list
    }

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
):
    """Recebe upload de planilha e aciona o fluxo de aquisição."""
    try:
        # Salva arquivo temporariamente
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        save_path = temp_dir / file.filename
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Objeto Mock compatível com streamlit uploaded_file
        class MockFile:
            def __init__(self, path, name):
                self.path = path
                self.name = name
            def getbuffer(self):
                with open(self.path, "rb") as f:
                    return f.read()

        orchestrator._context["uploaded_file"] = MockFile(save_path, file.filename)
        
        response_text = orchestrator.process_user_input("fiz o upload do arquivo")
        
        return {
            "message": response_text,
            "state": orchestrator.get_current_state().name,
            "ui_options": orchestrator.get_ui_options(),
            "progress": orchestrator.get_progress()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.get("/google-auth-url")
def get_google_auth_url(
    redirect_uri: Optional[str] = None,
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
):
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
):
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
        "google_files_list": files_list
    }

@router.post("/reset")
def reset_onboarding(
    orchestrator: OnboardingOrchestrator = Depends(get_onboarding_orchestrator)
):
    """Reseta o estado do onboarding."""
    orchestrator.reset_config()
    return {"message": "Onboarding resetado."}
