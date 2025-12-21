from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    auth,
    budgets,
    chat,
    dashboard,
    health,
    jobs,
    notifications,
    onboarding,
    presence,
    profile,
    transactions,
)

description = """
# BudgetIA API 💰
API Rest para gerenciamento financeiro pessoal assistido por IA.

## Recursos
* **Transações**: Leitura e escrita na planilha mestra.
* **Health**: Verificação de status do serviço.
"""

app = FastAPI(
    title="BudgetIA API",
    description=description,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS (Permite que React/Frontend externo acesse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Rotas
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(profile.router)
app.include_router(jobs.router)
app.include_router(notifications.router)
app.include_router(presence.router)
app.include_router(auth.router)
app.include_router(onboarding.router)

if __name__ == "__main__":
    import uvicorn
    # Permite rodar diretamente via 'python src/api/main.py'
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
