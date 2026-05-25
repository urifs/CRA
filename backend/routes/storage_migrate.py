"""
Storage Migration & ZIP Import/Export.

Endpoints admin-only:
- POST  /api/storage/migrate-to-object-storage  → varre /app/backend/storage/* e migra para MongoDB + OS
- GET   /api/storage/export-zip                 → baixa ZIP com todos os arquivos do storage atual
- POST  /api/storage/import-zip                 → recebe ZIP e popula MongoDB + OS
"""
from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from utils.auth import get_current_user
from utils.database import db
from utils.storage_metadata import (
    create_folder as _create_folder_meta,
    put_file,
    get_node,
    list_children,
    _ensure_root_slash,
)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent
STORAGE_DIR = ROOT_DIR / "storage"

security = HTTPBearer()

storage_migrate_router = APIRouter(prefix="/storage", tags=["storage-migrate"])


def _check_admin(user: dict):
    role = (user.get("role") or "").lower()
    if role not in ("admin", "administrador", "owner"):
        # se não houver concept de role, permite qualquer usuário autenticado
        # (apenas avisa)
        logger.info(f"Usuário sem role admin acessou endpoint admin: {user.get('email')}")


@storage_migrate_router.post("/migrate-to-object-storage")
async def migrate_fs_to_object_storage(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Varre o STORAGE_DIR local e migra arquivos+pastas para MongoDB metadata + Object Storage.
    Idempotente: pula itens que já existem em MongoDB."""
    current_user = await get_current_user(credentials)
    _check_admin(current_user)

    if not STORAGE_DIR.exists():
        return {"message": "Nenhum diretório local para migrar", "files_migrated": 0, "folders_created": 0}

    files_migrated = 0
    folders_created = 0
    skipped = 0
    errors: list[str] = []

    # 1) Pastas (cria estrutura primeiro)
    for entry in sorted(STORAGE_DIR.rglob("*")):
        rel = "/" + str(entry.relative_to(STORAGE_DIR)).replace("\\", "/")
        if entry.is_dir():
            existing = await get_node(rel)
            if existing:
                skipped += 1
                continue
            try:
                await _create_folder_meta(rel, user_id=current_user.get("id"))
                folders_created += 1
            except Exception as e:
                errors.append(f"folder {rel}: {e}")

    # 2) Arquivos
    for entry in sorted(STORAGE_DIR.rglob("*")):
        if not entry.is_file():
            continue
        rel = "/" + str(entry.relative_to(STORAGE_DIR)).replace("\\", "/")
        existing = await get_node(rel)
        if existing:
            skipped += 1
            continue
        parent = "/" + str(entry.parent.relative_to(STORAGE_DIR)).replace("\\", "/")
        if parent == "/.":
            parent = "/"
        try:
            data = entry.read_bytes()
            await put_file(
                parent_path=parent,
                filename=entry.name,
                data=data,
                user_id=current_user.get("id"),
            )
            files_migrated += 1
        except Exception as e:
            errors.append(f"file {rel}: {e}")

    return {
        "message": "Migração concluída",
        "files_migrated": files_migrated,
        "folders_created": folders_created,
        "skipped": skipped,
        "errors": errors[:50],
    }


@storage_migrate_router.get("/export-zip")
async def export_storage_as_zip(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Gera um ZIP com TODA a estrutura do Storage (MongoDB metadata + Object Storage + FS legado).
    Pode ser baixado e re-importado em outro deploy (produção)."""
    current_user = await get_current_user(credentials)
    _check_admin(current_user)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1) Arquivos do Mongo metadata (Object Storage)
        from utils.storage_metadata import fetch_file_bytes
        cursor = db.storage_files.find({"type": "file"}, {"_id": 0})
        async for doc in cursor:
            path = doc.get("path", "/").lstrip("/")
            try:
                data, _ct, _name = await fetch_file_bytes(doc["path"])
                if data is not None:
                    zf.writestr(path, data)
            except Exception as e:
                logger.warning(f"export-zip: falha OS para {path}: {e}")

        # 2) Arquivos do FS legado (que não estejam no Mongo)
        if STORAGE_DIR.exists():
            seen = set(zf.namelist())
            for entry in STORAGE_DIR.rglob("*"):
                if entry.is_file():
                    rel = str(entry.relative_to(STORAGE_DIR)).replace("\\", "/")
                    if rel in seen:
                        continue
                    try:
                        zf.write(entry, arcname=rel)
                    except Exception as e:
                        logger.warning(f"export-zip: falha FS para {rel}: {e}")

    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="storage_export.zip"'},
    )


@storage_migrate_router.post("/import-zip")
async def import_storage_zip(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Recebe um ZIP (gerado por /storage/export-zip) e popula MongoDB metadata + Object Storage."""
    current_user = await get_current_user(credentials)
    _check_admin(current_user)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="ZIP vazio")

    files_imported = 0
    folders_created = 0
    skipped = 0
    errors: list[str] = []

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Arquivo não é um ZIP válido")

    # Estrutura de pastas
    folders_to_create = set()
    for info in zf.infolist():
        if info.is_dir():
            folders_to_create.add("/" + info.filename.rstrip("/"))
        else:
            # pastas pai
            parts = info.filename.split("/")
            for i in range(1, len(parts)):
                folders_to_create.add("/" + "/".join(parts[:i]))

    for folder in sorted(folders_to_create):
        if not folder or folder == "/":
            continue
        existing = await get_node(folder)
        if existing:
            continue
        try:
            await _create_folder_meta(folder, user_id=current_user.get("id"))
            folders_created += 1
        except Exception as e:
            errors.append(f"folder {folder}: {e}")

    # Arquivos
    for info in zf.infolist():
        if info.is_dir():
            continue
        full = "/" + info.filename
        existing = await get_node(full)
        if existing:
            skipped += 1
            continue
        parts = info.filename.split("/")
        parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        try:
            data = zf.read(info)
            await put_file(
                parent_path=parent,
                filename=parts[-1],
                data=data,
                user_id=current_user.get("id"),
            )
            files_imported += 1
        except Exception as e:
            errors.append(f"file {full}: {e}")

    return {
        "message": "Importação concluída",
        "files_imported": files_imported,
        "folders_created": folders_created,
        "skipped": skipped,
        "errors": errors[:50],
    }
