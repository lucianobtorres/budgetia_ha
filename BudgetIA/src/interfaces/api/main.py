from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import APIRouter
import os
import uvicorn

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
    intelligence,
    admin,
    subscription, 
    system,
    categories,
    imports,
    ocr, # <--- Novo
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

# Configuração de CORS (Flexível para Docker/Home Assistant)
# Permite definir origens via variável de ambiente (separadas por vírgula)
# Ex: ALLOWED_ORIGINS="https://homeassistant.local:8123,http://192.168.1.100:8123"
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

# Adiciona defaults locais essenciais
default_origins = [
    "http://localhost:5173",  # Vite Dev
    "http://localhost:4173",  # Vite Preview
    "http://localhost:8000",  # API Local
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

# Unifica garantindo unicidade
final_origins = list(set(allowed_origins + default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=final_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Rotas
# Criar Router Principal da API
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
api_router.include_router(intelligence.router)
api_router.include_router(admin.router)
api_router.include_router(subscription.router)
api_router.include_router(system.router)
api_router.include_router(categories.router)
api_router.include_router(imports.router)
api_router.include_router(ocr.router) # <--- Novo

# Incluir na App Principal
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    import logging
    from core.logger import EndpointFilter, app_logger
    
    # Configura filtro para reduzir ruído de logs de acesso
    access_logger = logging.getLogger("uvicorn.access")
    # Filtra requisições de arquivos estáticos do PWA
    access_logger.addFilter(EndpointFilter(path="/pwa-"))
    access_logger.addFilter(EndpointFilter(path="/assets/"))
    
    app_logger.info("Sistema Log de Acessos configurado: Filtros ativos para /pwa e /assets.")


if __name__ == "__main__":
    # Permite rodar diretamente via 'python src/api/main.py'
    uvicorn.run("interfaces.api.main:app", host="0.0.0.0", port=8000, reload=True)

# --- Serving Static Files (Frontend) for Docker/Add-on ---
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
