"""
Export Routes (PDF / Excel / OFX / Recibos / Duplicatas / Extrato bancário).
Extraído de server.py na Sessão 32 de refatoração (Fase 2 Parte 1).

Contém endpoints genéricos de exportação por categoria: /export/pdf/{cat},
/export/excel/{cat}, /export/ofx/{cat}, /export/combined, /export/individual/*,
/export/recibo/*, /export/duplicata/*, /export/extrato-bancario, /export/relatorio-conta-bancaria.
"""
from __future__ import annotations

import base64
import io
import os
import re
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, ConfigDict

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db

# Reportlab (PDF)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch, mm
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# XlsxWriter (Excel)
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

# PyPDF2 (Merge combined PDFs)
try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    PdfReader = PdfWriter = None

import logging
logger = logging.getLogger(__name__)

exports_all_router = APIRouter(tags=["Exportação"])


# ============ HELPER: Filtro de período por coleção ============

# Mapeamento coleção -> campo de data primário usado para filtragem por período.
# Coleções não listadas usam "created_at" como fallback.
COLLECTION_DATE_FIELDS = {
    "contas_pagar": "data_vencimento",
    "contas_receber": "data_vencimento",
    "ordens_servico": "data_emissao",
    "maintenances": "service_date",
    "alugueis": "data_inicio",
    "ponto_registros": "data",
    "ferias": "data_inicio",
    "obras": "data_inicio",
    "imoveis": "data_inicio",
    "stock_movements": "created_at",
    "usage_logs": "created_at",
    "audit_logs": "created_at",
    "folha_pagamento": "competencia",  # YYYY-MM
    "epi_fichas": "data_entrega",
}


def _apply_period_filter(
    collection_name: str,
    query_filter: dict,
    data_inicio: Optional[str],
    data_fim: Optional[str],
) -> dict:
    """Aplica filtro por período (data_inicio/data_fim em YYYY-MM-DD) ao query_filter
    com base no campo de data principal da coleção.

    - Para campos do tipo string YYYY-MM-DD (ex.: data_vencimento), $gte/$lte funcionam direto.
    - Para `created_at` (ISO datetime string), append T23:59:59 no fim do dia.
    - Para `competencia` (YYYY-MM), recorta o YYYY-MM dos parâmetros.
    """
    if not data_inicio and not data_fim:
        return query_filter

    date_field = COLLECTION_DATE_FIELDS.get(collection_name, "created_at")
    period: dict = {}

    if date_field == "competencia":
        # Folha de pagamento opera por competência YYYY-MM
        if data_inicio and len(data_inicio) >= 7:
            period["$gte"] = data_inicio[:7]
        if data_fim and len(data_fim) >= 7:
            period["$lte"] = data_fim[:7]
    elif date_field == "created_at":
        # ISO datetime string. Para incluir o último dia inteiro, usar fim do dia.
        if data_inicio:
            period["$gte"] = data_inicio  # "2026-04-01" < "2026-04-01T..." trabalha como prefixo
        if data_fim:
            period["$lte"] = f"{data_fim}T23:59:59.999999+00:00"
    else:
        # Campo texto YYYY-MM-DD
        if data_inicio:
            period["$gte"] = data_inicio
        if data_fim:
            period["$lte"] = data_fim

    if not period:
        return query_filter

    # Mesclar com filtro existente no mesmo campo (ex.: vencidas já tem $lt today)
    existing = query_filter.get(date_field)
    if isinstance(existing, dict):
        merged = dict(existing)
        merged.update(period)
        query_filter[date_field] = merged
    else:
        query_filter[date_field] = period

    return query_filter


def _apply_forma_pagamento_filter(
    collection_name: str,
    query_filter: dict,
    forma_pagamento: Optional[str],
) -> dict:
    """Filtra contas_pagar / contas_receber pelo campo `forma_pagamento` (case-insensitive).
    Para outras coleções é no-op. Aceita o nome da forma (ex.: "PIX") ou "todas"/None.
    """
    if not forma_pagamento or forma_pagamento.lower() == "todas":
        return query_filter
    if collection_name not in ("contas_pagar", "contas_receber"):
        return query_filter
    # Match exato case-insensitive (escape para evitar regex injection)
    query_filter["forma_pagamento"] = {
        "$regex": f"^{re.escape(forma_pagamento)}$",
        "$options": "i",
    }
    return query_filter


# ============ PDF EXPORT ROUTES ============

from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import base64
import urllib.request

# Categorias e subcategorias para exportação
EXPORT_CATEGORIES_V2 = {
    "gerenciamento": [
        {
            "id": "maquinas",
            "label": "Máquinas",
            "icon": "truck",
            "subcategories": [
                {"id": "machines", "label": "Lista de Máquinas", "description": "Todas as máquinas cadastradas"},
                {"id": "machines_operational", "label": "Máquinas Operacionais", "description": "Apenas máquinas em operação"},
                {"id": "machines_maintenance", "label": "Máquinas em Manutenção", "description": "Máquinas paradas para manutenção"},
                {"id": "categories", "label": "Categorias de Máquinas", "description": "Tipos e categorias"},
            ]
        },
        {
            "id": "manutencoes",
            "label": "Manutenções",
            "icon": "wrench",
            "subcategories": [
                {"id": "maintenances", "label": "Todas as Manutenções", "description": "Histórico completo"},
                {"id": "maintenances_preventiva", "label": "Manutenções Preventivas", "description": "Apenas preventivas"},
                {"id": "maintenances_corretiva", "label": "Manutenções Corretivas", "description": "Apenas corretivas"},
                {"id": "maintenances_oil", "label": "Trocas de Óleo", "description": "Histórico de trocas de óleo"},
            ]
        },
        {
            "id": "horimetro",
            "label": "Horímetro",
            "icon": "clock",
            "subcategories": [
                {"id": "horimetro", "label": "Todos os Registros", "description": "Histórico completo de horímetro"},
                {"id": "horimetro_por_maquina", "label": "Resumo por Máquina", "description": "Horas trabalhadas por máquina"},
                {"id": "horimetro_por_operador", "label": "Resumo por Operador", "description": "Horas trabalhadas por operador"},
            ]
        },
        {
            "id": "combustivel",
            "label": "Combustível",
            "icon": "fuel",
            "subcategories": [
                {"id": "combustivel", "label": "Todos os Registros", "description": "Histórico completo de combustível"},
                {"id": "combustivel_por_maquina", "label": "Consumo por Máquina", "description": "Litros consumidos por máquina"},
                {"id": "veiculos_abastecedores", "label": "Veículos Tanque", "description": "Lista de veículos abastecedores"},
            ]
        },
        {
            "id": "frotas",
            "label": "Frotas",
            "icon": "truck",
            "subcategories": [
                {"id": "frotas", "label": "Todas as Frotas", "description": "Lista completa de frotas"},
                {"id": "frotas_documentos", "label": "Documentos de Frota", "description": "IPVA, licenciamento, seguros"},
            ]
        },
        {
            "id": "operadores",
            "label": "Operadores",
            "icon": "users",
            "subcategories": [
                {"id": "operadores", "label": "Todos os Operadores", "description": "Lista completa de operadores"},
                {"id": "operadores_rh", "label": "Operadores RH", "description": "Funcionários do RH"},
                {"id": "operadores_cadastro", "label": "Operadores Cadastro", "description": "Operadores cadastrados"},
            ]
        },
        {
            "id": "estoque",
            "label": "Estoque",
            "icon": "package",
            "subcategories": [
                {"id": "stock_items", "label": "Itens de Estoque", "description": "Todos os itens cadastrados"},
                {"id": "stock_low", "label": "Estoque Baixo", "description": "Itens abaixo do mínimo"},
                {"id": "stock_categories", "label": "Categorias de Estoque", "description": "Categorias de produtos"},
                {"id": "stock_movements", "label": "Movimentações", "description": "Entradas e saídas"},
                {"id": "stock_movements_entrada", "label": "Entradas de Estoque", "description": "Apenas entradas"},
                {"id": "stock_movements_saida", "label": "Saídas de Estoque", "description": "Apenas saídas"},
            ]
        },
        {
            "id": "obras",
            "label": "Obras e Projetos",
            "icon": "building",
            "subcategories": [
                {"id": "obras", "label": "Todas as Obras", "description": "Lista completa de obras"},
                {"id": "obras_andamento", "label": "Obras em Andamento", "description": "Projetos ativos"},
                {"id": "obras_concluidas", "label": "Obras Concluídas", "description": "Projetos finalizados"},
                {"id": "obras_pausadas", "label": "Obras Pausadas", "description": "Projetos pausados"},
                {"id": "medicoes", "label": "Medições de Obras", "description": "Todas as medições registradas"},
            ]
        },
        {
            "id": "uso",
            "label": "Registros de Uso",
            "icon": "clock",
            "subcategories": [
                {"id": "usage_logs", "label": "Todos os Registros", "description": "Horímetro completo"},
            ]
        },
        {
            "id": "usuarios",
            "label": "Usuários",
            "icon": "users",
            "subcategories": [
                {"id": "users", "label": "Lista de Usuários", "description": "Todos os usuários do sistema"},
            ]
        },
    ],
    "administrativo": [
        {
            "id": "financeiro_pagar",
            "label": "Contas a Pagar",
            "icon": "trending-down",
            "subcategories": [
                {"id": "contas_pagar", "label": "Todas as Contas", "description": "Lista completa"},
                {"id": "contas_pagar_pendente", "label": "Contas Pendentes", "description": "Aguardando pagamento"},
                {"id": "contas_pagar_quitada", "label": "Contas Quitadas", "description": "Já pagas"},
                {"id": "contas_pagar_vencidas", "label": "Contas Vencidas", "description": "Fora do prazo"},
            ]
        },
        {
            "id": "financeiro_receber",
            "label": "Contas a Receber",
            "icon": "trending-up",
            "subcategories": [
                {"id": "contas_receber", "label": "Todas as Contas", "description": "Lista completa"},
                {"id": "contas_receber_pendente", "label": "Contas Pendentes", "description": "Aguardando recebimento"},
                {"id": "contas_receber_quitada", "label": "Contas Recebidas", "description": "Já recebidas"},
                {"id": "contas_receber_vencidas", "label": "Contas Vencidas", "description": "Fora do prazo"},
            ]
        },
        {
            "id": "cadastros",
            "label": "Cadastros",
            "icon": "users",
            "subcategories": [
                {"id": "cadastros", "label": "Todos os Cadastros", "description": "Clientes e fornecedores"},
                {"id": "cadastros_clientes", "label": "Clientes", "description": "Apenas clientes"},
                {"id": "cadastros_fornecedores", "label": "Fornecedores", "description": "Apenas fornecedores"},
            ]
        },
        {
            "id": "produtos",
            "label": "Produtos e Serviços",
            "icon": "package",
            "subcategories": [
                {"id": "produtos_admin", "label": "Todos os Produtos", "description": "Catálogo completo"},
            ]
        },
        {
            "id": "ordens",
            "label": "Ordens de Serviço",
            "icon": "clipboard",
            "subcategories": [
                {"id": "ordens_servico", "label": "Todas as OS", "description": "Lista completa"},
                {"id": "ordens_servico_aberta", "label": "OS Abertas", "description": "Aguardando execução"},
                {"id": "ordens_servico_andamento", "label": "OS em Andamento", "description": "Em execução"},
                {"id": "ordens_servico_concluida", "label": "OS Concluídas", "description": "Finalizadas"},
            ]
        },
        {
            "id": "alugueis",
            "label": "Aluguéis de Máquinas",
            "icon": "truck",
            "subcategories": [
                {"id": "alugueis", "label": "Todos os Aluguéis", "description": "Lista completa"},
                {"id": "alugueis_ativo", "label": "Aluguéis Ativos", "description": "Em andamento"},
                {"id": "alugueis_finalizado", "label": "Aluguéis Finalizados", "description": "Encerrados"},
            ]
        },
        {
            "id": "imoveis_cat",
            "label": "Imóveis para Locação",
            "icon": "building",
            "subcategories": [
                {"id": "imoveis", "label": "Todos os Imóveis", "description": "Lista completa"},
                {"id": "imoveis_ativo", "label": "Imóveis Locados", "description": "Com inquilino"},
                {"id": "imoveis_pendente", "label": "Imóveis Disponíveis", "description": "Sem inquilino"},
            ]
        },
        {
            "id": "contabil",
            "label": "Contabilidade",
            "icon": "dollar",
            "subcategories": [
                {"id": "plano_contas", "label": "Plano de Contas", "description": "Estrutura contábil"},
                {"id": "plano_contas_receita", "label": "Contas de Receita", "description": "Apenas receitas"},
                {"id": "plano_contas_despesa", "label": "Contas de Despesa", "description": "Apenas despesas"},
                {"id": "centros_custo", "label": "Centros de Custo", "description": "Todos os centros"},
                {"id": "formas_pagamento", "label": "Formas de Pagamento", "description": "Métodos de pagamento"},
            ]
        },
        {
            "id": "contas_bancarias_cat",
            "label": "Contas Bancárias",
            "icon": "building",
            "subcategories": [
                {"id": "contas_bancarias", "label": "Todas as Contas", "description": "Lista completa de contas"},
                {"id": "contas_bancarias_ativas", "label": "Contas Ativas", "description": "Apenas contas ativas"},
                {"id": "extrato_bancario", "label": "Extrato Bancário", "description": "Extrato por conta"},
            ]
        },
        {
            "id": "relatorio_conta_bancaria",
            "label": "Relatório por Conta Bancária",
            "icon": "dollar",
            "subcategories": [
                {"id": "rel_conta_bancaria_pagar", "label": "Contas a Pagar por Banco", "description": "Filtre por conta bancária e status"},
                {"id": "rel_conta_bancaria_receber", "label": "Contas a Receber por Banco", "description": "Filtre por conta bancária e status"},
            ]
        },
        {
            "id": "usuarios_admin",
            "label": "Usuários",
            "icon": "users",
            "subcategories": [
                {"id": "users", "label": "Lista de Usuários", "description": "Todos os usuários"},
            ]
        },
    ],
    "rh": [
        {
            "id": "funcionarios_cat",
            "label": "Funcionários",
            "icon": "users",
            "subcategories": [
                {"id": "funcionarios", "label": "Todos os Funcionários", "description": "Lista completa de funcionários"},
                {"id": "funcionarios_ativos", "label": "Funcionários Ativos", "description": "Funcionários em atividade"},
                {"id": "funcionarios_desligados", "label": "Funcionários Desligados", "description": "Ex-funcionários"},
            ]
        },
        {
            "id": "ponto_cat",
            "label": "Registro de Ponto",
            "icon": "clock",
            "subcategories": [
                {"id": "ponto_registros", "label": "Todos os Registros", "description": "Histórico completo de ponto"},
                {"id": "ponto_hoje", "label": "Registros de Hoje", "description": "Ponto do dia atual"},
                {"id": "ponto_mes", "label": "Registros do Mês", "description": "Ponto do mês atual"},
            ]
        },
        {
            "id": "folha_cat",
            "label": "Folha de Pagamento",
            "icon": "dollar",
            "subcategories": [
                {"id": "folha_pagamento", "label": "Folhas de Pagamento", "description": "Todas as folhas geradas"},
                {"id": "holerites", "label": "Holerites", "description": "Demonstrativos de pagamento"},
            ]
        },
        {
            "id": "ferias_cat",
            "label": "Férias",
            "icon": "calendar",
            "subcategories": [
                {"id": "ferias", "label": "Todas as Férias", "description": "Histórico de férias"},
                {"id": "ferias_proximas", "label": "Férias Próximas", "description": "Férias a vencer em 60 dias"},
                {"id": "ferias_vencidas", "label": "Férias Vencidas", "description": "Férias não gozadas"},
            ]
        },
        {
            "id": "epi_cat",
            "label": "EPIs",
            "icon": "hard-hat",
            "subcategories": [
                {"id": "epi_fichas", "label": "Fichas de EPI", "description": "Todas as fichas cadastradas"},
                {"id": "epi_vencidos", "label": "EPIs Vencidos", "description": "EPIs a renovar"},
            ]
        },
        {
            "id": "custos_cat",
            "label": "Custos de RH",
            "icon": "calculator",
            "subcategories": [
                {"id": "custos_funcionarios", "label": "Custo por Funcionário", "description": "Detalhamento de custos"},
                {"id": "custos_encargos", "label": "Encargos Sociais", "description": "INSS, FGTS, etc"},
            ]
        },
    ]
}

@exports_all_router.get("/export/categories/{module}")
async def get_export_categories(module: str, current_user: dict = Depends(get_current_user)):
    """Retorna as categorias disponíveis para exportação"""
    if module not in EXPORT_CATEGORIES_V2:
        raise HTTPException(status_code=400, detail="Módulo inválido")
    return EXPORT_CATEGORIES_V2[module]

