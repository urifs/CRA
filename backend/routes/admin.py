"""
Admin Routes - Apenas endpoints únicos:
- PUT /admin/ordens-servico/{id}/concluir
- GET /admin/ordens-servico/{id}/export-pdf

Os demais endpoints administrativos (CRUD de cadastros, ordens, plano-contas,
centros-custo, notificações, dashboard) estão em /app/backend/server.py.
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import Response
from datetime import datetime
import os
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create router
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# ============ ORDENS DE SERVIÇO (endpoints únicos) ============

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

    # Dados da empresa emissora.
    # `empresa_emissora` pode ser:
    #   - "locadora" / "construtora" (legado, mapeado para CNPJs conhecidos)
    #   - ID de um centro de custo cadastrado
    #   - Nome textual livre
    emp = ordem.get("empresa_emissora") or "locadora"

    centro_emp = None
    if emp not in ("locadora", "construtora"):
        # Busca por ID ou nome no centros_custo
        centro_emp = await db.centros_custo.find_one(
            {"$or": [{"id": emp}, {"nome": emp}]},
            {"_id": 0},
        )

    # Mapeamento de empresas conhecidas (com CNPJ/telefone/endereço)
    empresas_conhecidas = {
        "construtora": {
            "nome": "RODRIGUES ALMEIDA CONSTRUCOES LTDA",
            "fantasia": "CRA CONSTRUCOES",
            "cnpj": "39.543.761/0002-06",
        },
        "locadora": {
            "nome": "RODRIGUES ALMEIDA LOCACOES LTDA",
            "fantasia": "CRA LOCACOES",
            "cnpj": "39.543.761/0001-25",
        },
    }
    if emp in empresas_conhecidas:
        info = empresas_conhecidas[emp]
        emp_nome, emp_fantasia, emp_cnpj = info["nome"], info["fantasia"], info["cnpj"]
        emp_telefone = "(63) 3214-9999"
        emp_endereco = "712 SUL AV. LO 15, 01 PLANO DIRETOR SUL"
        emp_cidade = "PALMAS-TO"
    elif centro_emp:
        # Prioriza campos novos do centro (razao_social, cnpj, etc.)
        emp_nome = centro_emp.get("razao_social") or centro_emp.get("nome") or "-"
        emp_fantasia = centro_emp.get("fantasia") or centro_emp.get("codigo") or ""
        emp_cnpj = centro_emp.get("cnpj") or "-"
        emp_telefone = centro_emp.get("telefone") or centro_emp.get("celular") or ""
        endereco_partes = [
            centro_emp.get("endereco"),
            centro_emp.get("bairro"),
        ]
        emp_endereco = ", ".join([p for p in endereco_partes if p]) or "-"
        cidade_uf = []
        if centro_emp.get("cidade"):
            cidade_uf.append(centro_emp["cidade"])
        if centro_emp.get("uf"):
            cidade_uf.append(centro_emp["uf"])
        emp_cidade = "-".join(cidade_uf) if cidade_uf else "-"

        # Fallback: se nada no centro, infere por nome
        if emp_cnpj == "-":
            nome_upper = (centro_emp.get("nome") or "").upper()
            if "CONSTRUC" in nome_upper:
                emp_cnpj = empresas_conhecidas["construtora"]["cnpj"]
            elif "LOCA" in nome_upper:
                emp_cnpj = empresas_conhecidas["locadora"]["cnpj"]
    else:
        # Texto livre — usa como nome
        emp_nome = emp
        emp_fantasia = ""
        emp_cnpj = "-"
        emp_telefone = ""
        emp_endereco = "-"
        emp_cidade = "-"

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
         _kv("Data Fech.", _data_br(ordem.get("data_fechamento") or ordem.get("data_conclusao")))[0],
         _kv("Data Fech.", _data_br(ordem.get("data_fechamento") or ordem.get("data_conclusao")))[1]],
        [_kv("Prev. Entrega", _data_br(ordem.get("data_previsao_entrega") or ordem.get("data_previsao")))[0],
         _kv("Prev. Entrega", _data_br(ordem.get("data_previsao_entrega") or ordem.get("data_previsao")))[1],
         _kv("Atendente", ordem.get("atendente_nome") or ordem.get("responsavel_nome"))[0],
         _kv("Atendente", ordem.get("atendente_nome") or ordem.get("responsavel_nome"))[1]],
        [_kv("Tipo Atend.", ordem.get("tipo_atendimento") or ordem.get("tipo"))[0],
         _kv("Tipo Atend.", ordem.get("tipo_atendimento") or ordem.get("tipo"))[1],
         _kv("Período", ordem.get("periodo"))[0], _kv("Período", ordem.get("periodo"))[1]],
        [_kv("Periodicidade", (ordem.get("periodicidade") or "").capitalize())[0],
         _kv("Periodicidade", (ordem.get("periodicidade") or "").capitalize())[1],
         _kv("KM", ordem.get("km"))[0], _kv("KM", ordem.get("km"))[1]],
        [_kv("Nº Doc Fiscal", ordem.get("numero_documento_fiscal"))[0],
         _kv("Nº Doc Fiscal", ordem.get("numero_documento_fiscal"))[1],
         _kv("Nº Contrato", ordem.get("numero_contrato"))[0], _kv("Nº Contrato", ordem.get("numero_contrato"))[1]],
        [_kv("Empresa Emissora", (ordem.get("empresa_emissora") or "").capitalize())[0],
         _kv("Empresa Emissora", (ordem.get("empresa_emissora") or "").capitalize())[1],
         _kv("Tipo Financeiro", (ordem.get("tipo_financeiro") or "nenhum").replace("_", " ").capitalize())[0],
         _kv("Tipo Financeiro", (ordem.get("tipo_financeiro") or "nenhum").replace("_", " ").capitalize())[1]],
        [_kv("Status", (ordem.get("status") or "aberta").capitalize())[0],
         _kv("Status", (ordem.get("status") or "aberta").capitalize())[1],
         _kv("Forma Pagto", ordem.get("forma_pagamento"))[0],
         _kv("Forma Pagto", ordem.get("forma_pagamento"))[1]],
        [_kv("Cond. Pagto", ordem.get("condicao_pagamento"))[0],
         _kv("Cond. Pagto", ordem.get("condicao_pagamento"))[1],
         _kv("Vlr Antecipado", _brl(ordem.get("valor_antecipado")))[0],
         _kv("Vlr Antecipado", _brl(ordem.get("valor_antecipado")))[1]],
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

    # Vínculos opcionais — Máquinas / Frotas / Fornecedores
    vinculos_data = []
    maq_ids = ordem.get("maquinas_ids") or []
    fro_ids = ordem.get("frotas_ids") or []
    forn_ids = ordem.get("fornecedores_ids") or []
    if maq_ids:
        maquinas = await db.machines.find(
            {"id": {"$in": maq_ids}},
            {"_id": 0, "name": 1, "plate": 1, "model": 1, "type": 1},
        ).to_list(50)
        if maquinas:
            txt = "; ".join(
                [f"{m.get('name','')} {('(' + m.get('plate') + ')') if m.get('plate') else ''}".strip()
                 for m in maquinas]
            )
            vinculos_data.append([Paragraph("MÁQUINAS", style_label), Paragraph(txt, style_value)])
    if fro_ids:
        frotas = await db.machines.find(
            {"id": {"$in": fro_ids}},
            {"_id": 0, "name": 1, "plate": 1, "model": 1},
        ).to_list(50)
        if frotas:
            txt = "; ".join(
                [f"{m.get('name','')} {('(' + m.get('plate') + ')') if m.get('plate') else ''}".strip()
                 for m in frotas]
            )
            vinculos_data.append([Paragraph("FROTAS", style_label), Paragraph(txt, style_value)])
    if forn_ids:
        fornecs = await db.cadastros.find(
            {"id": {"$in": forn_ids}},
            {"_id": 0, "nome": 1, "nome_razao": 1, "razao_social": 1, "fantasia": 1, "cpf_cnpj": 1},
        ).to_list(50)
        if fornecs:
            txt = "; ".join(
                [f"{(f.get('nome_razao') or f.get('razao_social') or f.get('nome') or '-')} "
                 f"{('(' + f.get('cpf_cnpj') + ')') if f.get('cpf_cnpj') else ''}".strip()
                 for f in fornecs]
            )
            vinculos_data.append([Paragraph("FORNECEDORES", style_label), Paragraph(txt, style_value)])

    if vinculos_data:
        elements.append(Table(
            [[Paragraph("VÍNCULOS", style_section)]],
            colWidths=[19.4 * cm],
            style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#444")),
                              ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]),
        ))
        t_v = Table(vinculos_data, colWidths=[2.8 * cm, 16.6 * cm])
        t_v.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t_v)
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
    if not itens and not (ordem.get("valores_extras") or []):
        # Caso não exista nenhum item nem valor adicional, exibe a descrição geral
        rows.append(["-", "1", "UN", Paragraph(ordem.get("descricao") or "-", style_value),
                     _brl(ordem.get("valor_total")), _brl(ordem.get("valor_total")),
                     _brl(0), _brl(ordem.get("valor_total"))])
        sub_total = float(ordem.get("valor_total") or 0)

    # Valores extras adicionais (compostos) — cada item compõe o Total da OS.
    # Quando vinculado a uma máquina, exibimos "Descrição — Máquina (placa)".
    for ve in (ordem.get("valores_extras") or []):
        try:
            v_val = float(ve.get("valor") or 0)
        except (TypeError, ValueError):
            v_val = 0
        v_desc = ve.get("descricao") or "Adicional"
        v_maq = ve.get("maquina_nome") or ""
        if v_maq:
            v_desc = f"{v_desc}<br/><font size='6' color='#666'>Máquina: {v_maq}</font>"
        rows.append(["-", "1", "UN", Paragraph(v_desc, style_value),
                     _brl(v_val), _brl(v_val), _brl(0), _brl(v_val)])
        sub_total += v_val

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

    # Observações de serviços / notas gerais — exibir TODOS os campos preenchidos
    if ordem.get("observacao_servicos"):
        elements.append(Paragraph("<b>OBSERVAÇÃO DOS SERVIÇOS:</b>", style_value))
        elements.append(Paragraph(str(ordem["observacao_servicos"]).replace("\n", "<br/>"), style_value))
        elements.append(Spacer(1, 0.15 * cm))
    if ordem.get("notas_gerais"):
        elements.append(Paragraph("<b>NOTAS GERAIS:</b>", style_value))
        elements.append(Paragraph(str(ordem["notas_gerais"]).replace("\n", "<br/>"), style_value))
        elements.append(Spacer(1, 0.15 * cm))
    if ordem.get("observacoes"):
        elements.append(Paragraph("<b>OBSERVAÇÕES:</b>", style_value))
        elements.append(Paragraph(str(ordem["observacoes"]).replace("\n", "<br/>"), style_value))
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
