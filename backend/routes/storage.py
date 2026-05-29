"""
Storage Routes - Apenas endpoints únicos:
- POST /storage/rename
- GET  /storage/search

Os demais endpoints de storage (list, folder, upload, download, delete, move,
folder/check-password, folder/set-password, folder/has-password) estão em
/app/backend/server.py.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Storage directory
STORAGE_DIR = ROOT_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

# Security
import jwt
import logging
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'fleet-maintenance-secret-key-2024')

security = HTTPBearer()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return decode_token(credentials.credentials)


# Create router
storage_router = APIRouter(prefix="/storage", tags=["Storage"])


# Models
class RenameItem(BaseModel):
    path: str
    new_name: str


@storage_router.post("/rename")
async def rename_storage_item(
    data: RenameItem,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Rename a file or folder"""
    await get_current_user(credentials)

    path = data.path if data.path.startswith("/") else "/" + data.path

    if "/" in data.new_name or "\\" in data.new_name:
        raise HTTPException(status_code=400, detail="Nome inválido")

    abs_path = STORAGE_DIR / path.lstrip("/")

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Item não encontrado")

    new_path = abs_path.parent / data.new_name

    if new_path.exists():
        raise HTTPException(status_code=400, detail="Já existe um item com este nome")

    try:
        abs_path.rename(new_path)

        if abs_path.is_dir():
            old_rel_path = "/" + str(abs_path.relative_to(STORAGE_DIR)).replace("\\", "/")
            new_rel_path = "/" + str(new_path.relative_to(STORAGE_DIR)).replace("\\", "/")
            await db.folder_passwords.update_one(
                {"path": old_rel_path},
                {"$set": {"path": new_rel_path}}
            )

        # Refletir rename no Drive
        try:
            from utils.storage import drive_rename
            drive_rename(path, data.new_name)
        except Exception as e:
            logger.warning(f"Falha ao renomear no Drive: {e}")

        return {
            "message": "Item renomeado com sucesso",
            "new_path": "/" + str(new_path.relative_to(STORAGE_DIR)).replace("\\", "/")
        }
    except Exception as e:
        logger.error(f"Error renaming item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao renomear: {str(e)}")


@storage_router.get("/search")
async def search_storage(
    query: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Search for files and folders (MongoDB metadata + FS legado)."""
    await get_current_user(credentials)
    from utils.storage_metadata import search as search_meta

    seen_paths = set()
    results = []

    # 1) MongoDB metadata
    try:
        for it in await search_meta(query):
            results.append({
                "name": it.get("name"),
                "type": it.get("type"),
                "path": it.get("path"),
                "size": it.get("size", 0),
            })
            seen_paths.add(it.get("path"))
    except Exception as e:
        logger.warning(f"Mongo search falhou: {e}")

    # 2) Fallback FS legado
    query_lower = query.lower()
    for root, dirs, files in os.walk(STORAGE_DIR):
        for name in dirs + files:
            if query_lower in name.lower():
                full_path = Path(root) / name
                rel_path = "/" + str(full_path.relative_to(STORAGE_DIR)).replace("\\", "/")
                if rel_path in seen_paths:
                    continue
                if full_path.is_dir():
                    results.append({
                        "name": name,
                        "type": "folder",
                        "path": rel_path,
                    })
                else:
                    results.append({
                        "name": name,
                        "type": "file",
                        "path": rel_path,
                        "size": full_path.stat().st_size,
                    })

    return results[:100]
