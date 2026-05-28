"""One-shot: sobe todo o conteúdo de /tmp/storage_backup/extracted para o Google Drive,
preservando hierarquia de pastas.

Cada arquivo vira:
    CRA-ERP/<caminho-relativo>

Idempotente: pula arquivos que já existem em ``storage_index`` com backend=drive.
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

from utils.storage import (  # noqa: E402
    MIME_BY_EXT,
    _drive_credentials_doc,
    _drive_upload,
    _sync_db,
)

BASE = Path("/tmp/storage_backup/extracted")


def _mime_from_name(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return MIME_BY_EXT.get(ext, "application/octet-stream")


def main() -> int:
    if not _drive_credentials_doc():
        print("Drive não está conectado.")
        return 2
    if not BASE.exists():
        print(f"Pasta {BASE} não existe.")
        return 1

    db = _sync_db()
    total = migrated = failed = skipped = 0
    for f in BASE.rglob("*"):
        if not f.is_file():
            continue
        total += 1
        rel = f.relative_to(BASE).as_posix()
        # use backup/<rel> as the canonical storage_index key
        key = f"backup-import/{rel}"

        existing = db.storage_index.find_one({"path": key, "backend": "drive"})
        if existing:
            print(f"[skip] {rel}")
            skipped += 1
            continue

        try:
            data = f.read_bytes()
            ct = _mime_from_name(f.name)
            # drive_path uses the raw relative path (no backup-import prefix)
            meta = _drive_upload(key, data, ct, drive_path=rel)
            if meta:
                print(f"[ok]   {rel} -> {meta['id']}")
                migrated += 1
            else:
                print(f"[fail] {rel}")
                failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"[err]  {rel}: {e}")
            failed += 1

    print(f"\nResumo: total={total} migrados={migrated} já-existentes={skipped} falhas={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
