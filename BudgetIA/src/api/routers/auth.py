from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.utils.security import verify_password, get_user, create_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str

@router.post("/login")
def login(data: LoginRequest):
    """Valida credenciais do usuário."""
    user = get_user(data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    
    if verify_password(data.password, user["password"]):
        return {
            "message": "Login realizado com sucesso",
            "user": {
                "username": data.username,
                "name": user["name"],
                "email": user["email"]
            }
        }
    
    raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

@router.post("/register")
def register(data: RegisterRequest):
    """Registra novo usuário."""
    # Validações básicas
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no mínimo 6 caracteres")
    
    if create_user(data.username, data.name, data.email, data.password):
        return {"message": "Usuário criado com sucesso"}
    
    raise HTTPException(status_code=409, detail="Usuário já existe")
