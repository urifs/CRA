"""Helper to build a COMPLETE MongoDB export (dump+schema+indexes+manifest+sql)
as an in-memory ZIP file. Used by the admin-panel endpoint
`/api/admin-panel/database-export` to allow downloading the full DB
from the running deployment (production) for migration to Supabase.

Coverage:
  - TODAS as collections (exceto `system.*`), TODOS os documentos, TODOS
    os campos — incluindo `_id` envelopado.
  - Tipos BSON especiais: ObjectId (`$oid`), datetime (`$date`), Decimal128
    (`$numberDecimal`), Binary (`$binary` base64), Timestamp, Regex, Code,
    MinKey/MaxKey, UUID.
  - Índices de cada collection (`indexes.json`).
  - Schema inferido, MANIFEST e DDL SQL (geração delegada ao script legado).
"""

from __future__ import annotations

import base64
import importlib.util
import io
import json
import sys
import tempfile
import uuid as uuid_mod
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from bson.binary import Binary
from bson.code import Code
from bson.decimal128 import Decimal128
from bson.max_key import MaxKey
from bson.min_key import MinKey
from bson.regex import Regex
from bson.timestamp import Timestamp

_SCRIPT_PATH = Path("/app/database_export/export_mongodb.py")


def _load_helpers():
    """Importa o script legado para reaproveitar `_infer_schema`,
    `_write_manifest` e `_write_sql_skeleton`."""
    spec = importlib.util.spec_from_file_location("export_mongodb", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["export_mongodb"] = mod
    spec.loader.exec_module(mod)
    return mod


def _serialize_full(value):
    """Converte qualquer valor BSON/Mongo em JSON puro, preservando tipos."""
    if value is None:
        return None
    if isinstance(value, bool):  # bool antes de int (bool é subclasse)
        return value
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, ObjectId):
        return {"$oid": str(value)}
    if isinstance(value, datetime):
        return {"$date": value.isoformat()}
    if isinstance(value, Decimal128):
        return {"$numberDecimal": str(value.to_decimal())}
    if isinstance(value, Binary):
        # UUID v3/v4 BSON Binary tem subtype 3/4
        return {
            "$binary": base64.b64encode(bytes(value)).decode("ascii"),
            "$type": format(value.subtype, "02x"),
        }
    if isinstance(value, bytes):
        return {"$binary": base64.b64encode(value).decode("ascii"), "$type": "00"}
    if isinstance(value, Timestamp):
        return {"$timestamp": {"t": value.time, "i": value.inc}}
    if isinstance(value, Regex):
        return {"$regex": value.pattern, "$options": value.flags}
    if isinstance(value, Code):
        out = {"$code": str(value)}
        if value.scope:
            out["$scope"] = {k: _serialize_full(v) for k, v in value.scope.items()}
        return out
    if isinstance(value, MinKey):
        return {"$minKey": 1}
    if isinstance(value, MaxKey):
        return {"$maxKey": 1}
    if isinstance(value, uuid_mod.UUID):
        return {"$uuid": str(value)}
    if isinstance(value, dict):
        return {k: _serialize_full(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_full(v) for v in value]
    # fallback — mantém como string mas registra o tipo
    return {"$unsupported": type(value).__name__, "value": str(value)}


def _serialize_index_info(ix_info: dict) -> dict:
    """Serializa o retorno de `db.coll.index_information()` para JSON."""
    out = {}
    for ix_name, ix_spec in ix_info.items():
        clean = {}
        for k, v in ix_spec.items():
            if k == "key":
                # key é lista de tuplas [(campo, ordem), ...]
                clean[k] = [list(item) if isinstance(item, tuple) else item for item in v]
            else:
                clean[k] = _serialize_full(v)
        out[ix_name] = clean
    return out


async def build_export_zip(db, db_name: str) -> tuple[bytes, dict]:
    """Gera um export COMPLETO do banco e retorna (zip_bytes, meta).

    O ZIP contém:
      - dump.json                  → todos os docs (com `_id` + todos os campos)
      - schema.json                → schema inferido
      - indexes.json               → índices por collection
      - verification.json          → contagem por collection + checksums
      - migrate_to_supabase.sql    → DDL Postgres
      - MANIFEST.md                → instruções legíveis
    """
    helpers = _load_helpers()

    all_collections = sorted(await db.list_collection_names())
    # `system.*` são metadados internos do MongoDB (perfis, índices), não
    # têm equivalente em Supabase — pulamos mas registramos.
    skipped: list[str] = []
    collection_names: list[str] = []
    for c in all_collections:
        if c.startswith("system."):
            skipped.append(c)
        else:
            collection_names.append(c)

    dump = {
        "_meta": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "database": db_name,
            "source": "MongoDB",
            "format_version": "2.0",
            "collection_count": len(collection_names),
            "skipped_system_collections": skipped,
            "includes_id_field": True,
            "includes_indexes": True,
        },
        "collections": {},
    }
    schema = {"_meta": dict(dump["_meta"]), "collections": {}}
    indexes: dict = {"_meta": dict(dump["_meta"]), "collections": {}}
    verification: dict = {
        "_meta": dict(dump["_meta"]),
        "per_collection": {},
        "totals": {},
    }

    grand_total = 0
    for name in collection_names:
        # IMPORTANTE: SEM projection — incluímos `_id` e absolutamente todos
        # os campos, sem exceção. Isso garante "TUDO sem falta".
        docs_raw = await db[name].find({}).to_list(None)
        docs_serialized = [_serialize_full(d) for d in docs_raw]
        dump["collections"][name] = docs_serialized

        # Para inferir schema usamos documentos COM `_id` removido (ele inflaciona
        # o schema sem trazer valor analítico) — mas o dump.json TEM o _id.
        docs_for_schema = [{k: v for k, v in d.items() if k != "_id"} for d in docs_raw]
        schema["collections"][name] = {
            "document_count": len(docs_raw),
            **helpers._infer_schema(docs_for_schema),
        }

        # Índices
        try:
            ix_info = await db[name].index_information()
            indexes["collections"][name] = _serialize_index_info(ix_info)
        except Exception as e:
            indexes["collections"][name] = {"_error": str(e)}

        # Verificação: contagem + sample IDs
        sample_ids = []
        for d in docs_raw[:3]:
            sample_ids.append({
                "id": d.get("id"),
                "_id": str(d.get("_id")) if d.get("_id") is not None else None,
            })
        verification["per_collection"][name] = {
            "document_count": len(docs_raw),
            "field_count_avg": round(
                sum(len(d) for d in docs_raw) / max(len(docs_raw), 1), 1
            ),
            "sample_ids": sample_ids,
            "has_id_field": all("id" in d for d in docs_raw) if docs_raw else None,
        }

        grand_total += len(docs_raw)

    dump["_meta"]["total_documents"] = grand_total
    schema["_meta"]["total_documents"] = grand_total
    verification["totals"] = {
        "collection_count": len(collection_names),
        "total_documents": grand_total,
    }

    # MANIFEST + SQL são funções do script legado (escrevem em path fixo).
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
        zf.writestr("dump.json", json.dumps(dump, ensure_ascii=False, indent=2, default=str))
        zf.writestr("schema.json", json.dumps(schema, ensure_ascii=False, indent=2, default=str))
        zf.writestr("indexes.json", json.dumps(indexes, ensure_ascii=False, indent=2, default=str))
        zf.writestr("verification.json", json.dumps(verification, ensure_ascii=False, indent=2, default=str))
        zf.writestr("MANIFEST.md", manifest_text)
        zf.writestr("migrate_to_supabase.sql", sql_text)

    meta = {
        "exported_at": dump["_meta"]["exported_at"],
        "database": db_name,
        "collection_count": len(collection_names),
        "total_documents": grand_total,
        "zip_size_bytes": buf.tell(),
        "skipped_system_collections": skipped,
        "files": ["dump.json", "schema.json", "indexes.json",
                  "verification.json", "MANIFEST.md", "migrate_to_supabase.sql"],
    }
    return buf.getvalue(), meta
