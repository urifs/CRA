"""
Storage Routes - File Manager system
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timezone
import os
import shutil
import bcrypt
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
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return decode_token(credentials.credentials)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Create router
storage_router = APIRouter(prefix="/storage", tags=["Storage"])


# Models
class FolderCreate(BaseModel):
    name: str
    parent_path: str = "/"
    password: Optional[str] = None


class FolderPasswordCheck(BaseModel):
    path: str
    password: str


class FolderPasswordSet(BaseModel):
    path: str
    password: Optional[str] = None


class RenameItem(BaseModel):
    path: str
    new_name: str


class MoveItem(BaseModel):
    source_path: str
    dest_path: str


@storage_router.get("/list")
async def list_storage_items(
    path: str = "/",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List files and folders in a path"""
    await get_current_user(credentials)
    
    if not path.startswith("/"):
        path = "/" + path
    
    abs_path = STORAGE_DIR / path.lstrip("/")
    
    if not abs_path.exists():
        abs_path.mkdir(parents=True, exist_ok=True)
    
    protected_folders = await db.folder_passwords.find({}, {"_id": 0, "path": 1}).to_list(1000)
    protected_paths = {f["path"] for f in protected_folders}
    
    items = []
    try:
        for entry in abs_path.iterdir():
            rel_path = "/" + str(entry.relative_to(STORAGE_DIR)).replace("\\", "/")
            
            if entry.is_dir():
                items_count = len(list(entry.iterdir())) if entry.exists() else 0
                items.append({
                    "name": entry.name,
                    "type": "folder",
                    "path": rel_path,
                    "items_count": items_count,
                    "modified_at": datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "has_password": rel_path in protected_paths
                })
            else:
                items.append({
                    "name": entry.name,
                    "type": "file",
                    "path": rel_path,
                    "size": entry.stat().st_size,
                    "modified_at": datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                })
    except Exception as e:
        logger.error(f"Error listing storage: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar arquivos: {str(e)}")
    
    items.sort(key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower()))
    
    return items


