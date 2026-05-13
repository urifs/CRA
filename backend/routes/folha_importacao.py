"""Importação de Folha de Pagamento via PDF.

Fluxo:
1. RH faz upload do PDF da folha completa (várias páginas com 1 holerite/funcionário/página).
2. Sistema usa Gemini Flash (emergentintegrations) para OCR/extração estruturada por página.
3. Match fuzzy com `funcionarios_collection` por nome.
4. Salva folha_importada (status=em_revisao) e cria 1 PDF separado por funcionário no storage.
5. RH envia ao Financeiro como `cheio` (1 conta) ou `individual` (N contas) -> cria solicitacao_folha.
6. Financeiro aceita escolhendo plano de contas + data vencimento -> cria contas a pagar com PDFs anexados.
"""
from __future__ import annotations

import os
import io
import json
import uuid
import logging
import unicodedata
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from PyPDF2 import PdfReader, PdfWriter
from rapidfuzz import process, fuzz

from utils.storage import put_object, get_object, APP_NAME

logger = logging.getLogger(__name__)

# ---------- DB ----------
_mongo_url = os.environ["MONGO_URL"]
_db_name = os.environ["DB_NAME"]
_client = AsyncIOMotorClient(_mongo_url)
db = _client[_db_name]
funcionarios_collection = db["funcionarios"]
folhas_importadas_collection = db["folhas_importadas"]
solicitacoes_folha_collection = db["solicitacoes_folha_financeiro"]
contas_pagar_collection = db["contas_pagar"]
plano_contas_collection = db["plano_contas"]

folha_router = APIRouter(prefix="/folha-pagamento", tags=["folha-pagamento"])


# =================== Notificações (tasks inbox) ===================
async def _criar_task(target_system: str, title: str, message: str,
                      priority: str = "media", origem: dict | None = None):
    """Insere notificação na inbox (sino) de um sistema. Reaproveita coleção 'tasks'."""
    try:
        doc = {
            "id": str(uuid.uuid4()),
            "target_system": target_system,
            "priority": priority,
            "title": title,
            "message": message,
            "attachments": [],
            "created_by_id": "system",
            "created_by_name": "Sistema (Folha)",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "read_at": None,
            "read_by": None,
            "origem": origem or {},
        }
        await db["tasks"].insert_one(doc)
    except Exception as e:
        logger.warning(f"Falha ao criar task '{title}': {e}")