async def generate_pdf_report(category: str, data: list, title: str) -> io.BytesIO:
    """Gera um relatório PDF formatado"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.black, alignment=TA_CENTER, spaceAfter=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=30)
    section_style = ParagraphStyle('SectionTitle', parent=styles['Heading2'], fontSize=14, textColor=colors.black, spaceBefore=20, spaceAfter=10)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=colors.black, spaceAfter=5)
    # Estilo para células da tabela com quebra de linha
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, textColor=colors.black, wordWrap='LTR', leading=10)
    header_cell_style = ParagraphStyle('HeaderCellStyle', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', wordWrap='LTR', leading=11)
    
    # Função auxiliar para criar célula com quebra de linha
    def cell(text, is_header=False):
        if text is None:
            text = "-"
        return Paragraph(str(text), header_cell_style if is_header else cell_style)
    
    def fmt_date(val):
        """Converte YYYY-MM-DD para DD/MM/AAAA"""
        if not val:
            return "-"
        s = str(val).strip()[:10]
        if len(s) == 10 and s[4] == '-':
            return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
        return s if s else "-"
    
    def fmt_money(val):
        """Formata valor em R$ X.XXX,XX (padrão brasileiro)"""
        try:
            f = float(val or 0)
            formatted = f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {formatted}"
        except (ValueError, TypeError):
            return "R$ 0,00"
    
    elements = []
    
    # Logo CRA (tentar carregar do arquivo local)
    try:
        logo_path = "/app/frontend/public/logo.png"
        if os.path.exists(logo_path):
            logo = RLImage(logo_path, width=3*cm, height=3*cm, kind='proportional')
            elements.append(logo)
            elements.append(Spacer(1, 10))
    except Exception as e:
        logging.warning(f"Não foi possível carregar o logo: {e}")
    
    # Título
    elements.append(Paragraph(f"CRA Construtora", title_style))
    elements.append(Paragraph(f"Relatório de {title}", section_style))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Resumo
    elements.append(Paragraph(f"Total de registros: {len(data)}", normal_style))
    elements.append(Spacer(1, 20))
    
    if not data:
        elements.append(Paragraph("Nenhum registro encontrado.", normal_style))
    else:
        # Criar tabela com os dados usando Paragraph para quebra de linha
        if category == "machines":
            headers = [cell("Nome", True), cell("Placa", True), cell("Marca", True), cell("Modelo", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                status = "Operacional" if item.get("status") == "operational" else "Em manutenção"
                table_data.append([
                    cell(item.get("name", "-")),
                    cell(item.get("plate", "-")),
                    cell(item.get("brand", "-")),
                    cell(item.get("model", "-")),
                    cell(status)
                ])
        elif category == "maintenances":
            headers = [cell("Equipamento", True), cell("Data", True), cell("Valor", True), cell("Peça", True), cell("Tipo", True), cell("Troca de Óleo", True)]
            table_data = [headers]
            for item in data:
                tipo = "Preventiva" if item.get("maintenance_type") == "preventiva" else "Corretiva"
                table_data.append([
                    cell(item.get("machine_name", "-") or item.get("machine_id", "-")),
                    cell(fmt_date(item.get("replacement_date"))),
                    cell(fmt_money(item.get('part_value', 0))),
                    cell(item.get("part_name", "-")),
                    cell(tipo),
                    cell("Sim" if item.get("is_oil_change") else "Não"),
                ])
        elif category == "stock_items":
            headers = [cell("Nome", True), cell("Código", True), cell("Categoria", True), cell("Qtd", True), cell("Mínimo", True), cell("Preço Un.", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("name", "-")),
                    cell(item.get("code", "-")),
                    cell(item.get("category", "-")),
                    cell(str(item.get("quantity", 0))),
                    cell(str(item.get("min_quantity", 0))),
                    cell(fmt_money(item.get('unit_price', 0)))
                ])
        elif category == "obras":
            headers = [cell("Cliente", True), cell("Data Início", True), cell("Data Fim", True), cell("Nome", True), cell("Local", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                status_map = {"em_andamento": "Em andamento", "concluida": "Concluída", "pausada": "Pausada"}
                table_data.append([
                    cell(item.get("cliente", "-") or item.get("cliente_nome", "-")),
                    cell(fmt_date(item.get("start_date"))),
                    cell(fmt_date(item.get("end_date"))),
                    cell(item.get("name", "-") or item.get("nome", "-")),
                    cell(item.get("location", "-")),
                    cell(status_map.get(item.get("status", ""), item.get("status", "-"))),
                ])
        elif category == "contas_pagar":
            headers = [cell("Fornecedor", True), cell("Vencimento", True), cell("Quitação", True), cell("Valor", True), cell("Descrição", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("fornecedor_nome", "-")),
                    cell(fmt_date(item.get("data_vencimento"))),
                    cell(fmt_date(item.get("data_pagamento"))),
                    cell(fmt_money(item.get('valor', 0))),
                    cell(item.get("descricao", "-")),
                    cell(item.get("status", "-").upper()),
                ])
        elif category == "contas_receber":
            headers = [cell("Cliente", True), cell("Vencimento", True), cell("Recebimento", True), cell("Valor", True), cell("Descrição", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("cliente_nome", "-")),
                    cell(fmt_date(item.get("data_vencimento"))),
                    cell(fmt_date(item.get("data_recebimento"))),
                    cell(fmt_money(item.get('valor', 0))),
                    cell(item.get("descricao", "-")),
                    cell(item.get("status", "-").upper()),
                ])
        elif category == "cadastros":
            headers = [cell("Nome/Razão", True), cell("Tipo", True), cell("CPF/CNPJ", True), cell("Telefone", True), cell("Cidade", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("nome_razao", "-")),
                    cell(item.get("tipo", "-").upper()),
                    cell(item.get("cpf_cnpj", "-")),
                    cell(item.get("telefone", "-")),
                    cell(item.get("cidade", "-"))
                ])
        elif category == "ordens_servico":
            headers = [cell("Cliente", True), cell("Data", True), cell("Valor", True), cell("Nº OS", True), cell("Descrição", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("cliente_nome", "-")),
                    cell(fmt_date(item.get("data_abertura") or item.get("created_at"))),
                    cell(fmt_money(item.get('valor_total', 0))),
                    cell(str(item.get("numero", "-"))),
                    cell(item.get("descricao", "-")),
                    cell(item.get("status", "-").upper()),
                ])
        elif category == "alugueis":
            headers = [cell("Cliente", True), cell("Vencimento", True), cell("Data Entrega", True), cell("Valor", True), cell("Máquina", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("cliente_nome", "-")),
                    cell(fmt_date(item.get("data_vencimento"))),
                    cell(fmt_date(item.get("data_entrega"))),
                    cell(fmt_money(item.get('valor_total', 0))),
                    cell(item.get("maquina_nome", "-")),
                    cell(item.get("status", "-").upper()),
                ])
        elif category == "produtos_admin":
            headers = [cell("Código", True), cell("Descrição", True), cell("Unidade", True), cell("Preço", True), cell("Estoque", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("codigo", "-")),
                    cell(item.get("descricao", "-")),
                    cell(item.get("unidade", "-")),
                    cell(fmt_money(item.get('preco', 0))),
                    cell(str(item.get("estoque", 0)))
                ])
        elif category == "plano_contas":
            headers = [cell("Código", True), cell("Nome", True), cell("Tipo", True), cell("Conta Pai", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("codigo", "-")),
                    cell(item.get("nome", "-")),
                    cell("Receita" if item.get("tipo") == "receita" else "Despesa"),
                    cell(item.get("pai_nome", "Raiz"))
                ])
        elif category == "centros_custo":
            headers = [cell("Código", True), cell("Nome", True), cell("Descrição", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("codigo", "-")),
                    cell(item.get("nome", "-")),
                    cell(item.get("descricao", "-"))
                ])
        elif category == "formas_pagamento":
            headers = [cell("Nome", True), cell("Descrição", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("nome", "-")),
                    cell(item.get("descricao", "-"))
                ])
        elif category == "categories":
            headers = [cell("Nome", True), cell("Descrição", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("name", "-")),
                    cell(item.get("description", "-"))
                ])
        elif category == "stock_movements":
            headers = [cell("Tipo", True), cell("Quantidade", True), cell("Motivo", True), cell("Data", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell("ENTRADA" if item.get("movement_type") == "entrada" else "SAÍDA"),
                    cell(str(item.get("quantity", 0))),
                    cell(item.get("reason", "-")),
                    cell(fmt_date(item.get("created_at")))
                ])
        elif category == "usage_logs":
            headers = [cell("Máquina ID", True), cell("Horas", True), cell("Data", True), cell("Observações", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("machine_id", "-")[:15] if item.get("machine_id") else "-"),
                    cell(str(item.get("hours", 0))),
                    cell(fmt_date(item.get("created_at"))),
                    cell(item.get("notes", "-"))
                ])
        elif category == "users":
            headers = [cell("Nome", True), cell("Email", True), cell("Tipo", True), cell("Criado em", True)]
            table_data = [headers]
            for item in data:
                role_map = {"admin": "Administrador", "gerenciamento": "Gerenciamento", "administrativo": "Administrativo", "ambos": "Ambos"}
                table_data.append([
                    cell(item.get("name", "-")),
                    cell(item.get("email", "-")),
                    cell(role_map.get(item.get("role", ""), item.get("role", "-"))),
                    cell(fmt_date(item.get("created_at")))
                ])
        elif category == "audit_logs":
            headers = [cell("Data", True), cell("Usuário", True), cell("Ação", True), cell("Módulo", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(fmt_date(item.get("created_at"))),
                    cell(item.get("user_name", "-")),
                    cell(item.get("action", "-")),
                    cell(item.get("module", "-"))
                ])
        elif category == "funcionarios":
            headers = [cell("Nome", True), cell("CPF", True), cell("Cargo", True), cell("Admissão", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                status_map = {"ativo": "Ativo", "ferias": "Férias", "afastado": "Afastado", "desligado": "Desligado"}
                table_data.append([
                    cell(item.get("nome", "-")),
                    cell(item.get("cpf", "-")),
                    cell(item.get("cargo", "-")),
                    cell(fmt_date(item.get("data_admissao"))),
                    cell(status_map.get(item.get("status", ""), item.get("status", "-")))
                ])
        elif category == "ponto_registros":
            headers = [cell("Funcionário", True), cell("Data", True), cell("Entrada", True), cell("Saída", True), cell("Horas", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("funcionario_nome", "-")),
                    cell(fmt_date(item.get("data"))),
                    cell(item.get("entrada", "-")),
                    cell(item.get("saida", "-")),
                    cell(item.get("horas_trabalhadas", "-"))
                ])
        elif category == "folha_pagamento":
            headers = [cell("Funcionário", True), cell("Competência", True), cell("Salário Líquido", True), cell("Descontos", True), cell("Salário Bruto", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("funcionario_nome", "-")),
                    cell(item.get("competencia", "-")),
                    cell(fmt_money(item.get('salario_liquido', 0))),
                    cell(fmt_money(item.get('total_descontos', 0))),
                    cell(fmt_money(item.get('salario_bruto', 0))),
                ])
        elif category == "ferias":
            headers = [cell("Funcionário", True), cell("Período Aquisitivo", True), cell("Início", True), cell("Fim", True), cell("Status", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("funcionario_nome", "-")),
                    cell(item.get("periodo_aquisitivo", "-")),
                    cell(fmt_date(item.get("data_inicio"))),
                    cell(fmt_date(item.get("data_fim"))),
                    cell(item.get("status", "-").upper())
                ])
        elif category == "epi_fichas":
            headers = [cell("Funcionário", True), cell("EPI", True), cell("Entrega", True), cell("Validade", True), cell("CA", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("funcionario_nome", "-")),
                    cell(item.get("epi_nome", "-")),
                    cell(fmt_date(item.get("data_entrega"))),
                    cell(fmt_date(item.get("data_validade"))),
                    cell(item.get("ca", "-"))
                ])
        elif category == "contas_bancarias":
            headers = [cell("Nome", True), cell("Banco", True), cell("Agência", True), cell("Conta", True), cell("Saldo", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("nome", "-")),
                    cell(item.get("banco", "-")),
                    cell(item.get("agencia", "-")),
                    cell(item.get("conta", "-")),
                    cell(fmt_money(item.get('saldo_atual', 0)))
                ])
        else:
            # Fallback genérico
            headers = [cell("ID", True), cell("Dados", True)]
            table_data = [headers]
            for item in data:
                table_data.append([
                    cell(item.get("id", "-")[:20] if item.get("id") else "-"),
                    cell(str(item)[:100])
                ])
        
        # Criar e estilizar a tabela - número de colunas baseado no número de headers
        num_cols = len(table_data[0]) if table_data else 5
        col_widths = [doc.width / num_cols] * num_cols
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.89, 0.10, 0.10)),  # Vermelho CRA
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(table)
        
        # Calcular e adicionar total quando houver valores monetários
        total_valor = 0
        campo_valor = None
        
        # Identificar o campo de valor baseado na categoria
        if category in ["contas_pagar", "contas_receber"]:
            campo_valor = "valor_final" if any(item.get("valor_final") for item in data) else "valor"
        elif category == "maintenances":
            campo_valor = "part_value"
        elif category == "ordens_servico":
            campo_valor = "valor_total"
        elif category == "alugueis":
            campo_valor = "valor_total"
        elif category == "stock_items":
            campo_valor = None  # Não somar estoque
        elif category == "folha_pagamento":
            campo_valor = "salario_liquido"
        elif category == "produtos_admin":
            campo_valor = None  # Não somar produtos
        elif category == "contas_bancarias":
            campo_valor = "saldo_atual"
        
        if campo_valor:
            for item in data:
                try:
                    valor = item.get(campo_valor, 0) or 0
                    total_valor += float(valor)
                except (ValueError, TypeError):
                    pass
            
            if total_valor > 0:
                elements.append(Spacer(1, 15))
                total_style = ParagraphStyle('TotalStyle', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', textColor=colors.Color(0.89, 0.10, 0.10))
                
                # Formatação do valor em formato brasileiro
                total_formatado = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                # Criar uma tabela para o total
                total_data = [[cell("TOTAL GERAL:", True), Paragraph(total_formatado, ParagraphStyle('TotalValor', fontSize=12, fontName='Helvetica-Bold', alignment=2))]]
                total_table = Table(total_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
                total_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
                    ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.89, 0.10, 0.10)),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ]))
                elements.append(total_table)
    
    # Rodapé
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph("CRA Construtora - Sistema de Gestão Empresarial", footer_style))
    elements.append(Paragraph(f"Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

@exports_all_router.get("/export/pdf/{category}")
async def export_pdf(
    category: str,
    centro_custo: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    forma_pagamento: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Exporta dados de uma categoria em PDF com filtros (centro de custo + período + forma de pagamento)"""
    
    # Mapear categoria para coleção, título e filtro
    category_configs = {
        # Máquinas
        "machines": {"collection": "machines", "title": "Máquinas", "filter": {}},
        "machines_operational": {"collection": "machines", "title": "Máquinas Operacionais", "filter": {"status": "operational"}},
        "machines_maintenance": {"collection": "machines", "title": "Máquinas em Manutenção", "filter": {"status": "maintenance"}},
        "categories": {"collection": "categories", "title": "Categorias de Máquinas", "filter": {}},
        
        # Manutenções
        "maintenances": {"collection": "maintenances", "title": "Manutenções", "filter": {}},
        "maintenances_preventiva": {"collection": "maintenances", "title": "Manutenções Preventivas", "filter": {"maintenance_type": "preventiva"}},
        "maintenances_corretiva": {"collection": "maintenances", "title": "Manutenções Corretivas", "filter": {"maintenance_type": "corretiva"}},
        "maintenances_oil": {"collection": "maintenances", "title": "Trocas de Óleo", "filter": {"is_oil_change": True}},
        
        # Estoque
        "stock_items": {"collection": "stock_items", "title": "Itens de Estoque", "filter": {}},
        "stock_low": {"collection": "stock_items", "title": "Estoque Baixo", "filter": {"$expr": {"$lte": ["$quantity", "$min_quantity"]}}},
        "stock_categories": {"collection": "stock_categories", "title": "Categorias de Estoque", "filter": {}},
        "stock_movements": {"collection": "stock_movements", "title": "Movimentações de Estoque", "filter": {}},
        "stock_movements_entrada": {"collection": "stock_movements", "title": "Entradas de Estoque", "filter": {"movement_type": "entrada"}},
        "stock_movements_saida": {"collection": "stock_movements", "title": "Saídas de Estoque", "filter": {"movement_type": "saida"}},
        
        # Obras
        "obras": {"collection": "obras", "title": "Obras e Projetos", "filter": {}},
        "obras_andamento": {"collection": "obras", "title": "Obras em Andamento", "filter": {"status": "em_andamento"}},
        "obras_concluidas": {"collection": "obras", "title": "Obras Concluídas", "filter": {"status": "concluida"}},
        "obras_pausadas": {"collection": "obras", "title": "Obras Pausadas", "filter": {"status": "pausada"}},
        
        # Uso
        "usage_logs": {"collection": "usage_logs", "title": "Registros de Uso", "filter": {}},
        
        # Usuários
        "users": {"collection": "users", "title": "Usuários", "filter": {}},
        
        # Auditoria
        "audit_logs": {"collection": "audit_logs", "title": "Logs de Auditoria", "filter": {}},
        
        # Contas a Pagar
        "contas_pagar": {"collection": "contas_pagar", "title": "Contas a Pagar", "filter": {}},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas a Pagar Pendentes", "filter": {"status": "em_aberto"}},
        "contas_pagar_pendentes": {"collection": "contas_pagar", "title": "Contas a Pagar Pendentes", "filter": {"status": "em_aberto"}},
        "contas_pagar_quitada": {"collection": "contas_pagar", "title": "Contas a Pagar Quitadas", "filter": {"status": "quitada"}},
        "contas_pagar_quitadas": {"collection": "contas_pagar", "title": "Contas a Pagar Quitadas", "filter": {"status": "quitada"}},
        "contas_pagar_vencidas": {"collection": "contas_pagar", "title": "Contas a Pagar Vencidas", "filter": {"status": "em_aberto", "data_vencimento": {"$lt": datetime.now().strftime("%Y-%m-%d")}}},
        
        # Contas a Receber
        "contas_receber": {"collection": "contas_receber", "title": "Contas a Receber", "filter": {}},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas a Receber Pendentes", "filter": {"status": "em_aberto"}},
        "contas_receber_pendentes": {"collection": "contas_receber", "title": "Contas a Receber Pendentes", "filter": {"status": "em_aberto"}},
        "contas_receber_quitada": {"collection": "contas_receber", "title": "Contas a Receber Recebidas", "filter": {"status": "quitada"}},
        "contas_receber_quitadas": {"collection": "contas_receber", "title": "Contas a Receber Recebidas", "filter": {"status": "quitada"}},
        "contas_receber_recebidas": {"collection": "contas_receber", "title": "Contas a Receber Recebidas", "filter": {"status": "quitada"}},
        "contas_receber_vencidas": {"collection": "contas_receber", "title": "Contas a Receber Vencidas", "filter": {"status": "em_aberto", "data_vencimento": {"$lt": datetime.now().strftime("%Y-%m-%d")}}},
        
        # Cadastros
        "cadastros": {"collection": "cadastros", "title": "Cadastros", "filter": {}},
        "cadastros_clientes": {"collection": "cadastros", "title": "Clientes", "filter": {"tipo": "cliente"}},
        "cadastros_fornecedores": {"collection": "cadastros", "title": "Fornecedores", "filter": {"tipo": "fornecedor"}},
        
        # Produtos
        "produtos_admin": {"collection": "produtos_admin", "title": "Produtos", "filter": {}},
        
        # Ordens de Serviço
        "ordens_servico": {"collection": "ordens_servico", "title": "Ordens de Serviço", "filter": {}},
        "ordens_servico_aberta": {"collection": "ordens_servico", "title": "OS Abertas", "filter": {"status": "aberta"}},
        "ordens_servico_andamento": {"collection": "ordens_servico", "title": "OS em Andamento", "filter": {"status": "em_andamento"}},
        "ordens_servico_concluida": {"collection": "ordens_servico", "title": "OS Concluídas", "filter": {"status": "concluida"}},
        
        # Aluguéis
        "alugueis": {"collection": "alugueis", "title": "Aluguéis de Máquinas", "filter": {}},
        "alugueis_ativo": {"collection": "alugueis", "title": "Aluguéis Ativos", "filter": {"status": "ativo"}},
        "alugueis_finalizado": {"collection": "alugueis", "title": "Aluguéis Finalizados", "filter": {"status": "finalizado"}},
        
        # Imóveis
        "imoveis": {"collection": "imoveis", "title": "Imóveis para Locação", "filter": {}},
        "imoveis_ativo": {"collection": "imoveis", "title": "Imóveis Locados", "filter": {"status": "ativo"}},
        "imoveis_pendente": {"collection": "imoveis", "title": "Imóveis Disponíveis", "filter": {"status": "pendente"}},
        
        # Contabilidade
        "plano_contas": {"collection": "plano_contas", "title": "Plano de Contas", "filter": {}},
        "plano_contas_receita": {"collection": "plano_contas", "title": "Contas de Receita", "filter": {"tipo": "receita"}},
        "plano_contas_despesa": {"collection": "plano_contas", "title": "Contas de Despesa", "filter": {"tipo": "despesa"}},
        "centros_custo": {"collection": "centros_custo", "title": "Centros de Custo", "filter": {}},
        "formas_pagamento": {"collection": "formas_pagamento", "title": "Formas de Pagamento", "filter": {}},
        
        # Contas Bancárias
        "contas_bancarias": {"collection": "contas_bancarias", "title": "Contas Bancárias", "filter": {}},
        "contas_bancarias_ativas": {"collection": "contas_bancarias", "title": "Contas Bancárias Ativas", "filter": {"ativo": True}},
        
        # RH - Funcionários
        "funcionarios": {"collection": "funcionarios", "title": "Funcionários", "filter": {}},
        "funcionarios_ativos": {"collection": "funcionarios", "title": "Funcionários Ativos", "filter": {"status": {"$ne": "desligado"}}},
        "funcionarios_desligados": {"collection": "funcionarios", "title": "Funcionários Desligados", "filter": {"status": "desligado"}},
        
        # RH - Ponto
        "ponto_registros": {"collection": "ponto_registros", "title": "Registros de Ponto", "filter": {}},
        "ponto_hoje": {"collection": "ponto_registros", "title": "Ponto de Hoje", "filter": {"data": datetime.now().strftime("%Y-%m-%d")}},
        "ponto_mes": {"collection": "ponto_registros", "title": "Ponto do Mês", "filter": {"data": {"$regex": f"^{datetime.now().strftime('%Y-%m')}"}}},
        
        # RH - Folha de Pagamento
        "folha_pagamento": {"collection": "folha_pagamento", "title": "Folha de Pagamento", "filter": {}},
        "holerites": {"collection": "folha_pagamento", "title": "Holerites", "filter": {}},
        
        # RH - Férias
        "ferias": {"collection": "ferias", "title": "Férias", "filter": {}},
        "ferias_proximas": {"collection": "ferias", "title": "Férias Próximas", "filter": {}},
        "ferias_vencidas": {"collection": "ferias", "title": "Férias Vencidas", "filter": {}},
        
        # RH - EPIs
        "epi_fichas": {"collection": "epi_fichas", "title": "Fichas de EPI", "filter": {}},
        "epi_vencidos": {"collection": "epi_fichas", "title": "EPIs Vencidos", "filter": {}},
        
        # RH - Custos
        "custos_funcionarios": {"collection": "funcionarios", "title": "Custos por Funcionário", "filter": {}},
        "custos_encargos": {"collection": "folha_pagamento", "title": "Encargos Sociais", "filter": {}},
    }
    
    if category not in category_configs:
        raise HTTPException(status_code=400, detail=f"Categoria '{category}' inválida")
    
    config = category_configs[category]
    collection_name = config["collection"]
    title = config["title"]
    query_filter = dict(config["filter"])  # Cópia para não mutar o original
    
    # Aplicar filtro de centro de custo para coleções financeiras
    FINANCIAL_COLLECTIONS = ["contas_pagar", "contas_receber"]
    if centro_custo and centro_custo != "todos" and collection_name in FINANCIAL_COLLECTIONS:
        query_filter["centro_custo"] = centro_custo
        title += f" - {centro_custo}"

    # Aplicar filtro de período (global)
    query_filter = _apply_period_filter(collection_name, query_filter, data_inicio, data_fim)
    if data_inicio or data_fim:
        title += f" ({data_inicio or '...'} a {data_fim or '...'})"

    # Aplicar filtro de forma de pagamento (apenas contas_pagar/receber)
    query_filter = _apply_forma_pagamento_filter(collection_name, query_filter, forma_pagamento)
    if forma_pagamento and forma_pagamento.lower() != "todas" and collection_name in ("contas_pagar", "contas_receber"):
        title += f" - Forma: {forma_pagamento}"
    
    # Buscar dados com filtro
    collection = db[collection_name]
    
    # Para usuários, não expor senha
    projection = {"_id": 0}
    if collection_name == "users":
        projection["password"] = 0
    
    data = await collection.find(query_filter, projection).to_list(1000)
    
    # Usar o nome base da coleção para formatação da tabela
    base_category = collection_name
    if base_category == "stock_categories":
        base_category = "categories"
    
    # Gerar PDF
    pdf_buffer = await generate_pdf_report(base_category, data, title)
    
    # Registrar na auditoria
    await create_audit_log(
        user=current_user,
        action="exportar",
        entity_type="relatório PDF",
        entity_id=category,
        entity_name=title,
        details=f"Exportou {len(data)} registros",
        module="Exportação"
    )
    
    # Retornar o PDF
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=CRA_{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        }
    )

