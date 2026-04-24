"""
Conciliação Bancária — endpoints extraídos de server.py na Sessão 32 de refatoração.
Gerencia: extratos importados, conciliação de itens, e desfazer conciliação.
"""
from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db

conciliacao_router = APIRouter(prefix="/conciliacao", tags=["Conciliação"])


# ============================================================================
# LISTAGEM
# ============================================================================

@conciliacao_router.get("")
async def list_conciliacoes(current_user: dict = Depends(get_current_user)):
    """Lista todas as conciliações realizadas"""
    return await db.conciliacoes.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@conciliacao_router.get("/extratos")
async def list_all_extratos_importados(current_user: dict = Depends(get_current_user)):
    """Lista todos os itens de extrato importados ainda não conciliados"""
    return await db.extratos_bancarios.find(
        {"conciliado": {"$ne": True}},
        {"_id": 0},
    ).sort("data", -1).to_list(1000)


@conciliacao_router.delete("/extratos")
async def limpar_extratos(current_user: dict = Depends(get_current_user)):
    """Limpa todos os itens de extrato importados que não foram conciliados"""
    result = await db.extratos_bancarios.delete_many({"conciliado": {"$ne": True}})
    await create_audit_log(
        current_user,
        "delete",
        "extratos_bancarios",
        "all",
        f"Limpou {result.deleted_count} extratos não conciliados",
    )
    return {"message": f"{result.deleted_count} itens de extrato removidos", "count": result.deleted_count}


