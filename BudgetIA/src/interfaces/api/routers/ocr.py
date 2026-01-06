from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Any
from interfaces.api.dependencies import get_llm_orchestrator
from core.llm_manager import LLMOrchestrator
from finance.services.ocr_service import OCRService
from core.logger import get_logger

logger = get_logger("API-OCR")

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.get("/status")
def get_ocr_status(llm_orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)):
    """Verifica se o serviço de OCR está disponível (há LLM de visão configurado)."""
    return {
        "available": llm_orchestrator.is_vision_available
    }

@router.post("/analyze")
async def analyze_receipt(
    file: UploadFile = File(...),
    llm_orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)
) -> Any:
    """
    Recebe uma imagem (upload), analisa com Vision LLM e retorna dados do recibo.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem.")

    try:
        content = await file.read()
        service = OCRService(llm_orchestrator)
        
        result = service.analyze_receipt(content, file.content_type)
        return result
        
    except Exception as e:
        logger.error(f"Erro ao processar OCR: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")
