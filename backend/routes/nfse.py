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

    # Fallback: PDF padronizado com layout corporativo (NFS-e simplificada)
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from utils.pdf_template import (
        create_corporate_doc, add_corporate_header, add_footer,
        get_corporate_styles, build_data_table, BRAND_COLORS, header_table_style,
    )

    def _br_money(v):
        try:
            return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "R$ 0,00"

    def _br_date(s: str) -> str:
        if not s:
            return "-"
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return s[:10]

    try:
        buffer = io.BytesIO()
        doc = create_corporate_doc(
            buffer, title=f"NFS-e {nfse.get('numero_nfse', '')}",
        )
        styles = get_corporate_styles()

        elements = []
        add_corporate_header(
            elements,
            doc_title="NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e",
            subtitle=f"Nº {nfse.get('numero_nfse', '-')} · Emissão {_br_date(nfse.get('data_emissao', ''))}",
        )

        # Aviso oficial
        from reportlab.lib.styles import ParagraphStyle
        aviso_style = ParagraphStyle(
            "Aviso", fontSize=8, alignment=1,
            textColor=colors.HexColor("#dc2626"),
        )
        elements.append(Paragraph(
            "<b>DOCUMENTO INFORMATIVO — Para a NFS-e oficial, consulte o portal da prefeitura.</b>",
            aviso_style,
        ))
        elements.append(Spacer(1, 12))

        # Identificação principal
        elements.append(Paragraph("IDENTIFICAÇÃO DA NOTA", styles["section"]))
        elements.append(build_data_table([
            ("Número da NFS-e:", str(nfse.get("numero_nfse", "-"))),
            ("Código de Verificação:", str(nfse.get("codigo_verificacao", "-"))),
            ("Data de Emissão:", _br_date(nfse.get("data_emissao", ""))),
            ("Status:", (nfse.get("status", "-") or "-").upper()),
            ("Município:", nfse.get("municipio_servico", nfse.get("municipio", "-"))),
            ("Natureza Operação:", nfse.get("natureza_operacao", "-") or "-"),
        ]))
        elements.append(Spacer(1, 12))

        # Prestador
        elements.append(Paragraph("PRESTADOR DO SERVIÇO", styles["section"]))
        elements.append(build_data_table([
            ("Razão Social:", nfse.get("prestador_nome") or nfse.get("razao_social_prestador") or "-"),
            ("CNPJ:", nfse.get("prestador_cnpj") or nfse.get("cnpj_prestador") or "-"),
            ("Inscrição Municipal:", nfse.get("prestador_im") or nfse.get("inscricao_municipal_prestador") or "-"),
            ("Endereço:", nfse.get("prestador_endereco") or "-"),
        ]))
        elements.append(Spacer(1, 12))

        # Tomador
        elements.append(Paragraph("TOMADOR DO SERVIÇO", styles["section"]))
        elements.append(build_data_table([
            ("Razão Social:", nfse.get("tomador_nome") or nfse.get("razao_social_tomador") or "-"),
            ("CNPJ/CPF:", nfse.get("tomador_cnpj") or nfse.get("cnpj_tomador") or "-"),
            ("Endereço:", nfse.get("tomador_endereco") or "-"),
        ]))
        elements.append(Spacer(1, 12))

        # Discriminação do serviço
        elements.append(Paragraph("DISCRIMINAÇÃO DO SERVIÇO", styles["section"]))
        discriminacao = (
            nfse.get("descricao_servico")
            or nfse.get("discriminacao")
            or "Não informado"
        )
        elements.append(Paragraph(
            str(discriminacao).replace("\n", "<br/>"),
            styles["body"],
        ))
        elements.append(Spacer(1, 12))

        # Quadro de valores
        elements.append(Paragraph("VALORES DO SERVIÇO", styles["section"]))
        valor_servico = float(nfse.get("valor_servico", nfse.get("valor_total", 0)) or 0)
        rows = [
            ["Descrição", "Valor"],
            ["Valor dos Serviços", _br_money(valor_servico)],
            ["Deduções", _br_money(nfse.get("valor_deducoes", 0))],
            ["Base de Cálculo", _br_money(nfse.get("base_calculo", valor_servico))],
            ["ISS Retido", _br_money(nfse.get("iss_retido", nfse.get("valor_iss", 0)))],
            ["IRRF", _br_money(nfse.get("valor_irrf", 0))],
            ["INSS", _br_money(nfse.get("valor_inss", 0))],
            ["CSLL", _br_money(nfse.get("valor_csll", 0))],
            ["COFINS", _br_money(nfse.get("valor_cofins", 0))],
            ["PIS", _br_money(nfse.get("valor_pis", 0))],
            ["VALOR LÍQUIDO", _br_money(nfse.get("valor_liquido", valor_servico))],
        ]
        # Remove rows com valor zero (exceto Valor dos Serviços e Valor Líquido)
        rows_filtradas = [rows[0]]
        for r in rows[1:]:
            if r[0] in ("Valor dos Serviços", "VALOR LÍQUIDO", "Base de Cálculo"):
                rows_filtradas.append(r)
            else:
                # mantém apenas se valor != R$ 0,00
                if r[1] != "R$ 0,00":
                    rows_filtradas.append(r)

        t_val = Table(rows_filtradas, colWidths=[10 * cm, 6 * cm])
        style = header_table_style()
        style.add("ALIGN", (1, 1), (1, -1), "RIGHT")
        # Destaca a última linha (Valor Líquido)
        style.add("BACKGROUND", (0, -1), (-1, -1), BRAND_COLORS["primary"])
        style.add("TEXTCOLOR", (0, -1), (-1, -1), colors.white)
        style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        t_val.setStyle(style)
        elements.append(t_val)

        add_footer(elements, "Sistema CRA · Nota Fiscal de Serviços Eletrônica")
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
