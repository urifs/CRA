"""
Template padrão de PDF da plataforma CRA Construtora.

Use estes helpers para garantir que TODO PDF exportado pela plataforma
(financeiro, RH, Chat IA, conciliação, NF-e/NFS-e, etc.) tenha o mesmo
cabeçalho corporativo, paleta e tipografia.

Uso típico:

    from utils.pdf_template import (
        create_corporate_doc, add_corporate_header, get_corporate_styles,
        add_footer, BRAND_COLORS,
    )

    buf = io.BytesIO()
    doc = create_corporate_doc(buf)
    elements = []
    add_corporate_header(elements, "Notificação de Falta", "Documento emitido em DD/MM/YYYY")
    # ... seus elementos ...
    add_footer(elements, "CRA Construtora · Confidencial")
    doc.build(elements)
"""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# Paleta corporativa (mantida em sync com o frontend)
BRAND_COLORS = {
    "primary": colors.HexColor("#0f766e"),       # teal-700 (linha divisória, destaques)
    "primary_dark": colors.HexColor("#0f172a"),  # slate-900 (títulos)
    "accent": colors.HexColor("#10b981"),        # emerald-500 (positivos)
    "danger": colors.HexColor("#dc2626"),        # red-600 (negativos)
    "muted": colors.HexColor("#64748b"),         # slate-500 (subtítulos)
    "muted_light": colors.HexColor("#94a3b8"),   # slate-400 (rodapés)
    "label_bg": colors.HexColor("#f8fafc"),      # slate-50 (cabeçalho de tabelas)
    "label_text": colors.HexColor("#475569"),    # slate-600 (texto de labels)
    "border": colors.HexColor("#cbd5e1"),        # slate-300 (bordas)
    "border_light": colors.HexColor("#e2e8f0"),  # slate-200 (linhas internas)
}

LOGO_PATH = "/app/frontend/public/logo.png"


def create_corporate_doc(buffer, *, landscape_mode: bool = False, title: str = "Documento"):
    """Retorna um SimpleDocTemplate com margens e tamanho padrão da CRA."""
    pagesize = landscape(A4) if landscape_mode else A4
    return SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        title=title,
        author="CRA Construtora",
    )


def get_corporate_styles():
    """Retorna um dicionário de estilos padronizados (Paragraph)."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CRATitle", parent=base["Heading1"],
            fontSize=18, leading=22, alignment=TA_CENTER,
            textColor=BRAND_COLORS["primary_dark"],
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "CRASub", parent=base["Normal"],
            fontSize=10, alignment=TA_CENTER,
            textColor=BRAND_COLORS["muted"],
            spaceAfter=14,
        ),
        "doc_title": ParagraphStyle(
            "CRADocTitle", parent=base["Heading1"],
            fontSize=16, leading=20, alignment=TA_CENTER,
            textColor=BRAND_COLORS["primary_dark"],
            spaceBefore=8, spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "CRASection", parent=base["Heading2"],
            fontSize=12, leading=16,
            textColor=BRAND_COLORS["primary_dark"],
            spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "CRABody", parent=base["Normal"],
            fontSize=10.5, leading=15, alignment=TA_JUSTIFY,
            textColor=colors.black, spaceAfter=6,
        ),
        "body_left": ParagraphStyle(
            "CRABodyLeft", parent=base["Normal"],
            fontSize=10.5, leading=15, alignment=TA_LEFT,
            textColor=colors.black, spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "CRASmall", parent=base["Normal"],
            fontSize=9, leading=12,
            textColor=BRAND_COLORS["muted"],
        ),
        "footer": ParagraphStyle(
            "CRAFooter", parent=base["Normal"],
            fontSize=8, alignment=TA_CENTER,
            textColor=BRAND_COLORS["muted_light"],
        ),
    }


def add_corporate_header(
    elements,
    doc_title: str = None,
    subtitle: str = None,
    company_name: str = "CRA Construtora",
):
    """Adiciona logo (se existir) + nome da empresa + subtítulo + linha divisória.
    Use no início de TODO PDF da plataforma.
    Passe ``company_name="CRA Apoio"`` para PDFs do módulo RH."""
    styles = get_corporate_styles()

    # Logo (se disponível)
    try:
        if os.path.exists(LOGO_PATH):
            elements.append(RLImage(LOGO_PATH, width=2.6 * cm, height=2.6 * cm, kind="proportional"))
            elements.append(Spacer(1, 4))
    except Exception:
        pass

    elements.append(Paragraph(company_name, styles["title"]))

    sub = subtitle or f"Documento emitido em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    elements.append(Paragraph(sub, styles["subtitle"]))

    # Linha divisória teal
    div = Table([[""]], colWidths=[16 * cm])
    div.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1.5, BRAND_COLORS["primary"]),
    ]))
    elements.append(div)
    elements.append(Spacer(1, 12))

    if doc_title:
        elements.append(Paragraph(doc_title, styles["doc_title"]))


def add_footer(elements, extra_text: str = None):
    """Adiciona um rodapé padronizado com data/hora de geração."""
    styles = get_corporate_styles()
    elements.append(Spacer(1, 18))
    text = extra_text or f"Documento gerado pela plataforma CRA · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    elements.append(Paragraph(text, styles["footer"]))


def build_data_table(rows, *, label_width=4.5, value_width=11.0):
    """Helper: monta uma tabela de pares Label/Valor com estilo corporativo.
    `rows` é uma lista de tuplas [(label, value), ...]."""
    t = Table(rows, colWidths=[label_width * cm, value_width * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), BRAND_COLORS["label_text"]),
        ("BACKGROUND", (0, 0), (0, -1), BRAND_COLORS["label_bg"]),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_COLORS["border"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BRAND_COLORS["border_light"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build_signatures_table(left_label="Colaborador", right_label="Setor de RH / Gestor"):
    """Helper: tabela de duas linhas de assinatura."""
    t = Table([["", ""], [left_label, right_label]], colWidths=[7.5 * cm, 7.5 * cm])
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (-1, 1), 0.7, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("TEXTCOLOR", (0, 1), (-1, 1), BRAND_COLORS["label_text"]),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
    ]))
    return t


def header_table_style():
    """Estilo padrão para a primeira linha (cabeçalho) de uma tabela de listagem."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLORS["primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_COLORS["label_bg"]]),
        ("GRID", (0, 0), (-1, -1), 0.3, BRAND_COLORS["border_light"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])
