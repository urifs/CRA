"""Migra todos os arquivos legados (Emergent Object Storage + filesystem local) para o Google Drive.

Como executar:
    python -m utils.migrate_to_drive --dry-run    # só lista o que faria
    python -m utils.migrate_to_drive              # executa de verdade

O script:
  1. Lê a collection ``storage_files`` (arquivos do módulo Armazenamento) e migra cada
     ``object_key`` para o Drive, preservando o path virtual (ex.: ``/Pasta/file.pdf`` ->
     ``CRA-ERP/Pasta/file.pdf``).
  2. Lê a collection ``anexos`` (anexos vinculados a entidades como contas / OS / RH) e
     migra ``storage_path`` de cada anexo.
  3. Varre ``/app/uploads`` (anexos legados em filesystem) e sobe para
     ``CRA-ERP/uploads-legacy/...``.

Após o sucesso de cada arquivo, o ``storage_index`` é atualizado para
``backend=drive`` com o ``drive_file_id``. Em download via ``utils.storage.get_object``
o sistema automaticamente vai buscar no Drive.

Idempotente: rodando de novo, arquivos já com ``backend=drive`` no ``storage_index``
são pulados.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Carrega .env antes de importar utils.storage
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(ROOT))  # noqa: E402

from utils.storage import (  # noqa: E402
    _drive_credentials_doc,
    _drive_upload,
    _get_object_emergent,
    _sync_db,
    MIME_BY_EXT,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
log = logging.getLogger("migrate_to_drive")


def _mime_from_name(name: str, default: str = "application/octet-stream") -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return MIME_BY_EXT.get(ext, default)


def _already_in_drive(path: str) -> bool:
    db = _sync_db()
    return bool(db.storage_index.find_one({"path": path, "backend": "drive"}))


def migrate_storage_files(dry_run: bool) -> tuple[int, int, int]:
    """Migra a collection storage_files (módulo Armazenamento). Retorna (total, migrados, falhas)."""
    db = _sync_db()
    cursor = db.storage_files.find({"type": "file"})
    total = migrated = failed = 0

    for doc in cursor:
        total += 1
        object_key = doc.get("object_key")
        virtual_path = doc.get("path") or doc.get("name") or f"unknown/{doc.get('id')}"

        if not object_key:
            log.warning("[storage_files] sem object_key, pulando: %s", virtual_path)
            failed += 1
            continue

        if _already_in_drive(object_key):
            log.info("[storage_files] já no Drive: %s", virtual_path)
            continue

        if dry_run:
            log.info("[storage_files] DRY: %s  (%s bytes)", virtual_path, doc.get("size", "?"))
            migrated += 1
            continue

        try:
            data, content_type = _get_object_emergent(object_key)
            content_type = doc.get("content_type") or content_type or _mime_from_name(virtual_path)
            # Storage index key is the object_key (matches get_object lookup),
            # but Drive hierarchy reflects the human virtual path.
            meta = _drive_upload(object_key, data, content_type, drive_path=virtual_path)
            if not meta:
                log.error("[storage_files] falha upload Drive: %s", virtual_path)
                failed += 1
                continue
            # The index is updated by _drive_upload. We also update storage_files
            # with the drive_file_id so the page can show it without indirection.
            db.storage_files.update_one(
                {"_id": doc["_id"]},
                {"$set": {"drive_file_id": meta["id"], "backend": "drive"}},
            )
            log.info("[storage_files] OK: %s -> %s", virtual_path, meta["id"])
            migrated += 1
        except Exception as e:  # noqa: BLE001
            log.exception("[storage_files] erro %s: %s", virtual_path, e)
            failed += 1

    return total, migrated, failed


def migrate_anexos(dry_run: bool) -> tuple[int, int, int]:
    """Migra a collection ``anexos`` (anexos vinculados a entidades como contas, OS, RH).

    Cada documento tem ``storage_path`` apontando para um path no Object Storage
    (ex.: ``cra-erp/anexos/<uuid>.pdf``).
    """
    db = _sync_db()
    cursor = db.anexos.find({})
    total = migrated = failed = 0

    for doc in cursor:
        total += 1
        storage_path = (doc.get("storage_path") or "").lstrip("/")
        original_name = doc.get("original_name") or doc.get("filename") or "anexo.bin"

        if not storage_path:
            # Anexo legado em filesystem (filename only)
            failed += 1
            continue

        # Use storage_path as the canonical key in storage_index
        if _already_in_drive(storage_path):
            log.info("[anexos] já no Drive: %s", storage_path)
            continue

        if dry_run:
            log.info("[anexos] DRY: %s (%s)", storage_path, original_name)
            migrated += 1
            continue

        try:
            data, ct = _get_object_emergent(storage_path)
            content_type = doc.get("mime_type") or ct or _mime_from_name(original_name)
            meta = _drive_upload(storage_path, data, content_type)
            if not meta:
                log.error("[anexos] falha upload Drive: %s", storage_path)
                failed += 1
                continue
            db.anexos.update_one(
                {"_id": doc["_id"]},
                {"$set": {"drive_file_id": meta["id"], "backend": "drive"}},
            )
            log.info("[anexos] OK: %s -> %s", storage_path, meta["id"])
            migrated += 1
        except Exception as e:  # noqa: BLE001
            log.exception("[anexos] erro %s: %s", storage_path, e)
            failed += 1

    return total, migrated, failed


def migrate_filesystem(dry_run: bool) -> tuple[int, int, int]:
    """Varre /app/uploads e sobe para CRA-ERP/uploads-legacy/..."""
    base = Path("/app/uploads")
    if not base.exists():
        log.info("[fs] /app/uploads não existe — pulando")
        return 0, 0, 0
    total = migrated = failed = 0
    for f in base.rglob("*"):
        if not f.is_file():
            continue
        total += 1
        rel = f.relative_to(base)
        virtual_path = f"uploads-legacy/{rel.as_posix()}"

        if _already_in_drive(virtual_path):
            log.info("[fs] já no Drive: %s", virtual_path)
            continue

        if dry_run:
            log.info("[fs] DRY: %s (%d bytes)", virtual_path, f.stat().st_size)
            migrated += 1
            continue

        try:
            data = f.read_bytes()
            content_type = _mime_from_name(f.name)
            meta = _drive_upload(virtual_path, data, content_type)
            if not meta:
                failed += 1
                continue
            log.info("[fs] OK: %s -> %s", virtual_path, meta["id"])
            migrated += 1
        except Exception as e:  # noqa: BLE001
            log.exception("[fs] erro %s: %s", virtual_path, e)
            failed += 1
    return total, migrated, failed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="apenas lista, não migra")
    parser.add_argument("--skip-fs", action="store_true", help="não varrer /app/uploads")
    parser.add_argument("--skip-anexos", action="store_true")
    parser.add_argument("--skip-storage-files", action="store_true")
    args = parser.parse_args()

    if not _drive_credentials_doc():
        log.error("Google Drive não está conectado. Conecte primeiro em /painel-admin → Integrações.")
        return 2

    log.info("=== Migração iniciada (dry_run=%s) ===", args.dry_run)

    grand = {"total": 0, "migrated": 0, "failed": 0}

    if not args.skip_storage_files:
        t, m, f = migrate_storage_files(args.dry_run)
        log.info("storage_files: total=%d migrados=%d falhas=%d", t, m, f)
        grand["total"] += t
        grand["migrated"] += m
        grand["failed"] += f

    if not args.skip_anexos:
        t, m, f = migrate_anexos(args.dry_run)
        log.info("anexos: total=%d migrados=%d falhas=%d", t, m, f)
        grand["total"] += t
        grand["migrated"] += m
        grand["failed"] += f

    if not args.skip_fs:
        t, m, f = migrate_filesystem(args.dry_run)
        log.info("filesystem: total=%d migrados=%d falhas=%d", t, m, f)
        grand["total"] += t
        grand["migrated"] += m
        grand["failed"] += f

    log.info("=== Resumo: total=%(total)d migrados=%(migrated)d falhas=%(failed)d ===", grand)
    return 0 if grand["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
