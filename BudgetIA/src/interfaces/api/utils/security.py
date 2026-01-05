import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import streamlit_authenticator as stauth

import os
import config

def load_users() -> Dict[str, Any]:
    """Carrega o arquivo users.yaml"""
    users_path = Path(config.USERS_FILE)
    if not users_path.exists():
        return {"credentials": {"usernames": {}}}
    
    try:
        with open(users_path, "r") as file:
            data = yaml.safe_load(file)
            if not data:
                return {"credentials": {"usernames": {}}}
            
            # Garante estrutura mínima se o arquivo existir mas estiver parcial
            if "credentials" not in data:
                data["credentials"] = {}
            if "usernames" not in data["credentials"]:
                data["credentials"]["usernames"] = {}
                
            return data
    except Exception as e:
        print(f"Erro ao carregar users.yaml: {e}")
        return {"credentials": {"usernames": {}}}

def save_users(data: Dict[str, Any]) -> None:
    """Salva dados no users.yaml"""
    users_path = Path(config.USERS_FILE)
    # Garante que diretório existe
    users_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(users_path, "w") as file:
        yaml.dump(data, file)

def hash_password(password: str) -> str:
    """Gera hash da senha usando oHasher do Streamlit Authenticator"""
    return stauth.Hasher([password]).generate()[0]

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica senha (compatível com lista ou string simples)"""
    import bcrypt
    try:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    except:
        pass
        
    # Tentativa manual simples com Streamlit Authenticator
    try:
        result = stauth.Hasher([password]).check([hashed_password])
        if isinstance(result, list):
            return result[0]
        return result
    except Exception as e:
        print(f"Erro verify_password: {e}")
        return False

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Busca usuário pelo username exato."""
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    return users.get(username)

def get_user_by_identifier(identifier: str) -> Optional[tuple[str, Dict[str, Any]]]:
    """
    Busca usuário por username OU email.
    Retorna tupla (username, user_data) ou None.
    """
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    
    # 1. Tenta match exato pelo username (chave)
    if identifier in users:
        return identifier, users[identifier]
        
    # 2. Tenta buscar pelo campo verificado de email
    lower_id = identifier.lower()
    for u_name, u_data in users.items():
        if u_data.get("email", "").lower() == lower_id:
            return u_name, u_data
            
    return None

def create_user(username: str, name: str, email: str, password: str) -> bool:
    """Cria novo usuário."""
    data = load_users()
    
    # Garante estrutura
    if "credentials" not in data:
        data["credentials"] = {}
    if "usernames" not in data["credentials"]:
        data["credentials"]["usernames"] = {}
        
    users = data["credentials"]["usernames"]
    
    if username in users:
        return False
        
    hashed = hash_password(password)
    
    users[username] = {
        "email": email,
        "name": name,
        "password": hashed,
        "role": "user",
        "created_at": datetime.now().isoformat(),
        "trial_ends_at": (datetime.now() + timedelta(days=14)).isoformat(),
        "logged_in": False
    }
    
    save_users(data)
    return True

def set_reset_token(username: str, token: str) -> bool:
    """Salva token de reset."""
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    if username in users:
        users[username]["reset_token"] = token
        save_users(data)
        return True
    return False

def get_user_by_reset_token(token: str) -> Optional[tuple[str, Dict[str, Any]]]:
    """Busca user pelo reset token."""
    data = load_users()
    for u, info in data.get("credentials", {}).get("usernames", {}).items():
        if info.get("reset_token") == token:
            return u, info
    return None

def clear_reset_token(username: str):
    data = load_users()
    if username in data.get("credentials", {}).get("usernames", {}):
        if "reset_token" in data["credentials"]["usernames"][username]:
            del data["credentials"]["usernames"][username]["reset_token"]
            save_users(data)

def update_password(username: str, new_password: str):
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    if username in users:
        users[username]["password"] = hash_password(new_password)
        save_users(data)

def update_last_login(username: str):
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    if username in users:
        users[username]["last_login"] = datetime.now().isoformat()
        save_users(data)

def delete_user_data(username: str) -> bool:
    import shutil
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    if username not in users: return False
    del users[username]
    save_users(data)
    
    user_dir = Path(os.path.join(config.DATA_DIR, "users", username))
    if user_dir.exists():
        try: shutil.rmtree(user_dir)
        except: pass
    return True

def toggle_user_block(username: str) -> bool:
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    if username not in users: return False
    current = users[username].get("disabled", False)
    users[username]["disabled"] = not current
    save_users(data)
    return not current
