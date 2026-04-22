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
    conciliacao_doc = {
        "id": conciliacao_id,
        "extrato_id": extrato_id,
        "extrato_descricao": extrato.get("descricao", ""),
        "conta_id": conta_id,
        "conta_tipo": conta_tipo,
        "conta_descricao": conta.get("descricao", conta.get("favorecido", "")),
        "valor": extrato.get("valor", 0),
        "data_extrato": extrato.get("data"),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
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

    await db.extratos_bancarios.update_one(
        {"id": conciliacao["extrato_id"]},
        {"$set": {"conciliado": False}, "$unset": {"conciliacao_id": ""}},
    )
    collection = db.contas_pagar if conciliacao["conta_tipo"] == "pagar" else db.contas_receber
    await collection.update_one(
        {"id": conciliacao["conta_id"]},
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
