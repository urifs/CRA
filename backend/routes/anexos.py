"""
Anexos Genéricos - Sistema unificado de anexos para qualquer entidade do ERP.

Suporta duas origens:
1. "local"  - arquivo enviado pelo computador (multipart). Salvo em uploads/anexos/.
2. "storage" - referência a um arquivo do módulo Armazenamento (não duplica).

Endpoints:
- POST   /api/anexos/{entity_type}/{entity_id}/upload          Upload local
- POST   /api/anexos/{entity_type}/{entity_id}/from-storage    Anexar do armazenamento
- GET    /api/anexos/{entity_type}/{entity_id}                 Lista anexos da entidade
- DELETE /api/anexos/{entity_type}/{entity_id}/{anexo_id}      Remove anexo
- GET    /api/anexos/download/{anexo_id}                       Download (local ou storage)
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import os
import uuid
import logging

import jwt
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ.get("JWT_SECRET", "fleet-maintenance-secret-key-2024")

ANEXOS_DIR = ROOT_DIR / "uploads" / "anexos"
ANEXOS_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR = ROOT_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

MAX_BYTES = 50 * 1024 * 1024  # 50MB

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

anexos_router = APIRouter(prefix="/anexos", tags=["anexos"])

VALID_ENTITY_TYPES = {
    # Financeiro / Admin
    "cadastro", "produto", "conta_pagar", "conta_receber", "centro_custo",
    "plano_contas", "conta_bancaria", "forma_pagamento", "aluguel", "imovel",
    "ordem_servico", "categoria",
    # Gerenciamento
    "maquina", "manutencao", "estoque", "obra", "fleet",
    "medicao", "horimetro", "combustivel", "abastecedor",
    # RH
    "funcionario", "folha_pagamento", "solicitacao_folha", "ferias",
    "banco_horas", "epi", "epi_ficha", "custo_rh", "abono",
    # Outros
    "notificacao", "importacao_nf", "emissao_nf", "conciliacao",
}


async def _verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="Token inválido")


def _validate_entity_type(entity_type: str):
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"entity_type inválido: '{entity_type}'. Aceitos: {sorted(VALID_ENTITY_TYPES)}",
        )


@anexos_router.get("/download/{anexo_id}")
async def download_anexo(
    anexo_id: str,
    token: Optional[str] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
):
    """Download do anexo (local ou storage). Aceita ?token= para uso em <iframe>."""
    if credentials and credentials.credentials:
        try:
            jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise HTTPException(status_code=401, detail="Token inválido")
    elif token:
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise HTTPException(status_code=401, detail="Token inválido")
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

    anexo = await db.entity_anexos.find_one({"id": anexo_id}, {"_id": 0})
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")

    if anexo["source"] == "local":
        file_path = ANEXOS_DIR / anexo["filename"]
    else:
        file_path = STORAGE_DIR / anexo["storage_path"].lstrip("/")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado")

    return FileResponse(
        path=str(file_path),
        filename=anexo.get("original_name") or file_path.name,
        media_type=anexo.get("content_type") or "application/octet-stream",
    )


@anexos_router.get("/{entity_type}/{entity_id}")
async def list_anexos(
    entity_type: str,
    entity_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista todos os anexos de uma entidade específica."""
    await _verify_token(credentials)
    _validate_entity_type(entity_type)

    anexos = await db.entity_anexos.find(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0},
    ).sort("uploaded_at", -1).to_list(500)

    return {"items": anexos, "count": len(anexos)}


@anexos_router.post("/{entity_type}/{entity_id}/upload")
async def upload_anexo_local(
    entity_type: str,
    entity_id: str,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Upload de arquivo do computador para a entidade."""
    payload = await _verify_token(credentials)
    _validate_entity_type(entity_type)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"Arquivo muito grande. Máximo: {MAX_BYTES // (1024*1024)}MB")

    ext = Path(file.filename).suffix.lower() if file.filename else ""
    unique = f"{entity_type}_{entity_id}_{uuid.uuid4()}{ext}"
    target = ANEXOS_DIR / unique
    with open(target, "wb") as f:
        f.write(content)

    anexo = {
        "id": str(uuid.uuid4()),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "source": "local",
        "filename": unique,
        "original_name": file.filename or unique,
        "storage_path": None,
        "size": len(content),
        "content_type": file.content_type or "application/octet-stream",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": payload.get("user_id") or payload.get("sub") or "system",
    }
    await db.entity_anexos.insert_one(anexo)
    anexo.pop("_id", None)
    return {"message": "Anexo enviado", "anexo": anexo}


@anexos_router.post("/{entity_type}/{entity_id}/from-storage")
async def attach_from_storage(
    entity_type: str,
    entity_id: str,
    body: dict = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Anexa por REFERÊNCIA um arquivo já existente no módulo Armazenamento.

    Body: { storage_path: "/Pasta/arquivo.pdf" }
    Aceita também storage_paths: [...] para múltiplas seleções.
    """
    payload = await _verify_token(credentials)
    _validate_entity_type(entity_type)

    paths = body.get("storage_paths") or ([body.get("storage_path")] if body.get("storage_path") else [])
    paths = [p for p in paths if p]
    if not paths:
        raise HTTPException(status_code=400, detail="storage_path ou storage_paths é obrigatório")

    created = []
    for path in paths:
        if not path.startswith("/"):
            path = "/" + path
        abs_path = STORAGE_DIR / path.lstrip("/")
        if not abs_path.exists() or not abs_path.is_file():
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado no armazenamento: {path}")

        anexo = {
            "id": str(uuid.uuid4()),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "source": "storage",
            "filename": abs_path.name,
            "original_name": abs_path.name,
            "storage_path": path,
            "size": abs_path.stat().st_size,
            "content_type": _guess_content_type(abs_path.suffix.lower()),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "uploaded_by": payload.get("user_id") or payload.get("sub") or "system",
        }
        await db.entity_anexos.insert_one(anexo)
        anexo.pop("_id", None)
        created.append(anexo)

    return {"message": f"{len(created)} anexo(s) vinculado(s)", "anexos": created}


@anexos_router.delete("/{entity_type}/{entity_id}/{anexo_id}")
async def delete_anexo(
    entity_type: str,
    entity_id: str,
    anexo_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Remove o vínculo do anexo. Se for 'local', apaga o arquivo do disco.
    Se for 'storage', mantém o arquivo no armazenamento (só remove o link)."""
    await _verify_token(credentials)
    _validate_entity_type(entity_type)

    anexo = await db.entity_anexos.find_one(
        {"id": anexo_id, "entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0},
    )
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")

    if anexo.get("source") == "local" and anexo.get("filename"):
        try:
            (ANEXOS_DIR / anexo["filename"]).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Falha ao remover arquivo local de anexo: {e}")

    await db.entity_anexos.delete_one({"id": anexo_id})
    return {"message": "Anexo removido"}


def _guess_content_type(ext: str) -> str:
    mapping = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".txt": "text/plain", ".csv": "text/csv",
        ".json": "application/json", ".xml": "application/xml",
        ".mp4": "video/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav",
        ".zip": "application/zip",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return mapping.get(ext, "application/octet-stream")