# Endpoint para exportação combinada de múltiplas categorias
class CombinedExportRequest(BaseModel):
    categories: list[str]
    format: str = "pdf"  # pdf, excel
    filters: Optional[dict] = None  # Filtros específicos por ID
    centro_custo: Optional[str] = None  # Filtro por centro de custo
    data_inicio: Optional[str] = None  # YYYY-MM-DD (filtro global de período)
    data_fim: Optional[str] = None     # YYYY-MM-DD
    forma_pagamento: Optional[str] = None  # ex.: "PIX", "boleto" ou "todas"

@exports_all_router.post("/export/combined")
async def export_combined(data: CombinedExportRequest, current_user: dict = Depends(get_current_user)):
    """Exporta múltiplas categorias em um único arquivo"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    category_configs = {
        "machines": {"collection": "machines", "title": "Máquinas", "filter": {}},
        "machines_operational": {"collection": "machines", "title": "Máquinas Operacionais", "filter": {"status": "operational"}},
        "machines_maintenance": {"collection": "machines", "title": "Máquinas em Manutenção", "filter": {"status": "maintenance"}},
        "categories": {"collection": "categories", "title": "Categorias de Máquinas", "filter": {}},
        "maintenances": {"collection": "maintenances", "title": "Manutenções", "filter": {}},
        "stock_items": {"collection": "stock_items", "title": "Itens de Estoque", "filter": {}},
        "obras": {"collection": "obras", "title": "Obras e Projetos", "filter": {}},
        "contas_pagar": {"collection": "contas_pagar", "title": "Contas a Pagar", "filter": {}},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas a Pagar Pendentes", "filter": {"status": "em_aberto"}},
        "contas_pagar_quitada": {"collection": "contas_pagar", "title": "Contas a Pagar Quitadas", "filter": {"status": "quitada"}},
        "contas_receber": {"collection": "contas_receber", "title": "Contas a Receber", "filter": {}},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas a Receber Pendentes", "filter": {"status": "em_aberto"}},
        "contas_receber_quitada": {"collection": "contas_receber", "title": "Contas a Receber Recebidas", "filter": {"status": "quitada"}},
        "cadastros": {"collection": "cadastros", "title": "Cadastros", "filter": {}},
        "produtos_admin": {"collection": "produtos_admin", "title": "Produtos", "filter": {}},
        "ordens_servico": {"collection": "ordens_servico", "title": "Ordens de Serviço", "filter": {}},
        "alugueis": {"collection": "alugueis", "title": "Aluguéis de Máquinas", "filter": {}},
        "plano_contas": {"collection": "plano_contas", "title": "Plano de Contas", "filter": {}},
        "centros_custo": {"collection": "centros_custo", "title": "Centros de Custo", "filter": {}},
        "formas_pagamento": {"collection": "formas_pagamento", "title": "Formas de Pagamento", "filter": {}},
        "fleets": {"collection": "fleets", "title": "Frotas", "filter": {}},
    }
    
    all_data = []
    for cat_id in data.categories:
        if cat_id not in category_configs:
            continue
        
        config = category_configs[cat_id]
        query_filter = config["filter"].copy()
        
        # Aplicar filtros específicos se fornecidos
        if data.filters and cat_id in data.filters:
            specific_filter = data.filters[cat_id]
            if "id" in specific_filter:
                query_filter["id"] = specific_filter["id"]
            if "ids" in specific_filter:
                query_filter["id"] = {"$in": specific_filter["ids"]}
        
        # Aplicar filtro de centro de custo para coleções financeiras
        FINANCIAL_COLLECTIONS = ["contas_pagar", "contas_receber"]
        if data.centro_custo and data.centro_custo != "todos" and config["collection"] in FINANCIAL_COLLECTIONS:
            query_filter["centro_custo"] = data.centro_custo

        # Aplicar filtro global de período
        query_filter = _apply_period_filter(
            config["collection"], query_filter, data.data_inicio, data.data_fim
        )

        # Aplicar filtro global de forma de pagamento
        query_filter = _apply_forma_pagamento_filter(
            config["collection"], query_filter, data.forma_pagamento
        )

        items = await db[config["collection"]].find(query_filter, {"_id": 0}).to_list(1000)
        if items:
            section_title = config["title"]
            if data.centro_custo and data.centro_custo != "todos" and config["collection"] in FINANCIAL_COLLECTIONS:
                section_title += f" - {data.centro_custo}"
            if data.data_inicio or data.data_fim:
                section_title += f" ({data.data_inicio or '...'} a {data.data_fim or '...'})"
            if data.forma_pagamento and data.forma_pagamento.lower() != "todas" and config["collection"] in ("contas_pagar", "contas_receber"):
                section_title += f" - {data.forma_pagamento}"
            all_data.append({
                "title": section_title,
                "items": items,
                "category": cat_id
            })
    
    if not all_data:
        raise HTTPException(status_code=400, detail="Nenhum dado encontrado para exportar")
    
    # Gerar PDF de cada seção usando generate_pdf_report (com colunas corretas)
    # e depois mesclar com PyPDF2
    from PyPDF2 import PdfWriter, PdfReader as PyPDFReader
    
    # Normalizar categoria para o mapeamento do generate_pdf_report
    CATEGORY_NORMALIZE = {
        "contas_pagar_pendente": "contas_pagar",
        "contas_pagar_quitadas": "contas_pagar",
        "contas_pagar_vencidas": "contas_pagar",
        "contas_receber_pendente": "contas_receber",
        "contas_receber_recebidas": "contas_receber",
        "contas_receber_vencidas": "contas_receber",
        "cadastros_clientes": "cadastros",
        "cadastros_fornecedores": "cadastros",
    }
    
    writer = PdfWriter()
    for section in all_data:
        base_cat = CATEGORY_NORMALIZE.get(section["category"], section["category"])
        section_buffer = await generate_pdf_report(
            base_cat,
            section["items"],
            section["title"]
        )
        reader = PyPDFReader(section_buffer)
        for page in reader.pages:
            writer.add_page(page)
    
    merged_buffer = io.BytesIO()
    writer.write(merged_buffer)
    merged_buffer.seek(0)
    
    return StreamingResponse(
        merged_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=CRA_Relatorio_Combinado_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        }
    )

# Endpoint para listar itens específicos para filtro de exportação
@exports_all_router.get("/export/items/{collection}")
async def get_export_items(
    collection: str,
    status: str = None,
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Retorna itens de uma coleção para seleção em exportação.
    Aceita filtro de período opcional (data_inicio/data_fim em YYYY-MM-DD) — quando passado,
    filtra pelo campo de data principal da coleção (ex.: data_vencimento p/ contas)."""
    valid_collections = {
        "plano_contas": {"name_field": "nome", "id_field": "id", "collection": "plano_contas"},
        "centros_custo": {"name_field": "nome", "id_field": "id", "collection": "centros_custo"},
        "fleets": {"name_field": "name", "id_field": "id", "collection": "fleets"},
        "cadastros": {"name_field": "nome", "id_field": "id", "collection": "cadastros"},
        "formas_pagamento": {"name_field": "nome", "id_field": "id", "collection": "formas_pagamento"},
        "contas_bancarias": {"name_field": "nome", "id_field": "id", "collection": "contas_bancarias"},
        # Contas a Pagar
        "contas_pagar": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "extra_fields": ["valor", "data_vencimento", "fornecedor_nome", "numero_doc"]},
        "contas_pagar_pendente": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "fornecedor_nome", "numero_doc"]},
        "contas_pagar_quitadas": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "filter": {"status": "quitada"}, "extra_fields": ["valor", "data_vencimento", "fornecedor_nome", "numero_doc"]},
        "contas_pagar_vencidas": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "fornecedor_nome", "numero_doc"], "vencidas": True},
        # Contas a Receber
        "contas_receber": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "extra_fields": ["valor", "data_vencimento", "cliente_nome", "numero_doc"]},
        "contas_receber_pendente": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "cliente_nome", "numero_doc"]},
        "contas_receber_recebidas": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "filter": {"status": "quitada"}, "extra_fields": ["valor", "data_vencimento", "cliente_nome", "numero_doc"]},
        "contas_receber_vencidas": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "cliente_nome", "numero_doc"], "vencidas": True},
        # Outras
        "machines": {"name_field": "name", "id_field": "id", "collection": "machines", "extra_fields": ["model", "plate"]},
        "maintenances": {"name_field": "description", "id_field": "id", "collection": "maintenances", "extra_fields": ["machine_name", "date"]},
        "stock_items": {"name_field": "name", "id_field": "id", "collection": "stock_items", "extra_fields": ["quantity", "category"]},
        "obras": {"name_field": "nome", "id_field": "id", "collection": "obras", "extra_fields": ["cliente", "status"]},
        "alugueis": {"name_field": "descricao", "id_field": "id", "collection": "alugueis", "extra_fields": ["valor", "data_inicio"]},
        "imoveis": {"name_field": "descricao", "id_field": "id", "collection": "imoveis", "extra_fields": ["valor_aluguel", "endereco", "cliente_nome"]},
        "usuarios": {"name_field": "name", "id_field": "id", "collection": "users", "extra_fields": ["email", "role"]},
    }
    
    if collection not in valid_collections:
        raise HTTPException(status_code=400, detail="Coleção inválida")
    
    config = valid_collections[collection]
    db_collection = config.get("collection", collection)
    query_filter = config.get("filter", {})
    
    # Se precisa filtrar vencidas
    if config.get("vencidas"):
        hoje = datetime.now().strftime("%Y-%m-%d")
        query_filter["data_vencimento"] = {"$lt": hoje}

    # Aplicar filtro de período (global) sobre o campo de data principal da coleção
    query_filter = _apply_period_filter(db_collection, query_filter, data_inicio, data_fim)

    projection = {"_id": 0, config["id_field"]: 1, config["name_field"]: 1}
    for field in config.get("extra_fields", []):
        projection[field] = 1
    
    items = await db[db_collection].find(query_filter, projection).to_list(500)
    
    result = []
    for item in items:
        entry = {
            "id": item.get(config["id_field"]),
            "name": item.get(config["name_field"], "Sem descrição")
        }
        # Adicionar campos extras para exibição
        for field in config.get("extra_fields", []):
            entry[field] = item.get(field)
        result.append(entry)
    
    return result


# ============ CONTAGEM EM MASSA DE ITENS POR COLEÇÃO (com filtro de período) ============
# Mesma config compartilhada — espelha o que está em get_export_items para resolver "vencidas",
# filtros estáticos e o campo de data principal de cada coleção.
_EXPORT_ITEMS_CONFIG = {
    "plano_contas": {"collection": "plano_contas"},
    "centros_custo": {"collection": "centros_custo"},
    "fleets": {"collection": "fleets"},
    "cadastros": {"collection": "cadastros"},
    "formas_pagamento": {"collection": "formas_pagamento"},
    "contas_bancarias": {"collection": "contas_bancarias"},
    "contas_pagar": {"collection": "contas_pagar"},
    "contas_pagar_pendente": {"collection": "contas_pagar", "filter": {"status": "em_aberto"}},
    "contas_pagar_quitadas": {"collection": "contas_pagar", "filter": {"status": "quitada"}},
    "contas_pagar_vencidas": {"collection": "contas_pagar", "filter": {"status": "em_aberto"}, "vencidas": True},
    "contas_receber": {"collection": "contas_receber"},
    "contas_receber_pendente": {"collection": "contas_receber", "filter": {"status": "em_aberto"}},
    "contas_receber_recebidas": {"collection": "contas_receber", "filter": {"status": "quitada"}},
    "contas_receber_vencidas": {"collection": "contas_receber", "filter": {"status": "em_aberto"}, "vencidas": True},
    "machines": {"collection": "machines"},
    "maintenances": {"collection": "maintenances"},
    "stock_items": {"collection": "stock_items"},
    "obras": {"collection": "obras"},
    "alugueis": {"collection": "alugueis"},
    "imoveis": {"collection": "imoveis"},
    "imoveis_ativo": {"collection": "imoveis", "filter": {"status": "ativo"}},
    "imoveis_pendente": {"collection": "imoveis", "filter": {"status": "pendente"}},
    "usuarios": {"collection": "users"},
    "extrato_bancario": {"collection": "contas_bancarias"},
}


