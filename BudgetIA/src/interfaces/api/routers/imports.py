from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import io
import logging
from finance.services.import_service import ImportService, ImportedTransaction
from core.llm_manager import LLMOrchestrator
from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_llm_orchestrator, get_planilha_manager

router = APIRouter(prefix="/imports", tags=["Imports"])

@router.post("/upload", response_model=List[ImportedTransaction])
async def upload_file(
    file: UploadFile = File(...),
    llm_orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator),
    manager: PlanilhaManager = Depends(get_planilha_manager)
):
    """
    Faz upload de um arquivo OFX, processa e retorna as transações encontradas com CATEGORIAS SUGERIDAS PELA IA.
    Não salva no banco de dados ainda; apenas retorna para revisão do frontend.
    """
    if not file.filename.lower().endswith('.ofx'):
         raise HTTPException(status_code=400, detail="Apenas arquivos .ofx são suportados no momento.")
         
    try:
        # Read file content
        content = await file.read()
        file_obj = io.BytesIO(content)
        
        # Instantiate Service with dependencies
        if not hasattr(manager, 'category_repo') or not hasattr(manager, 'transaction_repo'):
             logging.error("PlanilhaManager missing category_repo or transaction_repo.")
             raise HTTPException(status_code=500, detail="Erro interno de dependência.")
             
        service = ImportService(llm_orchestrator, manager.category_repo, manager.transaction_repo)
        
        # Parse & Auto-Classify
        transactions = service.parse_ofx(file_obj)
        
        return transactions
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar arquivo: {str(e)}")
