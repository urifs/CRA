"""
Script de auditoria de anexos.

Percorre TODOS os anexos no MongoDB e classifica cada um em:
  a) ✅ OK em Object Storage (acessível via storage_metadata.fetch_file_bytes)
  b) ⚠️  Em filesystem local (storage/ ou uploads/anexos/) - quebra no próximo deploy
  c) ❌ Referência órfã - registro existe mas binário sumiu (404 garantido)

Coleções inspecionadas:
  - entity_anexos        (anexos universais via AnexosManager)
  - attachments          (anexos legados de OS, manutenções, etc.)
  - chat_artifacts       (PDFs gerados pelo chat IA)
  - tasks (attachments)  (anexos da caixa de tarefas)

Uso:  python -m utils.audit_anexos
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Garante imports relativos
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import db  # noqa: E402

ROOT_DIR = Path(__file__).parent.parent
ANEXOS_DIR = ROOT_DIR / "uploads" / "anexos"
STORAGE_DIR = ROOT_DIR / "storage"


async def _check_object_storage(object_key: str) -> bool:
    """Tenta buscar um object_key no Object Storage."""
    try:
        from utils.storage import get_object  # type: ignore
        data, _ = get_object(object_key)
        return data is not None and len(data) > 0
    except Exception:
        return False


async def _check_storage_metadata_path(storage_path: str) -> tuple[str, str]:
    """
    Verifica se um storage_path está acessível via storage_metadata (Object Storage).
    Retorna ('ok'|'missing_in_mongo'|'no_object_key', detalhe).
    """
    if not storage_path:
        return "no_path", ""
    p = "/" + storage_path.lstrip("/")
    node = await db.storage_files.find_one({"path": p}, {"_id": 0})
    if not node:
        return "missing_in_mongo", p
    object_key = node.get("object_key")
    if not object_key:
        return "no_object_key", p
    ok = await _check_object_storage(object_key)
    return ("ok" if ok else "object_missing"), object_key


async def audit_entity_anexos() -> dict:
    """Audita a collection `entity_anexos`."""
    results = {"total": 0, "ok_os": 0, "fs_local": 0, "fs_missing": 0, "details": []}
    cursor = db.entity_anexos.find({}, {"_id": 0})
    async for a in cursor:
        results["total"] += 1
        source = a.get("source")
        if source == "local":
            # Anexo enviado pelo upload direto - mora em uploads/anexos/<filename>
            fp = ANEXOS_DIR / (a.get("filename") or "")
            if fp.exists():
                results["fs_local"] += 1
                results["details"].append(
                    {"id": a.get("id"), "type": "local", "status": "fs_local", "path": str(fp)}
                )
            else:
                results["fs_missing"] += 1
                results["details"].append(
                    {"id": a.get("id"), "type": "local", "status": "missing", "path": str(fp)}
                )
        elif source == "storage":
            sp = a.get("storage_path") or ""
            status, info = await _check_storage_metadata_path(sp)
            if status == "ok":
                results["ok_os"] += 1
            elif status in ("missing_in_mongo", "no_object_key"):
                # Sem registro novo no Mongo: olhar FS legado
                fp = STORAGE_DIR / sp.lstrip("/")
                if fp.exists():
                    results["fs_local"] += 1
                    results["details"].append(
                        {"id": a.get("id"), "type": "storage", "status": "fs_local_legacy", "path": str(fp)}
                    )
                else:
                    results["fs_missing"] += 1
                    results["details"].append(
                        {"id": a.get("id"), "type": "storage", "status": "missing", "storage_path": sp}
                    )
            elif status == "object_missing":
                results["fs_missing"] += 1
                results["details"].append(
                    {"id": a.get("id"), "type": "storage", "status": "object_missing", "object_key": info}
                )
        else:
            # source desconhecida
            results["fs_missing"] += 1
            results["details"].append(
                {"id": a.get("id"), "type": source, "status": "unknown_source"}
            )
    return results


async def audit_attachments() -> dict:
    """Audita a collection `attachments` (anexos legados de OS, manutenções, etc.).
    Schema real: { stored_filename, filename, entity_type, entity_id, ... }.
    Arquivo físico em ROOT_DIR/uploads/<stored_filename>.
    """
    UPLOAD_DIR = ROOT_DIR / "uploads"
    results = {"total": 0, "ok_os": 0, "fs_local": 0, "fs_missing": 0, "details": []}
    cursor = db.attachments.find({}, {"_id": 0})
    async for a in cursor:
        results["total"] += 1
        object_key = a.get("object_key")
        if object_key:
            ok = await _check_object_storage(object_key)
            if ok:
                results["ok_os"] += 1
            else:
                results["fs_missing"] += 1
                results["details"].append(
                    {"id": a.get("id"), "name": a.get("filename"), "status": "object_missing", "object_key": object_key}
                )
            continue

        stored = a.get("stored_filename") or a.get("file_path") or a.get("path")
        if not stored:
            results["fs_missing"] += 1
            results["details"].append(
                {"id": a.get("id"), "name": a.get("filename"), "status": "no_reference"}
            )
            continue

        # Tenta múltiplos diretórios conhecidos
        candidates = [
            UPLOAD_DIR / stored,
            ROOT_DIR / "uploads" / "anexos" / stored,
            ROOT_DIR / stored if not Path(stored).is_absolute() else Path(stored),
        ]
        found = next((c for c in candidates if c.exists()), None)
        if found:
            results["fs_local"] += 1
            results["details"].append(
                {"id": a.get("id"), "name": a.get("filename"), "status": "fs_local", "path": str(found)}
            )
        else:
            results["fs_missing"] += 1
            results["details"].append(
                {"id": a.get("id"), "name": a.get("filename"), "status": "missing", "stored_filename": stored}
            )
    return results


async def audit_chat_artifacts() -> dict:
    """Audita a collection `chat_artifacts` (PDFs gerados pelo chat IA).
    Schema real: { content_b64: '<base64>', filename, content_type }.
    Binário armazenado INLINE no Mongo via base64 → 100% persistente.
    """
    results = {"total": 0, "ok_os": 0, "fs_local": 0, "fs_missing": 0, "details": []}
    cursor = db.chat_artifacts.find({}, {"_id": 0})
    async for a in cursor:
        results["total"] += 1
        # Binário inline = persistência total (Mongo)
        if a.get("content_b64") or a.get("content") or a.get("data") or a.get("file_id"):
            results["ok_os"] += 1
        else:
            file_path = a.get("file_path") or a.get("path")
            if file_path:
                fp = Path(file_path)
                if not fp.is_absolute():
                    fp = ROOT_DIR / fp
                if fp.exists():
                    results["fs_local"] += 1
                else:
                    results["fs_missing"] += 1
                    results["details"].append({"id": a.get("id"), "name": a.get("filename"), "status": "missing", "path": str(fp)})
            else:
                results["fs_missing"] += 1
                results["details"].append({"id": a.get("id"), "name": a.get("filename"), "status": "no_reference"})
    return results


async def audit_task_attachments() -> dict:
    """Audita anexos embutidos em tasks (collection `tasks`, array `attachments`)."""
    results = {"total": 0, "ok_os": 0, "fs_local": 0, "fs_missing": 0, "details": []}
    cursor = db.tasks.find({"attachments": {"$exists": True, "$ne": []}}, {"_id": 0})
    async for t in cursor:
        for att in (t.get("attachments") or []):
            results["total"] += 1
            object_key = att.get("object_key")
            file_path = att.get("path") or att.get("file_path")
            if object_key:
                ok = await _check_object_storage(object_key)
                if ok:
                    results["ok_os"] += 1
                else:
                    results["fs_missing"] += 1
                    results["details"].append(
                        {"task_id": t.get("id"), "name": att.get("name"), "status": "object_missing"}
                    )
            elif file_path:
                fp = Path(file_path)
                if not fp.is_absolute():
                    fp = ROOT_DIR / fp
                if fp.exists():
                    results["fs_local"] += 1
                else:
                    results["fs_missing"] += 1
                    results["details"].append(
                        {"task_id": t.get("id"), "name": att.get("name"), "status": "missing"}
                    )
            else:
                # Pode ser inline (base64)
                if att.get("content") or att.get("data"):
                    results["ok_os"] += 1
                else:
                    results["fs_missing"] += 1
                    results["details"].append(
                        {"task_id": t.get("id"), "name": att.get("name"), "status": "no_reference"}
                    )
    return results


async def main():
    print("=" * 75)
    print("🔍 AUDITORIA DE ANEXOS - ERP CRA")
    print("=" * 75)

    sections = [
        ("entity_anexos (AnexosManager universal)", audit_entity_anexos),
        ("attachments (legado de OS / manutenções)", audit_attachments),
        ("chat_artifacts (PDFs do Chat IA)", audit_chat_artifacts),
        ("tasks.attachments (Caixa de Tarefas)", audit_task_attachments),
    ]

    grand = {"total": 0, "ok_os": 0, "fs_local": 0, "fs_missing": 0}
    section_results = []

    for title, fn in sections:
        print(f"\n📂 {title}")
        print("-" * 75)
        try:
            r = await fn()
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
            continue
        section_results.append((title, r))
        print(f"   Total registros           : {r['total']}")
        print(f"   ✅ OK em Object Storage   : {r['ok_os']}")
        print(f"   ⚠️  Em filesystem local   : {r['fs_local']}  (quebra no próximo deploy)")
        print(f"   ❌ Referências órfãs       : {r['fs_missing']}  (já estão quebradas)")
        for k in grand:
            grand[k] += r.get(k, 0)

    print("\n" + "=" * 75)
    print("📊 TOTAL GERAL")
    print("=" * 75)
    total = grand["total"]
    if total == 0:
        print("Nenhum anexo encontrado no banco.")
        return
    pct_ok = grand["ok_os"] * 100 / total
    pct_fs = grand["fs_local"] * 100 / total
    pct_mi = grand["fs_missing"] * 100 / total
    print(f"   Total de anexos          : {total}")
    print(f"   ✅ Persistentes (OS)     : {grand['ok_os']:>5}  ({pct_ok:5.1f}%)")
    print(f"   ⚠️  Filesystem local     : {grand['fs_local']:>5}  ({pct_fs:5.1f}%)")
    print(f"   ❌ Órfãos (binário sumiu): {grand['fs_missing']:>5}  ({pct_mi:5.1f}%)")
    print("=" * 75)

    # Detalhes apenas se houver pendências
    if grand["fs_local"] > 0 or grand["fs_missing"] > 0:
        print("\n📋 DETALHES DOS PENDENTES (até 30 primeiros por seção):")
        for title, r in section_results:
            problems = [d for d in r["details"] if d["status"] != "ok"][:30]
            if not problems:
                continue
            print(f"\n  • {title}")
            for d in problems:
                print(f"     - {d}")

    print("\n✅ Auditoria concluída.")


if __name__ == "__main__":
    asyncio.run(main())
