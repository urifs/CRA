from datetime import datetime, timezone
from typing import Optional
from utils.database import db
import uuid

async def create_audit_log(
    user: dict,
    action: str,
    entity_type: str,
    entity_id: str,
    entity_name: str = "",
    details: str = "",
    module: str = "Sistema",
    snapshot: Optional[dict] = None,
    reversible: bool = False,
):
    """Cria um registro de auditoria no banco de dados.

    Args:
        snapshot: Estado anterior do documento (antes da ação). Necessário para
            permitir rollback de updates/deletes.
        reversible: Quando True, marca o log como reversível (apto a Desfazer).
    """
    log_id = str(uuid.uuid4())

    # Regra de reversibilidade (mesma do server.py):
    # - Exportações nunca são reversíveis.
    # - Em módulo Administrativo: create/update/delete são reversíveis
    #   (create: rollback exclui; update/delete: restaura snapshot).
    action_lower = (action or "").lower()
    is_create = action_lower in ("criar", "create")
    is_update = action_lower in ("editar", "update")
    is_delete = action_lower in ("excluir", "delete")
    is_export = "export" in action_lower or "exportar" in action_lower
    if is_export:
        reversible_final = False
    elif reversible:
        if is_create:
            reversible_final = True
        elif (is_update or is_delete) and snapshot is not None:
            reversible_final = True
        else:
            reversible_final = False
    else:
        if module == "Administrativo":
            if is_create:
                reversible_final = True
            elif (is_update or is_delete) and snapshot is not None:
                reversible_final = True
            else:
                reversible_final = False
        else:
            reversible_final = False

    log_doc = {
        "id": log_id,
        "user_id": user.get("id"),
        "user_name": user.get("name"),
        "user_email": user.get("email", ""),
        "user_role": user.get("role", "gerenciamento"),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "details": details,
        "module": module,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reversible": reversible_final,
        "rolled_back": False,
    }
    if snapshot is not None:
        def _norm(v):
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, dict):
                return {k: _norm(vv) for k, vv in v.items()}
            if isinstance(v, list):
                return [_norm(vv) for vv in v]
            return v
        log_doc["snapshot"] = _norm({k: v for k, v in snapshot.items() if k != "_id"})
    await db.audit_logs.insert_one(log_doc)
    return log_doc

