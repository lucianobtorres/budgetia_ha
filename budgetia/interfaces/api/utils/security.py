import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit_authenticator as stauth

import os
import config

USERS_FILE = Path(os.path.join(config.DATA_DIR, "users.yaml"))

def load_users() -> Dict[str, Any]:
    """Carrega o arquivo de usuários."""
    if not USERS_FILE.exists():
        return {"credentials": {"usernames": {}}}
    
    with open(USERS_FILE, 'r') as file:
        return yaml.safe_load(file) or {}

def save_users(data: Dict[str, Any]) -> None:
    """Salva o arquivo de usuários."""
    USERS_FILE.parent.mkdir(exist_ok=True, parents=True)
    with open(USERS_FILE, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash (usando stauth logic)."""
    # stauth usa bcrypt internamente. O Hasher do stauth tem método check?
    # Vamos usar o stauth.Hasher para manter compatibilidade total.
    # Na versão atual, stauth.Hasher.check_pw(plain, hashed) (método estático ou via bcrypt)
    # Mas utils.py usa stauth.Hasher([pass]).generate().
    # Vamos usar bcrypt direto se stauth for Wrapper, ou importar o stauth.
    # Olhando utils.py, ele usa stauth.Authenticate. 
    # O stauth geralmente usa bcrypt.
    
    import bcrypt
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except:
        return False

def hash_password(plain_password: str) -> str:
    """Gera hash da senha compatível com Streamlit Authenticator."""
    return str(stauth.Hasher([plain_password]).generate()[0])

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Busca usuário pelo username."""
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    return users.get(username)

def create_user(username: str, name: str, email: str, password: str) -> bool:
    """Cria novo usuário. Retorna False se já existir."""
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    
    if username in users:
        return False
        
    hashed = hash_password(password)
    
    users[username] = {
        "email": email,
        "name": name,
        "password": hashed,
        "logged_in": False # Legacy field
    }
    
    # Garantir estrutura
    if "credentials" not in data: data["credentials"] = {}
    if "usernames" not in data["credentials"]: data["credentials"]["usernames"] = {}
    
    data["credentials"]["usernames"] = users
    
    # Garantir outros campos do yaml (cookie, preauthorized) se não existirem
    if "cookie" not in data:
        data["cookie"] = {"expiry_days": 30, "key": "some_signature_key", "name": "some_cookie_name"}
    
    save_users(data)
    return True
