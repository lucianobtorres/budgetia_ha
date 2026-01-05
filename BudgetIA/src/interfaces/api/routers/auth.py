from fastapi import APIRouter, HTTPException, Depends, status
from typing import Any
from pydantic import BaseModel
from datetime import timedelta
import config
from interfaces.api.utils.security import verify_password, get_user, create_user, load_users, set_reset_token, save_users, update_last_login
from core.email_service import EmailService
from interfaces.api.dependencies import get_email_service

from core.logger import get_logger

logger = get_logger("Auth")

router = APIRouter(prefix="/auth", tags=["Autenticação"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    # username: str # Removed, generated auto
    password: str
    name: str
    email: str

class VerifyEmailRequest(BaseModel):
    token: str

@router.post("/login")
def login(data: LoginRequest) -> dict[str, Any]:
    """Valida credenciais do usuário (Username ou Email)."""
    from interfaces.api.utils.security import get_user_by_identifier
    
    logger.info(f"Tentativa de login: {data.username} (Identifier)")
    
    # Busca por ID (User ou Email)
    result = get_user_by_identifier(data.username) 
    
    if not result:
        logger.warning(f"Login falhou: Usuário não encontrado para '{data.username}'")
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    
    username, user = result
    
    if verify_password(data.password, user["password"]):
        # Checa bloqueio administrativo
        if user.get("disabled", False):
             logger.warning(f"Login bloqueado: Conta desativada para {username}")
             raise HTTPException(status_code=403, detail="Sua conta foi bloqueada pelo administrador.")

        # Checa se email foi verificado (Apenas em modo SAAS)
        if config.DEPLOY_MODE == "SAAS":
             is_verified = user.get("email_verified", True) # Default True
             
             if is_verified is False:
                 logger.warning(f"Login bloqueado: Email não verificado para {username}")
                 raise HTTPException(status_code=403, detail="Email não verificado. Verifique sua caixa de entrada.")
        
        from interfaces.api.utils.jwt import create_access_token
        
        # Registra login
        update_last_login(username)
        
        access_token_expires = timedelta(minutes=float(config.ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": username,
                "name": user["name"],
                "role": user.get("role", "user"),
                "trial_ends_at": user.get("trial_ends_at"),
                "deploy_mode": config.DEPLOY_MODE
            }
        }
    
    raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

@router.post("/register")
async def register(
    data: RegisterRequest, 
    email_service: EmailService = Depends(get_email_service)
) -> dict[str, str]:
    """Registra novo usuário e envia email de verificação."""
    logger.info(f"Nova tentativa de registro: {data.name} <{data.email}>")
    
    # Validações básicas
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no mínimo 6 caracteres")

    # 1. Gerar Username único a partir do Email
    base_username = data.email.split("@")[0].lower()
    # Remove caracteres especiais
    import re
    base_username = re.sub(r'[^a-z0-9._]', '', base_username)
    
    # Verifica colisões
    final_username = base_username
    users_db = load_users()
    existing_usernames = users_db.get("credentials", {}).get("usernames", {})
    
    # Check extra se o EMAIL já existe
    for u_data in existing_usernames.values():
        if u_data.get("email") == data.email:
             raise HTTPException(status_code=409, detail="Email já cadastrado.")

    counter = 1
    while final_username in existing_usernames:
        final_username = f"{base_username}{counter}"
        counter += 1
    
    # 2. Cria usuário
    if create_user(final_username, data.name, data.email, data.password):
        users_db = load_users()
        existing_users_count = len(users_db.get("credentials", {}).get("usernames", {}))
        
        is_self_hosted = config.DEPLOY_MODE == "SELF_HOSTED"
        
        # --- Lógica de Auto-Admin (Self-Hosted) ---
        # Se for o PRIMEIRO e ÚNICO usuário criado (count == 1 pois acabamos de criar)
        # E estivermos em modo SELF_HOSTED, promove a Admin
        role = "user"
        if is_self_hosted and existing_users_count == 1:
            users_db["credentials"]["usernames"][final_username]["role"] = "admin"
            role = "admin"
            logger.info(f"👑 Primeiro usuário '{final_username}' promovido a ADMIN automaticamente (Modo: {config.DEPLOY_MODE})")

        # Configura verificação
        import secrets
        verification_token = secrets.token_urlsafe(32)
        users_db["credentials"]["usernames"][final_username]["verification_token"] = verification_token if not is_self_hosted else None
        users_db["credentials"]["usernames"][final_username]["email_verified"] = is_self_hosted
        
        save_users(users_db)
        
        if not is_self_hosted:
            # Tenta enviar email
            sent = email_service.send_verification_email(data.email, verification_token, data.name)
            if sent:
                return {"message": "Usuário criado. Verifique seu email.", "username": final_username}
            else:
                # Fallback se email falhar
                logger.warning("Falha no envio de email de verificação.")
                return {"message": "Usuário criado, mas houve erro no envio do email.", "username": final_username}
        else:
            msg = "Usuário criado com sucesso!"
            if role == "admin":
                msg += " (Admin)"
            return {"message": msg, "username": final_username}
    
    raise HTTPException(status_code=409, detail="Erro ao criar usuário")

@router.post("/verify-email")
def verify_email(data: VerifyEmailRequest) -> dict[str, str]:
    """Verifica o email usando o token."""
    logger.info(f"Recebendo requisição de verificação.")
    
    users_db = load_users()
    users = users_db.get("credentials", {}).get("usernames", {})
    
    target_username = None
    for uname, info in users.items():
        if info.get("verification_token") == data.token:
            target_username = uname
            break
            
    if not target_username:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
        
    users_db["credentials"]["usernames"][target_username]["email_verified"] = True
    users_db["credentials"]["usernames"][target_username]["verification_token"] = None 
    save_users(users_db)
    
    return {"message": "Email verificado com sucesso!"}

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
async def forgot_password_endpoint(
    data: ForgotPasswordRequest,
    email_service: EmailService = Depends(get_email_service)
) -> dict[str, str]:
    """Inicia fluxo de recuperação de senha."""
    import secrets
    
    users_data = load_users().get("credentials", {}).get("usernames", {})
    target_username = None
    
    for username, info in users_data.items():
        if info.get("email") == data.email:
            target_username = username
            break
            
    if target_username:
        token = secrets.token_urlsafe(32)
        set_reset_token(target_username, token)
        
        # Tenta enviar email via serviço
        email_sent = email_service.send_password_reset(data.email, token)
        
        # --- Fallback Local (Self-Hosted) ---
        # Se email falhou (ou não configurado) E estamos em modo Self-Hosted/Dev
        # Logamos o token para recuperação manual
        if not email_sent or config.DEPLOY_MODE == "SELF_HOSTED":
             if not config.RESEND_API_KEY:
                 print("\n" + "="*60)
                 print(f"🔐 [LOCAL RESET] Token de recuperação para {target_username}:")
                 print(f"Token: {token}")
                 print(f"Link:  http://homeassistant.local:8123/api/hassio_ingress/blah/reset-password?token={token}") 
                 print("="*60 + "\n")
                 logger.warning(f"Token de reset logado no console para {target_username} (Email Service inativo).")

    # Sempre retorna sucesso por segurança
    return {"message": "Se o email existir, as instruções foram enviadas (ou verifique os logs do servidor)."}

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest) -> dict[str, str]:
    """Redefine a senha usando o token."""
    from interfaces.api.utils.security import get_user_by_reset_token, update_password, clear_reset_token
    
    result = get_user_by_reset_token(data.token)
    if not result:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
        
    username, _ = result
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 6 caracteres")
        
    update_password(username, data.new_password)
    clear_reset_token(username)
    
    return {"message": "Senha redefinida com sucesso."}
