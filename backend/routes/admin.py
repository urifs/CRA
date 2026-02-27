"""
Admin Routes - Administrative module endpoints (Financeiro, Cadastros, Contas a Pagar/Receber, etc.)
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body, Query
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


class OrdemServicoCreate(BaseModel):
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    descricao: str
    tipo: str = "servico"
    data_abertura: str
    data_previsao: Optional[str] = None
    data_conclusao: Optional[str] = None
    valor_total: float = 0
    status: str = "aberta"
    prioridade: str = "media"
    responsavel_id: Optional[str] = None
    responsavel_nome: Optional[str] = None
    maquina_id: Optional[str] = None
    maquina_nome: Optional[str] = None
    observacoes: Optional[str] = None


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


# ============ CONTAS A PAGAR ============

@admin_router.get("/contas-pagar")
async def list_contas_pagar(
    status: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """Listar contas a pagar"""
    query = {}
    if status:
        query["status"] = status
    if data_inicio and data_fim:
        query["data_vencimento"] = {"$gte": data_inicio, "$lte": data_fim}
    
    contas = []
    async for c in db.contas_pagar.find(query).sort("data_vencimento", 1):
        c["_id"] = str(c["_id"])
        contas.append(c)
    return contas


@admin_router.get("/contas-pagar/{conta_id}")
async def get_conta_pagar(conta_id: str):
    """Obter conta a pagar por ID"""
    conta = await db.contas_pagar.find_one({"id": conta_id})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    conta["_id"] = str(conta["_id"])
    return conta


@admin_router.post("/contas-pagar")
async def create_conta_pagar(data: ContaPagarCreate):
    """Criar conta a pagar"""
    last = await db.contas_pagar.find_one(sort=[("numero", -1)])
    numero = (last.get("numero", 0) if last else 0) + 1
    
    conta_doc = data.dict()
    conta_doc["id"] = str(uuid.uuid4())
    conta_doc["numero"] = numero
    conta_doc["created_at"] = datetime.now().isoformat()
    
    await db.contas_pagar.insert_one(conta_doc)
    conta_doc["_id"] = str(conta_doc.get("_id", ""))
    return conta_doc


@admin_router.put("/contas-pagar/{conta_id}")
async def update_conta_pagar(conta_id: str, data: ContaPagarCreate):
    """Atualizar conta a pagar"""
    existing = await db.contas_pagar.find_one({"id": conta_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.contas_pagar.update_one({"id": conta_id}, {"$set": update_data})
    return {"message": "Conta atualizada"}


@admin_router.put("/contas-pagar/{conta_id}/quitar")
async def quitar_conta_pagar(conta_id: str, data_pagamento: str = Body(..., embed=True)):
    """Quitar conta a pagar"""
    existing = await db.contas_pagar.find_one({"id": conta_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_pagar.update_one(
        {"id": conta_id},
        {"$set": {"status": "quitada", "data_pagamento": data_pagamento, "updated_at": datetime.now().isoformat()}}
    )
    return {"message": "Conta quitada"}


@admin_router.delete("/contas-pagar/{conta_id}")
async def delete_conta_pagar(conta_id: str):
    """Excluir conta a pagar"""
    result = await db.contas_pagar.delete_one({"id": conta_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    return {"message": "Conta excluída"}


# ============ CONTAS A RECEBER ============

@admin_router.get("/contas-receber")
async def list_contas_receber(
    status: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """Listar contas a receber"""
    query = {}
    if status:
        query["status"] = status
    if data_inicio and data_fim:
        query["data_vencimento"] = {"$gte": data_inicio, "$lte": data_fim}
    
    contas = []
    async for c in db.contas_receber.find(query).sort("data_vencimento", 1):
        c["_id"] = str(c["_id"])
        contas.append(c)
    return contas


@admin_router.get("/contas-receber/{conta_id}")
async def get_conta_receber(conta_id: str):
    """Obter conta a receber por ID"""
    conta = await db.contas_receber.find_one({"id": conta_id})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    conta["_id"] = str(conta["_id"])
    return conta


@admin_router.post("/contas-receber")
async def create_conta_receber(data: ContaReceberCreate):
    """Criar conta a receber"""
    last = await db.contas_receber.find_one(sort=[("numero", -1)])
    numero = (last.get("numero", 0) if last else 0) + 1
    
    conta_doc = data.dict()
    conta_doc["id"] = str(uuid.uuid4())
    conta_doc["numero"] = numero
    conta_doc["created_at"] = datetime.now().isoformat()
    
    await db.contas_receber.insert_one(conta_doc)
    conta_doc["_id"] = str(conta_doc.get("_id", ""))
    return conta_doc


@admin_router.put("/contas-receber/{conta_id}")
async def update_conta_receber(conta_id: str, data: ContaReceberCreate):
    """Atualizar conta a receber"""
    existing = await db.contas_receber.find_one({"id": conta_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.contas_receber.update_one({"id": conta_id}, {"$set": update_data})
    return {"message": "Conta atualizada"}


@admin_router.put("/contas-receber/{conta_id}/receber")
async def receber_conta(conta_id: str, data_recebimento: str = Body(..., embed=True)):
    """Receber conta"""
    existing = await db.contas_receber.find_one({"id": conta_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_receber.update_one(
        {"id": conta_id},
        {"$set": {"status": "recebida", "data_recebimento": data_recebimento, "updated_at": datetime.now().isoformat()}}
    )
    return {"message": "Conta recebida"}


@admin_router.delete("/contas-receber/{conta_id}")
async def delete_conta_receber(conta_id: str):
    """Excluir conta a receber"""
    result = await db.contas_receber.delete_one({"id": conta_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    return {"message": "Conta excluída"}


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