@exports_all_router.get("/export/items-count")
async def get_export_items_count(
    collections: str = Query(..., description="Lista de subcategorias separadas por vírgula"),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Retorna a contagem de itens de várias subcategorias em uma única chamada,
    aplicando o mesmo filtro de período que `/export/items/{collection}`.
    Body de resposta: { "<subcategoria>": <int>, ... }. Subcategorias inválidas/inexistentes
    saem com -1 (UI ignora ou esconde)."""
    ids = [s.strip() for s in (collections or "").split(",") if s.strip()]
    if not ids:
        return {}

    out: dict = {}
    for sub_id in ids:
        cfg = _EXPORT_ITEMS_CONFIG.get(sub_id)
        if not cfg:
            out[sub_id] = -1
            continue
        db_collection = cfg["collection"]
        query_filter = dict(cfg.get("filter") or {})
        if cfg.get("vencidas"):
            hoje = datetime.now().strftime("%Y-%m-%d")
            existing = query_filter.get("data_vencimento") or {}
            if isinstance(existing, dict):
                existing.update({"$lt": hoje})
                query_filter["data_vencimento"] = existing
            else:
                query_filter["data_vencimento"] = {"$lt": hoje}
        query_filter = _apply_period_filter(db_collection, query_filter, data_inicio, data_fim)
        try:
            count = await db[db_collection].count_documents(query_filter)
        except Exception:
            count = -1
        out[sub_id] = count
    return out


@exports_all_router.get("/export/individual/{category}/{item_id}")
async def export_individual_item(category: str, item_id: str, current_user: dict = Depends(get_current_user)):
    """Exporta um item individual em PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    import io
    
    # Mapeamento de categorias para coleções
    category_config = {
        "contas_pagar": {"collection": "contas_pagar", "title": "Conta a Pagar"},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Conta a Pagar (Pendente)"},
        "contas_pagar_quitadas": {"collection": "contas_pagar", "title": "Conta a Pagar (Quitada)"},
        "contas_pagar_vencidas": {"collection": "contas_pagar", "title": "Conta a Pagar (Vencida)"},
        "contas_receber": {"collection": "contas_receber", "title": "Conta a Receber"},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Conta a Receber (Pendente)"},
        "contas_receber_recebidas": {"collection": "contas_receber", "title": "Conta a Receber (Recebida)"},
        "contas_receber_vencidas": {"collection": "contas_receber", "title": "Conta a Receber (Vencida)"},
        "machines": {"collection": "machines", "title": "Máquina"},
        "maintenances": {"collection": "maintenances", "title": "Manutenção"},
        "stock_items": {"collection": "stock_items", "title": "Item de Estoque"},
        "obras": {"collection": "obras", "title": "Obra"},
        "alugueis": {"collection": "alugueis", "title": "Aluguel de Máquina"},
        "imoveis": {"collection": "imoveis", "title": "Imóvel"},
        "plano_contas": {"collection": "plano_contas", "title": "Plano de Contas"},
        "centros_custo": {"collection": "centros_custo", "title": "Centro de Custo"},
        "cadastros": {"collection": "cadastros", "title": "Cadastro"},
        "contas_bancarias": {"collection": "contas_bancarias", "title": "Conta Bancária"},
    }
    
    if category not in category_config:
        raise HTTPException(status_code=400, detail="Categoria inválida")
    
    config = category_config[category]
    item = await db[config["collection"]].find_one({"id": item_id}, {"_id": 0})
    
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Função auxiliar para formatar valor
    def fmt_valor(v):
        if v is None or v == "":
            return "-"
        try:
            return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return str(v)
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=15, textColor=colors.HexColor("#1a1a1a"))
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=9, textColor=colors.gray, spaceAfter=15)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=11, spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#D4A000"))
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=8, textColor=colors.gray, wordWrap='LTR')
    value_style = ParagraphStyle('Value', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#1a1a1a"), wordWrap='LTR', leading=12)
    
    elements = []
    
    # Logo
    try:
        logo_path = "/app/frontend/public/logo.png"
        if os.path.exists(logo_path):
            logo = RLImage(logo_path, width=2.5*cm, height=2.5*cm, kind='proportional')
            elements.append(logo)
            elements.append(Spacer(1, 0.3*cm))
    except:
        pass
    
    # Título
    elements.append(Paragraph(config["title"], title_style))
    elements.append(Paragraph(f"Exportado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    
    # Campos específicos por tipo
    if "contas_pagar" in category or "contas_receber" in category:
        is_pagar = "contas_pagar" in category
        pessoa_label = "Fornecedor" if is_pagar else "Cliente"
        pessoa_nome = item.get("fornecedor_nome" if is_pagar else "cliente_nome", "-")
        pessoa_doc = item.get("fornecedor_cnpj" if is_pagar else "cliente_documento", "-")
        
        # Seção: Identificação
        elements.append(Paragraph("IDENTIFICAÇÃO", section_style))
        id_data = [
            [Paragraph("Nº Documento:", label_style), Paragraph(item.get("numero_documento", item.get("id", "-")[:12]), value_style),
             Paragraph("Conta Movimento:", label_style), Paragraph(item.get("conta_bancaria_nome", "-"), value_style)],
            [Paragraph(f"{pessoa_label}:", label_style), Paragraph(pessoa_nome, value_style),
             Paragraph("CPF/CNPJ:", label_style), Paragraph(pessoa_doc, value_style)],
        ]
        id_table = Table(id_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        id_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(id_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # Seção: Descrição
        elements.append(Paragraph("DESCRIÇÃO", section_style))
        desc_text = item.get("descricao", "-")
        desc_table = Table([[Paragraph(desc_text, value_style)]], colWidths=[18*cm])
        desc_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(desc_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # Seção: Datas
        elements.append(Paragraph("DATAS", section_style))
        data_emissao = item.get("data_emissao", item.get("created_at", "-")[:10] if item.get("created_at") else "-")
        data_venc = item.get("data_vencimento", "-")
        data_pag = item.get("data_pagamento" if is_pagar else "data_recebimento", "-")
        dates_data = [
            [Paragraph("Data Emissão:", label_style), Paragraph(data_emissao, value_style),
             Paragraph("Data Vencimento:", label_style), Paragraph(data_venc, value_style),
             Paragraph("Data Pagamento:" if is_pagar else "Data Recebimento:", label_style), Paragraph(data_pag if data_pag else "-", value_style)],
        ]
        dates_table = Table(dates_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm, 3*cm, 3*cm])
        dates_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (4, 0), (4, -1), colors.HexColor("#f8f8f8")),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ]))
        elements.append(dates_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # Seção: Classificação
        elements.append(Paragraph("CLASSIFICAÇÃO", section_style))
        class_data = [
            [Paragraph("Plano de Contas:", label_style), Paragraph(item.get("plano_contas_nome", "-"), value_style),
             Paragraph("Subconta:", label_style), Paragraph(item.get("subconta_nome", "-"), value_style)],
            [Paragraph("Centro de Custo:", label_style), Paragraph(item.get("centro_custo_nome", "-"), value_style),
             Paragraph("Frota:", label_style), Paragraph(item.get("fleet_nome", "-"), value_style)],
            [Paragraph("Forma Pagamento:", label_style), Paragraph(item.get("forma_pagamento_nome", "-"), value_style),
             Paragraph("Conta Bancária:", label_style), Paragraph(item.get("conta_bancaria_nome", "-"), value_style)],
        ]
        class_table = Table(class_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        class_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(class_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # Seção: Valores
        elements.append(Paragraph("VALORES", section_style))
        valor = float(item.get("valor", 0) or 0)
        desconto = float(item.get("desconto", 0) or 0)
        multa = float(item.get("multa", 0) or 0)
        juros = float(item.get("juros", 0) or 0)
        valor_final = float(item.get("valor_final", valor) or valor)
        
        valores_data = [
            [Paragraph("Valor Original:", label_style), Paragraph(fmt_valor(valor), value_style),
             Paragraph("Desconto:", label_style), Paragraph(fmt_valor(desconto), value_style)],
            [Paragraph("Multa:", label_style), Paragraph(fmt_valor(multa), value_style),
             Paragraph("Juros:", label_style), Paragraph(fmt_valor(juros), value_style)],
        ]
        valores_table = Table(valores_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        valores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ]))
        elements.append(valores_table)
        
        # Total
        total_data = [[Paragraph("VALOR TOTAL:", ParagraphStyle('TotalLabel', fontSize=10, textColor=colors.white)), 
                       Paragraph(fmt_valor(valor_final), ParagraphStyle('TotalValue', fontSize=12, textColor=colors.white))]]
        total_table = Table(total_data, colWidths=[9*cm, 9*cm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#D4A000")),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # Seção: Observações
        obs = item.get("observacoes", "")
        if obs:
            elements.append(Paragraph("OBSERVAÇÕES", section_style))
            obs_table = Table([[Paragraph(obs, value_style)]], colWidths=[18*cm])
            obs_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(obs_table)
        
        # Status
        status = item.get("status", "em_aberto")
        status_text = "QUITADA" if status == "quitada" else "EM ABERTO"
        status_color = colors.HexColor("#28a745") if status == "quitada" else colors.HexColor("#dc3545")
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(f"<b>Status: {status_text}</b>", ParagraphStyle('Status', fontSize=12, alignment=1, textColor=status_color)))
        
    elif category == "machines":
        table_data = [
            [Paragraph("Nome:", label_style), Paragraph(item.get("name", "-"), value_style)],
            [Paragraph("Modelo:", label_style), Paragraph(item.get("model", "-"), value_style)],
            [Paragraph("Placa:", label_style), Paragraph(item.get("plate", "-"), value_style)],
            [Paragraph("Categoria:", label_style), Paragraph(item.get("category", "-"), value_style)],
            [Paragraph("Ano:", label_style), Paragraph(str(item.get("year", "-")), value_style)],
            [Paragraph("Horímetro:", label_style), Paragraph(str(item.get("horimeter", "-")), value_style)],
            [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style)],
            [Paragraph("Frota:", label_style), Paragraph(item.get("fleet_name", "-"), value_style)],
            [Paragraph("Observações:", label_style), Paragraph(item.get("observations", "-"), value_style)],
        ]
        table = Table(table_data, colWidths=[4*cm, 14*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(table)
        
    elif category == "maintenances":
        table_data = [
            [Paragraph("Descrição:", label_style), Paragraph(item.get("description", "-"), value_style)],
            [Paragraph("Máquina:", label_style), Paragraph(item.get("machine_name", "-"), value_style)],
            [Paragraph("Data:", label_style), Paragraph(item.get("date", "-"), value_style)],
            [Paragraph("Tipo:", label_style), Paragraph(item.get("type", "-"), value_style)],
            [Paragraph("Custo:", label_style), Paragraph(fmt_valor(item.get("cost", 0)), value_style)],
            [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style)],
            [Paragraph("Mecânico:", label_style), Paragraph(item.get("mechanic", "-"), value_style)],
            [Paragraph("Observações:", label_style), Paragraph(item.get("observations", "-"), value_style)],
        ]
        table = Table(table_data, colWidths=[4*cm, 14*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(table)
    
    elif category == "plano_contas":
        # Informações do plano de contas
        elements.append(Paragraph("DADOS DO PLANO DE CONTAS", section_style))
        info_data = [
            [Paragraph("Código:", label_style), Paragraph(item.get("codigo", "-"), value_style),
             Paragraph("Nome:", label_style), Paragraph(item.get("nome", "-"), value_style)],
            [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style),
             Paragraph("Natureza:", label_style), Paragraph(item.get("natureza", "-"), value_style)],
            [Paragraph("Conta Pai:", label_style), Paragraph(item.get("conta_pai_nome", "-"), value_style),
             Paragraph("Status:", label_style), Paragraph("Ativo" if item.get("ativo", True) else "Inativo", value_style)],
        ]
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Buscar contas a pagar e receber vinculadas a este plano
        plano_id = item.get("id")
        plano_nome = item.get("nome", "")
        
        # Contas a Pagar
        contas_pagar = await db["contas_pagar"].find(
            {"$or": [{"plano_conta_id": plano_id}, {"plano_conta_nome": plano_nome}]}, 
            {"_id": 0}
        ).to_list(500)
        
        # Contas a Receber
        contas_receber = await db["contas_receber"].find(
            {"$or": [{"plano_conta_id": plano_id}, {"plano_conta_nome": plano_nome}]}, 
            {"_id": 0}
        ).to_list(500)
        
        # Tabela de Contas a Pagar vinculadas
        if contas_pagar:
            elements.append(Paragraph("CONTAS A PAGAR VINCULADAS", section_style))
            pagar_headers = [
                Paragraph("<b>Descrição</b>", label_style),
                Paragraph("<b>Fornecedor</b>", label_style),
                Paragraph("<b>Vencimento</b>", label_style),
                Paragraph("<b>Valor</b>", label_style),
                Paragraph("<b>Status</b>", label_style)
            ]
            pagar_data = [pagar_headers]
            total_pagar = 0
            for cp in contas_pagar:
                valor = float(cp.get("valor_final") or cp.get("valor", 0) or 0)
                total_pagar += valor
                status = "Quitada" if cp.get("status") == "quitada" else "Em Aberto"
                pagar_data.append([
                    Paragraph(cp.get("descricao", "-")[:40], value_style),
                    Paragraph((cp.get("fornecedor_nome", "-") or "-")[:25], value_style),
                    Paragraph(cp.get("data_vencimento", "-"), value_style),
                    Paragraph(fmt_valor(valor), value_style),
                    Paragraph(status, value_style)
                ])
            # Total
            pagar_data.append([
                Paragraph("", value_style),
                Paragraph("<b>TOTAL</b>", value_style),
                Paragraph("", value_style),
                Paragraph(f"<b>{fmt_valor(total_pagar)}</b>", value_style),
                Paragraph("", value_style)
            ])
            pagar_table = Table(pagar_data, colWidths=[5*cm, 4*cm, 2.5*cm, 3*cm, 2.5*cm])
            pagar_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#dc3545")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f5f5f5")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(pagar_table)
            elements.append(Spacer(1, 0.4*cm))
        
        # Tabela de Contas a Receber vinculadas
        if contas_receber:
            elements.append(Paragraph("CONTAS A RECEBER VINCULADAS", section_style))
            receber_headers = [
                Paragraph("<b>Descrição</b>", label_style),
                Paragraph("<b>Cliente</b>", label_style),
                Paragraph("<b>Vencimento</b>", label_style),
                Paragraph("<b>Valor</b>", label_style),
                Paragraph("<b>Status</b>", label_style)
            ]
            receber_data = [receber_headers]
            total_receber = 0
            for cr in contas_receber:
                valor = float(cr.get("valor_final") or cr.get("valor", 0) or 0)
                total_receber += valor
                status = "Recebida" if cr.get("status") == "recebida" else "Em Aberto"
                receber_data.append([
                    Paragraph(cr.get("descricao", "-")[:40], value_style),
                    Paragraph((cr.get("cliente_nome", "-") or "-")[:25], value_style),
                    Paragraph(cr.get("data_vencimento", "-"), value_style),
                    Paragraph(fmt_valor(valor), value_style),
                    Paragraph(status, value_style)
                ])
            # Total
            receber_data.append([
                Paragraph("", value_style),
                Paragraph("<b>TOTAL</b>", value_style),
                Paragraph("", value_style),
                Paragraph(f"<b>{fmt_valor(total_receber)}</b>", value_style),
                Paragraph("", value_style)
            ])
            receber_table = Table(receber_data, colWidths=[5*cm, 4*cm, 2.5*cm, 3*cm, 2.5*cm])
            receber_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#28a745")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f5f5f5")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(receber_table)
            elements.append(Spacer(1, 0.4*cm))
        
        # Resumo
        if contas_pagar or contas_receber:
            total_pagar = sum(float(cp.get("valor_final") or cp.get("valor", 0) or 0) for cp in contas_pagar)
            total_receber = sum(float(cr.get("valor_final") or cr.get("valor", 0) or 0) for cr in contas_receber)
            saldo = total_receber - total_pagar
            
            elements.append(Paragraph("RESUMO FINANCEIRO", section_style))
            resumo_data = [
                [Paragraph("Total a Pagar:", label_style), Paragraph(fmt_valor(total_pagar), ParagraphStyle('VP', fontSize=10, textColor=colors.HexColor("#dc3545")))],
                [Paragraph("Total a Receber:", label_style), Paragraph(fmt_valor(total_receber), ParagraphStyle('VR', fontSize=10, textColor=colors.HexColor("#28a745")))],
                [Paragraph("<b>Saldo:</b>", label_style), Paragraph(f"<b>{fmt_valor(saldo)}</b>", ParagraphStyle('VS', fontSize=11, textColor=colors.HexColor("#28a745") if saldo >= 0 else colors.HexColor("#dc3545")))],
            ]
            resumo_table = Table(resumo_data, colWidths=[4*cm, 6*cm])
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(resumo_table)
        else:
            elements.append(Paragraph("Nenhuma conta vinculada a este plano de contas.", value_style))
    
    elif category == "centros_custo":
        # Informações do centro de custo
        elements.append(Paragraph("DADOS DO CENTRO DE CUSTO", section_style))
        info_data = [
            [Paragraph("Código:", label_style), Paragraph(item.get("codigo", "-"), value_style)],
            [Paragraph("Nome:", label_style), Paragraph(item.get("nome", "-"), value_style)],
            [Paragraph("Descrição:", label_style), Paragraph(item.get("descricao", "-"), value_style)],
            [Paragraph("Status:", label_style), Paragraph("Ativo" if item.get("ativo", True) else "Inativo", value_style)],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 14*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Buscar contas vinculadas a este centro de custo
        centro_nome = item.get("nome", "")
        
        contas_pagar = await db["contas_pagar"].find({"centro_custo": centro_nome}, {"_id": 0}).to_list(500)
        contas_receber = await db["contas_receber"].find({"centro_custo": centro_nome}, {"_id": 0}).to_list(500)
        
        # Contas a Pagar
        if contas_pagar:
            elements.append(Paragraph("CONTAS A PAGAR - CENTRO DE CUSTO", section_style))
            total_pagar = sum(float(cp.get("valor_final") or cp.get("valor", 0) or 0) for cp in contas_pagar)
            elements.append(Paragraph(f"Total de {len(contas_pagar)} contas | Valor: {fmt_valor(total_pagar)}", value_style))
            elements.append(Spacer(1, 0.3*cm))
        
        # Contas a Receber
        if contas_receber:
            elements.append(Paragraph("CONTAS A RECEBER - CENTRO DE CUSTO", section_style))
            total_receber = sum(float(cr.get("valor_final") or cr.get("valor", 0) or 0) for cr in contas_receber)
            elements.append(Paragraph(f"Total de {len(contas_receber)} contas | Valor: {fmt_valor(total_receber)}", value_style))
    
    elif category == "cadastros":
        # Informações completas do cadastro
        elements.append(Paragraph("DADOS DO CADASTRO", section_style))
        
        nome = item.get("razao_social") or item.get("nome", "-")
        doc = item.get("cnpj") or item.get("cpf", "-")
        
        info_data = [
            [Paragraph("Nome/Razão Social:", label_style), Paragraph(nome, value_style)],
            [Paragraph("CPF/CNPJ:", label_style), Paragraph(doc, value_style)],
            [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style)],
            [Paragraph("Telefone:", label_style), Paragraph(item.get("telefone", "-"), value_style)],
            [Paragraph("Email:", label_style), Paragraph(item.get("email", "-"), value_style)],
            [Paragraph("Endereço:", label_style), Paragraph(item.get("endereco", "-"), value_style)],
            [Paragraph("Cidade:", label_style), Paragraph(item.get("cidade", "-"), value_style)],
            [Paragraph("Estado:", label_style), Paragraph(item.get("estado", "-"), value_style)],
            [Paragraph("CEP:", label_style), Paragraph(item.get("cep", "-"), value_style)],
            [Paragraph("Observações:", label_style), Paragraph(item.get("observacoes", "-"), value_style)],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 14*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
    
    elif category == "contas_bancarias":
        # Informações completas da conta bancária
        elements.append(Paragraph("DADOS DA CONTA BANCÁRIA", section_style))
        
        info_data = [
            [Paragraph("Nome:", label_style), Paragraph(item.get("nome", "-"), value_style),
             Paragraph("Banco:", label_style), Paragraph(item.get("banco", "-"), value_style)],
            [Paragraph("Agência:", label_style), Paragraph(item.get("agencia", "-"), value_style),
             Paragraph("Conta:", label_style), Paragraph(item.get("conta", "-"), value_style)],
            [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style),
             Paragraph("Titular:", label_style), Paragraph(item.get("titular", "-"), value_style)],
            [Paragraph("CPF/CNPJ:", label_style), Paragraph(item.get("cpf_cnpj", "-"), value_style),
             Paragraph("PIX:", label_style), Paragraph(item.get("pix", "-"), value_style)],
            [Paragraph("Status:", label_style), Paragraph("Ativa" if item.get("ativa", True) else "Inativa", value_style),
             Paragraph("Saldo:", label_style), Paragraph(fmt_valor(item.get("saldo", 0)), value_style)],
        ]
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
    
    elif category == "alugueis":
        # Informações completas do aluguel
        elements.append(Paragraph("DADOS DO ALUGUEL", section_style))
        
        info_data = [
            [Paragraph("Máquina:", label_style), Paragraph(item.get("maquina_nome", "-"), value_style),
             Paragraph("Cliente:", label_style), Paragraph(item.get("cliente_nome", "-"), value_style)],
            [Paragraph("Data Início:", label_style), Paragraph(item.get("data_inicio", "-"), value_style),
             Paragraph("Data Fim:", label_style), Paragraph(item.get("data_fim", "-"), value_style)],
            [Paragraph("Valor Diário:", label_style), Paragraph(fmt_valor(item.get("valor_diario", 0)), value_style),
             Paragraph("Valor Total:", label_style), Paragraph(fmt_valor(item.get("valor_total") or item.get("valor", 0)), value_style)],
            [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style),
             Paragraph("Horímetro Início:", label_style), Paragraph(str(item.get("horimetro_inicio", "-")), value_style)],
        ]
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        
        if item.get("observacoes"):
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph("OBSERVAÇÕES", section_style))
            elements.append(Paragraph(item.get("observacoes", "-"), value_style))
    
    elif "imoveis" in category:
        # Informações completas do imóvel
        elements.append(Paragraph("DADOS DO IMÓVEL", section_style))
        
        endereco = item.get("endereco", {})
        if isinstance(endereco, dict):
            endereco_str = f"{endereco.get('logradouro', '')}, {endereco.get('numero', '')} - {endereco.get('bairro', '')} - {endereco.get('cidade', '')}/{endereco.get('estado', '')} - CEP: {endereco.get('cep', '')}"
        else:
            endereco_str = str(endereco) if endereco else "-"
        
        info_data = [
            [Paragraph("Descrição:", label_style), Paragraph(item.get("descricao", "-"), value_style)],
            [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style)],
            [Paragraph("Área:", label_style), Paragraph(item.get("area", "-"), value_style)],
            [Paragraph("Endereço:", label_style), Paragraph(endereco_str, value_style)],
            [Paragraph("Quartos:", label_style), Paragraph(str(item.get("quartos", "-")), value_style)],
            [Paragraph("Banheiros:", label_style), Paragraph(str(item.get("banheiros", "-")), value_style)],
            [Paragraph("Vagas:", label_style), Paragraph(str(item.get("vagas", "-")), value_style)],
            [Paragraph("Valor Aluguel:", label_style), Paragraph(fmt_valor(item.get("valor_aluguel", 0)), value_style)],
            [Paragraph("Valor Condomínio:", label_style), Paragraph(fmt_valor(item.get("valor_condominio", 0)), value_style)],
            [Paragraph("Valor IPTU:", label_style), Paragraph(fmt_valor(item.get("valor_iptu", 0)), value_style)],
            [Paragraph("Inquilino:", label_style), Paragraph(item.get("inquilino_nome", "-"), value_style)],
            [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style)],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 14*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        
    else:
        # Genérico para outros tipos
        table_data = []
        for k, v in item.items():
            if k not in ["id", "created_at", "updated_at", "created_by", "_id"]:
                label = k.replace("_", " ").title()
                value = str(v) if v is not None else "-"
                table_data.append([Paragraph(f"{label}:", label_style), Paragraph(value, value_style)])
        
        if table_data:
            table = Table(table_data, colWidths=[4*cm, 14*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    # Log de auditoria
    item_name = item.get("descricao") or item.get("name") or item.get("nome") or item_id
    await create_audit_log(current_user, "export", category, item_id, f"Item individual: {item_name}")
    
    filename = f"CRA_{config['title'].replace(' ', '_')}_{item_id[:8]}.pdf"
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# Endpoint para exportar múltiplos itens individuais
class MultipleItemsExport(BaseModel):
    category: str
    item_ids: list
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    forma_pagamento: Optional[str] = None

@exports_all_router.post("/export/individual-multiple")
async def export_multiple_individual_items(data: MultipleItemsExport, current_user: dict = Depends(get_current_user)):
    """Exporta múltiplos itens individuais em um único PDF - cada item com detalhes completos.
    Aceita filtro opcional de período (intersecção: somente itens dentro do range)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    import io
    
    category_config = {
        "contas_pagar": {"collection": "contas_pagar", "title": "Contas a Pagar"},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas a Pagar Pendentes"},
        "contas_pagar_quitadas": {"collection": "contas_pagar", "title": "Contas a Pagar Quitadas"},
        "contas_pagar_vencidas": {"collection": "contas_pagar", "title": "Contas a Pagar Vencidas"},
        "contas_receber": {"collection": "contas_receber", "title": "Contas a Receber"},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas a Receber Pendentes"},
        "contas_receber_recebidas": {"collection": "contas_receber", "title": "Contas a Receber Recebidas"},
        "contas_receber_vencidas": {"collection": "contas_receber", "title": "Contas a Receber Vencidas"},
        "machines": {"collection": "machines", "title": "Máquinas"},
        "maintenances": {"collection": "maintenances", "title": "Manutenções"},
        "stock_items": {"collection": "stock_items", "title": "Itens de Estoque"},
        "obras": {"collection": "obras", "title": "Obras"},
        "alugueis": {"collection": "alugueis", "title": "Aluguéis"},
        "imoveis": {"collection": "imoveis", "title": "Imóveis"},
        "imoveis_ativo": {"collection": "imoveis", "title": "Imóveis Ativos"},
        "imoveis_pendente": {"collection": "imoveis", "title": "Imóveis Pendentes"},
        "plano_contas": {"collection": "plano_contas", "title": "Plano de Contas"},
        "centros_custo": {"collection": "centros_custo", "title": "Centros de Custo"},
        "cadastros": {"collection": "cadastros", "title": "Cadastros"},
        "contas_bancarias": {"collection": "contas_bancarias", "title": "Contas Bancárias"},
        "formas_pagamento": {"collection": "formas_pagamento", "title": "Formas de Pagamento"},
        "fleets": {"collection": "fleets", "title": "Frotas"},
    }
    
    if data.category not in category_config:
        raise HTTPException(status_code=400, detail="Categoria inválida")
    
    config = category_config[data.category]
    multi_filter: dict = {"id": {"$in": data.item_ids}}
    multi_filter = _apply_period_filter(config["collection"], multi_filter, data.data_inicio, data.data_fim)
    multi_filter = _apply_forma_pagamento_filter(config["collection"], multi_filter, data.forma_pagamento)
    items = await db[config["collection"]].find(multi_filter, {"_id": 0}).to_list(100)
    
    if not items:
        raise HTTPException(status_code=404, detail="Nenhum item encontrado no período selecionado")
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=5, alignment=1, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.gray, spaceAfter=8, alignment=1)
    section_style = ParagraphStyle('Section', fontSize=12, fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=8, textColor=colors.HexColor("#D4A000"))
    label_style = ParagraphStyle('Label', fontSize=9, fontName='Helvetica-Bold')
    value_style = ParagraphStyle('Value', fontSize=9, leading=12, wordWrap='CJK')
    
    elements = []
    
    def fmt_valor(v):
        if v is None or v == "":
            return "-"
        try:
            return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return str(v)
    
    # Para cada item, gerar página completa com todos os detalhes
    for idx, item in enumerate(items):
        if idx > 0:
            elements.append(PageBreak())
        
        # Cabeçalho
        elements.append(Paragraph(f"{config['title']}", title_style))
        elements.append(Paragraph(f"Item {idx + 1} de {len(items)} | Exportado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Conteúdo baseado no tipo de categoria
        category = data.category
        
        if "contas_pagar" in category or "contas_receber" in category:
            elements.append(Paragraph("INFORMAÇÕES DA CONTA", section_style))
            
            # Buscar dados relacionados
            fornecedor_nome = item.get("fornecedor_nome") or item.get("cliente_nome") or "-"
            plano_nome = item.get("plano_conta_nome") or item.get("plano_contas_nome") or "-"
            centro_nome = item.get("centro_custo_nome") or item.get("centro_custo") or "-"
            forma_pag = item.get("forma_pagamento_nome") or item.get("forma_pagamento") or "-"
            conta_banco = item.get("conta_bancaria_nome") or "-"
            
            info_data = [
                [Paragraph("Nº:", label_style), Paragraph(str(item.get("numero", "-")), value_style),
                 Paragraph("Status:", label_style), Paragraph("Quitada" if item.get("status") == "quitada" else "Em Aberto", value_style)],
                [Paragraph("Fornecedor/Cliente:", label_style), Paragraph(fornecedor_nome, value_style),
                 Paragraph("CNPJ/CPF:", label_style), Paragraph(item.get("fornecedor_cnpj") or item.get("cliente_cnpj") or "-", value_style)],
                [Paragraph("Documento:", label_style), Paragraph(item.get("documento", "-"), value_style),
                 Paragraph("Nº Doc:", label_style), Paragraph(item.get("numero_doc", "-"), value_style)],
                [Paragraph("Data Emissão:", label_style), Paragraph(item.get("data_emissao", "-"), value_style),
                 Paragraph("Data Vencimento:", label_style), Paragraph(item.get("data_vencimento", "-"), value_style)],
                [Paragraph("Valor Original:", label_style), Paragraph(fmt_valor(item.get("valor", 0)), value_style),
                 Paragraph("Valor Final:", label_style), Paragraph(fmt_valor(item.get("valor_final") or item.get("valor", 0)), value_style)],
                [Paragraph("Juros:", label_style), Paragraph(fmt_valor(item.get("juros", 0)), value_style),
                 Paragraph("Desconto:", label_style), Paragraph(fmt_valor(item.get("desconto", 0)), value_style)],
                [Paragraph("Plano de Contas:", label_style), Paragraph(plano_nome, value_style),
                 Paragraph("Centro de Custo:", label_style), Paragraph(centro_nome, value_style)],
                [Paragraph("Forma Pagamento:", label_style), Paragraph(forma_pag, value_style),
                 Paragraph("Conta Bancária:", label_style), Paragraph(conta_banco, value_style)],
            ]
            
            if item.get("data_pagamento") or item.get("data_recebimento"):
                info_data.append([
                    Paragraph("Data Pagamento:", label_style), 
                    Paragraph(item.get("data_pagamento") or item.get("data_recebimento") or "-", value_style),
                    Paragraph("", label_style), Paragraph("", value_style)
                ])
            
            info_table = Table(info_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
            
            # Descrição
            if item.get("descricao"):
                elements.append(Spacer(1, 0.4*cm))
                elements.append(Paragraph("DESCRIÇÃO", section_style))
                desc_table = Table([[Paragraph(item.get("descricao", "-"), value_style)]], colWidths=[18*cm])
                desc_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffef5")),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(desc_table)
            
            # Observações
            if item.get("observacoes"):
                elements.append(Spacer(1, 0.3*cm))
                elements.append(Paragraph("OBSERVAÇÕES", section_style))
                obs_table = Table([[Paragraph(item.get("observacoes", "-"), value_style)]], colWidths=[18*cm])
                obs_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(obs_table)
        
        elif category == "plano_contas":
            elements.append(Paragraph("DADOS DO PLANO DE CONTAS", section_style))
            info_data = [
                [Paragraph("Código:", label_style), Paragraph(item.get("codigo", "-"), value_style),
                 Paragraph("Nome:", label_style), Paragraph(item.get("nome", "-"), value_style)],
                [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style),
                 Paragraph("Natureza:", label_style), Paragraph(item.get("natureza", "-"), value_style)],
                [Paragraph("Conta Pai:", label_style), Paragraph(item.get("conta_pai_nome", "-"), value_style),
                 Paragraph("Status:", label_style), Paragraph("Ativo" if item.get("ativo", True) else "Inativo", value_style)],
            ]
            info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
        
        elif category == "cadastros":
            elements.append(Paragraph("DADOS DO CADASTRO", section_style))
            nome = item.get("razao_social") or item.get("nome", "-")
            doc = item.get("cnpj") or item.get("cpf", "-")
            info_data = [
                [Paragraph("Nome/Razão Social:", label_style), Paragraph(nome, value_style)],
                [Paragraph("CPF/CNPJ:", label_style), Paragraph(doc, value_style)],
                [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style)],
                [Paragraph("Telefone:", label_style), Paragraph(item.get("telefone", "-"), value_style)],
                [Paragraph("Email:", label_style), Paragraph(item.get("email", "-"), value_style)],
                [Paragraph("Endereço:", label_style), Paragraph(item.get("endereco", "-"), value_style)],
                [Paragraph("Cidade/Estado:", label_style), Paragraph(f"{item.get('cidade', '-')}/{item.get('estado', '-')}", value_style)],
                [Paragraph("CEP:", label_style), Paragraph(item.get("cep", "-"), value_style)],
                [Paragraph("Observações:", label_style), Paragraph(item.get("observacoes", "-"), value_style)],
            ]
            info_table = Table(info_data, colWidths=[4*cm, 14*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
        
        elif category == "contas_bancarias":
            elements.append(Paragraph("DADOS DA CONTA BANCÁRIA", section_style))
            info_data = [
                [Paragraph("Nome:", label_style), Paragraph(item.get("nome", "-"), value_style),
                 Paragraph("Banco:", label_style), Paragraph(item.get("banco", "-"), value_style)],
                [Paragraph("Agência:", label_style), Paragraph(item.get("agencia", "-"), value_style),
                 Paragraph("Conta:", label_style), Paragraph(item.get("conta", "-"), value_style)],
                [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style),
                 Paragraph("Titular:", label_style), Paragraph(item.get("titular", "-"), value_style)],
                [Paragraph("CPF/CNPJ:", label_style), Paragraph(item.get("cpf_cnpj", "-"), value_style),
                 Paragraph("PIX:", label_style), Paragraph(item.get("pix", "-"), value_style)],
                [Paragraph("Status:", label_style), Paragraph("Ativa" if item.get("ativa", True) else "Inativa", value_style),
                 Paragraph("Saldo:", label_style), Paragraph(fmt_valor(item.get("saldo", 0)), value_style)],
            ]
            info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
        
        elif "imoveis" in category:
            elements.append(Paragraph("DADOS DO IMÓVEL", section_style))
            endereco = item.get("endereco", {})
            if isinstance(endereco, dict):
                endereco_str = f"{endereco.get('logradouro', '')}, {endereco.get('numero', '')} - {endereco.get('bairro', '')} - {endereco.get('cidade', '')}/{endereco.get('estado', '')} - CEP: {endereco.get('cep', '')}"
            else:
                endereco_str = str(endereco) if endereco else "-"
            
            info_data = [
                [Paragraph("Descrição:", label_style), Paragraph(item.get("descricao", "-"), value_style)],
                [Paragraph("Tipo:", label_style), Paragraph(item.get("tipo", "-"), value_style)],
                [Paragraph("Área:", label_style), Paragraph(item.get("area", "-"), value_style)],
                [Paragraph("Endereço:", label_style), Paragraph(endereco_str, value_style)],
                [Paragraph("Quartos:", label_style), Paragraph(str(item.get("quartos", "-")), value_style)],
                [Paragraph("Banheiros:", label_style), Paragraph(str(item.get("banheiros", "-")), value_style)],
                [Paragraph("Valor Aluguel:", label_style), Paragraph(fmt_valor(item.get("valor_aluguel", 0)), value_style)],
                [Paragraph("Inquilino:", label_style), Paragraph(item.get("inquilino_nome", "-"), value_style)],
                [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style)],
            ]
            info_table = Table(info_data, colWidths=[4*cm, 14*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
        
        elif category == "alugueis":
            elements.append(Paragraph("DADOS DO ALUGUEL", section_style))
            info_data = [
                [Paragraph("Máquina:", label_style), Paragraph(item.get("maquina_nome", "-"), value_style),
                 Paragraph("Cliente:", label_style), Paragraph(item.get("cliente_nome", "-"), value_style)],
                [Paragraph("Data Início:", label_style), Paragraph(item.get("data_inicio", "-"), value_style),
                 Paragraph("Data Fim:", label_style), Paragraph(item.get("data_fim", "-"), value_style)],
                [Paragraph("Valor Diário:", label_style), Paragraph(fmt_valor(item.get("valor_diario", 0)), value_style),
                 Paragraph("Valor Total:", label_style), Paragraph(fmt_valor(item.get("valor_total") or item.get("valor", 0)), value_style)],
                [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style),
                 Paragraph("Horímetro:", label_style), Paragraph(str(item.get("horimetro_inicio", "-")), value_style)],
            ]
            info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8f8f8")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
            if item.get("observacoes"):
                elements.append(Spacer(1, 0.3*cm))
                elements.append(Paragraph("OBSERVAÇÕES", section_style))
                elements.append(Paragraph(item.get("observacoes", "-"), value_style))
        
        elif category == "machines":
            elements.append(Paragraph("DADOS DA MÁQUINA", section_style))
            info_data = [
                [Paragraph("Nome:", label_style), Paragraph(item.get("name", "-"), value_style)],
                [Paragraph("Modelo:", label_style), Paragraph(item.get("model", "-"), value_style)],
                [Paragraph("Ano:", label_style), Paragraph(str(item.get("year", "-")), value_style)],
                [Paragraph("Categoria:", label_style), Paragraph(item.get("category", "-"), value_style)],
                [Paragraph("Frota:", label_style), Paragraph(item.get("fleet_name", "-"), value_style)],
                [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style)],
                [Paragraph("Horímetro:", label_style), Paragraph(str(item.get("horimetro_atual", "-")), value_style)],
            ]
            info_table = Table(info_data, colWidths=[4*cm, 14*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
        
        elif category == "maintenances":
            elements.append(Paragraph("DADOS DA MANUTENÇÃO", section_style))
            info_data = [
                [Paragraph("Descrição:", label_style), Paragraph(item.get("description", "-"), value_style)],
                [Paragraph("Máquina:", label_style), Paragraph(item.get("machine_name", "-"), value_style)],
                [Paragraph("Data:", label_style), Paragraph(item.get("date", "-"), value_style)],
                [Paragraph("Tipo:", label_style), Paragraph(item.get("type", "-"), value_style)],
                [Paragraph("Custo:", label_style), Paragraph(fmt_valor(item.get("cost", 0)), value_style)],
                [Paragraph("Status:", label_style), Paragraph(item.get("status", "-"), value_style)],
                [Paragraph("Mecânico:", label_style), Paragraph(item.get("mechanic", "-"), value_style)],
                [Paragraph("Observações:", label_style), Paragraph(item.get("observations", "-"), value_style)],
            ]
            info_table = Table(info_data, colWidths=[4*cm, 14*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
        
        else:
            # Genérico para outras categorias
            elements.append(Paragraph("DETALHES DO ITEM", section_style))
            info_data = []
            for key, val in item.items():
                if key not in ["_id", "id", "created_at", "updated_at", "created_by"]:
                    if isinstance(val, dict):
                        val = str(val)
                    info_data.append([Paragraph(f"{key}:", label_style), Paragraph(str(val) if val else "-", value_style)])
            
            if info_data:
                info_table = Table(info_data, colWidths=[5*cm, 13*cm])
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(info_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    await create_audit_log(current_user, "export", data.category, None, f"Múltiplos itens: {len(items)}")
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CRA_{config['title'].replace(' ', '_')}_{len(items)}_itens.pdf"}
    )


# Função auxiliar para converter valor para extenso
def valor_por_extenso(valor):
    """Converte valor numérico para extenso em português"""
    unidades = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
    dezenas = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
    dez_a_dezenove = ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
    centenas = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']
    
    def grupo_de_tres(n):
        if n == 0:
            return ''
        elif n == 100:
            return 'cem'
        
        resultado = ''
        c = n // 100
        d = (n % 100) // 10
        u = n % 10
        
        if c > 0:
            resultado += centenas[c]
            if d > 0 or u > 0:
                resultado += ' e '
        
        if d == 1:
            resultado += dez_a_dezenove[u]
        elif d > 1:
            resultado += dezenas[d]
            if u > 0:
                resultado += ' e ' + unidades[u]
        elif u > 0:
            resultado += unidades[u]
        
        return resultado
    
    if valor == 0:
        return 'zero reais'
    
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))
    
    resultado = ''
    
    # Milhões
    milhoes = inteiro // 1000000
    if milhoes > 0:
        if milhoes == 1:
            resultado += 'um milhão'
        else:
            resultado += grupo_de_tres(milhoes) + ' milhões'
        inteiro = inteiro % 1000000
        if inteiro > 0:
            resultado += ', ' if inteiro >= 100 else ' e '
    
    # Milhares
    milhares = inteiro // 1000
    if milhares > 0:
        if milhares == 1:
            resultado += 'mil'
        else:
            resultado += grupo_de_tres(milhares) + ' mil'
        inteiro = inteiro % 1000
        if inteiro > 0:
            resultado += ', ' if inteiro >= 100 else ' e '
    
    # Centenas, dezenas e unidades
    if inteiro > 0:
        resultado += grupo_de_tres(inteiro)
    
    # Reais
    valor_int = int(valor)
    if valor_int == 1:
        resultado += ' real'
    elif valor_int > 0:
        resultado += ' reais'
    
    # Centavos
    if centavos > 0:
        if valor_int > 0:
            resultado += ' e '
        resultado += grupo_de_tres(centavos)
        if centavos == 1:
            resultado += ' centavo'
        else:
            resultado += ' centavos'
    
    return resultado.upper()


# Dados das empresas CRA
EMPRESAS_CRA = {
    "construtora": {
        "nome": "CRA CONSTRUTORA",
        "cnpj": "04.887.879/0001-96",
        "ie": "",
        "telefone": "(63) 98407-1513",
        "endereco": "Q. ASR SE, 75, AVENIDA LO 15, QI 10, LOTE 51A, PLANO DIRETOR SUL, CEP 77022-418, PALMAS - TO"
    },
    "locadora": {
        "nome": "CRA LOCADORA",
        "cnpj": "39.543.761/0001-25",
        "ie": "",
        "telefone": "(63) 98407-1513",
        "endereco": "Q. ASR SE, 75, AVENIDA LO 15, QI 10, LOTE 51A, PLANO DIRETOR SUL, CEP 77022-418, PALMAS - TO"
    }
}

# Endpoint para gerar Recibo
@exports_all_router.get("/export/recibo/{category}/{item_id}")
async def export_recibo(
    category: str,
    item_id: str,
    empresa: str = "locadora",
    pagamento_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Gera um recibo de pagamento em PDF.
    Se `pagamento_id` for informado, emite recibo do pagamento parcial específico
    (valor individual, data do pagamento parcial, saldo restante)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    import io
    
    collection_map = {
        "contas_pagar": "contas_pagar", "contas_pagar_pendente": "contas_pagar",
        "contas_pagar_quitadas": "contas_pagar", "contas_pagar_vencidas": "contas_pagar",
        "contas_receber": "contas_receber", "contas_receber_pendente": "contas_receber",
        "contas_receber_recebidas": "contas_receber", "contas_receber_vencidas": "contas_receber",
        "alugueis": "alugueis",
        "imoveis": "imoveis", "imoveis_ativo": "imoveis", "imoveis_pendente": "imoveis"
    }
    
    if category not in collection_map:
        raise HTTPException(status_code=400, detail="Categoria não suporta recibo")
    
    item = await db[collection_map[category]].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Usar dados da empresa selecionada
    empresa_data = EMPRESAS_CRA.get(empresa, EMPRESAS_CRA["locadora"])
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    elements = []
    
    # Logo
    try:
        logo_path = "/app/frontend/public/logo.png"
        if os.path.exists(logo_path):
            logo = RLImage(logo_path, width=3*cm, height=3*cm, kind='proportional')
            elements.append(logo)
    except Exception as e:
        logging.warning(f"Não foi possível carregar o logo: {e}")
    
    # Cabeçalho com dados da empresa selecionada
    empresa_nome = empresa_data["nome"]
    empresa_cnpj = empresa_data["cnpj"]
    empresa_endereco = empresa_data["endereco"]
    empresa_telefone = empresa_data["telefone"]
    
    # Estilo do cabeçalho com mais espaçamento
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=10, alignment=1, textColor=colors.gray, spaceBefore=4, spaceAfter=4, leading=14)
    empresa_nome_style = ParagraphStyle('EmpNome', fontSize=16, alignment=1, spaceAfter=12, fontName='Helvetica-Bold')
    
    elements.append(Paragraph(empresa_nome, empresa_nome_style))
    elements.append(Spacer(1, 0.4*cm))  # Mais espaço após o nome
    
    if empresa_cnpj:
        elements.append(Paragraph(f"CNPJ: {empresa_cnpj}", header_style))
    if empresa_endereco:
        elements.append(Paragraph(empresa_endereco, header_style))
    if empresa_telefone:
        elements.append(Paragraph(f"Tel: {empresa_telefone}", header_style))
    
    elements.append(Spacer(1, 0.8*cm))  # Mais espaço antes do título RECIBO
    elements.append(Paragraph("RECIBO", ParagraphStyle('Title', fontSize=24, alignment=1, spaceAfter=10, fontName='Helvetica-Bold')))
    elements.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", ParagraphStyle('Data', fontSize=10, alignment=2)))
    elements.append(Spacer(1, 0.5*cm))
    
    # Dados do cliente/fornecedor — enriquecer buscando o cadastro completo
    # quando o conta_pagar/receber só tiver fornecedor_id/cliente_id mas faltarem
    # CPF/CNPJ, telefone e endereço.
    cadastro_doc = None
    cadastro_id = item.get("fornecedor_id") or item.get("cliente_id")
    if cadastro_id:
        cadastro_doc = await db.cadastros.find_one({"id": cadastro_id}, {"_id": 0})

    def _pick(*vals):
        for v in vals:
            if v not in (None, "", "-"):
                return v
        return "-"

    pessoa_nome = _pick(
        item.get("fornecedor_nome"),
        item.get("cliente_nome"),
        (cadastro_doc or {}).get("nome_razao"),
        (cadastro_doc or {}).get("apelido_fantasia"),
    )
    pessoa_doc = _pick(
        item.get("fornecedor_cnpj"),
        item.get("fornecedor_documento"),
        item.get("cliente_documento"),
        item.get("cliente_cnpj"),
        (cadastro_doc or {}).get("cpf_cnpj"),
    )
    pessoa_telefone = _pick(
        item.get("fornecedor_telefone"),
        item.get("cliente_telefone"),
        (cadastro_doc or {}).get("telefone"),
        (cadastro_doc or {}).get("celular"),
    )
    # Endereço: se vier estruturado no cadastro, montar string completa
    end_cad = ""
    if cadastro_doc:
        partes_end = [
            cadastro_doc.get("endereco"),
            cadastro_doc.get("numero"),
            cadastro_doc.get("complemento"),
            cadastro_doc.get("bairro"),
            cadastro_doc.get("cidade"),
            cadastro_doc.get("uf"),
        ]
        end_cad = ", ".join([p for p in partes_end if p]) or ""
        if cadastro_doc.get("cep") and end_cad:
            end_cad = f"{end_cad} - CEP {cadastro_doc.get('cep')}"
    pessoa_endereco = _pick(
        item.get("fornecedor_endereco"),
        item.get("cliente_endereco"),
        end_cad,
    )

    # Determina PAGADOR (quem pagou) para o "Recebi(emos) de":
    # - contas_pagar.*  → a empresa CRA pagou o fornecedor (pagador = empresa)
    # - contas_receber.* / alugueis / imoveis → o cliente pagou a empresa (pagador = cliente)
    if category.startswith("contas_pagar"):
        pagador_nome = empresa_nome
    else:
        pagador_nome = item.get("cliente_nome") or item.get("fornecedor_nome") or empresa_nome
    
    label_style = ParagraphStyle('Label', fontSize=9, textColor=colors.gray)
    value_style = ParagraphStyle('Value', fontSize=10)
    
    client_data = [
        [Paragraph("Nome:", label_style), Paragraph(pessoa_nome, value_style)],
        [Paragraph("CPF/CNPJ:", label_style), Paragraph(pessoa_doc, value_style)],
        [Paragraph("Telefone:", label_style), Paragraph(pessoa_telefone, value_style)],
        [Paragraph("Endereço:", label_style), Paragraph(pessoa_endereco, value_style)],
    ]
    client_table = Table(client_data, colWidths=[2.5*cm, 15*cm])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.4*cm))
    
    # Valor / Pagamento parcial
    valor_total_conta = item.get("valor_final") or item.get("valor") or item.get("valor_aluguel") or 0

    # Busca o pagamento parcial específico se pagamento_id foi informado.
    # Contas a pagar usam array `pagamentos`; contas a receber usam `recebimentos`.
    pagamento_sel = None
    lista_pagamentos = (item.get("pagamentos") or item.get("recebimentos") or [])
    if pagamento_id:
        for p in lista_pagamentos:
            if p.get("id") == pagamento_id:
                pagamento_sel = p
                break
        if not pagamento_sel:
            raise HTTPException(status_code=404, detail="Pagamento parcial não encontrado")

    if pagamento_sel:
        valor = pagamento_sel.get("valor", 0) or 0
        # Soma dos pagamentos feitos até este (inclusive)
        valor_ja_pago_ate_aqui = 0
        encontrou = False
        for p in lista_pagamentos:
            valor_ja_pago_ate_aqui += p.get("valor", 0) or 0
            if p.get("id") == pagamento_id:
                encontrou = True
                break
        if not encontrou:
            valor_ja_pago_ate_aqui = valor
        saldo_restante = max(0, valor_total_conta - valor_ja_pago_ate_aqui)
        tipo_recibo = "RECIBO - PAGAMENTO PARCIAL" if saldo_restante > 0.01 else "RECIBO - PAGAMENTO FINAL (QUITAÇÃO)"
    else:
        valor = valor_total_conta
        valor_ja_pago_ate_aqui = valor_total_conta
        saldo_restante = 0
        tipo_recibo = "RECIBO"

    valor_str = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Atualiza o título do recibo caso seja parcial
    # (o Paragraph de "RECIBO" já foi adicionado — adicionamos um subtítulo complementar)
    if pagamento_sel:
        elements.append(Paragraph(
            f"<i>{tipo_recibo}</i>",
            ParagraphStyle('SubTitulo', fontSize=11, alignment=1, spaceAfter=8, textColor=colors.HexColor("#C62828"))
        ))
        elements.append(Spacer(1, 0.2*cm))

    elements.append(Paragraph(f"Recebi(emos) de <b>{pagador_nome}</b> a importância de:", ParagraphStyle('Extenso', fontSize=10)))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(f"<b>{valor_por_extenso(valor)}</b>", ParagraphStyle('ValorExtenso', fontSize=10)))
    elements.append(Spacer(1, 0.3*cm))
    
    valor_box = Table([[Paragraph(f"<b>{valor_str}</b>", ParagraphStyle('ValorNum', fontSize=18, alignment=1))]], colWidths=[17.5*cm])
    valor_box.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(valor_box)
    elements.append(Spacer(1, 0.4*cm))
    
    # Detalhes completos do documento
    elements.append(Paragraph("<b>Referente a:</b>", ParagraphStyle('Ref', fontSize=10)))
    elements.append(Spacer(1, 0.2*cm))
    
    descricao = item.get("descricao", "-")
    plano_contas = item.get("plano_contas_nome", "-")
    centro_custo = item.get("centro_custo_nome", "-")
    forma_pag = item.get("forma_pagamento_nome", "-")
    
    # Formatar datas para o formato brasileiro (dd/mm/aaaa)
    def formatar_data_br(data_str):
        if not data_str or data_str == "-":
            return "-"
        try:
            # Tentar formato YYYY-MM-DD
            if len(data_str) >= 10 and "-" in data_str:
                partes = data_str[:10].split("-")
                if len(partes) == 3:
                    return f"{partes[2]}/{partes[1]}/{partes[0]}"
            return data_str
        except Exception:
            return data_str
    
    data_venc = formatar_data_br(item.get("data_vencimento", "-"))
    if pagamento_sel:
        data_pag = formatar_data_br(pagamento_sel.get("data", "-"))
        obs_pagamento = pagamento_sel.get("observacao") or item.get("observacoes", "-")
        forma_pag_recibo = pagamento_sel.get("forma_pagamento_nome") or forma_pag
    else:
        data_pag = formatar_data_br(item.get("data_pagamento") or item.get("data_recebimento") or "-")
        obs_pagamento = item.get("observacoes", "-")
        forma_pag_recibo = forma_pag
    
    # Estilo com word-wrap para textos longos
    detail_value_style = ParagraphStyle('DetailValue', fontSize=9, leading=12, wordWrap='CJK')
    detail_label_style = ParagraphStyle('DetailLabel', fontSize=9, fontName='Helvetica-Bold')
    
    detail_data = [
        [Paragraph("Descrição", detail_label_style), Paragraph(descricao if descricao else "-", detail_value_style)],
        [Paragraph("Data de Vencimento", detail_label_style), Paragraph(data_venc if data_venc else "-", detail_value_style)],
        [Paragraph("Data de Pagamento", detail_label_style), Paragraph(data_pag if data_pag else "-", detail_value_style)],
        [Paragraph("Forma de Pagamento", detail_label_style), Paragraph(forma_pag_recibo if forma_pag_recibo else "-", detail_value_style)],
        [Paragraph("Plano de Contas", detail_label_style), Paragraph(plano_contas if plano_contas else "-", detail_value_style)],
        [Paragraph("Centro de Custo", detail_label_style), Paragraph(centro_custo if centro_custo else "-", detail_value_style)],
        [Paragraph("Observações", detail_label_style), Paragraph(obs_pagamento if obs_pagamento else "-", detail_value_style)],
    ]
    # Se é pagamento parcial, adiciona linhas com resumo financeiro
    if pagamento_sel:
        def _brl(v):
            return f"R$ {(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        resumo_style = ParagraphStyle('DetailValueHL', fontSize=10, leading=13, fontName='Helvetica-Bold')
        # Ajustes opcionais do pagamento: juros, multa, desconto
        vj = float(pagamento_sel.get("valor_juros") or 0)
        vm = float(pagamento_sel.get("valor_multa") or 0)
        vd = float(pagamento_sel.get("valor_desconto") or 0)
        if vj > 0:
            detail_data.append([
                Paragraph("Juros", detail_label_style),
                Paragraph(f"<font color='#EF6C00'>+ {_brl(vj)}</font>", resumo_style),
            ])
        if vm > 0:
            detail_data.append([
                Paragraph("Multa", detail_label_style),
                Paragraph(f"<font color='#C62828'>+ {_brl(vm)}</font>", resumo_style),
            ])
        if vd > 0:
            detail_data.append([
                Paragraph("Desconto", detail_label_style),
                Paragraph(f"<font color='#2E7D32'>- {_brl(vd)}</font>", resumo_style),
            ])
        if vj + vm + vd > 0:
            liquido_parcela = valor + vj + vm - vd
            detail_data.append([
                Paragraph("Valor Líquido da Parcela", detail_label_style),
                Paragraph(_brl(liquido_parcela), resumo_style),
            ])
        detail_data.append([Paragraph("Valor Total da Conta", detail_label_style), Paragraph(_brl(valor_total_conta), resumo_style)])
        detail_data.append([Paragraph("Total Pago (com este)", detail_label_style), Paragraph(_brl(valor_ja_pago_ate_aqui), resumo_style)])
        detail_data.append([
            Paragraph("Saldo Restante", detail_label_style),
            Paragraph(
                _brl(saldo_restante),
                ParagraphStyle('Saldo', fontSize=10, leading=13, fontName='Helvetica-Bold',
                               textColor=colors.HexColor("#C62828") if saldo_restante > 0.01 else colors.HexColor("#2E7D32")),
            ),
        ])

    detail_table = Table(detail_data, colWidths=[4*cm, 13.5*cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 1*cm))
    
    # Assinatura - usar nome do fornecedor/cliente ao invés da empresa
    elements.append(Paragraph("_" * 50, ParagraphStyle('Linha', alignment=1)))
    elements.append(Paragraph(pessoa_nome, ParagraphStyle('Assinatura', fontSize=10, alignment=1)))
    
    doc.build(elements)
    buffer.seek(0)
    
    audit_detail = f"Recibo: {item.get('descricao', item_id)}"
    if pagamento_sel:
        audit_detail += f" — parcial R$ {valor:,.2f} em {pagamento_sel.get('data', '')}"
    await create_audit_log(current_user, "export", "recibo", item_id, audit_detail)
    
    filename_suffix = f"_parcial_{pagamento_id[:8]}" if pagamento_id else ""
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CRA_Recibo_{item_id[:8]}{filename_suffix}.pdf"}
    )


# Endpoint para gerar Duplicata/Recibo Fatura
@exports_all_router.get("/export/duplicata/{category}/{item_id}")
async def export_duplicata(category: str, item_id: str, empresa: str = "locadora", current_user: dict = Depends(get_current_user)):
    """Gera uma duplicata/recibo fatura em PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    import io
    
    collection_map = {
        "contas_pagar": "contas_pagar", "contas_pagar_pendente": "contas_pagar",
        "contas_pagar_quitadas": "contas_pagar", "contas_pagar_vencidas": "contas_pagar",
        "contas_receber": "contas_receber", "contas_receber_pendente": "contas_receber",
        "contas_receber_recebidas": "contas_receber", "contas_receber_vencidas": "contas_receber",
        "alugueis": "alugueis",
        "imoveis": "imoveis", "imoveis_ativo": "imoveis", "imoveis_pendente": "imoveis"
    }
    
    if category not in collection_map:
        raise HTTPException(status_code=400, detail="Categoria não suporta duplicata")
    
    item = await db[collection_map[category]].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Usar dados da empresa selecionada
    empresa_data = EMPRESAS_CRA.get(empresa, EMPRESAS_CRA["locadora"])
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    elements = []
    
    # Dados da empresa selecionada
    empresa_nome = empresa_data["nome"]
    empresa_cnpj = empresa_data["cnpj"]
    empresa_ie = empresa_data["ie"]
    empresa_endereco = empresa_data["endereco"]
    empresa_telefone = empresa_data["telefone"]
    
    # Logo
    try:
        logo_path = "/app/frontend/public/logo.png"
        if os.path.exists(logo_path):
            logo = RLImage(logo_path, width=2.5*cm, height=2.5*cm, kind='proportional')
            elements.append(logo)
    except Exception as e:
        logging.warning(f"Logo não carregado: {e}")
    
    # Cabeçalho com espaçamento melhorado
    empresa_nome_style = ParagraphStyle('EmpNome', fontSize=14, alignment=1, spaceAfter=10, fontName='Helvetica-Bold')
    header_style = ParagraphStyle('Sub', fontSize=9, alignment=1, textColor=colors.gray, spaceBefore=4, spaceAfter=4, leading=12)
    
    elements.append(Paragraph(empresa_nome, empresa_nome_style))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(f"CNPJ: {empresa_cnpj}", header_style))
    elements.append(Paragraph(empresa_endereco, header_style))
    elements.append(Paragraph(f"Tel: {empresa_telefone}", header_style))
    elements.append(Spacer(1, 0.5*cm))
    
    elements.append(Paragraph("DUPLICATA", ParagraphStyle('Title', fontSize=18, alignment=1, spaceAfter=5)))
    elements.append(Spacer(1, 0.3*cm))
    
    # Dados principais
    valor = item.get("valor_final") or item.get("valor") or item.get("valor_aluguel") or 0
    valor_str = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    pessoa_nome = item.get("fornecedor_nome") or item.get("cliente_nome") or "-"
    pessoa_doc = item.get("fornecedor_cnpj") or item.get("cliente_documento") or item.get("cliente_cnpj") or "-"
    pessoa_endereco = item.get("fornecedor_endereco") or item.get("endereco") or item.get("cliente_endereco") or "-"
    pessoa_telefone = item.get("fornecedor_telefone") or item.get("cliente_telefone") or "-"
    cidade = item.get("cidade", "-")
    
    label_style = ParagraphStyle('Label', fontSize=7, textColor=colors.gray)
    value_style = ParagraphStyle('Value', fontSize=9)
    
    # Formatar datas para o formato brasileiro (dd/mm/aaaa)
    def formatar_data_br(data_str):
        if not data_str or data_str == "-":
            return "-"
        try:
            if len(data_str) >= 10 and "-" in data_str:
                partes = data_str[:10].split("-")
                if len(partes) == 3:
                    return f"{partes[2]}/{partes[1]}/{partes[0]}"
            return data_str
        except Exception:
            return data_str

    data_venc_br = formatar_data_br(item.get("data_vencimento", "-"))

    # Linha 1: Valor, Número, Vencimento
    row1_data = [
        [Paragraph("VALOR", label_style), Paragraph("Nº DOCUMENTO", label_style), Paragraph("VENCIMENTO", label_style)],
        [Paragraph(f"<b>{valor_str}</b>", ParagraphStyle('V', fontSize=14)), 
         Paragraph(item_id[:12].upper(), value_style), 
         Paragraph(f"<b>{data_venc_br}</b>", ParagraphStyle('Venc', fontSize=11))]
    ]
    row1_table = Table(row1_data, colWidths=[6*cm, 6.5*cm, 6.5*cm])
    row1_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(row1_table)
    
    # Dados do Sacado
    sacado_data = [
        [Paragraph("SACADO (PAGADOR)", label_style), "", ""],
        [Paragraph("Nome:", label_style), Paragraph(pessoa_nome, value_style), ""],
        [Paragraph("CPF/CNPJ:", label_style), Paragraph(pessoa_doc, value_style), Paragraph(f"Tel: {pessoa_telefone}", value_style)],
        [Paragraph("Endereço:", label_style), Paragraph(pessoa_endereco, value_style), Paragraph(f"Cidade: {cidade}", value_style)],
    ]
    sacado_table = Table(sacado_data, colWidths=[3*cm, 9*cm, 7*cm])
    sacado_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D4A000")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(sacado_table)
    
    # Valor por extenso
    extenso_data = [
        [Paragraph("VALOR POR EXTENSO", label_style)],
        [Paragraph(valor_por_extenso(valor), ParagraphStyle('Ext', fontSize=9))],
    ]
    extenso_table = Table(extenso_data, colWidths=[19*cm])
    extenso_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(extenso_table)
    
    # Descrição completa com word-wrap
    descricao = item.get("descricao", "-")
    plano_contas = item.get("plano_contas_nome", "-")
    centro_custo = item.get("centro_custo_nome", "-")
    forma_pag = item.get("forma_pagamento_nome", "-")
    obs = item.get("observacoes", "")
    
    desc_value_style = ParagraphStyle('Desc', fontSize=9, leading=12, wordWrap='CJK')
    desc_info_style = ParagraphStyle('Info', fontSize=8, leading=11)
    
    desc_data = [
        [Paragraph("DESCRIÇÃO / REFERÊNCIA", label_style)],
        [Paragraph(descricao if descricao else "-", desc_value_style)],
        [Paragraph(f"<b>Plano de Contas:</b> {plano_contas if plano_contas else '-'} | <b>Centro de Custo:</b> {centro_custo if centro_custo else '-'} | <b>Forma Pagamento:</b> {forma_pag if forma_pag else '-'}", desc_info_style)],
    ]

    # Ajustes da conta (juros/multa/desconto) — só aparecem se presentes
    conta_juros = float(item.get("valor_juros") or 0)
    conta_multa = float(item.get("valor_multa") or 0)
    conta_desconto = float(item.get("valor_desconto") or 0)
    if conta_juros + conta_multa + conta_desconto > 0:
        def _brl_dup(v):
            return f"R$ {(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        partes_ajuste = []
        if conta_juros > 0:
            partes_ajuste.append(f"<b>Juros:</b> <font color='#EF6C00'>+ {_brl_dup(conta_juros)}</font>")
        if conta_multa > 0:
            partes_ajuste.append(f"<b>Multa:</b> <font color='#C62828'>+ {_brl_dup(conta_multa)}</font>")
        if conta_desconto > 0:
            partes_ajuste.append(f"<b>Desconto:</b> <font color='#2E7D32'>- {_brl_dup(conta_desconto)}</font>")
        desc_data.append([Paragraph(" | ".join(partes_ajuste), desc_info_style)])

    if obs:
        desc_data.append([Paragraph(f"<b>Obs:</b> {obs}", ParagraphStyle('Obs', fontSize=8, textColor=colors.gray, leading=11, wordWrap='CJK'))])
    
    desc_table = Table(desc_data, colWidths=[19*cm])
    desc_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#f0f0f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(desc_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Texto de reconhecimento
    elements.append(Paragraph(
        "<b>RECONHEÇO(EMOS) A EXATIDÃO DESTA DUPLICATA NA IMPORTÂNCIA ACIMA QUE PAGAREI(EMOS) À " +
        f"{empresa_nome} OU À SUA ORDEM NA PRAÇA E VENCIMENTO INDICADOS.</b>",
        ParagraphStyle('Reconhece', fontSize=7, alignment=1, leading=9)
    ))
    elements.append(Spacer(1, 0.4*cm))
    
    # Assinaturas
    assin_data = [
        [Paragraph("DATA DO ACEITE", label_style), Paragraph("ASSINATURA DO SACADO", label_style), Paragraph("ASSINATURA DO SACADOR", label_style)],
        [Paragraph("____/____/________", value_style), Paragraph("_" * 25, value_style), Paragraph("_" * 25, value_style)],
    ]
    assin_table = Table(assin_data, colWidths=[6*cm, 6.5*cm, 6.5*cm])
    assin_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(assin_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    await create_audit_log(current_user, "export", "duplicata", item_id, f"Duplicata: {item.get('descricao', item_id)}")
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CRA_Duplicata_{item_id[:8]}.pdf"}
    )


# Endpoint para exportar extrato de conta bancária
@exports_all_router.get("/export/extrato-bancario/{conta_id}")
async def export_extrato_bancario(
    conta_id: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Exporta extrato de uma conta bancária específica em PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    # Buscar a conta bancária
    conta = await db.contas_bancarias.find_one({"id": conta_id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")
    
    # Buscar movimentações (contas a pagar quitadas + contas a receber quitadas vinculadas a esta conta)
    movimentacoes = []
    
    # Filtro de data
    date_filter = {}
    if data_inicio:
        date_filter["$gte"] = data_inicio
    if data_fim:
        date_filter["$lte"] = data_fim
    
    # Buscar contas a pagar quitadas desta conta
    pagar_filter = {"conta_bancaria_id": conta_id, "status": "quitada"}
    if date_filter:
        pagar_filter["data_pagamento"] = date_filter
    
    contas_pagar = await db.contas_pagar.find(pagar_filter, {"_id": 0}).to_list(500)
    for cp in contas_pagar:
        movimentacoes.append({
            "data": cp.get("data_pagamento", cp.get("data_vencimento", "")),
            "tipo": "SAÍDA",
            "descricao": cp.get("descricao", ""),
            "documento": cp.get("numero_doc", ""),
            "favorecido": cp.get("fornecedor_nome", ""),
            "valor": -abs(cp.get("valor_final") or cp.get("valor", 0)),
        })
    
    # Buscar contas a receber quitadas desta conta
    receber_filter = {"conta_bancaria_id": conta_id, "status": "quitada"}
    if date_filter:
        receber_filter["data_recebimento"] = date_filter
    
    contas_receber = await db.contas_receber.find(receber_filter, {"_id": 0}).to_list(500)
    for cr in contas_receber:
        movimentacoes.append({
            "data": cr.get("data_recebimento", cr.get("data_vencimento", "")),
            "tipo": "ENTRADA",
            "descricao": cr.get("descricao", ""),
            "documento": cr.get("numero_doc", ""),
            "favorecido": cr.get("cliente_nome", ""),
            "valor": abs(cr.get("valor_final") or cr.get("valor", 0)),
        })
    
    # Ordenar por data
    movimentacoes.sort(key=lambda x: x.get("data", ""))
    
    # Calcular totais
    total_entradas = sum(m["valor"] for m in movimentacoes if m["valor"] > 0)
    total_saidas = sum(m["valor"] for m in movimentacoes if m["valor"] < 0)
    
    # Gerar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#D4A000'), spaceAfter=12)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey, spaceAfter=6)
    
    elements = []
    
    # Cabeçalho
    elements.append(Paragraph("CRA Construtora", title_style))
    elements.append(Paragraph(f"Extrato Bancário - {conta['nome']}", styles['Heading2']))
    elements.append(Paragraph(f"Banco: {conta['banco']} | Agência: {conta['agencia']} | Conta: {conta['conta']}", subtitle_style))
    
    if data_inicio or data_fim:
        periodo = f"Período: {data_inicio or 'Início'} até {data_fim or 'Atual'}"
        elements.append(Paragraph(periodo, subtitle_style))
    
    elements.append(Spacer(1, 20))
    
    # Resumo
    resumo_data = [
        ["RESUMO DO PERÍODO", ""],
        ["Total de Entradas:", f"R$ {total_entradas:,.2f}"],
        ["Total de Saídas:", f"R$ {abs(total_saidas):,.2f}"],
        ["Saldo do Período:", f"R$ {(total_entradas + total_saidas):,.2f}"],
        ["Saldo Atual da Conta:", f"R$ {conta.get('saldo_atual', 0):,.2f}"],
    ]
    
    resumo_table = Table(resumo_data, colWidths=[200, 150])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4A000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('SPAN', (0, 0), (-1, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F0F0F0')),
    ]))
    elements.append(resumo_table)
    elements.append(Spacer(1, 20))
    
    # Tabela de movimentações
    if movimentacoes:
        elements.append(Paragraph("Movimentações", styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        mov_data = [["Data", "Tipo", "Descrição", "Documento", "Favorecido", "Valor"]]
        for m in movimentacoes:
            valor_str = f"R$ {m['valor']:,.2f}"
            mov_data.append([
                m.get("data", "")[:10] if m.get("data") else "",
                m["tipo"],
                m["descricao"][:30] if m.get("descricao") else "",
                m.get("documento", "")[:15] if m.get("documento") else "",
                m.get("favorecido", "")[:20] if m.get("favorecido") else "",
                valor_str
            ])
        
        mov_table = Table(mov_data, colWidths=[60, 50, 120, 70, 100, 80])
        mov_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4A000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(mov_table)
    else:
        elements.append(Paragraph("Nenhuma movimentação encontrada no período.", subtitle_style))
    
    # Rodapé
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    
    doc.build(elements)
    buffer.seek(0)
    
    # Registrar na auditoria
    await create_audit_log(current_user, "export", "extrato_bancario", conta_id, conta["nome"])
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Extrato_{conta['nome'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )


# ============ EXCEL/OFX EXPORT ROUTES ============
import xlsxwriter

async def generate_excel_report(category: str, data: list, title: str) -> io.BytesIO:
    """Gera um relatório Excel formatado"""
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
    worksheet = workbook.add_worksheet('Dados')
    
    # Formatos
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#E31A1A',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
    money_format = workbook.add_format({'border': 1, 'num_format': 'R$ #,##0.00', 'valign': 'vcenter'})
    date_format = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy', 'valign': 'vcenter'})
    
    def fmt_date_xl(val):
        """Converte YYYY-MM-DD para DD/MM/AAAA como string"""
        if not val:
            return ""
        s = str(val).strip()[:10]
        if len(s) == 10 and s[4] == '-':
            return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
        return s
    
    def fmt_money_xl(val):
        """Converte valor para float seguro"""
        try:
            return float(val or 0)
        except (ValueError, TypeError):
            return 0.0
    
    def write_headers(headers):
        worksheet.set_row(0, 18)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
    
    # Definir headers e dados baseado na categoria
    if category == "contas_pagar":
        headers = ["Fornecedor", "Vencimento", "Quitação", "Valor", "Descrição", "Status", "Centro de Custo", "Plano de Contas"]
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(1, 1, 14)
        worksheet.set_column(2, 2, 14)
        worksheet.set_column(3, 3, 16)
        worksheet.set_column(4, 4, 35)
        worksheet.set_column(5, 5, 12)
        worksheet.set_column(6, 6, 22)
        worksheet.set_column(7, 7, 22)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("fornecedor_nome", ""), cell_format)
            worksheet.write(row, 1, fmt_date_xl(item.get("data_vencimento")), cell_format)
            worksheet.write(row, 2, fmt_date_xl(item.get("data_pagamento")), cell_format)
            worksheet.write(row, 3, fmt_money_xl(item.get("valor")), money_format)
            worksheet.write(row, 4, item.get("descricao", ""), cell_format)
            worksheet.write(row, 5, item.get("status", "").capitalize(), cell_format)
            worksheet.write(row, 6, item.get("centro_custo", "") or item.get("centro_custo_nome", ""), cell_format)
            worksheet.write(row, 7, item.get("plano_conta_nome", "") or item.get("plano_contas_nome", ""), cell_format)
    
    elif category == "contas_receber":
        headers = ["Cliente", "Vencimento", "Recebimento", "Valor", "Descrição", "Status", "Centro de Custo", "Plano de Contas"]
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(1, 1, 14)
        worksheet.set_column(2, 2, 14)
        worksheet.set_column(3, 3, 16)
        worksheet.set_column(4, 4, 35)
        worksheet.set_column(5, 5, 12)
        worksheet.set_column(6, 6, 22)
        worksheet.set_column(7, 7, 22)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("cliente_nome", ""), cell_format)
            worksheet.write(row, 1, fmt_date_xl(item.get("data_vencimento")), cell_format)
            worksheet.write(row, 2, fmt_date_xl(item.get("data_recebimento")), cell_format)
            worksheet.write(row, 3, fmt_money_xl(item.get("valor")), money_format)
            worksheet.write(row, 4, item.get("descricao", ""), cell_format)
            worksheet.write(row, 5, item.get("status", "").capitalize(), cell_format)
            worksheet.write(row, 6, item.get("centro_custo", "") or item.get("centro_custo_nome", ""), cell_format)
            worksheet.write(row, 7, item.get("plano_conta_nome", "") or item.get("plano_contas_nome", ""), cell_format)
    
    elif category == "machines":
        headers = ["Nome", "Placa", "Marca", "Modelo", "Ano", "Status", "Categoria"]
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(1, 1, 14)
        worksheet.set_column(6, 6, 20)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            status = "Operacional" if item.get("status") == "operational" else "Em Manutenção"
            worksheet.write(row, 0, item.get("name", ""), cell_format)
            worksheet.write(row, 1, item.get("plate", ""), cell_format)
            worksheet.write(row, 2, item.get("brand", ""), cell_format)
            worksheet.write(row, 3, item.get("model", ""), cell_format)
            worksheet.write(row, 4, item.get("year", ""), cell_format)
            worksheet.write(row, 5, status, cell_format)
            worksheet.write(row, 6, item.get("category_name", ""), cell_format)
    
    elif category == "cadastros":
        headers = ["Nome/Razão Social", "CPF/CNPJ", "Tipo", "Telefone", "Email", "Cidade", "Status"]
        worksheet.set_column(0, 0, 35)
        worksheet.set_column(1, 1, 18)
        worksheet.set_column(4, 4, 28)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("nome_razao", ""), cell_format)
            worksheet.write(row, 1, item.get("cpf_cnpj", ""), cell_format)
            worksheet.write(row, 2, item.get("tipo_cadastro", "").capitalize(), cell_format)
            worksheet.write(row, 3, item.get("telefone", "") or item.get("celular", ""), cell_format)
            worksheet.write(row, 4, item.get("email", ""), cell_format)
            worksheet.write(row, 5, item.get("cidade", ""), cell_format)
            worksheet.write(row, 6, item.get("status", "").capitalize(), cell_format)
    
    elif category == "alugueis":
        headers = ["Cliente", "Vencimento", "Data Entrega", "Valor", "Máquina", "Status", "Nº Contrato"]
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(4, 4, 24)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("cliente_nome", ""), cell_format)
            worksheet.write(row, 1, fmt_date_xl(item.get("data_vencimento")), cell_format)
            worksheet.write(row, 2, fmt_date_xl(item.get("data_entrega")), cell_format)
            worksheet.write(row, 3, fmt_money_xl(item.get("valor")), money_format)
            worksheet.write(row, 4, item.get("maquina_nome", ""), cell_format)
            worksheet.write(row, 5, item.get("status", "").capitalize(), cell_format)
            worksheet.write(row, 6, item.get("numero_contrato", ""), cell_format)
    
    elif category == "maintenances":
        headers = ["Equipamento", "Data", "Valor", "Peça", "Tipo", "Troca de Óleo"]
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(3, 3, 28)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            tipo = "Preventiva" if item.get("maintenance_type") == "preventiva" else "Corretiva"
            worksheet.write(row, 0, item.get("machine_name", "") or item.get("machine_id", ""), cell_format)
            worksheet.write(row, 1, fmt_date_xl(item.get("replacement_date")), cell_format)
            worksheet.write(row, 2, fmt_money_xl(item.get("part_value")), money_format)
            worksheet.write(row, 3, item.get("part_name", ""), cell_format)
            worksheet.write(row, 4, tipo, cell_format)
            worksheet.write(row, 5, "Sim" if item.get("is_oil_change") else "Não", cell_format)
    
    elif category == "stock_items":
        headers = ["Nome", "Código", "Categoria", "Quantidade", "Qtd. Mínima", "Preço Unitário"]
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 16)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("name", ""), cell_format)
            worksheet.write(row, 1, item.get("code", ""), cell_format)
            worksheet.write(row, 2, item.get("category", ""), cell_format)
            worksheet.write(row, 3, item.get("quantity", 0), cell_format)
            worksheet.write(row, 4, item.get("min_quantity", 0), cell_format)
            worksheet.write(row, 5, fmt_money_xl(item.get("unit_price")), money_format)
    
    elif category == "obras":
        headers = ["Cliente", "Data Início", "Data Fim", "Nome", "Local", "Status", "Contrato"]
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(3, 3, 30)
        worksheet.set_column(4, 4, 25)
        write_headers(headers)
        status_map_obras = {"em_andamento": "Em andamento", "concluida": "Concluída", "pausada": "Pausada"}
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("cliente", "") or item.get("cliente_nome", ""), cell_format)
            worksheet.write(row, 1, fmt_date_xl(item.get("start_date") or item.get("data_inicio")), cell_format)
            worksheet.write(row, 2, fmt_date_xl(item.get("end_date") or item.get("data_fim")), cell_format)
            worksheet.write(row, 3, item.get("name", "") or item.get("nome", ""), cell_format)
            worksheet.write(row, 4, item.get("location", "") or item.get("local", ""), cell_format)
            worksheet.write(row, 5, status_map_obras.get(item.get("status", ""), item.get("status", "")), cell_format)
            worksheet.write(row, 6, item.get("numero_contrato", ""), cell_format)
    
    elif category == "produtos_admin":
        headers = ["Código", "Descrição", "Unidade", "Preço", "Estoque"]
        worksheet.set_column(1, 1, 35)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("codigo", ""), cell_format)
            worksheet.write(row, 1, item.get("descricao", ""), cell_format)
            worksheet.write(row, 2, item.get("unidade", ""), cell_format)
            worksheet.write(row, 3, fmt_money_xl(item.get("preco")), money_format)
            worksheet.write(row, 4, item.get("estoque", 0), cell_format)
    
    elif category == "ordens_servico":
        headers = ["Cliente", "Data", "Valor Total", "Nº OS", "Descrição", "Status"]
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(4, 4, 35)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("cliente_nome", ""), cell_format)
            worksheet.write(row, 1, fmt_date_xl(item.get("data_abertura") or item.get("created_at")), cell_format)
            worksheet.write(row, 2, fmt_money_xl(item.get("valor_total")), money_format)
            worksheet.write(row, 3, item.get("numero", ""), cell_format)
            worksheet.write(row, 4, item.get("descricao", ""), cell_format)
            worksheet.write(row, 5, item.get("status", "").capitalize(), cell_format)
    
    elif category == "contas_bancarias":
        headers = ["Nome", "Banco", "Agência", "Conta", "Tipo", "Titular", "Saldo Atual"]
        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(5, 5, 28)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("nome", ""), cell_format)
            worksheet.write(row, 1, item.get("banco", ""), cell_format)
            worksheet.write(row, 2, item.get("agencia", ""), cell_format)
            worksheet.write(row, 3, item.get("conta", ""), cell_format)
            worksheet.write(row, 4, item.get("tipo", ""), cell_format)
            worksheet.write(row, 5, item.get("titular", ""), cell_format)
            worksheet.write(row, 6, fmt_money_xl(item.get("saldo_atual") or item.get("saldo")), money_format)
    
    elif category == "funcionarios":
        headers = ["Nome", "CPF", "Cargo", "Setor", "Admissão", "Salário", "Status"]
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(2, 2, 22)
        write_headers(headers)
        status_map_func = {"ativo": "Ativo", "ferias": "Férias", "afastado": "Afastado", "desligado": "Desligado"}
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("nome", ""), cell_format)
            worksheet.write(row, 1, item.get("cpf", ""), cell_format)
            worksheet.write(row, 2, item.get("cargo", ""), cell_format)
            worksheet.write(row, 3, item.get("setor", ""), cell_format)
            worksheet.write(row, 4, fmt_date_xl(item.get("data_admissao")), cell_format)
            worksheet.write(row, 5, fmt_money_xl(item.get("salario")), money_format)
            worksheet.write(row, 6, status_map_func.get(item.get("status", ""), item.get("status", "")), cell_format)
    
    elif category == "folha_pagamento":
        headers = ["Funcionário", "Competência", "Salário Bruto", "Descontos", "Salário Líquido"]
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 14)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("funcionario_nome", ""), cell_format)
            worksheet.write(row, 1, item.get("competencia", ""), cell_format)
            worksheet.write(row, 2, fmt_money_xl(item.get("salario_bruto")), money_format)
            worksheet.write(row, 3, fmt_money_xl(item.get("total_descontos")), money_format)
            worksheet.write(row, 4, fmt_money_xl(item.get("salario_liquido")), money_format)
    
    elif category == "ponto_registros":
        headers = ["Funcionário", "Data", "Entrada", "Saída", "Horas Trabalhadas"]
        worksheet.set_column(0, 0, 30)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("funcionario_nome", ""), cell_format)
            worksheet.write(row, 1, fmt_date_xl(item.get("data")), cell_format)
            worksheet.write(row, 2, item.get("entrada", ""), cell_format)
            worksheet.write(row, 3, item.get("saida", ""), cell_format)
            worksheet.write(row, 4, item.get("horas_trabalhadas", ""), cell_format)
    
    elif category == "ferias":
        headers = ["Funcionário", "Período Aquisitivo", "Início", "Fim", "Dias", "Status"]
        worksheet.set_column(0, 0, 30)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("funcionario_nome", ""), cell_format)
            worksheet.write(row, 1, item.get("periodo_aquisitivo", ""), cell_format)
            worksheet.write(row, 2, fmt_date_xl(item.get("data_inicio")), cell_format)
            worksheet.write(row, 3, fmt_date_xl(item.get("data_fim")), cell_format)
            worksheet.write(row, 4, item.get("dias", ""), cell_format)
            worksheet.write(row, 5, item.get("status", "").capitalize(), cell_format)
    
    elif category == "epi_fichas":
        headers = ["Funcionário", "EPI", "CA", "Data Entrega", "Validade", "Quantidade"]
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 25)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("funcionario_nome", ""), cell_format)
            worksheet.write(row, 1, item.get("epi_nome", ""), cell_format)
            worksheet.write(row, 2, item.get("ca", ""), cell_format)
            worksheet.write(row, 3, fmt_date_xl(item.get("data_entrega")), cell_format)
            worksheet.write(row, 4, fmt_date_xl(item.get("data_validade")), cell_format)
            worksheet.write(row, 5, item.get("quantidade", 1), cell_format)
    
    elif category == "plano_contas":
        headers = ["Código", "Nome", "Tipo", "Conta Pai"]
        worksheet.set_column(1, 1, 30)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("codigo", ""), cell_format)
            worksheet.write(row, 1, item.get("nome", ""), cell_format)
            worksheet.write(row, 2, "Receita" if item.get("tipo") == "receita" else "Despesa", cell_format)
            worksheet.write(row, 3, item.get("pai_nome", "Raiz"), cell_format)
    
    elif category == "centros_custo":
        headers = ["Código", "Nome", "Descrição"]
        worksheet.set_column(1, 1, 28)
        worksheet.set_column(2, 2, 35)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("codigo", ""), cell_format)
            worksheet.write(row, 1, item.get("nome", ""), cell_format)
            worksheet.write(row, 2, item.get("descricao", ""), cell_format)
    
    elif category == "medicoes":
        headers = ["Descrição", "Obra", "Valor", "Data", "Status"]
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 25)
        write_headers(headers)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("descricao", ""), cell_format)
            worksheet.write(row, 1, item.get("obra_nome", "") or item.get("obra", ""), cell_format)
            worksheet.write(row, 2, fmt_money_xl(item.get("valor")), money_format)
            worksheet.write(row, 3, fmt_date_xl(item.get("data") or item.get("created_at")), cell_format)
            worksheet.write(row, 4, item.get("status", "").capitalize(), cell_format)
    
    else:
        # Genérico: pegar as chaves relevantes do primeiro item (excluindo IDs internos)
        SKIP_KEYS = {"_id", "password", "id", "created_by"}
        if data:
            keys = [k for k in data[0].keys() if k not in SKIP_KEYS][:12]
            for col, key in enumerate(keys):
                label = key.replace("_", " ").title()
                worksheet.write(0, col, label, header_format)
                worksheet.set_column(col, col, 20)
            for row, item in enumerate(data, 1):
                for col, key in enumerate(keys):
                    value = item.get(key, "")
                    # Detectar campos de data (YYYY-MM-DD)
                    if isinstance(value, str) and len(value) >= 10 and value[4:5] == '-':
                        worksheet.write(row, col, fmt_date_xl(value), cell_format)
                    elif isinstance(value, (int, float)):
                        worksheet.write(row, col, value, cell_format)
                    else:
                        worksheet.write(row, col, str(value)[:60] if value else "", cell_format)
    
    # Adicionar linha de total quando houver valores monetários
    total_valor = 0
    campo_valor = None
    col_valor = 1
    row_total = len(data) + 2

    if category in ["contas_pagar", "contas_receber"]:
        campo_valor = "valor"; col_valor = 3
    elif category == "alugueis":
        campo_valor = "valor"; col_valor = 3
    elif category == "maintenances":
        campo_valor = "part_value"; col_valor = 2
    elif category == "ordens_servico":
        campo_valor = "valor_total"; col_valor = 2
    elif category == "folha_pagamento":
        campo_valor = "salario_liquido"; col_valor = 2
    elif category == "contas_bancarias":
        campo_valor = "saldo_atual"; col_valor = 6
    
    if campo_valor:
        for item in data:
            try:
                valor = item.get(campo_valor, 0) or 0
                total_valor += float(valor)
            except (ValueError, TypeError):
                pass
        
        if total_valor > 0:
            # Formatos para o total
            total_label_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFE0E0',
                'border': 2,
                'align': 'right',
                'valign': 'vcenter',
                'font_size': 11
            })
            total_value_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFE0E0',
                'border': 2,
                'num_format': 'R$ #,##0.00',
                'valign': 'vcenter',
                'font_size': 11
            })
            
            # Escrever o total
            worksheet.write(row_total, col_valor - 1, "TOTAL GERAL:", total_label_format)
            worksheet.write(row_total, col_valor, total_valor, total_value_format)
    
    workbook.close()
    buffer.seek(0)
    return buffer