# =================== Helpers ===================
def _normalize(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper().strip()


async def _all_funcionarios_norm() -> list[dict]:
    out = []
    async for f in funcionarios_collection.find(
        {}, {"_id": 0, "id": 1, "nome": 1, "cpf": 1, "status": 1}
    ):
        out.append({**f, "_norm": _normalize(f.get("nome", ""))})
    return out


def _fuzzy_pick(nome_pdf: str, candidatos: list[dict]) -> dict:
    """Faz match com rapidfuzz. Retorna dict {match_id, nome_db, score, status}.
    status: 'high' (>=92), 'medium' (70..91), 'low' (<70)."""
    if not candidatos:
        return {"match_id": None, "nome_db": None, "score": 0, "status": "low"}
    nome_norm = _normalize(nome_pdf)
    choices = {c["id"]: c["_norm"] for c in candidatos if c.get("_norm")}
    if not choices:
        return {"match_id": None, "nome_db": None, "score": 0, "status": "low"}
    melhor = process.extractOne(nome_norm, choices, scorer=fuzz.token_sort_ratio)
    if not melhor:
        return {"match_id": None, "nome_db": None, "score": 0, "status": "low"}
    nome_db_norm, score, fid = melhor
    nome_db = next((c.get("nome") for c in candidatos if c["id"] == fid), None)
    if score >= 92:
        st = "high"
    elif score >= 70:
        st = "medium"
    else:
        st = "low"
    return {
        "match_id": fid if score >= 70 else None,
        "nome_db": nome_db,
        "score": int(score),
        "status": st,
    }


async def _ocr_folha_pdf(pdf_bytes: bytes) -> dict:
    """Chama Gemini Flash para extrair estrutura da folha. Retorna dict com:
    {empresa, cnpj, mes_competencia, ano_competencia, funcionarios:[{
        nome, codigo, funcao, valor_liquido, total_vencimentos, total_descontos,
        salario_base, base_inss, base_fgts, fgts_mes, base_irrf, paginas_indices
    }], total_geral}.
    """
    from emergentintegrations.llm.chat import (
        LlmChat, UserMessage, FileContentWithMimeType,
    )

    # Salva temporariamente para entregar ao SDK
    tmp_dir = "/tmp/folha_ocr"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = f"{tmp_dir}/{uuid.uuid4().hex}.pdf"
    with open(tmp_path, "wb") as fh:
        fh.write(pdf_bytes)
    try:
        chat = LlmChat(
            api_key=os.environ["EMERGENT_LLM_KEY"],
            session_id=f"folha-ocr-{uuid.uuid4().hex[:8]}",
            system_message=(
                "Você é um extrator estruturado de holerites/folhas de pagamento brasileiras. "
                "Devolva EXCLUSIVAMENTE JSON válido (sem markdown, sem comentários)."
            ),
        ).with_model("gemini", "gemini-2.5-flash")
        prompt = (
            "Analise este PDF de folha de pagamento (pode ter várias páginas, normalmente 1 holerite "
            "por funcionário por página, podendo haver duplicatas via empresa/funcionário). Extraia:\n\n"
            "{\n"
            '  "empresa": "razao social",\n'
            '  "cnpj": "...",\n'
            '  "mes_competencia": 1-12,\n'
            '  "ano_competencia": 2026,\n'
            '  "funcionarios": [\n'
            "    {\n"
            '      "nome": "NOME COMPLETO EXATO COMO NO PDF",\n'
            '      "codigo": "código do funcionário no sistema da folha (se houver)",\n'
            '      "funcao": "cargo/função",\n'
            '      "departamento": "...",\n'
            '      "admissao": "YYYY-MM-DD se possível",\n'
            '      "valor_liquido": 1234.56,\n'
            '      "total_vencimentos": 1234.56,\n'
            '      "total_descontos": 1234.56,\n'
            '      "salario_base": 1234.56,\n'
            '      "base_inss": 1234.56,\n'
            '      "base_fgts": 1234.56,\n'
            '      "fgts_mes": 1234.56,\n'
            '      "base_irrf": 1234.56,\n'
            '      "vencimentos_detalhados": [{"codigo":"","descricao":"DIAS NORMAIS","referencia":"30","valor":2000.00}],\n'
            '      "descontos_detalhados": [{"codigo":"","descricao":"INSS","referencia":"8.80","valor":150.00}],\n'
            '      "paginas": [1, 2]  // índices 1-based das páginas onde este holerite aparece\n'
            "    }\n"
            "  ],\n"
            '  "total_geral_liquido": 1234.56\n'
            "}\n\n"
            "IMPORTANTE:\n"
            "- DEDUPLICAR funcionários (mesmo nome aparece 2x se for duplicata empresa/funcionário) — agrupe páginas no mesmo registro.\n"
            "- Use ponto decimal (não vírgula) e números puros (sem 'R$').\n"
            "- Se um campo não estiver presente, use 0 ou string vazia.\n"
            "- 'paginas' deve listar TODAS as páginas (1-based) em que aquele holerite específico aparece.\n"
            "- Calcule total_geral_liquido SOMANDO os valor_liquido de cada funcionário ÚNICO (após deduplicação)."
        )
        fc = FileContentWithMimeType(file_path=tmp_path, mime_type="application/pdf")
        msg = UserMessage(text=prompt, file_contents=[fc])
        raw = await chat.send_message(msg)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    raw_str = raw if isinstance(raw, str) else str(raw)
    # Limpa markdown wrappers que o LLM possa devolver
    s = raw_str.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s.rsplit("```", 1)[0]
        # remove "json\n" inicial
        s = s.lstrip("json").lstrip("\n").strip()
    try:
        return json.loads(s)
    except Exception as e:
        logger.error(f"OCR JSON inválido: {e}; raw[:500]={s[:500]}")
        raise HTTPException(
            status_code=500,
            detail="Não consegui interpretar a folha. PDF pode estar fora do padrão esperado.",
        )


def _split_pdf_pages(pdf_bytes: bytes, paginas_1based: list[int]) -> bytes:
    """Extrai um subconjunto de páginas do PDF, preservando-as num novo PDF."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    total = len(reader.pages)
    for p in paginas_1based:
        idx = p - 1
        if 0 <= idx < total:
            writer.add_page(reader.pages[idx])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


# =================== Pydantic ===================
class ResolverMatchPayload(BaseModel):
    funcionarios: list[dict] = Field(
        default_factory=list,
        description="Lista de {nome_pdf, funcionario_id} para forçar/ajustar mapping",
    )


class EnviarFinanceiroPayload(BaseModel):
    modo: str = Field(..., pattern="^(cheio|individual)$")
    observacao: Optional[str] = None


class AceitarSolicitacaoPayload(BaseModel):
    plano_contas_id: str
    data_vencimento: str  # YYYY-MM-DD
    conta_bancaria_id: Optional[str] = None
    forma_pagamento: Optional[str] = None
    observacao: Optional[str] = None


# =================== Background Processing ===================
async def _processar_folha_background(folha_id: str, pdf_bytes: bytes, filename: str):
    """Roda em asyncio.create_task — atualiza folha conforme progresso.
    Etapas:
      1. validando (10%)  -> PDF aberto
      2. ocr (30%)        -> pedindo extração ao Gemini
      3. matching (75%)   -> fuzzy match com cadastro
      4. dividindo (90%)  -> split + upload dos holerites
      5. concluida (100%) -> status='em_revisao'
    Em qualquer falha, marca status='erro' com mensagem.
    """
    async def _atualiza(progresso: int, etapa: str, **extra):
        update = {"progresso": progresso, "etapa": etapa, **extra}
        await folhas_importadas_collection.update_one(
            {"id": folha_id}, {"$set": update}
        )

    try:
        # 1. Validação básica (PDF + storage do master)
        await _atualiza(5, "validando")
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            total_paginas = len(reader.pages)
        except Exception as e:
            await _atualiza(100, "erro", status="erro", erro=f"PDF inválido: {e}")
            return
        if total_paginas == 0:
            await _atualiza(100, "erro", status="erro", erro="PDF sem páginas")
            return

        master_path = f"{APP_NAME}/folha-importada/{folha_id}/master.pdf"
        put_object(master_path, pdf_bytes, "application/pdf")
        await _atualiza(15, "ocr_iniciando", master_pdf_path=master_path, total_paginas=total_paginas)

        # 2. OCR via Gemini (a parte mais demorada — 30-60s)
        try:
            parsed = await _ocr_folha_pdf(pdf_bytes)
        except HTTPException as e:
            await _atualiza(100, "erro", status="erro", erro=e.detail)
            return
        except Exception as e:
            await _atualiza(100, "erro", status="erro", erro=f"OCR falhou: {e}")
            return

        funcionarios_pdf = parsed.get("funcionarios") or []
        if not funcionarios_pdf:
            await _atualiza(100, "erro", status="erro", erro="Nenhum holerite identificado")
            return

        await _atualiza(60, "matching")

        # 3. Match fuzzy + split por funcionário
        candidatos = await _all_funcionarios_norm()
        total_func = len(funcionarios_pdf)
        funcs_persist = []
        for idx, f in enumerate(funcionarios_pdf):
            nome_pdf = f.get("nome") or f"Funcionário #{idx+1}"
            match = _fuzzy_pick(nome_pdf, candidatos)
            paginas = f.get("paginas") or []
            anexo_path = None
            if paginas:
                try:
                    sub_pdf = _split_pdf_pages(pdf_bytes, paginas)
                    anexo_path = f"{APP_NAME}/folha-importada/{folha_id}/func-{idx+1}.pdf"
                    put_object(anexo_path, sub_pdf, "application/pdf")
                except Exception as e:
                    logger.warning(f"Split falhou para {nome_pdf}: {e}")
            funcs_persist.append({
                "linha_id": str(uuid.uuid4()),
                "nome_pdf": nome_pdf,
                "codigo_pdf": f.get("codigo"),
                "funcao_pdf": f.get("funcao"),
                "departamento_pdf": f.get("departamento"),
                "admissao_pdf": f.get("admissao"),
                "valor_liquido": float(f.get("valor_liquido") or 0),
                "total_vencimentos": float(f.get("total_vencimentos") or 0),
                "total_descontos": float(f.get("total_descontos") or 0),
                "salario_base": float(f.get("salario_base") or 0),
                "base_inss": float(f.get("base_inss") or 0),
                "base_fgts": float(f.get("base_fgts") or 0),
                "fgts_mes": float(f.get("fgts_mes") or 0),
                "base_irrf": float(f.get("base_irrf") or 0),
                "vencimentos_detalhados": f.get("vencimentos_detalhados") or [],
                "descontos_detalhados": f.get("descontos_detalhados") or [],
                "paginas": paginas,
                "anexo_holerite_path": anexo_path,
                "funcionario_id": match["match_id"],
                "match_nome_db": match["nome_db"],
                "match_score": match["score"],
                "match_status": match["status"],
            })
            # Progresso 60 -> 95 enquanto faz split
            await _atualiza(
                60 + int(35 * (idx + 1) / max(total_func, 1)),
                "split",
            )

        total_geral = parsed.get("total_geral_liquido")
        if total_geral is None or total_geral == 0:
            total_geral = sum(x["valor_liquido"] for x in funcs_persist)

        # 4. Finaliza
        await folhas_importadas_collection.update_one(
            {"id": folha_id},
            {"$set": {
                "status": "em_revisao",
                "progresso": 100,
                "etapa": "concluida",
                "empresa": parsed.get("empresa"),
                "cnpj": parsed.get("cnpj"),
                "mes_competencia": int(parsed.get("mes_competencia") or 0),
                "ano_competencia": int(parsed.get("ano_competencia") or 0),
                "total_geral_liquido": float(total_geral),
                "total_funcionarios": len(funcs_persist),
                "filename_original": filename,
                "total_paginas": total_paginas,
                "master_pdf_path": master_path,
                "funcionarios": funcs_persist,
                "concluida_em": datetime.now(timezone.utc).isoformat(),
            }},
        )

        # Notifica o RH que a folha está pronta para revisão
        mes = int(parsed.get("mes_competencia") or 0)
        ano = int(parsed.get("ano_competencia") or 0)
        comp_str = f"{mes:02d}/{ano}" if mes else "—"
        sem_match = sum(1 for x in funcs_persist if not x.get("funcionario_id"))
        await _criar_task(
            target_system="rh",
            title=f"Folha {comp_str} pronta para revisão",
            message=(
                f"{len(funcs_persist)} funcionário(s) extraído(s) — Total "
                f"R$ {float(total_geral):.2f}."
                + (f" Atenção: {sem_match} sem vínculo identificado." if sem_match else "")
            ),
            priority="alta" if sem_match > 0 else "media",
            origem={"tipo": "folha_importada", "folha_id": folha_id},
        )
    except Exception as e:
        logger.exception("Erro inesperado processando folha")
        await _atualiza(100, "erro", status="erro", erro=str(e))


# =================== Endpoints RH ===================
@folha_router.post("/importar")
async def importar_folha(arquivo: UploadFile = File(...)):
    """Inicia processamento em background. Retorna 202 com {id, status:'processando'}.
    Cliente faz polling em GET /folha-pagamento/{id} para acompanhar progresso (0-100)."""
    import asyncio
    if not arquivo.filename or not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um PDF")
    pdf_bytes = await arquivo.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(pdf_bytes) > 30 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo > 30MB")

    folha_id = str(uuid.uuid4())
    doc = {
        "id": folha_id,
        "status": "processando",
        "progresso": 0,
        "etapa": "fila",
        "filename_original": arquivo.filename,
        "total_funcionarios": 0,
        "total_geral_liquido": 0,
        "funcionarios": [],
        "envio_financeiro": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await folhas_importadas_collection.insert_one(doc)

    # Dispara task em background
    asyncio.create_task(
        _processar_folha_background(folha_id, pdf_bytes, arquivo.filename)
    )

    doc.pop("_id", None)
    return doc


@folha_router.post("/_legacy_importar_sync")
async def importar_folha_sync(arquivo: UploadFile = File(...)):
    """Endpoint legado SÍNCRONO (mantido apenas para testes/CLI). Retorna após processar tudo (~30-60s).
    Para uso normal, use POST /importar (assíncrono)."""
    if not arquivo.filename or not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um PDF")
    pdf_bytes = await arquivo.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(pdf_bytes) > 30 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo > 30MB")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_paginas = len(reader.pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF inválido: {e}")
    if total_paginas == 0:
        raise HTTPException(status_code=400, detail="PDF sem páginas")

    parsed = await _ocr_folha_pdf(pdf_bytes)
    funcionarios_pdf = parsed.get("funcionarios") or []
    if not funcionarios_pdf:
        raise HTTPException(status_code=422, detail="Nenhum holerite identificado no PDF")

    folha_id = str(uuid.uuid4())
    master_path = f"{APP_NAME}/folha-importada/{folha_id}/master.pdf"
    put_object(master_path, pdf_bytes, "application/pdf")

    candidatos = await _all_funcionarios_norm()
    funcs_persist = []
    for idx, f in enumerate(funcionarios_pdf):
        nome_pdf = f.get("nome") or f"Funcionário #{idx+1}"
        match = _fuzzy_pick(nome_pdf, candidatos)
        paginas = f.get("paginas") or []
        anexo_path = None
        if paginas:
            try:
                sub_pdf = _split_pdf_pages(pdf_bytes, paginas)
                anexo_path = f"{APP_NAME}/folha-importada/{folha_id}/func-{idx+1}.pdf"
                put_object(anexo_path, sub_pdf, "application/pdf")
            except Exception as e:
                logger.warning(f"Split falhou para {nome_pdf}: {e}")
        funcs_persist.append({
            "linha_id": str(uuid.uuid4()),
            "nome_pdf": nome_pdf,
            "codigo_pdf": f.get("codigo"),
            "funcao_pdf": f.get("funcao"),
            "departamento_pdf": f.get("departamento"),
            "admissao_pdf": f.get("admissao"),
            "valor_liquido": float(f.get("valor_liquido") or 0),
            "total_vencimentos": float(f.get("total_vencimentos") or 0),
            "total_descontos": float(f.get("total_descontos") or 0),
            "salario_base": float(f.get("salario_base") or 0),
            "base_inss": float(f.get("base_inss") or 0),
            "base_fgts": float(f.get("base_fgts") or 0),
            "fgts_mes": float(f.get("fgts_mes") or 0),
            "base_irrf": float(f.get("base_irrf") or 0),
            "vencimentos_detalhados": f.get("vencimentos_detalhados") or [],
            "descontos_detalhados": f.get("descontos_detalhados") or [],
            "paginas": paginas,
            "anexo_holerite_path": anexo_path,
            "funcionario_id": match["match_id"],
            "match_nome_db": match["nome_db"],
            "match_score": match["score"],
            "match_status": match["status"],
        })

    total_geral = parsed.get("total_geral_liquido")
    if total_geral is None or total_geral == 0:
        total_geral = sum(x["valor_liquido"] for x in funcs_persist)

    doc = {
        "id": folha_id,
        "empresa": parsed.get("empresa"),
        "cnpj": parsed.get("cnpj"),
        "mes_competencia": int(parsed.get("mes_competencia") or 0),
        "ano_competencia": int(parsed.get("ano_competencia") or 0),
        "total_geral_liquido": float(total_geral),
        "total_funcionarios": len(funcs_persist),
        "filename_original": arquivo.filename,
        "total_paginas": total_paginas,
        "master_pdf_path": master_path,
        "funcionarios": funcs_persist,
        "status": "em_revisao",
        "progresso": 100,
        "etapa": "concluida",
        "envio_financeiro": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await folhas_importadas_collection.insert_one(doc)
    doc.pop("_id", None)
    return doc


@folha_router.get("")
async def listar_folhas():
    out = []
    async for d in folhas_importadas_collection.find({}, {"_id": 0}).sort("created_at", -1):
        out.append(d)
    return out


@folha_router.get("/{folha_id}")
async def get_folha(folha_id: str):
    d = await folhas_importadas_collection.find_one({"id": folha_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Folha não encontrada")
    return d


@folha_router.post("/{folha_id}/resolver-matches")
async def resolver_matches(folha_id: str, payload: ResolverMatchPayload):
    folha = await folhas_importadas_collection.find_one({"id": folha_id}, {"_id": 0})
    if not folha:
        raise HTTPException(status_code=404, detail="Folha não encontrada")

    # Mapeia linha_id -> funcionario_id
    overrides = {x.get("linha_id"): x.get("funcionario_id") for x in payload.funcionarios}
    new_funcs = []
    for f in folha["funcionarios"]:
        lid = f.get("linha_id")
        if lid in overrides:
            fid = overrides[lid]
            if fid:
                doc = await funcionarios_collection.find_one({"id": fid}, {"_id": 0, "nome": 1})
                if not doc:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Funcionário {fid} não encontrado",
                    )
                f["funcionario_id"] = fid
                f["match_nome_db"] = doc.get("nome")
                f["match_score"] = 100
                f["match_status"] = "manual"
            else:
                # explicit clear (override = '' / None)
                f["funcionario_id"] = None
                f["match_nome_db"] = None
                f["match_score"] = 0
                f["match_status"] = "low"
        new_funcs.append(f)
    await folhas_importadas_collection.update_one(
        {"id": folha_id}, {"$set": {"funcionarios": new_funcs}}
    )
    return {"ok": True, "atualizados": len(overrides)}


@folha_router.post("/{folha_id}/enviar-financeiro")
async def enviar_financeiro(folha_id: str, payload: EnviarFinanceiroPayload):
    folha = await folhas_importadas_collection.find_one({"id": folha_id}, {"_id": 0})
    if not folha:
        raise HTTPException(status_code=404, detail="Folha não encontrada")
    if folha["status"] not in ("em_revisao", "rejeitada"):
        # Permite reenviar somente se foi rejeitada ou ainda em revisão.
        # Bloqueia se está 'enviada' com solicitação pendente ativa (evita duplicidade).
        sol_pendente = await solicitacoes_folha_collection.find_one(
            {"folha_id": folha_id, "status": "pendente"}, {"_id": 0, "id": 1}
        )
        if sol_pendente:
            raise HTTPException(
                status_code=400,
                detail="Já existe uma solicitação pendente no Financeiro para esta folha",
            )
        if folha["status"] == "aceita":
            raise HTTPException(
                status_code=400, detail="Folha já foi aceita; não pode ser reenviada"
            )

    # Bloqueia se houver linhas low (sem match)
    sem_match = [
        f for f in folha["funcionarios"]
        if not f.get("funcionario_id")
    ]
    if sem_match:
        raise HTTPException(
            status_code=400,
            detail=f"{len(sem_match)} funcionário(s) sem mapping (resolva os matches primeiro)",
        )

    sol_id = str(uuid.uuid4())
    sol = {
        "id": sol_id,
        "folha_id": folha_id,
        "modo": payload.modo,  # cheio | individual
        "observacao_rh": payload.observacao,
        "empresa": folha.get("empresa"),
        "mes_competencia": folha.get("mes_competencia"),
        "ano_competencia": folha.get("ano_competencia"),
        "total_geral_liquido": folha.get("total_geral_liquido"),
        "total_funcionarios": folha.get("total_funcionarios"),
        "status": "pendente",  # pendente -> aceita -> rejeitada
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decidido_em": None,
        "decidido_por": None,
        "contas_pagar_ids": [],
    }
    await solicitacoes_folha_collection.insert_one(sol)
    await folhas_importadas_collection.update_one(
        {"id": folha_id},
        {"$set": {
            "status": "enviada",
            "envio_financeiro": {
                "solicitacao_id": sol_id,
                "modo": payload.modo,
                "enviada_em": sol["created_at"],
            },
        }},
    )
    sol.pop("_id", None)

    # Notifica o Financeiro
    mes = sol.get("mes_competencia") or 0
    ano = sol.get("ano_competencia") or 0
    comp_str = f"{mes:02d}/{ano}" if mes else "—"
    modo_label = "folha cheia" if payload.modo == "cheio" else "individual"
    await _criar_task(
        target_system="administrativo",
        title=f"Solicitação de Folha {comp_str} — aguardando aprovação",
        message=(
            f"{folha.get('empresa') or 'Folha'} | "
            f"{folha.get('total_funcionarios')} funcionário(s) | "
            f"R$ {float(folha.get('total_geral_liquido') or 0):.2f} | "
            f"Modo: {modo_label}."
        ),
        priority="alta",
        origem={
            "tipo": "solicitacao_folha",
            "solicitacao_id": sol_id,
            "folha_id": folha_id,
            "rota": f"/administrativo/solicitacoes-folha?abrir={sol_id}",
        },
    )
    return sol


@folha_router.delete("/{folha_id}")
async def excluir_folha(folha_id: str):
    """Exclui uma folha importada. Permite excluir folhas em qualquer status —
    inclusive 'aceita'. As contas a pagar geradas a partir dela continuam no
    Financeiro (o usuário deve removê-las manualmente, conforme avisado na UI)."""
    folha = await folhas_importadas_collection.find_one({"id": folha_id}, {"_id": 0})
    if not folha:
        raise HTTPException(status_code=404, detail="Folha não encontrada")
    await folhas_importadas_collection.delete_one({"id": folha_id})
    # Remove TODAS as solicitações ligadas (pendentes, aceitas, rejeitadas)
    await solicitacoes_folha_collection.delete_many({"folha_id": folha_id})
    return {"ok": True}


@folha_router.get("/{folha_id}/master-pdf")
async def baixar_master_pdf(folha_id: str):
    from fastapi.responses import Response
    folha = await folhas_importadas_collection.find_one({"id": folha_id}, {"_id": 0})
    if not folha or not folha.get("master_pdf_path"):
        raise HTTPException(status_code=404, detail="PDF não encontrado")
    data, ct = get_object(folha["master_pdf_path"])
    return Response(
        content=data,
        media_type=ct,
        headers={"Content-Disposition": f'attachment; filename="folha_{folha_id[:8]}.pdf"'},
    )


@folha_router.get("/{folha_id}/holerite/{linha_id}")
async def baixar_holerite_individual(folha_id: str, linha_id: str):
    from fastapi.responses import Response
    folha = await folhas_importadas_collection.find_one({"id": folha_id}, {"_id": 0})
    if not folha:
        raise HTTPException(status_code=404, detail="Folha não encontrada")
    linha = next((f for f in folha["funcionarios"] if f["linha_id"] == linha_id), None)
    if not linha or not linha.get("anexo_holerite_path"):
        raise HTTPException(status_code=404, detail="Holerite não encontrado")
    data, ct = get_object(linha["anexo_holerite_path"])
    nome_safe = (linha.get("nome_pdf") or "func").replace(" ", "_")[:40]
    return Response(
        content=data,
        media_type=ct,
        headers={"Content-Disposition": f'attachment; filename="holerite_{nome_safe}.pdf"'},
    )


# =================== Endpoints Financeiro ===================
fin_folha_router = APIRouter(prefix="/financeiro/solicitacoes-folha", tags=["financeiro-folha"])


@fin_folha_router.get("")
async def listar_solicitacoes(status: Optional[str] = None):
    q = {}
    if status:
        q["status"] = status
    out = []
    async for d in solicitacoes_folha_collection.find(q, {"_id": 0}).sort("created_at", -1):
        # Enriquece com dados da folha
        folha = await folhas_importadas_collection.find_one(
            {"id": d["folha_id"]}, {"_id": 0, "funcionarios": 1, "filename_original": 1}
        )
        if folha:
            d["funcionarios_preview"] = [
                {
                    "linha_id": f["linha_id"],
                    "nome_pdf": f.get("nome_pdf"),
                    "funcionario_id": f.get("funcionario_id"),
                    "valor_liquido": f.get("valor_liquido"),
                    "match_nome_db": f.get("match_nome_db"),
                }
                for f in (folha.get("funcionarios") or [])
            ]
            d["filename_original"] = folha.get("filename_original")
        out.append(d)
    return out


@fin_folha_router.get("/{sol_id}")
async def get_solicitacao(sol_id: str):
    sol = await solicitacoes_folha_collection.find_one({"id": sol_id}, {"_id": 0})
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    folha = await folhas_importadas_collection.find_one({"id": sol["folha_id"]}, {"_id": 0})
    sol["folha"] = folha
    return sol


@fin_folha_router.post("/{sol_id}/aceitar")
async def aceitar_solicitacao(sol_id: str, payload: AceitarSolicitacaoPayload):
    sol = await solicitacoes_folha_collection.find_one({"id": sol_id}, {"_id": 0})
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if sol["status"] != "pendente":
        raise HTTPException(status_code=400, detail=f"Solicitação está {sol['status']}")

    folha = await folhas_importadas_collection.find_one({"id": sol["folha_id"]}, {"_id": 0})
    if not folha:
        raise HTTPException(status_code=404, detail="Folha origem não encontrada")

    plano = await plano_contas_collection.find_one({"id": payload.plano_contas_id}, {"_id": 0})
    if not plano:
        raise HTTPException(status_code=400, detail="Plano de contas inválido")

    # Valida data
    try:
        datetime.strptime(payload.data_vencimento, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="data_vencimento inválida (use YYYY-MM-DD)")

    competencia_str = ""
    mes = folha.get("mes_competencia") or 0
    ano = folha.get("ano_competencia") or datetime.now().year
    nomes_meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    if 1 <= mes <= 12:
        competencia_str = f"{nomes_meses[mes]}/{ano}"

    # Helper para montar bloco de detalhes completos da folha (TODAS as informações)
    def _bloco_detalhes_folha(funcionarios_lista):
        linhas = []
        linhas.append("════════ FOLHA DE PAGAMENTO — DETALHAMENTO COMPLETO ════════")
        linhas.append(f"Competência: {competencia_str or f'{mes:02d}/{ano}'}")
        linhas.append(f"Empresa: {folha.get('empresa') or '—'}")
        if folha.get('cnpj'):
            linhas.append(f"CNPJ: {folha.get('cnpj')}")
        linhas.append(f"Solicitação RH: {sol_id[:8]}")
        linhas.append(f"Folha ID: {sol['folha_id'][:8]}")
        linhas.append(f"Modo: {sol['modo']}")
        linhas.append(f"Total de funcionários: {len(funcionarios_lista)}")
        total_venc = sum(float(x.get('total_vencimentos') or 0) for x in funcionarios_lista)
        total_desc = sum(float(x.get('total_descontos') or 0) for x in funcionarios_lista)
        total_liq = sum(float(x.get('valor_liquido') or 0) for x in funcionarios_lista)
        linhas.append(f"Total vencimentos: R$ {total_venc:.2f}")
        linhas.append(f"Total descontos: R$ {total_desc:.2f}")
        linhas.append(f"Total líquido: R$ {total_liq:.2f}")
        linhas.append("")
        linhas.append("──────── FUNCIONÁRIOS ────────")
        for idx, fnc in enumerate(funcionarios_lista, 1):
            nome = fnc.get('match_nome_db') or fnc.get('nome_pdf') or 'Funcionário'
            cpf = fnc.get('cpf') or fnc.get('cpf_pdf') or '—'
            cargo = fnc.get('cargo') or fnc.get('cargo_pdf') or '—'
            linhas.append(f"{idx}. {nome}")
            linhas.append(f"   CPF: {cpf} | Cargo: {cargo}")
            linhas.append(f"   Líquido: R$ {float(fnc.get('valor_liquido') or 0):.2f}")
            linhas.append(f"   Vencimentos: R$ {float(fnc.get('total_vencimentos') or 0):.2f}")
            linhas.append(f"   Descontos: R$ {float(fnc.get('total_descontos') or 0):.2f}")
            if fnc.get('funcionario_id'):
                linhas.append(f"   Vínculo DB: {fnc.get('funcionario_id')}")
            else:
                linhas.append("   Vínculo DB: NÃO VINCULADO")
            # Detalhes de rubricas se existirem
            rubricas = fnc.get('rubricas') or fnc.get('eventos') or []
            if rubricas:
                linhas.append("   Rubricas:")
                for r in rubricas[:30]:
                    rcod = r.get('codigo') or '—'
                    rdesc = r.get('descricao') or '—'
                    rref = r.get('referencia') or ''
                    rval = float(r.get('valor') or 0)
                    rtipo = r.get('tipo') or ''
                    linhas.append(f"     • [{rcod}] {rdesc} {rref} {rtipo}: R$ {rval:.2f}")
            obs_func = fnc.get('observacoes') or fnc.get('obs')
            if obs_func:
                linhas.append(f"   Obs: {obs_func}")
        if payload.observacao:
            linhas.append("")
            linhas.append(f"──── Observação do financeiro: {payload.observacao}")
        return "\n".join(linhas)

    contas_criadas: list[str] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    if sol["modo"] == "cheio":
        # 1 conta agrupada com PDF mestre como anexo
        descricao = f"Folha de Pagamento - {competencia_str or f'{mes:02d}/{ano}'} - {folha.get('empresa') or 'Empresa'} - {sol['total_funcionarios']} func"
        conta_id = str(uuid.uuid4())
        anexos = []
        if folha.get("master_pdf_path"):
            anexos.append({
                "id": str(uuid.uuid4()),
                "filename_original": folha.get("filename_original") or "folha.pdf",
                "storage_path": folha["master_pdf_path"],
                "content_type": "application/pdf",
            })
        # Anexa também os holerites individuais
        funcionarios_lista = folha.get("funcionarios") or []
        for f in funcionarios_lista:
            if f.get("anexo_holerite_path"):
                anexos.append({
                    "id": str(uuid.uuid4()),
                    "filename_original": f"holerite_{(f.get('nome_pdf') or 'func').replace(' ', '_')[:40]}.pdf",
                    "storage_path": f["anexo_holerite_path"],
                    "content_type": "application/pdf",
                })
        # Snapshot estruturado de TODOS os funcionários da folha
        funcionarios_snapshot = []
        for f in funcionarios_lista:
            funcionarios_snapshot.append({
                "funcionario_id": f.get("funcionario_id"),
                "linha_id": f.get("linha_id"),
                "nome_pdf": f.get("nome_pdf"),
                "match_nome_db": f.get("match_nome_db"),
                "cpf": f.get("cpf") or f.get("cpf_pdf"),
                "cargo": f.get("cargo") or f.get("cargo_pdf"),
                "valor_liquido": float(f.get("valor_liquido") or 0),
                "total_vencimentos": float(f.get("total_vencimentos") or 0),
                "total_descontos": float(f.get("total_descontos") or 0),
                "rubricas": f.get("rubricas") or f.get("eventos") or [],
                "anexo_holerite_path": f.get("anexo_holerite_path"),
                "observacoes": f.get("observacoes") or f.get("obs"),
            })
        nova_conta = {
            "id": conta_id,
            "descricao": descricao,
            "fornecedor_nome": folha.get("empresa") or "Folha de Pagamento",
            "fornecedor_cnpj": folha.get("cnpj"),
            "valor": float(folha.get("total_geral_liquido") or 0),
            "valor_desconto": 0,
            "valor_juros": 0,
            "valor_multa": 0,
            "valor_retencao": 0,
            "data_emissao": datetime.now().strftime("%Y-%m-%d"),
            "data_vencimento": payload.data_vencimento,
            "status": "em_aberto",
            "plano_contas_id": payload.plano_contas_id,
            "plano_conta_id": payload.plano_contas_id,
            "plano_contas_nome": plano.get("nome"),
            "plano_conta_nome": plano.get("nome"),
            "conta_bancaria_id": payload.conta_bancaria_id,
            "forma_pagamento": payload.forma_pagamento,
            "observacao": _bloco_detalhes_folha(funcionarios_lista),
            "observacoes": _bloco_detalhes_folha(funcionarios_lista),
            # Snapshot estruturado para uso pelo financeiro
            "folha_detalhes": {
                "competencia_str": competencia_str,
                "mes_competencia": mes,
                "ano_competencia": ano,
                "empresa": folha.get("empresa"),
                "cnpj_empresa": folha.get("cnpj"),
                "modo": sol["modo"],
                "total_funcionarios": sol['total_funcionarios'],
                "total_vencimentos": sum(float(x.get('total_vencimentos') or 0) for x in funcionarios_lista),
                "total_descontos": sum(float(x.get('total_descontos') or 0) for x in funcionarios_lista),
                "total_liquido": float(folha.get("total_geral_liquido") or 0),
                "funcionarios": funcionarios_snapshot,
            },
            "anexos": anexos,
            "origem": "folha_pagamento",
            "folha_id": sol["folha_id"],
            "solicitacao_folha_id": sol_id,
            "created_at": now_iso,
        }
        await contas_pagar_collection.insert_one(nova_conta)
        contas_criadas.append(conta_id)

    else:
        # individual: 1 conta por funcionário, com PDF dele como anexo
        for f in (folha.get("funcionarios") or []):
            conta_id = str(uuid.uuid4())
            nome = f.get("match_nome_db") or f.get("nome_pdf") or "Funcionário"
            cpf_func = f.get("cpf") or f.get("cpf_pdf")
            cargo_func = f.get("cargo") or f.get("cargo_pdf")
            descricao = f"Folha - {nome} - {competencia_str or f'{mes:02d}/{ano}'}"
            anexos = []
            if f.get("anexo_holerite_path"):
                anexos.append({
                    "id": str(uuid.uuid4()),
                    "filename_original": f"holerite_{nome.replace(' ', '_')[:40]}.pdf",
                    "storage_path": f["anexo_holerite_path"],
                    "content_type": "application/pdf",
                })
            # Bloco detalhado do funcionário individual
            linhas_det = []
            linhas_det.append("════════ HOLERITE — DETALHAMENTO COMPLETO ════════")
            linhas_det.append(f"Competência: {competencia_str or f'{mes:02d}/{ano}'}")
            linhas_det.append(f"Empresa: {folha.get('empresa') or '—'}")
            if folha.get('cnpj'):
                linhas_det.append(f"CNPJ Empresa: {folha.get('cnpj')}")
            linhas_det.append(f"Funcionário: {nome}")
            linhas_det.append(f"CPF: {cpf_func or '—'}")
            linhas_det.append(f"Cargo: {cargo_func or '—'}")
            if f.get('funcionario_id'):
                linhas_det.append(f"Vínculo DB: {f.get('funcionario_id')}")
            else:
                linhas_det.append("Vínculo DB: NÃO VINCULADO")
            linhas_det.append("")
            linhas_det.append(f"Total vencimentos: R$ {float(f.get('total_vencimentos') or 0):.2f}")
            linhas_det.append(f"Total descontos: R$ {float(f.get('total_descontos') or 0):.2f}")
            linhas_det.append(f"Líquido a pagar: R$ {float(f.get('valor_liquido') or 0):.2f}")
            rubricas = f.get('rubricas') or f.get('eventos') or []
            if rubricas:
                linhas_det.append("")
                linhas_det.append("──── Rubricas ────")
                for r in rubricas:
                    rcod = r.get('codigo') or '—'
                    rdesc = r.get('descricao') or '—'
                    rref = r.get('referencia') or ''
                    rval = float(r.get('valor') or 0)
                    rtipo = r.get('tipo') or ''
                    linhas_det.append(f"  • [{rcod}] {rdesc} {rref} {rtipo}: R$ {rval:.2f}")
            obs_func = f.get('observacoes') or f.get('obs')
            if obs_func:
                linhas_det.append(f"\nObs do holerite: {obs_func}")
            linhas_det.append(f"\nSolicitação RH: {sol_id[:8]} | Folha: {sol['folha_id'][:8]} | Linha: {f.get('linha_id') or '—'}")
            if payload.observacao:
                linhas_det.append(f"\n──── Observação financeiro: {payload.observacao}")
            observacao_completa = "\n".join(linhas_det)

            nova_conta = {
                "id": conta_id,
                "descricao": descricao,
                "fornecedor_nome": nome,
                "fornecedor_cpf": cpf_func,
                "funcionario_id": f.get("funcionario_id"),
                "valor": float(f.get("valor_liquido") or 0),
                "valor_desconto": 0,
                "valor_juros": 0,
                "valor_multa": 0,
                "valor_retencao": 0,
                "data_emissao": datetime.now().strftime("%Y-%m-%d"),
                "data_vencimento": payload.data_vencimento,
                "status": "em_aberto",
                "plano_contas_id": payload.plano_contas_id,
                "plano_conta_id": payload.plano_contas_id,
                "plano_contas_nome": plano.get("nome"),
                "plano_conta_nome": plano.get("nome"),
                "conta_bancaria_id": payload.conta_bancaria_id,
                "forma_pagamento": payload.forma_pagamento,
                "observacao": observacao_completa,
                "observacoes": observacao_completa,
                # Snapshot estruturado do holerite individual
                "folha_detalhes": {
                    "competencia_str": competencia_str,
                    "mes_competencia": mes,
                    "ano_competencia": ano,
                    "empresa": folha.get("empresa"),
                    "cnpj_empresa": folha.get("cnpj"),
                    "modo": "individual",
                    "funcionario": {
                        "funcionario_id": f.get("funcionario_id"),
                        "linha_id": f.get("linha_id"),
                        "nome_pdf": f.get("nome_pdf"),
                        "match_nome_db": f.get("match_nome_db"),
                        "cpf": cpf_func,
                        "cargo": cargo_func,
                        "valor_liquido": float(f.get("valor_liquido") or 0),
                        "total_vencimentos": float(f.get("total_vencimentos") or 0),
                        "total_descontos": float(f.get("total_descontos") or 0),
                        "rubricas": rubricas,
                        "anexo_holerite_path": f.get("anexo_holerite_path"),
                        "observacoes": obs_func,
                    },
                },
                "anexos": anexos,
                "origem": "folha_pagamento",
                "folha_id": sol["folha_id"],
                "linha_folha_id": f.get("linha_id"),
                "solicitacao_folha_id": sol_id,
                "created_at": now_iso,
            }
            await contas_pagar_collection.insert_one(nova_conta)
            contas_criadas.append(conta_id)

    # Atualiza solicitação e folha
    await solicitacoes_folha_collection.update_one(
        {"id": sol_id},
        {"$set": {
            "status": "aceita",
            "decidido_em": now_iso,
            "data_vencimento": payload.data_vencimento,
            "plano_contas_id": payload.plano_contas_id,
            "plano_contas_nome": plano.get("nome"),
            "conta_bancaria_id": payload.conta_bancaria_id,
            "forma_pagamento": payload.forma_pagamento,
            "observacao_financeiro": payload.observacao,
            "contas_pagar_ids": contas_criadas,
        }},
    )
    await folhas_importadas_collection.update_one(
        {"id": sol["folha_id"]},
        {"$set": {"status": "aceita", "contas_pagar_ids": contas_criadas}},
    )

    # Notifica o RH do retorno positivo
    mes = sol.get("mes_competencia") or 0
    ano = sol.get("ano_competencia") or 0
    comp_str = f"{mes:02d}/{ano}" if mes else "—"
    await _criar_task(
        target_system="rh",
        title=f"Folha {comp_str} aceita — {len(contas_criadas)} conta(s) lançada(s)",
        message=(
            f"O Financeiro aceitou a folha. Vencimento: {payload.data_vencimento}. "
            f"Plano: {plano.get('nome') or '—'}."
        ),
        priority="media",
        origem={"tipo": "folha_aceita", "folha_id": sol["folha_id"]},
    )
    return {"ok": True, "modo": sol["modo"], "contas_criadas": contas_criadas, "total": len(contas_criadas)}


@fin_folha_router.post("/{sol_id}/rejeitar")
async def rejeitar_solicitacao(sol_id: str, body: dict = Body(default={})):
    motivo = (body.get("motivo") or "").strip()
    sol = await solicitacoes_folha_collection.find_one({"id": sol_id}, {"_id": 0})
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if sol["status"] != "pendente":
        raise HTTPException(status_code=400, detail=f"Solicitação está {sol['status']}")
    now_iso = datetime.now(timezone.utc).isoformat()
    await solicitacoes_folha_collection.update_one(
        {"id": sol_id},
        {"$set": {
            "status": "rejeitada",
            "decidido_em": now_iso,
            "motivo_rejeicao": motivo,
        }},
    )
    await folhas_importadas_collection.update_one(
        {"id": sol["folha_id"]},
        {"$set": {"status": "rejeitada"}},
    )
    # Notifica o RH do retorno negativo
    mes = sol.get("mes_competencia") or 0
    ano = sol.get("ano_competencia") or 0
    comp_str = f"{mes:02d}/{ano}" if mes else "—"
    await _criar_task(
        target_system="rh",
        title=f"Folha {comp_str} foi rejeitada pelo Financeiro",
        message=motivo or "Sem motivo informado. Revise e reenvie.",
        priority="alta",
        origem={"tipo": "folha_rejeitada", "folha_id": sol["folha_id"]},
    )
    return {"ok": True}



@fin_folha_router.delete("/{sol_id}")
async def excluir_solicitacao(sol_id: str):
    """Exclui uma solicitação de folha do Financeiro (em qualquer status).

    - PENDENTE: remove a solicitação e devolve a folha original para 'em_revisao'
      (assim ela pode ser reenviada pelo RH).
    - ACEITA: remove a solicitação. As Contas a Pagar geradas NÃO são apagadas
      automaticamente — o usuário deve removê-las manualmente caso queira.
    - REJEITADA: remove a solicitação (limpeza de histórico).
    """
    sol = await solicitacoes_folha_collection.find_one({"id": sol_id}, {"_id": 0})
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    await solicitacoes_folha_collection.delete_one({"id": sol_id})

    # Se estava pendente, devolve a folha ao RH em revisão
    if sol.get("status") == "pendente" and sol.get("folha_id"):
        await folhas_importadas_collection.update_one(
            {"id": sol["folha_id"]},
            {"$set": {"status": "em_revisao"}},
        )

    return {"ok": True, "status_anterior": sol.get("status")}
