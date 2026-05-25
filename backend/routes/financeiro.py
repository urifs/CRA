"""
Financeiro — Contas a Pagar e Contas a Receber.
Endpoints extraídos de server.py na Sessão 32 de refatoração (Fase 1 Parte 2).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db
from utils.sequences import get_next_sequence

financeiro_router = APIRouter(prefix="/admin", tags=["Financeiro"])


# ============================================================================
# MODELS — Contas a Pagar
# ============================================================================

class ContaPagarCreate(BaseModel):
    fornecedor_id: Optional[str] = None
    fornecedor_nome: Optional[str] = None
    documento: Optional[str] = None
    numero_doc: Optional[str] = None
    descricao: str
    valor: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_retencao: Optional[float] = 0  # Retenção (IRRF/INSS/ISS) — descontada do valor total
    total_parcelas: Optional[int] = 1
    numero_parcela: Optional[int] = 1
    parcela_origem_id: Optional[str] = None
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_pagamento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    subconta_id: Optional[str] = None
    subconta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None
    frota_nome: Optional[str] = None
    maquina_id: Optional[str] = None
    maquina_nome: Optional[str] = None
    forma_pagamento: str = "dinheiro"
    conta_movimento: Optional[str] = None
    conta_bancaria_id: Optional[str] = None
    conta_bancaria_nome: Optional[str] = None
    status: str = "em_aberto"
    observacoes: Optional[str] = None


class ContaParceladaCreate(BaseModel):
    fornecedor_id: Optional[str] = None
    fornecedor_nome: Optional[str] = None
    documento: Optional[str] = None
    numero_doc: Optional[str] = None
    descricao: str
    valor_total: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_retencao: Optional[float] = 0  # Retenção total (será dividida proporcionalmente)
    data_emissao: Optional[str] = None
    data_primeiro_vencimento: str
    total_parcelas: int
    intervalo_dias: int = 30
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    subconta_id: Optional[str] = None
    subconta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None
    frota_nome: Optional[str] = None
    maquina_id: Optional[str] = None
    maquina_nome: Optional[str] = None
    forma_pagamento: str = "boleto"
    conta_movimento: Optional[str] = None
    conta_bancaria_id: Optional[str] = None
    conta_bancaria_nome: Optional[str] = None
    observacoes: Optional[str] = None
    # Campos de linhagem/origem — preservados ao parcelar uma conta existente
    nfe_id: Optional[str] = None
    nfse_id: Optional[str] = None
    anexos: Optional[list] = None
    origem: Optional[str] = None
    folha_id: Optional[str] = None
    ordem_servico_id: Optional[str] = None
    contrato_id: Optional[str] = None


class QuitarContaRequest(BaseModel):
    data_pagamento: Optional[str] = None
    conta_bancaria_id: Optional[str] = None
    valor_pago: Optional[float] = None
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_desconto: Optional[float] = 0
    observacao: Optional[str] = None


# ============================================================================
# MODELS — Contas a Receber
# ============================================================================

class ContaReceberCreate(BaseModel):
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    documento: Optional[str] = None
    numero_doc: Optional[str] = None
    descricao: str
    valor: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_retencao: Optional[float] = 0  # Retenção (IRRF/INSS/ISS) — descontada do valor total
    total_parcelas: Optional[int] = 1
    numero_parcela: Optional[int] = 1
    parcela_origem_id: Optional[str] = None
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_recebimento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    subconta_id: Optional[str] = None
    subconta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None
    frota_nome: Optional[str] = None
    maquina_id: Optional[str] = None
    maquina_nome: Optional[str] = None
    forma_pagamento: str = "dinheiro"
    conta_movimento: Optional[str] = None
    conta_bancaria_id: Optional[str] = None
    conta_bancaria_nome: Optional[str] = None
    status: str = "em_aberto"
    faturamento: Optional[str] = None
    observacoes: Optional[str] = None


class ContaReceberParceladaCreate(BaseModel):
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    documento: Optional[str] = None
    numero_doc: Optional[str] = None
    descricao: str
    valor_total: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_retencao: Optional[float] = 0  # Retenção total (será dividida proporcionalmente)
    data_emissao: Optional[str] = None
    data_primeiro_vencimento: str
    total_parcelas: int
    intervalo_dias: int = 30
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    subconta_id: Optional[str] = None
    subconta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None
    frota_nome: Optional[str] = None
    maquina_id: Optional[str] = None
    maquina_nome: Optional[str] = None
    forma_pagamento: str = "boleto"
    conta_movimento: Optional[str] = None
    conta_bancaria_id: Optional[str] = None
    conta_bancaria_nome: Optional[str] = None
    faturamento: Optional[str] = None
    observacoes: Optional[str] = None
    # Campos de linhagem/origem
    nfe_id: Optional[str] = None
    nfse_id: Optional[str] = None
    anexos: Optional[list] = None
    origem: Optional[str] = None
    ordem_servico_id: Optional[str] = None
    contrato_id: Optional[str] = None


class QuitarContaReceberRequest(BaseModel):
    data_recebimento: Optional[str] = None
    data_pagamento: Optional[str] = None  # alias aceito pelo frontend
    conta_bancaria_id: Optional[str] = None
    valor_recebido: Optional[float] = None
    valor_pago: Optional[float] = None  # alias
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_desconto: Optional[float] = 0
    observacao: Optional[str] = None


# ============================================================================
# CONTAS A PAGAR
# ============================================================================

@financeiro_router.get("/contas-pagar")
async def get_contas_pagar(
    status: Optional[str] = None,
    vencimento: Optional[str] = None,
    forma_pagamento: Optional[str] = None,
    plano_conta_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    tipo_data: Optional[str] = "vencimento",
    valor: Optional[float] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    query: dict = {}
    # Status "a_pagar" é um filtro virtual que engloba TODAS as contas ainda
    # não quitadas (em_aberto, parcial e pendente). Isso garante que uma
    # conta com pagamento parcial continue aparecendo na visão "A Pagar"
    # até ser totalmente quitada.
    if status:
        if status == "a_pagar":
            query["status"] = {"$in": ["em_aberto", "parcial", "pendente"]}
        else:
            query["status"] = status
    if forma_pagamento:
        query["forma_pagamento"] = forma_pagamento
    if plano_conta_id:
        query["plano_conta_id"] = plano_conta_id
    if search:
        query["$or"] = [
            {"descricao": {"$regex": search, "$options": "i"}},
            {"fornecedor_nome": {"$regex": search, "$options": "i"}},
            {"documento": {"$regex": search, "$options": "i"}},
        ]
    if valor is not None:
        # Busca por valor exato em valor bruto OU valor_final
        epsilon = 0.005
        query["$or"] = (query.get("$or") or []) + [
            {"valor": {"$gte": valor - epsilon, "$lte": valor + epsilon}},
            {"valor_final": {"$gte": valor - epsilon, "$lte": valor + epsilon}},
        ]

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Para filtros de vencimento, consideramos pendentes (em_aberto), parciais
    # e pendentes legados como "ainda devidas".
    status_pendente = {"$in": ["em_aberto", "parcial", "pendente"]}
    if vencimento == "vencidas":
        query["data_vencimento"] = {"$lt": hoje}
        query["status"] = status_pendente
    elif vencimento == "hoje":
        query["data_vencimento"] = hoje
    elif vencimento == "a_vencer":
        query["data_vencimento"] = {"$gt": hoje}
        query["status"] = status_pendente

    if data_inicio and data_fim:
        campo_data = "data_pagamento" if tipo_data == "pagamento" else "data_vencimento"
        query[campo_data] = {"$gte": data_inicio, "$lte": data_fim}

    contas = await db.contas_pagar.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(1000)

    for conta in contas:
        v = conta.get("valor", 0)
        desconto = conta.get("valor_desconto", 0)
        juros = conta.get("valor_juros", 0)
        multa = conta.get("valor_multa", 0)
        conta["valor_final"] = v - desconto + juros + multa

    # Anexa resumo de saldo do grupo de parcelas (calculado a partir de TODAS as
    # parcelas do grupo, ignorando os filtros aplicados na listagem)
    origem_ids = {c.get("parcela_origem_id") for c in contas if c.get("parcela_origem_id")}
    if origem_ids:
        all_parcelas = await db.contas_pagar.find(
            {"parcela_origem_id": {"$in": list(origem_ids)}},
            {"_id": 0, "parcela_origem_id": 1, "valor": 1, "valor_desconto": 1,
             "valor_juros": 1, "valor_multa": 1, "valor_pago": 1, "valor_final": 1,
             "status": 1, "total_parcelas": 1},
        ).to_list(5000)
        resumo: dict = {}
        for p in all_parcelas:
            oid = p.get("parcela_origem_id")
            v = p.get("valor", 0) or 0
            vf = (v - (p.get("valor_desconto", 0) or 0)
                  + (p.get("valor_juros", 0) or 0)
                  + (p.get("valor_multa", 0) or 0))
            pago = p.get("valor_pago", 0) or 0
            if p.get("status") == "quitada" and pago < vf:
                pago = vf
            r = resumo.setdefault(oid, {
                "total_geral": 0, "total_pago": 0, "saldo_restante": 0,
                "qtd_parcelas": 0, "qtd_quitadas": 0,
            })
            r["total_geral"] += vf
            r["total_pago"] += pago
            r["qtd_parcelas"] += 1
            if p.get("status") == "quitada":
                r["qtd_quitadas"] += 1
        for oid, r in resumo.items():
            r["total_geral"] = round(r["total_geral"], 2)
            r["total_pago"] = round(r["total_pago"], 2)
            r["saldo_restante"] = round(r["total_geral"] - r["total_pago"], 2)
        for conta in contas:
            oid = conta.get("parcela_origem_id")
            if oid and oid in resumo:
                conta["grupo_parcelas"] = resumo[oid]

    return contas


@financeiro_router.get("/contas-pagar/grupo/{parcela_origem_id}")
async def get_grupo_parcelas_pagar(
    parcela_origem_id: str, current_user: dict = Depends(get_current_user)
):
    """Retorna todas as parcelas do mesmo grupo (mesmo parcela_origem_id),
    ignorando filtros, com resumo de saldo."""
    parcelas = await db.contas_pagar.find(
        {"parcela_origem_id": parcela_origem_id}, {"_id": 0}
    ).sort("numero_parcela", 1).to_list(5000)
    if not parcelas:
        raise HTTPException(status_code=404, detail="Grupo de parcelas não encontrado")

    total_geral = 0.0
    total_pago = 0.0
    qtd_quitadas = 0
    for p in parcelas:
        v = p.get("valor", 0) or 0
        vf = (v - (p.get("valor_desconto", 0) or 0)
              + (p.get("valor_juros", 0) or 0)
              + (p.get("valor_multa", 0) or 0))
        p["valor_final"] = vf
        pago = p.get("valor_pago", 0) or 0
        if p.get("status") == "quitada" and pago < vf:
            pago = vf
        total_geral += vf
        total_pago += pago
        if p.get("status") == "quitada":
            qtd_quitadas += 1
    return {
        "parcela_origem_id": parcela_origem_id,
        "parcelas": parcelas,
        "resumo": {
            "total_geral": round(total_geral, 2),
            "total_pago": round(total_pago, 2),
            "saldo_restante": round(total_geral - total_pago, 2),
            "qtd_parcelas": len(parcelas),
            "qtd_quitadas": qtd_quitadas,
        },
    }


@financeiro_router.post("/contas-pagar")
async def create_conta_pagar(
    data: ContaPagarCreate, current_user: dict = Depends(get_current_user)
):
    numero = await get_next_sequence("contas_pagar")
    valor_final = (
        data.valor
        - (data.valor_desconto or 0)
        + (data.valor_juros or 0)
        + (data.valor_multa or 0)
        - (data.valor_retencao or 0)
    )

    conta = {
        "id": str(uuid.uuid4()),
        "numero": numero,
        **data.model_dump(),
        "valor_final": valor_final,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.contas_pagar.insert_one(conta)
    await create_audit_log(current_user, "create", "conta_pagar", conta["id"], data.descricao,
                           module="Administrativo", reversible=True)
    conta.pop("_id", None)
    return conta


@financeiro_router.post("/contas-pagar/parcelado")
async def create_conta_pagar_parcelada(
    data: ContaParceladaCreate, current_user: dict = Depends(get_current_user)
):
    """Cria múltiplas parcelas de uma conta a pagar"""
    if data.total_parcelas < 1:
        raise HTTPException(status_code=400, detail="Número de parcelas deve ser maior que zero")
    if data.total_parcelas > 120:
        raise HTTPException(status_code=400, detail="Número máximo de parcelas é 120")

    valor_parcela = round(data.valor_total / data.total_parcelas, 2)
    valor_ultima_parcela = round(data.valor_total - (valor_parcela * (data.total_parcelas - 1)), 2)
    # Distribui retenção proporcionalmente entre as parcelas
    retencao_total = float(data.valor_retencao or 0)
    retencao_parcela = round(retencao_total / data.total_parcelas, 2) if data.total_parcelas else 0
    retencao_ultima = round(retencao_total - (retencao_parcela * (data.total_parcelas - 1)), 2)
    parcela_origem_id = str(uuid.uuid4())

    parcelas_criadas = []
    data_vencimento = datetime.strptime(data.data_primeiro_vencimento, "%Y-%m-%d")

    for i in range(data.total_parcelas):
        numero_parcela = i + 1
        valor = valor_parcela if numero_parcela < data.total_parcelas else valor_ultima_parcela
        retencao = retencao_parcela if numero_parcela < data.total_parcelas else retencao_ultima
        numero = await get_next_sequence("contas_pagar")

        conta = {
            "id": str(uuid.uuid4()),
            "numero": numero,
            "fornecedor_id": data.fornecedor_id,
            "fornecedor_nome": data.fornecedor_nome,
            "documento": data.documento,
            "numero_doc": data.numero_doc,
            "descricao": f"{data.descricao} - Parcela {numero_parcela}/{data.total_parcelas}",
            "valor": valor,
            "valor_desconto": 0,
            "valor_juros": 0,
            "valor_multa": 0,
            "valor_retencao": retencao,
            "valor_final": valor - retencao,
            "total_parcelas": data.total_parcelas,
            "numero_parcela": numero_parcela,
            "parcela_origem_id": parcela_origem_id,
            "data_emissao": data.data_emissao,
            "data_vencimento": data_vencimento.strftime("%Y-%m-%d"),
            "data_pagamento": None,
            "data_cancelamento": None,
            "plano_conta_id": data.plano_conta_id,
            "plano_conta_nome": data.plano_conta_nome,
            "subconta_id": data.subconta_id,
            "subconta_nome": data.subconta_nome,
            "centro_custo": data.centro_custo,
            "frota_id": data.frota_id,
            "frota_nome": data.frota_nome,
            "forma_pagamento": data.forma_pagamento,
            "conta_movimento": data.conta_movimento,
            "conta_bancaria_id": data.conta_bancaria_id,
            "conta_bancaria_nome": data.conta_bancaria_nome,
            "status": "em_aberto",
            "observacoes": data.observacoes,
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        # Propaga campos de linhagem/origem para cada parcela
        for fld in ("nfe_id", "nfse_id", "anexos", "origem", "folha_id",
                    "ordem_servico_id", "contrato_id"):
            val = getattr(data, fld, None)
            if val is not None:
                conta[fld] = val
        await db.contas_pagar.insert_one(conta)
        conta.pop("_id", None)
        parcelas_criadas.append(conta)
        data_vencimento = data_vencimento + timedelta(days=data.intervalo_dias)

    await create_audit_log(
        current_user, "create", "conta_pagar_parcelada", parcela_origem_id,
        f"{data.descricao} - {data.total_parcelas} parcelas",
        module="Administrativo",
    )

    return {
        "message": f"{data.total_parcelas} parcelas criadas com sucesso",
        "parcela_origem_id": parcela_origem_id,
        "valor_total": data.valor_total,
        "valor_parcela": valor_parcela,
        "parcelas": parcelas_criadas,
    }


@financeiro_router.put("/contas-pagar/{id}")
async def update_conta_pagar(
    id: str, data: ContaPagarCreate, current_user: dict = Depends(get_current_user)
):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    valor_final = (
        data.valor
        - (data.valor_desconto or 0)
        + (data.valor_juros or 0)
        + (data.valor_multa or 0)
        - (data.valor_retencao or 0)
    )
    update_data = data.model_dump()
    update_data["valor_final"] = valor_final
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Editar apenas METADADOS da conta. NUNCA sobrescrever o estado de
    # pagamento — o usuário pode editar uma conta quitada (ex: ajustar o
    # plano de contas ou anexar nota) e o status DEVE permanecer quitada.
    # Esses campos são alterados exclusivamente pelos endpoints /quitar
    # e /cancelar.
    PAYMENT_FIELDS = {
        "status", "valor_pago", "saldo_restante", "pagamentos",
        "data_pagamento", "data_ultimo_pagamento", "data_cancelamento",
    }
    for f in PAYMENT_FIELDS:
        update_data.pop(f, None)

    await db.contas_pagar.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(
        current_user, "update", "conta_pagar", id, data.descricao,
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return await db.contas_pagar.find_one({"id": id}, {"_id": 0})


@financeiro_router.patch("/contas-pagar/{id}/quitar")
async def quitar_conta_pagar(
    id: str,
    data: Optional[QuitarContaRequest] = None,
    current_user: dict = Depends(get_current_user),
):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    data_pagamento = data.data_pagamento if data and data.data_pagamento else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conta_bancaria_id = data.conta_bancaria_id if data else None

    valor_total = conta.get("valor_final") or conta.get("valor", 0)
    valor_ja_pago = conta.get("valor_pago", 0) or 0
    saldo_restante_atual = valor_total - valor_ja_pago

    valor_pago_agora = data.valor_pago if data and data.valor_pago is not None else saldo_restante_atual

    if valor_pago_agora > saldo_restante_atual + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Valor pago ({valor_pago_agora:.2f}) excede o saldo restante ({saldo_restante_atual:.2f})",
        )

    novo_valor_pago = valor_ja_pago + valor_pago_agora
    novo_saldo_restante = valor_total - novo_valor_pago

    if novo_saldo_restante <= 0.01:
        novo_status = "quitada"
        novo_saldo_restante = 0
    else:
        novo_status = "parcial"

    pagamento_registro = {
        "id": str(uuid.uuid4()),
        "data": data_pagamento,
        "valor": valor_pago_agora,
        "valor_juros": (data.valor_juros or 0) if data else 0,
        "valor_multa": (data.valor_multa or 0) if data else 0,
        "valor_desconto": (data.valor_desconto or 0) if data else 0,
        "conta_bancaria_id": conta_bancaria_id,
        "observacao": data.observacao if data else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("name", current_user.get("email", "")),
    }

    # Valor líquido realmente movimentado no banco (incluindo juros/multa/desconto)
    ajuste_liquido = ((data.valor_juros or 0) + (data.valor_multa or 0) - (data.valor_desconto or 0)) if data else 0
    valor_liquido_movimentado = valor_pago_agora + ajuste_liquido

    pagamentos_historico = conta.get("pagamentos", []) or []
    pagamentos_historico.append(pagamento_registro)

    update_data = {
        "status": novo_status,
        "valor_pago": novo_valor_pago,
        "saldo_restante": novo_saldo_restante,
        "pagamentos": pagamentos_historico,
        "data_ultimo_pagamento": data_pagamento,
    }
    if novo_status == "quitada":
        update_data["data_pagamento"] = data_pagamento

    if conta_bancaria_id:
        update_data["conta_bancaria_id"] = conta_bancaria_id
        conta_bancaria = await db.contas_bancarias.find_one({"id": conta_bancaria_id}, {"_id": 0})
        if conta_bancaria:
            novo_saldo_banco = (conta_bancaria.get("saldo_atual", 0) or 0) - valor_liquido_movimentado
            await db.contas_bancarias.update_one(
                {"id": conta_bancaria_id},
                {"$set": {"saldo_atual": novo_saldo_banco, "updated_at": datetime.now(timezone.utc).isoformat()}},
            )

    await db.contas_pagar.update_one({"id": id}, {"$set": update_data})

    tipo_quitacao = "QUITADA" if novo_status == "quitada" else f"PAGAMENTO PARCIAL R$ {valor_pago_agora:.2f}"
    await create_audit_log(
        current_user, "update", "conta_pagar", id,
        f"{conta['descricao']} - {tipo_quitacao} em {data_pagamento}",
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {
        "message": "Pagamento registrado com sucesso",
        "data_pagamento": data_pagamento,
        "valor_pago": valor_pago_agora,
        "valor_total_pago": novo_valor_pago,
        "saldo_restante": novo_saldo_restante,
        "status": novo_status,
    }


@financeiro_router.patch("/contas-pagar/{id}/cancelar")
async def cancelar_conta_pagar(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    await db.contas_pagar.update_one(
        {"id": id},
        {"$set": {"status": "cancelada", "data_cancelamento": datetime.now(timezone.utc).strftime("%Y-%m-%d")}},
    )
    await create_audit_log(current_user, "update", "conta_pagar", id, f"{conta['descricao']} - CANCELADA",
                           module="Administrativo", snapshot=conta, reversible=True)
    return {"message": "Conta cancelada"}


@financeiro_router.delete("/contas-pagar/{id}")
async def delete_conta_pagar(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    await db.contas_pagar.delete_one({"id": id})

    # Desvincula NF-e e NFS-e que referenciavam esta conta para permitir
    # criar uma nova conta a pagar a partir delas.
    await db.nfe_importadas.update_many(
        {"conta_pagar_id": id},
        {"$set": {"conta_pagar_id": None}},
    )
    await db.nfse_importadas.update_many(
        {"conta_pagar_id": id},
        {"$set": {"conta_pagar_id": None}},
    )

    await create_audit_log(
        current_user, "delete", "conta_pagar", id, conta["descricao"],
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {"message": "Conta excluída"}


# ============================================================================
# CONTAS A RECEBER
# ============================================================================

@financeiro_router.get("/contas-receber")
async def get_contas_receber(
    status: Optional[str] = None,
    vencimento: Optional[str] = None,
    forma_pagamento: Optional[str] = None,
    plano_conta_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    tipo_data: Optional[str] = "vencimento",
    valor: Optional[float] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    query: dict = {}
    # Status "a_receber" é virtual: engloba todas as contas ainda não totalmente
    # recebidas (em_aberto + parcial + pendente).
    if status:
        if status == "a_receber" or status == "a_pagar":
            query["status"] = {"$in": ["em_aberto", "parcial", "pendente"]}
        else:
            query["status"] = status
    if forma_pagamento:
        query["forma_pagamento"] = forma_pagamento
    if plano_conta_id:
        query["plano_conta_id"] = plano_conta_id
    if search:
        query["$or"] = [
            {"descricao": {"$regex": search, "$options": "i"}},
            {"cliente_nome": {"$regex": search, "$options": "i"}},
            {"documento": {"$regex": search, "$options": "i"}},
        ]
    if valor is not None:
        epsilon = 0.005
        query["$or"] = (query.get("$or") or []) + [
            {"valor": {"$gte": valor - epsilon, "$lte": valor + epsilon}},
            {"valor_final": {"$gte": valor - epsilon, "$lte": valor + epsilon}},
        ]

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    status_pendente = {"$in": ["em_aberto", "parcial", "pendente"]}
    if vencimento == "vencidas":
        query["data_vencimento"] = {"$lt": hoje}
        query["status"] = status_pendente
    elif vencimento == "hoje":
        query["data_vencimento"] = hoje
    elif vencimento == "a_vencer":
        query["data_vencimento"] = {"$gt": hoje}
        query["status"] = status_pendente

    if data_inicio and data_fim:
        campo_data = "data_recebimento" if tipo_data == "pagamento" else "data_vencimento"
        query[campo_data] = {"$gte": data_inicio, "$lte": data_fim}

    contas = await db.contas_receber.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(1000)

    for conta in contas:
        v = conta.get("valor", 0)
        desconto = conta.get("valor_desconto", 0)
        juros = conta.get("valor_juros", 0)
        multa = conta.get("valor_multa", 0)
        conta["valor_final"] = v - desconto + juros + multa

    # Anexa resumo de saldo do grupo de parcelas (todas as parcelas, ignorando filtros)
    origem_ids = {c.get("parcela_origem_id") for c in contas if c.get("parcela_origem_id")}
    if origem_ids:
        all_parcelas = await db.contas_receber.find(
            {"parcela_origem_id": {"$in": list(origem_ids)}},
            {"_id": 0, "parcela_origem_id": 1, "valor": 1, "valor_desconto": 1,
             "valor_juros": 1, "valor_multa": 1, "valor_pago": 1, "valor_final": 1,
             "status": 1, "total_parcelas": 1},
        ).to_list(5000)
        resumo: dict = {}
        for p in all_parcelas:
            oid = p.get("parcela_origem_id")
            v = p.get("valor", 0) or 0
            vf = (v - (p.get("valor_desconto", 0) or 0)
                  + (p.get("valor_juros", 0) or 0)
                  + (p.get("valor_multa", 0) or 0))
            pago = p.get("valor_pago", 0) or 0
            if p.get("status") == "quitada" and pago < vf:
                pago = vf
            r = resumo.setdefault(oid, {
                "total_geral": 0, "total_pago": 0, "saldo_restante": 0,
                "qtd_parcelas": 0, "qtd_quitadas": 0,
            })
            r["total_geral"] += vf
            r["total_pago"] += pago
            r["qtd_parcelas"] += 1
            if p.get("status") == "quitada":
                r["qtd_quitadas"] += 1
        for oid, r in resumo.items():
            r["total_geral"] = round(r["total_geral"], 2)
            r["total_pago"] = round(r["total_pago"], 2)
            r["saldo_restante"] = round(r["total_geral"] - r["total_pago"], 2)
        for conta in contas:
            oid = conta.get("parcela_origem_id")
            if oid and oid in resumo:
                conta["grupo_parcelas"] = resumo[oid]

    return contas


@financeiro_router.get("/contas-receber/grupo/{parcela_origem_id}")
async def get_grupo_parcelas_receber(
    parcela_origem_id: str, current_user: dict = Depends(get_current_user)
):
    """Retorna todas as parcelas do mesmo grupo de contas a receber."""
    parcelas = await db.contas_receber.find(
        {"parcela_origem_id": parcela_origem_id}, {"_id": 0}
    ).sort("numero_parcela", 1).to_list(5000)
    if not parcelas:
        raise HTTPException(status_code=404, detail="Grupo de parcelas não encontrado")

    total_geral = 0.0
    total_pago = 0.0
    qtd_quitadas = 0
    for p in parcelas:
        v = p.get("valor", 0) or 0
        vf = (v - (p.get("valor_desconto", 0) or 0)
              + (p.get("valor_juros", 0) or 0)
              + (p.get("valor_multa", 0) or 0))
        p["valor_final"] = vf
        pago = p.get("valor_pago", 0) or 0
        if p.get("status") == "quitada" and pago < vf:
            pago = vf
        total_geral += vf
        total_pago += pago
        if p.get("status") == "quitada":
            qtd_quitadas += 1
    return {
        "parcela_origem_id": parcela_origem_id,
        "parcelas": parcelas,
        "resumo": {
            "total_geral": round(total_geral, 2),
            "total_pago": round(total_pago, 2),
            "saldo_restante": round(total_geral - total_pago, 2),
            "qtd_parcelas": len(parcelas),
            "qtd_quitadas": qtd_quitadas,
        },
    }


@financeiro_router.post("/contas-receber")
async def create_conta_receber(
    data: ContaReceberCreate, current_user: dict = Depends(get_current_user)
):
    numero = await get_next_sequence("contas_receber")
    valor_final = (
        data.valor
        - (data.valor_desconto or 0)
        + (data.valor_juros or 0)
        + (data.valor_multa or 0)
        - (data.valor_retencao or 0)
    )

    conta = {
        "id": str(uuid.uuid4()),
        "numero": numero,
        **data.model_dump(),
        "valor_final": valor_final,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.contas_receber.insert_one(conta)
    await create_audit_log(current_user, "create", "conta_receber", conta["id"], data.descricao,
                           module="Administrativo", reversible=True)
    conta.pop("_id", None)
    return conta


@financeiro_router.post("/contas-receber/parcelado")
async def create_conta_receber_parcelada(
    data: ContaReceberParceladaCreate, current_user: dict = Depends(get_current_user)
):
    if data.total_parcelas < 1:
        raise HTTPException(status_code=400, detail="Número de parcelas deve ser maior que zero")
    if data.total_parcelas > 120:
        raise HTTPException(status_code=400, detail="Número máximo de parcelas é 120")

    valor_parcela = round(data.valor_total / data.total_parcelas, 2)
    valor_ultima_parcela = round(data.valor_total - (valor_parcela * (data.total_parcelas - 1)), 2)
    # Distribui retenção proporcionalmente entre as parcelas
    retencao_total = float(data.valor_retencao or 0)
    retencao_parcela = round(retencao_total / data.total_parcelas, 2) if data.total_parcelas else 0
    retencao_ultima = round(retencao_total - (retencao_parcela * (data.total_parcelas - 1)), 2)
    parcela_origem_id = str(uuid.uuid4())

    parcelas_criadas = []
    data_vencimento = datetime.strptime(data.data_primeiro_vencimento, "%Y-%m-%d")

    for i in range(data.total_parcelas):
        numero_parcela = i + 1
        valor = valor_parcela if numero_parcela < data.total_parcelas else valor_ultima_parcela
        retencao = retencao_parcela if numero_parcela < data.total_parcelas else retencao_ultima
        numero = await get_next_sequence("contas_receber")

        conta = {
            "id": str(uuid.uuid4()),
            "numero": numero,
            "cliente_id": data.cliente_id,
            "cliente_nome": data.cliente_nome,
            "documento": data.documento,
            "numero_doc": data.numero_doc,
            "descricao": f"{data.descricao} - Parcela {numero_parcela}/{data.total_parcelas}",
            "valor": valor,
            "valor_desconto": 0,
            "valor_juros": 0,
            "valor_multa": 0,
            "valor_retencao": retencao,
            "valor_final": valor - retencao,
            "total_parcelas": data.total_parcelas,
            "numero_parcela": numero_parcela,
            "parcela_origem_id": parcela_origem_id,
            "data_emissao": data.data_emissao,
            "data_vencimento": data_vencimento.strftime("%Y-%m-%d"),
            "data_recebimento": None,
            "data_cancelamento": None,
            "plano_conta_id": data.plano_conta_id,
            "plano_conta_nome": data.plano_conta_nome,
            "subconta_id": data.subconta_id,
            "subconta_nome": data.subconta_nome,
            "centro_custo": data.centro_custo,
            "frota_id": data.frota_id,
            "frota_nome": data.frota_nome,
            "forma_pagamento": data.forma_pagamento,
            "conta_movimento": data.conta_movimento,
            "conta_bancaria_id": data.conta_bancaria_id,
            "conta_bancaria_nome": data.conta_bancaria_nome,
            "status": "em_aberto",
            "faturamento": data.faturamento,
            "observacoes": data.observacoes,
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        # Propaga campos de linhagem/origem para cada parcela
        for fld in ("nfe_id", "nfse_id", "anexos", "origem",
                    "ordem_servico_id", "contrato_id"):
            val = getattr(data, fld, None)
            if val is not None:
                conta[fld] = val
        await db.contas_receber.insert_one(conta)
        conta.pop("_id", None)
        parcelas_criadas.append(conta)
        data_vencimento = data_vencimento + timedelta(days=data.intervalo_dias)

    await create_audit_log(
        current_user, "create", "conta_receber_parcelada", parcela_origem_id,
        f"{data.descricao} - {data.total_parcelas} parcelas",
        module="Administrativo",
    )
    return {
        "message": f"{data.total_parcelas} parcelas criadas com sucesso",
        "parcela_origem_id": parcela_origem_id,
        "valor_total": data.valor_total,
        "valor_parcela": valor_parcela,
        "parcelas": parcelas_criadas,
    }


@financeiro_router.put("/contas-receber/{id}")
async def update_conta_receber(
    id: str, data: ContaReceberCreate, current_user: dict = Depends(get_current_user)
):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    valor_final = (
        data.valor
        - (data.valor_desconto or 0)
        + (data.valor_juros or 0)
        + (data.valor_multa or 0)
        - (data.valor_retencao or 0)
    )
    update_data = data.model_dump()
    update_data["valor_final"] = valor_final
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Editar apenas METADADOS — preservar estado de recebimento. Status
    # (quitada/parcial/cancelada) e histórico de pagamentos só mudam pelos
    # endpoints /quitar e /cancelar.
    PAYMENT_FIELDS = {
        "status", "valor_pago", "saldo_restante", "pagamentos",
        "data_pagamento", "data_ultimo_pagamento", "data_cancelamento",
    }
    for f in PAYMENT_FIELDS:
        update_data.pop(f, None)

    await db.contas_receber.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(
        current_user, "update", "conta_receber", id, data.descricao,
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return await db.contas_receber.find_one({"id": id}, {"_id": 0})


@financeiro_router.patch("/contas-receber/{id}/quitar")
async def quitar_conta_receber(
    id: str,
    data: Optional[QuitarContaReceberRequest] = None,
    current_user: dict = Depends(get_current_user),
):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    # Frontend pode mandar data_pagamento/valor_pago (alias) — aceitar ambos
    data_recebimento = (
        (data.data_recebimento if data and data.data_recebimento else None)
        or (data.data_pagamento if data and data.data_pagamento else None)
        or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    conta_bancaria_id = data.conta_bancaria_id if data else None

    valor_total = conta.get("valor_final") or conta.get("valor", 0)
    valor_ja_recebido = conta.get("valor_recebido", 0) or 0
    saldo_restante_atual = valor_total - valor_ja_recebido

    valor_recebido_input = None
    if data:
        valor_recebido_input = data.valor_recebido if data.valor_recebido is not None else data.valor_pago
    valor_recebido_agora = valor_recebido_input if valor_recebido_input is not None else saldo_restante_atual

    if valor_recebido_agora > saldo_restante_atual + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Valor recebido ({valor_recebido_agora:.2f}) excede o saldo restante ({saldo_restante_atual:.2f})",
        )

    novo_valor_recebido = valor_ja_recebido + valor_recebido_agora
    novo_saldo_restante = valor_total - novo_valor_recebido

    if novo_saldo_restante <= 0.01:
        novo_status = "quitada"
        novo_saldo_restante = 0
    else:
        novo_status = "parcial"

    recebimento_registro = {
        "id": str(uuid.uuid4()),
        "data": data_recebimento,
        "valor": valor_recebido_agora,
        "valor_juros": (data.valor_juros or 0) if data else 0,
        "valor_multa": (data.valor_multa or 0) if data else 0,
        "valor_desconto": (data.valor_desconto or 0) if data else 0,
        "conta_bancaria_id": conta_bancaria_id,
        "observacao": data.observacao if data else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("name", current_user.get("email", "")),
    }

    # Valor líquido que entra na conta bancária (base + juros + multa - desconto)
    ajuste_liquido = ((data.valor_juros or 0) + (data.valor_multa or 0) - (data.valor_desconto or 0)) if data else 0
    valor_liquido_recebido = valor_recebido_agora + ajuste_liquido

    recebimentos_historico = conta.get("recebimentos", []) or []
    recebimentos_historico.append(recebimento_registro)

    update_data = {
        "status": novo_status,
        "valor_recebido": novo_valor_recebido,
        "saldo_restante": novo_saldo_restante,
        "recebimentos": recebimentos_historico,
        "data_ultimo_recebimento": data_recebimento,
    }
    if novo_status == "quitada":
        update_data["data_recebimento"] = data_recebimento

    if conta_bancaria_id:
        update_data["conta_bancaria_id"] = conta_bancaria_id
        conta_bancaria = await db.contas_bancarias.find_one({"id": conta_bancaria_id}, {"_id": 0})
        if conta_bancaria:
            novo_saldo_banco = (conta_bancaria.get("saldo_atual", 0) or 0) + valor_liquido_recebido
            await db.contas_bancarias.update_one(
                {"id": conta_bancaria_id},
                {"$set": {"saldo_atual": novo_saldo_banco, "updated_at": datetime.now(timezone.utc).isoformat()}},
            )

    await db.contas_receber.update_one({"id": id}, {"$set": update_data})

    tipo_quitacao = "QUITADA" if novo_status == "quitada" else f"RECEBIMENTO PARCIAL R$ {valor_recebido_agora:.2f}"
    await create_audit_log(
        current_user, "update", "conta_receber", id,
        f"{conta['descricao']} - {tipo_quitacao} em {data_recebimento}",
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {
        "message": "Recebimento registrado com sucesso",
        "data_recebimento": data_recebimento,
        "valor_recebido": valor_recebido_agora,
        "valor_total_recebido": novo_valor_recebido,
        "saldo_restante": novo_saldo_restante,
        "status": novo_status,
    }


@financeiro_router.patch("/contas-receber/{id}/cancelar")
async def cancelar_conta_receber(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    await db.contas_receber.update_one(
        {"id": id},
        {"$set": {"status": "cancelada", "data_cancelamento": datetime.now(timezone.utc).strftime("%Y-%m-%d")}},
    )
    await create_audit_log(current_user, "update", "conta_receber", id, f"{conta['descricao']} - CANCELADA",
                           module="Administrativo", snapshot=conta, reversible=True)
    return {"message": "Conta cancelada"}


@financeiro_router.delete("/contas-receber/{id}")
async def delete_conta_receber(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    await db.contas_receber.delete_one({"id": id})

    # Desvincula NF-e e NFS-e que referenciavam esta conta a receber.
    await db.nfe_importadas.update_many(
        {"conta_receber_id": id},
        {"$set": {"conta_receber_id": None}},
    )
    await db.nfse_importadas.update_many(
        {"conta_receber_id": id},
        {"$set": {"conta_receber_id": None}},
    )

    await create_audit_log(
        current_user, "delete", "conta_receber", id, conta["descricao"],
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {"message": "Conta excluída"}