def generate_ofx_content(data: list, account_type: str = "pagar") -> str:
    """Gera conteúdo OFX para importação em sistemas financeiros"""
    now = datetime.now()
    
    ofx_content = f"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<DTSERVER>{now.strftime('%Y%m%d%H%M%S')}
<LANGUAGE>POR
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<STMTRS>
<CURDEF>BRL
<BANKACCTFROM>
<BANKID>001
<ACCTID>CRA_CONSTRUTORA
<ACCTTYPE>CHECKING
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>{now.strftime('%Y%m%d')}
<DTEND>{now.strftime('%Y%m%d')}
"""
    
    for item in data:
        trntype = "DEBIT" if account_type == "pagar" else "CREDIT"
        valor = float(item.get("valor", 0))
        if account_type == "pagar":
            valor = -abs(valor)  # Negativo para débitos
        else:
            valor = abs(valor)  # Positivo para créditos
        
        data_venc = item.get("data_vencimento", now.strftime("%Y-%m-%d"))
        if data_venc:
            data_venc = data_venc.replace("-", "")[:8]
        else:
            data_venc = now.strftime('%Y%m%d')
        
        fitid = item.get("id", str(uuid.uuid4()))[:20]
        memo = item.get("descricao", "")[:32]
        
        ofx_content += f"""<STMTTRN>
