from datetime import datetime, timezone
from utils.database import db
import uuid

async def create_audit_log(
    user: dict,
    action: str,
    entity_type: str,
    entity_id: str,
    entity_name: str = "",
    details: str = "",
    module: str = "Sistema"
):
    """Cria um registro de auditoria no banco de dados"""
    log_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.get("id"),
        "user_name": user.get("name"),
        "user_role": user.get("role", "gerenciamento"),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "details": details,
        "module": module,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(log_doc)
    return log_doc
