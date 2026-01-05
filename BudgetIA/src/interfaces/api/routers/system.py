from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
import os
import logging

router = APIRouter(prefix="/system", tags=["System"])
logger = logging.getLogger(__name__)

BANNER_FILE = os.path.join(os.getcwd(), "data", "system_status.json")

class SystemBanner(BaseModel):
    is_active: bool
    message: str
    level: str = "info" # info, warning, error
    expires_at: Optional[str] = None
    id: str # Unique ID for dismissal tracking

@router.get("/banner", response_model=Optional[SystemBanner])
def get_system_banner():
    """
    Retorna o banner do sistema atual se estiver ativo e não expirado.
    """
    if not os.path.exists(BANNER_FILE):
        return None
        
    try:
        with open(BANNER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        banner = SystemBanner(**data)
        
        if not banner.is_active:
            return None
            
        if banner.expires_at:
            if datetime.fromisoformat(banner.expires_at) < datetime.now():
                return None
                
        return banner
    except Exception as e:
        logger.error(f"Erro ao ler banner do sistema: {e}")
        return None
