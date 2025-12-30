from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import PyJWTError
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from core.logger import get_logger

logger = get_logger("JWT")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um JWT assinado."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({"exp": expire})
    
    # Debug da criação (Mantendo para garantir)
    k_prev = SECRET_KEY[:4] + "***" if SECRET_KEY else "None"
    logger.debug(f"JWT CREATE: KeyPrefix={k_prev} | Len={len(SECRET_KEY)} | Hash={hash(SECRET_KEY)} | Type={type(SECRET_KEY)} | Algorithm={ALGORITHM} | Sub={to_encode.get('sub')}")
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica e valida o JWT."""
    try:
        # Debug radical: Ver a chave e o token
        k_prev = SECRET_KEY[:4] + "***" if SECRET_KEY else "None"
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError as e:
        logger.error(f"JWT DECODE ERROR: {e} | KeyPrefix={k_prev} | Len={len(SECRET_KEY)} | Hash={hash(SECRET_KEY)} | Type={type(SECRET_KEY)} | TokenStart={token[:10]}...")
        return None
