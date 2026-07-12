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
    # Também blindamos `parcela_origem_id`: ele identifica o grupo de
    # parcelas e NÃO pode ser zerado por uma edição que não envie o campo
    # no payload (caso típico: Pydantic preenche com None o default).
    PAYMENT_FIELDS = {
        "status", "valor_pago", "saldo_restante", "pagamentos",
        "data_pagamento", "data_ultimo_pagamento", "data_cancelamento",
        "parcela_origem_id",
    }
    for f in PAYMENT_FIELDS:
        update_data.pop(f, None)

    await db.contas_pagar.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(
        current_user, "update", "conta_pagar", id, data.descricao,
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return await db.contas_pagar.find_one({"id": id}, {"_id": 0})


def _recompute_conta_state(lancamentos: list, valor_total: float):
    """Recalcula (valor_confirmado, saldo, status) a partir dos lançamentos.
    Conta APENAS entradas com status 'pago'. Entradas antigas sem 'status' são
    consideradas 'pago' (compatibilidade com dados existentes)."""
    pago = 0.0
    for p in (lancamentos or []):
        if p.get("status", "pago") == "pago":
            pago += float(p.get("valor") or 0)
    pago = round(pago, 2)
    if valor_total and pago >= valor_total - 0.01:
        return pago, 0.0, "quitada"
    if pago > 0.01:
        return pago, round(valor_total - pago, 2), "parcial"
    return 0.0, round(valor_total, 2), "em_aberto"


class ConfirmarPagamentoRequest(BaseModel):
    pago: Optional[bool] = True
    conta_bancaria_id: Optional[str] = None


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
    pagamentos_historico = conta.get("pagamentos", []) or []

    ja_pago = sum(float(p.get("valor") or 0) for p in pagamentos_historico if p.get("status", "pago") == "pago")
    ja_pendente = sum(float(p.get("valor") or 0) for p in pagamentos_historico if p.get("status", "pago") == "a_pagar")

    # Pagamento PARCIAL (usuário informou um valor) é registrado como PENDENTE ("a pagar"):
    # não soma ao total pago nem move o banco até ser CONFIRMADO manualmente.
    # Quitação TOTAL (valor_pago ausente) continua confirmada na hora.
    registrar_pendente = bool(data and data.valor_pago is not None)

    if registrar_pendente:
        valor_pago_agora = data.valor_pago
        disponivel = valor_total - ja_pago - ja_pendente
        if valor_pago_agora > disponivel + 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Valor ({valor_pago_agora:.2f}) excede o saldo ainda não lançado ({disponivel:.2f})",
            )
    else:
        valor_pago_agora = valor_total - ja_pago - ja_pendente

    pagamento_registro = {
        "id": str(uuid.uuid4()),
        "data": data_pagamento,
        "valor": valor_pago_agora,
        "valor_juros": (data.valor_juros or 0) if data else 0,
        "valor_multa": (data.valor_multa or 0) if data else 0,
        "valor_desconto": (data.valor_desconto or 0) if data else 0,
        "conta_bancaria_id": conta_bancaria_id,
        "observacao": data.observacao if data else None,
        "status": "a_pagar" if registrar_pendente else "pago",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("name", current_user.get("email", "")),
    }
    if not registrar_pendente:
        pagamento_registro["data_confirmacao"] = data_pagamento
    pagamentos_historico.append(pagamento_registro)

    # Estado da conta considera apenas lançamentos CONFIRMADOS (status pago)
    novo_valor_pago, novo_saldo_restante, novo_status = _recompute_conta_state(pagamentos_historico, valor_total)

    update_data = {
        "status": novo_status,
        "valor_pago": novo_valor_pago,
        "saldo_restante": novo_saldo_restante,
        "pagamentos": pagamentos_historico,
        "data_ultimo_pagamento": data_pagamento,
    }
    if novo_status == "quitada":
        update_data["data_pagamento"] = data_pagamento

    # Movimenta o banco apenas quando o lançamento já entra confirmado (quitação total)
    if conta_bancaria_id and not registrar_pendente:
        ajuste_liquido = ((data.valor_juros or 0) + (data.valor_multa or 0) - (data.valor_desconto or 0)) if data else 0
        valor_liquido_movimentado = valor_pago_agora + ajuste_liquido
        update_data["conta_bancaria_id"] = conta_bancaria_id
        conta_bancaria = await db.contas_bancarias.find_one({"id": conta_bancaria_id}, {"_id": 0})
        if conta_bancaria:
            novo_saldo_banco = (conta_bancaria.get("saldo_atual", 0) or 0) - valor_liquido_movimentado
            await db.contas_bancarias.update_one(
                {"id": conta_bancaria_id},
                {"$set": {"saldo_atual": novo_saldo_banco, "updated_at": datetime.now(timezone.utc).isoformat()}},
            )

    await db.contas_pagar.update_one({"id": id}, {"$set": update_data})

    if registrar_pendente:
        tipo_quitacao = f"PAGAMENTO PARCIAL PENDENTE R$ {valor_pago_agora:.2f}"
        msg = "Pagamento parcial registrado como PENDENTE (a pagar). Confirme como pago para somar ao total."
    else:
        tipo_quitacao = "QUITADA" if novo_status == "quitada" else f"PAGAMENTO R$ {valor_pago_agora:.2f}"
        msg = "Pagamento registrado com sucesso"
    await create_audit_log(
        current_user, "update", "conta_pagar", id,
        f"{conta['descricao']} - {tipo_quitacao} em {data_pagamento}",
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {
        "message": msg,
        "data_pagamento": data_pagamento,
        "valor_pago": valor_pago_agora,
        "valor_total_pago": novo_valor_pago,
        "saldo_restante": novo_saldo_restante,
        "status": novo_status,
        "pendente": registrar_pendente,
        "pagamento_id": pagamento_registro["id"],
    }


@financeiro_router.patch("/contas-pagar/{id}/pagamento/{pagamento_id}/confirmar")
async def confirmar_pagamento_pagar(
    id: str, pagamento_id: str,
    data: Optional[ConfirmarPagamentoRequest] = None,
    current_user: dict = Depends(get_current_user),
):
    """Confirma (marca como PAGO) ou reverte para pendente um pagamento parcial.
    Só ao confirmar o valor é somado ao total pago da conta e movido no banco."""
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    pagamentos = conta.get("pagamentos", []) or []
    entry = next((p for p in pagamentos if p.get("id") == pagamento_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Lançamento de pagamento não encontrado")

    marcar_pago = data.pago if (data and data.pago is not None) else True
    estava_pago = entry.get("status", "pago") == "pago"
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry["status"] = "pago" if marcar_pago else "a_pagar"
    if marcar_pago:
        entry["data_confirmacao"] = hoje
        if data and data.conta_bancaria_id:
            entry["conta_bancaria_id"] = data.conta_bancaria_id

    valor_total = conta.get("valor_final") or conta.get("valor", 0)
    novo_valor_pago, novo_saldo, novo_status = _recompute_conta_state(pagamentos, valor_total)
    update = {
        "pagamentos": pagamentos,
        "valor_pago": novo_valor_pago,
        "saldo_restante": novo_saldo,
        "status": novo_status,
    }
    if novo_status == "quitada":
        update["data_pagamento"] = entry.get("data") or hoje

    # Movimenta o banco somente na transição de status
    cb_id = entry.get("conta_bancaria_id")
    if cb_id and (marcar_pago != estava_pago):
        ajuste = (entry.get("valor_juros", 0) or 0) + (entry.get("valor_multa", 0) or 0) - (entry.get("valor_desconto", 0) or 0)
        liquido = (float(entry.get("valor") or 0)) + ajuste
        conta_bancaria = await db.contas_bancarias.find_one({"id": cb_id}, {"_id": 0})
        if conta_bancaria:
            delta = -liquido if marcar_pago else liquido
            await db.contas_bancarias.update_one(
                {"id": cb_id},
                {"$set": {"saldo_atual": (conta_bancaria.get("saldo_atual", 0) or 0) + delta, "updated_at": datetime.now(timezone.utc).isoformat()}},
            )

    await db.contas_pagar.update_one({"id": id}, {"$set": update})
    await create_audit_log(
        current_user, "update", "conta_pagar", id,
        f"{conta['descricao']} - PAGAMENTO {'CONFIRMADO' if marcar_pago else 'REVERTIDO P/ PENDENTE'} R$ {float(entry.get('valor') or 0):.2f}",
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {
        "message": "Pagamento confirmado" if marcar_pago else "Pagamento revertido para pendente",
        "valor_total_pago": novo_valor_pago,
        "saldo_restante": novo_saldo,
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
    # endpoints /quitar e /cancelar. Também blindamos `parcela_origem_id`:
    # ele identifica o grupo de parcelas e NÃO pode ser zerado por uma
    # edição que não envie o campo no payload.
    PAYMENT_FIELDS = {
        "status", "valor_pago", "valor_recebido", "saldo_restante",
        "pagamentos", "recebimentos",
        "data_pagamento", "data_recebimento", "data_ultimo_pagamento",
        "data_ultimo_recebimento", "data_cancelamento",
        "parcela_origem_id",
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
    recebimentos_historico = conta.get("recebimentos", []) or []

    ja_recebido = sum(float(p.get("valor") or 0) for p in recebimentos_historico if p.get("status", "pago") == "pago")
    ja_pendente = sum(float(p.get("valor") or 0) for p in recebimentos_historico if p.get("status", "pago") == "a_pagar")

    valor_recebido_input = None
    if data:
        valor_recebido_input = data.valor_recebido if data.valor_recebido is not None else data.valor_pago

    # Recebimento PARCIAL fica PENDENTE ("a receber") até ser confirmado manualmente.
    registrar_pendente = valor_recebido_input is not None

    if registrar_pendente:
        valor_recebido_agora = valor_recebido_input
        disponivel = valor_total - ja_recebido - ja_pendente
        if valor_recebido_agora > disponivel + 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Valor ({valor_recebido_agora:.2f}) excede o saldo ainda não lançado ({disponivel:.2f})",
            )
    else:
        valor_recebido_agora = valor_total - ja_recebido - ja_pendente

    recebimento_registro = {
        "id": str(uuid.uuid4()),
        "data": data_recebimento,
        "valor": valor_recebido_agora,
        "valor_juros": (data.valor_juros or 0) if data else 0,
        "valor_multa": (data.valor_multa or 0) if data else 0,
        "valor_desconto": (data.valor_desconto or 0) if data else 0,
        "conta_bancaria_id": conta_bancaria_id,
        "observacao": data.observacao if data else None,
        "status": "a_pagar" if registrar_pendente else "pago",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("name", current_user.get("email", "")),
    }
    if not registrar_pendente:
        recebimento_registro["data_confirmacao"] = data_recebimento
    recebimentos_historico.append(recebimento_registro)

    novo_valor_recebido, novo_saldo_restante, novo_status = _recompute_conta_state(recebimentos_historico, valor_total)

    update_data = {
        "status": novo_status,
        "valor_recebido": novo_valor_recebido,
        "saldo_restante": novo_saldo_restante,
        "recebimentos": recebimentos_historico,
        "data_ultimo_recebimento": data_recebimento,
    }
    if novo_status == "quitada":
        update_data["data_recebimento"] = data_recebimento

    if conta_bancaria_id and not registrar_pendente:
        ajuste_liquido = ((data.valor_juros or 0) + (data.valor_multa or 0) - (data.valor_desconto or 0)) if data else 0
        valor_liquido_recebido = valor_recebido_agora + ajuste_liquido
        update_data["conta_bancaria_id"] = conta_bancaria_id
        conta_bancaria = await db.contas_bancarias.find_one({"id": conta_bancaria_id}, {"_id": 0})
        if conta_bancaria:
            novo_saldo_banco = (conta_bancaria.get("saldo_atual", 0) or 0) + valor_liquido_recebido
            await db.contas_bancarias.update_one(
                {"id": conta_bancaria_id},
                {"$set": {"saldo_atual": novo_saldo_banco, "updated_at": datetime.now(timezone.utc).isoformat()}},
            )

    await db.contas_receber.update_one({"id": id}, {"$set": update_data})

    if registrar_pendente:
        tipo_quitacao = f"RECEBIMENTO PARCIAL PENDENTE R$ {valor_recebido_agora:.2f}"
        msg = "Recebimento parcial registrado como PENDENTE (a receber). Confirme como recebido para somar ao total."
    else:
        tipo_quitacao = "QUITADA" if novo_status == "quitada" else f"RECEBIMENTO R$ {valor_recebido_agora:.2f}"
        msg = "Recebimento registrado com sucesso"
    await create_audit_log(
        current_user, "update", "conta_receber", id,
        f"{conta['descricao']} - {tipo_quitacao} em {data_recebimento}",
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {
        "message": msg,
        "data_recebimento": data_recebimento,
        "valor_recebido": valor_recebido_agora,
        "valor_total_recebido": novo_valor_recebido,
        "saldo_restante": novo_saldo_restante,
        "status": novo_status,
        "pendente": registrar_pendente,
        "recebimento_id": recebimento_registro["id"],
    }


@financeiro_router.patch("/contas-receber/{id}/recebimento/{recebimento_id}/confirmar")
async def confirmar_recebimento(
    id: str, recebimento_id: str,
    data: Optional[ConfirmarPagamentoRequest] = None,
    current_user: dict = Depends(get_current_user),
):
    """Confirma (marca como RECEBIDO) ou reverte para pendente um recebimento parcial."""
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    recebimentos = conta.get("recebimentos", []) or []
    entry = next((p for p in recebimentos if p.get("id") == recebimento_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Lançamento de recebimento não encontrado")

    marcar_pago = data.pago if (data and data.pago is not None) else True
    estava_pago = entry.get("status", "pago") == "pago"
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry["status"] = "pago" if marcar_pago else "a_pagar"
    if marcar_pago:
        entry["data_confirmacao"] = hoje
        if data and data.conta_bancaria_id:
            entry["conta_bancaria_id"] = data.conta_bancaria_id

    valor_total = conta.get("valor_final") or conta.get("valor", 0)
    novo_valor_recebido, novo_saldo, novo_status = _recompute_conta_state(recebimentos, valor_total)
    update = {
        "recebimentos": recebimentos,
        "valor_recebido": novo_valor_recebido,
        "saldo_restante": novo_saldo,
        "status": novo_status,
    }
    if novo_status == "quitada":
        update["data_recebimento"] = entry.get("data") or hoje

    cb_id = entry.get("conta_bancaria_id")
    if cb_id and (marcar_pago != estava_pago):
        ajuste = (entry.get("valor_juros", 0) or 0) + (entry.get("valor_multa", 0) or 0) - (entry.get("valor_desconto", 0) or 0)
        liquido = (float(entry.get("valor") or 0)) + ajuste
        conta_bancaria = await db.contas_bancarias.find_one({"id": cb_id}, {"_id": 0})
        if conta_bancaria:
            delta = liquido if marcar_pago else -liquido
            await db.contas_bancarias.update_one(
                {"id": cb_id},
                {"$set": {"saldo_atual": (conta_bancaria.get("saldo_atual", 0) or 0) + delta, "updated_at": datetime.now(timezone.utc).isoformat()}},
            )

    await db.contas_receber.update_one({"id": id}, {"$set": update})
    await create_audit_log(
        current_user, "update", "conta_receber", id,
        f"{conta['descricao']} - RECEBIMENTO {'CONFIRMADO' if marcar_pago else 'REVERTIDO P/ PENDENTE'} R$ {float(entry.get('valor') or 0):.2f}",
        module="Administrativo", snapshot=conta, reversible=True,
    )
    return {
        "message": "Recebimento confirmado" if marcar_pago else "Recebimento revertido para pendente",
        "valor_total_recebido": novo_valor_recebido,
        "saldo_restante": novo_saldo,
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


# ============================================================================
# RECOVERY — Restaurar parcela_origem_id de contas que perderam o vínculo
# devido ao bug do PUT (sessão 7). Use ?dry_run=true para preview.
# ============================================================================

async def _recover_parcela_vinculos(
    collection_name: str,
    fornecedor_key: str,
    dry_run: bool,
    current_user: dict,
) -> dict:
    """Restaura `parcela_origem_id` em contas órfãs (None) que pertencem a um
    grupo de parcelas. Critério de agrupamento (deve ser idêntico em todas
    as parcelas do mesmo grupo):
       fornecedor/cliente + documento + data_emissao + valor + total_parcelas

    Estratégia:
       1) Buscar todas as contas com parcela_origem_id=None E total_parcelas>1
       2) Agrupar pelos critérios acima
       3) Se um grupo tem EXATAMENTE `total_parcelas` itens, gera novo
          parcela_origem_id e atribui a todos.
       4) Grupos incompletos viram "conflitos" (não tocados).

    Quando há parcelas no banco com parcela_origem_id JÁ preenchido que casam
    com o mesmo critério (algumas órfãs + algumas com vínculo), reaproveitamos
    o origem_id existente em vez de criar um novo.
    """
    collection = db[collection_name]

    # 1) Buscar parcelas órfãs (com indício de fazer parte de grupo)
    query = {
        "$or": [
            {"parcela_origem_id": None},
            {"parcela_origem_id": {"$exists": False}},
        ],
        "total_parcelas": {"$gt": 1},
    }
    orfas = await collection.find(query, {"_id": 0}).to_list(20000)

    def _grupo_key(c: dict) -> tuple:
        return (
            c.get(fornecedor_key) or "",
            (c.get("documento") or "").strip().lower(),
            (c.get("numero_doc") or "").strip().lower(),
            (c.get("data_emissao") or "")[:10],
            round(float(c.get("valor") or 0), 2),
            int(c.get("total_parcelas") or 0),
        )

    # 2) Agrupar órfãs pelo critério
    grupos: dict[tuple, list[dict]] = {}
    for c in orfas:
        grupos.setdefault(_grupo_key(c), []).append(c)

    resultado = {
        "collection": collection_name,
        "dry_run": dry_run,
        "orfas_encontradas": len(orfas),
        "grupos_completos_restaurados": 0,
        "parcelas_restauradas": 0,
        "grupos_reutilizando_origem_existente": 0,
        "conflitos": [],  # grupos incompletos
        "exemplos": [],
    }

    for chave, parcelas in grupos.items():
        total_parcelas = chave[5]
        # Procurar se já existe alguma parcela COM origem_id e mesmo critério
        # (caso típico: 1 parcela perdeu vínculo, outras 2 mantiveram).
        # Como fornecedor_id/documento/numero_doc podem estar None ou "" no
        # banco, usamos $in para casar ambas variantes.
        def _eq_or_empty(val):
            if val in (None, ""):
                return {"$in": [None, ""]}
            return val

        sibling_query = {
            fornecedor_key: _eq_or_empty(parcelas[0].get(fornecedor_key)),
            "documento": _eq_or_empty(parcelas[0].get("documento")),
            "numero_doc": _eq_or_empty(parcelas[0].get("numero_doc")),
            "data_emissao": parcelas[0].get("data_emissao"),
            "valor": parcelas[0].get("valor"),
            "total_parcelas": total_parcelas,
            "parcela_origem_id": {"$nin": [None, ""], "$exists": True},
        }
        sibling = await collection.find_one(sibling_query, {"_id": 0, "parcela_origem_id": 1})

        if sibling and sibling.get("parcela_origem_id"):
            # Reaproveita o origem_id existente em TODAS as órfãs do grupo
            origem_id = sibling["parcela_origem_id"]
            resultado["grupos_reutilizando_origem_existente"] += 1
            if not dry_run:
                await collection.update_many(
                    {"id": {"$in": [p["id"] for p in parcelas]}},
                    {"$set": {"parcela_origem_id": origem_id}},
                )
            resultado["parcelas_restauradas"] += len(parcelas)
            resultado["exemplos"].append({
                "tipo": "reaproveitado",
                "origem_id": origem_id,
                "criterio": {"fornecedor": chave[0], "documento": chave[1], "valor": chave[4], "total_parcelas": total_parcelas},
                "ids_restaurados": [p["id"] for p in parcelas],
            })
        elif len(parcelas) == total_parcelas:
            # Grupo completo de órfãs — cria um novo origem_id
            new_origem = str(uuid.uuid4())
            resultado["grupos_completos_restaurados"] += 1
            if not dry_run:
                await collection.update_many(
                    {"id": {"$in": [p["id"] for p in parcelas]}},
                    {"$set": {"parcela_origem_id": new_origem}},
                )
            resultado["parcelas_restauradas"] += len(parcelas)
            resultado["exemplos"].append({
                "tipo": "novo_grupo",
                "origem_id": new_origem,
                "criterio": {"fornecedor": chave[0], "documento": chave[1], "valor": chave[4], "total_parcelas": total_parcelas},
                "ids_restaurados": [p["id"] for p in parcelas],
            })
        else:
            # Grupo incompleto — não toca
            resultado["conflitos"].append({
                "criterio": {"fornecedor": chave[0], "documento": chave[1], "valor": chave[4], "total_parcelas": total_parcelas},
                "encontradas": len(parcelas),
                "esperadas": total_parcelas,
                "ids": [p["id"] for p in parcelas],
            })

    if not dry_run and resultado["parcelas_restauradas"] > 0:
        await create_audit_log(
            current_user, "recover", collection_name, None,
            f"Recuperação de vínculo de parcelas: {resultado['parcelas_restauradas']} parcelas em {resultado['grupos_completos_restaurados'] + resultado['grupos_reutilizando_origem_existente']} grupos",
            module="Administrativo",
        )

    return resultado


@financeiro_router.post("/recover-parcela-vinculos")
async def recover_parcela_vinculos(
    dry_run: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """Restaura `parcela_origem_id` em parcelas órfãs (contas a pagar e receber)
    decorrentes do bug do PUT (sessão 7). Use `?dry_run=true` para visualizar
    o que será feito; `?dry_run=false` para aplicar.

    Retorna estatísticas por coleção e exemplos dos grupos restaurados.
    """
    cp = await _recover_parcela_vinculos("contas_pagar", "fornecedor_id", dry_run, current_user)
    cr = await _recover_parcela_vinculos("contas_receber", "cliente_id", dry_run, current_user)
    return {
        "dry_run": dry_run,
        "contas_pagar": cp,
        "contas_receber": cr,
        "total_parcelas_restauradas": cp["parcelas_restauradas"] + cr["parcelas_restauradas"],
    }



# ============================================================================
# CORREÇÃO DE VALORES CORROMPIDOS (bug de ponto flutuante — sessão 27)
# ----------------------------------------------------------------------------
# Contexto: ao abrir uma conta para edição, o frontend convertia o valor para
# centavos com `valor * 100`. Por limitação do IEEE754 do JavaScript, valores
# como 1138.13 viravam "113813.00000000001" e, ao serem lidos como centavos,
# explodiam para 1.138.130.000.000,00. A causa raiz foi corrigida em
# utils/masks.js. Estes endpoints corrigem os registros JÁ gravados errados,
# reconstruindo o valor original APENAS quando é matematicamente comprovável
# (re-simulação do bug bate exatamente com o valor armazenado).
# ============================================================================

_VALOR_CORROMPIDO_THRESHOLD = 1_000_000_000.0  # R$ 1 bilhão — abaixo disso nunca é corrupção
_CAMPOS_MONETARIOS = [
    "valor", "valor_desconto", "valor_juros", "valor_multa",
    "valor_retencao", "valor_pago", "valor_recebido",
]


def _js_corrupt(real: float) -> float:
    """Reproduz EXATAMENTE o bug do JavaScript: formatCurrency((real*100).toString()).
    Python e JS usam o mesmo IEEE754 (double) e o mesmo repr de menor round-trip,
    então o resultado é idêntico ao que o frontend gravou."""
    x = real * 100.0
    s = repr(x)
    digits = "".join(ch for ch in s if ch.isdigit())[:15]
    digits = digits.lstrip("0") or "0"
    return int(digits) / 100.0


def _reconstruir_valor(valor) -> Optional[float]:
    """Tenta reconstruir o valor original a partir do valor corrompido.
    Retorna o valor correto SOMENTE se for seguro (gold-check), senão None."""
    if not isinstance(valor, (int, float)):
        return None
    if valor < _VALOR_CORROMPIDO_THRESHOLD:
        return None
    cents = round(valor * 100)
    s = str(int(cents)).rstrip("0")
    if not s:
        return None
    real = int(s) / 100.0
    if not (0 < real < 100_000_000):  # valor plausível para o ERP
        return None
    # GOLD CHECK: re-simula o bug e confere se reproduz o valor armazenado
    if abs(_js_corrupt(real) - float(valor)) < 0.01:
        return round(real, 2)
    return None


def _calcular_correcao(doc: dict) -> Optional[dict]:
    """Monta o conjunto de mudanças seguras para um documento, ou None se não
    for possível reconstruir TODOS os campos corrompidos com segurança."""
    changes: dict = {}
    tem_corrompido = False
    for campo in _CAMPOS_MONETARIOS:
        v = doc.get(campo)
        if isinstance(v, (int, float)) and v >= _VALOR_CORROMPIDO_THRESHOLD:
            tem_corrompido = True
            r = _reconstruir_valor(v)
            if r is None:
                return None  # há campo corrompido irrecuperável → revisão manual
            changes[campo] = r
    # valor_final também pode estar corrompido isoladamente
    vf = doc.get("valor_final")
    if isinstance(vf, (int, float)) and vf >= _VALOR_CORROMPIDO_THRESHOLD:
        tem_corrompido = True
    if not tem_corrompido:
        return None
    # Recalcula valor_final e saldo_restante a partir dos valores corrigidos
    valor = changes.get("valor", doc.get("valor") or 0) or 0
    desc = changes.get("valor_desconto", doc.get("valor_desconto") or 0) or 0
    juros = changes.get("valor_juros", doc.get("valor_juros") or 0) or 0
    multa = changes.get("valor_multa", doc.get("valor_multa") or 0) or 0
    ret = changes.get("valor_retencao", doc.get("valor_retencao") or 0) or 0
    changes["valor_final"] = round(valor - desc + juros + multa - ret, 2)
    pago = changes.get("valor_pago", doc.get("valor_pago") or 0) or 0
    recebido = changes.get("valor_recebido", doc.get("valor_recebido") or 0) or 0
    pago_total = pago or recebido
    changes["saldo_restante"] = round(changes["valor_final"] - pago_total, 2)
    return changes


async def _scan_valores_corrompidos(collection_name: str, nome_campo: str):
    coll = db[collection_name]
    corrigiveis = []
    manuais = []
    query = {"$or": [{c: {"$gte": _VALOR_CORROMPIDO_THRESHOLD}} for c in _CAMPOS_MONETARIOS + ["valor_final"]]}
    async for doc in coll.find(query):
        item = {
            "collection": collection_name,
            "id": doc.get("id"),
            "numero": doc.get("numero"),
            "descricao": doc.get("descricao"),
            "nome": doc.get(nome_campo),
            "documento": doc.get("documento"),
            "numero_parcela": doc.get("numero_parcela"),
            "total_parcelas": doc.get("total_parcelas"),
            "valor_atual": doc.get("valor_final") or doc.get("valor"),
        }
        changes = _calcular_correcao(doc)
        if changes is not None:
            item["valor_sugerido"] = changes.get("valor", doc.get("valor"))
            item["valor_final_sugerido"] = changes.get("valor_final")
            item["changes"] = changes
            corrigiveis.append(item)
        else:
            manuais.append(item)
    return corrigiveis, manuais


@financeiro_router.get("/valores-corrompidos")
async def listar_valores_corrompidos(current_user: dict = Depends(get_current_user)):
    """Lista contas (a pagar e a receber) com valores absurdos (bug de ponto
    flutuante), separando as que podem ser corrigidas automaticamente com
    segurança das que precisam de revisão manual."""
    cp_ok, cp_manual = await _scan_valores_corrompidos("contas_pagar", "fornecedor_nome")
    cr_ok, cr_manual = await _scan_valores_corrompidos("contas_receber", "cliente_nome")
    corrigiveis = cp_ok + cr_ok
    manuais = cp_manual + cr_manual
    return {
        "corrigiveis": corrigiveis,
        "manuais": manuais,
        "total_corrigiveis": len(corrigiveis),
        "total_manuais": len(manuais),
    }


class CorrigirValoresRequest(BaseModel):
    ids: Optional[list[str]] = None  # IDs específicos; se vazio/None, corrige TODOS os corrigíveis


@financeiro_router.post("/valores-corrompidos/corrigir")
async def corrigir_valores_corrompidos(
    payload: CorrigirValoresRequest,
    current_user: dict = Depends(get_current_user),
):
    """Aplica as correções seguras. Se `ids` for informado, corrige apenas esses
    registros; caso contrário, corrige todos os reconstruíveis com segurança."""
    cp_ok, _ = await _scan_valores_corrompidos("contas_pagar", "fornecedor_nome")
    cr_ok, _ = await _scan_valores_corrompidos("contas_receber", "cliente_nome")
    todos = cp_ok + cr_ok

    ids_filtro = set(payload.ids) if payload.ids else None
    corrigidos = []
    for item in todos:
        if ids_filtro is not None and item["id"] not in ids_filtro:
            continue
        coll = db[item["collection"]]
        await coll.update_one({"id": item["id"]}, {"$set": item["changes"]})
        corrigidos.append({
            "collection": item["collection"],
            "id": item["id"],
            "numero": item["numero"],
            "valor_antigo": item["valor_atual"],
            "valor_novo": item["changes"].get("valor_final"),
        })

    try:
        await create_audit_log(
            current_user, "corrigir_valores_corrompidos", "financeiro", "batch",
            f"{len(corrigidos)} registro(s) corrigido(s)", module="Financeiro",
        )
    except Exception:
        pass

    return {"total_corrigidos": len(corrigidos), "registros": corrigidos}
