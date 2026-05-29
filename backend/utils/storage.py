"""Helper para armazenamento de arquivos com fallback automático.

Se o Google Drive estiver conectado, arquivos são gravados lá com a hierarquia
``CRA-ERP/<path-sem-prefixo-cra-erp>``. Caso contrário, vão para o Emergent Object
Storage. A interface ``put_object`` / ``get_object`` é mantida idêntica.

Para evitar conflitos entre Motor (async) e contextos síncronos, esse módulo usa
PyMongo síncrono para o índice ``storage_index`` e ``drive_credentials``.
"""
from __future__ import annotations

import io
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import requests
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from pymongo import MongoClient

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "cra-erp"
DRIVE_ROOT = "CRA-ERP"
SCOPES = ["https://www.googleapis.com/auth/drive"]
WORKSPACE_KEY = "workspace"

_storage_key: Optional[str] = None
_mongo: Optional[MongoClient] = None


def _get_emergent_key() -> str:
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY não configurado em backend/.env")
    return key


def _sync_db():
    global _mongo
    if _mongo is None:
        _mongo = MongoClient(os.environ["MONGO_URL"], tz_aware=True)
    return _mongo[os.environ["DB_NAME"]]


def init_storage(force: bool = False) -> str:
    """Inicializa (ou reusa) a sessão do Object Storage."""
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    resp = requests.post(
        f"{STORAGE_URL}/init",
        json={"emergent_key": _get_emergent_key()},
        timeout=30,
    )
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    logger.info("Object storage inicializado")
    return _storage_key


# ---------------- Object Storage primitives ----------------

def _put_object_emergent(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    try:
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120,
        )
        if resp.status_code == 403:
            key = init_storage(force=True)
            resp = requests.put(
                f"{STORAGE_URL}/objects/{path}",
                headers={"X-Storage-Key": key, "Content-Type": content_type},
                data=data,
                timeout=120,
            )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error("put_object (emergent) falhou: %s - %s", e, resp.text[:200] if resp else "")
        raise


def _get_object_emergent(path: str) -> tuple[bytes, str]:
    key = init_storage()
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    if resp.status_code == 403:
        key = init_storage(force=True)
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


# ---------------- Google Drive (sync) ----------------

def _drive_credentials_doc() -> Optional[dict]:
    return _sync_db().drive_credentials.find_one({"key": WORKSPACE_KEY})


