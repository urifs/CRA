"""
Storage Metadata Layer - MongoDB-backed metadata for the Storage module.

Cada arquivo/pasta tem um documento na coleção `storage_files`:
    {
        "id": "<uuid>",                   # PK
        "path": "/folder/subfolder/file.pdf",  # virtual path, único
        "parent_path": "/folder/subfolder",    # para listagens rápidas
        "name": "file.pdf",
        "type": "file" | "folder",
        "size": 1234,                     # apenas files
        "content_type": "application/pdf",# apenas files
        "object_key": "cra-erp/storage/<uuid>",  # chave no Object Storage; só files
        "modified_at": ISO datetime,
        "created_at": ISO datetime,
        "uploaded_by": "<user_id>"        # opcional
    }

Index único em `path`. Senha de pasta continua em `folder_passwords` (compatibilidade).
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from utils.database import db
from utils.storage import put_object, get_object, MIME_BY_EXT

logger = logging.getLogger(__name__)

OBJECT_PREFIX = "storage"  # vira cra-erp/storage/<uuid>


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_root_slash(path: str) -> str:
    p = (path or "/").strip()
    if not p.startswith("/"):
        p = "/" + p
    if len(p) > 1 and p.endswith("/"):
        p = p.rstrip("/")
    return p


def _split_path(path: str) -> tuple[str, str]:
    """Retorna (parent_path, name). Para '/foo/bar.pdf' → ('/foo', 'bar.pdf')."""
    p = _ensure_root_slash(path)
    if p == "/":
        return "/", ""
    parts = p.rstrip("/").split("/")
    name = parts[-1]
    parent = "/".join(parts[:-1]) or "/"
    return parent, name


async def ensure_indexes() -> None:
    try:
        await db.storage_files.create_index("path", unique=True)
        await db.storage_files.create_index("parent_path")
    except Exception as e:
        logger.warning(f"[storage_metadata] create_index falhou (provavelmente já existe): {e}")


async def get_node(path: str) -> Optional[dict]:
    p = _ensure_root_slash(path)
    return await db.storage_files.find_one({"path": p}, {"_id": 0})


async def list_children(parent_path: str) -> list[dict]:
    p = _ensure_root_slash(parent_path)
    cursor = db.storage_files.find({"parent_path": p}, {"_id": 0})
    items = await cursor.to_list(10000)
    items.sort(key=lambda x: (0 if x.get("type") == "folder" else 1, (x.get("name") or "").lower()))
    return items


async def create_folder(path: str, user_id: Optional[str] = None) -> dict:
    """Cria folder na MongoDB (idempotente). Cria também todos os ancestrais."""
    p = _ensure_root_slash(path)
    if p == "/":
        return {"path": "/", "type": "folder"}

    # Cria ancestrais
    parts = p.lstrip("/").split("/")
    current = ""
    last_doc = None
    for part in parts:
        current = current + "/" + part
        existing = await db.storage_files.find_one({"path": current})
        if existing:
            last_doc = existing
            continue
        parent, name = _split_path(current)
        doc = {
            "id": str(uuid.uuid4()),
            "path": current,
            "parent_path": parent,
            "name": name,
            "type": "folder",
            "modified_at": _now_iso(),
            "created_at": _now_iso(),
            "uploaded_by": user_id,
        }
        await db.storage_files.insert_one(doc)
        last_doc = doc

    last_doc = await db.storage_files.find_one({"path": p}, {"_id": 0})
    return last_doc


async def put_file(
    parent_path: str,
    filename: str,
    data: bytes,
    content_type: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Sobe bytes para Object Storage e grava metadados. Trata duplicatas com sufixo _1, _2…"""
    parent_path = _ensure_root_slash(parent_path)
    # Garante folders ancestrais
    if parent_path != "/":
        await create_folder(parent_path, user_id=user_id)

    # Dedup de nome
    base = filename
    name_only = base.rsplit(".", 1)[0] if "." in base else base
    ext = ("." + base.rsplit(".", 1)[1]) if "." in base else ""
    final_name = base
    counter = 1
    while await db.storage_files.find_one(
        {"path": (parent_path.rstrip("/") + "/" + final_name) if parent_path != "/" else ("/" + final_name)}
    ):
        final_name = f"{name_only}_{counter}{ext}"
        counter += 1

    full_path = (parent_path.rstrip("/") + "/" + final_name) if parent_path != "/" else ("/" + final_name)

    # Content-Type
    if not content_type:
        ext_lower = (final_name.rsplit(".", 1)[1].lower() if "." in final_name else "")
        content_type = MIME_BY_EXT.get(ext_lower, "application/octet-stream")

    # Upload para Object Storage
    object_key = f"{OBJECT_PREFIX}/{uuid.uuid4()}"
    put_object(object_key, data, content_type)

    # Persiste metadados
    doc = {
        "id": str(uuid.uuid4()),
        "path": full_path,
        "parent_path": parent_path,
        "name": final_name,
        "type": "file",
        "size": len(data),
        "content_type": content_type,
        "object_key": object_key,
        "modified_at": _now_iso(),
        "created_at": _now_iso(),
        "uploaded_by": user_id,
    }
    await db.storage_files.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def fetch_file_bytes(path: str) -> tuple[bytes, str, str]:
    """Retorna (bytes, content_type, name)."""
    p = _ensure_root_slash(path)
    node = await db.storage_files.find_one({"path": p}, {"_id": 0})
    if not node or node.get("type") != "file":
        return None, None, None
    object_key = node.get("object_key")
    if not object_key:
        return None, None, None
    data, ct = get_object(object_key)
    return data, node.get("content_type") or ct, node.get("name")


