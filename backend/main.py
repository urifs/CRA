"""
CRA Construtora - Sistema de Gestão Empresarial
Backend API - Versão Refatorada

Estrutura:
- /routes - Rotas da API organizadas por domínio
- /models - Modelos Pydantic
- /utils - Utilitários (auth, database, audit)
- /services - Lógica de negócios (futuro)

Este arquivo é o ponto de entrada da aplicação.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

# Adicionar o diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import client, UPLOAD_DIR

# Importar todos os routers
from routes.all_routes import api_router

# Create the main app
app = FastAPI(
    title="CRA Construtora",
    description="Sistema de Gestão Empresarial - API",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# Shutdown event
@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
