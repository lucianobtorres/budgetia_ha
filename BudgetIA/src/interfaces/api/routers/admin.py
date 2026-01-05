from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from interfaces.api.utils.security import load_users, save_users, get_user
from interfaces.api.utils.jwt import create_access_token
from interfaces.api.dependencies import get_current_user
import config

router = APIRouter(prefix="/admin", tags=["Admin"])



class UserSummary(BaseModel):
    username: str
    name: str
    email: str
    role: str
    created_at: str
    last_login: Optional[str]
    trial_ends_at: Optional[str]
    status: str
    is_blocked: Optional[bool]

def verify_admin_role(current_user: dict = Depends(get_current_user)):
    user = get_user(current_user["username"])
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado. Requer privilégios de administrador.")
    return user

@router.get("/users", response_model=List[UserSummary])
def list_users(admin: dict = Depends(verify_admin_role)):
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    
    summary_list = []
    now = datetime.now()
    
    for username, info in users.items():
        role = info.get("role", "user")
        trial_end = info.get("trial_ends_at")
        disabled = info.get("disabled", False)
        
        status = "ACTIVE"
        if disabled:
            status = "BLOCKED"
        elif role == "admin":
            status = "ADMIN"
        elif trial_end:
            try:
                end_dt = datetime.fromisoformat(trial_end)
                if end_dt < now:
                    status = "EXPIRED"
                else:
                    status = "TRIAL"
            except:
                status = "ACTIVE" # Fallback
                
        summary_list.append(UserSummary(
            username=username,
            name=info.get("name", username),
            email=info.get("email", ""),
            role=role,
            created_at=info.get("created_at", now.isoformat()),
            last_login=info.get("last_login"),
            trial_ends_at=trial_end,
            status=status,
            is_blocked=disabled
        ))
        
    return summary_list

@router.post("/users/{username}/extend-trial")
def extend_trial(username: str, admin: dict = Depends(verify_admin_role)):
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    
    if username not in users:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    current_end = users[username].get("trial_ends_at")
    now = datetime.now()
    
    try:
        if current_end:
            curr_dt = datetime.fromisoformat(current_end)
            if curr_dt < now:
                # Se já venceu, reinicia conta de 14 dias a partir de agora
                new_dt = now + timedelta(days=14)
            else:
                # Se ainda ativo, soma 14 dias ao final atual
                new_dt = curr_dt + timedelta(days=14)
        else:
            # Nunca teve trial (antigo?), dá 14 dias
            new_dt = now + timedelta(days=14)
            
        users[username]["trial_ends_at"] = new_dt.isoformat()
        save_users(data)
        
        return {"message": f"Trial estendido até {new_dt.date()}"}

    except Exception as e:
        import logging
        logging.error(f"Erro extendendo trial: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar data: {str(e)}")

@router.post("/users/{username}/reset-trial")
def reset_trial(username: str, admin: dict = Depends(verify_admin_role)):
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    
    if username not in users:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    # Reset to default 14 days from now
    new_dt = datetime.now() + timedelta(days=14)
    
    users[username]["trial_ends_at"] = new_dt.isoformat()
    save_users(data)
    
    return {"message": f"Trial restaurado para 14 dias (até {new_dt.date()})"}

class ImpersonateRequest(BaseModel):
    target_username: str

@router.post("/impersonate")
def impersonate_user(req: ImpersonateRequest, admin: dict = Depends(verify_admin_role)):
    """Gera token de acesso para outro usuário (apenas Admin)."""
    target = get_user(req.target_username)
    
    if not target:
        raise HTTPException(status_code=404, detail="Usuário alvo não encontrado")
        
    if target.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Não é permitido impersonar outro administrador.")
        
    access_token = create_access_token(
        data={"sub": req.target_username}, 
        expires_delta=timedelta(minutes=60)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.delete("/users/{username}")
def delete_user_endpoint(username: str, admin: dict = Depends(verify_admin_role)):
    from interfaces.api.utils.security import delete_user_data
    if delete_user_data(username):
        return {"message": "Usuário deletado."}
    raise HTTPException(status_code=404, detail="Usuário não encontrado.")

@router.post("/users/{username}/toggle-block")
def toggle_block_endpoint(username: str, admin: dict = Depends(verify_admin_role)):
    from interfaces.api.utils.security import toggle_user_block
    new_state = toggle_user_block(username)
    return {"message": "Bloqueado" if new_state else "Desbloqueado", "is_blocked": new_state}

class BroadcastRequest(BaseModel):
    message: str
    title: str = "Mensagem do Admin"
    category: str = "financial_alert"
    priority: str = "normal"
    target_usernames: Optional[List[str]] = None # None or Empty = All
    send_notification: bool = True
    send_email: bool = False
    is_system_banner: bool = False

@router.post("/broadcast")
def send_broadcast(req: BroadcastRequest, admin: dict = Depends(verify_admin_role)):
    """Envia notificação para um ou todos os usuários."""
    from interfaces.api.dependencies import get_notification_service, get_push_notification_service
    from core.user_config_service import UserConfigService
    from application.services.notification_service import NotificationService
    from application.services.push_notification_service import PushNotificationService
    from core.email_service import EmailService
    import json
    import os
    
    data = load_users()
    users = data.get("credentials", {}).get("usernames", {})
    
    targets = []
    if req.target_usernames and len(req.target_usernames) > 0:
        # Validate targets
        for u in req.target_usernames:
            if u in users:
                targets.append(u)
    else:
        # All users
        targets = list(users.keys())
        
    notif_count = 0
    email_count = 0
    
    # 1. Send In-App / Push Notifications
    for username in targets:
        try:
            # Instantiate services for specific user
            config_service = UserConfigService(username)
            push_service = PushNotificationService(config_service.config_dir) # Reusing dependency logic
            notif_service = NotificationService(config_service, push_service)
            
            # 1. Notification (Optional)
            if req.send_notification:
                notif_service.add_notification(
                    message=req.message,
                    category=req.category,
                    priority=req.priority
                )
                notif_count += 1
            
            # 2. Add Email Logic (Optional)
            if req.send_email:
                user_email = users[username].get("email")
                if user_email:
                    EmailService.send_email(
                        to=user_email,
                        subject=req.title,
                        html_content=f"<p>{req.message}</p>"
                    )
                    email_count += 1
                    
        except Exception as e:
            # Log but don't fail entire batch
            import logging
            logging.error(f"Falha ao enviar broadcast para {username}: {e}")

    # 3. System Banner Logic
    if req.is_system_banner:
        try:
            banner_data = {
                "id": str(int(datetime.now().timestamp())),
                "is_active": True,
                "message": req.message,
                "level": "info",
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat() # Default 24h
            }
            # Path matching system.py
            banner_path = os.path.join(os.getcwd(), "data", "system_status.json")
            os.makedirs(os.path.dirname(banner_path), exist_ok=True)
            with open(banner_path, "w", encoding="utf-8") as f:
                json.dump(banner_data, f)
        except Exception as e:
            import logging
            logging.error(f"Erro salvando banner do sistema: {e}")
            
    return {
        "message": f"Processamento concluído para {len(targets)} usuários.",
        "notifications_sent": notif_count,
        "emails_sent": email_count,
        "banner_active": req.is_system_banner
    }