async def delete_node(path: str) -> int:
    """Deleta arquivo ou pasta (recursivo). Retorna nº de docs removidos."""
    p = _ensure_root_slash(path)
    node = await db.storage_files.find_one({"path": p})
    if not node:
        return 0
    if node.get("type") == "file":
        await db.storage_files.delete_one({"path": p})
        # TODO: object_storage delete (API não implementada no helper)
        return 1
    # folder: deleta tudo abaixo
    prefix = p.rstrip("/") + "/"
    res = await db.storage_files.delete_many({
        "$or": [
            {"path": p},
            {"path": {"$regex": f"^{prefix}"}},
        ]
    })
    return res.deleted_count


async def rename_node(old_path: str, new_name: str) -> dict:
    p = _ensure_root_slash(old_path)
    node = await db.storage_files.find_one({"path": p}, {"_id": 0})
    if not node:
        raise ValueError("Arquivo/pasta não encontrado")
    parent, _ = _split_path(p)
    new_path = (parent.rstrip("/") + "/" + new_name) if parent != "/" else ("/" + new_name)
    # Conflito de nome
    if await db.storage_files.find_one({"path": new_path}):
        raise ValueError("Já existe item com esse nome")
    # Atualiza o nó
    await db.storage_files.update_one(
        {"path": p},
        {"$set": {"path": new_path, "name": new_name, "modified_at": _now_iso()}},
    )
    # Se for folder, atualizar descendentes
    if node.get("type") == "folder":
        prefix_old = p.rstrip("/") + "/"
        prefix_new = new_path.rstrip("/") + "/"
        descendants = await db.storage_files.find({"path": {"$regex": f"^{prefix_old}"}}, {"_id": 0}).to_list(100000)
        for d in descendants:
            np = prefix_new + d["path"][len(prefix_old):]
            new_parent, _ = _split_path(np)
            await db.storage_files.update_one(
                {"path": d["path"]},
                {"$set": {"path": np, "parent_path": new_parent, "modified_at": _now_iso()}},
            )
    return await db.storage_files.find_one({"path": new_path}, {"_id": 0})


async def move_node(src_path: str, dest_parent_path: str) -> dict:
    src = _ensure_root_slash(src_path)
    dest_parent = _ensure_root_slash(dest_parent_path)
    node = await db.storage_files.find_one({"path": src}, {"_id": 0})
    if not node:
        raise ValueError("Arquivo/pasta de origem não encontrado")
    if dest_parent != "/":
        await create_folder(dest_parent)
    new_path = (dest_parent.rstrip("/") + "/" + node["name"]) if dest_parent != "/" else ("/" + node["name"])
    if await db.storage_files.find_one({"path": new_path}):
        raise ValueError("Já existe item com esse nome no destino")
    await db.storage_files.update_one(
        {"path": src},
        {"$set": {"path": new_path, "parent_path": dest_parent, "modified_at": _now_iso()}},
    )
    if node.get("type") == "folder":
        prefix_old = src.rstrip("/") + "/"
        prefix_new = new_path.rstrip("/") + "/"
        descendants = await db.storage_files.find({"path": {"$regex": f"^{prefix_old}"}}, {"_id": 0}).to_list(100000)
        for d in descendants:
            np = prefix_new + d["path"][len(prefix_old):]
            new_p, _ = _split_path(np)
            await db.storage_files.update_one(
                {"path": d["path"]},
                {"$set": {"path": np, "parent_path": new_p, "modified_at": _now_iso()}},
            )
    return await db.storage_files.find_one({"path": new_path}, {"_id": 0})


async def search(query: str) -> list[dict]:
    """Busca por nome (case-insensitive)."""
    q = (query or "").strip()
    if not q:
        return []
    rx = {"$regex": q, "$options": "i"}
    cursor = db.storage_files.find({"name": rx, "type": "file"}, {"_id": 0}).limit(500)
    return await cursor.to_list(500)


async def count_in_folder(folder_path: str) -> int:
    p = _ensure_root_slash(folder_path)
    if p == "/":
        return await db.storage_files.count_documents({"parent_path": "/"})
    prefix = p.rstrip("/") + "/"
    return await db.storage_files.count_documents({
        "$or": [{"parent_path": p}, {"path": {"$regex": f"^{prefix}"}}]
    })
