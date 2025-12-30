import sys
import os
from datetime import timedelta

# Adiciona o path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Tenta importar da estrutura de pastas
try:
    from interfaces.api.utils.jwt import create_access_token, decode_access_token
    from config import SECRET_KEY, ALGORITHM
except ImportError:
    # Fallback se rodar de dentro de src
    sys.path.append(os.getcwd())
    from src.interfaces.api.utils.jwt import create_access_token, decode_access_token
    from src.config import SECRET_KEY, ALGORITHM

def test_jwt_cycle():
    print(f"--- JWT ISOLATION TEST ---")
    print(f"SECRET_KEY (fist 4): {SECRET_KEY[:4] if SECRET_KEY else 'None'}")
    print(f"ALGORITHM: {ALGORITHM}")
    
    # 1. Criar Token
    data = {"sub": "test_user"}
    print(f"\n1. Criando token para: {data}")
    token = create_access_token(data, expires_delta=timedelta(minutes=5))
    print(f"Token Gerado: {token}")
    
    # 2. Decodificar Imediatamente
    print(f"\n2. Tentando Decodificar...")
    payload = decode_access_token(token)
    
    if payload:
        print(f"✅ SUCESSO! Payload decodificado: {payload}")
    else:
        print(f"❌ FALHA! Payload é None.")

if __name__ == "__main__":
    test_jwt_cycle()
