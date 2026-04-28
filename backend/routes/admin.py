"""
Admin Routes - Administrative module endpoints (Financeiro, Cadastros, Contas a Pagar/Receber, etc.)
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body, Query
from fastapi.responses import Response
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import os
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create router
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# ============ ADMIN MODELS ============

class CadastroCreate(BaseModel):
    tipo_cadastro: str = "cliente"
    tipo_pessoa: str = "PF"
    status: str = "ativo"
    nome_razao: str
    apelido_fantasia: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    rg_ie: Optional[str] = None
    telefone: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    grupo: Optional[str] = None
    rota: Optional[str] = None
    vendedor: Optional[str] = None
    limite_credito: Optional[float] = None
    observacoes: Optional[str] = None


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
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_pagamento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None
    frota_nome: Optional[str] = None
    forma_pagamento: str = "dinheiro"
    conta_movimento: Optional[str] = None
    status: str = "em_aberto"
    observacoes: Optional[str] = None


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
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_recebimento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    forma_pagamento: str = "dinheiro"
    conta_movimento: Optional[str] = None
    status: str = "em_aberto"
    observacoes: Optional[str] = None


class OrdemServicoItem(BaseModel):
    codigo: Optional[str] = None
    quantidade: float = 1
    unidade: str = "UN"
    descricao: str
    valor_unitario: float = 0
    valor_desconto: float = 0


class OrdemServicoCreate(BaseModel):
    # Identificação
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    cliente_documento: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_telefone: Optional[str] = None
    cliente_celular: Optional[str] = None
    cliente_fantasia: Optional[str] = None
    cliente_ie: Optional[str] = None
    cliente_endereco: Optional[str] = None
    cliente_bairro: Optional[str] = None
    cliente_cidade: Optional[str] = None
    cliente_uf: Optional[str] = None
    cliente_cep: Optional[str] = None

    # Endereço de entrega / obra (pode diferir do cadastro)
    endereco_entrega: Optional[str] = None
    obra: Optional[str] = None
    obra_id: Optional[str] = None
    numero_contrato: Optional[str] = None
    numero_documento_fiscal: Optional[str] = None

    # Datas e tipo de atendimento
    descricao: str
    tipo: str = "servico"
    tipo_atendimento: Optional[str] = None
    periodo: Optional[str] = None
    data_abertura: str
    data_fechamento: Optional[str] = None
    data_previsao: Optional[str] = None
    data_conclusao: Optional[str] = None

    # Itens da OS
    itens: Optional[List[OrdemServicoItem]] = None

    # Valores
    valor_total: float = 0
    valor_desconto: float = 0
    valor_subtotal: float = 0

    # Pagamento e observações
    forma_pagamento: Optional[str] = None
    condicao_pagamento: Optional[str] = None
    observacao_servicos: Optional[str] = None
    observacoes: Optional[str] = None
    notas_gerais: Optional[str] = None

    # Status / responsável / máquina
    status: str = "aberta"
    prioridade: str = "media"
    responsavel_id: Optional[str] = None
    responsavel_nome: Optional[str] = None
    atendente_nome: Optional[str] = None
    maquina_id: Optional[str] = None
    maquina_nome: Optional[str] = None

    # Empresa emissora (1 ou 2 — para suportar a coluna "Empresa" do template)
    empresa_emissora: Optional[str] = None  # "locadora" | "construtora"


class PlanoContaCreate(BaseModel):
    codigo: str
    nome: str
    tipo: str = "despesa"
    grupo: Optional[str] = None
    descricao: Optional[str] = None
    status: str = "ativo"


class CentroCustoCreate(BaseModel):
    codigo: str
    nome: str
    tipo: Optional[str] = None
    responsavel: Optional[str] = None
    descricao: Optional[str] = None
    status: str = "ativo"


# ============ DASHBOARD ADMIN ============

@admin_router.get("/dashboard")
async def get_admin_dashboard():
    """Dashboard financeiro administrativo"""
    try:
        contas_pagar = await db.contas_pagar.find({"status": "em_aberto"}).to_list(1000)
        contas_receber = await db.contas_receber.find({"status": "em_aberto"}).to_list(1000)
        ordens_servico = await db.ordens_servico.find({"status": {"$in": ["aberta", "em_andamento"]}}).to_list(1000)
        
        total_pagar = sum(c.get("valor", 0) for c in contas_pagar)
        total_receber = sum(c.get("valor", 0) for c in contas_receber)
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        vencidas_pagar = [c for c in contas_pagar if c.get("data_vencimento", "") < hoje]
        vencidas_receber = [c for c in contas_receber if c.get("data_vencimento", "") < hoje]
        
        return {
            "resumo": {
                "total_pagar": total_pagar,
                "total_receber": total_receber,
                "saldo": total_receber - total_pagar,
                "contas_pagar_qtd": len(contas_pagar),
                "contas_receber_qtd": len(contas_receber),
                "ordens_abertas": len(ordens_servico)
            },
            "vencimentos": {
                "pagar_vencidas": len(vencidas_pagar),
                "pagar_vencidas_valor": sum(c.get("valor", 0) for c in vencidas_pagar),
                "receber_vencidas": len(vencidas_receber),
                "receber_vencidas_valor": sum(c.get("valor", 0) for c in vencidas_receber)
            }
        }
    except Exception as e:
        return {"error": str(e)}


# ============ CADASTROS ============

@admin_router.get("/cadastros")
async def list_cadastros(tipo: Optional[str] = None, status: Optional[str] = None):
    """Listar cadastros (clientes, fornecedores, etc.)"""
    query = {}
    if tipo:
        query["tipo_cadastro"] = tipo
    if status:
        query["status"] = status
    
    cadastros = []
    async for c in db.cadastros.find(query).sort("codigo", -1):
        c["_id"] = str(c["_id"])
        cadastros.append(c)
    return cadastros


@admin_router.get("/cadastros/{cadastro_id}")
async def get_cadastro(cadastro_id: str):
    """Obter cadastro por ID"""
    cadastro = await db.cadastros.find_one({"id": cadastro_id})
    if not cadastro:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    cadastro["_id"] = str(cadastro["_id"])
    return cadastro


@admin_router.post("/cadastros")
async def create_cadastro(data: CadastroCreate):
    """Criar novo cadastro"""
    last = await db.cadastros.find_one(sort=[("codigo", -1)])
    codigo = (last.get("codigo", 0) if last else 0) + 1
    
    cadastro_doc = data.dict()
    cadastro_doc["id"] = str(uuid.uuid4())
    cadastro_doc["codigo"] = codigo
    cadastro_doc["created_at"] = datetime.now().isoformat()
    
    await db.cadastros.insert_one(cadastro_doc)
    cadastro_doc["_id"] = str(cadastro_doc.get("_id", ""))
    return cadastro_doc


@admin_router.put("/cadastros/{cadastro_id}")
async def update_cadastro(cadastro_id: str, data: CadastroCreate):
    """Atualizar cadastro"""
    existing = await db.cadastros.find_one({"id": cadastro_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.cadastros.update_one({"id": cadastro_id}, {"$set": update_data})
    return {"message": "Cadastro atualizado"}


@admin_router.delete("/cadastros/{cadastro_id}")
async def delete_cadastro(cadastro_id: str):
    """Excluir cadastro"""
    result = await db.cadastros.delete_one({"id": cadastro_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    return {"message": "Cadastro excluído"}


# ============ CONTAS A PAGAR / RECEBER ============
# (Endpoints extraídos para /app/backend/routes/financeiro.py — Refactor Sessão 32 Parte 2)
# (Versões antigas e incompletas aqui removidas para evitar conflito de rota)

# ============ ORDENS DE SERVIÇO ============

@admin_router.get("/ordens-servico")
async def list_ordens_servico(status: Optional[str] = None):
    """Listar ordens de serviço"""
    query = {}
    if status:
        query["status"] = status
    
    ordens = []
    async for o in db.ordens_servico.find(query).sort("data_abertura", -1):
        o["_id"] = str(o["_id"])
        ordens.append(o)
    return ordens


@admin_router.get("/ordens-servico/{ordem_id}")
async def get_ordem_servico(ordem_id: str):
    """Obter ordem de serviço por ID"""
    ordem = await db.ordens_servico.find_one({"id": ordem_id})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    ordem["_id"] = str(ordem["_id"])
    return ordem


@admin_router.post("/ordens-servico")
async def create_ordem_servico(data: OrdemServicoCreate):
    """Criar ordem de serviço"""
    last = await db.ordens_servico.find_one(sort=[("numero", -1)])
    numero = (last.get("numero", 0) if last else 0) + 1
    
    ordem_doc = data.dict()
    ordem_doc["id"] = str(uuid.uuid4())
    ordem_doc["numero"] = numero
    ordem_doc["created_at"] = datetime.now().isoformat()
    
    await db.ordens_servico.insert_one(ordem_doc)
    ordem_doc["_id"] = str(ordem_doc.get("_id", ""))
    return ordem_doc


@admin_router.put("/ordens-servico/{ordem_id}")
async def update_ordem_servico(ordem_id: str, data: OrdemServicoCreate):
    """Atualizar ordem de serviço"""
    existing = await db.ordens_servico.find_one({"id": ordem_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.ordens_servico.update_one({"id": ordem_id}, {"$set": update_data})
    return {"message": "Ordem atualizada"}


@admin_router.put("/ordens-servico/{ordem_id}/concluir")
async def concluir_ordem_servico(ordem_id: str, data_conclusao: str = Body(..., embed=True)):
    """Concluir ordem de serviço"""
    existing = await db.ordens_servico.find_one({"id": ordem_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    
    await db.ordens_servico.update_one(
        {"id": ordem_id},
        {"$set": {"status": "concluida", "data_conclusao": data_conclusao, "updated_at": datetime.now().isoformat()}}
    )
    return {"message": "Ordem concluída"}


@admin_router.delete("/ordens-servico/{ordem_id}")
async def delete_ordem_servico(ordem_id: str):
    """Excluir ordem de serviço"""
    result = await db.ordens_servico.delete_one({"id": ordem_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    return {"message": "Ordem excluída"}


@admin_router.get("/ordens-servico/{ordem_id}/export-pdf")
async def export_ordem_servico_pdf(ordem_id: str):
    """Exporta a Ordem de Serviço (DAV-OS) em PDF no formato STT."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    import io

    ordem = await db.ordens_servico.find_one({"id": ordem_id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")

    # Dados da empresa emissora
    emp = ordem.get("empresa_emissora") or "locadora"
    if emp == "construtora":
        emp_nome = "RODRIGUES ALMEIDA CONSTRUCOES LTDA"
        emp_fantasia = "CRA CONSTRUCOES"
        emp_cnpj = "39.543.761/0002-06"
    else:
        emp_nome = "RODRIGUES ALMEIDA LOCACOES LTDA"
        emp_fantasia = "CRA LOCACOES"
        emp_cnpj = "39.543.761/0001-25"
    emp_telefone = "(63) 3214-9999"
    emp_endereco = "712 SUL AV. LO 15, 01 PLANO DIRETOR SUL"
    emp_cidade = "PALMAS-TO"

    def _brl(v):
        try:
            return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "R$ 0,00"

    def _data_br(d):
        if not d:
            return "-"
        s = str(d)
        if len(s) >= 10 and "-" in s:
            p = s[:10].split("-")
            if len(p) == 3:
                return f"{p[2]}/{p[1]}/{p[0]}"
        return s

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=0.8 * cm, rightMargin=0.8 * cm,
                            topMargin=0.6 * cm, bottomMargin=0.6 * cm)
    elements = []

    # Estilos
    style_label = ParagraphStyle("L", fontSize=7, fontName="Helvetica-Bold", textColor=colors.HexColor("#444"))
    style_value = ParagraphStyle("V", fontSize=8, fontName="Helvetica", leading=10, wordWrap="CJK")
    style_warn = ParagraphStyle("W", fontSize=7, fontName="Helvetica-Bold",
                                textColor=colors.HexColor("#C62828"), alignment=1)
    style_section = ParagraphStyle("S", fontSize=9, fontName="Helvetica-Bold",
                                   textColor=colors.white, alignment=0)

    # Cabeçalho: identificação da OS + empresa
    cab_data = [[
        Paragraph(
            f"<b>DAV-OS (ORDEM DE SERVIÇO) - N.: {ordem.get('numero', ordem_id[:8])}</b><br/>"
            f"<b>{emp_nome}</b><br/>{emp_fantasia} — CNPJ: {emp_cnpj}<br/>"
            f"{emp_telefone} | {emp_endereco} | {emp_cidade}",
            style_value,
        )
    ]]
    cab_table = Table(cab_data, colWidths=[19.4 * cm])
    cab_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(cab_table)
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(Paragraph(
        "NÃO É DOCUMENTO FISCAL — NÃO É VÁLIDO COMO RECIBO E COMO GARANTIA DE MERCADORIA — NÃO COMPROVA PAGAMENTO",
        style_warn,
    ))
    elements.append(Spacer(1, 0.2 * cm))

    # Identificação do destinatário
    elements.append(Table(
        [[Paragraph("IDENTIFICAÇÃO DO DESTINATÁRIO", style_section)]],
        colWidths=[19.4 * cm],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#444")),
                          ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3),
                          ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]),
    ))

    def _kv(label, value):
        return [Paragraph(label.upper(), style_label),
                Paragraph(str(value or "-"), style_value)]

    cliente_data = [
        [_kv("Cliente", ordem.get("cliente_nome"))[0], _kv("Cliente", ordem.get("cliente_nome"))[1],
         _kv("CPF/CNPJ", ordem.get("cliente_documento"))[0], _kv("CPF/CNPJ", ordem.get("cliente_documento"))[1]],
        [_kv("Fantasia", ordem.get("cliente_fantasia"))[0], _kv("Fantasia", ordem.get("cliente_fantasia"))[1],
         _kv("IE", ordem.get("cliente_ie"))[0], _kv("IE", ordem.get("cliente_ie"))[1]],
        [_kv("Endereço", ordem.get("cliente_endereco"))[0], _kv("Endereço", ordem.get("cliente_endereco"))[1],
         _kv("Bairro", ordem.get("cliente_bairro"))[0], _kv("Bairro", ordem.get("cliente_bairro"))[1]],
        [_kv("Cidade", ordem.get("cliente_cidade"))[0], _kv("Cidade", ordem.get("cliente_cidade"))[1],
         _kv("UF/CEP", f"{ordem.get('cliente_uf','')}/{ordem.get('cliente_cep','')}")[0],
         _kv("UF/CEP", f"{ordem.get('cliente_uf','')}/{ordem.get('cliente_cep','')}")[1]],
        [_kv("E-mail", ordem.get("cliente_email"))[0], _kv("E-mail", ordem.get("cliente_email"))[1],
         _kv("Fone/Cel", f"{ordem.get('cliente_telefone','')} / {ordem.get('cliente_celular','')}")[0],
         _kv("Fone/Cel", f"{ordem.get('cliente_telefone','')} / {ordem.get('cliente_celular','')}")[1]],
    ]
    t_cli = Table(cliente_data, colWidths=[2.4 * cm, 7.0 * cm, 2.4 * cm, 7.6 * cm])
    t_cli.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f0f0f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(t_cli)
    elements.append(Spacer(1, 0.15 * cm))

    # Dados da obra/atendimento
    elements.append(Table(
        [[Paragraph("DADOS DA OBRA / ATENDIMENTO", style_section)]],
        colWidths=[19.4 * cm],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#444")),
                          ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3),
                          ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]),
    ))
    obra_data = [
        [_kv("End. Entrega", ordem.get("endereco_entrega"))[0], _kv("End. Entrega", ordem.get("endereco_entrega"))[1],
         _kv("Obra", ordem.get("obra"))[0], _kv("Obra", ordem.get("obra"))[1]],
        [_kv("Data Abertura", _data_br(ordem.get("data_abertura")))[0],
         _kv("Data Abertura", _data_br(ordem.get("data_abertura")))[1],
         _kv("Data Fech.", _data_br(ordem.get("data_fechamento") or ordem.get("data_conclusao") or ordem.get("data_previsao")))[0],
         _kv("Data Fech.", _data_br(ordem.get("data_fechamento") or ordem.get("data_conclusao") or ordem.get("data_previsao")))[1]],
        [_kv("Tipo Atend.", ordem.get("tipo_atendimento") or ordem.get("tipo"))[0],
         _kv("Tipo Atend.", ordem.get("tipo_atendimento") or ordem.get("tipo"))[1],
         _kv("Período", ordem.get("periodo"))[0], _kv("Período", ordem.get("periodo"))[1]],
        [_kv("Nº Doc Fiscal", ordem.get("numero_documento_fiscal"))[0],
         _kv("Nº Doc Fiscal", ordem.get("numero_documento_fiscal"))[1],
         _kv("Nº Contrato", ordem.get("numero_contrato"))[0], _kv("Nº Contrato", ordem.get("numero_contrato"))[1]],
    ]
    t_obra = Table(obra_data, colWidths=[2.4 * cm, 7.0 * cm, 2.4 * cm, 7.6 * cm])
    t_obra.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f0f0f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(t_obra)
    elements.append(Spacer(1, 0.15 * cm))

    # Tabela de serviços
    elements.append(Table(
        [[Paragraph("SERVIÇOS / ITENS", style_section)]],
        colWidths=[19.4 * cm],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#444")),
                          ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3),
                          ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]),
    ))
    itens = ordem.get("itens") or []
    rows = [["Código", "Qtde", "UN", "Descrição Serviço", "Vlr Un.", "Vlr Total", "Vlr Desc", "Total Líq."]]
    sub_total = 0.0
    desc_total = 0.0
    for it in itens:
        q = float(it.get("quantidade") or 0)
        vu = float(it.get("valor_unitario") or 0)
        vd = float(it.get("valor_desconto") or 0)
        vt = q * vu
        liq = vt - vd
        sub_total += vt
        desc_total += vd
        rows.append([
            it.get("codigo") or "-",
            f"{q:g}",
            it.get("unidade") or "UN",
            Paragraph((it.get("descricao") or "")[:200], style_value),
            _brl(vu), _brl(vt), _brl(vd), _brl(liq),
        ])
    if not itens:
        rows.append(["-", "1", "UN", Paragraph(ordem.get("descricao") or "-", style_value),
                     _brl(ordem.get("valor_total")), _brl(ordem.get("valor_total")),
                     _brl(0), _brl(ordem.get("valor_total"))])
        sub_total = float(ordem.get("valor_total") or 0)

    t_itens = Table(rows, colWidths=[1.8 * cm, 1.2 * cm, 1.0 * cm, 6.4 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 3.0 * cm])
    t_itens.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#444")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (1, 1), (2, -1), "CENTER"),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_itens)
    elements.append(Spacer(1, 0.15 * cm))

    # Resumo financeiro
    desc_geral = float(ordem.get("valor_desconto") or 0) + desc_total
    total_servicos = sub_total - desc_geral
    total_os = float(ordem.get("valor_total") or total_servicos)
    resumo_data = [
        [Paragraph("N. de Itens", style_label), Paragraph(str(len(itens) or 1), style_value),
         Paragraph("Sub-Total", style_label), Paragraph(_brl(sub_total), style_value),
         Paragraph("Desconto", style_label), Paragraph(_brl(desc_geral), style_value),
         Paragraph("Total Serviços", style_label), Paragraph(_brl(total_servicos), style_value),
         Paragraph("TOTAL DA OS", style_label),
         Paragraph(f"<b>{_brl(total_os)}</b>",
                   ParagraphStyle("R", fontSize=10, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#C62828")))],
    ]
    t_resumo = Table(resumo_data,
                     colWidths=[1.6 * cm, 1.0 * cm, 1.6 * cm, 1.8 * cm, 1.6 * cm, 1.8 * cm,
                                1.8 * cm, 2.2 * cm, 2.0 * cm, 3.0 * cm])
    t_resumo.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (4, 0), (4, 0), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (6, 0), (6, 0), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (8, 0), (8, 0), colors.HexColor("#f0f0f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_resumo)
    elements.append(Spacer(1, 0.2 * cm))

    # Forma de pagamento
    if ordem.get("forma_pagamento") or ordem.get("condicao_pagamento"):
        elements.append(Paragraph(
            f"<b>FORMA DE PAGAMENTO:</b> {ordem.get('forma_pagamento') or '-'}"
            + (f" — {ordem.get('condicao_pagamento')}" if ordem.get("condicao_pagamento") else ""),
            style_value,
        ))
        elements.append(Spacer(1, 0.15 * cm))

    # Observações de serviços / notas gerais
    if ordem.get("observacao_servicos"):
        elements.append(Paragraph("<b>OBSERVAÇÃO:</b>", style_value))
        elements.append(Paragraph(ordem["observacao_servicos"].replace("\n", "<br/>"), style_value))
        elements.append(Spacer(1, 0.15 * cm))
    if ordem.get("notas_gerais") or ordem.get("observacoes"):
        notas = ordem.get("notas_gerais") or ordem.get("observacoes")
        elements.append(Paragraph("<b>NOTAS:</b>", style_value))
        elements.append(Paragraph(notas.replace("\n", "<br/>"), style_value))
        elements.append(Spacer(1, 0.3 * cm))

    # Assinaturas
    assinatura_data = [
        ["_" * 40, "_" * 40],
        [Paragraph(f"<b>Atendente</b><br/>{ordem.get('atendente_nome') or ordem.get('responsavel_nome') or '-'}",
                   ParagraphStyle("As", fontSize=8, alignment=1)),
         Paragraph("<b>Cliente</b><br/>" + (ordem.get("cliente_nome") or "-"),
                   ParagraphStyle("Ac", fontSize=8, alignment=1))],
    ]
    t_ass = Table(assinatura_data, colWidths=[9.7 * cm, 9.7 * cm])
    t_ass.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                               ("TOPPADDING", (0, 0), (-1, -1), 12),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    elements.append(t_ass)

    doc.build(elements)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=OS_{ordem.get('numero', ordem_id[:8])}.pdf"},
    )


# ============ PLANO DE CONTAS ============

@admin_router.get("/plano-contas")
async def list_plano_contas(tipo: Optional[str] = None):
    """Listar plano de contas"""
    query = {"status": "ativo"}
    if tipo:
        query["tipo"] = tipo
    
    contas = []
    async for c in db.plano_contas.find(query).sort("codigo", 1):
        c["_id"] = str(c["_id"])
        contas.append(c)
    return contas


@admin_router.post("/plano-contas")
async def create_plano_conta(data: PlanoContaCreate):
    """Criar plano de contas"""
    existing = await db.plano_contas.find_one({"codigo": data.codigo})
    if existing:
        raise HTTPException(status_code=400, detail="Código já existe")
    
    conta_doc = data.dict()
    conta_doc["id"] = str(uuid.uuid4())
    conta_doc["created_at"] = datetime.now().isoformat()
    
    await db.plano_contas.insert_one(conta_doc)
    conta_doc["_id"] = str(conta_doc.get("_id", ""))
    return conta_doc


@admin_router.put("/plano-contas/{conta_id}")
async def update_plano_conta(conta_id: str, data: PlanoContaCreate):
    """Atualizar plano de contas"""
    existing = await db.plano_contas.find_one({"id": conta_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.plano_contas.update_one({"id": conta_id}, {"$set": update_data})
    return {"message": "Conta atualizada"}


@admin_router.delete("/plano-contas/{conta_id}")
async def delete_plano_conta(conta_id: str):
    """Excluir plano de contas"""
    result = await db.plano_contas.delete_one({"id": conta_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    return {"message": "Conta excluída"}


# ============ CENTRO DE CUSTOS ============

@admin_router.get("/centros-custo")
async def list_centros_custo():
    """Listar centros de custo"""
    centros = []
    async for c in db.centros_custo.find({"status": "ativo"}).sort("codigo", 1):
        c["_id"] = str(c["_id"])
        centros.append(c)
    return centros


@admin_router.post("/centros-custo")
async def create_centro_custo(data: CentroCustoCreate):
    """Criar centro de custo"""
    existing = await db.centros_custo.find_one({"codigo": data.codigo})
    if existing:
        raise HTTPException(status_code=400, detail="Código já existe")
    
    centro_doc = data.dict()
    centro_doc["id"] = str(uuid.uuid4())
    centro_doc["created_at"] = datetime.now().isoformat()
    
    await db.centros_custo.insert_one(centro_doc)
    centro_doc["_id"] = str(centro_doc.get("_id", ""))
    return centro_doc


@admin_router.put("/centros-custo/{centro_id}")
async def update_centro_custo(centro_id: str, data: CentroCustoCreate):
    """Atualizar centro de custo"""
    existing = await db.centros_custo.find_one({"id": centro_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Centro não encontrado")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.centros_custo.update_one({"id": centro_id}, {"$set": update_data})
    return {"message": "Centro atualizado"}


@admin_router.delete("/centros-custo/{centro_id}")
async def delete_centro_custo(centro_id: str):
    """Excluir centro de custo"""
    result = await db.centros_custo.delete_one({"id": centro_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Centro não encontrado")
    return {"message": "Centro excluído"}


# ============ NOTIFICAÇÕES ============

@admin_router.get("/notificacoes")
async def get_admin_notificacoes():
    """Obter notificações administrativas (vencimentos)"""
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    notificacoes = []
    
    # Contas a pagar vencendo
    async for conta in db.contas_pagar.find({"status": "em_aberto"}):
        vencimento = conta.get("data_vencimento", "")
        if vencimento:
            vencida = vencimento < hoje
            dias = (datetime.strptime(vencimento, "%Y-%m-%d") - datetime.now()).days
            if dias <= 7:
                notificacoes.append({
                    "tipo": "conta_pagar",
                    "titulo": f"Conta a Pagar - {conta.get('descricao', '')}",
                    "valor": conta.get("valor", 0),
                    "vencimento": vencimento,
                    "vencida": vencida,
                    "dias": dias,
                    "urgencia": "alta" if vencida else ("media" if dias <= 3 else "baixa"),
                    "id": conta.get("id")
                })
    
    # Contas a receber vencendo
    async for conta in db.contas_receber.find({"status": "em_aberto"}):
        vencimento = conta.get("data_vencimento", "")
        if vencimento:
            vencida = vencimento < hoje
            dias = (datetime.strptime(vencimento, "%Y-%m-%d") - datetime.now()).days
            if dias <= 7:
                notificacoes.append({
                    "tipo": "conta_receber",
                    "titulo": f"Conta a Receber - {conta.get('descricao', '')}",
                    "valor": conta.get("valor", 0),
                    "vencimento": vencimento,
                    "vencida": vencida,
                    "dias": dias,
                    "urgencia": "alta" if vencida else ("media" if dias <= 3 else "baixa"),
                    "id": conta.get("id")
                })
    
    # Ordens de serviço pendentes
    async for ordem in db.ordens_servico.find({"status": {"$in": ["aberta", "em_andamento"]}}):
        previsao = ordem.get("data_previsao", "")
        if previsao:
            vencida = previsao < hoje
            dias = (datetime.strptime(previsao, "%Y-%m-%d") - datetime.now()).days
            if dias <= 3:
                notificacoes.append({
                    "tipo": "ordem_servico",
                    "titulo": f"OS #{ordem.get('numero', '')} - {ordem.get('descricao', '')}",
                    "valor": ordem.get("valor_total", 0),
                    "vencimento": previsao,
                    "vencida": vencida,
                    "dias": dias,
                    "urgencia": "alta" if vencida else "media",
                    "id": ordem.get("id")
                })
    
    notificacoes.sort(key=lambda x: (not x["vencida"], x["dias"]))
    
    return {
        "total": len(notificacoes),
        "vencidas": len([n for n in notificacoes if n["vencida"]]),
        "alta": len([n for n in notificacoes if n["urgencia"] == "alta"]),
        "media": len([n for n in notificacoes if n["urgencia"] == "media"]),
        "baixa": len([n for n in notificacoes if n["urgencia"] == "baixa"]),
        "notificacoes": notificacoes
    }
