"""
NFS-e (Notas Fiscais de Serviço Eletrônicas) — endpoints extraídos de server.py
na Sessão 32 de refatoração. Gerencia as NFS-e importadas dos webservices municipais.
"""
from __future__ import annotations

import base64
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Response

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db

nfse_router = APIRouter(prefix="/nfse", tags=["NFS-e"])


# ============================================================================
# LISTAGEM / CONSULTA
# ============================================================================

@nfse_router.get("/importadas")
async def list_nfses_importadas(
    certificado_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Lista todas as NFS-e (Notas de Serviço) importadas"""
    filtro: dict = {}
    if certificado_id:
        filtro["certificado_id"] = certificado_id
    if status:
        filtro["status"] = status
    return await db.nfse_importadas.find(filtro, {"_id": 0}).sort("data_emissao", -1).to_list(500)


@nfse_router.get("/importadas/{nfse_id}")
async def get_nfse_detail(nfse_id: str, current_user: dict = Depends(get_current_user)):
    """Retorna detalhes de uma NFS-e específica"""
    nfse = await db.nfse_importadas.find_one({"id": nfse_id}, {"_id": 0})
    if not nfse:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")
    return nfse


# ============================================================================
# DOWNLOAD
# ============================================================================

@nfse_router.get("/importadas/{nfse_id}/download-xml")
async def download_nfse_xml(nfse_id: str, current_user: dict = Depends(get_current_user)):
    """Download do XML da NFS-e"""
    nfse = await db.nfse_importadas.find_one({"id": nfse_id})
    if not nfse:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")

    xml_base64 = nfse.get("xml_base64")
    if not xml_base64:
        raise HTTPException(status_code=404, detail="XML não disponível para esta NFS-e")

    try:
        xml_content = base64.b64decode(xml_base64)
        filename = f"NFSe_{nfse.get('numero_nfse', 'sem_numero')}.xml"
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar XML: {str(e)}")


@nfse_router.get("/importadas/{nfse_id}/download-pdf-original")
async def download_nfse_pdf_original(nfse_id: str, current_user: dict = Depends(get_current_user)):
    """Download do PDF ORIGINAL (anexado pelo prestador). Para o modelo padrão da plataforma,
    use /download-pdf."""
    nfse = await db.nfse_importadas.find_one({"id": nfse_id})
    if not nfse:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")
    pdf_base64 = nfse.get("pdf_base64")
    if not pdf_base64:
        raise HTTPException(status_code=404, detail="PDF original não disponível")
    try:
        pdf_content = base64.b64decode(pdf_base64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao decodificar PDF: {e}")
    filename = f"NFSe_{nfse.get('numero_nfse', 'sem_numero')}_original.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@nfse_router.get("/importadas/{nfse_id}/download-pdf")
async def download_nfse_pdf(nfse_id: str, current_user: dict = Depends(get_current_user)):
    """Download do PDF da NFS-e — usa PDF original se disponível; fallback simplificado."""
    nfse = await db.nfse_importadas.find_one({"id": nfse_id})
    if not nfse:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")

    pdf_base64 = nfse.get("pdf_base64")
    # NOTA: o usuário pediu que o download de PDF sempre siga o modelo padrão WebISS.
    # O PDF original (pdf_base64) é mantido no banco apenas para auditoria e pode
    # ser baixado via /importadas/{id}/download-pdf-original (endpoint abaixo).
    # Aqui SEMPRE geramos o template no formato modelo.

    # Fallback: PDF gerado seguindo o LAYOUT OFICIAL WebISS Palmas
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    def _br_money(v, *, blank_zero=False):
        try:
            v = float(v or 0)
        except Exception:
            v = 0
        if blank_zero and v == 0:
            return "0,00"
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _br_dt(s, fmt="%d/%m/%Y %H:%M:%S"):
        if not s:
            return "-"
        try:
            d = s if isinstance(s, datetime) else datetime.fromisoformat(str(s).replace("Z", "+00:00"))
            return d.strftime(fmt)
        except Exception:
            try:
                return datetime.strptime(str(s)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                return str(s)[:19]

    def _comp(s):
        if not s:
            return "-"
        try:
            d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
            return d.strftime("%m/%Y")
        except Exception:
            try:
                return datetime.strptime(str(s)[:10], "%Y-%m-%d").strftime("%m/%Y")
            except Exception:
                return str(s)[:7]

    try:
        # Coleta dados
        numero = str(nfse.get("numero_nfse", "-"))
        cod_verif = str(nfse.get("codigo_verificacao", "-"))
        emissao_str = _br_dt(nfse.get("data_emissao") or nfse.get("created_at"))
        comp_str = _comp(nfse.get("data_emissao") or nfse.get("created_at"))
        municipio_servico = nfse.get("municipio_servico") or nfse.get("municipio") or "Palmas - TO"
        reg_especial = nfse.get("regime_especial") or "Nenhum"
        exig_iss = nfse.get("exigibilidade_iss") or "Exigível em Palmas"

        # Prestador
        p_razao = nfse.get("prestador_nome") or nfse.get("razao_social_prestador") or "-"
        p_fantasia = nfse.get("prestador_fantasia") or nfse.get("nome_fantasia_prestador") or ""
        p_cnpj = nfse.get("prestador_cnpj") or nfse.get("cnpj_prestador") or "-"
        p_im = nfse.get("prestador_im") or nfse.get("inscricao_municipal_prestador") or ""
        p_ie = nfse.get("prestador_ie") or nfse.get("inscricao_estadual_prestador") or ""
        p_simples = "Sim" if nfse.get("optante_simples_nacional") else "Não"
        p_incent = "Sim" if nfse.get("incentivador_cultural") else "Não"
        p_email = nfse.get("prestador_email") or ""
        p_fone = nfse.get("prestador_telefone") or nfse.get("prestador_fone") or ""
        p_endereco = nfse.get("prestador_endereco") or "-"

        # Tomador
        t_razao = nfse.get("tomador_nome") or nfse.get("razao_social_tomador") or "-"
        t_doc = nfse.get("tomador_cnpj") or nfse.get("cnpj_tomador") or nfse.get("tomador_cpf") or "-"
        t_im = nfse.get("tomador_im") or ""
        t_ie = nfse.get("tomador_ie") or ""
        t_email = nfse.get("tomador_email") or ""
        t_fone = nfse.get("tomador_telefone") or nfse.get("tomador_fone") or ""
        t_endereco = nfse.get("tomador_endereco") or "-"

        # Serviço
        cod_servico = nfse.get("codigo_servico") or ""
        desc_servico_curta = nfse.get("descricao_codigo_servico") or nfse.get("item_lista_servico") or ""
        cnae = nfse.get("cnae") or nfse.get("codigo_cnae") or ""
        servico_curto = (
            f"{cod_servico} - {desc_servico_curta}" if cod_servico or desc_servico_curta else "-"
        )
        if cnae:
            servico_curto = f"{servico_curto} CNAE: {cnae}."

        descricao = (
            nfse.get("descricao_servico") or nfse.get("discriminacao") or "-"
        )
        forma_pgto = nfse.get("forma_pagamento") or ""

        # Valores
        v_pis = float(nfse.get("valor_pis") or 0)
        v_cofins = float(nfse.get("valor_cofins") or 0)
        v_inss = float(nfse.get("valor_inss") or 0)
        v_ir = float(nfse.get("valor_irrf") or nfse.get("valor_ir") or 0)
        v_csll = float(nfse.get("valor_csll") or 0)
        v_outras_ret = float(nfse.get("valor_outras_retencoes") or 0)
        v_deducoes = float(nfse.get("valor_deducoes") or 0)
        v_desc_cond = float(nfse.get("desconto_condicionado") or 0)
        v_desc_incond = float(nfse.get("desconto_incondicionado") or 0)
        v_servico = float(nfse.get("valor_servico") or nfse.get("valor_total") or 0)
        v_base_iss = float(nfse.get("base_calculo") or v_servico)
        aliq = float(nfse.get("aliquota_iss") or nfse.get("aliquota") or 0)
        v_iss = float(nfse.get("valor_iss") or 0)
        iss_retido_flag = bool(nfse.get("iss_retido"))
        v_iss_ret = float(nfse.get("valor_iss_retido") or 0)
        v_liquido = float(nfse.get("valor_liquido") or v_servico)
        v_total = v_servico

        # Doc
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=10 * mm, rightMargin=10 * mm,
            topMargin=8 * mm, bottomMargin=8 * mm,
            title=f"NFS-e {numero}",
        )

        # Estilos
        st_label = ParagraphStyle("lbl", fontName="Helvetica-Bold", fontSize=6.2, leading=8, textColor=colors.black)
        st_val = ParagraphStyle("val", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.black)
        st_val_b = ParagraphStyle("valb", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.black)
        st_val_right = ParagraphStyle("vr", fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=TA_RIGHT)
        st_section = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=colors.HexColor("#444"))
        st_title = ParagraphStyle("tit", fontName="Helvetica-Bold", fontSize=14, leading=17, alignment=TA_CENTER)
        st_sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=7.5, leading=9, alignment=TA_CENTER)
        st_footer = ParagraphStyle("ft", fontName="Helvetica", fontSize=7, leading=9, alignment=TA_CENTER)
        st_total = ParagraphStyle("tot", fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=TA_RIGHT, textColor=colors.HexColor("#000"))

        def _kv(label, value, val_style=st_val):
            return Table(
                [[Paragraph(label, st_label)], [Paragraph(str(value or "—"), val_style)]],
                colWidths=[None],
                style=TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]),
            )

        elements = []

        # ============= CABEÇALHO =============
        header_left = Table(
            [
                [Paragraph("<b>MUNICÍPIO DE PALMAS</b>", ParagraphStyle("h1", fontSize=10, fontName="Helvetica-Bold", alignment=TA_CENTER))],
                [Paragraph("Secretaria Municipal de Finanças", ParagraphStyle("h2", fontSize=8, alignment=TA_CENTER))],
                [Paragraph("Diretoria de Fiscalização", ParagraphStyle("h3", fontSize=8, alignment=TA_CENTER))],
                [Paragraph(
                    "Quadra 502 Sul Av. Theotônio Segurado APM - Plano Diretor Sul - Palmas - TO<br/>CEP 77021-654 — Tel.: (63) 2111-2522",
                    ParagraphStyle("h4", fontSize=6.5, alignment=TA_CENTER, leading=8))],
            ],
            colWidths=[10 * cm],
            style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]),
        )

        # Box direito com Nota / Verificação
        box_direito = Table(
            [
                [Paragraph(f"<b>Nota:</b> {numero[:7] if len(numero) >= 7 else numero}", ParagraphStyle("bx1", fontSize=7))],
                [Paragraph(f"<b>{numero[-8:]}</b>", ParagraphStyle("bx2", fontSize=14, fontName="Helvetica-Bold"))],
                [Paragraph("<b>Código Verificação</b>", ParagraphStyle("bx3", fontSize=7))],
                [Paragraph(f"<b>{cod_verif}</b>", ParagraphStyle("bx4", fontSize=11, fontName="Helvetica-Bold"))],
            ],
            colWidths=[6 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]),
        )

        cab = Table(
            [[header_left, box_direito]],
            colWidths=[10 * cm, 9 * cm],
            style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]),
        )
        elements.append(cab)
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e", st_title))
        elements.append(Spacer(1, 6))

        # ============= INFOS GERAIS =============
        infos = Table(
            [[
                _kv("Emissão (Horário de Brasília)", emissao_str, st_val_b),
                _kv("Período de Competência", comp_str, st_val_b),
                _kv("Reg. Especial Tributação", reg_especial),
                _kv("Exigibilidade do ISS", exig_iss),
                _kv("Município de Prestação do Serviço", municipio_servico, st_val_b),
            ]],
            colWidths=[4.0 * cm, 2.6 * cm, 3.6 * cm, 3.4 * cm, 5.4 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#666")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]),
        )
        elements.append(infos)

        # ============= PRESTADOR =============
        elements.append(Spacer(1, 3))
        prestador_grid = Table(
            [
                [Paragraph("<b>PRESTADOR DE SERVIÇOS</b>", st_section)],
                [Table([[
                    _kv("CPF/CNPJ", p_cnpj, st_val_b),
                    _kv("Inscrição Municipal", p_im),
                    _kv("Inscrição Estadual", p_ie),
                ]], colWidths=[6 * cm, 6.5 * cm, 6.5 * cm], style=TableStyle([
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#888")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))],
                [Table([[
                    _kv("Nome / Razão Social", p_razao, st_val_b),
                    _kv("Nome Fantasia", p_fantasia, st_val_b),
                ]], colWidths=[10 * cm, 9 * cm], style=TableStyle([
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#888")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))],
                [Table([[
                    _kv("Simples Nacional", p_simples),
                    _kv("Incentivador Cultural", p_incent),
                    _kv("Email", p_email),
                    _kv("Fone/Fax", p_fone),
                ]], colWidths=[3.2 * cm, 3.5 * cm, 7.8 * cm, 4.5 * cm], style=TableStyle([
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#888")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))],
                [_kv("Endereço", p_endereco)],
            ],
            colWidths=[19 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
            ]),
        )
        elements.append(prestador_grid)

        # ============= TOMADOR =============
        tomador_grid = Table(
            [
                [Paragraph("<b>TOMADOR DE SERVIÇOS</b>", st_section)],
                [_kv("Nome / Razão Social", t_razao, st_val_b)],
                [Table([[
                    _kv("CPF/CNPJ", t_doc, st_val_b),
                    _kv("Inscrição Municipal", t_im),
                    _kv("Inscrição Estadual", t_ie),
                ]], colWidths=[6 * cm, 6.5 * cm, 6.5 * cm], style=TableStyle([
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#888")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))],
                [Table([[
                    _kv("Email", t_email),
                    _kv("Fone/Fax", t_fone),
                ]], colWidths=[12 * cm, 7 * cm], style=TableStyle([
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#888")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))],
                [_kv("Endereço", t_endereco)],
            ],
            colWidths=[19 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
            ]),
        )
        elements.append(tomador_grid)

        # ============= SERVIÇO PRESTADO =============
        servico_grid = Table(
            [
                [Paragraph("<b>SERVIÇO PRESTADO</b>", st_section)],
                [Paragraph(servico_curto, st_val)],
            ],
            colWidths=[19 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
            ]),
        )
        elements.append(servico_grid)

        # ============= DESCRIÇÃO =============
        desc_html = str(descricao).replace("\n", "<br/>")
        if forma_pgto:
            desc_html += f"<br/><br/><b>FORMA DE PAGAMENTO:</b> {forma_pgto}"
        descricao_grid = Table(
            [
                [Paragraph("<b>DESCRIÇÃO DOS SERVIÇOS</b>", st_section)],
                [Paragraph(desc_html, st_val)],
            ],
            colWidths=[19 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
            ]),
        )
        elements.append(descricao_grid)

        # ============= RETENÇÕES FEDERAIS =============
        ret_header = ["PIS (R$)", "COFINS (R$)", "INSS (R$)", "IR (R$)", "CSLL (R$)", "Outras Retenções (R$)"]
        ret_values = [
            _br_money(v_pis, blank_zero=True),
            _br_money(v_cofins, blank_zero=True),
            _br_money(v_inss, blank_zero=True),
            _br_money(v_ir, blank_zero=True),
            _br_money(v_csll, blank_zero=True),
            _br_money(v_outras_ret, blank_zero=True),
        ]
        retencoes_grid = Table(
            [
                [Paragraph("<b>RETENÇÕES FEDERAIS</b>", st_section)] + [""] * 5,
                [Paragraph(f"<b>{h}</b>", ParagraphStyle("rh", fontSize=7, alignment=TA_CENTER)) for h in ret_header],
                [Paragraph(f"<b>{v}</b>", ParagraphStyle("rv", fontSize=8.5, alignment=TA_CENTER, fontName="Helvetica-Bold")) for v in ret_values],
            ],
            colWidths=[3.166 * cm] * 6,
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("LINEBELOW", (0, 1), (-1, 1), 0.3, colors.HexColor("#888")),
                ("INNERGRID", (0, 1), (-1, -1), 0.3, colors.HexColor("#888")),
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]),
        )
        elements.append(retencoes_grid)

        # ============= VALORES =============
        iss_retido_str = (
            "*****" if not iss_retido_flag and v_iss_ret == 0
            else _br_money(v_iss_ret, blank_zero=True)
        )
        valores_grid = Table(
            [
                [Paragraph("<b>VALORES</b>", st_section), "", ""],
                [
                    Paragraph(f"<b>Deduções (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                    Paragraph(f"<b>Desc. Cond. (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                    Paragraph(f"<b>Desc. Incond. (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                ],
                [
                    Paragraph(f"<b>{_br_money(v_deducoes, blank_zero=True)}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                    Paragraph(f"<b>{_br_money(v_desc_cond, blank_zero=True)}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                    Paragraph(f"<b>{_br_money(v_desc_incond, blank_zero=True)}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                ],
                [
                    Paragraph(f"<b>Valor dos Serviços (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                    Paragraph(f"<b>Base de Cálculo ISS (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                    Paragraph(f"<b>Alíquota ISS (%)</b>", ParagraphStyle("vlbl", fontSize=7)),
                ],
                [
                    Paragraph(f"<b>{_br_money(v_servico)}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                    Paragraph(f"<b>{_br_money(v_base_iss)}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                    Paragraph(f"<b>{aliq:.2f}".replace(".", ",") + "</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                ],
                [
                    Paragraph(f"<b>ISS (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                    Paragraph(f"<b>ISS Retido (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                    Paragraph(f"<b>Valor Líquido (R$)</b>", ParagraphStyle("vlbl", fontSize=7)),
                ],
                [
                    Paragraph(f"<b>{_br_money(v_iss)}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                    Paragraph(f"<b>{iss_retido_str}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                    Paragraph(f"<b>{_br_money(v_liquido)}</b>", ParagraphStyle("vv", fontSize=9, alignment=TA_RIGHT)),
                ],
            ],
            colWidths=[6.333 * cm, 6.333 * cm, 6.333 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("INNERGRID", (0, 1), (-1, -1), 0.3, colors.HexColor("#888")),
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]),
        )
        elements.append(valores_grid)

        # Valor Total da Nota
        total_grid = Table(
            [[
                Paragraph("<b>Valor Total da Nota (R$)</b>", ParagraphStyle("tlbl", fontSize=8, alignment=TA_LEFT)),
                Paragraph(f"<b>{_br_money(v_total)}</b>", st_total),
            ]],
            colWidths=[10 * cm, 9 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F8F8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]),
        )
        elements.append(total_grid)

        # ============= OUTRAS INFORMAÇÕES =============
        outras_info = nfse.get("outras_informacoes") or nfse.get("informacoes_adicionais") or ""
        if not outras_info and v_total > 0:
            trib_fed = v_total * 0.1345
            trib_mun = v_total * (aliq / 100 if aliq else 0.05)
            outras_info = f"Trib. aprox. R$ {_br_money(trib_fed)} Federal e R$ {_br_money(trib_mun)} Municipal. Fonte: IBPT"
        outras_grid = Table(
            [
                [Paragraph("<b>OUTRAS INFORMAÇÕES</b>", st_section)],
                [Paragraph(outras_info or "-", st_val)],
            ],
            colWidths=[19 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
            ]),
        )
        elements.append(outras_grid)

        # ============= RODAPÉ =============
        elements.append(Spacer(1, 6))
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        elements.append(Paragraph(
            f"Visualizado em: {agora} | Para validação desta NFSe acesse: "
            f"http://palmasto.webiss.com.br/externo/nfse/validar",
            st_footer,
        ))
        elements.append(Paragraph(
            "Esta NFS-e é autodeclaratória. Esta NFS-e foi emitida com respaldo no Decreto nº 1667 de 6 de dezembro de 2018.",
            st_footer,
        ))

        doc.build(elements)
        buffer.seek(0)

        filename = f"NFSe_{numero}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logging.exception("Erro gerando PDF NFS-e (WebISS layout)")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")


# ============================================================================
# CRIAR CONTA A PAGAR / ATUALIZAR STATUS
# ============================================================================

@nfse_router.post("/importadas/{nfse_id}/criar-conta-pagar")
async def criar_conta_pagar_from_nfse(nfse_id: str, current_user: dict = Depends(get_current_user)):
    """Cria uma conta a pagar a partir de uma NFS-e"""
    nfse = await db.nfse_importadas.find_one({"id": nfse_id}, {"_id": 0})
    if not nfse:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")

    if nfse.get("conta_pagar_id"):
        raise HTTPException(status_code=400, detail="Esta NFS-e já possui uma conta a pagar vinculada")

    conta_pagar_id = str(uuid.uuid4())
    data_emissao = nfse.get("data_emissao") or datetime.now(timezone.utc).isoformat()
    data_iso = data_emissao[:10] if isinstance(data_emissao, str) else datetime.now().strftime("%Y-%m-%d")

    conta_pagar_doc = {
        "id": conta_pagar_id,
        "descricao": f"NFS-e {nfse.get('numero_nfse', '')} - {nfse.get('prestador_nome', nfse.get('razao_social_prestador', 'Serviço'))}",
        "valor": nfse.get("valor_servico", nfse.get("valor_total", 0)),
        "data_vencimento": data_iso,
        "data_emissao": data_iso,
        "status": "pendente",
        "favorecido": nfse.get("prestador_nome", nfse.get("razao_social_prestador", "")),
        "cnpj_favorecido": nfse.get("prestador_cnpj", nfse.get("cnpj_prestador", "")),
        "nfse_id": nfse_id,
        "numero_nfse": nfse.get("numero_nfse", ""),
        "origem": "nfse",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.contas_pagar.insert_one(conta_pagar_doc)

    await db.nfse_importadas.update_one(
        {"id": nfse_id},
        {"$set": {"conta_pagar_id": conta_pagar_id, "status": "processada"}},
    )

    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="conta_pagar",
        entity_id=conta_pagar_id,
        entity_name=conta_pagar_doc["descricao"],
        details=f"Conta a pagar criada a partir da NFS-e {nfse.get('numero_nfse', '')}",
        module="Financeiro",
    )
    return {
        "message": "Conta a pagar criada com sucesso",
        "conta_pagar_id": conta_pagar_id,
        "nfse_id": nfse_id,
    }


@nfse_router.patch("/importadas/{nfse_id}/status")
async def update_nfse_status(
    nfse_id: str,
    status: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
):
    """Atualiza o status de uma NFS-e importada"""
    if status not in ["nova", "processada", "ignorada"]:
        raise HTTPException(status_code=400, detail="Status inválido")

    result = await db.nfse_importadas.update_one(
        {"id": nfse_id},
        {"$set": {"status": status}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")
    return {"message": "Status atualizado"}
