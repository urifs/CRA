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


@nfse_router.get("/importadas/{nfse_id}/download-pdf")
async def download_nfse_pdf(nfse_id: str, current_user: dict = Depends(get_current_user)):
    """Download do PDF da NFS-e — usa PDF original se disponível; fallback simplificado."""
    nfse = await db.nfse_importadas.find_one({"id": nfse_id})
    if not nfse:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")

    pdf_base64 = nfse.get("pdf_base64")
    if pdf_base64:
        try:
            pdf_content = base64.b64decode(pdf_base64)
            filename = f"NFSe_{nfse.get('numero_nfse', 'sem_numero')}.pdf"
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            logging.warning(f"Erro ao decodificar PDF armazenado: {e}")

    # Fallback: PDF simplificado via ReportLab
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=1 * cm, rightMargin=1 * cm,
            topMargin=1 * cm, bottomMargin=1 * cm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=14, spaceAfter=6, alignment=1)
        subtitle_style = ParagraphStyle("Subtitle", parent=styles["Heading2"], fontSize=10, spaceAfter=4)
        normal_style = ParagraphStyle("Normal", parent=styles["Normal"], fontSize=8)
        small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=7)

        elements = [
            Paragraph("NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e", title_style),
            Paragraph(
                "<font color='red'><b>⚠ PDF gerado pelo sistema - Para obter a NFS-e oficial, consulte o portal da prefeitura</b></font>",
                small_style,
            ),
            Spacer(1, 10),
        ]

        valor_fmt = f"R$ {nfse.get('valor_servico', nfse.get('valor_total', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        data_emissao = (nfse.get("data_emissao") or "-")[:10]

        info = [
            ["NFS-e Nº:", str(nfse.get("numero_nfse", "-")), "Data Emissão:", data_emissao],
            ["Valor Total:", valor_fmt, "Status:", nfse.get("status", "-").upper()],
        ]
        t = Table(info, colWidths=[3 * cm, 5 * cm, 3 * cm, 5 * cm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

        # Prestador
        elements.append(Paragraph("<b>PRESTADOR DO SERVIÇO</b>", subtitle_style))
        prestador_info = [
            ["Razão Social:", nfse.get("prestador_nome", nfse.get("razao_social_prestador", "-"))],
            ["CNPJ:", nfse.get("prestador_cnpj", nfse.get("cnpj_prestador", "-"))],
        ]
        t = Table(prestador_info, colWidths=[3 * cm, 13 * cm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

        # Tomador
        elements.append(Paragraph("<b>TOMADOR DO SERVIÇO</b>", subtitle_style))
        tomador_info = [
            ["Razão Social:", nfse.get("tomador_nome", nfse.get("razao_social_tomador", "-"))],
            ["CNPJ/CPF:", nfse.get("tomador_cnpj", nfse.get("cnpj_tomador", "-"))],
        ]
        t = Table(tomador_info, colWidths=[3 * cm, 13 * cm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

        # Discriminação
        elements.append(Paragraph("<b>DISCRIMINAÇÃO DO SERVIÇO</b>", subtitle_style))
        discriminacao = nfse.get("descricao_servico", nfse.get("discriminacao", "Não informado"))
        elements.append(Paragraph(discriminacao, normal_style))

        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            f"<i>Documento gerado pelo Sistema CRA em {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>",
            normal_style,
        ))

        doc.build(elements)
        buffer.seek(0)

        filename = f"NFSe_{nfse.get('numero_nfse', 'sem_numero')}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
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
