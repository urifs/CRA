"""
Export Routes - PDF and Excel export functionality
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from datetime import datetime, timezone
import os
import io
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
import jwt
JWT_SECRET = os.environ.get('JWT_SECRET', 'fleet-maintenance-secret-key-2024')

security = HTTPBearer()

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return decode_token(credentials.credentials)

# Create router
export_router = APIRouter(prefix="/export", tags=["Export"])


def generate_pdf_report(title: str, data: list, columns: list) -> io.BytesIO:
    """Gera um relatório PDF formatado"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1*cm, bottomMargin=1*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1
    )
    
    elements = []
    
    # Título
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    
    # Data/hora
    date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=9, alignment=2)
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 20))
    
    if data:
        # Cabeçalho
        table_data = [columns]
        
        # Dados
        for item in data:
            row = []
            for col in columns:
                col_key = col.lower().replace(" ", "_").replace("ç", "c").replace("ã", "a").replace("í", "i")
                value = item.get(col_key, item.get(col, "-"))
                if isinstance(value, float):
                    value = f"R$ {value:,.2f}"
                row.append(str(value) if value else "-")
            table_data.append(row)
        
        # Criar tabela
        col_widths = [doc.width / len(columns)] * len(columns)
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        elements.append(table)
    else:
        elements.append(Paragraph("Nenhum dado encontrado.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


@export_router.get("/pdf/machines")
async def export_machines_pdf(
    category_id: Optional[str] = None,
    fleet_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar máquinas em PDF"""
    await get_current_user(credentials)
    
    query = {}
    if category_id:
        query["category_id"] = category_id
    if fleet_id:
        query["fleet_id"] = fleet_id
    
    machines = await db.machines.find(query, {"_id": 0}).to_list(500)
    
    data = []
    for m in machines:
        category = await db.categories.find_one({"id": m.get("category_id")}, {"_id": 0})
        data.append({
            "nome": m.get("name", "-"),
            "placa": m.get("plate", "-"),
            "categoria": category["name"] if category else "-",
            "marca": m.get("brand", "-"),
            "modelo": m.get("model", "-"),
            "ano": str(m.get("year", "-")),
            "status": "Operacional" if m.get("status") == "operational" else m.get("status", "-")
        })
    
    columns = ["Nome", "Placa", "Categoria", "Marca", "Modelo", "Ano", "Status"]
    buffer = generate_pdf_report("Relatório de Máquinas", data, columns)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=maquinas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
    )


@export_router.get("/pdf/maintenances")
async def export_maintenances_pdf(
    machine_id: Optional[str] = None,
    maintenance_type: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar manutenções em PDF"""
    await get_current_user(credentials)
    
    query = {}
    if machine_id:
        query["machine_id"] = machine_id
    if maintenance_type:
        query["maintenance_type"] = maintenance_type
    if data_inicio and data_fim:
        query["replacement_date"] = {"$gte": data_inicio, "$lte": data_fim}
    
    maintenances = await db.maintenances.find(query, {"_id": 0}).sort("replacement_date", -1).to_list(500)
    
    data = []
    total_valor = 0
    for m in maintenances:
        machine = await db.machines.find_one({"id": m.get("machine_id")}, {"_id": 0})
        valor = m.get("part_value", 0)
        total_valor += valor
        data.append({
            "maquina": machine["name"] if machine else "-",
            "peca": m.get("part_name", "-"),
            "tipo": "Preventiva" if m.get("maintenance_type") == "preventiva" else "Corretiva",
            "data": m.get("replacement_date", "-"),
            "valor": valor
        })
    
    columns = ["Máquina", "Peça", "Tipo", "Data", "Valor"]
    buffer = generate_pdf_report(f"Relatório de Manutenções - Total: R$ {total_valor:,.2f}", data, columns)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=manutencoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
    )


@export_router.get("/pdf/stock")
async def export_stock_pdf(
    category: Optional[str] = None,
    low_stock_only: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar estoque em PDF"""
    await get_current_user(credentials)
    
    query = {}
    if category:
        query["category"] = category
    
    items = await db.stock_items.find(query, {"_id": 0}).to_list(500)
    
    if low_stock_only:
        items = [i for i in items if i.get("quantity", 0) <= i.get("min_quantity", 0)]
    
    data = []
    for i in items:
        data.append({
            "codigo": i.get("code", "-"),
            "nome": i.get("name", "-"),
            "categoria": i.get("category", "-"),
            "quantidade": str(i.get("quantity", 0)),
            "minimo": str(i.get("min_quantity", 0)),
            "preco_unit": i.get("unit_price", 0),
            "local": i.get("location", "-")
        })
    
    columns = ["Código", "Nome", "Categoria", "Quantidade", "Mínimo", "Preço Unit", "Local"]
    buffer = generate_pdf_report("Relatório de Estoque", data, columns)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
    )


@export_router.get("/pdf/contas-pagar")
async def export_contas_pagar_pdf(
    status: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar contas a pagar em PDF"""
    await get_current_user(credentials)
    
    query = {}
    if status:
        query["status"] = status
    if data_inicio and data_fim:
        query["data_vencimento"] = {"$gte": data_inicio, "$lte": data_fim}
    
    contas = await db.contas_pagar.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(500)
    
    data = []
    total = 0
    for c in contas:
        valor = c.get("valor", 0)
        total += valor
        data.append({
            "numero": str(c.get("numero", "-")),
            "descricao": c.get("descricao", "-"),
            "fornecedor": c.get("fornecedor_nome", "-"),
            "vencimento": c.get("data_vencimento", "-"),
            "valor": valor,
            "status": c.get("status", "-").replace("_", " ").title()
        })
    
    columns = ["Número", "Descrição", "Fornecedor", "Vencimento", "Valor", "Status"]
    buffer = generate_pdf_report(f"Contas a Pagar - Total: R$ {total:,.2f}", data, columns)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=contas_pagar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
    )


@export_router.get("/pdf/contas-receber")
async def export_contas_receber_pdf(
    status: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar contas a receber em PDF"""
    await get_current_user(credentials)
    
    query = {}
    if status:
        query["status"] = status
    if data_inicio and data_fim:
        query["data_vencimento"] = {"$gte": data_inicio, "$lte": data_fim}
    
    contas = await db.contas_receber.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(500)
    
    data = []
    total = 0
    for c in contas:
        valor = c.get("valor", 0)
        total += valor
        data.append({
            "numero": str(c.get("numero", "-")),
            "descricao": c.get("descricao", "-"),
            "cliente": c.get("cliente_nome", "-"),
            "vencimento": c.get("data_vencimento", "-"),
            "valor": valor,
            "status": c.get("status", "-").replace("_", " ").title()
        })
    
    columns = ["Número", "Descrição", "Cliente", "Vencimento", "Valor", "Status"]
    buffer = generate_pdf_report(f"Contas a Receber - Total: R$ {total:,.2f}", data, columns)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=contas_receber_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
    )


# ============ EXCEL EXPORTS ============

@export_router.get("/excel/machines")
async def export_machines_excel(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar máquinas em Excel"""
    await get_current_user(credentials)
    
    import pandas as pd
    
    machines = await db.machines.find({}, {"_id": 0}).to_list(500)
    
    data = []
    for m in machines:
        category = await db.categories.find_one({"id": m.get("category_id")}, {"_id": 0})
        data.append({
            "Nome": m.get("name", "-"),
            "Placa": m.get("plate", "-"),
            "Categoria": category["name"] if category else "-",
            "Marca": m.get("brand", "-"),
            "Modelo": m.get("model", "-"),
            "Ano": m.get("year", ""),
            "Status": m.get("status", "-")
        })
    
    df = pd.DataFrame(data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Máquinas')
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=maquinas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
    )


@export_router.get("/excel/maintenances")
async def export_maintenances_excel(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar manutenções em Excel"""
    await get_current_user(credentials)
    
    import pandas as pd
    
    maintenances = await db.maintenances.find({}, {"_id": 0}).sort("replacement_date", -1).to_list(500)
    
    data = []
    for m in maintenances:
        machine = await db.machines.find_one({"id": m.get("machine_id")}, {"_id": 0})
        data.append({
            "Máquina": machine["name"] if machine else "-",
            "Peça": m.get("part_name", "-"),
            "Tipo": m.get("maintenance_type", "-"),
            "Data": m.get("replacement_date", "-"),
            "Valor": m.get("part_value", 0),
            "Descrição": m.get("description", "-")
        })
    
    df = pd.DataFrame(data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Manutenções')
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=manutencoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
    )


@export_router.get("/excel/stock")
async def export_stock_excel(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Exportar estoque em Excel"""
    await get_current_user(credentials)
    
    import pandas as pd
    
    items = await db.stock_items.find({}, {"_id": 0}).to_list(500)
    
    data = []
    for i in items:
        data.append({
            "Código": i.get("code", "-"),
            "Nome": i.get("name", "-"),
            "Categoria": i.get("category", "-"),
            "Quantidade": i.get("quantity", 0),
            "Mínimo": i.get("min_quantity", 0),
            "Preço Unitário": i.get("unit_price", 0),
            "Local": i.get("location", "-")
        })
    
    df = pd.DataFrame(data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estoque')
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
    )