<TRNTYPE>{trntype}
<DTPOSTED>{data_venc}
<TRNAMT>{valor:.2f}
<FITID>{fitid}
<MEMO>{memo}
</STMTTRN>
"""
    
    ofx_content += """</BANKTRANLIST>
<LEDGERBAL>
<BALAMT>0.00
<DTASOF>""" + now.strftime('%Y%m%d%H%M%S') + """
</LEDGERBAL>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""
    
    return ofx_content

@exports_all_router.get("/export/excel/{category}")
async def export_excel(
    category: str,
    centro_custo: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    forma_pagamento: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Exporta dados de uma categoria em Excel (com filtro opcional de período e forma de pagamento)"""
    
    category_configs = {
        "machines": {"collection": "machines", "title": "Maquinas", "filter": {}},
        "maintenances": {"collection": "maintenances", "title": "Manutencoes", "filter": {}},
        "stock_items": {"collection": "stock_items", "title": "Estoque", "filter": {}},
        "obras": {"collection": "obras", "title": "Obras", "filter": {}},
        "contas_pagar": {"collection": "contas_pagar", "title": "Contas_a_Pagar", "filter": {}},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Pendentes", "filter": {"status": "em_aberto"}},
        "contas_pagar_pendentes": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Pendentes", "filter": {"status": "em_aberto"}},
        "contas_pagar_quitada": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Quitadas", "filter": {"status": "quitada"}},
        "contas_pagar_quitadas": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Quitadas", "filter": {"status": "quitada"}},
        "contas_pagar_vencidas": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Vencidas", "filter": {"status": "em_aberto"}},
        "contas_receber": {"collection": "contas_receber", "title": "Contas_a_Receber", "filter": {}},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas_a_Receber_Pendentes", "filter": {"status": "em_aberto"}},
        "contas_receber_pendentes": {"collection": "contas_receber", "title": "Contas_a_Receber_Pendentes", "filter": {"status": "em_aberto"}},
        "contas_receber_quitada": {"collection": "contas_receber", "title": "Contas_a_Receber_Recebidas", "filter": {"status": "quitada"}},
        "contas_receber_quitadas": {"collection": "contas_receber", "title": "Contas_a_Receber_Recebidas", "filter": {"status": "quitada"}},
        "contas_receber_recebidas": {"collection": "contas_receber", "title": "Contas_a_Receber_Recebidas", "filter": {"status": "quitada"}},
        "contas_receber_vencidas": {"collection": "contas_receber", "title": "Contas_a_Receber_Vencidas", "filter": {"status": "em_aberto"}},
        "cadastros": {"collection": "cadastros", "title": "Cadastros", "filter": {}},
        "cadastros_clientes": {"collection": "cadastros", "title": "Clientes", "filter": {"tipo_cadastro": "cliente"}},
        "cadastros_fornecedores": {"collection": "cadastros", "title": "Fornecedores", "filter": {"tipo_cadastro": "fornecedor"}},
        "produtos_admin": {"collection": "produtos_admin", "title": "Produtos", "filter": {}},
        "alugueis": {"collection": "alugueis", "title": "Alugueis", "filter": {}},
        "medicoes": {"collection": "medicoes", "title": "Medicoes", "filter": {}},
    }
    
    if category not in category_configs:
        raise HTTPException(status_code=400, detail=f"Categoria '{category}' inválida para Excel")
    
    config = category_configs[category]
    excel_filter = dict(config["filter"])
    
    # Aplicar filtro de centro de custo para coleções financeiras
    FINANCIAL_COLLECTIONS = ["contas_pagar", "contas_receber"]
    if centro_custo and centro_custo != "todos" and config["collection"] in FINANCIAL_COLLECTIONS:
        excel_filter["centro_custo"] = centro_custo

    # Aplicar filtro global de período
    excel_filter = _apply_period_filter(config["collection"], excel_filter, data_inicio, data_fim)
    # Filtro de forma de pagamento (apenas contas_pagar/receber)
    excel_filter = _apply_forma_pagamento_filter(config["collection"], excel_filter, forma_pagamento)

    collection = db[config["collection"]]
    data = await collection.find(excel_filter, {"_id": 0}).to_list(5000)
    
    excel_buffer = await generate_excel_report(config["collection"], data, config["title"])
    
    await create_audit_log(
        user=current_user,
        action="exportar excel",
        entity_type="relatório Excel",
        entity_id=category,
        entity_name=config["title"],
        details=f"Exportou {len(data)} registros",
        module="Exportação"
    )
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=CRA_{config['title']}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        }
    )

@exports_all_router.get("/export/ofx/{category}")
async def export_ofx(
    category: str,
    centro_custo: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    forma_pagamento: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Exporta dados financeiros em formato OFX (com filtro opcional de período e forma de pagamento)"""
    
    valid_categories = {
        "contas_pagar": {"collection": "contas_pagar", "title": "Contas_a_Pagar", "type": "pagar"},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Pendentes", "type": "pagar", "filter": {"status": "em_aberto"}},
        "contas_pagar_pendentes": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Pendentes", "type": "pagar", "filter": {"status": "em_aberto"}},
        "contas_pagar_quitada": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Quitadas", "type": "pagar", "filter": {"status": "quitada"}},
        "contas_pagar_quitadas": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Quitadas", "type": "pagar", "filter": {"status": "quitada"}},
        "contas_receber": {"collection": "contas_receber", "title": "Contas_a_Receber", "type": "receber"},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas_a_Receber_Pendentes", "type": "receber", "filter": {"status": "em_aberto"}},
        "contas_receber_pendentes": {"collection": "contas_receber", "title": "Contas_a_Receber_Pendentes", "type": "receber", "filter": {"status": "em_aberto"}},
        "contas_receber_quitada": {"collection": "contas_receber", "title": "Contas_a_Receber_Recebidas", "type": "receber", "filter": {"status": "quitada"}},
        "contas_receber_quitadas": {"collection": "contas_receber", "title": "Contas_a_Receber_Recebidas", "type": "receber", "filter": {"status": "quitada"}},
        "contas_receber_recebidas": {"collection": "contas_receber", "title": "Contas_a_Receber_Recebidas", "type": "receber", "filter": {"status": "quitada"}},
    }
    
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail="OFX só está disponível para contas a pagar/receber")
    
    config = valid_categories[category]
    query_filter = dict(config.get("filter", {}))
    if centro_custo and centro_custo != "todos":
        query_filter["centro_custo"] = centro_custo
    # Filtro de período
    query_filter = _apply_period_filter(config["collection"], query_filter, data_inicio, data_fim)
    # Filtro de forma de pagamento
    query_filter = _apply_forma_pagamento_filter(config["collection"], query_filter, forma_pagamento)
    collection = db[config["collection"]]
    data = await collection.find(query_filter, {"_id": 0}).to_list(5000)
    
    ofx_content = generate_ofx_content(data, config["type"])
    
    await create_audit_log(
        user=current_user,
        action="exportar ofx",
        entity_type="relatório OFX",
        entity_id=category,
        entity_name=config["title"],
        details=f"Exportou {len(data)} registros",
        module="Exportação"
    )
    
    return StreamingResponse(
        io.BytesIO(ofx_content.encode('latin-1')),
        media_type="application/x-ofx",
        headers={
            "Content-Disposition": f"attachment; filename=CRA_{config['title']}_{datetime.now().strftime('%Y%m%d_%H%M')}.ofx"
        }
    )