def _drive_service():
    """Returns a built Drive service or None if not connected. Refreshes token if needed."""
    doc = _drive_credentials_doc()
    if not doc:
        return None
    creds = Credentials(
        token=doc["access_token"],
        refresh_token=doc.get("refresh_token"),
        token_uri=doc["token_uri"],
        client_id=doc["client_id"],
        client_secret=doc["client_secret"],
        scopes=doc.get("scopes") or SCOPES,
    )
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            _sync_db().drive_credentials.update_one(
                {"key": WORKSPACE_KEY},
                {
                    "$set": {
                        "access_token": creds.token,
                        "expiry": creds.expiry.replace(tzinfo=timezone.utc).isoformat()
                        if creds.expiry
                        else None,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Failed to refresh Drive token: %s", e)
            return None
    try:
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:  # noqa: BLE001
        logger.exception("Failed to build Drive service: %s", e)
        return None


def _find_or_create_folder(service, name: str, parent_id: Optional[str]) -> str:
    safe = name.replace("'", "\\'")
    q = f"name = '{safe}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = service.files().list(q=q, fields="files(id, name)", pageSize=1).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    body: dict = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    return service.files().create(body=body, fields="id").execute()["id"]


def _ensure_path(service, path_parts: list[str]) -> str:
    parent = None
    for part in path_parts:
        parent = _find_or_create_folder(service, part, parent)
    return parent  # type: ignore[return-value]


def _path_to_drive(path: str) -> tuple[list[str], str]:
    """Split storage path into (folder_parts, filename), prefixing with CRA-ERP root."""
    parts = [p for p in path.split("/") if p]
    if parts and parts[0] == APP_NAME:
        parts = parts[1:]
    if not parts:
        return [DRIVE_ROOT], "file.bin"
    filename = parts[-1]
    folder_parts = [DRIVE_ROOT, *parts[:-1]]
    return folder_parts, filename


def _virtual_path_parts(virtual_path: str) -> list[str]:
    """Splits a user-facing storage path like '/Sistemas/Financeiro' into folder parts under CRA-ERP."""
    parts = [p for p in virtual_path.split("/") if p]
    if parts and parts[0] == APP_NAME:
        parts = parts[1:]
    return [DRIVE_ROOT, *parts]


def _find_folder_id(service, path_parts: list[str]) -> Optional[str]:
    """Returns the folder id of the given path or None if it doesn't exist."""
    parent = None
    for name in path_parts:
        safe = name.replace("'", "\\'")
        q = (
            f"name = '{safe}' and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        if parent:
            q += f" and '{parent}' in parents"
        res = service.files().list(q=q, fields="files(id)", pageSize=1).execute()
        files = res.get("files", [])
        if not files:
            return None
        parent = files[0]["id"]
    return parent


def _drive_upload(path: str, data: bytes, content_type: str, *, drive_path: Optional[str] = None) -> Optional[dict]:
    """Uploads to Drive and indexes the mapping.

    Args:
        path: canonical storage index key (matches what get_object will look up).
        drive_path: optional alternative hierarchy under CRA-ERP (defaults to `path`).
            Useful for migration where the index key is an opaque ``storage/<uuid>``
            but the Drive folders should reflect the human virtual path.
    """
    service = _drive_service()
    if not service:
        return None
    try:
        folder_parts, filename = _path_to_drive(drive_path or path)
        folder_id = _ensure_path(service, folder_parts)
        media = MediaIoBaseUpload(
            io.BytesIO(data),
            mimetype=content_type or "application/octet-stream",
            resumable=False,
        )
        meta = {"name": filename, "parents": [folder_id]}
        file = (
            service.files()
            .create(
                body=meta,
                media_body=media,
                fields="id, name, webViewLink, size, mimeType",
            )
            .execute()
        )
        _sync_db().storage_index.update_one(
            {"path": path},
            {
                "$set": {
                    "path": path,
                    "backend": "drive",
                    "drive_file_id": file["id"],
                    "filename": file.get("name"),
                    "mime_type": file.get("mimeType") or content_type,
                    "size": int(file.get("size") or len(data)),
                    "web_view_link": file.get("webViewLink"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
            upsert=True,
        )
        return file
    except Exception as e:  # noqa: BLE001
        logger.exception("Drive upload failed for path=%s: %s", path, e)
        return None


def _drive_download(path: str) -> Optional[tuple[bytes, str]]:
    idx = _sync_db().storage_index.find_one({"path": path, "backend": "drive"})
    if not idx:
        return None
    service = _drive_service()
    if not service:
        return None
    try:
        request = service.files().get_media(fileId=idx["drive_file_id"])
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _status, done = downloader.next_chunk()
        buf.seek(0)
        return buf.read(), idx.get("mime_type") or "application/octet-stream"
    except Exception as e:  # noqa: BLE001
        logger.exception("Drive download failed for path=%s: %s", path, e)
        return None


# ---------------- Public API ----------------

def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload bytes. Tries Drive first; falls back to Object Storage on failure."""
    # Try Drive only when connected
    if _drive_credentials_doc():
        meta = _drive_upload(path, data, content_type)
        if meta:
            return {
                "path": path,
                "size": int(meta.get("size") or len(data)),
                "etag": meta["id"],
                "backend": "drive",
                "web_view_link": meta.get("webViewLink"),
            }
        logger.warning("Drive upload failed for %s — falling back to Object Storage", path)

    info = _put_object_emergent(path, data, content_type)
    try:
        _sync_db().storage_index.update_one(
            {"path": path},
            {
                "$set": {
                    "path": path,
                    "backend": "object_storage",
                    "size": int(info.get("size") or len(data)),
                    "mime_type": content_type,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
            upsert=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not index object_storage path %s: %s", path, e)
    info["backend"] = "object_storage"
    return info


def get_object(path: str) -> tuple[bytes, str]:
    """Baixa um objeto. Tenta Drive primeiro (via índice), depois Object Storage."""
    if _drive_credentials_doc():
        result = _drive_download(path)
        if result is not None:
            return result
    return _get_object_emergent(path)


MIME_BY_EXT = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "heic": "image/heic",
    "heif": "image/heif",
}


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    name = _SAFE_NAME_RE.sub("_", name).strip("._-")
    return name or "file.bin"


# ---------------- Drive -> System sync ----------------

def _walk_drive(service, folder_id: str, parent_path: str = "/") -> list[dict]:
    """Lista recursivamente arquivos+pastas a partir de ``folder_id``.

    Retorna: lista de dicts {path, name, parent_path, type, mime_type, size, drive_file_id}.
    """
    items: list[dict] = []
    page_token = None
    while True:
        res = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                pageSize=1000,
                pageToken=page_token,
                orderBy="folder,name",
            )
            .execute()
        )
        for f in res.get("files", []):
            name = f["name"]
            full_path = (parent_path.rstrip("/") + "/" + name) if parent_path != "/" else ("/" + name)
            is_folder = f["mimeType"] == "application/vnd.google-apps.folder"
            items.append(
                {
                    "path": full_path,
                    "name": name,
                    "parent_path": parent_path,
                    "type": "folder" if is_folder else "file",
                    "mime_type": f["mimeType"],
                    "size": int(f.get("size") or 0),
                    "modified_time": f.get("modifiedTime"),
                    "drive_file_id": f["id"],
                }
            )
            if is_folder:
                items.extend(_walk_drive(service, f["id"], full_path))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return items


def sync_from_drive() -> dict:
    """Sincroniza o sistema com o estado atual do Drive (CRA-ERP/).

    Para cada arquivo/pasta encontrado no Drive que ainda NÃO existe em ``storage_files``,
    cria a entrada correspondente. Para arquivos, também grava no ``storage_index`` apontando
    para o ``drive_file_id`` para que ``get_object`` consiga baixá-los.

    Retorna: {folders_added, files_added, total_scanned, skipped}.
    """
    if not _drive_credentials_doc():
        return {"error": "Drive não conectado", "folders_added": 0, "files_added": 0, "total_scanned": 0, "skipped": 0}
    service = _drive_service()
    if not service:
        return {"error": "Drive indisponível", "folders_added": 0, "files_added": 0, "total_scanned": 0, "skipped": 0}

    root_id = _find_folder_id(service, [DRIVE_ROOT])
    if not root_id:
        return {"folders_added": 0, "files_added": 0, "total_scanned": 0, "skipped": 0}

    db = _sync_db()
    items = _walk_drive(service, root_id, "/")
    folders_added = files_added = skipped = 0

    # 1. Pastas primeiro (para garantir parent_path correto)
    for item in [i for i in items if i["type"] == "folder"]:
        existing = db.storage_files.find_one({"path": item["path"]})
        if existing:
            skipped += 1
            continue
        from uuid import uuid4

        doc = {
            "id": str(uuid4()),
            "path": item["path"],
            "parent_path": item["parent_path"],
            "name": item["name"],
            "type": "folder",
            "modified_at": item["modified_time"] or datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "drive_file_id": item["drive_file_id"],
            "synced_from_drive": True,
        }
        db.storage_files.insert_one(doc)
        folders_added += 1

    # 2. Arquivos
    for item in [i for i in items if i["type"] == "file"]:
        existing = db.storage_files.find_one({"path": item["path"]})
        if existing:
            skipped += 1
            continue
        from uuid import uuid4

        # Use drive_file_id-derived object_key so put/get can find it
        object_key = f"drive/{item['drive_file_id']}"
        doc = {
            "id": str(uuid4()),
            "path": item["path"],
            "parent_path": item["parent_path"],
            "name": item["name"],
            "type": "file",
            "size": item["size"],
            "content_type": item["mime_type"],
            "object_key": object_key,
            "modified_at": item["modified_time"] or datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "drive_file_id": item["drive_file_id"],
            "backend": "drive",
            "synced_from_drive": True,
        }
        db.storage_files.insert_one(doc)
        # Index for downloads
        db.storage_index.update_one(
            {"path": object_key},
            {
                "$set": {
                    "path": object_key,
                    "backend": "drive",
                    "drive_file_id": item["drive_file_id"],
                    "filename": item["name"],
                    "mime_type": item["mime_type"],
                    "size": item["size"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
            upsert=True,
        )
        files_added += 1

    return {
        "folders_added": folders_added,
        "files_added": files_added,
        "total_scanned": len(items),
        "skipped": skipped,
    }


# ---------------- Public folder operations on Drive ----------------

def drive_create_folder(virtual_path: str) -> Optional[str]:
    """Cria a hierarquia de pastas no Drive se ela ainda não existir.
    Retorna o folder_id da pasta criada (ou None se Drive não conectado/falhou).
    """
    if not _drive_credentials_doc():
        return None
    service = _drive_service()
    if not service:
        return None
    try:
        parts = _virtual_path_parts(virtual_path)
        return _ensure_path(service, parts)
    except Exception as e:  # noqa: BLE001
        logger.exception("drive_create_folder falhou para %s: %s", virtual_path, e)
        return None


def drive_delete_folder(virtual_path: str) -> bool:
    """Apaga (envia para a lixeira do Drive) uma pasta inteira pelo seu path virtual.
    Retorna True se foi apagada (ou já não existia). False em falha real.
    """
    if not _drive_credentials_doc():
        return True  # Drive não conectado: ok, nada a fazer
    service = _drive_service()
    if not service:
        return True
    try:
        parts = _virtual_path_parts(virtual_path)
        if len(parts) <= 1:
            # Não deixa apagar a raiz CRA-ERP
            logger.warning("drive_delete_folder: bloqueado tentativa de apagar raiz %s", virtual_path)
            return False
        folder_id = _find_folder_id(service, parts)
        if not folder_id:
            return True  # já não existe
        service.files().delete(fileId=folder_id).execute()
        # Limpa entries do storage_index sob esse path
        prefix = virtual_path.rstrip("/") + "/"
        _sync_db().storage_index.delete_many({"path": {"$regex": f"^{re.escape(prefix)}"}})
        return True
    except Exception as e:  # noqa: BLE001
        logger.exception("drive_delete_folder falhou para %s: %s", virtual_path, e)
        return False


def drive_delete_file(path_or_object_key: str) -> bool:
    """Apaga um arquivo do Drive usando o ``storage_index`` para localizar o ``drive_file_id``.
    Aceita o object_key (forma usada por put_object) OU um virtual path.
    """
    if not _drive_credentials_doc():
        return True
    service = _drive_service()
    if not service:
        return True
    db = _sync_db()
    idx = db.storage_index.find_one(
        {"path": path_or_object_key, "backend": "drive"}
    )
    if not idx:
        return True  # não está no Drive (talvez Object Storage), ok
    try:
        service.files().delete(fileId=idx["drive_file_id"]).execute()
        db.storage_index.delete_one({"_id": idx["_id"]})
        return True
    except Exception as e:  # noqa: BLE001
        logger.exception("drive_delete_file falhou para %s: %s", path_or_object_key, e)
        return False


def drive_rename(virtual_path: str, new_name: str) -> bool:
    """Renomeia uma pasta ou arquivo no Drive."""
    if not _drive_credentials_doc():
        return True
    service = _drive_service()
    if not service:
        return True
    try:
        parts = _virtual_path_parts(virtual_path)
        # Tenta como pasta primeiro
        node_id = _find_folder_id(service, parts)
        if not node_id and parts:
            # Tenta como arquivo: localiza dentro do parent
            parent_id = _find_folder_id(service, parts[:-1])
            if not parent_id:
                return True
            safe = parts[-1].replace("'", "\\'")
            res = (
                service.files()
                .list(q=f"name = '{safe}' and '{parent_id}' in parents and trashed = false",
                      fields="files(id)", pageSize=1)
                .execute()
            )
            files = res.get("files", [])
            if not files:
                return True
            node_id = files[0]["id"]
        service.files().update(fileId=node_id, body={"name": new_name}).execute()
        return True
    except Exception as e:  # noqa: BLE001
        logger.exception("drive_rename falhou para %s -> %s: %s", virtual_path, new_name, e)
        return False
