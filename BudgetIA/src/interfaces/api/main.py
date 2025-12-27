from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interfaces.api.routers import (
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
    telemetry,
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
# Criar Router Principal da API
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(dashboard.router)
api_router.include_router(transactions.router)
api_router.include_router(budgets.router)
api_router.include_router(profile.router)
api_router.include_router(jobs.router)
api_router.include_router(notifications.router)
api_router.include_router(presence.router)
api_router.include_router(auth.router)
api_router.include_router(onboarding.router)
api_router.include_router(telemetry.router)

# Incluir na App Principal
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    # Permite rodar diretamente via 'python src/api/main.py'
    uvicorn.run("interfaces.api.main:app", host="0.0.0.0", port=8000, reload=True)

# --- Serving Static Files (Frontend) for Docker/Add-on ---
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check where the static files are (configured in Dockerfile)
STATIC_DIR = os.getenv("STATIC_DIR", "/app/static")

if os.path.isdir(STATIC_DIR):
    # Mount assets (js, css, etc)
    app.mount("/assets", StaticFiles(directory=f"{STATIC_DIR}/assets"), name="assets")
    
    # Catch-all for SPA (Single Page Application)
    # Any route that is not API should return index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API routes to bubble up (already handled above if matched)
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
            return {"error": "Not Found"}
            
        # Check if file exists in static root (e.g. favicon.ico, manifest.json)
        potential_file = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(potential_file):
            return FileResponse(potential_file)
            
        # Default to index.html for React Router
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