# ============ FILE UPLOAD/ATTACHMENT ROUTES ============

from fastapi.staticfiles import StaticFiles
import shutil

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Relatório de Contas por Conta Bancária
@exports_all_router.get("/export/relatorio-conta-bancaria")
async def export_relatorio_conta_bancaria(
    conta_bancaria_id: str,
    tipo: str = "pagar",  # "pagar", "receber" ou "todas"
    status: str = "todas",  # "todas", "pendente", "quitada", "parcial"
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    forma_pagamento: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Exporta relatório de contas a pagar ou receber filtrado por conta bancária, status, período e forma de pagamento"""
    
    # Buscar conta bancária
    conta_bancaria = await db.contas_bancarias.find_one({"id": conta_bancaria_id}, {"_id": 0})
    if not conta_bancaria:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")
    
    # Construir filtro base
    filtro_base = {"conta_bancaria_id": conta_bancaria_id}
    
    if status == "pendente":
        filtro_base["status"] = {"$in": ["pendente", "em_aberto"]}
    elif status == "quitada":
        filtro_base["status"] = "quitada"
    elif status == "parcial":
        filtro_base["status"] = "parcial"

    # Aplicar filtro global de período (data_vencimento para contas)
    filtro_base = _apply_period_filter("contas_pagar", filtro_base, data_inicio, data_fim)
    # Filtro de forma de pagamento
    filtro_base = _apply_forma_pagamento_filter("contas_pagar", filtro_base, forma_pagamento)
    
    # Buscar dados conforme o tipo
    data = []
    if tipo == "pagar":
        data = await db.contas_pagar.find(filtro_base, {"_id": 0}).sort("data_vencimento", -1).to_list(5000)
        for d in data:
            d["_tipo"] = "pagar"
        titulo = "Contas a Pagar"
    elif tipo == "receber":
        data = await db.contas_receber.find(filtro_base, {"_id": 0}).sort("data_vencimento", -1).to_list(5000)
        for d in data:
            d["_tipo"] = "receber"
        titulo = "Contas a Receber"
    else:  # todas
        data_pagar = await db.contas_pagar.find(filtro_base, {"_id": 0}).sort("data_vencimento", -1).to_list(5000)
        data_receber = await db.contas_receber.find(filtro_base, {"_id": 0}).sort("data_vencimento", -1).to_list(5000)
        for d in data_pagar:
            d["_tipo"] = "pagar"
        for d in data_receber:
            d["_tipo"] = "receber"
        data = data_pagar + data_receber
        # Ordenar por data de vencimento
        data.sort(key=lambda x: x.get("data_vencimento", ""), reverse=True)
        titulo = "Contas a Pagar e Receber"
    
    # Adicionar status ao título
    if status == "pendente":
        titulo += " - Pendentes"
    elif status == "quitada":
        titulo += " - Quitadas"
    elif status == "parcial":
        titulo += " - Parcialmente Pagas"
    else:
        titulo += " - Todas"
    
    # Gerar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.black, alignment=TA_CENTER, spaceAfter=10)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=20)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=9, textColor=colors.black, spaceAfter=5)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, textColor=colors.black, wordWrap='LTR', leading=10)
    header_cell_style = ParagraphStyle('HeaderCellStyle', parent=styles['Normal'], fontSize=8, textColor=colors.white, fontName='Helvetica-Bold', wordWrap='LTR', leading=10)
    
    def cell(text, is_header=False):
        if text is None:
            text = "-"
        return Paragraph(str(text), header_cell_style if is_header else cell_style)
    
    elements = []
    
    # Logo
    try:
        logo_path = "/app/frontend/public/logo.png"
        if os.path.exists(logo_path):
            logo = RLImage(logo_path, width=2.5*cm, height=2.5*cm, kind='proportional')
            elements.append(logo)
            elements.append(Spacer(1, 10))
    except Exception as e:
        logging.warning(f"Não foi possível carregar o logo: {e}")
    
    # Título
    elements.append(Paragraph("CRA Construtora", title_style))
    elements.append(Paragraph(f"Relatório de {titulo}", title_style))
    
    # Info da conta bancária
    banco_info = f"{conta_bancaria.get('banco', '')} - Ag: {conta_bancaria.get('agencia', '')} / CC: {conta_bancaria.get('conta', '')}"
    elements.append(Paragraph(f"Conta Bancária: {banco_info}", subtitle_style))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 15))
    
    # Resumo
    total_valor = sum(c.get("valor_final") or c.get("valor", 0) for c in data)
    total_pago = sum(c.get("valor_pago", 0) or c.get("valor_recebido", 0) or 0 for c in data)
    total_saldo = total_valor - total_pago
    
    elements.append(Paragraph(f"Total de registros: {len(data)}", normal_style))
    elements.append(Paragraph(f"Valor Total: R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), normal_style))
    if status != "pendente":
        elements.append(Paragraph(f"Total Pago/Recebido: R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), normal_style))
        elements.append(Paragraph(f"Saldo Restante: R$ {total_saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), normal_style))
    elements.append(Spacer(1, 15))
    
    if not data:
        elements.append(Paragraph("Nenhum registro encontrado para os filtros selecionados.", normal_style))
    else:
        # Tabela
        if tipo == "pagar":
            headers = [
                cell("Fornecedor", True), 
                cell("Descrição", True), 
                cell("Vencimento", True), 
                cell("Quitação", True),
                cell("Valor", True),
                cell("Pago", True),
                cell("Status", True)
            ]
        else:
            headers = [
                cell("Cliente", True), 
                cell("Descrição", True), 
                cell("Vencimento", True), 
                cell("Recebimento", True),
                cell("Valor", True),
                cell("Recebido", True),
                cell("Status", True)
            ]
        
        table_data = [headers]
        for item in data:
            valor = item.get("valor_final") or item.get("valor", 0)
            pago = item.get("valor_pago", 0) or item.get("valor_recebido", 0) or 0
            
            status_map = {
                "quitada": "Quitada",
                "parcial": "Parcial",
                "pendente": "Pendente",
                "em_aberto": "Em Aberto",
                "cancelada": "Cancelada"
            }
            status_text = status_map.get(item.get("status", ""), item.get("status", "-"))
            
            nome = item.get("fornecedor_nome", "") if tipo == "pagar" else item.get("cliente_nome", "")
            
            # Data de quitação
            if tipo == "pagar":
                data_quitacao = item.get("data_pagamento", "")
            else:
                data_quitacao = item.get("data_recebimento", "")
            
            if data_quitacao and len(str(data_quitacao)) >= 10:
                data_quitacao = str(data_quitacao)[:10]
            else:
                data_quitacao = "-"
            
            table_data.append([
                cell(nome[:25] if nome else "-"),
                cell((item.get("descricao", "") or "-")[:30]),
                cell(item.get("data_vencimento", "-")[:10] if item.get("data_vencimento") else "-"),
                cell(data_quitacao),
                cell(f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
                cell(f"R$ {pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
                cell(status_text)
            ])
        
        # Calcular larguras das colunas
        col_widths = [3*cm, 3.5*cm, 2.2*cm, 2.2*cm, 2.3*cm, 2.3*cm, 1.8*cm]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4A000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    # Log de auditoria
    await create_audit_log(
        user=current_user,
        action="exportar PDF",
        entity_type="relatório conta bancária",
        entity_id=conta_bancaria_id,
        entity_name=f"{titulo} - {banco_info}",
        details=f"Exportou {len(data)} registros",
        module="Exportação"
    )
    
    filename = f"CRA_Relatorio_{tipo.capitalize()}_{conta_bancaria.get('banco', 'Banco')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



# ============ EXTRATO DO PLANO DE CONTAS ============
@exports_all_router.get("/export/extrato-plano-contas")
async def export_extrato_plano_contas(
    plano_conta_id: Optional[str] = None,  # vazio = todos os planos
    data_inicio: Optional[str] = None,     # YYYY-MM-DD
    data_fim: Optional[str] = None,        # YYYY-MM-DD
    tipo: str = "ambos",                   # "pagar", "receber" ou "ambos"
    status: str = "todas",                 # "todas", "em_aberto", "quitada", "parcial"
    incluir_detalhes: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """Gera PDF do extrato do plano de contas no padrão da plataforma.

    - Resumo consolidado por plano/subconta no período (saldo a pagar / a receber)
    - Detalhamento de cada lançamento (Contas a Pagar e Contas a Receber) no período
    - Filtros: plano_conta_id (opcional), data_inicio, data_fim, tipo, status
    """
    # Filtro de período por data_vencimento (padrão financeiro)
    period_filter = {}
    if data_inicio:
        period_filter.setdefault("data_vencimento", {})["$gte"] = data_inicio
    if data_fim:
        period_filter.setdefault("data_vencimento", {})["$lte"] = data_fim

    # Filtro de status
    status_filter = {}
    if status == "em_aberto":
        status_filter["status"] = {"$in": ["em_aberto", "pendente"]}
    elif status == "quitada":
        status_filter["status"] = "quitada"
    elif status == "parcial":
        status_filter["status"] = "parcial"

    plano_filter = {}
    plano_doc = None
    if plano_conta_id:
        plano_doc = await db.plano_contas.find_one({"id": plano_conta_id}, {"_id": 0})
        if not plano_doc:
            raise HTTPException(status_code=404, detail="Plano de contas não encontrado")
        plano_filter = {"$or": [{"plano_conta_id": plano_conta_id}, {"subconta_id": plano_conta_id}]}

    base_filter = {**period_filter, **status_filter, **plano_filter}

    contas_pagar_data: List[dict] = []
    contas_receber_data: List[dict] = []
    if tipo in ("pagar", "ambos"):
        contas_pagar_data = await db.contas_pagar.find(base_filter, {"_id": 0}).sort("data_vencimento", 1).to_list(5000)
    if tipo in ("receber", "ambos"):
        contas_receber_data = await db.contas_receber.find(base_filter, {"_id": 0}).sort("data_vencimento", 1).to_list(5000)

    # Resumo agregado por plano/subconta
    resumo: dict = {}

    def _key(item):
        plano_nome = item.get("plano_conta_nome") or "(Sem plano)"
        subconta_nome = item.get("subconta_nome") or "—"
        return (plano_nome, subconta_nome)

    for c in contas_pagar_data:
        k = _key(c)
        r = resumo.setdefault(k, {"qtd_pagar": 0, "valor_pagar": 0.0, "qtd_receber": 0, "valor_receber": 0.0})
        r["qtd_pagar"] += 1
        r["valor_pagar"] += float(c.get("valor_final") or c.get("valor") or 0)
    for c in contas_receber_data:
        k = _key(c)
        r = resumo.setdefault(k, {"qtd_pagar": 0, "valor_pagar": 0.0, "qtd_receber": 0, "valor_receber": 0.0})
        r["qtd_receber"] += 1
        r["valor_receber"] += float(c.get("valor_final") or c.get("valor") or 0)

    # ====== Geração do PDF ======
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.black, alignment=TA_CENTER, spaceAfter=10)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=10)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#444"), spaceBefore=10, spaceAfter=8)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=9, textColor=colors.black, spaceAfter=5)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, textColor=colors.black, wordWrap='LTR', leading=10)
    header_cell_style = ParagraphStyle('HeaderCellStyle', parent=styles['Normal'], fontSize=8, textColor=colors.white, fontName='Helvetica-Bold', wordWrap='LTR', leading=10)

    def _cell(text, header=False):
        if text is None:
            text = "-"
        return Paragraph(str(text), header_cell_style if header else cell_style)

    def _brl(v):
        try:
            return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "R$ 0,00"

    def _fmt_data(d):
        if not d:
            return "-"
        s = str(d)[:10]
        if "-" in s and len(s) == 10:
            try:
                y, m, dd = s.split("-")
                return f"{dd}/{m}/{y}"
            except Exception:
                return s
        return s

    elements = []

    # Logo + cabeçalho padrão
    try:
        logo_path = "/app/frontend/public/logo.png"
        if os.path.exists(logo_path):
            elements.append(RLImage(logo_path, width=2.5*cm, height=2.5*cm, kind='proportional'))
            elements.append(Spacer(1, 8))
    except Exception:
        pass

    elements.append(Paragraph("CRA Construtora", title_style))
    elements.append(Paragraph("Extrato do Plano de Contas", title_style))

    # Subtítulos com filtros
    if plano_doc:
        elements.append(Paragraph(
            f"Plano: {plano_doc.get('codigo', '')} {('-' if plano_doc.get('codigo') else '')} {plano_doc.get('nome', '')}",
            subtitle_style,
        ))
    else:
        elements.append(Paragraph("Plano: Todos os planos cadastrados", subtitle_style))

    periodo_txt = "Período: "
    periodo_txt += _fmt_data(data_inicio) if data_inicio else "início dos registros"
    periodo_txt += " até "
    periodo_txt += _fmt_data(data_fim) if data_fim else "data atual"
    elements.append(Paragraph(periodo_txt, subtitle_style))

    status_label = {
        "em_aberto": "Apenas em aberto",
        "quitada": "Apenas quitadas",
        "parcial": "Apenas parcialmente pagas",
    }.get(status, "Todas (em aberto + quitadas + parciais)")
    elements.append(Paragraph(f"Status: {status_label}", subtitle_style))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 12))

    # ===== Resumo consolidado =====
    elements.append(Paragraph("Resumo por Plano / Subconta", section_style))
    if not resumo:
        elements.append(Paragraph("Nenhum lançamento encontrado para os filtros selecionados.", normal_style))
    else:
        cab = [
            _cell("Plano", True), _cell("Subconta", True),
            _cell("Qtd. a Pagar", True), _cell("Total a Pagar", True),
            _cell("Qtd. a Receber", True), _cell("Total a Receber", True),
            _cell("Saldo (R - P)", True),
        ]
        rows_resumo = [cab]
        total_p = total_r = 0.0
        qtd_p = qtd_r = 0
        for (plano_nome, subconta_nome), v in sorted(resumo.items()):
            saldo = (v["valor_receber"] or 0) - (v["valor_pagar"] or 0)
            rows_resumo.append([
                _cell(plano_nome[:30]),
                _cell(subconta_nome[:25]),
                _cell(str(v["qtd_pagar"])),
                _cell(_brl(v["valor_pagar"])),
                _cell(str(v["qtd_receber"])),
                _cell(_brl(v["valor_receber"])),
                _cell(_brl(saldo)),
            ])
            total_p += v["valor_pagar"]; total_r += v["valor_receber"]
            qtd_p += v["qtd_pagar"]; qtd_r += v["qtd_receber"]
        rows_resumo.append([
            _cell("TOTAL", True), _cell("", True),
            _cell(str(qtd_p), True), _cell(_brl(total_p), True),
            _cell(str(qtd_r), True), _cell(_brl(total_r), True),
            _cell(_brl(total_r - total_p), True),
        ])
        t_resumo = Table(rows_resumo, colWidths=[3.5*cm, 2.6*cm, 1.6*cm, 2.4*cm, 1.6*cm, 2.4*cm, 2.6*cm], repeatRows=1)
        t_resumo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4A000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFE6A1')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
        ]))
        elements.append(t_resumo)
        elements.append(Spacer(1, 12))

    # ===== Detalhamento (lançamentos) =====
    if incluir_detalhes:
        if contas_pagar_data:
            elements.append(Paragraph("Lançamentos — Contas a Pagar", section_style))
            cab_p = [
                _cell("Vencimento", True), _cell("Fornecedor", True),
                _cell("Descrição", True), _cell("Plano / Sub", True),
                _cell("Doc.", True), _cell("Valor", True), _cell("Status", True),
            ]
            rows_p = [cab_p]
            for c in contas_pagar_data:
                rows_p.append([
                    _cell(_fmt_data(c.get("data_vencimento"))),
                    _cell((c.get("fornecedor_nome") or "-")[:25]),
                    _cell((c.get("descricao") or "-")[:32]),
                    _cell(((c.get("plano_conta_nome") or "-") + (" / " + c.get("subconta_nome") if c.get("subconta_nome") else ""))[:25]),
                    _cell(c.get("numero_doc") or c.get("documento") or "-"),
                    _cell(_brl(c.get("valor_final") or c.get("valor"))),
                    _cell(c.get("status") or "-"),
                ])
            t_p = Table(rows_p, colWidths=[2.0*cm, 3.0*cm, 3.5*cm, 3.0*cm, 1.8*cm, 2.3*cm, 1.5*cm], repeatRows=1)
            t_p.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C62828')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fdecec')]),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ]))
            elements.append(t_p)
            elements.append(Spacer(1, 10))

        if contas_receber_data:
            elements.append(Paragraph("Lançamentos — Contas a Receber", section_style))
            cab_r = [
                _cell("Vencimento", True), _cell("Cliente", True),
                _cell("Descrição", True), _cell("Plano / Sub", True),
                _cell("Doc.", True), _cell("Valor", True), _cell("Status", True),
            ]
            rows_r = [cab_r]
            for c in contas_receber_data:
                rows_r.append([
                    _cell(_fmt_data(c.get("data_vencimento"))),
                    _cell((c.get("cliente_nome") or "-")[:25]),
                    _cell((c.get("descricao") or "-")[:32]),
                    _cell(((c.get("plano_conta_nome") or "-") + (" / " + c.get("subconta_nome") if c.get("subconta_nome") else ""))[:25]),
                    _cell(c.get("numero_doc") or c.get("documento") or "-"),
                    _cell(_brl(c.get("valor_final") or c.get("valor"))),
                    _cell(c.get("status") or "-"),
                ])
            t_r = Table(rows_r, colWidths=[2.0*cm, 3.0*cm, 3.5*cm, 3.0*cm, 1.8*cm, 2.3*cm, 1.5*cm], repeatRows=1)
            t_r.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f5e9')]),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ]))
            elements.append(t_r)

    doc.build(elements)
    buffer.seek(0)

    await create_audit_log(
        user=current_user,
        action="exportar PDF",
        entity_type="extrato plano de contas",
        entity_id=plano_conta_id or "todos",
        entity_name=(plano_doc or {}).get("nome", "Todos os planos"),
        details=f"Pagar:{len(contas_pagar_data)} Receber:{len(contas_receber_data)} Período:{data_inicio or '-'}|{data_fim or '-'}",
        module="Exportação",
    )

    plano_label = (plano_doc or {}).get("nome", "Todos").replace(" ", "_")[:30]
    filename = f"CRA_Extrato_PlanoContas_{plano_label}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