@conciliacao_router.get("/extratos/{conta_bancaria_id}")
async def list_extratos_importados(
    conta_bancaria_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Lista itens de extrato não conciliados de uma conta bancária específica"""
    return await db.extratos_bancarios.find(
        {"conta_bancaria_id": conta_bancaria_id, "conciliado": {"$ne": True}},
        {"_id": 0},
    ).sort("data", -1).to_list(1000)


# ============================================================================
# IMPORTAÇÃO DE EXTRATO (PDF)
# ============================================================================

DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2})")
VALUE_RE = re.compile(r"-?\s*\d{1,3}(?:\.\d{3})*,\d{2}")

DEBITO_KW = [
    "DEB", "DEBIT", "DÉBITO", "PGTO", "PAGAMENTO", "PAG ", "SAQUE",
    "TARIFA", "TAR ", "IOF", "JUROS", "COMPRA", "BOLETO", "TITULO",
    "PIX ENV", "PIX PAGO", "TED ENV", "DOC ENV", "ENVIAD",
    "TRANSF ENV", "RESGAT", "CARTAO", "VISA", "MASTER", "ELO",
    "IMPOSTOS", "AGUA ", "ENERGIA", "TELEFONE", "INTERNET", "GAS ",
]
CREDITO_KW = [
    "CRED", "CREDIT", "CRÉDITO", "DEP ", "DEPÓSITO", "DEPOSITO",
    "RENDIMENTO", "REMUNER", "PIX REC", "TED REC", "DOC REC",
    "RECEBID", "RECEB ", "TRANSF REC", "SALARIO", "SALÁRIO",
    "APLICAC", "REND ", "JUROS CR",
]


def _parse_date(s: str):
    s = s.strip()
    try:
        fmt = "%d/%m/%y" if len(s.split("/")[-1]) == 2 else "%d/%m/%Y"
        return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
    except Exception:
        return None


def _parse_valor(raw: str) -> float:
    return float(raw.strip().replace(" ", "").replace(".", "").replace(",", "."))


def _detectar_tipo_por_keywords(texto: str, tipo_inicial: str) -> str:
    t = texto.upper()
    for kw in DEBITO_KW:
        if kw in t:
            return "saida"
    for kw in CREDITO_KW:
        if kw in t:
            return "entrada"
    return tipo_inicial


def _selecionar_valor_e_tipo(values_raw: list, linha_texto: str):
    """
    Extrai valor da transação (NÃO o saldo corrente).
    Extratos BR típicos: DATA  DESCRIÇÃO  VALOR_TX  SALDO
    """
    if not values_raw:
        return None, "entrada"

    # 1) Valor negativo explícito → saída
    for raw in values_raw:
        if raw.strip().startswith("-"):
            return abs(_parse_valor(raw)), "saida"

    # 2) Indicador D/C/E/S logo após o valor
    for raw in values_raw:
        idx = linha_texto.find(raw.strip())
        if idx < 0:
            continue
        after = linha_texto[idx + len(raw.strip()): idx + len(raw.strip()) + 5].strip().upper()
        if after and after[0] in ("D", "S"):
            return abs(_parse_valor(raw)), "saida"
        if after and after[0] in ("C", "E"):
            return abs(_parse_valor(raw)), "entrada"

    # 3) Primeiro valor = transação
    v = abs(_parse_valor(values_raw[0]))
    tipo = _detectar_tipo_por_keywords(linha_texto, "entrada")
    return v, tipo


def _extrair_descricao(linha: str, date_str: str, value_str: str) -> str:
    d_start = linha.find(date_str)
    v_start = linha.find(value_str.strip())
    if d_start >= 0 and v_start > d_start:
        desc = linha[d_start + len(date_str): v_start].strip()
    else:
        desc = DATE_RE.sub("", VALUE_RE.sub("", linha)).strip()
    desc = re.sub(r"\s{2,}", " ", desc)
    return desc[:200]


@conciliacao_router.post("/importar-extrato")
async def importar_extrato_pdf(
    file: UploadFile = File(...),
    conta_bancaria_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Importa um extrato bancário em PDF e extrai as movimentações."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")

    conta = await db.contas_bancarias.find_one({"id": conta_bancaria_id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")

    try:
        import pdfplumber

        content = await file.read()
        extracted_items = []

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

                for table in page.extract_tables():
                    if not table:
                        continue
                    header_row = table[0] if table else []
                    header_lower = [str(h or "").lower() for h in header_row]

                    def col_idx(keywords):
                        for kw in keywords:
                            for i, h in enumerate(header_lower):
                                if kw in h:
                                    return i
                        return -1

                    col_debito = col_idx(["déb", "deb", "saída", "saida"])
                    col_credito = col_idx(["créd", "cred", "entr", "entrada"])
                    col_valor = col_idx(["valor", "movim", "quantia"])
                    col_saldo = col_idx(["saldo", "balance"])

                    for row in table:
                        if not row:
                            continue
                        row_cells = [str(c or "").strip() for c in row]
                        row_text = " ".join(row_cells)

                        date_match = DATE_RE.search(row_text)
                        if not date_match:
                            continue
                        iso_date = _parse_date(date_match.group(1))
                        if not iso_date:
                            continue

                        valor_final = None
                        tipo_final = "entrada"

                        if col_debito >= 0 and col_credito >= 0:
                            v_deb = row_cells[col_debito] if col_debito < len(row_cells) else ""
                            v_cred = row_cells[col_credito] if col_credito < len(row_cells) else ""
                            if v_deb and VALUE_RE.search(v_deb):
                                valor_final = abs(_parse_valor(VALUE_RE.findall(v_deb)[0]))
                                tipo_final = "saida"
                            elif v_cred and VALUE_RE.search(v_cred):
                                valor_final = abs(_parse_valor(VALUE_RE.findall(v_cred)[0]))
                                tipo_final = "entrada"

                        if valor_final is None and col_valor >= 0:
                            if col_valor < len(row_cells):
                                cell_v = row_cells[col_valor]
                                matches_v = VALUE_RE.findall(cell_v)
                                if matches_v:
                                    valor_final, tipo_final = _selecionar_valor_e_tipo(matches_v, cell_v)

                        if valor_final is None:
                            all_vals = VALUE_RE.findall(row_text)
                            vals_sem_saldo = all_vals[:-1] if len(all_vals) > 1 else all_vals
                            if not vals_sem_saldo:
                                continue
                            valor_final, tipo_final = _selecionar_valor_e_tipo(vals_sem_saldo, row_text)

                        if valor_final is None or valor_final == 0:
                            continue

                        tipo_final = _detectar_tipo_por_keywords(row_text, tipo_final)

                        saldo_cell = row_cells[col_saldo] if col_saldo >= 0 and col_saldo < len(row_cells) else ""
                        descricao = row_text
                        descricao = DATE_RE.sub("", descricao)
                        if saldo_cell:
                            descricao = descricao.replace(saldo_cell, "")
                        descricao = VALUE_RE.sub("", descricao).strip()
                        descricao = re.sub(r"\s{2,}", " ", descricao)[:200]
                        if len(descricao) < 2:
                            continue

                        extracted_items.append({
                            "id": str(uuid.uuid4()),
                            "conta_bancaria_id": conta_bancaria_id,
                            "data": iso_date,
                            "descricao": descricao,
                            "valor": valor_final,
                            "tipo": tipo_final,
                            "conciliado": False,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })

        # Fallback: extração linha por linha
        if not extracted_items and full_text:
            for line in full_text.split("\n"):
                line = line.strip()
                if len(line) < 10:
                    continue
                date_match = DATE_RE.search(line)
                if not date_match:
                    continue
                iso_date = _parse_date(date_match.group(1))
                if not iso_date:
                    continue
                all_vals = VALUE_RE.findall(line)
                if not all_vals:
                    continue
                vals_sem_saldo = all_vals[:-1] if len(all_vals) > 1 else all_vals
                valor_final, tipo_final = _selecionar_valor_e_tipo(vals_sem_saldo, line)
                if valor_final is None or valor_final == 0:
                    continue
                tipo_final = _detectar_tipo_por_keywords(line, tipo_final)
                descricao = _extrair_descricao(line, date_match.group(1), vals_sem_saldo[0])
                if len(descricao) < 2:
                    continue
                extracted_items.append({
                    "id": str(uuid.uuid4()),
                    "conta_bancaria_id": conta_bancaria_id,
                    "data": iso_date,
                    "descricao": descricao,
                    "valor": valor_final,
                    "tipo": tipo_final,
                    "conciliado": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

        # Remover duplicatas
        unique_items, seen = [], set()
        for item in extracted_items:
            key = f"{item['data']}|{item['valor']:.2f}|{item['descricao'][:80]}"
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        if unique_items:
            await db.extratos_bancarios.insert_many(unique_items)

        await create_audit_log(
            user=current_user,
            action="importar",
            entity_type="extrato_bancario",
            entity_id=conta_bancaria_id,
            entity_name=f"{conta.get('banco', '')} - {file.filename}",
            details=f"{len(unique_items)} movimentações importadas",
            module="Financeiro",
        )
        return {"message": "Extrato importado com sucesso", "count": len(unique_items)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")


# ============================================================================
# CONCILIAR / DESFAZER
# ============================================================================

@conciliacao_router.post("/conciliar")
async def conciliar_itens(
    extrato_id: str = Body(...),
    conta_id: str = Body(...),
    conta_tipo: str = Body(...),  # "pagar" ou "receber"
    current_user: dict = Depends(get_current_user),
):
    """Concilia um item do extrato com uma conta do sistema."""
    extrato = await db.extratos_bancarios.find_one({"id": extrato_id}, {"_id": 0})
    if not extrato:
        raise HTTPException(status_code=404, detail="Item do extrato não encontrado")
    if extrato.get("conciliado"):
        raise HTTPException(status_code=400, detail="Item do extrato já foi conciliado")

    collection = db.contas_pagar if conta_tipo == "pagar" else db.contas_receber
    conta = await collection.find_one({"id": conta_id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    if conta.get("conciliado"):
        raise HTTPException(status_code=400, detail="Esta conta já foi conciliada")

    conciliacao_id = str(uuid.uuid4())
    _now_iso = datetime.now(timezone.utc).isoformat()
    conciliacao_doc = {
        "id": conciliacao_id,
        "extrato_id": extrato_id,
        "extrato_ids": [extrato_id],
        "extrato_descricao": extrato.get("descricao", ""),
        "extratos_descricao": [extrato.get("descricao", "")],
        "conta_id": conta_id,
        "conta_tipo": conta_tipo,
        "conta_descricao": conta.get("descricao", conta.get("favorecido", "")),
        "contas_ids": [conta_id],
        "contas_tipos": [conta_tipo],
        "contas_descricao": [f"[{conta_tipo.capitalize()}] {conta.get('descricao', conta.get('favorecido', ''))}"],
        "valor": extrato.get("valor", 0),
        "valor_extratos": extrato.get("valor", 0),
        "valor_contas": conta.get("valor_final") or conta.get("valor", 0),
        "diferenca": abs((extrato.get("valor", 0) or 0) - ((conta.get("valor_final") or conta.get("valor", 0)) or 0)),
        "data_extrato": extrato.get("data"),
        "data_conciliacao": _now_iso[:10],
        "created_by": current_user["id"],
        "created_at": _now_iso,
    }
    await db.conciliacoes.insert_one(conciliacao_doc)

    await db.extratos_bancarios.update_one(
        {"id": extrato_id},
        {"$set": {"conciliado": True, "conciliacao_id": conciliacao_id}},
    )
    await collection.update_one(
        {"id": conta_id},
        {"$set": {"conciliado": True, "conciliacao_id": conciliacao_id}},
    )

    await create_audit_log(
        user=current_user,
        action="conciliar",
        entity_type="conciliacao",
        entity_id=conciliacao_id,
        entity_name=f"Extrato: {extrato.get('descricao', '')[:30]} <-> Conta: {conta.get('descricao', '')[:30]}",
        module="Financeiro",
    )
    return {"message": "Conciliação realizada com sucesso", "id": conciliacao_id}


@conciliacao_router.delete("/{conciliacao_id}")
async def desfazer_conciliacao(
    conciliacao_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Desfaz uma conciliação."""
    conciliacao = await db.conciliacoes.find_one({"id": conciliacao_id}, {"_id": 0})
    if not conciliacao:
        raise HTTPException(status_code=404, detail="Conciliação não encontrada")

    # Legado: extrato_id único OU nova estrutura: extrato_ids: []
    extrato_ids = conciliacao.get("extrato_ids") or ([conciliacao["extrato_id"]] if conciliacao.get("extrato_id") else [])
    if extrato_ids:
        await db.extratos_bancarios.update_many(
            {"id": {"$in": extrato_ids}},
            {"$set": {"conciliado": False}, "$unset": {"conciliacao_id": ""}},
        )

    # Contas vinculadas (legado: conta_id+conta_tipo / novo: contas: [{id,tipo}])
    contas_vinc = conciliacao.get("contas") or ([{"id": conciliacao["conta_id"], "tipo": conciliacao["conta_tipo"]}] if conciliacao.get("conta_id") else [])
    for c in contas_vinc:
        coll = db.contas_pagar if c.get("tipo") == "pagar" else db.contas_receber
        await coll.update_one(
            {"id": c["id"]},
            {"$set": {"conciliado": False}, "$unset": {"conciliacao_id": ""}},
        )

    await db.conciliacoes.delete_one({"id": conciliacao_id})

    await create_audit_log(
        user=current_user,
        action="desfazer",
        entity_type="conciliacao",
        entity_id=conciliacao_id,
        entity_name="Conciliação desfeita",
        module="Financeiro",
    )
    return {"message": "Conciliação desfeita com sucesso"}


# ============================================================================
# MULTI-CONCILIAÇÃO (N extratos ↔ M contas)
# ============================================================================

@conciliacao_router.post("/conciliar-lote")
async def conciliar_lote(
    extrato_ids: list = Body(..., description="Lista de IDs de extratos bancários"),
    contas: list = Body(..., description="Lista de {id, tipo: 'pagar'|'receber'}"),
    observacao: str = Body("", description="Observação opcional"),
    tolerancia: float = Body(0.10, description="Tolerância de diferença absoluta entre totais"),
    current_user: dict = Depends(get_current_user),
):
    """Concilia N extratos com M contas do sistema em uma única operação.
    Valida que a soma dos valores bate (com tolerância configurável)."""
    if not extrato_ids or not contas:
        raise HTTPException(status_code=400, detail="Selecione ao menos 1 extrato e 1 conta")

    # Carrega extratos
    extratos = await db.extratos_bancarios.find(
        {"id": {"$in": extrato_ids}}, {"_id": 0}
    ).to_list(100)
    if len(extratos) != len(extrato_ids):
        raise HTTPException(status_code=404, detail="Um ou mais extratos não foram encontrados")
    if any(e.get("conciliado") for e in extratos):
        raise HTTPException(status_code=400, detail="Um ou mais extratos já foram conciliados")

    # Carrega contas
    contas_carregadas = []
    for c in contas:
        cid = c.get("id")
        ctipo = c.get("tipo")
        if ctipo not in ("pagar", "receber"):
            raise HTTPException(status_code=400, detail=f"Tipo inválido: {ctipo}")
        coll = db.contas_pagar if ctipo == "pagar" else db.contas_receber
        doc = await coll.find_one({"id": cid}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Conta {ctipo} {cid} não encontrada")
        if doc.get("conciliado"):
            raise HTTPException(status_code=400, detail=f"Conta {ctipo} {cid} já foi conciliada")
        doc["_tipo"] = ctipo
        contas_carregadas.append(doc)

    total_extratos = sum(e.get("valor", 0) for e in extratos)
    total_contas = sum(
        c.get("valor_final") or c.get("valor", 0) for c in contas_carregadas
    )
    diferenca = abs(total_extratos - total_contas)
    if diferenca > tolerancia:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Os totais não batem: extratos R$ {total_extratos:,.2f} vs contas R$ {total_contas:,.2f} "
                f"(diferença R$ {diferenca:,.2f})."
            ),
        )

    conciliacao_id = str(uuid.uuid4())
    conciliacao_doc = {
        "id": conciliacao_id,
        "tipo": "lote",
        "extrato_ids": extrato_ids,
        "extratos_descricao": [e.get("descricao", "") for e in extratos],
        "contas": [{"id": c["id"], "tipo": c["_tipo"]} for c in contas_carregadas],
        "contas_descricao": [c.get("descricao", c.get("favorecido", "")) for c in contas_carregadas],
        "valor_extratos": total_extratos,
        "valor_contas": total_contas,
        "diferenca": diferenca,
        "observacao": observacao,
        "data_conciliacao": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_by": current_user["id"],
        "created_by_name": current_user.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.conciliacoes.insert_one(conciliacao_doc)

    await db.extratos_bancarios.update_many(
        {"id": {"$in": extrato_ids}},
        {"$set": {"conciliado": True, "conciliacao_id": conciliacao_id}},
    )
    for c in contas_carregadas:
        coll = db.contas_pagar if c["_tipo"] == "pagar" else db.contas_receber
        await coll.update_one(
            {"id": c["id"]},
            {"$set": {"conciliado": True, "conciliacao_id": conciliacao_id}},
        )

    await create_audit_log(
        user=current_user,
        action="conciliar",
        entity_type="conciliacao",
        entity_id=conciliacao_id,
        entity_name=f"Lote: {len(extrato_ids)} extrato(s) ↔ {len(contas_carregadas)} conta(s)",
        details=f"Total R$ {total_extratos:,.2f}",
        module="Financeiro",
    )
    return {
        "message": "Conciliação em lote realizada com sucesso",
        "id": conciliacao_id,
        "valor_extratos": total_extratos,
        "valor_contas": total_contas,
        "diferenca": diferenca,
    }


# ============================================================================
# EXPORTAÇÃO PDF
# ============================================================================

@conciliacao_router.get("/export-pdf")
async def export_conciliacao_pdf(
    conta_bancaria_id: str = None,
    data_inicio: str = None,
    data_fim: str = None,
    completo: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Exporta relatório de conciliação em PDF.
    - completo=False: apenas conciliações realizadas
    - completo=True: inclui extratos e contas pendentes"""
    from fastapi.responses import Response
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    # Busca conta bancária (se informada)
    conta_banco = None
    if conta_bancaria_id:
        conta_banco = await db.contas_bancarias.find_one({"id": conta_bancaria_id}, {"_id": 0})

    # Filtros de conciliações
    conc_filter: dict = {}
    conta_filter_or = None
    if conta_bancaria_id:
        # Busca conciliações que usaram extratos daquela conta
        extratos_conta = await db.extratos_bancarios.find(
            {"conta_bancaria_id": conta_bancaria_id},
            {"_id": 0, "id": 1},
        ).to_list(5000)
        ids_ext_conta = [e["id"] for e in extratos_conta]
        conta_filter_or = [
            {"extrato_id": {"$in": ids_ext_conta}},
            {"extrato_ids": {"$in": ids_ext_conta}},
        ]

    # Filtro de período: considera data_conciliacao (nova) OU created_at (legado).
    # Conciliações antigas do endpoint /conciliar singular não têm data_conciliacao.
    date_filter_or = None
    if data_inicio and data_fim:
        date_filter_or = [
            {"data_conciliacao": {"$gte": data_inicio, "$lte": data_fim}},
            {
                "data_conciliacao": {"$exists": False},
                "created_at": {"$gte": data_inicio, "$lte": data_fim + "T23:59:59"},
            },
        ]

    # Combina filtros via $and para permitir múltiplos $or
    and_clauses = []
    if conta_filter_or:
        and_clauses.append({"$or": conta_filter_or})
    if date_filter_or:
        and_clauses.append({"$or": date_filter_or})
    if and_clauses:
        conc_filter["$and"] = and_clauses

    conciliacoes = await db.conciliacoes.find(conc_filter, {"_id": 0}).sort("created_at", -1).to_list(2000)

    # Pendentes (se modo completo)
    extratos_pend = []
    contas_pend_pagar = []
    contas_pend_receber = []
    if completo:
        ext_filter = {"conciliado": {"$ne": True}}
        if conta_bancaria_id:
            ext_filter["conta_bancaria_id"] = conta_bancaria_id
        extratos_pend = await db.extratos_bancarios.find(ext_filter, {"_id": 0}).sort("data", 1).to_list(2000)
        contas_pend_pagar = await db.contas_pagar.find(
            {"conciliado": {"$ne": True}, "status": "em_aberto"}, {"_id": 0}
        ).sort("data_vencimento", 1).to_list(2000)
        contas_pend_receber = await db.contas_receber.find(
            {"conciliado": {"$ne": True}, "status": "em_aberto"}, {"_id": 0}
        ).sort("data_vencimento", 1).to_list(2000)

    # Construir PDF
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=14, alignment=1, textColor=colors.HexColor("#C62828"), spaceAfter=6)
    sub_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=9, alignment=1, textColor=colors.grey, spaceAfter=12)
    section_style = ParagraphStyle("Sec", parent=styles["Heading2"], fontSize=11, textColor=colors.HexColor("#C62828"), spaceBefore=12, spaceAfter=6)
    normal_style = ParagraphStyle("N", parent=styles["Normal"], fontSize=8)

    def _fmt_date(s):
        if not s:
            return "—"
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return s

    def _fmt_brl(v):
        try:
            return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "R$ 0,00"

    elements = [Paragraph("CRA Construtora", title_style)]
    banco_info = ""
    if conta_banco:
        banco_info = f"Banco: {conta_banco.get('banco', '')} · Agência {conta_banco.get('agencia', '')} · Conta {conta_banco.get('conta', '')}"
    periodo_info = ""
    if data_inicio and data_fim:
        periodo_info = f" · Período: {_fmt_date(data_inicio)} a {_fmt_date(data_fim)}"
    elements.append(Paragraph("Relatório de Conciliação Bancária", section_style))
    if banco_info or periodo_info:
        elements.append(Paragraph(banco_info + periodo_info, sub_style))
    elements.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))

    # Totais
    total_conc = sum(
        c.get("valor_extratos") or c.get("valor", 0) for c in conciliacoes
    )
    total_pend_ext = sum(e.get("valor", 0) for e in extratos_pend)
    total_pend_pagar = sum((c.get("valor_final") or c.get("valor", 0)) for c in contas_pend_pagar)
    total_pend_receber = sum((c.get("valor_final") or c.get("valor", 0)) for c in contas_pend_receber)

    resumo_data = [
        ["Conciliações Realizadas", str(len(conciliacoes)), _fmt_brl(total_conc)],
    ]
    if completo:
        resumo_data += [
            ["Extratos Pendentes", str(len(extratos_pend)), _fmt_brl(total_pend_ext)],
            ["Contas a Pagar Pendentes", str(len(contas_pend_pagar)), _fmt_brl(total_pend_pagar)],
            ["Contas a Receber Pendentes", str(len(contas_pend_receber)), _fmt_brl(total_pend_receber)],
        ]
    resumo_tbl = Table([["Indicador", "Qtd.", "Valor"]] + resumo_data, colWidths=[10 * cm, 3 * cm, 6 * cm])
    resumo_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C62828")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(resumo_tbl)

    # Detalhe conciliações
    elements.append(Paragraph("Conciliações Realizadas", section_style))
    if conciliacoes:
        # Pré-carrega tipos de todos os extratos envolvidos (evita N+1)
        all_ext_ids = set()
        for c in conciliacoes:
            for eid in (c.get("extrato_ids") or ([c.get("extrato_id")] if c.get("extrato_id") else [])):
                if eid:
                    all_ext_ids.add(eid)
        tipo_por_ext = {}
        if all_ext_ids:
            rows_ext = await db.extratos_bancarios.find(
                {"id": {"$in": list(all_ext_ids)}},
                {"_id": 0, "id": 1, "tipo": 1},
            ).to_list(5000)
            tipo_por_ext = {r["id"]: (r.get("tipo") or "").lower() for r in rows_ext}

        elements.append(Paragraph(
            "<font color='#2E7D32'>Verde</font> = Entrada (+) &nbsp;&nbsp; "
            "<font color='#C62828'>Vermelho</font> = Saída (-) &nbsp;&nbsp; "
            "<font color='#616161'>Cinza</font> = Misto",
            normal_style,
        ))
        data_tbl = [["Data", "Tipo", "Extrato(s)", "Conta(s) do Sistema", "Valor Extrato", "Valor Conta", "Diferença"]]
        row_styles = []
        for idx, c in enumerate(conciliacoes, start=1):
            data_c = c.get("data_conciliacao") or (c.get("created_at") or "")[:10]
            ext_desc = c.get("extratos_descricao") or ([c.get("extrato_descricao", "")] if c.get("extrato_descricao") else [])
            cont_desc = c.get("contas_descricao") or ([c.get("conta_descricao", "")] if c.get("conta_descricao") else [])
            v_ext = c.get("valor_extratos") if c.get("valor_extratos") is not None else c.get("valor", 0)
            v_cont = c.get("valor_contas") if c.get("valor_contas") is not None else c.get("valor", 0)
            diff = c.get("diferenca", 0) or 0

            # Deriva tipo a partir dos extratos envolvidos
            ext_ids = c.get("extrato_ids") or ([c.get("extrato_id")] if c.get("extrato_id") else [])
            tipos = {tipo_por_ext.get(eid, "") for eid in ext_ids if eid}
            tipos.discard("")
            if tipos == {"entrada"}:
                tipo_label, sinal, cor = "ENTRADA", "+", colors.HexColor("#2E7D32")
            elif tipos == {"saida"}:
                tipo_label, sinal, cor = "SAÍDA", "-", colors.HexColor("#C62828")
            else:
                tipo_label, sinal, cor = "MISTO", "", colors.HexColor("#616161")

            data_tbl.append([
                _fmt_date(data_c),
                tipo_label,
                Paragraph("<br/>".join(ext_desc)[:200], normal_style),
                Paragraph("<br/>".join(cont_desc)[:200], normal_style),
                f"{sinal} {_fmt_brl(v_ext)}" if sinal else _fmt_brl(v_ext),
                f"{sinal} {_fmt_brl(v_cont)}" if sinal else _fmt_brl(v_cont),
                _fmt_brl(diff),
            ])
            row_styles.append(("TEXTCOLOR", (1, idx), (1, idx), cor))
            row_styles.append(("FONTNAME", (1, idx), (1, idx), "Helvetica-Bold"))
            row_styles.append(("TEXTCOLOR", (4, idx), (5, idx), cor))
            row_styles.append(("FONTNAME", (4, idx), (5, idx), "Helvetica-Bold"))
        t = Table(data_tbl, colWidths=[2 * cm, 2 * cm, 6.5 * cm, 6.5 * cm, 2.7 * cm, 2.7 * cm, 2 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C62828")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            *row_styles,
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("<i>Nenhuma conciliação no período selecionado.</i>", normal_style))

    if completo:
        if extratos_pend:
            elements.append(Paragraph("Extratos Pendentes de Conciliação", section_style))
            elements.append(Paragraph(
                "<font color='#2E7D32'>Verde</font> = Entrada &nbsp;&nbsp; "
                "<font color='#C62828'>Vermelho</font> = Saída",
                normal_style,
            ))
            rows = [["Data", "Descrição", "Tipo", "Valor"]]
            row_styles = []
            for idx, e in enumerate(extratos_pend[:200], start=1):
                is_entrada = (e.get("tipo", "") or "").lower() == "entrada"
                tipo_label = "ENTRADA" if is_entrada else "SAÍDA"
                sinal = "+" if is_entrada else "-"
                cor = colors.HexColor("#2E7D32") if is_entrada else colors.HexColor("#C62828")
                rows.append([
                    _fmt_date(e.get("data")),
                    Paragraph((e.get("descricao", "") or "")[:200], normal_style),
                    tipo_label,
                    f"{sinal} {_fmt_brl(e.get('valor', 0))}",
                ])
                # Cor do tipo e do valor
                row_styles.append(("TEXTCOLOR", (2, idx), (3, idx), cor))
                row_styles.append(("FONTNAME", (2, idx), (3, idx), "Helvetica-Bold"))
            t = Table(rows, colWidths=[2 * cm, 15 * cm, 2.5 * cm, 3 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C62828")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                *row_styles,
            ]))
            elements.append(t)

        if contas_pend_pagar:
            elements.append(Paragraph("Contas a Pagar Pendentes", section_style))
            elements.append(Paragraph(
                "<font color='#C62828'>Valor em vermelho</font> = saída financeira",
                normal_style,
            ))
            rows = [["Vencimento", "Fornecedor", "Descrição", "Valor"]]
            n_rows = 0
            for c in contas_pend_pagar[:200]:
                rows.append([
                    _fmt_date(c.get("data_vencimento")),
                    Paragraph((c.get("fornecedor_nome") or "")[:80], normal_style),
                    Paragraph((c.get("descricao") or "")[:200], normal_style),
                    f"- {_fmt_brl(c.get('valor_final') or c.get('valor', 0))}",
                ])
                n_rows += 1
            t = Table(rows, colWidths=[2.5 * cm, 5 * cm, 11 * cm, 3 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C62828")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("TEXTCOLOR", (3, 1), (3, n_rows), colors.HexColor("#C62828")),
                ("FONTNAME", (3, 1), (3, n_rows), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(t)

        if contas_pend_receber:
            elements.append(Paragraph("Contas a Receber Pendentes", section_style))
            elements.append(Paragraph(
                "<font color='#2E7D32'>Valor em verde</font> = entrada financeira",
                normal_style,
            ))
            rows = [["Vencimento", "Cliente", "Descrição", "Valor"]]
            n_rows = 0
            for c in contas_pend_receber[:200]:
                rows.append([
                    _fmt_date(c.get("data_vencimento")),
                    Paragraph((c.get("cliente_nome") or "")[:80], normal_style),
                    Paragraph((c.get("descricao") or "")[:200], normal_style),
                    f"+ {_fmt_brl(c.get('valor_final') or c.get('valor', 0))}",
                ])
                n_rows += 1
            t = Table(rows, colWidths=[2.5 * cm, 5 * cm, 11 * cm, 3 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C62828")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("TEXTCOLOR", (3, 1), (3, n_rows), colors.HexColor("#2E7D32")),
                ("FONTNAME", (3, 1), (3, n_rows), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(t)

    doc.build(elements)
    buf.seek(0)

    filename = f"Conciliacao_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
