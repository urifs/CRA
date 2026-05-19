"""Helper to build a complete MongoDB export (dump+schema+manifest+sql)
as an in-memory ZIP file. Used by the admin-panel endpoint
`/api/admin-panel/database-export` to allow downloading the full DB
from the running deployment (production) for migration to Supabase.

The logic is shared with /app/database_export/export_mongodb.py — we
load that module dynamically so there's a single source of truth.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_PATH = Path("/app/database_export/export_mongodb.py")


def _load_helpers():
    """Import the standalone export script as a module so we can reuse
    `_serialize`, `_infer_schema`, `_write_manifest`, `_write_sql_skeleton`."""
    spec = importlib.util.spec_from_file_location("export_mongodb", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["export_mongodb"] = mod
    spec.loader.exec_module(mod)
    return mod


async def build_export_zip(db, db_name: str) -> tuple[bytes, dict]:
    """Generates a full export of the given MongoDB database and returns
    `(zip_bytes, meta)` ready to stream to the client.

    The ZIP contains the four canonical artifacts:
      - dump.json
      - schema.json
      - migrate_to_supabase.sql
      - MANIFEST.md
    """
    helpers = _load_helpers()

    collection_names = sorted(await db.list_collection_names())

    dump = {
        "_meta": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "database": db_name,
            "source": "MongoDB",
            "format_version": "1.0",
            "collection_count": len(collection_names),
        },
        "collections": {},
    }
    schema = {"_meta": dict(dump["_meta"]), "collections": {}}

    grand_total = 0
    for name in collection_names:
        docs = await db[name].find({}, {"_id": 0}).to_list(None)
        dump["collections"][name] = [helpers._serialize(d) for d in docs]
        schema["collections"][name] = {
            "document_count": len(docs),
            **helpers._infer_schema(docs),
        }
        grand_total += len(docs)

    dump["_meta"]["total_documents"] = grand_total
    schema["_meta"]["total_documents"] = grand_total

    # MANIFEST e SQL são funções do script que escrevem em path fixo;
    # redirecionamos a constante de output para um tempdir e lemos de volta.
    tmpdir = Path(tempfile.mkdtemp(prefix="dbexport_"))
    original_manifest = helpers.OUT_MANIFEST
    original_sql = helpers.OUT_SQL
    helpers.OUT_MANIFEST = tmpdir / "MANIFEST.md"
    helpers.OUT_SQL = tmpdir / "migrate_to_supabase.sql"
    try:
        helpers._write_manifest(schema)
        helpers._write_sql_skeleton(schema)
        manifest_text = helpers.OUT_MANIFEST.read_text(encoding="utf-8")
        sql_text = helpers.OUT_SQL.read_text(encoding="utf-8")
    finally:
        helpers.OUT_MANIFEST = original_manifest
        helpers.OUT_SQL = original_sql

    # Empacota em ZIP em memória
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr(
            "dump.json",
            json.dumps(dump, ensure_ascii=False, indent=2, default=str),
        )
        zf.writestr(
            "schema.json",
            json.dumps(schema, ensure_ascii=False, indent=2, default=str),
        )
        zf.writestr("MANIFEST.md", manifest_text)
        zf.writestr("migrate_to_supabase.sql", sql_text)

    meta = {
        "exported_at": dump["_meta"]["exported_at"],
        "database": db_name,
        "collection_count": len(collection_names),
        "total_documents": grand_total,
        "zip_size_bytes": buf.tell(),
    }
    return buf.getvalue(), meta
