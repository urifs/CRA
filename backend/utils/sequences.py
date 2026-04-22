"""Shared sequence helper for auto-incrementing collection numbers."""
from utils.database import db


async def get_next_sequence(collection_name: str) -> int:
    """Retorna o próximo número sequencial para uma coleção (ex: contas_pagar)."""
    result = await db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return result["seq"]
