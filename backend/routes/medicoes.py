"""
Medições de Máquinas (Machine Measurements) — horímetro, km, combustível, produção.
Extraído de server.py na Sessão 32 Fase 2 Parte 2.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db

medicoes_router = APIRouter(prefix="/medicoes", tags=["Medições"])


# ============================================================================
# MODELS
# ============================================================================

class MedicaoCreate(BaseModel):
    obra_id: str
    maquina_id: str
    tipo: str  # 'horimetro', 'km', 'combustivel', 'producao', 'outro'
    valor_anterior: Optional[float] = 0
    valor_atual: float
    unidade: str
    data_medicao: str
    observacoes: Optional[str] = None


class MedicaoResponse(BaseModel):
    id: str
    obra_id: str
    obra_nome: Optional[str] = None
    maquina_id: str
    maquina_nome: Optional[str] = None
    maquina_placa: Optional[str] = None
    tipo: str
    valor_anterior: float
    valor_atual: float
    diferenca: float
    unidade: str
    data_medicao: str
    observacoes: Optional[str] = None
    registrado_por: Optional[str] = None
    created_at: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@medicoes_router.post("")
async def create_medicao(
    medicao: MedicaoCreate,
    current_user: dict = Depends(get_current_user),
):
    """Registrar nova medição de máquina"""
    obra = await db.obras.find_one({"id": medicao.obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    maquina = await db.machines.find_one({"id": medicao.maquina_id}, {"_id": 0})
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    diferenca = medicao.valor_atual - (medicao.valor_anterior or 0)

    medicao_doc = {
        "id": str(uuid.uuid4()),
        "obra_id": medicao.obra_id,
        "obra_nome": obra.get("name"),
        "maquina_id": medicao.maquina_id,
        "maquina_nome": maquina.get("name"),
        "maquina_placa": maquina.get("plate"),
        "tipo": medicao.tipo,
        "valor_anterior": medicao.valor_anterior or 0,
        "valor_atual": medicao.valor_atual,
        "diferenca": diferenca,
        "unidade": medicao.unidade,
        "data_medicao": medicao.data_medicao,
        "observacoes": medicao.observacoes,
        "registrado_por": current_user["name"],
        "registrado_por_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.medicoes.insert_one(medicao_doc)

    # Atualiza última medição na máquina
    await db.machines.update_one(
        {"id": medicao.maquina_id},
        {"$set": {
            f"ultima_medicao_{medicao.tipo}": medicao.valor_atual,
            f"ultima_medicao_{medicao.tipo}_data": medicao.data_medicao,
        }},
    )

    await create_audit_log(
        user=current_user,
        action="registrar medição",
        entity_type="medicao",
        entity_id=medicao_doc["id"],
        entity_name=f"{maquina.get('name')} - {medicao.tipo}",
        details=f"Valor: {medicao.valor_atual} {medicao.unidade} (diferença: {diferenca})",
        module="Gerenciamento",
    )
    return {"message": "Medição registrada com sucesso", "id": medicao_doc["id"]}


@medicoes_router.get("")
async def get_medicoes(
    obra_id: Optional[str] = None,
    maquina_id: Optional[str] = None,
    tipo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Listar medições com filtros"""
    query: dict = {}
    if obra_id:
        query["obra_id"] = obra_id
    if maquina_id:
        query["maquina_id"] = maquina_id
    if tipo:
        query["tipo"] = tipo
    if data_inicio:
        query["data_medicao"] = {"$gte": data_inicio}
    if data_fim:
        if "data_medicao" in query:
            query["data_medicao"]["$lte"] = data_fim
        else:
            query["data_medicao"] = {"$lte": data_fim}

    return await db.medicoes.find(query, {"_id": 0}).sort("data_medicao", -1).to_list(500)


@medicoes_router.get("/resumo/{obra_id}")
async def get_medicoes_resumo(
    obra_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Resumo de medições por obra (totais por máquina e tipo)"""
    obra = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    medicoes = await db.medicoes.find({"obra_id": obra_id}, {"_id": 0}).to_list(1000)

    maquinas_resumo: dict = {}
    for m in medicoes:
        maq_id = m["maquina_id"]
        if maq_id not in maquinas_resumo:
            maquinas_resumo[maq_id] = {
                "maquina_id": maq_id,
                "maquina_nome": m.get("maquina_nome", ""),
                "maquina_placa": m.get("maquina_placa", ""),
                "medicoes_por_tipo": {},
            }

        tipo = m["tipo"]
        if tipo not in maquinas_resumo[maq_id]["medicoes_por_tipo"]:
            maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo] = {
                "tipo": tipo,
                "unidade": m["unidade"],
                "total_diferenca": 0,
                "valor_inicial": m["valor_anterior"],
                "valor_final": m["valor_atual"],
                "qtd_medicoes": 0,
            }

        maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo]["total_diferenca"] += m["diferenca"]
        maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo]["valor_final"] = m["valor_atual"]
        maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo]["qtd_medicoes"] += 1

    return {
        "obra_id": obra_id,
        "obra_nome": obra.get("name"),
        "total_medicoes": len(medicoes),
        "maquinas": list(maquinas_resumo.values()),
    }


@medicoes_router.get("/{medicao_id}")
async def get_medicao(medicao_id: str, current_user: dict = Depends(get_current_user)):
    """Obter uma medição específica"""
    medicao = await db.medicoes.find_one({"id": medicao_id}, {"_id": 0})
    if not medicao:
        raise HTTPException(status_code=404, detail="Medição não encontrada")
    return medicao


@medicoes_router.put("/{medicao_id}")
async def update_medicao(
    medicao_id: str,
    medicao: MedicaoCreate,
    current_user: dict = Depends(get_current_user),
):
    """Atualizar medição"""
    existing = await db.medicoes.find_one({"id": medicao_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Medição não encontrada")

    diferenca = medicao.valor_atual - (medicao.valor_anterior or 0)

    await db.medicoes.update_one(
        {"id": medicao_id},
        {"$set": {
            "tipo": medicao.tipo,
            "valor_anterior": medicao.valor_anterior or 0,
            "valor_atual": medicao.valor_atual,
            "diferenca": diferenca,
            "unidade": medicao.unidade,
            "data_medicao": medicao.data_medicao,
            "observacoes": medicao.observacoes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    await create_audit_log(
        user=current_user,
        action="atualizar medição",
        entity_type="medicao",
        entity_id=medicao_id,
        entity_name=f"{existing.get('maquina_nome')} - {medicao.tipo}",
        module="Gerenciamento",
    )
    return {"message": "Medição atualizada com sucesso"}


@medicoes_router.delete("/{medicao_id}")
async def delete_medicao(medicao_id: str, current_user: dict = Depends(get_current_user)):
    """Excluir medição"""
    existing = await db.medicoes.find_one({"id": medicao_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Medição não encontrada")

    await db.medicoes.delete_one({"id": medicao_id})

    await create_audit_log(
        user=current_user,
        action="excluir medição",
        entity_type="medicao",
        entity_id=medicao_id,
        entity_name=f"{existing.get('maquina_nome')} - {existing.get('tipo')}",
        module="Gerenciamento",
    )
    return {"message": "Medição excluída com sucesso"}