@storage_router.post("/folder")
async def create_folder(
    data: FolderCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new folder"""
    current_user = await get_current_user(credentials)
    
    if not data.name or "/" in data.name or "\\" in data.name:
        raise HTTPException(status_code=400, detail="Nome de pasta inválido")
    
    parent = data.parent_path if data.parent_path.startswith("/") else "/" + data.parent_path
    full_path = STORAGE_DIR / parent.lstrip("/") / data.name
    folder_path = "/" + str(full_path.relative_to(STORAGE_DIR)).replace("\\", "/")
    
    if full_path.exists():
        raise HTTPException(status_code=400, detail="Pasta já existe")
    
    try:
        full_path.mkdir(parents=True, exist_ok=False)
        
        if data.password:
            password_hash = hash_password(data.password)
            await db.folder_passwords.update_one(
                {"path": folder_path},
                {"$set": {
                    "path": folder_path,
                    "password_hash": password_hash,
                    "created_by": current_user["id"],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        return {"message": "Pasta criada com sucesso", "path": folder_path, "has_password": bool(data.password)}
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar pasta: {str(e)}")


@storage_router.post("/folder/check-password")
async def check_folder_password(
    data: FolderPasswordCheck,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verifica se a senha da pasta está correta"""
    await get_current_user(credentials)
    
    path = data.path if data.path.startswith("/") else "/" + data.path
    folder_record = await db.folder_passwords.find_one({"path": path}, {"_id": 0})
    
    if not folder_record:
        return {"valid": True, "message": "Pasta não possui senha"}
    
    if verify_password(data.password, folder_record["password_hash"]):
        return {"valid": True, "message": "Senha correta"}
    else:
        raise HTTPException(status_code=401, detail="Senha incorreta")


@storage_router.post("/folder/set-password")
async def set_folder_password(
    data: FolderPasswordSet,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Define ou remove a senha de uma pasta"""
    current_user = await get_current_user(credentials)
    
    path = data.path if data.path.startswith("/") else "/" + data.path
    abs_path = STORAGE_DIR / path.lstrip("/")
    
    if not abs_path.exists() or not abs_path.is_dir():
        raise HTTPException(status_code=404, detail="Pasta não encontrada")
    
    if data.password:
        password_hash = hash_password(data.password)
        await db.folder_passwords.update_one(
            {"path": path},
            {"$set": {
                "path": path,
                "password_hash": password_hash,
                "updated_by": current_user["id"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        return {"message": "Senha definida com sucesso", "has_password": True}
    else:
        await db.folder_passwords.delete_one({"path": path})
        return {"message": "Senha removida com sucesso", "has_password": False}


@storage_router.get("/folder/has-password")
async def check_folder_has_password(
    path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verifica se uma pasta possui senha"""
    await get_current_user(credentials)
    
    if not path.startswith("/"):
        path = "/" + path
    
    folder_record = await db.folder_passwords.find_one({"path": path}, {"_id": 0})
    return {"has_password": folder_record is not None}


@storage_router.post("/upload")
async def upload_storage_file(
    file: UploadFile = File(...),
    path: str = Form("/"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload a file to storage"""
    current_user = await get_current_user(credentials)
    
    if not path.startswith("/"):
        path = "/" + path
    
    dir_path = STORAGE_DIR / path.lstrip("/")
    dir_path.mkdir(parents=True, exist_ok=True)
    
    content = await file.read()
    filename = file.filename or "arquivo"
    file_path = dir_path / filename
    
    counter = 1
    base_name = Path(filename).stem
    ext = Path(filename).suffix
    while file_path.exists():
        filename = f"{base_name}_{counter}{ext}"
        file_path = dir_path / filename
        counter += 1
    
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        
        rel_path = "/" + str(file_path.relative_to(STORAGE_DIR)).replace("\\", "/")
        
        return {
            "message": "Arquivo enviado com sucesso",
            "path": rel_path,
            "filename": filename,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar arquivo: {str(e)}")


@storage_router.get("/download")
async def download_storage_file(
    path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Download a file from storage"""
    await get_current_user(credentials)
    
    if not path.startswith("/"):
        path = "/" + path
    
    file_path = STORAGE_DIR / path.lstrip("/")
    
    if not file_path.exists() or file_path.is_dir():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@storage_router.delete("/delete")
async def delete_storage_item(
    path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a file or folder from storage"""
    current_user = await get_current_user(credentials)
    
    if not path.startswith("/"):
        path = "/" + path
    
    if path == "/" or path == "":
        raise HTTPException(status_code=400, detail="Não é possível excluir a pasta raiz")
    
    abs_path = STORAGE_DIR / path.lstrip("/")
    
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    try:
        if abs_path.is_dir():
            await db.folder_passwords.delete_one({"path": path})
            shutil.rmtree(abs_path)
            return {"message": "Pasta excluída com sucesso"}
        else:
            abs_path.unlink()
            return {"message": "Arquivo excluído com sucesso"}
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {str(e)}")


@storage_router.post("/rename")
async def rename_storage_item(
    data: RenameItem,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Rename a file or folder"""
    current_user = await get_current_user(credentials)
    
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
        
        return {
            "message": "Item renomeado com sucesso",
            "new_path": "/" + str(new_path.relative_to(STORAGE_DIR)).replace("\\", "/")
        }
    except Exception as e:
        logger.error(f"Error renaming item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao renomear: {str(e)}")


@storage_router.post("/move")
async def move_storage_item(
    data: MoveItem,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Move a file or folder to another location"""
    current_user = await get_current_user(credentials)
    
    source = data.source_path if data.source_path.startswith("/") else "/" + data.source_path
    dest = data.dest_path if data.dest_path.startswith("/") else "/" + data.dest_path
    
    source_abs = STORAGE_DIR / source.lstrip("/")
    dest_abs = STORAGE_DIR / dest.lstrip("/")
    
    if not source_abs.exists():
        raise HTTPException(status_code=404, detail="Item de origem não encontrado")
    
    dest_abs.mkdir(parents=True, exist_ok=True)
    new_path = dest_abs / source_abs.name
    
    if new_path.exists():
        raise HTTPException(status_code=400, detail="Já existe um item com este nome no destino")
    
    try:
        shutil.move(str(source_abs), str(new_path))
        
        if source_abs.is_dir():
            old_rel = "/" + str(source_abs.relative_to(STORAGE_DIR)).replace("\\", "/")
            new_rel = "/" + str(new_path.relative_to(STORAGE_DIR)).replace("\\", "/")
            await db.folder_passwords.update_one(
                {"path": old_rel},
                {"$set": {"path": new_rel}}
            )
        
        return {
            "message": "Item movido com sucesso",
            "new_path": "/" + str(new_path.relative_to(STORAGE_DIR)).replace("\\", "/")
        }
    except Exception as e:
        logger.error(f"Error moving item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao mover: {str(e)}")


@storage_router.get("/search")
async def search_storage(
    query: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Search for files and folders"""
    await get_current_user(credentials)
    
    results = []
    query_lower = query.lower()
    
    for root, dirs, files in os.walk(STORAGE_DIR):
        for name in dirs + files:
            if query_lower in name.lower():
                full_path = Path(root) / name
                rel_path = "/" + str(full_path.relative_to(STORAGE_DIR)).replace("\\", "/")
                
                if full_path.is_dir():
                    results.append({
                        "name": name,
                        "type": "folder",
                        "path": rel_path
                    })
                else:
                    results.append({
                        "name": name,
                        "type": "file",
                        "path": rel_path,
                        "size": full_path.stat().st_size
                    })
    
    return results[:50]
