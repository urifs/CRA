from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Response, Body
from fastapi.responses import FileResponse
"""
================================================================================
CRA CONSTRUTORA - SISTEMA DE GESTÃO EMPRESARIAL
================================================================================
Backend API - FastAPI + MongoDB

ÍNDICE DO ARQUIVO:
------------------
Linha ~40   : MODELS - Modelos Pydantic
Linha ~350  : AUTH HELPERS - Funções de autenticação
Linha ~450  : AUTH ROUTES - Rotas de autenticação
Linha ~520  : CATEGORY ROUTES - Rotas de categorias de máquinas
Linha ~600  : MACHINE ROUTES - Rotas de máquinas
Linha ~800  : MAINTENANCE ROUTES - Rotas de manutenções
Linha ~1000 : STOCK ROUTES - Rotas de estoque
Linha ~1300 : OBRA ROUTES - Rotas de obras/projetos
Linha ~1500 : DASHBOARD ROUTES - Rotas do dashboard
Linha ~1800 : ADMIN FINANCIAL ROUTES - Rotas administrativas financeiras
Linha ~3200 : NOTIFICATION ROUTES - Rotas de notificações
Linha ~3400 : ADMIN PANEL ROUTES - Rotas do painel admin (usuários, auditoria, DB)
Linha ~4200 : EXPORT ROUTES - Rotas de exportação PDF
Linha ~4600 : CHATBOT ROUTES - Rotas do chatbot com IA
Linha ~4900 : FILE ROUTES - Rotas de upload de arquivos
Linha ~5100 : TASK ROUTES - Rotas do sistema de tarefas
Linha ~5350 : APP STARTUP/SHUTDOWN - Eventos da aplicação

ARQUITETURA:
------------
- Frontend: React + TailwindCSS + Shadcn/UI
- Backend: FastAPI + MongoDB (Motor)
- Auth: JWT com bcrypt para senhas
- Integração: Gemini AI para chatbot

DEPENDÊNCIAS PRINCIPAIS:
------------------------
- fastapi, motor (async MongoDB)
- pydantic, python-jose (JWT)
- bcrypt, reportlab (PDF)
- emergentintegrations (Gemini AI)
================================================================================
"""

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import jwt
import bcrypt
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import modular routes
from routes.rh import rh_router
from routes.admin import admin_router
from routes.machines import machines_router
from routes.chatbot import chatbot_router
from routes.storage import storage_router
from routes.exports import export_router
from routes.stock import stock_router
from routes.obras import obras_router

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'fleet-maintenance-secret-key-2024')
JWT_ALGORITHM = "HS256"

# Create the main app
app = FastAPI(title="CRA Construtora")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# ============ MODELS ============

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    role: str = "gerenciamento"
    created_at: str

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#E31A1A"  # Cor padrão vermelho

class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    color: str = "#E31A1A"
    subcategories_count: int = 0
    created_at: str

# Subcategorias de máquinas
class SubcategoryCreate(BaseModel):
    name: str
    category_id: str
    description: Optional[str] = ""

class SubcategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    category_id: str
    category_name: str = ""
    description: str
    created_at: str

class MachineCreate(BaseModel):
    name: str
    plate: Optional[str] = ""
    category_id: str
    subcategory_id: Optional[str] = None
    brand: Optional[str] = ""
    model: Optional[str] = ""
    year: Optional[int] = None
    notes: Optional[str] = ""
    obra_id: Optional[str] = None
    fleet_id: Optional[str] = None
    subfleet_id: Optional[str] = None
    operator_id: Optional[str] = None  # ID do funcionário/operador
    identificador_tipo: Optional[str] = None  # 'chassi' ou 'serie'
    identificador_numero: Optional[str] = None

class MachineResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    plate: Optional[str] = ""
    category_id: str
    category_name: Optional[str] = ""
    subcategory_id: Optional[str] = None
    subcategory_name: Optional[str] = ""
    brand: str
    model: str
    year: Optional[int] = None
    notes: str
    status: str
    obra_id: Optional[str] = None
    obra_name: Optional[str] = ""
    fleet_id: Optional[str] = None
    fleet_name: Optional[str] = ""
    subfleet_id: Optional[str] = None
    subfleet_name: Optional[str] = ""
    operator_id: Optional[str] = None
    operator_name: Optional[str] = ""
    identificador_tipo: Optional[str] = None
    identificador_numero: Optional[str] = None
    horimetro_atual: Optional[float] = None
    created_at: str

class MaintenanceCreate(BaseModel):
    machine_id: str
    part_name: str
    replacement_date: str
    part_value: float
    maintenance_type: str  # preventiva ou corretiva
    description: Optional[str] = ""
    is_oil_change: bool = False  # marca se é troca de óleo

class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_id: str
    machine_name: Optional[str] = ""
    machine_plate: Optional[str] = ""
    part_name: str
    replacement_date: str
    part_value: float
    maintenance_type: str
    description: str
    photos: List[str]
    is_oil_change: bool = False
    created_at: str

class DashboardStats(BaseModel):
    total_machines: int
    total_maintenances: int
    preventive_count: int
    corrective_count: int
    total_spent: float
    recent_maintenances: List[MaintenanceResponse]
    low_stock_count: int = 0
    oil_change_alerts: int = 0

# ============ OIL CHANGE / USAGE MODELS ============

class UsageLogCreate(BaseModel):
    machine_id: str
    hours: float
    notes: Optional[str] = ""

class UsageLogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_id: str
    machine_name: Optional[str] = ""
    machine_plate: Optional[str] = ""
    hours: float
    notes: str
    created_at: str

class OilChangeStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    machine_id: str
    machine_name: str
    machine_plate: str
    last_oil_change_date: Optional[str] = None
    hours_since_change: float
    hours_remaining: float
    days_since_change: int
    days_remaining: int
    needs_alert: bool
    alert_reason: Optional[str] = None

# ============ FLEET MODELS ============

class FleetCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class FleetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class FleetResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    machines_count: int = 0
    subfleets_count: int = 0
    created_at: str

class SubfleetCreate(BaseModel):
    name: str
    fleet_id: str
    description: Optional[str] = ""

class SubfleetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class SubfleetResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    fleet_id: str
    fleet_name: str = ""
    description: str
    machines_count: int = 0
    created_at: str

class NotificationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_id: str
    machine_name: str
    machine_plate: str
    notification_type: str
    message: str
    hours_remaining: Optional[float] = None
    days_remaining: Optional[int] = None
    created_at: str

# ============ STOCK MODELS ============

class StockCategoryCreate(BaseModel):
    name: str

class StockCategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    subcategories_count: int = 0
    created_at: str

# Subcategorias de estoque
class StockSubcategoryCreate(BaseModel):
    name: str
    category_id: str

class StockSubcategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    category_id: str
    category_name: str = ""
    created_at: str

class StockItemCreate(BaseModel):
    name: str
    code: Optional[str] = ""
    category: Optional[str] = ""  # filtro, óleo, correia, etc.
    subcategory_id: Optional[str] = None
    unit: str = "un"  # un, L, kg, etc.
    quantity: float = 0
    min_quantity: float = 0
    unit_price: Optional[float] = 0
    location: Optional[str] = ""
    notes: Optional[str] = ""

class StockItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    code: str
    category: str
    subcategory_id: Optional[str] = None
    subcategory_name: Optional[str] = ""
    unit: str
    quantity: float
    min_quantity: float
    unit_price: float
    location: str
    notes: str
    is_low_stock: bool
    created_at: str

class StockMovementCreate(BaseModel):
    item_id: str
    movement_type: str  # entrada ou saida
    quantity: float
    reason: Optional[str] = ""
    notes: Optional[str] = ""

class StockMovementResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    item_id: str
    item_name: Optional[str] = ""
    movement_type: str
    quantity: float
    previous_quantity: float
    new_quantity: float
    reason: str
    notes: str
    created_at: str

# ============ OBRA (PROJECT) MODELS ============

class ObraCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    location: Optional[str] = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "em_andamento"  # em_andamento, concluida, pausada

class ObraResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    location: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    machine_count: int = 0
    total_maintenance_cost: float = 0
    created_at: str

class ObraDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    location: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    machines: List[MachineResponse] = []
    maintenances: List[MaintenanceResponse] = []
    total_maintenance_cost: float = 0
    preventive_cost: float = 0
    corrective_cost: float = 0
    created_at: str

class MachineObraUpdate(BaseModel):
    obra_id: Optional[str] = None  # None to remove from obra

# ============ HORIMETRO MODELS ============

class HorimetroCreate(BaseModel):
    machine_id: str
    data: str
    hora_inicial: float
    hora_final: float
    horas_trabalhadas: Optional[float] = None
    operador: Optional[str] = None
    observacoes: Optional[str] = None
    tipo_medicao: Optional[str] = "hora"  # "hora" ou "km"

class HorimetroResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_id: str
    machine_name: Optional[str] = None
    data: str
    hora_inicial: float
    hora_final: float
    horas_trabalhadas: float
    operador: Optional[str] = None
    observacoes: Optional[str] = None
    tipo_medicao: str = "hora"
    created_by: str
    created_at: str

# ============ COMBUSTIVEL MODELS ============

# Modelo para veículo abastecedor (tanque)
class VeiculoAbastecedorCreate(BaseModel):
    machine_id: str  # ID da máquina que é abastecedora
    capacidade_diesel: float = 0  # Capacidade total de diesel em litros
    capacidade_oleo: float = 0  # Capacidade total de óleo em litros
    capacidade_graxa: float = 0  # Capacidade total de graxa em litros
    litros_diesel: float = 0  # Litros de diesel atual
    litros_oleo: float = 0  # Litros de óleo atual
    litros_graxa: float = 0  # Litros de graxa atual
    operador_id: Optional[str] = None

class VeiculoAbastecedorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_id: str
    machine_name: Optional[str] = None
    capacidade_diesel: float = 0
    capacidade_oleo: float = 0
    capacidade_graxa: float = 0
    litros_diesel: float = 0
    litros_oleo: float = 0
    litros_graxa: float = 0
    operador_id: Optional[str] = None
    operador_nome: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: Optional[str] = None

# Modelo para registro de combustível (abastecimento)
class CombustivelCreate(BaseModel):
    machine_id: str
    data: str
    tipo_registro: str = "abastecido"  # "abastecedor" ou "abastecido"
    tipo_medicao: str = "litros"  # 'litros_hora' ou 'litros_km' ou 'litros'
    hora_km_inicial: Optional[float] = None
    litros_diesel: float = 0
    litros_oleo: float = 0
    litros_graxa: float = 0
    # Para abastecido
    fonte_abastecimento: Optional[str] = None  # "interno" ou "externo"
    veiculo_abastecedor_id: Optional[str] = None  # ID do veículo abastecedor (se interno)
    operador_id: Optional[str] = None
    observacoes: Optional[str] = None

class CombustivelResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_id: str
    machine_name: Optional[str] = None
    data: str
    tipo_registro: str = "abastecido"
    tipo_medicao: str = "litros"
    hora_km_inicial: Optional[float] = None
    litros_diesel: float = 0
    litros_oleo: float = 0
    litros_graxa: float = 0
    fonte_abastecimento: Optional[str] = None
    veiculo_abastecedor_id: Optional[str] = None
    veiculo_abastecedor_nome: Optional[str] = None
    operador_id: Optional[str] = None
    operador_nome: Optional[str] = None
    observacoes: Optional[str] = None
    created_by: str
    created_at: str

# ============ AUDIT LOG MODELS ============

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    user_name: str
    user_email: str
    action: str  # criar, editar, excluir
    entity_type: str  # maquina, manutencao, obra, estoque, categoria, etc
    entity_id: str
    entity_name: str
    details: Optional[str] = ""
    created_at: str

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc).timestamp() + 86400 * 7  # 7 days
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ============ AUDIT LOG HELPER ============

async def create_audit_log(
    user: dict,
    action: str,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    details: str = "",
    module: str = ""
):
    """Create an audit log entry for tracking user actions."""
    # Mapear ações para descrições em português
    action_labels = {
        "criar": "Criou",
        "create": "Criou",
        "editar": "Editou",
        "update": "Editou",
        "excluir": "Excluiu",
        "delete": "Excluiu",
        "login": "Fez login",
        "logout": "Fez logout"
    }
    
    # Mapear tipos de entidade para descrições
    entity_labels = {
        "categoria": "Categoria de Máquina",
        "máquina": "Máquina",
        "maquina": "Máquina",
        "manutenção": "Manutenção",
        "manutencao": "Manutenção",
        "registro de uso": "Registro de Uso (Horímetro)",
        "categoria de estoque": "Categoria de Estoque",
        "item de estoque": "Item de Estoque",
        "movimentação de estoque (entrada)": "Entrada de Estoque",
        "movimentação de estoque (saída)": "Saída de Estoque",
        "obra": "Obra/Projeto",
        "cadastro": "Cadastro (Cliente/Fornecedor)",
        "conta_pagar": "Conta a Pagar",
        "conta_receber": "Conta a Receber",
        "produto": "Produto",
        "ordem_servico": "Ordem de Serviço",
        "plano_contas": "Plano de Contas",
        "centro_custo": "Centro de Custo",
        "forma_pagamento": "Forma de Pagamento",
        "aluguel": "Aluguel de Máquina",
        "documento (users)": "Documento (Usuários)",
        "documento (machines)": "Documento (Máquinas)",
        "documento (maintenances)": "Documento (Manutenções)",
        "usuario": "Usuário",
        "user": "Usuário"
    }
    
    # Determinar o módulo automaticamente se não especificado
    if not module:
        admin_entities = ["cadastro", "conta_pagar", "conta_receber", "produto", 
                         "ordem_servico", "plano_contas", "centro_custo", 
                         "forma_pagamento", "aluguel"]
        gerenciamento_entities = ["categoria", "máquina", "maquina", "manutenção", 
                                  "manutencao", "registro de uso", "categoria de estoque",
                                  "item de estoque", "obra"]
        admin_panel_entities = ["usuario", "user"]
        
        entity_lower = entity_type.lower()
        if any(e in entity_lower for e in admin_entities):
            module = "Administrativo"
        elif any(e in entity_lower for e in gerenciamento_entities) or "estoque" in entity_lower:
            module = "Gerenciamento"
        elif any(e in entity_lower for e in admin_panel_entities) or "documento" in entity_lower:
            module = "Painel Admin"
        else:
            module = "Sistema"
    
    # Criar descrição detalhada da ação
    action_label = action_labels.get(action.lower(), action.capitalize())
    entity_label = entity_labels.get(entity_type.lower(), entity_type)
    
    # Construir descrição completa
    full_action = f"{action_label} {entity_label}"
    
    # Adicionar detalhes formatados
    detailed_info = f"Item: {entity_name}"
    if details:
        detailed_info += f" | {details}"
    
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "user_email": user["email"],
        "action": full_action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "module": module,
        "details": detailed_info,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit_doc)

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user.email)
    user_response = UserResponse(
        id=user_id,
        name=user.name,
        email=user.email,
        created_at=user_doc["created_at"]
    )
    return TokenResponse(token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Atualizar último login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    token = create_token(user["id"], user["email"])
    user_response = UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        role=user.get("role", "gerenciamento"),
        created_at=user["created_at"]
    )
    return TokenResponse(token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        role=current_user.get("role", "gerenciamento"),
        created_at=current_user["created_at"]
    )

# ============ CREATE ADMIN ACCOUNT (PUBLIC) ============

class AdminCreate(BaseModel):
    name: str
    email: str
    password: str

@api_router.post("/auth/create-admin")
async def create_admin_account(data: AdminCreate):
    """
    Cria uma conta administrador com acesso total ao sistema.
    Disponível publicamente na tela de login.
    """
    # Verificar se email já existe
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Este email já está cadastrado")
    
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "role": "admin",  # Acesso total
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    return {"message": "Conta administrador criada com sucesso!", "email": data.email}

# ============ SPECIAL ADMIN SETUP ENDPOINT ============
# Endpoint especial para promover usuário para admin (usar uma vez para configurar)

class AdminSetupRequest(BaseModel):
    email: str
    secret_key: str

@api_router.post("/auth/setup-admin")
async def setup_admin(request: AdminSetupRequest):
    """
    Endpoint especial para promover um usuário existente para admin.
    Usar a chave secreta: CRA-SETUP-2026-ADMIN
    """
    SETUP_SECRET = "CRA-SETUP-2026-ADMIN"
    
    if request.secret_key != SETUP_SECRET:
        raise HTTPException(status_code=403, detail="Chave secreta inválida")
    
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Promover para admin com acesso total
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"role": "admin"}}
    )
    
    return {
        "message": f"Usuário {request.email} promovido para administrador com sucesso!",
        "email": request.email,
        "new_role": "admin"
    }

# ============ CATEGORY ROUTES ============

@api_router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, current_user: dict = Depends(get_current_user)):
    category_id = str(uuid.uuid4())
    category_doc = {
        "id": category_id,
        "name": category.name,
        "description": category.description or "",
        "color": category.color or "#E31A1A",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.categories.insert_one(category_doc)
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="categoria",
        entity_id=category_id,
        entity_name=category.name
    )
    
    return CategoryResponse(
        id=category_id,
        name=category.name,
        description=category.description or "",
        color=category.color or "#E31A1A",
        created_at=category_doc["created_at"]
    )

@api_router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(current_user: dict = Depends(get_current_user)):
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    return [CategoryResponse(
        id=c["id"],
        name=c["name"],
        description=c.get("description", ""),
        color=c.get("color", "#E31A1A"),
        created_at=c["created_at"]
    ) for c in categories]

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    await db.categories.delete_one({"id": category_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="categoria",
        entity_id=category_id,
        entity_name=existing["name"]
    )
    
    return {"message": "Categoria removida com sucesso"}

@api_router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, category: CategoryCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    await db.categories.update_one(
        {"id": category_id},
        {"$set": {"name": category.name, "description": category.description or "", "color": category.color or "#E31A1A"}}
    )
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="categoria",
        entity_id=category_id,
        entity_name=category.name,
        details=f"Nome anterior: {existing['name']}"
    )
    
    return CategoryResponse(
        id=category_id,
        name=category.name,
        description=category.description or "",
        color=category.color or "#E31A1A",
        created_at=existing["created_at"]
    )

# ============ SUBCATEGORY ROUTES (Machine Subcategories) ============

@api_router.post("/subcategories", response_model=SubcategoryResponse)
async def create_subcategory(subcategory: SubcategoryCreate, current_user: dict = Depends(get_current_user)):
    """Create a new subcategory for machines"""
    # Verify category exists
    category = await db.categories.find_one({"id": subcategory.category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    subcategory_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    doc = {
        "id": subcategory_id,
        "name": subcategory.name,
        "category_id": subcategory.category_id,
        "description": subcategory.description or "",
        "created_at": now
    }
    
    await db.subcategories.insert_one(doc)
    
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="subcategoria",
        entity_id=subcategory_id,
        entity_name=subcategory.name,
        module="Gerenciamento"
    )
    
    return SubcategoryResponse(**doc, category_name=category["name"])

@api_router.get("/subcategories", response_model=List[SubcategoryResponse])
async def list_subcategories(category_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """List all subcategories, optionally filtered by category"""
    query = {"category_id": category_id} if category_id else {}
    subcategories = await db.subcategories.find(query, {"_id": 0}).to_list(500)
    
    # Get category names
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    return [SubcategoryResponse(**s, category_name=category_map.get(s["category_id"], "")) for s in subcategories]

@api_router.put("/subcategories/{subcategory_id}", response_model=SubcategoryResponse)
async def update_subcategory(subcategory_id: str, data: SubcategoryCreate, current_user: dict = Depends(get_current_user)):
    """Update a subcategory"""
    existing = await db.subcategories.find_one({"id": subcategory_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    
    await db.subcategories.update_one(
        {"id": subcategory_id},
        {"$set": {"name": data.name, "description": data.description or ""}}
    )
    
    updated = await db.subcategories.find_one({"id": subcategory_id}, {"_id": 0})
    category = await db.categories.find_one({"id": updated["category_id"]}, {"_id": 0})
    
    return SubcategoryResponse(**updated, category_name=category["name"] if category else "")

@api_router.delete("/subcategories/{subcategory_id}")
async def delete_subcategory(subcategory_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a subcategory"""
    subcategory = await db.subcategories.find_one({"id": subcategory_id}, {"_id": 0})
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    
    # Remove subcategory from machines
    await db.machines.update_many({"subcategory_id": subcategory_id}, {"$set": {"subcategory_id": None}})
    
    await db.subcategories.delete_one({"id": subcategory_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="subcategoria",
        entity_id=subcategory_id,
        entity_name=subcategory["name"],
        module="Gerenciamento"
    )
    
    return {"message": "Subcategoria excluída com sucesso"}

# ============ FLEET ROUTES ============

@api_router.post("/fleets", response_model=FleetResponse)
async def create_fleet(fleet: FleetCreate, current_user: dict = Depends(get_current_user)):
    """Create a new fleet"""
    fleet_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    fleet_doc = {
        "id": fleet_id,
        "name": fleet.name,
        "description": fleet.description or "",
        "created_at": now
    }
    
    await db.fleets.insert_one(fleet_doc)
    
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="frota",
        entity_id=fleet_id,
        entity_name=fleet.name,
        module="Gerenciamento"
    )
    
    return FleetResponse(**fleet_doc, machines_count=0, subfleets_count=0)

@api_router.get("/fleets", response_model=List[FleetResponse])
async def list_fleets(current_user: dict = Depends(get_current_user)):
    """List all fleets"""
    fleets = await db.fleets.find({}, {"_id": 0}).to_list(500)
    
    result = []
    for f in fleets:
        # Count machines in this fleet
        machines_count = await db.machines.count_documents({"fleet_id": f["id"]})
        # Count subfleets
        subfleets_count = await db.subfleets.count_documents({"fleet_id": f["id"]})
        result.append(FleetResponse(
            **f,
            machines_count=machines_count,
            subfleets_count=subfleets_count
        ))
    
    return result

@api_router.get("/fleets/{fleet_id}", response_model=FleetResponse)
async def get_fleet(fleet_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific fleet"""
    fleet = await db.fleets.find_one({"id": fleet_id}, {"_id": 0})
    if not fleet:
        raise HTTPException(status_code=404, detail="Frota não encontrada")
    
    machines_count = await db.machines.count_documents({"fleet_id": fleet_id})
    subfleets_count = await db.subfleets.count_documents({"fleet_id": fleet_id})
    
    return FleetResponse(**fleet, machines_count=machines_count, subfleets_count=subfleets_count)

@api_router.put("/fleets/{fleet_id}", response_model=FleetResponse)
async def update_fleet(fleet_id: str, fleet: FleetUpdate, current_user: dict = Depends(get_current_user)):
    """Update a fleet"""
    existing = await db.fleets.find_one({"id": fleet_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Frota não encontrada")
    
    update_data = {k: v for k, v in fleet.dict().items() if v is not None}
    if update_data:
        await db.fleets.update_one({"id": fleet_id}, {"$set": update_data})
    
    updated = await db.fleets.find_one({"id": fleet_id}, {"_id": 0})
    machines_count = await db.machines.count_documents({"fleet_id": fleet_id})
    subfleets_count = await db.subfleets.count_documents({"fleet_id": fleet_id})
    
    await create_audit_log(
        user=current_user,
        action="atualizar",
        entity_type="frota",
        entity_id=fleet_id,
        entity_name=updated["name"],
        module="Gerenciamento"
    )
    
    return FleetResponse(**updated, machines_count=machines_count, subfleets_count=subfleets_count)

@api_router.delete("/fleets/{fleet_id}")
async def delete_fleet(fleet_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a fleet"""
    fleet = await db.fleets.find_one({"id": fleet_id}, {"_id": 0})
    if not fleet:
        raise HTTPException(status_code=404, detail="Frota não encontrada")
    
    # Remove fleet reference from machines
    await db.machines.update_many({"fleet_id": fleet_id}, {"$set": {"fleet_id": None, "subfleet_id": None}})
    
    # Delete subfleets
    await db.subfleets.delete_many({"fleet_id": fleet_id})
    
    # Delete fleet
    await db.fleets.delete_one({"id": fleet_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="frota",
        entity_id=fleet_id,
        entity_name=fleet["name"],
        module="Gerenciamento"
    )
    
    return {"message": "Frota excluída com sucesso"}

# ============ SUBFLEET ROUTES ============

@api_router.post("/subfleets", response_model=SubfleetResponse)
async def create_subfleet(subfleet: SubfleetCreate, current_user: dict = Depends(get_current_user)):
    """Create a new subfleet"""
    # Check if fleet exists
    fleet = await db.fleets.find_one({"id": subfleet.fleet_id}, {"_id": 0})
    if not fleet:
        raise HTTPException(status_code=404, detail="Frota não encontrada")
    
    subfleet_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    subfleet_doc = {
        "id": subfleet_id,
        "name": subfleet.name,
        "fleet_id": subfleet.fleet_id,
        "description": subfleet.description or "",
        "created_at": now
    }
    
    await db.subfleets.insert_one(subfleet_doc)
    
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="subfrota",
        entity_id=subfleet_id,
        entity_name=subfleet.name,
        module="Gerenciamento"
    )
    
    return SubfleetResponse(**subfleet_doc, fleet_name=fleet["name"], machines_count=0)

@api_router.get("/subfleets", response_model=List[SubfleetResponse])
async def list_subfleets(fleet_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """List subfleets, optionally filtered by fleet"""
    query = {"fleet_id": fleet_id} if fleet_id else {}
    subfleets = await db.subfleets.find(query, {"_id": 0}).to_list(500)
    
    # Get fleet names
    fleet_ids = list(set(s["fleet_id"] for s in subfleets))
    fleets = await db.fleets.find({"id": {"$in": fleet_ids}}, {"_id": 0}).to_list(500)
    fleet_map = {f["id"]: f["name"] for f in fleets}
    
    result = []
    for s in subfleets:
        machines_count = await db.machines.count_documents({"subfleet_id": s["id"]})
        result.append(SubfleetResponse(
            **s,
            fleet_name=fleet_map.get(s["fleet_id"], ""),
            machines_count=machines_count
        ))
    
    return result

@api_router.put("/subfleets/{subfleet_id}", response_model=SubfleetResponse)
async def update_subfleet(subfleet_id: str, subfleet: SubfleetUpdate, current_user: dict = Depends(get_current_user)):
    """Update a subfleet"""
    existing = await db.subfleets.find_one({"id": subfleet_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Subfrota não encontrada")
    
    update_data = {k: v for k, v in subfleet.dict().items() if v is not None}
    if update_data:
        await db.subfleets.update_one({"id": subfleet_id}, {"$set": update_data})
    
    updated = await db.subfleets.find_one({"id": subfleet_id}, {"_id": 0})
    fleet = await db.fleets.find_one({"id": updated["fleet_id"]}, {"_id": 0})
    machines_count = await db.machines.count_documents({"subfleet_id": subfleet_id})
    
    await create_audit_log(
        user=current_user,
        action="atualizar",
        entity_type="subfrota",
        entity_id=subfleet_id,
        entity_name=updated["name"],
        module="Gerenciamento"
    )
    
    return SubfleetResponse(**updated, fleet_name=fleet["name"] if fleet else "", machines_count=machines_count)

@api_router.delete("/subfleets/{subfleet_id}")
async def delete_subfleet(subfleet_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a subfleet"""
    subfleet = await db.subfleets.find_one({"id": subfleet_id}, {"_id": 0})
    if not subfleet:
        raise HTTPException(status_code=404, detail="Subfrota não encontrada")
    
    # Remove subfleet reference from machines
    await db.machines.update_many({"subfleet_id": subfleet_id}, {"$set": {"subfleet_id": None}})
    
    # Delete subfleet
    await db.subfleets.delete_one({"id": subfleet_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="subfrota",
        entity_id=subfleet_id,
        entity_name=subfleet["name"],
        module="Gerenciamento"
    )
    
    return {"message": "Subfrota excluída com sucesso"}

# ============ MACHINE ROUTES ============

@api_router.post("/machines", response_model=MachineResponse)
async def create_machine(machine: MachineCreate, current_user: dict = Depends(get_current_user)):
    # Check if plate already exists (only if plate is provided)
    if machine.plate:
        existing = await db.machines.find_one({"plate": machine.plate.upper()})
        if existing:
            raise HTTPException(status_code=400, detail="Placa já cadastrada")
    
    # Get category name
    category = await db.categories.find_one({"id": machine.category_id}, {"_id": 0})
    category_name = category["name"] if category else ""
    
    # Get obra name if specified
    obra_name = ""
    if machine.obra_id:
        obra = await db.obras.find_one({"id": machine.obra_id}, {"_id": 0})
        obra_name = obra["name"] if obra else ""
    
    # Get fleet and subfleet names
    fleet_name = ""
    subfleet_name = ""
    if machine.fleet_id:
        fleet = await db.fleets.find_one({"id": machine.fleet_id}, {"_id": 0})
        fleet_name = fleet["name"] if fleet else ""
    if machine.subfleet_id:
        subfleet = await db.subfleets.find_one({"id": machine.subfleet_id}, {"_id": 0})
        subfleet_name = subfleet["name"] if subfleet else ""
    
    # Get operator name
    operator_name = ""
    if machine.operator_id:
        operator = await db.cadastros.find_one({"id": machine.operator_id}, {"_id": 0})
        operator_name = operator.get("nome_razao", "") if operator else ""
    
    # Get subcategory name
    subcategory_name = ""
    if machine.subcategory_id:
        subcategory = await db.subcategories.find_one({"id": machine.subcategory_id}, {"_id": 0})
        subcategory_name = subcategory["name"] if subcategory else ""
    
    machine_id = str(uuid.uuid4())
    machine_doc = {
        "id": machine_id,
        "name": machine.name,
        "plate": (machine.plate or "").upper(),
        "category_id": machine.category_id,
        "subcategory_id": machine.subcategory_id,
        "brand": machine.brand or "",
        "model": machine.model or "",
        "year": machine.year,
        "notes": machine.notes or "",
        "obra_id": machine.obra_id,
        "fleet_id": machine.fleet_id,
        "subfleet_id": machine.subfleet_id,
        "operator_id": machine.operator_id,
        "status": "operational",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.machines.insert_one(machine_doc)
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="máquina",
        entity_id=machine_id,
        entity_name=f"{machine.name} ({(machine.plate or '').upper()})"
    )
    
    return MachineResponse(
        id=machine_id,
        name=machine.name,
        plate=(machine.plate or "").upper(),
        category_id=machine.category_id,
        category_name=category_name,
        subcategory_id=machine.subcategory_id,
        subcategory_name=subcategory_name,
        brand=machine.brand or "",
        model=machine.model or "",
        year=machine.year,
        notes=machine.notes or "",
        obra_id=machine.obra_id,
        obra_name=obra_name,
        fleet_id=machine.fleet_id,
        fleet_name=fleet_name,
        subfleet_id=machine.subfleet_id,
        subfleet_name=subfleet_name,
        operator_id=machine.operator_id,
        operator_name=operator_name,
        status="operational",
        created_at=machine_doc["created_at"]
    )

@api_router.get("/machines", response_model=List[MachineResponse])
async def get_machines(obra_id: Optional[str] = None, fleet_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if obra_id:
        query["obra_id"] = obra_id
    if fleet_id:
        query["fleet_id"] = fleet_id
    
    machines = await db.machines.find(query, {"_id": 0}).to_list(1000)
    
    # Get all categories
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    # Get all obras
    obras = await db.obras.find({}, {"_id": 0}).to_list(100)
    obra_map = {o["id"]: o["name"] for o in obras}
    
    # Get all fleets and subfleets
    fleets = await db.fleets.find({}, {"_id": 0}).to_list(100)
    fleet_map = {f["id"]: f["name"] for f in fleets}
    
    subfleets = await db.subfleets.find({}, {"_id": 0}).to_list(500)
    subfleet_map = {s["id"]: s["name"] for s in subfleets}
    
    # Get all cadastros (operators)
    cadastros = await db.cadastros.find({}, {"_id": 0}).to_list(1000)
    operator_map = {c["id"]: c.get("nome_razao", "") for c in cadastros}
    
    # Get all subcategories
    subcategories = await db.subcategories.find({}, {"_id": 0}).to_list(500)
    subcategory_map = {s["id"]: s["name"] for s in subcategories}
    
    return [MachineResponse(
        id=m["id"],
        name=m["name"],
        plate=m.get("plate", ""),
        category_id=m["category_id"],
        category_name=category_map.get(m["category_id"], ""),
        subcategory_id=m.get("subcategory_id"),
        subcategory_name=subcategory_map.get(m.get("subcategory_id", ""), ""),
        brand=m.get("brand", ""),
        model=m.get("model", ""),
        year=m.get("year"),
        notes=m.get("notes", ""),
        status=m.get("status", "operational"),
        obra_id=m.get("obra_id"),
        obra_name=obra_map.get(m.get("obra_id", ""), ""),
        fleet_id=m.get("fleet_id"),
        fleet_name=fleet_map.get(m.get("fleet_id", ""), ""),
        subfleet_id=m.get("subfleet_id"),
        subfleet_name=subfleet_map.get(m.get("subfleet_id", ""), ""),
        operator_id=m.get("operator_id"),
        operator_name=operator_map.get(m.get("operator_id", ""), ""),
        created_at=m["created_at"]
    ) for m in machines]

@api_router.get("/machines/{machine_id}", response_model=MachineResponse)
async def get_machine(machine_id: str, current_user: dict = Depends(get_current_user)):
    machine = await db.machines.find_one({"id": machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    category = await db.categories.find_one({"id": machine["category_id"]}, {"_id": 0})
    category_name = category["name"] if category else ""
    
    obra_name = ""
    if machine.get("obra_id"):
        obra = await db.obras.find_one({"id": machine["obra_id"]}, {"_id": 0})
        obra_name = obra["name"] if obra else ""
    
    fleet_name = ""
    if machine.get("fleet_id"):
        fleet = await db.fleets.find_one({"id": machine["fleet_id"]}, {"_id": 0})
        fleet_name = fleet["name"] if fleet else ""
    
    subfleet_name = ""
    if machine.get("subfleet_id"):
        subfleet = await db.subfleets.find_one({"id": machine["subfleet_id"]}, {"_id": 0})
        subfleet_name = subfleet["name"] if subfleet else ""
    
    operator_name = ""
    if machine.get("operator_id"):
        operator = await db.cadastros.find_one({"id": machine["operator_id"]}, {"_id": 0})
        operator_name = operator.get("nome_razao", "") if operator else ""
    
    return MachineResponse(
        id=machine["id"],
        name=machine["name"],
        plate=machine.get("plate", ""),
        category_id=machine["category_id"],
        category_name=category_name,
        brand=machine.get("brand", ""),
        model=machine.get("model", ""),
        year=machine.get("year"),
        notes=machine.get("notes", ""),
        status=machine.get("status", "operational"),
        obra_id=machine.get("obra_id"),
        obra_name=obra_name,
        fleet_id=machine.get("fleet_id"),
        fleet_name=fleet_name,
        subfleet_id=machine.get("subfleet_id"),
        subfleet_name=subfleet_name,
        operator_id=machine.get("operator_id"),
        operator_name=operator_name,
        created_at=machine["created_at"]
    )

@api_router.put("/machines/{machine_id}", response_model=MachineResponse)
async def update_machine(machine_id: str, machine: MachineCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.machines.find_one({"id": machine_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    # Get category name
    category = await db.categories.find_one({"id": machine.category_id}, {"_id": 0})
    category_name = category["name"] if category else ""
    
    # Get obra name if specified
    obra_name = ""
    if machine.obra_id:
        obra = await db.obras.find_one({"id": machine.obra_id}, {"_id": 0})
        obra_name = obra["name"] if obra else ""
    
    update_doc = {
        "name": machine.name,
        "plate": machine.plate.upper(),
        "category_id": machine.category_id,
        "brand": machine.brand or "",
        "model": machine.model or "",
        "year": machine.year,
        "notes": machine.notes or "",
        "obra_id": machine.obra_id
    }
    await db.machines.update_one({"id": machine_id}, {"$set": update_doc})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="máquina",
        entity_id=machine_id,
        entity_name=f"{machine.name} ({machine.plate.upper()})",
        details=f"Dados anteriores: {existing['name']} ({existing['plate']})"
    )
    
    return MachineResponse(
        id=machine_id,
        name=machine.name,
        plate=machine.plate.upper(),
        category_id=machine.category_id,
        category_name=category_name,
        brand=machine.brand or "",
        model=machine.model or "",
        year=machine.year,
        notes=machine.notes or "",
        status=existing.get("status", "operational"),
        obra_id=machine.obra_id,
        obra_name=obra_name,
        created_at=existing["created_at"]
    )

# ============ UPDATE MACHINE OBRA (TAG) ============

@api_router.patch("/machines/{machine_id}/obra", response_model=MachineResponse)
async def update_machine_obra(machine_id: str, update: MachineObraUpdate, current_user: dict = Depends(get_current_user)):
    existing = await db.machines.find_one({"id": machine_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    # Validate obra if specified
    obra_name = ""
    if update.obra_id:
        obra = await db.obras.find_one({"id": update.obra_id}, {"_id": 0})
        if not obra:
            raise HTTPException(status_code=404, detail="Obra não encontrada")
        obra_name = obra["name"]
    
    await db.machines.update_one({"id": machine_id}, {"$set": {"obra_id": update.obra_id}})
    
    # Audit log
    old_obra = existing.get("obra_id")
    if update.obra_id:
        action_detail = f"Vinculada à obra: {obra_name}"
    else:
        action_detail = "Removida da obra"
    
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="máquina",
        entity_id=machine_id,
        entity_name=f"{existing['name']} ({existing['plate']})",
        details=action_detail
    )
    
    category = await db.categories.find_one({"id": existing["category_id"]}, {"_id": 0})
    category_name = category["name"] if category else ""
    
    return MachineResponse(
        id=machine_id,
        name=existing["name"],
        plate=existing["plate"],
        category_id=existing["category_id"],
        category_name=category_name,
        brand=existing.get("brand", ""),
        model=existing.get("model", ""),
        year=existing.get("year"),
        notes=existing.get("notes", ""),
        status=existing.get("status", "operational"),
        obra_id=update.obra_id,
        obra_name=obra_name,
        created_at=existing["created_at"]
    )

@api_router.delete("/machines/{machine_id}")
async def delete_machine(machine_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.machines.find_one({"id": machine_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    await db.machines.delete_one({"id": machine_id})
    # Delete related maintenances
    await db.maintenances.delete_many({"machine_id": machine_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="máquina",
        entity_id=machine_id,
        entity_name=f"{existing['name']} ({existing['plate']})"
    )
    
    return {"message": "Máquina removida com sucesso"}

# ============ HORIMETRO ROUTES ============

@api_router.get("/horimetro", response_model=List[HorimetroResponse])
async def list_horimetro(
    machine_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Lista todos os registros de horímetro"""
    query = {}
    if machine_id:
        query["machine_id"] = machine_id
    
    registros = await db.horimetro.find(query, {"_id": 0}).sort("data", -1).skip(skip).limit(limit).to_list(limit)
    
    # Adicionar nome da máquina
    for registro in registros:
        machine = await db.machines.find_one({"id": registro["machine_id"]}, {"_id": 0, "name": 1})
        registro["machine_name"] = machine["name"] if machine else "Máquina não encontrada"
    
    return registros

@api_router.get("/horimetro/{registro_id}", response_model=HorimetroResponse)
async def get_horimetro(registro_id: str, current_user: dict = Depends(get_current_user)):
    """Obtém um registro de horímetro específico"""
    registro = await db.horimetro.find_one({"id": registro_id}, {"_id": 0})
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    machine = await db.machines.find_one({"id": registro["machine_id"]}, {"_id": 0, "name": 1})
    registro["machine_name"] = machine["name"] if machine else "Máquina não encontrada"
    
    return registro

@api_router.post("/horimetro", response_model=HorimetroResponse)
async def create_horimetro(data: HorimetroCreate, current_user: dict = Depends(get_current_user)):
    """Cria um novo registro de horímetro"""
    # Verificar se a máquina existe
    machine = await db.machines.find_one({"id": data.machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    # Calcular horas trabalhadas se não fornecido
    horas_trabalhadas = data.horas_trabalhadas
    if horas_trabalhadas is None:
        horas_trabalhadas = data.hora_final - data.hora_inicial
    
    registro_id = str(uuid.uuid4())
    registro_doc = {
        "id": registro_id,
        "machine_id": data.machine_id,
        "data": data.data,
        "hora_inicial": data.hora_inicial,
        "hora_final": data.hora_final,
        "horas_trabalhadas": horas_trabalhadas,
        "operador": data.operador or "",
        "observacoes": data.observacoes or "",
        "tipo_medicao": data.tipo_medicao or "hora",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.horimetro.insert_one(registro_doc)
    
    # Atualizar horímetro atual da máquina
    await db.machines.update_one(
        {"id": data.machine_id},
        {"$set": {"horimetro_atual": data.hora_final}}
    )
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="horímetro",
        entity_id=registro_id,
        entity_name=f"{machine['name']} - {data.data}"
    )
    
    registro_doc["machine_name"] = machine["name"]
    return registro_doc

@api_router.put("/horimetro/{registro_id}", response_model=HorimetroResponse)
async def update_horimetro(registro_id: str, data: HorimetroCreate, current_user: dict = Depends(get_current_user)):
    """Atualiza um registro de horímetro"""
    existing = await db.horimetro.find_one({"id": registro_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    machine = await db.machines.find_one({"id": data.machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    horas_trabalhadas = data.horas_trabalhadas
    if horas_trabalhadas is None:
        horas_trabalhadas = data.hora_final - data.hora_inicial
    
    update_doc = {
        "machine_id": data.machine_id,
        "data": data.data,
        "hora_inicial": data.hora_inicial,
        "hora_final": data.hora_final,
        "horas_trabalhadas": horas_trabalhadas,
        "operador": data.operador or "",
        "observacoes": data.observacoes or "",
        "tipo_medicao": data.tipo_medicao or "hora"
    }
    
    await db.horimetro.update_one({"id": registro_id}, {"$set": update_doc})
    
    # Atualizar horímetro atual da máquina se for o registro mais recente
    await db.machines.update_one(
        {"id": data.machine_id},
        {"$set": {"horimetro_atual": data.hora_final}}
    )
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="horímetro",
        entity_id=registro_id,
        entity_name=f"{machine['name']} - {data.data}"
    )
    
    updated = await db.horimetro.find_one({"id": registro_id}, {"_id": 0})
    updated["machine_name"] = machine["name"]
    return updated

@api_router.delete("/horimetro/{registro_id}")
async def delete_horimetro(registro_id: str, current_user: dict = Depends(get_current_user)):
    """Exclui um registro de horímetro"""
    existing = await db.horimetro.find_one({"id": registro_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    machine = await db.machines.find_one({"id": existing["machine_id"]}, {"_id": 0, "name": 1})
    
    await db.horimetro.delete_one({"id": registro_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="horímetro",
        entity_id=registro_id,
        entity_name=f"{machine['name'] if machine else 'Máquina'} - {existing['data']}"
    )
    
    return {"message": "Registro excluído com sucesso"}

@api_router.get("/horimetro/machine/{machine_id}", response_model=List[HorimetroResponse])
async def get_horimetro_by_machine(machine_id: str, limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Obtém registros de horímetro de uma máquina específica"""
    machine = await db.machines.find_one({"id": machine_id}, {"_id": 0, "name": 1})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    registros = await db.horimetro.find({"machine_id": machine_id}, {"_id": 0}).sort("data", -1).limit(limit).to_list(limit)
    
    for registro in registros:
        registro["machine_name"] = machine["name"]
    
    return registros

# ============ COMBUSTIVEL ROUTES ============

# --- Rotas para Veículos Abastecedores ---

@api_router.get("/combustivel/abastecedores")
async def list_veiculos_abastecedores(current_user: dict = Depends(get_current_user)):
    """Lista todos os veículos abastecedores cadastrados"""
    abastecedores = await db.veiculos_abastecedores.find({}, {"_id": 0}).to_list(100)
    
    result = []
    for abast in abastecedores:
        machine = await db.machines.find_one({"id": abast["machine_id"]}, {"_id": 0, "name": 1})
        abast["machine_name"] = machine["name"] if machine else "Máquina não encontrada"
        
        # Buscar nome do operador
        if abast.get("operador_id"):
            # Tentar funcionário do RH
            funcionario = await db.funcionarios.find_one({"id": abast["operador_id"]}, {"_id": 0, "nome": 1})
            if funcionario:
                abast["operador_nome"] = funcionario["nome"]
            else:
                # Tentar cadastro financeiro
                cadastro = await db.cadastros.find_one({"id": abast["operador_id"]}, {"_id": 0, "nome_razao": 1})
                abast["operador_nome"] = cadastro["nome_razao"] if cadastro else None
        
        result.append(abast)
    
    return result

@api_router.post("/combustivel/abastecedores")
async def create_veiculo_abastecedor(data: VeiculoAbastecedorCreate, current_user: dict = Depends(get_current_user)):
    """Cadastra uma máquina como veículo abastecedor"""
    machine = await db.machines.find_one({"id": data.machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    # Verificar se já existe
    existing = await db.veiculos_abastecedores.find_one({"machine_id": data.machine_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Esta máquina já está cadastrada como abastecedor")
    
    abastecedor_id = str(uuid.uuid4())
    abastecedor_doc = {
        "id": abastecedor_id,
        "machine_id": data.machine_id,
        "capacidade_diesel": data.capacidade_diesel,
        "capacidade_oleo": data.capacidade_oleo,
        "capacidade_graxa": data.capacidade_graxa,
        "litros_diesel": data.litros_diesel,
        "litros_oleo": data.litros_oleo,
        "litros_graxa": data.litros_graxa,
        "operador_id": data.operador_id,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.veiculos_abastecedores.insert_one(abastecedor_doc)
    
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="veículo abastecedor",
        entity_id=abastecedor_id,
        entity_name=machine["name"]
    )
    
    # Buscar o documento criado sem o _id para evitar erro de serialização
    created = await db.veiculos_abastecedores.find_one({"id": abastecedor_id}, {"_id": 0})
    created["machine_name"] = machine["name"]
    return created

@api_router.put("/combustivel/abastecedores/{abastecedor_id}")
async def update_veiculo_abastecedor(abastecedor_id: str, data: VeiculoAbastecedorCreate, current_user: dict = Depends(get_current_user)):
    """Atualiza um veículo abastecedor"""
    existing = await db.veiculos_abastecedores.find_one({"id": abastecedor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Veículo abastecedor não encontrado")
    
    machine = await db.machines.find_one({"id": data.machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    update_doc = {
        "machine_id": data.machine_id,
        "capacidade_diesel": data.capacidade_diesel,
        "capacidade_oleo": data.capacidade_oleo,
        "capacidade_graxa": data.capacidade_graxa,
        "litros_diesel": data.litros_diesel,
        "litros_oleo": data.litros_oleo,
        "litros_graxa": data.litros_graxa,
        "operador_id": data.operador_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.veiculos_abastecedores.update_one({"id": abastecedor_id}, {"$set": update_doc})
    
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="veículo abastecedor",
        entity_id=abastecedor_id,
        entity_name=machine["name"]
    )
    
    updated = await db.veiculos_abastecedores.find_one({"id": abastecedor_id}, {"_id": 0})
    updated["machine_name"] = machine["name"]
    return updated

@api_router.delete("/combustivel/abastecedores/{abastecedor_id}")
async def delete_veiculo_abastecedor(abastecedor_id: str, current_user: dict = Depends(get_current_user)):
    """Remove um veículo abastecedor"""
    existing = await db.veiculos_abastecedores.find_one({"id": abastecedor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Veículo abastecedor não encontrado")
    
    machine = await db.machines.find_one({"id": existing["machine_id"]}, {"_id": 0, "name": 1})
    
    await db.veiculos_abastecedores.delete_one({"id": abastecedor_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="veículo abastecedor",
        entity_id=abastecedor_id,
        entity_name=machine["name"] if machine else "Máquina"
    )
    
    return {"message": "Veículo abastecedor removido com sucesso"}

# --- Rotas para Registros de Combustível ---

@api_router.get("/combustivel", response_model=List[CombustivelResponse])
async def list_combustivel(
    machine_id: Optional[str] = None,
    tipo_registro: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Lista todos os registros de combustível"""
    query = {}
    if machine_id:
        query["machine_id"] = machine_id
    if tipo_registro:
        query["tipo_registro"] = tipo_registro
    
    registros = await db.combustivel.find(query, {"_id": 0}).sort("data", -1).skip(skip).limit(limit).to_list(limit)
    
    for registro in registros:
        machine = await db.machines.find_one({"id": registro["machine_id"]}, {"_id": 0, "name": 1})
        registro["machine_name"] = machine["name"] if machine else "Máquina não encontrada"
        
        # Buscar nome do veículo abastecedor se houver
        if registro.get("veiculo_abastecedor_id"):
            abast = await db.veiculos_abastecedores.find_one({"id": registro["veiculo_abastecedor_id"]}, {"_id": 0})
            if abast:
                abast_machine = await db.machines.find_one({"id": abast["machine_id"]}, {"_id": 0, "name": 1})
                registro["veiculo_abastecedor_nome"] = abast_machine["name"] if abast_machine else None
        
        # Buscar nome do operador
        if registro.get("operador_id"):
            funcionario = await db.funcionarios.find_one({"id": registro["operador_id"]}, {"_id": 0, "nome": 1})
            if funcionario:
                registro["operador_nome"] = funcionario["nome"]
            else:
                cadastro = await db.cadastros.find_one({"id": registro["operador_id"]}, {"_id": 0, "nome_razao": 1})
                registro["operador_nome"] = cadastro["nome_razao"] if cadastro else None
    
    return registros

@api_router.get("/combustivel/{registro_id}", response_model=CombustivelResponse)
async def get_combustivel(registro_id: str, current_user: dict = Depends(get_current_user)):
    """Obtém um registro de combustível específico"""
    registro = await db.combustivel.find_one({"id": registro_id}, {"_id": 0})
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    machine = await db.machines.find_one({"id": registro["machine_id"]}, {"_id": 0, "name": 1})
    registro["machine_name"] = machine["name"] if machine else "Máquina não encontrada"
    
    return registro

@api_router.post("/combustivel", response_model=CombustivelResponse)
async def create_combustivel(data: CombustivelCreate, current_user: dict = Depends(get_current_user)):
    """Cria um novo registro de combustível"""
    machine = await db.machines.find_one({"id": data.machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    registro_id = str(uuid.uuid4())
    registro_doc = {
        "id": registro_id,
        "machine_id": data.machine_id,
        "data": data.data,
        "tipo_registro": data.tipo_registro,
        "tipo_medicao": data.tipo_medicao,
        "hora_km_inicial": data.hora_km_inicial or 0,
        "litros_diesel": data.litros_diesel,
        "litros_oleo": data.litros_oleo,
        "litros_graxa": data.litros_graxa,
        "fonte_abastecimento": data.fonte_abastecimento,
        "veiculo_abastecedor_id": data.veiculo_abastecedor_id,
        "operador_id": data.operador_id,
        "observacoes": data.observacoes or "",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.combustivel.insert_one(registro_doc)
    
    # Se foi abastecido por um veículo abastecedor interno, descontar do tanque
    if data.tipo_registro == "abastecido" and data.fonte_abastecimento == "interno" and data.veiculo_abastecedor_id:
        abastecedor = await db.veiculos_abastecedores.find_one({"id": data.veiculo_abastecedor_id}, {"_id": 0})
        if abastecedor:
            new_diesel = max(0, abastecedor.get("litros_diesel", 0) - data.litros_diesel)
            new_oleo = max(0, abastecedor.get("litros_oleo", 0) - data.litros_oleo)
            new_graxa = max(0, abastecedor.get("litros_graxa", 0) - data.litros_graxa)
            
            await db.veiculos_abastecedores.update_one(
                {"id": data.veiculo_abastecedor_id},
                {"$set": {
                    "litros_diesel": new_diesel,
                    "litros_oleo": new_oleo,
                    "litros_graxa": new_graxa,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
    
    # Se for registro de abastecedor (entrada de combustível no tanque), adicionar ao tanque
    if data.tipo_registro == "abastecedor":
        # Encontrar o abastecedor pela máquina
        abastecedor = await db.veiculos_abastecedores.find_one({"machine_id": data.machine_id}, {"_id": 0})
        if abastecedor:
            new_diesel = abastecedor.get("litros_diesel", 0) + data.litros_diesel
            new_oleo = abastecedor.get("litros_oleo", 0) + data.litros_oleo
            new_graxa = abastecedor.get("litros_graxa", 0) + data.litros_graxa
            
            await db.veiculos_abastecedores.update_one(
                {"id": abastecedor["id"]},
                {"$set": {
                    "litros_diesel": new_diesel,
                    "litros_oleo": new_oleo,
                    "litros_graxa": new_graxa,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
    
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="combustível",
        entity_id=registro_id,
        entity_name=f"{machine['name']} - {data.data}"
    )
    
    # Buscar o documento criado sem o _id para evitar erro de serialização
    created = await db.combustivel.find_one({"id": registro_id}, {"_id": 0})
    created["machine_name"] = machine["name"]
    return created

@api_router.delete("/combustivel/{registro_id}")
async def delete_combustivel(registro_id: str, current_user: dict = Depends(get_current_user)):
    """Exclui um registro de combustível"""
    existing = await db.combustivel.find_one({"id": registro_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    machine = await db.machines.find_one({"id": existing["machine_id"]}, {"_id": 0, "name": 1})
    
    await db.combustivel.delete_one({"id": registro_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="combustível",
        entity_id=registro_id,
        entity_name=f"{machine['name'] if machine else 'Máquina'} - {existing['data']}"
    )
    
    return {"message": "Registro excluído com sucesso"}

@api_router.get("/combustivel/machine/{machine_id}")
async def get_combustivel_by_machine(machine_id: str, limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Obtém registros de combustível de uma máquina específica"""
    machine = await db.machines.find_one({"id": machine_id}, {"_id": 0, "name": 1})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    registros = await db.combustivel.find({"machine_id": machine_id}, {"_id": 0}).sort("data", -1).limit(limit).to_list(limit)
    
    for registro in registros:
        registro["machine_name"] = machine["name"]
    
    return registros

# Rota para buscar operadores (RH + Cadastros Financeiro)
@api_router.get("/operadores")
async def list_operadores(current_user: dict = Depends(get_current_user)):
    """Lista todos os operadores disponíveis (funcionários RH + cadastros financeiro)"""
    operadores = []
    
    # Buscar funcionários do RH
    funcionarios = await db.funcionarios.find({}, {"_id": 0, "id": 1, "nome": 1, "cargo": 1}).to_list(500)
    for f in funcionarios:
        operadores.append({
            "id": f["id"],
            "nome": f["nome"],
            "tipo": "rh",
            "cargo": f.get("cargo", "")
        })
    
    # Buscar cadastros do financeiro (nome_razao é o campo correto)
    cadastros = await db.cadastros.find({}, {"_id": 0, "id": 1, "nome_razao": 1, "tipo_cadastro": 1}).to_list(500)
    for c in cadastros:
        operadores.append({
            "id": c["id"],
            "nome": c.get("nome_razao", ""),
            "tipo": "cadastro",
            "cargo": c.get("tipo_cadastro", "")
        })
    
    return operadores

# ============ MAINTENANCE ROUTES ============

@api_router.post("/maintenances", response_model=MaintenanceResponse)
async def create_maintenance(maintenance: MaintenanceCreate, current_user: dict = Depends(get_current_user)):
    # Check if machine exists
    machine = await db.machines.find_one({"id": maintenance.machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    maintenance_id = str(uuid.uuid4())
    maintenance_doc = {
        "id": maintenance_id,
        "machine_id": maintenance.machine_id,
        "part_name": maintenance.part_name,
        "replacement_date": maintenance.replacement_date,
        "part_value": maintenance.part_value,
        "maintenance_type": maintenance.maintenance_type,
        "description": maintenance.description or "",
        "is_oil_change": maintenance.is_oil_change,
        "photos": [],
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.maintenances.insert_one(maintenance_doc)
    
    # Update machine status to maintenance if corrective
    if maintenance.maintenance_type == "corretiva":
        await db.machines.update_one({"id": maintenance.machine_id}, {"$set": {"status": "maintenance"}})
    
    # If oil change, reset hours counter for this machine
    if maintenance.is_oil_change:
        await db.machines.update_one(
            {"id": maintenance.machine_id}, 
            {"$set": {"last_oil_change_date": maintenance.replacement_date, "hours_since_oil_change": 0}}
        )
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="manutenção",
        entity_id=maintenance_id,
        entity_name=f"{maintenance.part_name} - {machine['name']}",
        details=f"Valor: R$ {maintenance.part_value:.2f}, Tipo: {maintenance.maintenance_type}"
    )
    
    return MaintenanceResponse(
        id=maintenance_id,
        machine_id=maintenance.machine_id,
        machine_name=machine["name"],
        machine_plate=machine["plate"],
        part_name=maintenance.part_name,
        replacement_date=maintenance.replacement_date,
        part_value=maintenance.part_value,
        maintenance_type=maintenance.maintenance_type,
        description=maintenance.description or "",
        is_oil_change=maintenance.is_oil_change,
        photos=[],
        created_at=maintenance_doc["created_at"]
    )

@api_router.get("/maintenances", response_model=List[MaintenanceResponse])
async def get_maintenances(machine_id: Optional[str] = None, oil_changes_only: bool = False, current_user: dict = Depends(get_current_user)):
    query = {}
    if machine_id:
        query["machine_id"] = machine_id
    if oil_changes_only:
        query["is_oil_change"] = True
    
    maintenances = await db.maintenances.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get all machines
    machines = await db.machines.find({}, {"_id": 0}).to_list(1000)
    machine_map = {m["id"]: {"name": m["name"], "plate": m["plate"]} for m in machines}
    
    return [MaintenanceResponse(
        id=m["id"],
        machine_id=m["machine_id"],
        machine_name=machine_map.get(m["machine_id"], {}).get("name", ""),
        machine_plate=machine_map.get(m["machine_id"], {}).get("plate", ""),
        part_name=m["part_name"],
        replacement_date=m["replacement_date"],
        part_value=m["part_value"],
        maintenance_type=m["maintenance_type"],
        description=m.get("description", ""),
        is_oil_change=m.get("is_oil_change", False),
        photos=m.get("photos", []),
        created_at=m["created_at"]
    ) for m in maintenances]

@api_router.get("/maintenances/{maintenance_id}", response_model=MaintenanceResponse)
async def get_maintenance(maintenance_id: str, current_user: dict = Depends(get_current_user)):
    maintenance = await db.maintenances.find_one({"id": maintenance_id}, {"_id": 0})
    if not maintenance:
        raise HTTPException(status_code=404, detail="Manutenção não encontrada")
    
    machine = await db.machines.find_one({"id": maintenance["machine_id"]}, {"_id": 0})
    
    return MaintenanceResponse(
        id=maintenance["id"],
        machine_id=maintenance["machine_id"],
        machine_name=machine["name"] if machine else "",
        machine_plate=machine["plate"] if machine else "",
        part_name=maintenance["part_name"],
        replacement_date=maintenance["replacement_date"],
        part_value=maintenance["part_value"],
        maintenance_type=maintenance["maintenance_type"],
        description=maintenance.get("description", ""),
        is_oil_change=maintenance.get("is_oil_change", False),
        photos=maintenance.get("photos", []),
        created_at=maintenance["created_at"]
    )

@api_router.delete("/maintenances/{maintenance_id}")
async def delete_maintenance(maintenance_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.maintenances.find_one({"id": maintenance_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Manutenção não encontrada")
    
    await db.maintenances.delete_one({"id": maintenance_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="manutenção",
        entity_id=maintenance_id,
        entity_name=existing["part_name"]
    )
    
    return {"message": "Manutenção removida com sucesso"}

# ============ PHOTO UPLOAD ============

@api_router.post("/maintenances/{maintenance_id}/photos")
async def upload_photo(
    maintenance_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    maintenance = await db.maintenances.find_one({"id": maintenance_id})
    if not maintenance:
        raise HTTPException(status_code=404, detail="Manutenção não encontrada")
    
    # Read file and convert to base64
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode('utf-8')
    photo_data = f"data:{file.content_type};base64,{base64_image}"
    
    # Add photo to maintenance
    photos = maintenance.get("photos", [])
    photos.append(photo_data)
    await db.maintenances.update_one({"id": maintenance_id}, {"$set": {"photos": photos}})
    
    return {"message": "Foto adicionada com sucesso", "photo": photo_data}

@api_router.delete("/maintenances/{maintenance_id}/photos/{photo_index}")
async def delete_photo(
    maintenance_id: str,
    photo_index: int,
    current_user: dict = Depends(get_current_user)
):
    maintenance = await db.maintenances.find_one({"id": maintenance_id})
    if not maintenance:
        raise HTTPException(status_code=404, detail="Manutenção não encontrada")
    
    photos = maintenance.get("photos", [])
    if photo_index < 0 or photo_index >= len(photos):
        raise HTTPException(status_code=400, detail="Índice de foto inválido")
    
    photos.pop(photo_index)
    await db.maintenances.update_one({"id": maintenance_id}, {"$set": {"photos": photos}})
    
    return {"message": "Foto removida com sucesso"}

# ============ USAGE LOG / OIL CHANGE ROUTES ============

@api_router.post("/usage-logs", response_model=UsageLogResponse)
async def create_usage_log(log: UsageLogCreate, current_user: dict = Depends(get_current_user)):
    # Check if machine exists
    machine = await db.machines.find_one({"id": log.machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    log_id = str(uuid.uuid4())
    log_doc = {
        "id": log_id,
        "machine_id": log.machine_id,
        "hours": log.hours,
        "notes": log.notes or "",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.usage_logs.insert_one(log_doc)
    
    # Update machine's hours since oil change
    current_hours = machine.get("hours_since_oil_change", 0)
    await db.machines.update_one(
        {"id": log.machine_id},
        {"$set": {"hours_since_oil_change": current_hours + log.hours}}
    )
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="registro de uso",
        entity_id=log_id,
        entity_name=f"{machine['name']} - {log.hours}h"
    )
    
    return UsageLogResponse(
        id=log_id,
        machine_id=log.machine_id,
        machine_name=machine["name"],
        machine_plate=machine["plate"],
        hours=log.hours,
        notes=log.notes or "",
        created_at=log_doc["created_at"]
    )

@api_router.get("/usage-logs", response_model=List[UsageLogResponse])
async def get_usage_logs(machine_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if machine_id:
        query["machine_id"] = machine_id
    
    logs = await db.usage_logs.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get machines
    machines = await db.machines.find({}, {"_id": 0}).to_list(1000)
    machine_map = {m["id"]: {"name": m["name"], "plate": m["plate"]} for m in machines}
    
    return [UsageLogResponse(
        id=l["id"],
        machine_id=l["machine_id"],
        machine_name=machine_map.get(l["machine_id"], {}).get("name", ""),
        machine_plate=machine_map.get(l["machine_id"], {}).get("plate", ""),
        hours=l["hours"],
        notes=l.get("notes", ""),
        created_at=l["created_at"]
    ) for l in logs]

@api_router.delete("/usage-logs/{log_id}")
async def delete_usage_log(log_id: str, current_user: dict = Depends(get_current_user)):
    """Exclui um registro de uso e atualiza as horas da máquina"""
    # Find the usage log
    log = await db.usage_logs.find_one({"id": log_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Registro de uso não encontrado")
    
    # Get machine info
    machine = await db.machines.find_one({"id": log["machine_id"]}, {"_id": 0})
    
    # Subtract hours from machine's total
    if machine:
        current_hours = machine.get("hours_since_oil_change", 0)
        new_hours = max(0, current_hours - log["hours"])  # Prevent negative
        await db.machines.update_one(
            {"id": log["machine_id"]},
            {"$set": {"hours_since_oil_change": new_hours}}
        )
    
    # Delete the usage log
    await db.usage_logs.delete_one({"id": log_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="registro de uso",
        entity_id=log_id,
        entity_name=f"{machine.get('name', 'N/A') if machine else 'N/A'} - {log['hours']}h"
    )
    
    return {"message": "Registro de uso excluído com sucesso"}

@api_router.get("/oil-change-status", response_model=List[OilChangeStatusResponse])
async def get_oil_change_status(current_user: dict = Depends(get_current_user)):
    machines = await db.machines.find({}, {"_id": 0}).to_list(1000)
    
    result = []
    today = datetime.now(timezone.utc)
    
    for machine in machines:
        hours_since_change = machine.get("hours_since_oil_change", 0)
        hours_remaining = 500 - hours_since_change
        
        last_oil_change_date = machine.get("last_oil_change_date")
        if last_oil_change_date:
            try:
                last_change = datetime.fromisoformat(last_oil_change_date.replace('Z', '+00:00'))
                if last_change.tzinfo is None:
                    last_change = last_change.replace(tzinfo=timezone.utc)
            except:
                last_change = datetime.strptime(last_oil_change_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_since_change = (today - last_change).days
            days_remaining = 365 - days_since_change
        else:
            days_since_change = 0
            days_remaining = 365
        
        # Check if needs alert
        needs_alert = False
        alert_reason = None
        
        if hours_remaining <= 50:
            needs_alert = True
            alert_reason = f"Faltam apenas {hours_remaining:.0f} horas para atingir 500h de uso"
        elif days_remaining <= 60 and hours_remaining > 50:
            needs_alert = True
            alert_reason = f"Faltam {days_remaining} dias para completar 1 ano desde a última troca"
        
        result.append(OilChangeStatusResponse(
            machine_id=machine["id"],
            machine_name=machine["name"],
            machine_plate=machine["plate"],
            last_oil_change_date=last_oil_change_date,
            hours_since_change=hours_since_change,
            hours_remaining=max(0, hours_remaining),
            days_since_change=days_since_change,
            days_remaining=max(0, days_remaining),
            needs_alert=needs_alert,
            alert_reason=alert_reason
        ))
    
    return result

@api_router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(current_user: dict = Depends(get_current_user)):
    machines = await db.machines.find({}, {"_id": 0}).to_list(1000)
    
    notifications = []
    today = datetime.now(timezone.utc)
    
    for machine in machines:
        hours_since_change = machine.get("hours_since_oil_change", 0)
        hours_remaining = 500 - hours_since_change
        
        last_oil_change_date = machine.get("last_oil_change_date")
        if last_oil_change_date:
            try:
                last_change = datetime.fromisoformat(last_oil_change_date.replace('Z', '+00:00'))
                if last_change.tzinfo is None:
                    last_change = last_change.replace(tzinfo=timezone.utc)
            except:
                last_change = datetime.strptime(last_oil_change_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_since_change = (today - last_change).days
            days_remaining = 365 - days_since_change
        else:
            days_since_change = 0
            days_remaining = 365
        
        # Alert for hours
        if hours_remaining <= 50 and hours_remaining > 0:
            notifications.append(NotificationResponse(
                id=f"oil-hours-{machine['id']}",
                machine_id=machine["id"],
                machine_name=machine["name"],
                machine_plate=machine["plate"],
                notification_type="oil_change_hours",
                message=f"⚠️ Troca de óleo necessária em breve! Restam apenas {hours_remaining:.0f} horas de uso.",
                hours_remaining=hours_remaining,
                days_remaining=None,
                created_at=today.isoformat()
            ))
        elif hours_remaining <= 0:
            notifications.append(NotificationResponse(
                id=f"oil-hours-urgent-{machine['id']}",
                machine_id=machine["id"],
                machine_name=machine["name"],
                machine_plate=machine["plate"],
                notification_type="oil_change_urgent",
                message=f"🚨 URGENTE: Limite de 500 horas atingido! Troque o óleo imediatamente.",
                hours_remaining=0,
                days_remaining=None,
                created_at=today.isoformat()
            ))
        
        # Alert for time (only if hours haven't triggered yet)
        if hours_remaining > 50:
            if days_remaining <= 0:
                notifications.append(NotificationResponse(
                    id=f"oil-time-urgent-{machine['id']}",
                    machine_id=machine["id"],
                    machine_name=machine["name"],
                    machine_plate=machine["plate"],
                    notification_type="oil_change_time_urgent",
                    message=f"🚨 URGENTE: Completou 1 ano desde a última troca de óleo! Troque imediatamente.",
                    hours_remaining=hours_remaining,
                    days_remaining=0,
                    created_at=today.isoformat()
                ))
            elif days_remaining <= 60:
                notifications.append(NotificationResponse(
                    id=f"oil-time-{machine['id']}",
                    machine_id=machine["id"],
                    machine_name=machine["name"],
                    machine_plate=machine["plate"],
                    notification_type="oil_change_time",
                    message=f"⚠️ Faltam {days_remaining} dias para completar 1 ano desde a última troca de óleo.",
                    hours_remaining=hours_remaining,
                    days_remaining=days_remaining,
                    created_at=today.isoformat()
                ))
    
    # Add low stock alerts (quantity < 5)
    stock_items = await db.stock_items.find({}, {"_id": 0}).to_list(1000)
    for item in stock_items:
        if item["quantity"] < 5:
            if item["quantity"] <= 0:
                notifications.append(NotificationResponse(
                    id=f"stock-empty-{item['id']}",
                    machine_id="",
                    machine_name=item["name"],
                    machine_plate=item.get("code", ""),
                    notification_type="stock_empty",
                    message=f"🚨 ESTOQUE ZERADO: {item['name']} está sem estoque! Reponha imediatamente.",
                    hours_remaining=None,
                    days_remaining=None,
                    created_at=today.isoformat()
                ))
            else:
                notifications.append(NotificationResponse(
                    id=f"stock-low-{item['id']}",
                    machine_id="",
                    machine_name=item["name"],
                    machine_plate=item.get("code", ""),
                    notification_type="stock_low",
                    message=f"⚠️ Estoque baixo: {item['name']} tem apenas {item['quantity']:.0f} {item.get('unit', 'un')} restantes.",
                    hours_remaining=None,
                    days_remaining=None,
                    created_at=today.isoformat()
                ))
    
    # Sort by urgency
    def sort_key(n):
        if "urgent" in n.notification_type or "empty" in n.notification_type:
            return 0
        return 1
    
    notifications.sort(key=sort_key)
    
    return notifications

# ============ BALANCE / FINANCIAL REPORTS ============

class MachineExpenseResponse(BaseModel):
    machine_id: str
    machine_name: str
    machine_plate: str
    category_name: str
    total_maintenances: int
    total_spent: float
    preventive_spent: float
    corrective_spent: float
    last_maintenance_date: Optional[str] = None

class MonthlyExpenseResponse(BaseModel):
    month: str
    year: int
    total_spent: float
    maintenance_count: int

class BalanceResponse(BaseModel):
    total_spent: float
    total_maintenances: int
    preventive_total: float
    corrective_total: float
    preventive_count: int
    corrective_count: int
    average_per_maintenance: float
    expenses_by_machine: List[MachineExpenseResponse]
    expenses_by_month: List[MonthlyExpenseResponse]

@api_router.get("/balance", response_model=BalanceResponse)
async def get_balance(current_user: dict = Depends(get_current_user)):
    # Get all maintenances
    maintenances = await db.maintenances.find({}, {"_id": 0}).to_list(10000)
    
    # Get all machines with categories
    machines = await db.machines.find({}, {"_id": 0}).to_list(1000)
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    machine_map = {m["id"]: {
        "name": m["name"], 
        "plate": m["plate"],
        "category_name": category_map.get(m.get("category_id", ""), "")
    } for m in machines}
    
    # Calculate totals
    total_spent = sum(m["part_value"] for m in maintenances)
    total_maintenances = len(maintenances)
    preventive = [m for m in maintenances if m["maintenance_type"] == "preventiva"]
    corrective = [m for m in maintenances if m["maintenance_type"] == "corretiva"]
    preventive_total = sum(m["part_value"] for m in preventive)
    corrective_total = sum(m["part_value"] for m in corrective)
    average_per_maintenance = total_spent / total_maintenances if total_maintenances > 0 else 0
    
    # Expenses by machine
    machine_expenses = {}
    for m in maintenances:
        mid = m["machine_id"]
        if mid not in machine_expenses:
            machine_expenses[mid] = {
                "total_maintenances": 0,
                "total_spent": 0,
                "preventive_spent": 0,
                "corrective_spent": 0,
                "last_maintenance_date": None
            }
        machine_expenses[mid]["total_maintenances"] += 1
        machine_expenses[mid]["total_spent"] += m["part_value"]
        if m["maintenance_type"] == "preventiva":
            machine_expenses[mid]["preventive_spent"] += m["part_value"]
        else:
            machine_expenses[mid]["corrective_spent"] += m["part_value"]
        
        # Track last maintenance
        if machine_expenses[mid]["last_maintenance_date"] is None or m["replacement_date"] > machine_expenses[mid]["last_maintenance_date"]:
            machine_expenses[mid]["last_maintenance_date"] = m["replacement_date"]
    
    expenses_by_machine = [
        MachineExpenseResponse(
            machine_id=mid,
            machine_name=machine_map.get(mid, {}).get("name", "Máquina Removida"),
            machine_plate=machine_map.get(mid, {}).get("plate", "-"),
            category_name=machine_map.get(mid, {}).get("category_name", ""),
            total_maintenances=data["total_maintenances"],
            total_spent=data["total_spent"],
            preventive_spent=data["preventive_spent"],
            corrective_spent=data["corrective_spent"],
            last_maintenance_date=data["last_maintenance_date"]
        )
        for mid, data in machine_expenses.items()
    ]
    expenses_by_machine.sort(key=lambda x: x.total_spent, reverse=True)
    
    # Expenses by month
    month_expenses = {}
    for m in maintenances:
        try:
            date = datetime.fromisoformat(m["replacement_date"].replace('Z', '+00:00'))
        except:
            date = datetime.strptime(m["replacement_date"], "%Y-%m-%d")
        key = f"{date.year}-{date.month:02d}"
        if key not in month_expenses:
            month_expenses[key] = {"total_spent": 0, "count": 0, "year": date.year, "month": date.month}
        month_expenses[key]["total_spent"] += m["part_value"]
        month_expenses[key]["count"] += 1
    
    month_names = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    expenses_by_month = [
        MonthlyExpenseResponse(
            month=month_names[data["month"]],
            year=data["year"],
            total_spent=data["total_spent"],
            maintenance_count=data["count"]
        )
        for key, data in sorted(month_expenses.items(), reverse=True)
    ]
    
    return BalanceResponse(
        total_spent=total_spent,
        total_maintenances=total_maintenances,
        preventive_total=preventive_total,
        corrective_total=corrective_total,
        preventive_count=len(preventive),
        corrective_count=len(corrective),
        average_per_maintenance=average_per_maintenance,
        expenses_by_machine=expenses_by_machine,
        expenses_by_month=expenses_by_month[:12]  # Last 12 months
    )

# ============ DASHBOARD ============

@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    # Count machines
    total_machines = await db.machines.count_documents({})
    
    # Count and sum maintenances
    maintenances = await db.maintenances.find({}, {"_id": 0}).to_list(1000)
    total_maintenances = len(maintenances)
    preventive_count = len([m for m in maintenances if m["maintenance_type"] == "preventiva"])
    corrective_count = len([m for m in maintenances if m["maintenance_type"] == "corretiva"])
    total_spent = sum(m["part_value"] for m in maintenances)
    
    # Get recent maintenances
    recent = await db.maintenances.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    # Get machines for recent maintenances
    machines = await db.machines.find({}, {"_id": 0}).to_list(1000)
    machine_map = {m["id"]: {"name": m["name"], "plate": m["plate"]} for m in machines}
    
    recent_maintenances = [MaintenanceResponse(
        id=m["id"],
        machine_id=m["machine_id"],
        machine_name=machine_map.get(m["machine_id"], {}).get("name", ""),
        machine_plate=machine_map.get(m["machine_id"], {}).get("plate", ""),
        part_name=m["part_name"],
        replacement_date=m["replacement_date"],
        part_value=m["part_value"],
        maintenance_type=m["maintenance_type"],
        description=m.get("description", ""),
        is_oil_change=m.get("is_oil_change", False),
        photos=m.get("photos", []),
        created_at=m["created_at"]
    ) for m in recent]
    
    # Count oil change alerts
    oil_change_alerts = 0
    today = datetime.now(timezone.utc)
    for machine in machines:
        hours_since_change = machine.get("hours_since_oil_change", 0)
        hours_remaining = 500 - hours_since_change
        
        last_oil_change_date = machine.get("last_oil_change_date")
        if last_oil_change_date:
            try:
                last_change = datetime.fromisoformat(last_oil_change_date.replace('Z', '+00:00'))
                if last_change.tzinfo is None:
                    last_change = last_change.replace(tzinfo=timezone.utc)
            except:
                last_change = datetime.strptime(last_oil_change_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_remaining = 365 - (today - last_change).days
        else:
            days_remaining = 365
        
        if hours_remaining <= 50 or days_remaining <= 60:
            oil_change_alerts += 1
    
    return DashboardStats(
        total_machines=total_machines,
        total_maintenances=total_maintenances,
        preventive_count=preventive_count,
        corrective_count=corrective_count,
        total_spent=total_spent,
        recent_maintenances=recent_maintenances,
        low_stock_count=await db.stock_items.count_documents({
            "$expr": {"$lte": ["$quantity", "$min_quantity"]}
        }),
        oil_change_alerts=oil_change_alerts
    )

# ============ STOCK ROUTES ============

# Stock Categories
@api_router.post("/stock/categories", response_model=StockCategoryResponse)
async def create_stock_category(category: StockCategoryCreate, current_user: dict = Depends(get_current_user)):
    # Check if category already exists
    existing = await db.stock_categories.find_one({"name": category.name})
    if existing:
        raise HTTPException(status_code=400, detail="Categoria já existe")
    
    category_id = str(uuid.uuid4())
    category_doc = {
        "id": category_id,
        "name": category.name,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_categories.insert_one(category_doc)
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="categoria de estoque",
        entity_id=category_id,
        entity_name=category.name
    )
    
    return StockCategoryResponse(
        id=category_id,
        name=category.name,
        created_at=category_doc["created_at"]
    )

@api_router.get("/stock/categories", response_model=List[StockCategoryResponse])
async def get_stock_categories(current_user: dict = Depends(get_current_user)):
    categories = await db.stock_categories.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    return [StockCategoryResponse(
        id=c["id"],
        name=c["name"],
        created_at=c["created_at"]
    ) for c in categories]

@api_router.delete("/stock/categories/{category_id}")
async def delete_stock_category(category_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.stock_categories.find_one({"id": category_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    await db.stock_categories.delete_one({"id": category_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="categoria de estoque",
        entity_id=category_id,
        entity_name=existing["name"]
    )
    
    return {"message": "Categoria removida com sucesso"}

# Stock Subcategories
@api_router.post("/stock/subcategories", response_model=StockSubcategoryResponse)
async def create_stock_subcategory(subcategory: StockSubcategoryCreate, current_user: dict = Depends(get_current_user)):
    """Create a new stock subcategory"""
    # Verify category exists
    category = await db.stock_categories.find_one({"id": subcategory.category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Categoria de estoque não encontrada")
    
    subcategory_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    doc = {
        "id": subcategory_id,
        "name": subcategory.name,
        "category_id": subcategory.category_id,
        "created_at": now
    }
    
    await db.stock_subcategories.insert_one(doc)
    
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="subcategoria de estoque",
        entity_id=subcategory_id,
        entity_name=subcategory.name
    )
    
    return StockSubcategoryResponse(**doc, category_name=category["name"])

@api_router.get("/stock/subcategories", response_model=List[StockSubcategoryResponse])
async def list_stock_subcategories(category_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """List all stock subcategories, optionally filtered by category"""
    query = {"category_id": category_id} if category_id else {}
    subcategories = await db.stock_subcategories.find(query, {"_id": 0}).to_list(500)
    
    # Get category names
    categories = await db.stock_categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    return [StockSubcategoryResponse(**s, category_name=category_map.get(s["category_id"], "")) for s in subcategories]

@api_router.delete("/stock/subcategories/{subcategory_id}")
async def delete_stock_subcategory(subcategory_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a stock subcategory"""
    subcategory = await db.stock_subcategories.find_one({"id": subcategory_id}, {"_id": 0})
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    
    # Remove subcategory from items
    await db.stock_items.update_many({"subcategory_id": subcategory_id}, {"$set": {"subcategory_id": None}})
    
    await db.stock_subcategories.delete_one({"id": subcategory_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="subcategoria de estoque",
        entity_id=subcategory_id,
        entity_name=subcategory["name"]
    )
    
    return {"message": "Subcategoria removida com sucesso"}

# Stock Items
@api_router.post("/stock/items", response_model=StockItemResponse)
async def create_stock_item(item: StockItemCreate, current_user: dict = Depends(get_current_user)):
    item_id = str(uuid.uuid4())
    item_doc = {
        "id": item_id,
        "name": item.name,
        "code": item.code or "",
        "category": item.category or "",
        "unit": item.unit,
        "quantity": item.quantity,
        "min_quantity": item.min_quantity,
        "unit_price": item.unit_price or 0,
        "location": item.location or "",
        "notes": item.notes or "",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_items.insert_one(item_doc)
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="item de estoque",
        entity_id=item_id,
        entity_name=item.name
    )
    
    return StockItemResponse(
        id=item_id,
        name=item.name,
        code=item.code or "",
        category=item.category or "",
        unit=item.unit,
        quantity=item.quantity,
        min_quantity=item.min_quantity,
        unit_price=item.unit_price or 0,
        location=item.location or "",
        notes=item.notes or "",
        is_low_stock=item.quantity <= item.min_quantity,
        created_at=item_doc["created_at"]
    )

@api_router.get("/stock/items", response_model=List[StockItemResponse])
async def get_stock_items(low_stock_only: bool = False, current_user: dict = Depends(get_current_user)):
    query = {}
    if low_stock_only:
        query["$expr"] = {"$lte": ["$quantity", "$min_quantity"]}
    
    items = await db.stock_items.find(query, {"_id": 0}).sort("name", 1).to_list(1000)
    
    return [StockItemResponse(
        id=i["id"],
        name=i["name"],
        code=i.get("code", ""),
        category=i.get("category", ""),
        unit=i.get("unit", "un"),
        quantity=i["quantity"],
        min_quantity=i.get("min_quantity", 0),
        unit_price=i.get("unit_price", 0),
        location=i.get("location", ""),
        notes=i.get("notes", ""),
        is_low_stock=i["quantity"] <= i.get("min_quantity", 0),
        created_at=i["created_at"]
    ) for i in items]

@api_router.get("/stock/items/{item_id}", response_model=StockItemResponse)
async def get_stock_item(item_id: str, current_user: dict = Depends(get_current_user)):
    item = await db.stock_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    return StockItemResponse(
        id=item["id"],
        name=item["name"],
        code=item.get("code", ""),
        category=item.get("category", ""),
        unit=item.get("unit", "un"),
        quantity=item["quantity"],
        min_quantity=item.get("min_quantity", 0),
        unit_price=item.get("unit_price", 0),
        location=item.get("location", ""),
        notes=item.get("notes", ""),
        is_low_stock=item["quantity"] <= item.get("min_quantity", 0),
        created_at=item["created_at"]
    )

@api_router.put("/stock/items/{item_id}", response_model=StockItemResponse)
async def update_stock_item(item_id: str, item: StockItemCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.stock_items.find_one({"id": item_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    update_doc = {
        "name": item.name,
        "code": item.code or "",
        "category": item.category or "",
        "unit": item.unit,
        "min_quantity": item.min_quantity,
        "unit_price": item.unit_price or 0,
        "location": item.location or "",
        "notes": item.notes or ""
    }
    await db.stock_items.update_one({"id": item_id}, {"$set": update_doc})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="item de estoque",
        entity_id=item_id,
        entity_name=item.name
    )
    
    return StockItemResponse(
        id=item_id,
        name=item.name,
        code=item.code or "",
        category=item.category or "",
        unit=item.unit,
        quantity=existing["quantity"],
        min_quantity=item.min_quantity,
        unit_price=item.unit_price or 0,
        location=item.location or "",
        notes=item.notes or "",
        is_low_stock=existing["quantity"] <= item.min_quantity,
        created_at=existing["created_at"]
    )

@api_router.delete("/stock/items/{item_id}")
async def delete_stock_item(item_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.stock_items.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    await db.stock_items.delete_one({"id": item_id})
    # Delete related movements
    await db.stock_movements.delete_many({"item_id": item_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="item de estoque",
        entity_id=item_id,
        entity_name=existing["name"]
    )
    
    return {"message": "Item removido com sucesso"}

@api_router.post("/stock/movements", response_model=StockMovementResponse)
async def create_stock_movement(movement: StockMovementCreate, current_user: dict = Depends(get_current_user)):
    # Check if item exists
    item = await db.stock_items.find_one({"id": movement.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    previous_quantity = item["quantity"]
    
    if movement.movement_type == "entrada":
        new_quantity = previous_quantity + movement.quantity
    elif movement.movement_type == "saida":
        if movement.quantity > previous_quantity:
            raise HTTPException(status_code=400, detail="Quantidade insuficiente em estoque")
        new_quantity = previous_quantity - movement.quantity
    else:
        raise HTTPException(status_code=400, detail="Tipo de movimentação inválido")
    
    # Update item quantity
    await db.stock_items.update_one({"id": movement.item_id}, {"$set": {"quantity": new_quantity}})
    
    # Create movement record
    movement_id = str(uuid.uuid4())
    movement_doc = {
        "id": movement_id,
        "item_id": movement.item_id,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
        "previous_quantity": previous_quantity,
        "new_quantity": new_quantity,
        "reason": movement.reason or "",
        "notes": movement.notes or "",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_movements.insert_one(movement_doc)
    
    # Audit log
    action_type = "entrada" if movement.movement_type == "entrada" else "saída"
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type=f"movimentação de estoque ({action_type})",
        entity_id=movement_id,
        entity_name=f"{item['name']} - {movement.quantity} {item.get('unit', 'un')}"
    )
    
    return StockMovementResponse(
        id=movement_id,
        item_id=movement.item_id,
        item_name=item["name"],
        movement_type=movement.movement_type,
        quantity=movement.quantity,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        reason=movement.reason or "",
        notes=movement.notes or "",
        created_at=movement_doc["created_at"]
    )

@api_router.get("/stock/movements", response_model=List[StockMovementResponse])
async def get_stock_movements(item_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if item_id:
        query["item_id"] = item_id
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get item names
    items = await db.stock_items.find({}, {"_id": 0}).to_list(1000)
    item_map = {i["id"]: i["name"] for i in items}
    
    return [StockMovementResponse(
        id=m["id"],
        item_id=m["item_id"],
        item_name=item_map.get(m["item_id"], ""),
        movement_type=m["movement_type"],
        quantity=m["quantity"],
        previous_quantity=m["previous_quantity"],
        new_quantity=m["new_quantity"],
        reason=m.get("reason", ""),
        notes=m.get("notes", ""),
        created_at=m["created_at"]
    ) for m in movements]

# ============ OBRAS (PROJECTS) ROUTES ============

@api_router.post("/obras", response_model=ObraResponse)
async def create_obra(obra: ObraCreate, current_user: dict = Depends(get_current_user)):
    obra_id = str(uuid.uuid4())
    obra_doc = {
        "id": obra_id,
        "name": obra.name,
        "description": obra.description or "",
        "location": obra.location or "",
        "start_date": obra.start_date,
        "end_date": obra.end_date,
        "status": obra.status,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.obras.insert_one(obra_doc)
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="obra",
        entity_id=obra_id,
        entity_name=obra.name
    )
    
    return ObraResponse(
        id=obra_id,
        name=obra.name,
        description=obra.description or "",
        location=obra.location or "",
        start_date=obra.start_date,
        end_date=obra.end_date,
        status=obra.status,
        machine_count=0,
        total_maintenance_cost=0,
        created_at=obra_doc["created_at"]
    )

@api_router.get("/obras", response_model=List[ObraResponse])
async def get_obras(current_user: dict = Depends(get_current_user)):
    obras = await db.obras.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    result = []
    for obra in obras:
        # Count machines in this obra
        machine_count = await db.machines.count_documents({"obra_id": obra["id"]})
        
        # Get machines to calculate maintenance costs
        machines = await db.machines.find({"obra_id": obra["id"]}, {"_id": 0}).to_list(1000)
        machine_ids = [m["id"] for m in machines]
        
        # Calculate total maintenance cost
        total_cost = 0
        if machine_ids:
            maintenances = await db.maintenances.find({
                "machine_id": {"$in": machine_ids}
            }, {"_id": 0}).to_list(10000)
            total_cost = sum(m["part_value"] for m in maintenances)
        
        result.append(ObraResponse(
            id=obra["id"],
            name=obra["name"],
            description=obra.get("description", ""),
            location=obra.get("location", ""),
            start_date=obra.get("start_date"),
            end_date=obra.get("end_date"),
            status=obra.get("status", "em_andamento"),
            machine_count=machine_count,
            total_maintenance_cost=total_cost,
            created_at=obra["created_at"]
        ))
    
    return result

@api_router.get("/obras/{obra_id}", response_model=ObraDetailResponse)
async def get_obra(obra_id: str, current_user: dict = Depends(get_current_user)):
    obra = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    # Get machines in this obra
    machines_db = await db.machines.find({"obra_id": obra_id}, {"_id": 0}).to_list(1000)
    
    # Get categories for machines
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    machines = [MachineResponse(
        id=m["id"],
        name=m["name"],
        plate=m["plate"],
        category_id=m["category_id"],
        category_name=category_map.get(m["category_id"], ""),
        brand=m.get("brand", ""),
        model=m.get("model", ""),
        year=m.get("year"),
        notes=m.get("notes", ""),
        status=m.get("status", "operational"),
        obra_id=m.get("obra_id"),
        obra_name=obra["name"],
        created_at=m["created_at"]
    ) for m in machines_db]
    
    # Get all maintenances for machines in this obra
    machine_ids = [m["id"] for m in machines_db]
    machine_map = {m["id"]: {"name": m["name"], "plate": m["plate"]} for m in machines_db}
    
    maintenances = []
    total_cost = 0
    preventive_cost = 0
    corrective_cost = 0
    
    if machine_ids:
        maintenances_db = await db.maintenances.find({
            "machine_id": {"$in": machine_ids}
        }, {"_id": 0}).sort("created_at", -1).to_list(10000)
        
        for m in maintenances_db:
            total_cost += m["part_value"]
            if m["maintenance_type"] == "preventiva":
                preventive_cost += m["part_value"]
            else:
                corrective_cost += m["part_value"]
            
            maintenances.append(MaintenanceResponse(
                id=m["id"],
                machine_id=m["machine_id"],
                machine_name=machine_map.get(m["machine_id"], {}).get("name", ""),
                machine_plate=machine_map.get(m["machine_id"], {}).get("plate", ""),
                part_name=m["part_name"],
                replacement_date=m["replacement_date"],
                part_value=m["part_value"],
                maintenance_type=m["maintenance_type"],
                description=m.get("description", ""),
                is_oil_change=m.get("is_oil_change", False),
                photos=m.get("photos", []),
                created_at=m["created_at"]
            ))
    
    return ObraDetailResponse(
        id=obra["id"],
        name=obra["name"],
        description=obra.get("description", ""),
        location=obra.get("location", ""),
        start_date=obra.get("start_date"),
        end_date=obra.get("end_date"),
        status=obra.get("status", "em_andamento"),
        machines=machines,
        maintenances=maintenances,
        total_maintenance_cost=total_cost,
        preventive_cost=preventive_cost,
        corrective_cost=corrective_cost,
        created_at=obra["created_at"]
    )

@api_router.put("/obras/{obra_id}", response_model=ObraResponse)
async def update_obra(obra_id: str, obra: ObraCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.obras.find_one({"id": obra_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    update_doc = {
        "name": obra.name,
        "description": obra.description or "",
        "location": obra.location or "",
        "start_date": obra.start_date,
        "end_date": obra.end_date,
        "status": obra.status
    }
    await db.obras.update_one({"id": obra_id}, {"$set": update_doc})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="obra",
        entity_id=obra_id,
        entity_name=obra.name
    )
    
    # Count machines
    machine_count = await db.machines.count_documents({"obra_id": obra_id})
    
    # Calculate total cost
    machines = await db.machines.find({"obra_id": obra_id}, {"_id": 0}).to_list(1000)
    machine_ids = [m["id"] for m in machines]
    total_cost = 0
    if machine_ids:
        maintenances = await db.maintenances.find({
            "machine_id": {"$in": machine_ids}
        }, {"_id": 0}).to_list(10000)
        total_cost = sum(m["part_value"] for m in maintenances)
    
    return ObraResponse(
        id=obra_id,
        name=obra.name,
        description=obra.description or "",
        location=obra.location or "",
        start_date=obra.start_date,
        end_date=obra.end_date,
        status=obra.status,
        machine_count=machine_count,
        total_maintenance_cost=total_cost,
        created_at=existing["created_at"]
    )

@api_router.delete("/obras/{obra_id}")
async def delete_obra(obra_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    await db.obras.delete_one({"id": obra_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="obra",
        entity_id=obra_id,
        entity_name=existing["name"]
    )
    
    # Remove obra_id from all machines that were in this obra
    await db.machines.update_many(
        {"obra_id": obra_id},
        {"$set": {"obra_id": None}}
    )
    
    return {"message": "Obra removida com sucesso"}


# ============ MEDIÇÕES DE MÁQUINAS (Machine Measurements) ============

class MedicaoCreate(BaseModel):
    obra_id: str
    maquina_id: str
    tipo: str  # 'horimetro', 'km', 'combustivel', 'producao', 'outro'
    valor_anterior: Optional[float] = 0
    valor_atual: float
    unidade: str  # 'horas', 'km', 'litros', 'toneladas', 'm³', 'unidades', etc.
    data_medicao: str
    observacoes: Optional[str] = None

class MedicaoResponse(BaseModel):
    id: str
    obra_id: str
    obra_nome: Optional[str] = None
    maquina_id: str
    maquina_nome: Optional[str] = None
    maquina_placa: Optional[str] = None
    tipo: str
    valor_anterior: float
    valor_atual: float
    diferenca: float
    unidade: str
    data_medicao: str
    observacoes: Optional[str] = None
    registrado_por: Optional[str] = None
    created_at: str

@api_router.post("/medicoes")
async def create_medicao(
    medicao: MedicaoCreate,
    current_user: dict = Depends(get_current_user)
):
    """Registrar nova medição de máquina"""
    # Verify obra exists
    obra = await db.obras.find_one({"id": medicao.obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    # Verify machine exists
    maquina = await db.machines.find_one({"id": medicao.maquina_id}, {"_id": 0})
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    # Calculate difference
    diferenca = medicao.valor_atual - (medicao.valor_anterior or 0)
    
    medicao_doc = {
        "id": str(uuid.uuid4()),
        "obra_id": medicao.obra_id,
        "obra_nome": obra.get("name"),
        "maquina_id": medicao.maquina_id,
        "maquina_nome": maquina.get("name"),
        "maquina_placa": maquina.get("plate"),
        "tipo": medicao.tipo,
        "valor_anterior": medicao.valor_anterior or 0,
        "valor_atual": medicao.valor_atual,
        "diferenca": diferenca,
        "unidade": medicao.unidade,
        "data_medicao": medicao.data_medicao,
        "observacoes": medicao.observacoes,
        "registrado_por": current_user["name"],
        "registrado_por_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.medicoes.insert_one(medicao_doc)
    
    # Update machine's last measurement
    await db.machines.update_one(
        {"id": medicao.maquina_id},
        {"$set": {
            f"ultima_medicao_{medicao.tipo}": medicao.valor_atual,
            f"ultima_medicao_{medicao.tipo}_data": medicao.data_medicao
        }}
    )
    
    await create_audit_log(
        user=current_user,
        action="registrar medição",
        entity_type="medicao",
        entity_id=medicao_doc["id"],
        entity_name=f"{maquina.get('name')} - {medicao.tipo}",
        details=f"Valor: {medicao.valor_atual} {medicao.unidade} (diferença: {diferenca})",
        module="Gerenciamento"
    )
    
    return {"message": "Medição registrada com sucesso", "id": medicao_doc["id"]}

@api_router.get("/medicoes")
async def get_medicoes(
    obra_id: Optional[str] = None,
    maquina_id: Optional[str] = None,
    tipo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Listar medições com filtros"""
    query = {}
    
    if obra_id:
        query["obra_id"] = obra_id
    if maquina_id:
        query["maquina_id"] = maquina_id
    if tipo:
        query["tipo"] = tipo
    if data_inicio:
        query["data_medicao"] = {"$gte": data_inicio}
    if data_fim:
        if "data_medicao" in query:
            query["data_medicao"]["$lte"] = data_fim
        else:
            query["data_medicao"] = {"$lte": data_fim}
    
    medicoes = await db.medicoes.find(query, {"_id": 0}).sort("data_medicao", -1).to_list(500)
    return medicoes

@api_router.get("/medicoes/resumo/{obra_id}")
async def get_medicoes_resumo(
    obra_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resumo de medições por obra (totais por máquina e tipo)"""
    obra = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    medicoes = await db.medicoes.find({"obra_id": obra_id}, {"_id": 0}).to_list(1000)
    
    # Aggregate by machine
    maquinas_resumo = {}
    for m in medicoes:
        maq_id = m["maquina_id"]
        if maq_id not in maquinas_resumo:
            maquinas_resumo[maq_id] = {
                "maquina_id": maq_id,
                "maquina_nome": m.get("maquina_nome", ""),
                "maquina_placa": m.get("maquina_placa", ""),
                "medicoes_por_tipo": {}
            }
        
        tipo = m["tipo"]
        if tipo not in maquinas_resumo[maq_id]["medicoes_por_tipo"]:
            maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo] = {
                "tipo": tipo,
                "unidade": m["unidade"],
                "total_diferenca": 0,
                "valor_inicial": m["valor_anterior"],
                "valor_final": m["valor_atual"],
                "qtd_medicoes": 0
            }
        
        maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo]["total_diferenca"] += m["diferenca"]
        maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo]["valor_final"] = m["valor_atual"]
        maquinas_resumo[maq_id]["medicoes_por_tipo"][tipo]["qtd_medicoes"] += 1
    
    return {
        "obra_id": obra_id,
        "obra_nome": obra.get("name"),
        "total_medicoes": len(medicoes),
        "maquinas": list(maquinas_resumo.values())
    }

@api_router.get("/medicoes/{medicao_id}")
async def get_medicao(
    medicao_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obter uma medição específica"""
    medicao = await db.medicoes.find_one({"id": medicao_id}, {"_id": 0})
    if not medicao:
        raise HTTPException(status_code=404, detail="Medição não encontrada")
    return medicao

@api_router.put("/medicoes/{medicao_id}")
async def update_medicao(
    medicao_id: str,
    medicao: MedicaoCreate,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar medição"""
    existing = await db.medicoes.find_one({"id": medicao_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Medição não encontrada")
    
    diferenca = medicao.valor_atual - (medicao.valor_anterior or 0)
    
    update_doc = {
        "tipo": medicao.tipo,
        "valor_anterior": medicao.valor_anterior or 0,
        "valor_atual": medicao.valor_atual,
        "diferenca": diferenca,
        "unidade": medicao.unidade,
        "data_medicao": medicao.data_medicao,
        "observacoes": medicao.observacoes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.medicoes.update_one({"id": medicao_id}, {"$set": update_doc})
    
    await create_audit_log(
        user=current_user,
        action="atualizar medição",
        entity_type="medicao",
        entity_id=medicao_id,
        entity_name=f"{existing.get('maquina_nome')} - {medicao.tipo}",
        module="Gerenciamento"
    )
    
    return {"message": "Medição atualizada com sucesso"}

@api_router.delete("/medicoes/{medicao_id}")
async def delete_medicao(
    medicao_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Excluir medição"""
    existing = await db.medicoes.find_one({"id": medicao_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Medição não encontrada")
    
    await db.medicoes.delete_one({"id": medicao_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir medição",
        entity_type="medicao",
        entity_id=medicao_id,
        entity_name=f"{existing.get('maquina_nome')} - {existing.get('tipo')}",
        module="Gerenciamento"
    )
    
    return {"message": "Medição excluída com sucesso"}


# ============ AUDIT LOG ROUTES ============

@api_router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if user_id:
        query["user_id"] = user_id
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [AuditLogResponse(
        id=l.get("id", ""),
        user_id=l.get("user_id", ""),
        user_name=l.get("user_name", "Usuário"),
        user_email=l.get("user_email", ""),
        action=l.get("action", ""),
        entity_type=l.get("entity_type", ""),
        entity_id=l.get("entity_id", ""),
        entity_name=l.get("entity_name", ""),
        details=l.get("details", ""),
        created_at=l.get("created_at", "")
    ) for l in logs]

# ============ ROOT ============

@api_router.get("/")
async def root():
    return {"message": "CRA Construtora API"}

# ============ ADMIN MODELS - COMPLETOS ============

# --- Cadastro Unificado de Clientes/Fornecedores ---
class CadastroCreate(BaseModel):
    # Tipo de cadastro
    tipo_cadastro: str = "cliente"  # cliente, fornecedor, cli_forn, transportador, funcionario
    tipo_pessoa: str = "PF"  # PF ou PJ
    status: str = "ativo"  # ativo, inativo
    
    # Dados principais
    nome_razao: str
    apelido_fantasia: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    rg_ie: Optional[str] = None  # RG ou Inscrição Estadual
    
    # Contato
    telefone: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    
    # Endereço
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    
    # Dados adicionais
    grupo: Optional[str] = None
    rota: Optional[str] = None
    vendedor: Optional[str] = None
    limite_credito: Optional[float] = None
    observacoes: Optional[str] = None

class CadastroResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    codigo: int
    tipo_cadastro: str
    tipo_pessoa: str
    status: str
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
    created_at: str

# --- Contas a Pagar (Completo) ---
class ContaPagarCreate(BaseModel):
    # Dados principais
    fornecedor_id: Optional[str] = None
    fornecedor_nome: Optional[str] = None
    documento: Optional[str] = None  # NF/NFS
    numero_doc: Optional[str] = None
    descricao: str
    valor: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    
    # Datas
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_pagamento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    
    # Classificação
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None  # Frota associada
    frota_nome: Optional[str] = None
    
    # Pagamento
    forma_pagamento: str = "dinheiro"  # dinheiro, pix, cartao_debito, cartao_credito, boleto, cheque, transferencia
    conta_movimento: Optional[str] = None
    
    # Status
    status: str = "em_aberto"  # em_aberto, quitada, cancelada, perdida
    
    observacoes: Optional[str] = None

class ContaPagarResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    numero: int
    fornecedor_id: Optional[str] = None
    fornecedor_nome: Optional[str] = None
    documento: Optional[str] = None
    numero_doc: Optional[str] = None
    descricao: str
    valor: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_final: Optional[float] = None
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_pagamento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None
    frota_nome: Optional[str] = None
    forma_pagamento: str
    conta_movimento: Optional[str] = None
    status: str
    observacoes: Optional[str] = None
    created_at: str

# --- Contas a Receber (Completo) ---
class ContaReceberCreate(BaseModel):
    # Dados principais
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    documento: Optional[str] = None  # NF/NFS
    numero_doc: Optional[str] = None
    descricao: str
    valor: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    
    # Datas
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_recebimento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    
    # Classificação
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None  # Frota associada
    frota_nome: Optional[str] = None
    
    # Pagamento
    forma_pagamento: str = "dinheiro"
    conta_movimento: Optional[str] = None
    
    # Status
    status: str = "em_aberto"  # em_aberto, quitada, cancelada, perdida
    
    # Faturamento
    faturamento: Optional[str] = None
    
    observacoes: Optional[str] = None

class ContaReceberResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    numero: int
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    documento: Optional[str] = None
    numero_doc: Optional[str] = None
    descricao: str
    valor: float
    valor_desconto: Optional[float] = 0
    valor_juros: Optional[float] = 0
    valor_multa: Optional[float] = 0
    valor_final: Optional[float] = None
    data_emissao: Optional[str] = None
    data_vencimento: str
    data_recebimento: Optional[str] = None
    data_cancelamento: Optional[str] = None
    plano_conta_id: Optional[str] = None
    plano_conta_nome: Optional[str] = None
    centro_custo: Optional[str] = None
    frota_id: Optional[str] = None
    frota_nome: Optional[str] = None
    forma_pagamento: str
    conta_movimento: Optional[str] = None
    status: str
    faturamento: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: str

# --- Produtos (Completo com dados fiscais) ---
class ProdutoCreate(BaseModel):
    # Identificação
    codigo_interno: Optional[str] = None
    codigo_fabricante: Optional[str] = None
    codigo_barras: Optional[str] = None
    descricao: str
    
    # Classificação
    fabricante: Optional[str] = None
    aplicacao: Optional[str] = None
    grupo: Optional[str] = None
    subgrupo: Optional[str] = None
    
    # Unidades
    unidade_comercial: str = "UN"
    unidade_tributada: Optional[str] = None
    multiplo: Optional[float] = 1
    
    # Preços
    preco_custo: Optional[float] = 0
    preco_custo_final: Optional[float] = 0
    preco_venda: Optional[float] = 0
    margem_lucro: Optional[float] = 0
    
    # Estoque
    estoque_atual: Optional[float] = 0
    estoque_minimo: Optional[float] = 0
    estoque_maximo: Optional[float] = 0
    localizacao: Optional[str] = None  # Prateleira
    
    # Dados fiscais
    ncm: Optional[str] = None
    cst: Optional[str] = None
    cest: Optional[str] = None
    origem: Optional[str] = "0"  # 0 = Nacional
    ipi: Optional[float] = 0
    icms: Optional[float] = 0
    pis: Optional[float] = 0
    cofins: Optional[float] = 0
    
    # Tipo do item (NF-e)
    tipo_item: Optional[str] = "00"  # 00=Mercadoria, 01=Matéria-prima, etc
    
    # Status
    status: str = "ativo"
    em_promocao: bool = False
    preco_promocao: Optional[float] = None
    
    observacoes: Optional[str] = None

class ProdutoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    codigo_interno: Optional[str] = None
    codigo_fabricante: Optional[str] = None
    codigo_barras: Optional[str] = None
    descricao: str
    fabricante: Optional[str] = None
    aplicacao: Optional[str] = None
    grupo: Optional[str] = None
    subgrupo: Optional[str] = None
    unidade_comercial: str
    unidade_tributada: Optional[str] = None
    multiplo: Optional[float] = 1
    preco_custo: Optional[float] = 0
    preco_custo_final: Optional[float] = 0
    preco_venda: Optional[float] = 0
    margem_lucro: Optional[float] = 0
    estoque_atual: Optional[float] = 0
    estoque_minimo: Optional[float] = 0
    estoque_maximo: Optional[float] = 0
    localizacao: Optional[str] = None
    ncm: Optional[str] = None
    cst: Optional[str] = None
    cest: Optional[str] = None
    origem: Optional[str] = "0"
    ipi: Optional[float] = 0
    icms: Optional[float] = 0
    pis: Optional[float] = 0
    cofins: Optional[float] = 0
    tipo_item: Optional[str] = "00"
    status: str
    em_promocao: bool = False
    preco_promocao: Optional[float] = None
    observacoes: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# --- Ordem de Serviço (Completo) ---
class OrdemServicoCreate(BaseModel):
    # Identificação
    numero_contrato: Optional[str] = None
    
    # Cliente
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    cliente_fantasia: Optional[str] = None
    
    # Obra/Projeto
    obra: Optional[str] = None
    prisma: Optional[str] = None
    
    # Datas
    data_abertura: Optional[str] = None
    data_previsao_entrega: Optional[str] = None
    data_conclusao: Optional[str] = None
    
    # Atendimento
    tipo_atendimento: Optional[str] = None
    atendente: Optional[str] = None
    empresa: Optional[str] = None
    
    # Valores
    valor_total: Optional[float] = 0
    valor_antecipado: Optional[float] = 0
    
    # Status
    status: str = "em_aberto"  # em_aberto, em_andamento, concluida, cancelada
    confirmada: bool = False
    
    # Tipo Financeiro (novo campo para refletir no dashboard)
    tipo_financeiro: Optional[str] = None  # a_pagar, a_receber, nenhum
    
    # Descrição
    descricao: Optional[str] = None
    observacoes: Optional[str] = None

class OrdemServicoItemCreate(BaseModel):
    produto_id: Optional[str] = None
    codigo_interno: Optional[str] = None
    descricao: str
    fabricante: Optional[str] = None
    unidade: str = "UN"
    quantidade: float = 1
    valor_unitario: float = 0
    desconto_percent: Optional[float] = 0
    valor_total: Optional[float] = 0

class OrdemServicoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    numero: int
    numero_contrato: Optional[str] = None
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    cliente_fantasia: Optional[str] = None
    obra: Optional[str] = None
    prisma: Optional[str] = None
    data_abertura: str
    data_previsao_entrega: Optional[str] = None
    data_conclusao: Optional[str] = None
    tipo_atendimento: Optional[str] = None
    atendente: Optional[str] = None
    empresa: Optional[str] = None
    valor_total: Optional[float] = 0
    valor_antecipado: Optional[float] = 0
    valor_restante: Optional[float] = 0
    status: str
    confirmada: bool = False
    tipo_financeiro: Optional[str] = None  # a_pagar, a_receber, nenhum
    descricao: Optional[str] = None
    observacoes: Optional[str] = None
    itens: Optional[List[dict]] = []
    created_at: str

# --- Plano de Contas (2 níveis) ---
class PlanoContaCreate(BaseModel):
    codigo: Optional[str] = None
    nome: str
    tipo: str  # receita ou despesa
    nivel: int = 1  # 1 = categoria pai, 2 = subcategoria
    pai_id: Optional[str] = None  # ID da categoria pai se for nível 2
    descricao: Optional[str] = None

class PlanoContaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    codigo: Optional[str] = None
    nome: str
    tipo: str
    nivel: int
    pai_id: Optional[str] = None
    pai_nome: Optional[str] = None
    descricao: Optional[str] = None
    created_at: str

# --- Centro de Custo ---
class CentroCustoCreate(BaseModel):
    codigo: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    status: str = "ativo"

class CentroCustoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    codigo: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    status: str
    created_at: str

# --- Formas de Pagamento ---
class FormaPagamentoCreate(BaseModel):
    codigo: Optional[str] = None
    nome: str
    tipo: str = "outros"  # dinheiro, pix, cartao_debito, cartao_credito, boleto, cheque, transferencia, outros
    taxa: Optional[float] = 0
    prazo_recebimento: Optional[int] = 0  # dias
    conta_bancaria: Optional[str] = None
    ativo: bool = True
    observacoes: Optional[str] = None

class FormaPagamentoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    codigo: Optional[str] = None
    nome: str
    tipo: str
    taxa: Optional[float] = 0
    prazo_recebimento: Optional[int] = 0
    conta_bancaria: Optional[str] = None
    ativo: bool
    observacoes: Optional[str] = None
    created_at: str

# --- Contas Bancárias ---
class ContaBancariaCreate(BaseModel):
    nome: str  # Nome identificador da conta (ex: "Conta Principal", "Conta Poupança")
    banco: str  # Nome do banco
    codigo_banco: Optional[str] = None  # Código do banco (ex: 001, 341)
    agencia: str
    agencia_digito: Optional[str] = None
    conta: str
    conta_digito: Optional[str] = None
    tipo_conta: str = "corrente"  # corrente, poupanca, investimento, caixa
    titular: Optional[str] = None
    cpf_cnpj_titular: Optional[str] = None
    chave_pix: Optional[str] = None
    tipo_chave_pix: Optional[str] = None  # cpf, cnpj, email, telefone, aleatoria
    saldo_inicial: Optional[float] = 0
    saldo_atual: Optional[float] = 0
    ativo: bool = True
    cor: Optional[str] = "#3B82F6"  # Cor para identificação visual
    observacoes: Optional[str] = None

class ContaBancariaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nome: str
    banco: str
    codigo_banco: Optional[str] = None
    agencia: str
    agencia_digito: Optional[str] = None
    conta: str
    conta_digito: Optional[str] = None
    tipo_conta: str
    titular: Optional[str] = None
    cpf_cnpj_titular: Optional[str] = None
    chave_pix: Optional[str] = None
    tipo_chave_pix: Optional[str] = None
    saldo_inicial: Optional[float] = 0
    saldo_atual: Optional[float] = 0
    ativo: bool
    cor: Optional[str] = "#3B82F6"
    observacoes: Optional[str] = None
    created_at: str

# --- Aluguéis de Máquinas ---
class AluguelCreate(BaseModel):
    # Máquina
    maquina_id: str
    maquina_nome: Optional[str] = None
    maquina_placa: Optional[str] = None
    
    # Cliente/Locatário
    cliente_nome: str
    cliente_telefone: Optional[str] = None
    cliente_documento: Optional[str] = None  # CPF/CNPJ
    
    # Contrato
    numero_contrato: Optional[str] = None
    
    # Período
    tipo_periodo: str  # diaria, semanal, quinzenal, mensal, semestral, anual, hora, outro
    periodo_especificado: Optional[str] = None  # quando tipo_periodo = outro
    
    # Datas
    data_entrega: str  # data que a máquina foi entregue
    data_vencimento: str  # data que deve ser devolvida/paga
    data_devolucao: Optional[str] = None  # data real de devolução
    
    # Valores
    valor: float
    valor_caucao: Optional[float] = 0  # valor de caução/garantia
    
    # Local
    local_entrega: Optional[str] = None
    
    # Status e observações
    status: str = "ativo"  # ativo, finalizado, cancelado
    observacoes: Optional[str] = None
    
    # Gerar conta a receber
    gerar_conta_receber: bool = True

class AluguelResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    numero: int
    maquina_id: str
    maquina_nome: Optional[str] = None
    maquina_placa: Optional[str] = None
    cliente_nome: str
    cliente_telefone: Optional[str] = None
    cliente_documento: Optional[str] = None
    tipo_periodo: str
    periodo_especificado: Optional[str] = None
    data_entrega: str
    data_vencimento: str
    data_devolucao: Optional[str] = None
    valor: float
    valor_caucao: Optional[float] = 0
    local_entrega: Optional[str] = None
    status: str
    observacoes: Optional[str] = None
    conta_receber_id: Optional[str] = None
    created_at: str

# --- Configurações do Sistema ---
class ConfiguracaoNotificacao(BaseModel):
    prazo_dias: int = 7  # dias antes do vencimento para notificar

# ============ ADMIN ENDPOINTS ============

# --- Funções auxiliares para auto-incremento ---
async def get_next_sequence(collection_name: str) -> int:
    result = await db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return result["seq"]

# --- Dashboard Admin ---
@api_router.get("/admin/dashboard")
async def get_admin_dashboard(current_user: dict = Depends(get_current_user)):
    from datetime import timedelta
    hoje = datetime.now(timezone.utc)
    hoje_str = hoje.strftime("%Y-%m-%d")
    inicio_mes = hoje.replace(day=1).strftime("%Y-%m-%d")
    inicio_ano = hoje.replace(month=1, day=1).strftime("%Y-%m-%d")
    proxima_semana = (hoje + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # ===== CONTAS A PAGAR =====
    # Em aberto
    contas_pagar_abertas = await db.contas_pagar.find({"status": "em_aberto"}, {"_id": 0}).to_list(5000)
    total_pagar_aberto = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_pagar_abertas)
    total_pagar_mes = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_pagar_abertas if c.get("data_vencimento", "") >= inicio_mes)
    total_pagar_ano = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_pagar_abertas if c.get("data_vencimento", "") >= inicio_ano)
    lista_pagar_vencidas = [c for c in contas_pagar_abertas if c.get("data_vencimento", "") < hoje_str]
    contas_pagar_vencidas = len(lista_pagar_vencidas)
    total_pagar_vencidas_valor = sum(c.get("valor_final") or c.get("valor", 0) for c in lista_pagar_vencidas)
    
    # Quitadas
    contas_pagar_quitadas = await db.contas_pagar.find({"status": "quitada"}, {"_id": 0}).to_list(5000)
    total_pagar_quitado = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_pagar_quitadas)
    total_pagar_quitado_mes = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_pagar_quitadas if c.get("data_pagamento", c.get("data_vencimento", "")) >= inicio_mes)
    total_pagar_quitado_ano = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_pagar_quitadas if c.get("data_pagamento", c.get("data_vencimento", "")) >= inicio_ano)
    
    # ===== CONTAS A RECEBER =====
    # Em aberto
    contas_receber_abertas = await db.contas_receber.find({"status": "em_aberto"}, {"_id": 0}).to_list(5000)
    total_receber_aberto = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_receber_abertas)
    total_receber_mes = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_receber_abertas if c.get("data_vencimento", "") >= inicio_mes)
    total_receber_ano = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_receber_abertas if c.get("data_vencimento", "") >= inicio_ano)
    lista_receber_vencidas = [c for c in contas_receber_abertas if c.get("data_vencimento", "") < hoje_str]
    contas_receber_vencidas = len(lista_receber_vencidas)
    total_receber_vencidas_valor = sum(c.get("valor_final") or c.get("valor", 0) for c in lista_receber_vencidas)
    
    # Quitadas/Recebidas
    contas_receber_quitadas = await db.contas_receber.find({"status": "quitada"}, {"_id": 0}).to_list(5000)
    total_receber_quitado = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_receber_quitadas)
    total_receber_quitado_mes = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_receber_quitadas if c.get("data_recebimento", c.get("data_vencimento", "")) >= inicio_mes)
    total_receber_quitado_ano = sum(c.get("valor_final") or c.get("valor", 0) for c in contas_receber_quitadas if c.get("data_recebimento", c.get("data_vencimento", "")) >= inicio_ano)
    
    # ===== ORDENS DE SERVIÇO COM TIPO FINANCEIRO =====
    os_a_pagar = await db.ordens_servico.find({"tipo_financeiro": "a_pagar", "status": {"$ne": "cancelada"}}, {"_id": 0}).to_list(1000)
    os_a_receber = await db.ordens_servico.find({"tipo_financeiro": "a_receber", "status": {"$ne": "cancelada"}}, {"_id": 0}).to_list(1000)
    total_os_pagar = sum(o.get("valor_total", 0) for o in os_a_pagar)
    total_os_receber = sum(o.get("valor_total", 0) for o in os_a_receber)
    
    # ===== COUNTS =====
    cadastros = await db.cadastros.count_documents({})
    fornecedores = await db.cadastros.count_documents({"tipo_cadastro": {"$in": ["fornecedor", "ambos"]}})
    produtos = await db.produtos_admin.count_documents({})
    ordens_abertas = await db.ordens_servico.count_documents({"status": {"$in": ["em_aberto", "em_andamento"]}})
    notas_emitidas = await db.notas_fiscais.count_documents({}) if await db.list_collection_names() else 0
    
    # ===== PRÓXIMOS VENCIMENTOS =====
    proximas_pagar = await db.contas_pagar.find({
        "status": "em_aberto",
        "data_vencimento": {"$lte": proxima_semana}
    }, {"_id": 0}).sort("data_vencimento", 1).limit(5).to_list(5)
    
    proximas_receber = await db.contas_receber.find({
        "status": "em_aberto",
        "data_vencimento": {"$lte": proxima_semana}
    }, {"_id": 0}).sort("data_vencimento", 1).limit(5).to_list(5)
    
    contas_proximas = []
    for c in proximas_pagar:
        contas_proximas.append({
            "tipo": "pagar",
            "descricao": c.get("descricao"),
            "valor": c.get("valor_final") or c.get("valor"),
            "vencimento": c.get("data_vencimento")
        })
    for c in proximas_receber:
        contas_proximas.append({
            "tipo": "receber",
            "descricao": c.get("descricao"),
            "valor": c.get("valor_final") or c.get("valor"),
            "vencimento": c.get("data_vencimento")
        })
    
    contas_proximas.sort(key=lambda x: x.get("vencimento", ""))
    
    # Saldo previsto = (receber aberto + OS receber) - (pagar aberto + OS pagar)
    saldo_previsto = (total_receber_aberto + total_os_receber) - (total_pagar_aberto + total_os_pagar)
    
    return {
        "stats": {
            "totalPagar": total_pagar_aberto,
            "totalReceber": total_receber_aberto,
            "saldoPrevisto": saldo_previsto,
            "contasVencidas": contas_pagar_vencidas + contas_receber_vencidas,
            "contasPagarVencidas": contas_pagar_vencidas,
            "contasReceberVencidas": contas_receber_vencidas,
            "notasEmitidas": 0,
            "fornecedores": fornecedores,
            "cadastros": cadastros,
            "produtos": produtos,
            "ordensAbertas": ordens_abertas
        },
        "aPagar": {
            "total": total_pagar_aberto,
            "mes": total_pagar_mes,
            "ano": total_pagar_ano,
            "vencidas": contas_pagar_vencidas,
            "osValor": total_os_pagar
        },
        "aReceber": {
            "total": total_receber_aberto,
            "mes": total_receber_mes,
            "ano": total_receber_ano,
            "vencidas": contas_receber_vencidas,
            "osValor": total_os_receber
        },
        "quitados": {
            "pagar": {
                "total": total_pagar_quitado,
                "mes": total_pagar_quitado_mes,
                "ano": total_pagar_quitado_ano
            },
            "receber": {
                "total": total_receber_quitado,
                "mes": total_receber_quitado_mes,
                "ano": total_receber_quitado_ano
            }
        },
        "contasProximas": contas_proximas[:10],
        "vencidas": {
            "pagar": {
                "quantidade": contas_pagar_vencidas,
                "valor": total_pagar_vencidas_valor,
                "lista": sorted(lista_pagar_vencidas, key=lambda x: x.get("data_vencimento", ""))[:50]
            },
            "receber": {
                "quantidade": contas_receber_vencidas,
                "valor": total_receber_vencidas_valor,
                "lista": sorted(lista_receber_vencidas, key=lambda x: x.get("data_vencimento", ""))[:50]
            },
            "totalQuantidade": contas_pagar_vencidas + contas_receber_vencidas,
            "totalValor": total_pagar_vencidas_valor + total_receber_vencidas_valor
        }
    }

# --- Consulta de CNPJ via BrasilAPI (Receita Federal) ---
import httpx

@api_router.get("/consulta/cnpj/{cnpj}")
async def consulta_cnpj(
    cnpj: str,
    current_user: dict = Depends(get_current_user)
):
    """Consulta dados de empresa via CNPJ usando BrasilAPI (dados da Receita Federal)"""
    
    # Remove caracteres não numéricos
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
    
    if len(cnpj_limpo) != 14:
        raise HTTPException(status_code=400, detail="CNPJ inválido. Deve conter 14 dígitos.")
    
    try:
        async with httpx.AsyncClient() as client:
            # Tentar BrasilAPI primeiro (mais confiável)
            response = await client.get(
                f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Mapear dados da BrasilAPI
                resultado = {
                    "razao_social": data.get("razao_social", ""),
                    "nome_fantasia": data.get("nome_fantasia", ""),
                    "cnpj": cnpj_limpo,
                    "inscricao_estadual": "",  # BrasilAPI não retorna IE
                    "telefone": data.get("ddd_telefone_1", ""),
                    "email": data.get("email", ""),
                    "cep": data.get("cep", ""),
                    "endereco": data.get("logradouro", ""),
                    "numero": data.get("numero", ""),
                    "complemento": data.get("complemento", ""),
                    "bairro": data.get("bairro", ""),
                    "cidade": data.get("municipio", ""),
                    "uf": data.get("uf", ""),
                    "situacao": data.get("descricao_situacao_cadastral", ""),
                    "atividade_principal": data.get("cnae_fiscal_descricao", ""),
                    "capital_social": str(data.get("capital_social", "")) if data.get("capital_social") else "",
                    "data_abertura": data.get("data_inicio_atividade", ""),
                    "natureza_juridica": data.get("natureza_juridica", ""),
                    "porte": data.get("porte", ""),
                }
                
                await create_audit_log(
                    user=current_user,
                    action="consultar cnpj",
                    entity_type="cnpj",
                    entity_id=cnpj_limpo,
                    entity_name=resultado.get("razao_social", cnpj_limpo),
                    module="Administrativo"
                )
                
                return {"success": True, "data": resultado}
            
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="CNPJ não encontrado na base da Receita Federal")
            else:
                raise HTTPException(status_code=500, detail="Erro ao consultar CNPJ")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Tempo de consulta excedido. Tente novamente.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar CNPJ: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar CNPJ: {str(e)}")

@api_router.get("/consulta/cep/{cep}")
async def consulta_cep(
    cep: str,
    current_user: dict = Depends(get_current_user)
):
    """Consulta endereço via CEP usando ViaCEP"""
    
    # Remove caracteres não numéricos
    cep_limpo = ''.join(filter(str.isdigit, cep))
    
    if len(cep_limpo) != 8:
        raise HTTPException(status_code=400, detail="CEP inválido. Deve conter 8 dígitos.")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=10)
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="CEP não encontrado")
            
            data = response.json()
            
            if data.get("erro"):
                raise HTTPException(status_code=404, detail="CEP não encontrado")
            
            resultado = {
                "cep": data.get("cep", "").replace("-", ""),
                "endereco": data.get("logradouro", ""),
                "complemento": data.get("complemento", ""),
                "bairro": data.get("bairro", ""),
                "cidade": data.get("localidade", ""),
                "uf": data.get("uf", ""),
                "ibge": data.get("ibge", ""),
                "ddd": data.get("ddd", "")
            }
            
            return {"success": True, "data": resultado}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar CEP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar CEP: {str(e)}")

# --- Cadastro de Clientes/Fornecedores ---
@api_router.get("/admin/cadastros")
async def get_cadastros(
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if tipo:
        query["tipo_cadastro"] = tipo
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"nome_razao": {"$regex": search, "$options": "i"}},
            {"apelido_fantasia": {"$regex": search, "$options": "i"}},
            {"cpf_cnpj": {"$regex": search, "$options": "i"}},
            {"cidade": {"$regex": search, "$options": "i"}}
        ]
    
    cadastros = await db.cadastros.find(query, {"_id": 0}).sort("nome_razao", 1).to_list(1000)
    return cadastros

@api_router.post("/admin/cadastros")
async def create_cadastro(data: CadastroCreate, current_user: dict = Depends(get_current_user)):
    codigo = await get_next_sequence("cadastros")
    cadastro = {
        "id": str(uuid.uuid4()),
        "codigo": codigo,
        **data.model_dump(),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.cadastros.insert_one(cadastro)
    await create_audit_log(current_user, "create", "cadastro", cadastro["id"], data.nome_razao)
    del cadastro["_id"]
    return cadastro

@api_router.get("/admin/cadastros/{id}")
async def get_cadastro(id: str, current_user: dict = Depends(get_current_user)):
    cadastro = await db.cadastros.find_one({"id": id}, {"_id": 0})
    if not cadastro:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    return cadastro

@api_router.put("/admin/cadastros/{id}")
async def update_cadastro(id: str, data: CadastroCreate, current_user: dict = Depends(get_current_user)):
    cadastro = await db.cadastros.find_one({"id": id}, {"_id": 0})
    if not cadastro:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.cadastros.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "cadastro", id, data.nome_razao)
    
    updated = await db.cadastros.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/cadastros/{id}")
async def delete_cadastro(id: str, current_user: dict = Depends(get_current_user)):
    cadastro = await db.cadastros.find_one({"id": id}, {"_id": 0})
    if not cadastro:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    
    await db.cadastros.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "cadastro", id, cadastro["nome_razao"])
    return {"message": "Cadastro excluído"}

# --- Anexos de Cadastros ---
CADASTROS_ANEXOS_DIR = ROOT_DIR / "uploads" / "cadastros"
CADASTROS_ANEXOS_DIR.mkdir(parents=True, exist_ok=True)

@api_router.post("/admin/cadastros/{id}/anexos")
async def upload_cadastro_anexo(
    id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload anexo para cadastro"""
    cadastro = await db.cadastros.find_one({"id": id}, {"_id": 0})
    if not cadastro:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    
    content = await file.read()
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 50MB")
    
    ext = Path(file.filename).suffix.lower() if file.filename else ''
    unique_filename = f"{id}_{uuid.uuid4()}{ext}"
    file_path = CADASTROS_ANEXOS_DIR / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    anexo = {
        "id": str(uuid.uuid4()),
        "filename": unique_filename,
        "original_name": file.filename,
        "size": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cadastros.update_one({"id": id}, {"$push": {"anexos": anexo}})
    await create_audit_log(current_user, "upload anexo", "cadastro", id, f"{cadastro['nome_razao']} - {file.filename}")
    
    return {"message": "Anexo adicionado", "anexo": anexo}

@api_router.delete("/admin/cadastros/{id}/anexos/{anexo_id}")
async def delete_cadastro_anexo(
    id: str,
    anexo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Excluir anexo de cadastro"""
    cadastro = await db.cadastros.find_one({"id": id}, {"_id": 0})
    if not cadastro:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    
    anexo = next((a for a in cadastro.get("anexos", []) if a["id"] == anexo_id), None)
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    file_path = CADASTROS_ANEXOS_DIR / anexo["filename"]
    if file_path.exists():
        file_path.unlink()
    
    await db.cadastros.update_one({"id": id}, {"$pull": {"anexos": {"id": anexo_id}}})
    await create_audit_log(current_user, "excluir anexo", "cadastro", id, cadastro["nome_razao"])
    
    return {"message": "Anexo excluído"}

@api_router.get("/admin/cadastros/{id}/anexos/{anexo_id}/download")
async def download_cadastro_anexo(
    id: str,
    anexo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download de anexo"""
    cadastro = await db.cadastros.find_one({"id": id}, {"_id": 0})
    if not cadastro:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado")
    
    anexo = next((a for a in cadastro.get("anexos", []) if a["id"] == anexo_id), None)
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    file_path = CADASTROS_ANEXOS_DIR / anexo["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=str(file_path),
        filename=anexo.get("original_name", anexo["filename"]),
        media_type="application/octet-stream"
    )

# --- Contas a Pagar (Completo) ---
@api_router.get("/admin/contas-pagar")
async def get_contas_pagar(
    status: Optional[str] = None,
    vencimento: Optional[str] = None,
    forma_pagamento: Optional[str] = None,
    plano_conta_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if forma_pagamento:
        query["forma_pagamento"] = forma_pagamento
    if plano_conta_id:
        query["plano_conta_id"] = plano_conta_id
    if search:
        query["$or"] = [
            {"descricao": {"$regex": search, "$options": "i"}},
            {"fornecedor_nome": {"$regex": search, "$options": "i"}},
            {"documento": {"$regex": search, "$options": "i"}}
        ]
    
    # Filtro de vencimento
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if vencimento == "vencidas":
        query["data_vencimento"] = {"$lt": hoje}
        query["status"] = "em_aberto"
    elif vencimento == "hoje":
        query["data_vencimento"] = hoje
    elif vencimento == "a_vencer":
        query["data_vencimento"] = {"$gt": hoje}
        query["status"] = "em_aberto"
    
    # Filtro de período
    if data_inicio and data_fim:
        query["data_vencimento"] = {"$gte": data_inicio, "$lte": data_fim}
    
    contas = await db.contas_pagar.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(1000)
    
    # Calcular valor final
    for conta in contas:
        valor = conta.get("valor", 0)
        desconto = conta.get("valor_desconto", 0)
        juros = conta.get("valor_juros", 0)
        multa = conta.get("valor_multa", 0)
        conta["valor_final"] = valor - desconto + juros + multa
    
    return contas

@api_router.post("/admin/contas-pagar")
async def create_conta_pagar(data: ContaPagarCreate, current_user: dict = Depends(get_current_user)):
    numero = await get_next_sequence("contas_pagar")
    valor_final = data.valor - (data.valor_desconto or 0) + (data.valor_juros or 0) + (data.valor_multa or 0)
    
    conta = {
        "id": str(uuid.uuid4()),
        "numero": numero,
        **data.model_dump(),
        "valor_final": valor_final,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contas_pagar.insert_one(conta)
    await create_audit_log(current_user, "create", "conta_pagar", conta["id"], data.descricao)
    del conta["_id"]
    return conta

@api_router.put("/admin/contas-pagar/{id}")
async def update_conta_pagar(id: str, data: ContaPagarCreate, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    valor_final = data.valor - (data.valor_desconto or 0) + (data.valor_juros or 0) + (data.valor_multa or 0)
    update_data = data.model_dump()
    update_data["valor_final"] = valor_final
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.contas_pagar.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "conta_pagar", id, data.descricao)
    
    updated = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.patch("/admin/contas-pagar/{id}/quitar")
async def quitar_conta_pagar(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_pagar.update_one({"id": id}, {
        "$set": {
            "status": "quitada",
            "data_pagamento": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }
    })
    await create_audit_log(current_user, "update", "conta_pagar", id, f"{conta['descricao']} - QUITADA")
    return {"message": "Conta quitada com sucesso"}

@api_router.patch("/admin/contas-pagar/{id}/cancelar")
async def cancelar_conta_pagar(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_pagar.update_one({"id": id}, {
        "$set": {
            "status": "cancelada",
            "data_cancelamento": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }
    })
    await create_audit_log(current_user, "update", "conta_pagar", id, f"{conta['descricao']} - CANCELADA")
    return {"message": "Conta cancelada"}

@api_router.delete("/admin/contas-pagar/{id}")
async def delete_conta_pagar(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_pagar.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_pagar.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "conta_pagar", id, conta["descricao"])
    return {"message": "Conta excluída"}

# --- Contas a Receber (Completo) ---
@api_router.get("/admin/contas-receber")
async def get_contas_receber(
    status: Optional[str] = None,
    vencimento: Optional[str] = None,
    forma_pagamento: Optional[str] = None,
    plano_conta_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if forma_pagamento:
        query["forma_pagamento"] = forma_pagamento
    if plano_conta_id:
        query["plano_conta_id"] = plano_conta_id
    if search:
        query["$or"] = [
            {"descricao": {"$regex": search, "$options": "i"}},
            {"cliente_nome": {"$regex": search, "$options": "i"}},
            {"documento": {"$regex": search, "$options": "i"}}
        ]
    
    # Filtro de vencimento
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if vencimento == "vencidas":
        query["data_vencimento"] = {"$lt": hoje}
        query["status"] = "em_aberto"
    elif vencimento == "hoje":
        query["data_vencimento"] = hoje
    elif vencimento == "a_vencer":
        query["data_vencimento"] = {"$gt": hoje}
        query["status"] = "em_aberto"
    
    # Filtro de período
    if data_inicio and data_fim:
        query["data_vencimento"] = {"$gte": data_inicio, "$lte": data_fim}
    
    contas = await db.contas_receber.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(1000)
    
    # Calcular valor final
    for conta in contas:
        valor = conta.get("valor", 0)
        desconto = conta.get("valor_desconto", 0)
        juros = conta.get("valor_juros", 0)
        multa = conta.get("valor_multa", 0)
        conta["valor_final"] = valor - desconto + juros + multa
    
    return contas

@api_router.post("/admin/contas-receber")
async def create_conta_receber(data: ContaReceberCreate, current_user: dict = Depends(get_current_user)):
    numero = await get_next_sequence("contas_receber")
    valor_final = data.valor - (data.valor_desconto or 0) + (data.valor_juros or 0) + (data.valor_multa or 0)
    
    conta = {
        "id": str(uuid.uuid4()),
        "numero": numero,
        **data.model_dump(),
        "valor_final": valor_final,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contas_receber.insert_one(conta)
    await create_audit_log(current_user, "create", "conta_receber", conta["id"], data.descricao)
    del conta["_id"]
    return conta

@api_router.put("/admin/contas-receber/{id}")
async def update_conta_receber(id: str, data: ContaReceberCreate, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    valor_final = data.valor - (data.valor_desconto or 0) + (data.valor_juros or 0) + (data.valor_multa or 0)
    update_data = data.model_dump()
    update_data["valor_final"] = valor_final
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.contas_receber.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "conta_receber", id, data.descricao)
    
    updated = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.patch("/admin/contas-receber/{id}/quitar")
async def quitar_conta_receber(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_receber.update_one({"id": id}, {
        "$set": {
            "status": "quitada",
            "data_recebimento": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }
    })
    await create_audit_log(current_user, "update", "conta_receber", id, f"{conta['descricao']} - QUITADA")
    return {"message": "Conta quitada com sucesso"}

@api_router.patch("/admin/contas-receber/{id}/cancelar")
async def cancelar_conta_receber(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_receber.update_one({"id": id}, {
        "$set": {
            "status": "cancelada",
            "data_cancelamento": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }
    })
    await create_audit_log(current_user, "update", "conta_receber", id, f"{conta['descricao']} - CANCELADA")
    return {"message": "Conta cancelada"}

@api_router.delete("/admin/contas-receber/{id}")
async def delete_conta_receber(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_receber.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await db.contas_receber.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "conta_receber", id, conta["descricao"])
    return {"message": "Conta excluída"}

# --- Produtos (Completo com dados fiscais) ---
@api_router.get("/admin/produtos")
async def get_produtos(
    grupo: Optional[str] = None,
    subgrupo: Optional[str] = None,
    fabricante: Optional[str] = None,
    status: Optional[str] = None,
    estoque_baixo: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if grupo:
        query["grupo"] = grupo
    if subgrupo:
        query["subgrupo"] = subgrupo
    if fabricante:
        query["fabricante"] = fabricante
    if status:
        query["status"] = status
    if estoque_baixo:
        query["$expr"] = {"$lte": ["$estoque_atual", "$estoque_minimo"]}
    if search:
        query["$or"] = [
            {"descricao": {"$regex": search, "$options": "i"}},
            {"codigo_interno": {"$regex": search, "$options": "i"}},
            {"codigo_fabricante": {"$regex": search, "$options": "i"}},
            {"fabricante": {"$regex": search, "$options": "i"}},
            {"aplicacao": {"$regex": search, "$options": "i"}}
        ]
    
    produtos = await db.produtos_admin.find(query, {"_id": 0}).sort("descricao", 1).to_list(1000)
    return produtos

@api_router.post("/admin/produtos")
async def create_produto(data: ProdutoCreate, current_user: dict = Depends(get_current_user)):
    # Gerar código interno se não fornecido
    codigo_interno = data.codigo_interno
    if not codigo_interno:
        seq = await get_next_sequence("produtos")
        codigo_interno = f"P{seq:06d}"
    
    # Calcular margem de lucro
    margem = 0
    if data.preco_custo and data.preco_custo > 0 and data.preco_venda:
        margem = ((data.preco_venda - data.preco_custo) / data.preco_custo) * 100
    
    produto = {
        "id": str(uuid.uuid4()),
        "codigo_interno": codigo_interno,
        **data.model_dump(exclude={"codigo_interno", "margem_lucro"}),
        "margem_lucro": round(margem, 2),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.produtos_admin.insert_one(produto)
    await create_audit_log(current_user, "create", "produto", produto["id"], data.descricao)
    del produto["_id"]
    return produto

@api_router.get("/admin/produtos/{id}")
async def get_produto(id: str, current_user: dict = Depends(get_current_user)):
    produto = await db.produtos_admin.find_one({"id": id}, {"_id": 0})
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@api_router.put("/admin/produtos/{id}")
async def update_produto(id: str, data: ProdutoCreate, current_user: dict = Depends(get_current_user)):
    produto = await db.produtos_admin.find_one({"id": id}, {"_id": 0})
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Calcular margem de lucro
    margem = 0
    if data.preco_custo and data.preco_custo > 0 and data.preco_venda:
        margem = ((data.preco_venda - data.preco_custo) / data.preco_custo) * 100
    
    update_data = data.model_dump()
    update_data["margem_lucro"] = round(margem, 2)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.produtos_admin.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "produto", id, data.descricao)
    
    updated = await db.produtos_admin.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/produtos/{id}")
async def delete_produto(id: str, current_user: dict = Depends(get_current_user)):
    produto = await db.produtos_admin.find_one({"id": id}, {"_id": 0})
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    await db.produtos_admin.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "produto", id, produto["descricao"])
    return {"message": "Produto excluído"}

# --- Anexos de Produtos ---
PRODUTOS_ANEXOS_DIR = ROOT_DIR / "uploads" / "produtos"
PRODUTOS_ANEXOS_DIR.mkdir(parents=True, exist_ok=True)

@api_router.post("/admin/produtos/{id}/anexos")
async def upload_produto_anexo(
    id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload anexo para produto"""
    produto = await db.produtos_admin.find_one({"id": id}, {"_id": 0})
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    content = await file.read()
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 50MB")
    
    ext = Path(file.filename).suffix.lower() if file.filename else ''
    unique_filename = f"{id}_{uuid.uuid4()}{ext}"
    file_path = PRODUTOS_ANEXOS_DIR / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    anexo = {
        "id": str(uuid.uuid4()),
        "filename": unique_filename,
        "original_name": file.filename,
        "size": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.produtos_admin.update_one({"id": id}, {"$push": {"anexos": anexo}})
    await create_audit_log(current_user, "upload anexo", "produto", id, f"{produto['descricao']} - {file.filename}")
    
    return {"message": "Anexo adicionado", "anexo": anexo}

@api_router.delete("/admin/produtos/{id}/anexos/{anexo_id}")
async def delete_produto_anexo(
    id: str,
    anexo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Excluir anexo de produto"""
    produto = await db.produtos_admin.find_one({"id": id}, {"_id": 0})
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    anexo = next((a for a in produto.get("anexos", []) if a["id"] == anexo_id), None)
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    file_path = PRODUTOS_ANEXOS_DIR / anexo["filename"]
    if file_path.exists():
        file_path.unlink()
    
    await db.produtos_admin.update_one({"id": id}, {"$pull": {"anexos": {"id": anexo_id}}})
    await create_audit_log(current_user, "excluir anexo", "produto", id, produto["descricao"])
    
    return {"message": "Anexo excluído"}

@api_router.get("/admin/produtos/{id}/anexos/{anexo_id}/download")
async def download_produto_anexo(
    id: str,
    anexo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download de anexo de produto"""
    produto = await db.produtos_admin.find_one({"id": id}, {"_id": 0})
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    anexo = next((a for a in produto.get("anexos", []) if a["id"] == anexo_id), None)
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    file_path = PRODUTOS_ANEXOS_DIR / anexo["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=str(file_path),
        filename=anexo.get("original_name", anexo["filename"]),
        media_type="application/octet-stream"
    )

# --- Ordens de Serviço (Completo) ---
@api_router.get("/admin/ordens-servico")
async def get_ordens_servico(
    status: Optional[str] = None,
    cliente_id: Optional[str] = None,
    obra: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    confirmada: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if cliente_id:
        query["cliente_id"] = cliente_id
    if obra:
        query["obra"] = {"$regex": obra, "$options": "i"}
    if confirmada is not None:
        query["confirmada"] = confirmada
    if data_inicio and data_fim:
        query["data_abertura"] = {"$gte": data_inicio, "$lte": data_fim}
    if search:
        query["$or"] = [
            {"cliente_nome": {"$regex": search, "$options": "i"}},
            {"cliente_fantasia": {"$regex": search, "$options": "i"}},
            {"obra": {"$regex": search, "$options": "i"}},
            {"descricao": {"$regex": search, "$options": "i"}},
            {"numero_contrato": {"$regex": search, "$options": "i"}}
        ]
    
    ordens = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Calcular valor restante
    for ordem in ordens:
        valor_total = ordem.get("valor_total", 0) or 0
        valor_antecipado = ordem.get("valor_antecipado", 0) or 0
        ordem["valor_restante"] = valor_total - valor_antecipado
    
    return ordens

@api_router.post("/admin/ordens-servico")
async def create_ordem_servico(data: OrdemServicoCreate, current_user: dict = Depends(get_current_user)):
    numero = await get_next_sequence("ordens_servico")
    
    ordem = {
        "id": str(uuid.uuid4()),
        "numero": numero,
        **data.model_dump(),
        "data_abertura": data.data_abertura or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "valor_restante": (data.valor_total or 0) - (data.valor_antecipado or 0),
        "itens": [],
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ordens_servico.insert_one(ordem)
    await create_audit_log(current_user, "create", "ordem_servico", ordem["id"], f"OS-{numero}")
    del ordem["_id"]
    return ordem

@api_router.get("/admin/ordens-servico/{id}")
async def get_ordem_servico(id: str, current_user: dict = Depends(get_current_user)):
    ordem = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    valor_total = ordem.get("valor_total", 0) or 0
    valor_antecipado = ordem.get("valor_antecipado", 0) or 0
    ordem["valor_restante"] = valor_total - valor_antecipado
    
    return ordem

@api_router.put("/admin/ordens-servico/{id}")
async def update_ordem_servico(id: str, data: OrdemServicoCreate, current_user: dict = Depends(get_current_user)):
    ordem = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    update_data = data.model_dump()
    update_data["valor_restante"] = (data.valor_total or 0) - (data.valor_antecipado or 0)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.ordens_servico.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "ordem_servico", id, f"OS-{ordem['numero']}")
    
    updated = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.post("/admin/ordens-servico/{id}/itens")
async def add_item_ordem_servico(id: str, data: OrdemServicoItemCreate, current_user: dict = Depends(get_current_user)):
    ordem = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    valor_total = data.quantidade * data.valor_unitario
    if data.desconto_percent:
        valor_total = valor_total * (1 - data.desconto_percent / 100)
    
    item = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "valor_total": round(valor_total, 2)
    }
    
    await db.ordens_servico.update_one({"id": id}, {"$push": {"itens": item}})
    
    # Recalcular valor total da OS
    ordem_atualizada = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    novo_total = sum(i.get("valor_total", 0) for i in ordem_atualizada.get("itens", []))
    await db.ordens_servico.update_one({"id": id}, {"$set": {"valor_total": novo_total}})
    
    return {"message": "Item adicionado", "item": item}

@api_router.delete("/admin/ordens-servico/{id}/itens/{item_id}")
async def remove_item_ordem_servico(id: str, item_id: str, current_user: dict = Depends(get_current_user)):
    ordem = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    await db.ordens_servico.update_one({"id": id}, {"$pull": {"itens": {"id": item_id}}})
    
    # Recalcular valor total da OS
    ordem_atualizada = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    novo_total = sum(i.get("valor_total", 0) for i in ordem_atualizada.get("itens", []))
    await db.ordens_servico.update_one({"id": id}, {"$set": {"valor_total": novo_total}})
    
    return {"message": "Item removido"}

class StatusOSUpdate(BaseModel):
    status: str

@api_router.patch("/admin/ordens-servico/{id}/status")
async def update_ordem_status(id: str, data: StatusOSUpdate, current_user: dict = Depends(get_current_user)):
    ordem = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    update_fields = {"status": data.status}
    if data.status == "concluida":
        update_fields["data_conclusao"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    await db.ordens_servico.update_one({"id": id}, {"$set": update_fields})
    await create_audit_log(current_user, "update", "ordem_servico", id, f"OS-{ordem['numero']} - Status: {data.status}")
    return {"message": "Status atualizado"}

@api_router.patch("/admin/ordens-servico/{id}/confirmar")
async def confirmar_ordem_servico(id: str, current_user: dict = Depends(get_current_user)):
    ordem = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    await db.ordens_servico.update_one({"id": id}, {"$set": {"confirmada": True}})
    await create_audit_log(current_user, "update", "ordem_servico", id, f"OS-{ordem['numero']} - CONFIRMADA")
    return {"message": "Ordem confirmada"}

@api_router.delete("/admin/ordens-servico/{id}")
async def delete_ordem_servico(id: str, current_user: dict = Depends(get_current_user)):
    ordem = await db.ordens_servico.find_one({"id": id}, {"_id": 0})
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    await db.ordens_servico.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "ordem_servico", id, f"OS-{ordem['numero']}")
    return {"message": "Ordem de serviço excluída"}

# --- Plano de Contas (2 níveis) ---
@api_router.get("/admin/plano-contas")
async def get_plano_contas(
    tipo: Optional[str] = None,
    nivel: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if tipo:
        query["tipo"] = tipo
    if nivel:
        query["nivel"] = nivel
    
    contas = await db.plano_contas.find(query, {"_id": 0}).sort([("tipo", 1), ("codigo", 1)]).to_list(1000)
    
    # Adicionar nome do pai se for nível 2
    for conta in contas:
        if conta.get("pai_id"):
            pai = await db.plano_contas.find_one({"id": conta["pai_id"]}, {"_id": 0})
            if pai:
                conta["pai_nome"] = pai.get("nome")
    
    return contas

@api_router.post("/admin/plano-contas")
async def create_plano_conta(data: PlanoContaCreate, current_user: dict = Depends(get_current_user)):
    conta = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.plano_contas.insert_one(conta)
    await create_audit_log(current_user, "create", "plano_conta", conta["id"], data.nome)
    del conta["_id"]
    return conta

@api_router.put("/admin/plano-contas/{id}")
async def update_plano_conta(id: str, data: PlanoContaCreate, current_user: dict = Depends(get_current_user)):
    conta = await db.plano_contas.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.plano_contas.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "plano_conta", id, data.nome)
    
    updated = await db.plano_contas.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/plano-contas/{id}")
async def delete_plano_conta(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.plano_contas.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    # Excluir subcontas primeiro (cascata)
    subcontas = await db.plano_contas.find({"pai_id": id}, {"_id": 0}).to_list(100)
    for sub in subcontas:
        await db.plano_contas.delete_one({"id": sub["id"]})
        await create_audit_log(current_user, "delete", "plano_conta", sub["id"], f"Subconta: {sub['nome']}")
    
    # Excluir a conta principal
    await db.plano_contas.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "plano_conta", id, conta["nome"])
    
    msg = f"Conta excluída" + (f" junto com {len(subcontas)} subconta(s)" if subcontas else "")
    return {"message": msg}

# --- Centro de Custo ---
@api_router.get("/admin/centros-custo")
async def get_centros_custo(current_user: dict = Depends(get_current_user)):
    centros = await db.centros_custo.find({}, {"_id": 0}).sort("nome", 1).to_list(1000)
    return centros

@api_router.post("/admin/centros-custo")
async def create_centro_custo(data: CentroCustoCreate, current_user: dict = Depends(get_current_user)):
    centro = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.centros_custo.insert_one(centro)
    await create_audit_log(current_user, "create", "centro_custo", centro["id"], data.nome)
    del centro["_id"]
    return centro

@api_router.put("/admin/centros-custo/{id}")
async def update_centro_custo(id: str, data: CentroCustoCreate, current_user: dict = Depends(get_current_user)):
    centro = await db.centros_custo.find_one({"id": id}, {"_id": 0})
    if not centro:
        raise HTTPException(status_code=404, detail="Centro de custo não encontrado")
    
    update_data = data.model_dump()
    await db.centros_custo.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "centro_custo", id, data.nome)
    
    updated = await db.centros_custo.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/centros-custo/{id}")
async def delete_centro_custo(id: str, current_user: dict = Depends(get_current_user)):
    centro = await db.centros_custo.find_one({"id": id}, {"_id": 0})
    if not centro:
        raise HTTPException(status_code=404, detail="Centro de custo não encontrado")
    
    await db.centros_custo.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "centro_custo", id, centro["nome"])
    return {"message": "Centro de custo excluído"}

# --- Formas de Pagamento ---
@api_router.get("/admin/formas-pagamento")
async def get_formas_pagamento(
    ativo: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if ativo is not None:
        query["ativo"] = ativo
    
    formas = await db.formas_pagamento.find(query, {"_id": 0}).sort("nome", 1).to_list(1000)
    return formas

@api_router.post("/admin/formas-pagamento")
async def create_forma_pagamento(data: FormaPagamentoCreate, current_user: dict = Depends(get_current_user)):
    forma = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.formas_pagamento.insert_one(forma)
    await create_audit_log(current_user, "create", "forma_pagamento", forma["id"], data.nome)
    del forma["_id"]
    return forma

@api_router.put("/admin/formas-pagamento/{id}")
async def update_forma_pagamento(id: str, data: FormaPagamentoCreate, current_user: dict = Depends(get_current_user)):
    forma = await db.formas_pagamento.find_one({"id": id}, {"_id": 0})
    if not forma:
        raise HTTPException(status_code=404, detail="Forma de pagamento não encontrada")
    
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.formas_pagamento.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "forma_pagamento", id, data.nome)
    
    updated = await db.formas_pagamento.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/formas-pagamento/{id}")
async def delete_forma_pagamento(id: str, current_user: dict = Depends(get_current_user)):
    forma = await db.formas_pagamento.find_one({"id": id}, {"_id": 0})
    if not forma:
        raise HTTPException(status_code=404, detail="Forma de pagamento não encontrada")
    
    await db.formas_pagamento.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "forma_pagamento", id, forma["nome"])
    return {"message": "Forma de pagamento excluída"}

# --- Contas Bancárias ---
@api_router.get("/admin/contas-bancarias")
async def get_contas_bancarias(
    ativo: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if ativo is not None:
        query["ativo"] = ativo
    
    contas = await db.contas_bancarias.find(query, {"_id": 0}).sort("nome", 1).to_list(1000)
    return contas

@api_router.post("/admin/contas-bancarias")
async def create_conta_bancaria(data: ContaBancariaCreate, current_user: dict = Depends(get_current_user)):
    conta = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contas_bancarias.insert_one(conta)
    await create_audit_log(current_user, "create", "conta_bancaria", conta["id"], data.nome)
    del conta["_id"]
    return conta

@api_router.get("/admin/contas-bancarias/{id}")
async def get_conta_bancaria(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_bancarias.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")
    return conta

@api_router.put("/admin/contas-bancarias/{id}")
async def update_conta_bancaria(id: str, data: ContaBancariaCreate, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_bancarias.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")
    
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.contas_bancarias.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "conta_bancaria", id, data.nome)
    
    updated = await db.contas_bancarias.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/contas-bancarias/{id}")
async def delete_conta_bancaria(id: str, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_bancarias.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")
    
    await db.contas_bancarias.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "conta_bancaria", id, conta["nome"])
    return {"message": "Conta bancária excluída"}

@api_router.patch("/admin/contas-bancarias/{id}/saldo")
async def update_saldo_conta_bancaria(id: str, saldo: float, current_user: dict = Depends(get_current_user)):
    conta = await db.contas_bancarias.find_one({"id": id}, {"_id": 0})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")
    
    await db.contas_bancarias.update_one({"id": id}, {"$set": {"saldo_atual": saldo, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await create_audit_log(current_user, "update", "conta_bancaria_saldo", id, f"Saldo: {saldo}")
    
    updated = await db.contas_bancarias.find_one({"id": id}, {"_id": 0})
    return updated

# --- Aluguéis de Máquinas ---
@api_router.get("/admin/alugueis")
async def get_alugueis(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    
    alugueis = await db.alugueis.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return alugueis

@api_router.get("/admin/alugueis/{id}")
async def get_aluguel(id: str, current_user: dict = Depends(get_current_user)):
    aluguel = await db.alugueis.find_one({"id": id}, {"_id": 0})
    if not aluguel:
        raise HTTPException(status_code=404, detail="Aluguel não encontrado")
    return aluguel

@api_router.post("/admin/alugueis")
async def create_aluguel(data: AluguelCreate, current_user: dict = Depends(get_current_user)):
    numero = await get_next_sequence("alugueis")
    
    aluguel = {
        "id": str(uuid.uuid4()),
        "numero": numero,
        **data.model_dump(exclude={"gerar_conta_receber"}),
        "conta_receber_id": None,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Gerar conta a receber automaticamente se solicitado
    if data.gerar_conta_receber:
        periodo_label = {
            "diaria": "Diária", "semanal": "Semanal", "quinzenal": "Quinzenal",
            "mensal": "Mensal", "semestral": "Semestral", "anual": "Anual",
            "hora": "Por Hora", "outro": data.periodo_especificado or "Outro"
        }.get(data.tipo_periodo, data.tipo_periodo)
        
        conta_receber = {
            "id": str(uuid.uuid4()),
            "numero": await get_next_sequence("contas_receber"),
            "cliente_nome": data.cliente_nome,
            "documento": data.cliente_documento,
            "descricao": f"Aluguel #{numero} - {data.maquina_nome or 'Máquina'} ({periodo_label})",
            "valor": data.valor,
            "valor_final": data.valor,
            "data_emissao": data.data_entrega,
            "data_vencimento": data.data_vencimento,
            "status": "em_aberto",
            "forma_pagamento": "boleto",
            "observacoes": f"Gerado automaticamente do aluguel #{numero}",
            "aluguel_id": aluguel["id"],
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.contas_receber.insert_one(conta_receber)
        aluguel["conta_receber_id"] = conta_receber["id"]
        del conta_receber["_id"]
    
    await db.alugueis.insert_one(aluguel)
    await create_audit_log(current_user, "create", "aluguel", aluguel["id"], f"Aluguel #{numero}")
    del aluguel["_id"]
    return aluguel

@api_router.put("/admin/alugueis/{id}")
async def update_aluguel(id: str, data: AluguelCreate, current_user: dict = Depends(get_current_user)):
    aluguel = await db.alugueis.find_one({"id": id}, {"_id": 0})
    if not aluguel:
        raise HTTPException(status_code=404, detail="Aluguel não encontrado")
    
    update_data = data.model_dump(exclude={"gerar_conta_receber"})
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.alugueis.update_one({"id": id}, {"$set": update_data})
    
    # Atualizar conta a receber se existir
    if aluguel.get("conta_receber_id"):
        await db.contas_receber.update_one(
            {"id": aluguel["conta_receber_id"]},
            {"$set": {
                "cliente_nome": data.cliente_nome,
                "valor": data.valor,
                "valor_final": data.valor,
                "data_vencimento": data.data_vencimento
            }}
        )
    
    await create_audit_log(current_user, "update", "aluguel", id, f"Aluguel #{aluguel['numero']}")
    
    updated = await db.alugueis.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.patch("/admin/alugueis/{id}/status")
async def update_aluguel_status(id: str, status_data: dict, current_user: dict = Depends(get_current_user)):
    aluguel = await db.alugueis.find_one({"id": id}, {"_id": 0})
    if not aluguel:
        raise HTTPException(status_code=404, detail="Aluguel não encontrado")
    
    new_status = status_data.get("status")
    update_data = {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}
    
    if new_status == "finalizado" and status_data.get("data_devolucao"):
        update_data["data_devolucao"] = status_data.get("data_devolucao")
    
    await db.alugueis.update_one({"id": id}, {"$set": update_data})
    
    # Se finalizado, marcar conta a receber como quitada
    if new_status == "finalizado" and aluguel.get("conta_receber_id"):
        await db.contas_receber.update_one(
            {"id": aluguel["conta_receber_id"]},
            {"$set": {"status": "quitada", "data_recebimento": datetime.now(timezone.utc).strftime("%Y-%m-%d")}}
        )
    
    await create_audit_log(current_user, "update", "aluguel", id, f"Status: {new_status}")
    
    updated = await db.alugueis.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/alugueis/{id}")
async def delete_aluguel(id: str, current_user: dict = Depends(get_current_user)):
    aluguel = await db.alugueis.find_one({"id": id}, {"_id": 0})
    if not aluguel:
        raise HTTPException(status_code=404, detail="Aluguel não encontrado")
    
    # Excluir conta a receber associada
    if aluguel.get("conta_receber_id"):
        await db.contas_receber.delete_one({"id": aluguel["conta_receber_id"]})
    
    await db.alugueis.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "aluguel", id, f"Aluguel #{aluguel['numero']}")
    return {"message": "Aluguel excluído"}

# --- Upload contrato de aluguel ---
CONTRATOS_DIR = ROOT_DIR / "uploads" / "contratos"
CONTRATOS_DIR.mkdir(parents=True, exist_ok=True)

@api_router.post("/admin/alugueis/{id}/contrato")
async def upload_contrato(
    id: str, 
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload de arquivo de contrato para um aluguel"""
    aluguel = await db.alugueis.find_one({"id": id}, {"_id": 0})
    if not aluguel:
        raise HTTPException(status_code=404, detail="Aluguel não encontrado")
    
    # Validate file type
    allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    ext = Path(file.filename).suffix.lower() if file.filename else ''
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Tipo de arquivo não permitido. Use: {', '.join(allowed_extensions)}")
    
    # Read file content
    content = await file.read()
    max_size = 50 * 1024 * 1024  # 50MB
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 50MB")
    
    # Save file
    unique_filename = f"{id}_{uuid.uuid4()}{ext}"
    file_path = CONTRATOS_DIR / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update aluguel
    await db.alugueis.update_one(
        {"id": id},
        {"$set": {
            "contrato_arquivo": unique_filename,
            "contrato_nome": file.filename,
            "contrato_uploaded_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await create_audit_log(current_user, "upload", "contrato", id, f"Contrato do aluguel #{aluguel.get('numero', id)}")
    return {"message": "Contrato anexado com sucesso", "filename": unique_filename}

@api_router.get("/admin/alugueis/{id}/contrato/download")
async def download_contrato(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download de arquivo de contrato"""
    aluguel = await db.alugueis.find_one({"id": id}, {"_id": 0})
    if not aluguel:
        raise HTTPException(status_code=404, detail="Aluguel não encontrado")
    
    if not aluguel.get("contrato_arquivo"):
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    
    file_path = CONTRATOS_DIR / aluguel["contrato_arquivo"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=str(file_path),
        filename=aluguel.get("contrato_nome", aluguel["contrato_arquivo"]),
        media_type="application/octet-stream"
    )

# --- IMÓVEIS PARA LOCAÇÃO ---
class ImovelCreate(BaseModel):
    tipo_imovel: str = "apartamento"
    descricao: str
    endereco: str
    numero: Optional[str] = ""
    complemento: Optional[str] = ""
    bairro: Optional[str] = ""
    cidade: Optional[str] = ""
    estado: Optional[str] = "TO"
    cep: Optional[str] = ""
    area_m2: Optional[float] = 0
    quartos: Optional[int] = 0
    banheiros: Optional[int] = 0
    vagas_garagem: Optional[int] = 0
    cliente_nome: str
    cliente_telefone: Optional[str] = ""
    cliente_documento: Optional[str] = ""
    numero_contrato: Optional[str] = ""
    tipo_periodo: str = "mensal"
    periodo_especificado: Optional[str] = ""
    data_inicio: str
    data_vencimento: Optional[str] = ""
    valor_aluguel: float
    valor_condominio: Optional[float] = 0
    valor_iptu: Optional[float] = 0
    valor_caucao: Optional[float] = 0
    dia_vencimento: Optional[int] = 10
    observacoes: Optional[str] = ""
    gerar_conta_receber: bool = True

@api_router.get("/admin/imoveis")
async def get_imoveis(current_user: dict = Depends(get_current_user)):
    imoveis = await db.imoveis.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return imoveis

@api_router.get("/admin/imoveis/{id}")
async def get_imovel(id: str, current_user: dict = Depends(get_current_user)):
    imovel = await db.imoveis.find_one({"id": id}, {"_id": 0})
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    return imovel

@api_router.post("/admin/imoveis")
async def create_imovel(imovel: ImovelCreate, current_user: dict = Depends(get_current_user)):
    imovel_dict = imovel.model_dump()
    imovel_dict["id"] = str(uuid.uuid4())
    imovel_dict["status"] = "ativo" if imovel_dict["cliente_nome"] else "pendente"
    imovel_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    imovel_dict["created_by"] = current_user.get("user_id")
    
    # Gerar conta a receber
    if imovel_dict["gerar_conta_receber"] and imovel_dict["valor_aluguel"] > 0:
        valor_total = imovel_dict["valor_aluguel"] + imovel_dict.get("valor_condominio", 0) + imovel_dict.get("valor_iptu", 0)
        
        # Calcular próximo vencimento
        hoje = datetime.now()
        dia_venc = imovel_dict.get("dia_vencimento", 10)
        if hoje.day > dia_venc:
            prox_mes = hoje.month + 1 if hoje.month < 12 else 1
            prox_ano = hoje.year if hoje.month < 12 else hoje.year + 1
        else:
            prox_mes = hoje.month
            prox_ano = hoje.year
        
        data_vencimento = f"{prox_ano}-{prox_mes:02d}-{dia_venc:02d}"
        
        conta_receber = {
            "id": str(uuid.uuid4()),
            "descricao": f"Aluguel - {imovel_dict['descricao']}",
            "cliente_nome": imovel_dict["cliente_nome"],
            "cliente_documento": imovel_dict.get("cliente_documento", ""),
            "valor": valor_total,
            "valor_final": valor_total,
            "data_vencimento": data_vencimento,
            "status": "em_aberto",
            "origem": "imovel",
            "imovel_id": imovel_dict["id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get("user_id")
        }
        await db.contas_receber.insert_one(conta_receber)
        imovel_dict["conta_receber_id"] = conta_receber["id"]
    
    await db.imoveis.insert_one(imovel_dict)
    await create_audit_log(current_user, "create", "imovel", imovel_dict["id"], f"Imóvel: {imovel_dict['descricao']}")
    
    created = await db.imoveis.find_one({"id": imovel_dict["id"]}, {"_id": 0})
    return created

@api_router.put("/admin/imoveis/{id}")
async def update_imovel(id: str, imovel: ImovelCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.imoveis.find_one({"id": id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    
    update_data = imovel.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.imoveis.update_one({"id": id}, {"$set": update_data})
    await create_audit_log(current_user, "update", "imovel", id, f"Imóvel: {update_data['descricao']}")
    
    updated = await db.imoveis.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.patch("/admin/imoveis/{id}/status")
async def update_imovel_status(id: str, status_data: dict, current_user: dict = Depends(get_current_user)):
    imovel = await db.imoveis.find_one({"id": id}, {"_id": 0})
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    
    new_status = status_data.get("status")
    await db.imoveis.update_one({"id": id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await create_audit_log(current_user, "update", "imovel", id, f"Status: {new_status}")
    
    updated = await db.imoveis.find_one({"id": id}, {"_id": 0})
    return updated

@api_router.delete("/admin/imoveis/{id}")
async def delete_imovel(id: str, current_user: dict = Depends(get_current_user)):
    imovel = await db.imoveis.find_one({"id": id}, {"_id": 0})
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    
    if imovel.get("conta_receber_id"):
        await db.contas_receber.delete_one({"id": imovel["conta_receber_id"]})
    
    await db.imoveis.delete_one({"id": id})
    await create_audit_log(current_user, "delete", "imovel", id, f"Imóvel: {imovel['descricao']}")
    return {"message": "Imóvel excluído"}

CONTRATOS_IMOVEIS_DIR = ROOT_DIR / "uploads" / "contratos_imoveis"
CONTRATOS_IMOVEIS_DIR.mkdir(parents=True, exist_ok=True)

@api_router.post("/admin/imoveis/{id}/contrato")
async def upload_contrato_imovel(id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    imovel = await db.imoveis.find_one({"id": id}, {"_id": 0})
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    
    ext = Path(file.filename).suffix.lower()
    allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Tipo não permitido. Use: {', '.join(allowed_extensions)}")
    
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 50MB")
    
    unique_filename = f"{id}_{uuid.uuid4()}{ext}"
    file_path = CONTRATOS_IMOVEIS_DIR / unique_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    await db.imoveis.update_one({"id": id}, {"$set": {
        "contrato_arquivo": unique_filename,
        "contrato_nome": file.filename,
        "contrato_uploaded_at": datetime.now(timezone.utc).isoformat()
    }})
    
    return {"message": "Contrato anexado", "filename": unique_filename}

# --- Buscar máquinas do sistema de gerenciamento ---
@api_router.get("/admin/maquinas-disponiveis")
async def get_maquinas_disponiveis(current_user: dict = Depends(get_current_user)):
    """Retorna lista de máquinas cadastradas no sistema de gerenciamento"""
    maquinas = await db.machines.find({}, {"_id": 0}).sort("name", 1).to_list(1000)
    return maquinas

# --- Notificações ---
@api_router.get("/admin/notificacoes")
async def get_notificacoes(
    prazo_dias: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Retorna itens com vencimento próximo"""
    from datetime import timedelta
    hoje = datetime.now(timezone.utc)
    hoje_str = hoje.strftime("%Y-%m-%d")
    limite = (hoje + timedelta(days=prazo_dias)).strftime("%Y-%m-%d")
    
    notificacoes = []
    
    # Contas a Pagar próximas do vencimento
    contas_pagar = await db.contas_pagar.find({
        "status": "em_aberto",
        "data_vencimento": {"$lte": limite}
    }, {"_id": 0}).to_list(100)
    
    for c in contas_pagar:
        vencida = c.get("data_vencimento", "") < hoje_str
        notificacoes.append({
            "tipo": "conta_pagar",
            "id": c.get("id"),
            "titulo": c.get("descricao") or f"Conta #{c.get('numero')}",
            "subtitulo": c.get("fornecedor_nome"),
            "valor": c.get("valor_final") or c.get("valor"),
            "data": c.get("data_vencimento"),
            "vencida": vencida,
            "urgencia": "alta" if vencida else ("media" if c.get("data_vencimento", "") <= (hoje + timedelta(days=3)).strftime("%Y-%m-%d") else "baixa"),
            "link": "/administrativo/a-pagar"
        })
    
    # Contas a Receber próximas do vencimento
    contas_receber = await db.contas_receber.find({
        "status": "em_aberto",
        "data_vencimento": {"$lte": limite}
    }, {"_id": 0}).to_list(100)
    
    for c in contas_receber:
        vencida = c.get("data_vencimento", "") < hoje_str
        notificacoes.append({
            "tipo": "conta_receber",
            "id": c.get("id"),
            "titulo": c.get("descricao") or f"Conta #{c.get('numero')}",
            "subtitulo": c.get("cliente_nome"),
            "valor": c.get("valor_final") or c.get("valor"),
            "data": c.get("data_vencimento"),
            "vencida": vencida,
            "urgencia": "alta" if vencida else ("media" if c.get("data_vencimento", "") <= (hoje + timedelta(days=3)).strftime("%Y-%m-%d") else "baixa"),
            "link": "/administrativo/a-receber"
        })
    
    # Ordens de Serviço com previsão de entrega próxima
    ordens = await db.ordens_servico.find({
        "status": {"$in": ["em_aberto", "em_andamento"]},
        "data_previsao_entrega": {"$lte": limite, "$ne": None, "$ne": ""}
    }, {"_id": 0}).to_list(100)
    
    for o in ordens:
        vencida = o.get("data_previsao_entrega", "") < hoje_str
        notificacoes.append({
            "tipo": "ordem_servico",
            "id": o.get("id"),
            "titulo": f"OS #{o.get('numero')} - {o.get('descricao', 'Sem descrição')[:50]}",
            "subtitulo": o.get("cliente_nome") or o.get("cliente_fantasia"),
            "valor": o.get("valor_total"),
            "data": o.get("data_previsao_entrega"),
            "vencida": vencida,
            "urgencia": "alta" if vencida else ("media" if o.get("data_previsao_entrega", "") <= (hoje + timedelta(days=3)).strftime("%Y-%m-%d") else "baixa"),
            "link": "/administrativo/ordens-servico"
        })
    
    # Aluguéis com vencimento próximo
    alugueis = await db.alugueis.find({
        "status": "ativo",
        "data_vencimento": {"$lte": limite}
    }, {"_id": 0}).to_list(100)
    
    for a in alugueis:
        vencida = a.get("data_vencimento", "") < hoje_str
        notificacoes.append({
            "tipo": "aluguel",
            "id": a.get("id"),
            "titulo": f"Aluguel #{a.get('numero')} - {a.get('maquina_nome', 'Máquina')}",
            "subtitulo": a.get("cliente_nome"),
            "valor": a.get("valor"),
            "data": a.get("data_vencimento"),
            "vencida": vencida,
            "urgencia": "alta" if vencida else ("media" if a.get("data_vencimento", "") <= (hoje + timedelta(days=3)).strftime("%Y-%m-%d") else "baixa"),
            "link": "/administrativo/alugueis"
        })
    
    # Ordenar por data e urgência
    notificacoes.sort(key=lambda x: (
        0 if x["urgencia"] == "alta" else (1 if x["urgencia"] == "media" else 2),
        x.get("data", "9999-99-99")
    ))
    
    # Resumo
    resumo = {
        "total": len(notificacoes),
        "vencidas": len([n for n in notificacoes if n["vencida"]]),
        "alta": len([n for n in notificacoes if n["urgencia"] == "alta"]),
        "media": len([n for n in notificacoes if n["urgencia"] == "media"]),
        "baixa": len([n for n in notificacoes if n["urgencia"] == "baixa"]),
        "por_tipo": {
            "conta_pagar": len([n for n in notificacoes if n["tipo"] == "conta_pagar"]),
            "conta_receber": len([n for n in notificacoes if n["tipo"] == "conta_receber"]),
            "ordem_servico": len([n for n in notificacoes if n["tipo"] == "ordem_servico"]),
            "aluguel": len([n for n in notificacoes if n["tipo"] == "aluguel"])
        }
    }
    
    return {
        "resumo": resumo,
        "notificacoes": notificacoes,
        "prazo_dias": prazo_dias
    }

@api_router.get("/admin/notificacoes/contagem")
async def get_notificacoes_contagem(
    prazo_dias: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Retorna apenas a contagem de notificações (para o badge)"""
    from datetime import timedelta
    hoje = datetime.now(timezone.utc)
    hoje_str = hoje.strftime("%Y-%m-%d")
    limite = (hoje + timedelta(days=prazo_dias)).strftime("%Y-%m-%d")
    
    count_pagar = await db.contas_pagar.count_documents({
        "status": "em_aberto",
        "data_vencimento": {"$lte": limite}
    })
    
    count_receber = await db.contas_receber.count_documents({
        "status": "em_aberto",
        "data_vencimento": {"$lte": limite}
    })
    
    count_os = await db.ordens_servico.count_documents({
        "status": {"$in": ["em_aberto", "em_andamento"]},
        "data_previsao_entrega": {"$lte": limite, "$ne": None, "$ne": ""}
    })
    
    count_alugueis = await db.alugueis.count_documents({
        "status": "ativo",
        "data_vencimento": {"$lte": limite}
    })
    
    # Contar vencidas
    count_vencidas = await db.contas_pagar.count_documents({
        "status": "em_aberto",
        "data_vencimento": {"$lt": hoje_str}
    }) + await db.contas_receber.count_documents({
        "status": "em_aberto",
        "data_vencimento": {"$lt": hoje_str}
    }) + await db.alugueis.count_documents({
        "status": "ativo",
        "data_vencimento": {"$lt": hoje_str}
    })
    
    total = count_pagar + count_receber + count_os + count_alugueis
    
    return {
        "total": total,
        "vencidas": count_vencidas,
        "prazo_dias": prazo_dias
    }


# ============ PAINEL ADMINISTRATIVO (GESTÃO DE USUÁRIOS) ============

@api_router.get("/admin-panel/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """Lista todos os usuários da plataforma"""
    users = []
    cursor = db.users.find({}, {"password": 0})
    async for user in cursor:
        users.append({
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role", "gerenciamento"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        })
    return users

class UserCreateAdmin(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "gerenciamento"  # gerenciamento, administrativo, ambos, admin

@api_router.post("/admin-panel/users")
async def create_user_admin(data: UserCreateAdmin, current_user: dict = Depends(get_current_user)):
    """Cria um novo usuário (apenas via painel admin)"""
    # Check if email already exists
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Validate role - includes all combination roles and custom roles like 'programador'
    valid_roles = [
        "gerenciamento", "administrativo", "rh", "ambos", 
        "ambos_rh", "gerenciamento_rh", "administrativo_rh", 
        "admin", "programador"
    ]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Tipo de acesso inválido. Opções: {', '.join(valid_roles)}")
    
    # Hash password
    hashed_password = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt())
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": data.name,
        "email": data.email,
        "password": hashed_password.decode('utf-8'),
        "role": data.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None
    }
    
    await db.users.insert_one(user_doc)
    
    # Traduzir role para português
    role_labels = {
        "gerenciamento": "Gerenciamento",
        "administrativo": "Administrativo",
        "rh": "RH",
        "ambos": "Gerenciamento + Administrativo",
        "ambos_rh": "Ger + Admin + RH",
        "gerenciamento_rh": "Gerenciamento + RH",
        "administrativo_rh": "Administrativo + RH",
        "admin": "Administrador",
        "programador": "Programador"
    }
    
    # Registrar na auditoria
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "action": f"Criou usuário: {data.name}",
        "details": f"Email: {data.email}\nTipo de Acesso: {role_labels.get(data.role, data.role)}",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Usuário criado com sucesso", "id": user_id}

class UserRoleUpdate(BaseModel):
    role: str

@api_router.patch("/admin-panel/users/{user_id}/role")
async def update_user_role(user_id: str, data: UserRoleUpdate, current_user: dict = Depends(get_current_user)):
    """Atualiza o role/permissões de um usuário"""
    # Roles com acesso total (admin e programador)
    admin_roles = ["admin", "programador"]
    if current_user.get("role") not in admin_roles:
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar permissões")
    
    # All valid roles including combination roles and custom roles
    valid_roles = [
        "gerenciamento", "administrativo", "rh", "ambos", 
        "ambos_rh", "gerenciamento_rh", "administrativo_rh", 
        "admin", "programador"
    ]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role inválido. Opções: {', '.join(valid_roles)}")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    old_role = user.get("role", "gerenciamento")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": data.role}}
    )
    
    # Registrar na auditoria
    await create_audit_log(
        user=current_user,
        action="alterar permissão",
        entity_type="usuário",
        entity_id=user_id,
        entity_name=user.get("name"),
        details=f"Permissão alterada de '{old_role}' para '{data.role}'",
        module="Painel Admin"
    )
    
    return {"message": "Permissão atualizada com sucesso", "new_role": data.role}

@api_router.delete("/admin-panel/users/{user_id}")
async def delete_user_admin(user_id: str, current_user: dict = Depends(get_current_user)):
    """Exclui um usuário"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Você não pode excluir sua própria conta")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await db.users.delete_one({"id": user_id})
    
    # Registrar na auditoria
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "action": f"Excluiu usuário: {user.get('name')}",
        "details": f"Email: {user.get('email')}",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Usuário excluído com sucesso"}

@api_router.get("/admin-panel/audit-logs")
async def get_audit_logs(current_user: dict = Depends(get_current_user)):
    """Retorna todos os logs de auditoria"""
    logs = []
    cursor = db.audit_logs.find({}).sort("created_at", -1).limit(500)
    async for log in cursor:
        logs.append({
            "id": log.get("id"),
            "user_id": log.get("user_id"),
            "user_name": log.get("user_name"),
            "user_email": log.get("user_email", ""),
            "action": log.get("action"),
            "entity_type": log.get("entity_type", ""),
            "entity_name": log.get("entity_name", ""),
            "module": log.get("module", "Sistema"),
            "details": log.get("details"),
            "created_at": log.get("created_at")
        })
    return logs

@api_router.get("/admin-panel/users/{user_id}/activities")
async def get_user_activities(user_id: str, current_user: dict = Depends(get_current_user)):
    """Retorna as atividades de um usuário específico"""
    activities = []
    cursor = db.audit_logs.find({"user_id": user_id}).sort("created_at", -1).limit(100)
    async for log in cursor:
        activities.append({
            "id": log.get("id"),
            "user_id": log.get("user_id"),
            "user_name": log.get("user_name"),
            "action": log.get("action"),
            "entity_type": log.get("entity_type", ""),
            "entity_name": log.get("entity_name", ""),
            "module": log.get("module", "Sistema"),
            "details": log.get("details"),
            "created_at": log.get("created_at")
        })
    return activities


# ============ DATABASE MANAGER ROUTES (ADMIN ONLY) ============

# Roles com acesso administrativo total
ADMIN_ROLES = ["admin", "programador"]

def require_admin(user: dict):
    """Verifica se o usuário é admin ou programador"""
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Acesso negado. Somente administradores podem acessar este recurso.")

# Lista de coleções disponíveis para gerenciamento
ALLOWED_COLLECTIONS = [
    "users", "machines", "maintenances", "categories", "stock_items", 
    "stock_categories", "stock_movements", "obras", "contas_pagar", 
    "contas_receber", "cadastros", "produtos_admin", "ordens_servico", 
    "alugueis", "audit_logs", "usage_logs"
]

@api_router.get("/admin-panel/database/{collection_name}")
async def get_collection_documents(
    collection_name: str, 
    page: int = 1, 
    limit: int = 20, 
    search: str = "",
    current_user: dict = Depends(get_current_user)
):
    """Retorna documentos de uma coleção específica com paginação e busca"""
    require_admin(current_user)
    
    if collection_name not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Coleção '{collection_name}' não permitida")
    
    collection = db[collection_name]
    skip = (page - 1) * limit
    
    # Build search query
    query = {}
    if search:
        # Busca em campos comuns - usar $exists para evitar erros
        query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"titulo": {"$regex": search, "$options": "i"}},
                {"descricao": {"$regex": search, "$options": "i"}},
                {"action": {"$regex": search, "$options": "i"}},
                {"id": {"$regex": search, "$options": "i"}}
            ]
        }
    
    try:
        # Get total count
        total = await collection.count_documents(query if search else {})
        
        # Get documents - tentar ordenar por created_at, se falhar usar _id
        documents = []
        try:
            cursor = collection.find(query if search else {}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
            async for doc in cursor:
                documents.append(doc)
        except Exception:
            # Fallback sem ordenação
            cursor = collection.find(query if search else {}, {"_id": 0}).skip(skip).limit(limit)
            async for doc in cursor:
                documents.append(doc)
        
        return {
            "documents": documents,
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar documentos: {str(e)}")

@api_router.post("/admin-panel/database/{collection_name}")
async def create_document(
    collection_name: str,
    document: dict,
    current_user: dict = Depends(get_current_user)
):
    """Cria um novo documento em uma coleção"""
    require_admin(current_user)
    
    if collection_name not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Coleção '{collection_name}' não permitida")
    
    collection = db[collection_name]
    
    # Adiciona ID e timestamp se não existirem
    if "id" not in document:
        document["id"] = str(uuid.uuid4())
    if "created_at" not in document:
        document["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await collection.insert_one(document)
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type=f"documento ({collection_name})",
        entity_id=document["id"],
        entity_name=document.get("name") or document.get("email") or document.get("titulo") or document["id"][:8],
        details=f"Documento criado via painel admin"
    )
    
    # Remove _id antes de retornar
    document.pop("_id", None)
    return {"message": "Documento criado com sucesso", "document": document}

@api_router.put("/admin-panel/database/{collection_name}/{doc_id}")
async def update_document(
    collection_name: str,
    doc_id: str,
    document: dict,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza um documento existente"""
    require_admin(current_user)
    
    if collection_name not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Coleção '{collection_name}' não permitida")
    
    collection = db[collection_name]
    
    # Encontra o documento
    existing = await collection.find_one({"id": doc_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Remove campos que não devem ser alterados diretamente
    document.pop("_id", None)
    
    # Atualiza o documento
    await collection.update_one({"id": doc_id}, {"$set": document})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type=f"documento ({collection_name})",
        entity_id=doc_id,
        entity_name=document.get("name") or document.get("email") or document.get("titulo") or doc_id[:8],
        details=f"Documento editado via painel admin"
    )
    
    return {"message": "Documento atualizado com sucesso"}

@api_router.delete("/admin-panel/database/{collection_name}/{doc_id}")
async def delete_document(
    collection_name: str,
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Exclui um documento de uma coleção"""
    require_admin(current_user)
    
    if collection_name not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Coleção '{collection_name}' não permitida")
    
    # Proteção especial para usuários admin
    if collection_name == "users":
        user_doc = await db.users.find_one({"id": doc_id}, {"_id": 0})
        if user_doc and user_doc.get("id") == current_user["id"]:
            raise HTTPException(status_code=400, detail="Você não pode excluir sua própria conta")
    
    collection = db[collection_name]
    
    # Encontra o documento para log
    existing = await collection.find_one({"id": doc_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Exclui o documento
    await collection.delete_one({"id": doc_id})
    
    # Audit log
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type=f"documento ({collection_name})",
        entity_id=doc_id,
        entity_name=existing.get("name") or existing.get("email") or existing.get("titulo") or doc_id[:8],
        details=f"Documento excluído via painel admin"
    )
    
    return {"message": "Documento excluído com sucesso"}


# ============ CHATBOT ROUTES (AI ASSISTANT) ============

from pydantic import BaseModel as PydanticBaseModel

class ChatMessage(PydanticBaseModel):
    message: str
    module: str = "gerenciamento"  # gerenciamento ou administrativo

class ChatResponse(PydanticBaseModel):
    response: str
    context_used: List[str] = []

async def get_full_platform_context() -> str:
    """Coleta TODAS as informações de TODAS as coleções do banco de dados"""
    context_parts = []
    
    context_parts.append("=" * 60)
    context_parts.append("BANCO DE DADOS COMPLETO - CRA CONSTRUTORA")
    context_parts.append("=" * 60)
    
    # ========== USUÁRIOS ==========
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nUSUÁRIOS DO SISTEMA ({len(users)} registros)\n{'='*40}")
    for u in users:
        context_parts.append(f"- Nome: {u.get('name')} | Email: {u.get('email')} | Tipo: {u.get('role', 'gerenciamento')} | Criado: {u.get('created_at', '-')[:10] if u.get('created_at') else '-'}")
    
    # ========== CATEGORIAS DE MÁQUINAS ==========
    categories = await db.categories.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCATEGORIAS DE MÁQUINAS ({len(categories)} registros)\n{'='*40}")
    for c in categories:
        context_parts.append(f"- ID: {c.get('id', '-')[:8]} | Nome: {c.get('name')} | Descrição: {c.get('description', '-')}")
    
    # ========== MÁQUINAS ==========
    machines = await db.machines.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nMÁQUINAS CADASTRADAS ({len(machines)} registros)\n{'='*40}")
    for m in machines:
        status = "Operacional" if m.get("status") == "operational" else "Em manutenção"
        context_parts.append(f"- ID: {m.get('id', '-')[:8]} | Nome: {m.get('name')} | Placa: {m.get('plate')} | Marca: {m.get('brand', '-')} | Modelo: {m.get('model', '-')} | Ano: {m.get('year', '-')} | Status: {status} | Horas desde troca óleo: {m.get('hours_since_oil_change', 0)}")
    
    # ========== MANUTENÇÕES ==========
    maintenances = await db.maintenances.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nMANUTENÇÕES ({len(maintenances)} registros)\n{'='*40}")
    # Calcular totais
    total_valor = sum(m.get('part_value', 0) for m in maintenances)
    preventivas = [m for m in maintenances if m.get('maintenance_type') == 'preventiva']
    corretivas = [m for m in maintenances if m.get('maintenance_type') == 'corretiva']
    context_parts.append(f"RESUMO: Total gasto: R$ {total_valor:.2f} | Preventivas: {len(preventivas)} | Corretivas: {len(corretivas)}")
    for m in maintenances:
        tipo = "Preventiva" if m.get("maintenance_type") == "preventiva" else "Corretiva"
        context_parts.append(f"- Peça: {m.get('part_name')} | Tipo: {tipo} | Valor: R$ {m.get('part_value', 0):.2f} | Data: {m.get('replacement_date', '-')} | Máquina ID: {m.get('machine_id', '-')[:8] if m.get('machine_id') else '-'} | Troca óleo: {'Sim' if m.get('is_oil_change') else 'Não'}")
    
    # ========== ESTOQUE - CATEGORIAS ==========
    stock_categories = await db.stock_categories.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCATEGORIAS DE ESTOQUE ({len(stock_categories)} registros)\n{'='*40}")
    for c in stock_categories:
        context_parts.append(f"- Nome: {c.get('name')}")
    
    # ========== ESTOQUE - ITENS ==========
    stock_items = await db.stock_items.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nITENS DE ESTOQUE ({len(stock_items)} registros)\n{'='*40}")
    low_stock = [i for i in stock_items if i.get("quantity", 0) <= i.get("min_quantity", 0)]
    context_parts.append(f"ALERTA: {len(low_stock)} itens com estoque baixo!")
    for i in stock_items:
        status = "⚠️ BAIXO" if i.get("quantity", 0) <= i.get("min_quantity", 0) else "OK"
        context_parts.append(f"- Nome: {i.get('name')} | Código: {i.get('code', '-')} | Categoria: {i.get('category', '-')} | Qtd: {i.get('quantity', 0)} {i.get('unit', 'un')} | Mínimo: {i.get('min_quantity', 0)} | Preço unit: R$ {i.get('unit_price', 0):.2f} | Local: {i.get('location', '-')} | Status: {status}")
    
    # ========== ESTOQUE - MOVIMENTAÇÕES ==========
    stock_movements = await db.stock_movements.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    context_parts.append(f"\n\n{'='*40}\nMOVIMENTAÇÕES DE ESTOQUE (últimas {len(stock_movements)})\n{'='*40}")
    for m in stock_movements:
        tipo = "ENTRADA" if m.get("movement_type") == "entrada" else "SAÍDA"
        context_parts.append(f"- {tipo}: {m.get('quantity')} unidades | Item ID: {m.get('item_id', '-')[:8] if m.get('item_id') else '-'} | Motivo: {m.get('reason', '-')} | Data: {m.get('created_at', '-')[:10] if m.get('created_at') else '-'}")
    
    # ========== OBRAS ==========
    obras = await db.obras.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nOBRAS/PROJETOS ({len(obras)} registros)\n{'='*40}")
    for o in obras:
        status_map = {"em_andamento": "Em andamento", "concluida": "Concluída", "pausada": "Pausada"}
        status = status_map.get(o.get("status", ""), o.get("status", ""))
        context_parts.append(f"- Nome: {o.get('name')} | Local: {o.get('location', '-')} | Status: {status} | Início: {o.get('start_date', '-')} | Fim: {o.get('end_date', '-')} | Descrição: {o.get('description', '-')}")
    
    # ========== REGISTROS DE USO (HORÍMETRO) ==========
    usage_logs = await db.usage_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    context_parts.append(f"\n\n{'='*40}\nREGISTROS DE USO/HORÍMETRO (últimos {len(usage_logs)})\n{'='*40}")
    for u in usage_logs:
        context_parts.append(f"- Máquina ID: {u.get('machine_id', '-')[:8] if u.get('machine_id') else '-'} | Horas: {u.get('hours', 0)} | Data: {u.get('created_at', '-')[:10] if u.get('created_at') else '-'} | Obs: {u.get('notes', '-')}")
    
    # ========== CADASTROS (CLIENTES/FORNECEDORES) ==========
    cadastros = await db.cadastros.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCADASTROS - CLIENTES/FORNECEDORES ({len(cadastros)} registros)\n{'='*40}")
    clientes = [c for c in cadastros if c.get('tipo') == 'cliente']
    fornecedores = [c for c in cadastros if c.get('tipo') == 'fornecedor']
    context_parts.append(f"RESUMO: {len(clientes)} clientes | {len(fornecedores)} fornecedores")
    for c in cadastros:
        context_parts.append(f"- Tipo: {c.get('tipo', 'cliente').upper()} | Nome/Razão: {c.get('nome_razao')} | CPF/CNPJ: {c.get('cpf_cnpj', '-')} | Tel: {c.get('telefone', '-')} | Email: {c.get('email', '-')} | Cidade: {c.get('cidade', '-')}/{c.get('estado', '-')}")
    
    # ========== CONTAS A PAGAR ==========
    contas_pagar = await db.contas_pagar.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCONTAS A PAGAR ({len(contas_pagar)} registros)\n{'='*40}")
    pendentes_pagar = [c for c in contas_pagar if c.get("status") == "pendente"]
    quitadas_pagar = [c for c in contas_pagar if c.get("status") == "quitada"]
    total_pendente_pagar = sum(c.get("valor", 0) for c in pendentes_pagar)
    total_quitado_pagar = sum(c.get("valor", 0) for c in quitadas_pagar)
    context_parts.append(f"RESUMO: Pendentes: {len(pendentes_pagar)} (R$ {total_pendente_pagar:.2f}) | Quitadas: {len(quitadas_pagar)} (R$ {total_quitado_pagar:.2f})")
    for c in contas_pagar:
        context_parts.append(f"- Descrição: {c.get('descricao')} | Valor: R$ {c.get('valor', 0):.2f} | Vencimento: {c.get('data_vencimento', '-')} | Status: {c.get('status', 'pendente').upper()} | Fornecedor: {c.get('fornecedor_nome', '-')} | Categoria: {c.get('plano_conta_nome', '-')}")
    
    # ========== CONTAS A RECEBER ==========
    contas_receber = await db.contas_receber.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCONTAS A RECEBER ({len(contas_receber)} registros)\n{'='*40}")
    pendentes_receber = [c for c in contas_receber if c.get("status") == "pendente"]
    quitadas_receber = [c for c in contas_receber if c.get("status") == "quitada"]
    total_pendente_receber = sum(c.get("valor", 0) for c in pendentes_receber)
    total_quitado_receber = sum(c.get("valor", 0) for c in quitadas_receber)
    context_parts.append(f"RESUMO: Pendentes: {len(pendentes_receber)} (R$ {total_pendente_receber:.2f}) | Recebidas: {len(quitadas_receber)} (R$ {total_quitado_receber:.2f})")
    for c in contas_receber:
        context_parts.append(f"- Descrição: {c.get('descricao')} | Valor: R$ {c.get('valor', 0):.2f} | Vencimento: {c.get('data_vencimento', '-')} | Status: {c.get('status', 'pendente').upper()} | Cliente: {c.get('cliente_nome', '-')} | Categoria: {c.get('plano_conta_nome', '-')}")
    
    # ========== PRODUTOS ==========
    produtos = await db.produtos_admin.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nPRODUTOS ({len(produtos)} registros)\n{'='*40}")
    for p in produtos:
        context_parts.append(f"- Código: {p.get('codigo', '-')} | Descrição: {p.get('descricao')} | Unidade: {p.get('unidade', '-')} | Preço: R$ {p.get('preco', 0):.2f} | Estoque: {p.get('estoque', 0)}")
    
    # ========== ORDENS DE SERVIÇO ==========
    ordens = await db.ordens_servico.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nORDENS DE SERVIÇO ({len(ordens)} registros)\n{'='*40}")
    abertas = [o for o in ordens if o.get("status") in ["aberta", "em_andamento"]]
    concluidas = [o for o in ordens if o.get("status") == "concluida"]
    context_parts.append(f"RESUMO: Abertas/Em andamento: {len(abertas)} | Concluídas: {len(concluidas)}")
    for o in ordens:
        context_parts.append(f"- OS Nº {o.get('numero')} | Descrição: {o.get('descricao', '-')[:60]} | Cliente: {o.get('cliente_nome', '-')} | Valor: R$ {o.get('valor_total', 0):.2f} | Status: {o.get('status', '-').upper()} | Tipo Financeiro: {o.get('tipo_financeiro', '-')}")
    
    # ========== PLANO DE CONTAS ==========
    plano_contas = await db.plano_contas.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nPLANO DE CONTAS ({len(plano_contas)} registros)\n{'='*40}")
    for p in plano_contas:
        tipo = "📥 RECEITA" if p.get("tipo") == "receita" else "📤 DESPESA"
        context_parts.append(f"- {tipo} | Código: {p.get('codigo', '-')} | Nome: {p.get('nome')} | Pai: {p.get('pai_nome', 'Raiz')}")
    
    # ========== CENTROS DE CUSTO ==========
    centros_custo = await db.centros_custo.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCENTROS DE CUSTO ({len(centros_custo)} registros)\n{'='*40}")
    for c in centros_custo:
        context_parts.append(f"- Código: {c.get('codigo', '-')} | Nome: {c.get('nome')} | Descrição: {c.get('descricao', '-')}")
    
    # ========== FORMAS DE PAGAMENTO ==========
    formas_pagamento = await db.formas_pagamento.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nFORMAS DE PAGAMENTO ({len(formas_pagamento)} registros)\n{'='*40}")
    for f in formas_pagamento:
        context_parts.append(f"- Nome: {f.get('nome')} | Descrição: {f.get('descricao', '-')}")
    
    # ========== ALUGUÉIS DE MÁQUINAS ==========
    alugueis = await db.alugueis.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nALUGUÉIS DE MÁQUINAS ({len(alugueis)} registros)\n{'='*40}")
    ativos = [a for a in alugueis if a.get("status") == "ativo"]
    finalizados = [a for a in alugueis if a.get("status") == "finalizado"]
    total_alugueis = sum(a.get("valor_total", 0) for a in alugueis)
    context_parts.append(f"RESUMO: Ativos: {len(ativos)} | Finalizados: {len(finalizados)} | Valor total: R$ {total_alugueis:.2f}")
    for a in alugueis:
        context_parts.append(f"- Máquina: {a.get('maquina_nome', '-')} | Cliente: {a.get('cliente_nome', '-')} | Tel: {a.get('cliente_telefone', '-')} | Período: {a.get('tipo_periodo', '-')} | Valor: R$ {a.get('valor_total', 0):.2f} | Status: {a.get('status', '-').upper()} | Entrega: {a.get('data_entrega', '-')} | Vencimento: {a.get('data_vencimento', '-')}")
    
    # ========== LOGS DE AUDITORIA (ÚLTIMOS) ==========
    audit_logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    context_parts.append(f"\n\n{'='*40}\nÚLTIMAS ATIVIDADES/AUDITORIA ({len(audit_logs)} registros)\n{'='*40}")
    for a in audit_logs:
        context_parts.append(f"- {a.get('created_at', '-')[:16] if a.get('created_at') else '-'} | Usuário: {a.get('user_name', '-')} | Ação: {a.get('action', '-')} | Módulo: {a.get('module', '-')}")
    
    # ========== RESUMO FINANCEIRO GERAL ==========
    context_parts.append(f"\n\n{'='*60}")
    context_parts.append("RESUMO FINANCEIRO GERAL")
    context_parts.append(f"{'='*60}")
    context_parts.append(f"Total gasto em manutenções: R$ {total_valor:.2f}")
    context_parts.append(f"Contas a pagar pendentes: R$ {total_pendente_pagar:.2f}")
    context_parts.append(f"Contas a receber pendentes: R$ {total_pendente_receber:.2f}")
    context_parts.append(f"Total em aluguéis: R$ {total_alugueis:.2f}")
    saldo_projetado = total_pendente_receber - total_pendente_pagar
    context_parts.append(f"Saldo projetado (a receber - a pagar): R$ {saldo_projetado:.2f}")
    
    return "\n".join(context_parts)

@api_router.post("/chatbot/ask", response_model=ChatResponse)
async def chatbot_ask(chat: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Endpoint do chatbot que responde perguntas sobre a plataforma"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    try:
        # Coletar contexto COMPLETO da plataforma
        platform_context = await get_full_platform_context()
        
        # Sistema message com contexto completo
        system_message = f"""Você é o assistente virtual inteligente da CRA Construtora.
Você tem ACESSO COMPLETO E TOTAL a TODAS as informações do banco de dados da plataforma.

DADOS COMPLETOS DO SISTEMA (ATUALIZADOS EM TEMPO REAL):
{platform_context}

SUAS CAPACIDADES:
- Você conhece TODOS os usuários, máquinas, manutenções, estoque, obras, contas, ordens de serviço, aluguéis, etc.
- Você pode calcular totais, médias, fazer comparações e análises
- Você sabe quais itens estão com estoque baixo
- Você conhece o histórico financeiro completo
- Você pode identificar padrões e fazer recomendações

INSTRUÇÕES DE FORMATAÇÃO (MUITO IMPORTANTE):
1. SEMPRE responda em português brasileiro
2. Use QUEBRAS DE LINHA para separar parágrafos e seções
3. Use listas com "•" para enumerar itens (não use asteriscos)
4. Formate valores monetários como R$ 1.234,56
5. Organize informações em seções claras quando houver muitos dados
6. NÃO use markdown com asteriscos (**, *)
7. Seja claro, direto e bem organizado
8. Separe diferentes tipos de informação com linhas em branco

EXEMPLO DE FORMATAÇÃO CORRETA:
Resumo do Estoque:

• Item 1: 50 unidades - R$ 25,90 cada
• Item 2: 30 unidades - R$ 15,00 cada

Total de itens: 2
Valor total em estoque: R$ 1.745,00

INSTRUÇÕES DE CONTEÚDO:
1. SEMPRE use os dados REAIS fornecidos acima
2. Seja ESPECÍFICO - cite nomes, valores, datas exatos
3. Se não encontrar a informação, diga claramente
4. Faça cálculos quando necessário
5. Seja proativo em fornecer informações úteis relacionadas
"""
        
        # Inicializar chat com Gemini
        llm_key = os.environ.get("EMERGENT_LLM_KEY")
        
        llm_chat = LlmChat(
            api_key=llm_key,
            session_id=f"chatbot-{current_user['id']}-{datetime.now().strftime('%Y%m%d%H%M')}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Enviar mensagem
        user_message = UserMessage(text=chat.message)
        response = await llm_chat.send_message(user_message)
        
        return ChatResponse(
            response=response,
            context_used=["todos_os_modulos"]
        )
        
    except Exception as e:
        logging.error(f"Erro no chatbot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")

@api_router.post("/chatbot/ask-with-files", response_model=ChatResponse)
async def chatbot_ask_with_files(
    message: str = Form(...),
    module: str = Form("gerenciamento"),
    files: List[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Endpoint do chatbot que processa arquivos anexados com extração de conteúdo"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import io
    
    try:
        # Processar arquivos anexados
        files_info = []
        file_contents = []
        
        if files:
            for file in files:
                content = await file.read()
                file_size = len(content)
                filename = file.filename or "arquivo_sem_nome"
                content_type = file.content_type or ""
                
                # Informações básicas do arquivo
                files_info.append({
                    "nome": filename,
                    "tipo": content_type,
                    "tamanho": f"{file_size / 1024:.1f} KB"
                })
                
                # Extrair conteúdo baseado no tipo de arquivo
                extracted_content = None
                
                # Arquivos de texto
                if 'text' in content_type or filename.endswith(('.txt', '.csv', '.json', '.xml', '.md', '.log')):
                    try:
                        text_content = content.decode('utf-8')
                        extracted_content = f"📄 CONTEÚDO DE {filename}:\n{text_content[:5000]}"
                        if len(text_content) > 5000:
                            extracted_content += "\n[...conteúdo truncado...]"
                    except:
                        extracted_content = f"⚠️ Arquivo {filename}: não foi possível decodificar como texto"
                
                # PDFs - extrair texto
                elif filename.lower().endswith('.pdf') or 'pdf' in content_type:
                    try:
                        from PyPDF2 import PdfReader
                        pdf_reader = PdfReader(io.BytesIO(content))
                        pdf_text = ""
                        for i, page in enumerate(pdf_reader.pages[:10]):  # Máximo 10 páginas
                            page_text = page.extract_text()
                            if page_text:
                                pdf_text += f"\n--- Página {i+1} ---\n{page_text}"
                        if pdf_text.strip():
                            extracted_content = f"📑 CONTEÚDO DO PDF {filename}:{pdf_text[:8000]}"
                            if len(pdf_text) > 8000:
                                extracted_content += "\n[...conteúdo truncado...]"
                        else:
                            extracted_content = f"📑 PDF {filename}: {len(pdf_reader.pages)} páginas (texto não extraível - pode ser imagem/escaneado)"
                    except Exception as pdf_err:
                        extracted_content = f"⚠️ PDF {filename}: erro ao extrair texto ({str(pdf_err)[:100]})"
                
                # Documentos Word
                elif filename.lower().endswith(('.docx', '.doc')):
                    try:
                        from docx import Document
                        doc = Document(io.BytesIO(content))
                        doc_text = "\n".join([para.text for para in doc.paragraphs])
                        if doc_text.strip():
                            extracted_content = f"📝 CONTEÚDO DO DOCUMENTO {filename}:\n{doc_text[:5000]}"
                            if len(doc_text) > 5000:
                                extracted_content += "\n[...conteúdo truncado...]"
                        else:
                            extracted_content = f"📝 Documento {filename}: sem texto extraível"
                    except Exception as doc_err:
                        extracted_content = f"⚠️ Documento {filename}: erro ao extrair ({str(doc_err)[:100]})"
                
                # Planilhas Excel
                elif filename.lower().endswith(('.xlsx', '.xls')):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
                        excel_content = []
                        for sheet_name in wb.sheetnames[:3]:  # Máximo 3 abas
                            sheet = wb[sheet_name]
                            sheet_data = f"\n--- Aba: {sheet_name} ---\n"
                            row_count = 0
                            for row in sheet.iter_rows(max_row=50, values_only=True):  # Máximo 50 linhas
                                row_values = [str(cell) if cell is not None else "" for cell in row]
                                if any(row_values):
                                    sheet_data += " | ".join(row_values) + "\n"
                                    row_count += 1
                            excel_content.append(sheet_data)
                        extracted_content = f"📊 CONTEÚDO DA PLANILHA {filename}:{''.join(excel_content)}"
                    except Exception as xl_err:
                        extracted_content = f"⚠️ Planilha {filename}: erro ao extrair ({str(xl_err)[:100]})"
                
                # Imagens - descrever que é uma imagem
                elif content_type.startswith('image/') or filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
                    try:
                        from PIL import Image
                        img = Image.open(io.BytesIO(content))
                        extracted_content = f"🖼️ IMAGEM {filename}: formato {img.format}, dimensões {img.width}x{img.height} pixels, modo {img.mode}"
                    except:
                        extracted_content = f"🖼️ Imagem {filename}: arquivo de imagem ({file_size / 1024:.1f} KB)"
                
                # Outros arquivos
                else:
                    extracted_content = f"📁 Arquivo {filename}: tipo {content_type or 'desconhecido'} ({file_size / 1024:.1f} KB)"
                
                if extracted_content:
                    file_contents.append(extracted_content)
                
                # Reset file pointer
                await file.seek(0)
        
        # Construir contexto dos arquivos
        files_context = ""
        if files_info:
            files_context = "\n\n═══════════════════════════════════════════════════════════════\n"
            files_context += "ARQUIVOS ANEXADOS PELO USUÁRIO:\n"
            files_context += "═══════════════════════════════════════════════════════════════\n"
            for info in files_info:
                files_context += f"• {info['nome']} ({info['tipo'] or 'tipo desconhecido'}, {info['tamanho']})\n"
            
            if file_contents:
                files_context += "\n" + "\n\n".join(file_contents)
            files_context += "\n═══════════════════════════════════════════════════════════════\n"
        
        # Coletar contexto da plataforma
        platform_context = await get_full_platform_context()
        
        # Sistema message com contexto
        system_message = f"""Você é o assistente virtual inteligente da CRA Construtora.
Você tem ACESSO COMPLETO E TOTAL a TODAS as informações do banco de dados da plataforma.

DADOS COMPLETOS DO SISTEMA:
{platform_context}

{files_context}

SUAS CAPACIDADES:
- Você pode analisar arquivos anexados (PDFs, documentos Word, planilhas Excel, textos)
- Você pode extrair e analisar informações de documentos
- Você pode comparar dados dos arquivos com dados da plataforma
- Você conhece TODOS os usuários, máquinas, manutenções, estoque, obras, contas, etc.

INSTRUÇÕES IMPORTANTES:
1. SEMPRE responda em português brasileiro
2. Use QUEBRAS DE LINHA para separar parágrafos
3. Use listas com "•" para enumerar itens
4. Formate valores monetários como R$ 1.234,56
5. Se o usuário anexou arquivos, ANALISE O CONTEÚDO EXTRAÍDO e faça comentários úteis
6. Se for uma planilha ou documento, resuma as informações principais
7. Se for uma imagem, descreva o que sabe sobre ela
8. NÃO use markdown com asteriscos (**, *)
9. Relacione os dados dos arquivos com os dados da plataforma quando relevante
"""
        
        # Inicializar chat com Gemini
        llm_key = os.environ.get("EMERGENT_LLM_KEY")
        
        llm_chat = LlmChat(
            api_key=llm_key,
            session_id=f"chatbot-files-{current_user['id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Mensagem do usuário
        user_text = message if message else "Analise os arquivos que anexei e me diga o que encontrou"
        if files_info:
            user_text += f"\n\n[Arquivos anexados: {', '.join([f['nome'] for f in files_info])}]"
        
        user_message = UserMessage(text=user_text)
        response = await llm_chat.send_message(user_message)
        
        return ChatResponse(
            response=response,
            context_used=["arquivos", "todos_os_modulos"]
        )
        
    except Exception as e:
        logging.error(f"Erro no chatbot com arquivos: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivos: {str(e)}")


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

@api_router.get("/export/categories/{module}")
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
        # Criar tabela com os dados
        if category == "machines":
            headers = ["Nome", "Placa", "Marca", "Modelo", "Status"]
            table_data = [headers]
            for item in data:
                status = "Operacional" if item.get("status") == "operational" else "Em manutenção"
                table_data.append([
                    item.get("name", "-")[:30],
                    item.get("plate", "-"),
                    item.get("brand", "-")[:15],
                    item.get("model", "-")[:15],
                    status
                ])
        elif category == "maintenances":
            headers = ["Peça", "Tipo", "Valor", "Data", "Troca Óleo"]
            table_data = [headers]
            for item in data:
                tipo = "Preventiva" if item.get("maintenance_type") == "preventiva" else "Corretiva"
                table_data.append([
                    item.get("part_name", "-")[:25],
                    tipo,
                    f"R$ {item.get('part_value', 0):.2f}",
                    item.get("replacement_date", "-")[:10] if item.get("replacement_date") else "-",
                    "Sim" if item.get("is_oil_change") else "Não"
                ])
        elif category == "stock_items":
            headers = ["Nome", "Código", "Categoria", "Qtd", "Mínimo", "Preço Un."]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("name", "-")[:20],
                    item.get("code", "-"),
                    item.get("category", "-")[:15],
                    str(item.get("quantity", 0)),
                    str(item.get("min_quantity", 0)),
                    f"R$ {item.get('unit_price', 0):.2f}"
                ])
        elif category == "obras":
            headers = ["Nome", "Local", "Status", "Início", "Fim"]
            table_data = [headers]
            for item in data:
                status_map = {"em_andamento": "Em andamento", "concluida": "Concluída", "pausada": "Pausada"}
                table_data.append([
                    item.get("name", "-")[:25],
                    item.get("location", "-")[:20],
                    status_map.get(item.get("status", ""), item.get("status", "-")),
                    item.get("start_date", "-")[:10] if item.get("start_date") else "-",
                    item.get("end_date", "-")[:10] if item.get("end_date") else "-"
                ])
        elif category == "contas_pagar":
            headers = ["Descrição", "Valor", "Vencimento", "Status", "Fornecedor"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("descricao", "-")[:25],
                    f"R$ {item.get('valor', 0):.2f}",
                    item.get("data_vencimento", "-")[:10] if item.get("data_vencimento") else "-",
                    item.get("status", "-").upper(),
                    item.get("fornecedor_nome", "-")[:15]
                ])
        elif category == "contas_receber":
            headers = ["Descrição", "Valor", "Vencimento", "Status", "Cliente"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("descricao", "-")[:25],
                    f"R$ {item.get('valor', 0):.2f}",
                    item.get("data_vencimento", "-")[:10] if item.get("data_vencimento") else "-",
                    item.get("status", "-").upper(),
                    item.get("cliente_nome", "-")[:15]
                ])
        elif category == "cadastros":
            headers = ["Nome/Razão", "Tipo", "CPF/CNPJ", "Telefone", "Cidade"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("nome_razao", "-")[:25],
                    item.get("tipo", "-").upper(),
                    item.get("cpf_cnpj", "-"),
                    item.get("telefone", "-"),
                    item.get("cidade", "-")[:15]
                ])
        elif category == "ordens_servico":
            headers = ["Nº OS", "Descrição", "Cliente", "Valor", "Status"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    str(item.get("numero", "-")),
                    item.get("descricao", "-")[:25],
                    item.get("cliente_nome", "-")[:15],
                    f"R$ {item.get('valor_total', 0):.2f}",
                    item.get("status", "-").upper()
                ])
        elif category == "alugueis":
            headers = ["Máquina", "Cliente", "Valor", "Status", "Vencimento"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("maquina_nome", "-")[:20],
                    item.get("cliente_nome", "-")[:15],
                    f"R$ {item.get('valor_total', 0):.2f}",
                    item.get("status", "-").upper(),
                    item.get("data_vencimento", "-")[:10] if item.get("data_vencimento") else "-"
                ])
        elif category == "produtos_admin":
            headers = ["Código", "Descrição", "Unidade", "Preço", "Estoque"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("codigo", "-"),
                    item.get("descricao", "-")[:25],
                    item.get("unidade", "-"),
                    f"R$ {item.get('preco', 0):.2f}",
                    str(item.get("estoque", 0))
                ])
        elif category == "plano_contas":
            headers = ["Código", "Nome", "Tipo", "Conta Pai"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("codigo", "-"),
                    item.get("nome", "-")[:30],
                    "Receita" if item.get("tipo") == "receita" else "Despesa",
                    item.get("pai_nome", "Raiz")[:20]
                ])
        elif category == "centros_custo":
            headers = ["Código", "Nome", "Descrição"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("codigo", "-"),
                    item.get("nome", "-")[:30],
                    item.get("descricao", "-")[:40]
                ])
        elif category == "formas_pagamento":
            headers = ["Nome", "Descrição"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("nome", "-")[:30],
                    item.get("descricao", "-")[:50]
                ])
        elif category == "categories":
            headers = ["Nome", "Descrição"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("name", "-")[:30],
                    item.get("description", "-")[:50]
                ])
        elif category == "stock_movements":
            headers = ["Tipo", "Quantidade", "Motivo", "Data"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    "ENTRADA" if item.get("movement_type") == "entrada" else "SAÍDA",
                    str(item.get("quantity", 0)),
                    item.get("reason", "-")[:30],
                    item.get("created_at", "-")[:10] if item.get("created_at") else "-"
                ])
        elif category == "usage_logs":
            headers = ["Máquina ID", "Horas", "Data", "Observações"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("machine_id", "-")[:15] if item.get("machine_id") else "-",
                    str(item.get("hours", 0)),
                    item.get("created_at", "-")[:10] if item.get("created_at") else "-",
                    item.get("notes", "-")[:30]
                ])
        elif category == "users":
            headers = ["Nome", "Email", "Tipo", "Criado em"]
            table_data = [headers]
            for item in data:
                role_map = {"admin": "Administrador", "gerenciamento": "Gerenciamento", "administrativo": "Administrativo", "ambos": "Ambos"}
                table_data.append([
                    item.get("name", "-")[:25],
                    item.get("email", "-")[:30],
                    role_map.get(item.get("role", ""), item.get("role", "-")),
                    item.get("created_at", "-")[:10] if item.get("created_at") else "-"
                ])
        elif category == "audit_logs":
            headers = ["Data", "Usuário", "Ação", "Módulo"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("created_at", "-")[:16] if item.get("created_at") else "-",
                    item.get("user_name", "-")[:20],
                    item.get("action", "-")[:30],
                    item.get("module", "-")[:15]
                ])
        else:
            # Fallback genérico
            headers = ["ID", "Dados"]
            table_data = [headers]
            for item in data:
                table_data.append([
                    item.get("id", "-")[:20] if item.get("id") else "-",
                    str(item)[:60]
                ])
        
        # Criar e estilizar a tabela
        col_widths = [doc.width / len(headers)] * len(headers)
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.89, 0.10, 0.10)),  # Vermelho CRA
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
    
    # Rodapé
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph("CRA Construtora - Sistema de Gestão Empresarial", footer_style))
    elements.append(Paragraph(f"Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

@api_router.get("/export/pdf/{category}")
async def export_pdf(category: str, current_user: dict = Depends(get_current_user)):
    """Exporta dados de uma categoria em PDF com filtros"""
    
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
        "contas_pagar_quitada": {"collection": "contas_pagar", "title": "Contas a Pagar Quitadas", "filter": {"status": "quitada"}},
        "contas_pagar_vencidas": {"collection": "contas_pagar", "title": "Contas a Pagar Vencidas", "filter": {"status": "em_aberto", "data_vencimento": {"$lt": datetime.now().strftime("%Y-%m-%d")}}},
        
        # Contas a Receber
        "contas_receber": {"collection": "contas_receber", "title": "Contas a Receber", "filter": {}},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas a Receber Pendentes", "filter": {"status": "em_aberto"}},
        "contas_receber_quitada": {"collection": "contas_receber", "title": "Contas a Receber Recebidas", "filter": {"status": "quitada"}},
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
    query_filter = config["filter"]
    
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

@api_router.post("/export/combined")
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
        
        items = await db[config["collection"]].find(query_filter, {"_id": 0}).to_list(1000)
        if items:
            all_data.append({
                "title": config["title"],
                "items": items,
                "category": cat_id
            })
    
    if not all_data:
        raise HTTPException(status_code=400, detail="Nenhum dado encontrado para exportar")
    
    # Gerar PDF combinado
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#E31A1A'),
        spaceAfter=12
    )
    
    elements = []
    
    for section in all_data:
        # Título da seção
        elements.append(Paragraph(section["title"], title_style))
        elements.append(Spacer(1, 10))
        
        # Tabela de dados
        if section["items"]:
            # Pegar as colunas do primeiro item
            sample = section["items"][0]
            columns = list(sample.keys())[:6]  # Limitar a 6 colunas
            
            # Header
            table_data = [columns]
            
            # Dados
            for item in section["items"][:50]:  # Limitar a 50 itens por seção
                row = [str(item.get(col, ""))[:30] for col in columns]
                table_data.append(row)
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E31A1A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(table)
        
        elements.append(PageBreak())
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=CRA_Relatorio_Combinado_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        }
    )

# Endpoint para listar itens específicos para filtro de exportação
@api_router.get("/export/items/{collection}")
async def get_export_items(collection: str, status: str = None, current_user: dict = Depends(get_current_user)):
    """Retorna itens de uma coleção para seleção em exportação"""
    valid_collections = {
        "plano_contas": {"name_field": "nome", "id_field": "id", "collection": "plano_contas"},
        "centros_custo": {"name_field": "nome", "id_field": "id", "collection": "centros_custo"},
        "fleets": {"name_field": "name", "id_field": "id", "collection": "fleets"},
        "cadastros": {"name_field": "nome", "id_field": "id", "collection": "cadastros"},
        "formas_pagamento": {"name_field": "nome", "id_field": "id", "collection": "formas_pagamento"},
        "contas_bancarias": {"name_field": "nome", "id_field": "id", "collection": "contas_bancarias"},
        # Contas a Pagar
        "contas_pagar": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "extra_fields": ["valor", "data_vencimento", "fornecedor_nome"]},
        "contas_pagar_pendente": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "fornecedor_nome"]},
        "contas_pagar_quitadas": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "filter": {"status": "quitada"}, "extra_fields": ["valor", "data_vencimento", "fornecedor_nome"]},
        "contas_pagar_vencidas": {"name_field": "descricao", "id_field": "id", "collection": "contas_pagar", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "fornecedor_nome"], "vencidas": True},
        # Contas a Receber
        "contas_receber": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "extra_fields": ["valor", "data_vencimento", "cliente_nome"]},
        "contas_receber_pendente": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "cliente_nome"]},
        "contas_receber_recebidas": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "filter": {"status": "quitada"}, "extra_fields": ["valor", "data_vencimento", "cliente_nome"]},
        "contas_receber_vencidas": {"name_field": "descricao", "id_field": "id", "collection": "contas_receber", "filter": {"status": "em_aberto"}, "extra_fields": ["valor", "data_vencimento", "cliente_nome"], "vencidas": True},
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


@api_router.get("/export/individual/{category}/{item_id}")
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

@api_router.post("/export/individual-multiple")
async def export_multiple_individual_items(data: MultipleItemsExport, current_user: dict = Depends(get_current_user)):
    """Exporta múltiplos itens individuais em um único PDF - cada item com detalhes completos"""
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
    items = await db[config["collection"]].find({"id": {"$in": data.item_ids}}, {"_id": 0}).to_list(100)
    
    if not items:
        raise HTTPException(status_code=404, detail="Nenhum item encontrado")
    
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
@api_router.get("/export/recibo/{category}/{item_id}")
async def export_recibo(category: str, item_id: str, empresa: str = "locadora", current_user: dict = Depends(get_current_user)):
    """Gera um recibo de pagamento em PDF"""
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
    
    # Dados do cliente/fornecedor
    pessoa_nome = item.get("fornecedor_nome") or item.get("cliente_nome") or "-"
    pessoa_doc = item.get("fornecedor_cnpj") or item.get("cliente_documento") or item.get("cliente_cnpj") or "-"
    pessoa_telefone = item.get("fornecedor_telefone") or item.get("cliente_telefone") or "-"
    pessoa_endereco = item.get("fornecedor_endereco") or item.get("cliente_endereco") or "-"
    
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
    
    # Valor
    valor = item.get("valor_final") or item.get("valor") or item.get("valor_aluguel") or 0
    valor_str = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    elements.append(Paragraph(f"Recebi(emos) de <b>{pessoa_nome}</b> a importância de:", ParagraphStyle('Extenso', fontSize=10)))
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
    data_venc = item.get("data_vencimento", "-")
    data_pag = item.get("data_pagamento") or item.get("data_recebimento") or "-"
    obs = item.get("observacoes", "-")
    
    # Estilo com word-wrap para textos longos
    detail_value_style = ParagraphStyle('DetailValue', fontSize=9, leading=12, wordWrap='CJK')
    detail_label_style = ParagraphStyle('DetailLabel', fontSize=9, fontName='Helvetica-Bold')
    
    detail_data = [
        [Paragraph("Descrição", detail_label_style), Paragraph(descricao if descricao else "-", detail_value_style)],
        [Paragraph("Data de Vencimento", detail_label_style), Paragraph(data_venc if data_venc else "-", detail_value_style)],
        [Paragraph("Data de Pagamento", detail_label_style), Paragraph(data_pag if data_pag else "-", detail_value_style)],
        [Paragraph("Forma de Pagamento", detail_label_style), Paragraph(forma_pag if forma_pag else "-", detail_value_style)],
        [Paragraph("Plano de Contas", detail_label_style), Paragraph(plano_contas if plano_contas else "-", detail_value_style)],
        [Paragraph("Centro de Custo", detail_label_style), Paragraph(centro_custo if centro_custo else "-", detail_value_style)],
        [Paragraph("Observações", detail_label_style), Paragraph(obs if obs else "-", detail_value_style)],
    ]
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
    
    # Assinatura
    elements.append(Paragraph("_" * 50, ParagraphStyle('Linha', alignment=1)))
    elements.append(Paragraph(empresa_nome, ParagraphStyle('Assinatura', fontSize=10, alignment=1)))
    
    doc.build(elements)
    buffer.seek(0)
    
    await create_audit_log(current_user, "export", "recibo", item_id, f"Recibo: {item.get('descricao', item_id)}")
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CRA_Recibo_{item_id[:8]}.pdf"}
    )


# Endpoint para gerar Duplicata/Recibo Fatura
@api_router.get("/export/duplicata/{category}/{item_id}")
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
    
    # Linha 1: Valor, Número, Vencimento
    row1_data = [
        [Paragraph("VALOR", label_style), Paragraph("Nº DOCUMENTO", label_style), Paragraph("VENCIMENTO", label_style)],
        [Paragraph(f"<b>{valor_str}</b>", ParagraphStyle('V', fontSize=14)), 
         Paragraph(item_id[:12].upper(), value_style), 
         Paragraph(f"<b>{item.get('data_vencimento', '-')}</b>", ParagraphStyle('Venc', fontSize=11))]
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
@api_router.get("/export/extrato-bancario/{conta_id}")
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
    
    # Definir headers e dados baseado na categoria
    if category in ["contas_pagar", "contas_receber"]:
        headers = ["Descrição", "Valor", "Vencimento", "Status", "Fornecedor/Cliente", "Centro de Custo", "Plano de Contas"]
        worksheet.set_column(0, 0, 30)  # Descrição
        worksheet.set_column(1, 1, 15)  # Valor
        worksheet.set_column(2, 2, 12)  # Vencimento
        worksheet.set_column(3, 3, 12)  # Status
        worksheet.set_column(4, 4, 25)  # Fornecedor
        worksheet.set_column(5, 5, 20)  # Centro de Custo
        worksheet.set_column(6, 6, 20)  # Plano de Contas
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("descricao", ""), cell_format)
            worksheet.write(row, 1, float(item.get("valor", 0)), money_format)
            worksheet.write(row, 2, item.get("data_vencimento", "")[:10] if item.get("data_vencimento") else "", cell_format)
            worksheet.write(row, 3, item.get("status", "").capitalize(), cell_format)
            worksheet.write(row, 4, item.get("fornecedor_nome", "") or item.get("cliente_nome", ""), cell_format)
            worksheet.write(row, 5, item.get("centro_custo_nome", ""), cell_format)
            worksheet.write(row, 6, item.get("plano_contas_nome", ""), cell_format)
    
    elif category == "machines":
        headers = ["Nome", "Placa", "Marca", "Modelo", "Ano", "Status", "Categoria"]
        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 12)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
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
        headers = ["Nome/Razão", "CPF/CNPJ", "Tipo", "Telefone", "Email", "Cidade", "Status"]
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 18)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("nome_razao", ""), cell_format)
            worksheet.write(row, 1, item.get("cpf_cnpj", ""), cell_format)
            worksheet.write(row, 2, item.get("tipo_cadastro", "").capitalize(), cell_format)
            worksheet.write(row, 3, item.get("telefone", "") or item.get("celular", ""), cell_format)
            worksheet.write(row, 4, item.get("email", ""), cell_format)
            worksheet.write(row, 5, item.get("cidade", ""), cell_format)
            worksheet.write(row, 6, item.get("status", "").capitalize(), cell_format)
    
    elif category == "alugueis":
        headers = ["Nº", "Máquina", "Cliente", "Valor", "Data Entrega", "Vencimento", "Status", "Contrato"]
        worksheet.set_column(0, 0, 8)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 25)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        for row, item in enumerate(data, 1):
            worksheet.write(row, 0, item.get("numero", ""), cell_format)
            worksheet.write(row, 1, item.get("maquina_nome", ""), cell_format)
            worksheet.write(row, 2, item.get("cliente_nome", ""), cell_format)
            worksheet.write(row, 3, float(item.get("valor", 0)), money_format)
            worksheet.write(row, 4, item.get("data_entrega", "")[:10] if item.get("data_entrega") else "", cell_format)
            worksheet.write(row, 5, item.get("data_vencimento", "")[:10] if item.get("data_vencimento") else "", cell_format)
            worksheet.write(row, 6, item.get("status", "").capitalize(), cell_format)
            worksheet.write(row, 7, item.get("numero_contrato", ""), cell_format)
    
    else:
        # Genérico: pegar as chaves do primeiro item
        if data:
            keys = [k for k in data[0].keys() if k not in ["_id", "password"]]
            for col, key in enumerate(keys):
                worksheet.write(0, col, key.replace("_", " ").title(), header_format)
            for row, item in enumerate(data, 1):
                for col, key in enumerate(keys):
                    value = item.get(key, "")
                    if isinstance(value, (int, float)):
                        worksheet.write(row, col, value, cell_format)
                    else:
                        worksheet.write(row, col, str(value)[:50] if value else "", cell_format)
    
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

@api_router.get("/export/excel/{category}")
async def export_excel(category: str, current_user: dict = Depends(get_current_user)):
    """Exporta dados de uma categoria em Excel"""
    
    category_configs = {
        "machines": {"collection": "machines", "title": "Maquinas", "filter": {}},
        "maintenances": {"collection": "maintenances", "title": "Manutencoes", "filter": {}},
        "stock_items": {"collection": "stock_items", "title": "Estoque", "filter": {}},
        "obras": {"collection": "obras", "title": "Obras", "filter": {}},
        "contas_pagar": {"collection": "contas_pagar", "title": "Contas_a_Pagar", "filter": {}},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Pendentes", "filter": {"status": "pendente"}},
        "contas_receber": {"collection": "contas_receber", "title": "Contas_a_Receber", "filter": {}},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas_a_Receber_Pendentes", "filter": {"status": "pendente"}},
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
    collection = db[config["collection"]]
    data = await collection.find(config["filter"], {"_id": 0}).to_list(5000)
    
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

@api_router.get("/export/ofx/{category}")
async def export_ofx(category: str, current_user: dict = Depends(get_current_user)):
    """Exporta dados financeiros em formato OFX"""
    
    valid_categories = {
        "contas_pagar": {"collection": "contas_pagar", "title": "Contas_a_Pagar", "type": "pagar"},
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas_a_Pagar_Pendentes", "type": "pagar", "filter": {"status": "pendente"}},
        "contas_receber": {"collection": "contas_receber", "title": "Contas_a_Receber", "type": "receber"},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas_a_Receber_Pendentes", "type": "receber", "filter": {"status": "pendente"}},
    }
    
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail="OFX só está disponível para contas a pagar/receber")
    
    config = valid_categories[category]
    query_filter = config.get("filter", {})
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

ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@api_router.post("/attachments/upload")
async def upload_attachment(
    file: UploadFile = File(...),
    entity_type: str = Form(...),  # contas_pagar, contas_receber, ordens_servico, etc
    entity_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload de anexo para uma entidade (conta, OS, etc)"""
    
    # Validar extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Tipo de arquivo não permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Validar tamanho
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 10MB")
    
    # Gerar nome único
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    # Salvar arquivo
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Criar registro do anexo
    attachment = {
        "id": file_id,
        "filename": file.filename,
        "stored_filename": filename,
        "file_type": file.content_type,
        "file_size": len(contents),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "uploaded_by": current_user["id"],
        "uploaded_by_name": current_user["name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.attachments.insert_one(attachment)
    
    # Atualizar a entidade com referência ao anexo
    collection = db[entity_type]
    await collection.update_one(
        {"id": entity_id},
        {"$push": {"anexos": file_id}}
    )
    
    # Auditoria
    await create_audit_log(
        user=current_user,
        action="anexar",
        entity_type=f"arquivo em {entity_type}",
        entity_id=entity_id,
        entity_name=file.filename,
        details=f"Arquivo anexado: {file.filename}",
        module="Administrativo"
    )
    
    attachment.pop("_id", None)
    return {"message": "Arquivo enviado com sucesso", "attachment": attachment}

@api_router.get("/attachments/download/{file_id}")
async def download_attachment(file_id: str, current_user: dict = Depends(get_current_user)):
    """Download de um anexo"""
    attachment = await db.attachments.find_one({"id": file_id}, {"_id": 0})
    if not attachment:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    file_path = UPLOAD_DIR / attachment["stored_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=attachment["filename"],
        media_type=attachment.get("file_type", "application/octet-stream")
    )

@api_router.get("/attachments/{entity_type}/{entity_id}")
async def get_attachments(entity_type: str, entity_id: str, current_user: dict = Depends(get_current_user)):
    """Lista anexos de uma entidade"""
    attachments = await db.attachments.find(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return attachments

@api_router.delete("/attachments/{file_id}")
async def delete_attachment(file_id: str, current_user: dict = Depends(get_current_user)):
    """Remove um anexo"""
    attachment = await db.attachments.find_one({"id": file_id}, {"_id": 0})
    if not attachment:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    # Remover arquivo físico
    file_path = UPLOAD_DIR / attachment["stored_filename"]
    if file_path.exists():
        file_path.unlink()
    
    # Remover registro do banco
    await db.attachments.delete_one({"id": file_id})
    
    # Remover referência da entidade
    collection = db[attachment["entity_type"]]
    await collection.update_one(
        {"id": attachment["entity_id"]},
        {"$pull": {"anexos": file_id}}
    )
    
    # Auditoria
    await create_audit_log(
        user=current_user,
        action="remover anexo",
        entity_type=f"arquivo de {attachment['entity_type']}",
        entity_id=attachment["entity_id"],
        entity_name=attachment["filename"],
        details=f"Anexo removido: {attachment['filename']}",
        module="Administrativo"
    )
    
    return {"message": "Anexo removido com sucesso"}


# ============ TASK/MESSAGE SYSTEM ============

# Directory for task attachments (100MB max)
TASK_UPLOAD_DIR = ROOT_DIR / "task_uploads"
TASK_UPLOAD_DIR.mkdir(exist_ok=True)

class TaskCreate(BaseModel):
    target_system: str  # "gerenciamento" or "administrativo"
    priority: str  # "baixa", "media", "alta"
    title: str
    message: str

class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    target_system: str
    priority: str
    title: str
    message: str
    attachments: List[dict] = []
    created_by_id: str
    created_by_name: str
    created_at: str
    read: bool = False
    read_at: Optional[str] = None
    read_by: Optional[str] = None

@api_router.post("/admin-panel/tasks")
async def create_task(
    task: TaskCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new task/message for a specific system"""
    current_user = await get_current_user(credentials)
    
    if current_user.get("role") not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar tarefas")
    
    if task.target_system not in ["gerenciamento", "administrativo"]:
        raise HTTPException(status_code=400, detail="Sistema alvo inválido")
    
    if task.priority not in ["baixa", "media", "alta"]:
        raise HTTPException(status_code=400, detail="Prioridade inválida")
    
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    task_doc = {
        "id": task_id,
        "target_system": task.target_system,
        "priority": task.priority,
        "title": task.title,
        "message": task.message,
        "attachments": [],
        "created_by_id": current_user["id"],
        "created_by_name": current_user["name"],
        "created_at": now,
        "read": False,
        "read_at": None,
        "read_by": None
    }
    
    await db.tasks.insert_one(task_doc)
    
    # Auditoria
    await create_audit_log(
        user=current_user,
        action="criar tarefa",
        entity_type="tarefa",
        entity_id=task_id,
        entity_name=task.title,
        details=f"Tarefa criada para {task.target_system} - Prioridade: {task.priority}",
        module="Painel Admin"
    )
    
    task_doc.pop("_id", None)
    return task_doc

@api_router.post("/admin-panel/tasks/{task_id}/attachments")
async def upload_task_attachment(
    task_id: str,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload attachment to a task (max 100MB)"""
    current_user = await get_current_user(credentials)
    
    if current_user.get("role") not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Apenas administradores podem adicionar anexos")
    
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    # Read file content
    content = await file.read()
    
    # Check file size (100MB max)
    max_size = 100 * 1024 * 1024  # 100MB
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 100MB")
    
    # Create task directory
    task_dir = TASK_UPLOAD_DIR / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    ext = Path(file.filename).suffix if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = task_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Add attachment info to task
    attachment = {
        "id": str(uuid.uuid4()),
        "original_name": file.filename,
        "filename": unique_filename,
        "content_type": file.content_type,
        "size": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tasks.update_one(
        {"id": task_id},
        {"$push": {"attachments": attachment}}
    )
    
    return {"message": "Anexo adicionado com sucesso", "attachment": attachment}

@api_router.get("/admin-panel/tasks")
async def list_all_tasks(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List all tasks (admin only)"""
    current_user = await get_current_user(credentials)
    
    if current_user.get("role") not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Apenas administradores podem ver todas as tarefas")
    
    tasks = await db.tasks.find().sort("created_at", -1).to_list(1000)
    
    for task in tasks:
        task.pop("_id", None)
    
    return tasks

@api_router.get("/tasks")
async def list_tasks_for_system(
    system: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List tasks for a specific system"""
    current_user = await get_current_user(credentials)
    
    if system not in ["gerenciamento", "administrativo"]:
        raise HTTPException(status_code=400, detail="Sistema inválido")
    
    tasks = await db.tasks.find({"target_system": system}).sort("created_at", -1).to_list(1000)
    
    for task in tasks:
        task.pop("_id", None)
    
    return tasks

@api_router.get("/tasks/unread-count")
async def get_unread_task_count(
    system: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get count of unread tasks for a system"""
    await get_current_user(credentials)
    
    if system not in ["gerenciamento", "administrativo"]:
        raise HTTPException(status_code=400, detail="Sistema inválido")
    
    count = await db.tasks.count_documents({"target_system": system, "read": False})
    
    return {"count": count}

@api_router.patch("/tasks/{task_id}/read")
async def mark_task_as_read(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark a task as read"""
    current_user = await get_current_user(credentials)
    
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db.tasks.update_one(
        {"id": task_id},
        {"$set": {"read": True, "read_at": now, "read_by": current_user["name"]}}
    )
    
    return {"message": "Tarefa marcada como lida"}

@api_router.get("/tasks/{task_id}/attachments/{filename}")
async def download_task_attachment(
    task_id: str,
    filename: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Download a task attachment"""
    await get_current_user(credentials)
    
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    # Find attachment
    attachment = None
    for att in task.get("attachments", []):
        if att["filename"] == filename:
            attachment = att
            break
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    file_path = TASK_UPLOAD_DIR / task_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=attachment["original_name"],
        media_type=attachment.get("content_type", "application/octet-stream")
    )

@api_router.delete("/admin-panel/tasks/{task_id}")
async def delete_task(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a task (admin only)"""
    current_user = await get_current_user(credentials)
    
    if current_user.get("role") not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir tarefas")
    
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    # Delete attachments directory
    task_dir = TASK_UPLOAD_DIR / task_id
    if task_dir.exists():
        import shutil
        shutil.rmtree(task_dir)
    
    await db.tasks.delete_one({"id": task_id})
    
    # Auditoria
    await create_audit_log(
        user=current_user,
        action="excluir tarefa",
        entity_type="tarefa",
        entity_id=task_id,
        entity_name=task["title"],
        details=f"Tarefa excluída: {task['title']}",
        module="Painel Admin"
    )
    
    return {"message": "Tarefa excluída com sucesso"}


# ============ RH SYSTEM (RECURSOS HUMANOS) ============
# Movido para: /app/backend/routes/rh.py
# Incluído via: api_router.include_router(rh_router)

# ============ STORAGE SYSTEM (FILE MANAGER) ============

# Directory for storage system
STORAGE_DIR = ROOT_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

class FolderCreate(BaseModel):
    name: str
    parent_path: str = "/"
    password: Optional[str] = None  # Senha opcional para proteger a pasta

class FolderPasswordCheck(BaseModel):
    path: str
    password: str

class FolderPasswordSet(BaseModel):
    path: str
    password: Optional[str] = None  # None para remover senha

class RenameItem(BaseModel):
    path: str
    new_name: str

@api_router.get("/storage/list")
async def list_storage_items(
    path: str = "/",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List files and folders in a path"""
    await get_current_user(credentials)
    
    # Normalize path
    if not path.startswith("/"):
        path = "/" + path
    
    # Build absolute path
    abs_path = STORAGE_DIR / path.lstrip("/")
    
    if not abs_path.exists():
        abs_path.mkdir(parents=True, exist_ok=True)
    
    # Buscar todas as pastas protegidas de uma vez
    protected_folders = await db.folder_passwords.find({}, {"_id": 0, "path": 1}).to_list(1000)
    protected_paths = {f["path"] for f in protected_folders}
    
    items = []
    try:
        for entry in abs_path.iterdir():
            rel_path = "/" + str(entry.relative_to(STORAGE_DIR)).replace("\\", "/")
            
            if entry.is_dir():
                # Count items inside folder
                items_count = len(list(entry.iterdir())) if entry.exists() else 0
                items.append({
                    "name": entry.name,
                    "type": "folder",
                    "path": rel_path,
                    "items_count": items_count,
                    "modified_at": datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "has_password": rel_path in protected_paths
                })
            else:
                items.append({
                    "name": entry.name,
                    "type": "file",
                    "path": rel_path,
                    "size": entry.stat().st_size,
                    "modified_at": datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                })
    except Exception as e:
        logger.error(f"Error listing storage: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar arquivos: {str(e)}")
    
    # Sort: folders first, then files, both alphabetically
    items.sort(key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower()))
    
    return items

@api_router.post("/storage/folder")
async def create_folder(
    data: FolderCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new folder"""
    current_user = await get_current_user(credentials)
    
    # Validate folder name
    if not data.name or "/" in data.name or "\\" in data.name:
        raise HTTPException(status_code=400, detail="Nome de pasta inválido")
    
    # Normalize parent path
    parent = data.parent_path if data.parent_path.startswith("/") else "/" + data.parent_path
    
    # Build full path
    full_path = STORAGE_DIR / parent.lstrip("/") / data.name
    folder_path = "/" + str(full_path.relative_to(STORAGE_DIR)).replace("\\", "/")
    
    if full_path.exists():
        raise HTTPException(status_code=400, detail="Pasta já existe")
    
    try:
        full_path.mkdir(parents=True, exist_ok=False)
        
        # Se tiver senha, salvar no MongoDB
        if data.password:
            password_hash = hash_password(data.password)
            await db.folder_passwords.update_one(
                {"path": folder_path},
                {"$set": {
                    "path": folder_path,
                    "password_hash": password_hash,
                    "created_by": current_user["id"],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        # Auditoria
        await create_audit_log(
            user=current_user,
            action="criar pasta",
            entity_type="storage",
            entity_id=data.name,
            entity_name=data.name,
            details=f"Pasta criada em {parent}" + (" (protegida com senha)" if data.password else ""),
            module="Armazenamento"
        )
        
        return {"message": "Pasta criada com sucesso", "path": folder_path, "has_password": bool(data.password)}
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar pasta: {str(e)}")

@api_router.post("/storage/folder/check-password")
async def check_folder_password(
    data: FolderPasswordCheck,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verifica se a senha da pasta está correta"""
    await get_current_user(credentials)
    
    # Normalizar path
    path = data.path if data.path.startswith("/") else "/" + data.path
    
    # Buscar senha da pasta
    folder_record = await db.folder_passwords.find_one({"path": path}, {"_id": 0})
    
    if not folder_record:
        return {"valid": True, "message": "Pasta não possui senha"}
    
    # Verificar senha
    if verify_password(data.password, folder_record["password_hash"]):
        return {"valid": True, "message": "Senha correta"}
    else:
        raise HTTPException(status_code=401, detail="Senha incorreta")

@api_router.post("/storage/folder/set-password")
async def set_folder_password(
    data: FolderPasswordSet,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Define ou remove a senha de uma pasta"""
    current_user = await get_current_user(credentials)
    
    # Normalizar path
    path = data.path if data.path.startswith("/") else "/" + data.path
    
    # Verificar se a pasta existe
    abs_path = STORAGE_DIR / path.lstrip("/")
    if not abs_path.exists() or not abs_path.is_dir():
        raise HTTPException(status_code=404, detail="Pasta não encontrada")
    
    if data.password:
        # Definir nova senha
        password_hash = hash_password(data.password)
        await db.folder_passwords.update_one(
            {"path": path},
            {"$set": {
                "path": path,
                "password_hash": password_hash,
                "updated_by": current_user["id"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        await create_audit_log(
            user=current_user,
            action="definir senha",
            entity_type="storage",
            entity_id=path,
            entity_name=path.split("/")[-1],
            details=f"Senha definida para pasta {path}",
            module="Armazenamento"
        )
        
        return {"message": "Senha definida com sucesso", "has_password": True}
    else:
        # Remover senha
        await db.folder_passwords.delete_one({"path": path})
        
        await create_audit_log(
            user=current_user,
            action="remover senha",
            entity_type="storage",
            entity_id=path,
            entity_name=path.split("/")[-1],
            details=f"Senha removida da pasta {path}",
            module="Armazenamento"
        )
        
        return {"message": "Senha removida com sucesso", "has_password": False}

@api_router.get("/storage/folder/has-password")
async def check_folder_has_password(
    path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verifica se uma pasta possui senha"""
    await get_current_user(credentials)
    
    # Normalizar path
    if not path.startswith("/"):
        path = "/" + path
    
    folder_record = await db.folder_passwords.find_one({"path": path}, {"_id": 0})
    return {"has_password": folder_record is not None}

@api_router.post("/storage/upload")
async def upload_storage_file(
    file: UploadFile = File(...),
    path: str = Form("/"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload a file to storage"""
    current_user = await get_current_user(credentials)
    
    # Normalize path
    if not path.startswith("/"):
        path = "/" + path
    
    # Build full path
    dir_path = STORAGE_DIR / path.lstrip("/")
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # Read file content
    content = await file.read()
    
    # Save file with original name (handle duplicates)
    filename = file.filename or "arquivo"
    file_path = dir_path / filename
    
    # If file exists, add number suffix
    counter = 1
    base_name = Path(filename).stem
    ext = Path(filename).suffix
    while file_path.exists():
        filename = f"{base_name}_{counter}{ext}"
        file_path = dir_path / filename
        counter += 1
    
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Auditoria
        await create_audit_log(
            user=current_user,
            action="upload arquivo",
            entity_type="storage",
            entity_id=filename,
            entity_name=filename,
            details=f"Arquivo enviado para {path}",
            module="Armazenamento"
        )
        
        rel_path = "/" + str(file_path.relative_to(STORAGE_DIR)).replace("\\", "/")
        return {
            "message": "Arquivo enviado com sucesso",
            "name": filename,
            "path": rel_path,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar arquivo: {str(e)}")

@api_router.get("/storage/download")
async def download_storage_file(
    path: str,
    token: Optional[str] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
):
    """Download a file from storage"""
    # Support both Authorization header and query param token (for iframe/img src)
    if credentials and credentials.credentials:
        try:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise HTTPException(status_code=401, detail="Token inválido")
    elif token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Normalize path
    if not path.startswith("/"):
        path = "/" + path
    
    # Build absolute path
    abs_path = STORAGE_DIR / path.lstrip("/")
    
    if not abs_path.exists() or not abs_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Determine content type
    content_type = "application/octet-stream"
    ext = abs_path.suffix.lower()
    content_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".json": "application/json",
        ".xml": "application/xml",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".zip": "application/zip"
    }
    content_type = content_types.get(ext, content_type)
    
    return FileResponse(
        path=str(abs_path),
        filename=abs_path.name,
        media_type=content_type
    )

@api_router.get("/storage/preview-office")
async def preview_office_file(
    path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Preview Word/Excel files as HTML"""
    current_user = await get_current_user(credentials)
    
    # Normalize path
    if not path.startswith("/"):
        path = "/" + path
    
    abs_path = STORAGE_DIR / path.lstrip("/")
    
    if not abs_path.exists() or not abs_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    ext = abs_path.suffix.lower()
    
    try:
        if ext in ['.doc', '.docx']:
            # Preview Word document
            from docx import Document
            doc = Document(str(abs_path))
            
            html_content = '<div style="font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto;">'
            for para in doc.paragraphs:
                style = para.style.name if para.style else ''
                if 'Heading 1' in style:
                    html_content += f'<h1 style="color: #333; border-bottom: 2px solid #E31A1A; padding-bottom: 10px;">{para.text}</h1>'
                elif 'Heading 2' in style:
                    html_content += f'<h2 style="color: #444;">{para.text}</h2>'
                elif 'Heading 3' in style:
                    html_content += f'<h3 style="color: #555;">{para.text}</h3>'
                else:
                    html_content += f'<p style="line-height: 1.6; margin: 10px 0;">{para.text}</p>'
            
            # Add tables
            for table in doc.tables:
                html_content += '<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">'
                for row in table.rows:
                    html_content += '<tr>'
                    for cell in row.cells:
                        html_content += f'<td style="border: 1px solid #ddd; padding: 8px;">{cell.text}</td>'
                    html_content += '</tr>'
                html_content += '</table>'
            
            html_content += '</div>'
            return {"html": html_content, "type": "word"}
            
        elif ext in ['.xls', '.xlsx']:
            # Preview Excel file
            import openpyxl
            wb = openpyxl.load_workbook(str(abs_path), data_only=True)
            
            html_content = '<div style="font-family: Arial, sans-serif; padding: 20px;">'
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                html_content += f'<h3 style="color: #E31A1A; margin-top: 20px;">Planilha: {sheet_name}</h3>'
                html_content += '<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">'
                
                for row in sheet.iter_rows(max_row=100, max_col=20):  # Limit to prevent huge tables
                    html_content += '<tr>'
                    for cell in row:
                        value = cell.value if cell.value is not None else ''
                        style = 'border: 1px solid #ddd; padding: 8px; '
                        if cell.row == 1:
                            style += 'background: #f5f5f5; font-weight: bold;'
                        html_content += f'<td style="{style}">{value}</td>'
                    html_content += '</tr>'
                
                html_content += '</table>'
            
            html_content += '</div>'
            return {"html": html_content, "type": "excel"}
        else:
            raise HTTPException(status_code=400, detail="Tipo de arquivo não suportado para preview")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

# Trash directory for storage system
STORAGE_TRASH_DIR = ROOT_DIR / "storage_trash"
STORAGE_TRASH_DIR.mkdir(exist_ok=True)

class MoveRequest(BaseModel):
    source_path: str
    destination_path: str

@api_router.post("/storage/move")
async def move_storage_item(
    data: MoveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Move a file or folder to another location"""
    current_user = await get_current_user(credentials)
    import shutil
    
    # Normalize paths
    source = data.source_path if data.source_path.startswith("/") else "/" + data.source_path
    dest = data.destination_path if data.destination_path.startswith("/") else "/" + data.destination_path
    
    source_abs = STORAGE_DIR / source.lstrip("/")
    dest_dir = STORAGE_DIR / dest.lstrip("/")
    
    if not source_abs.exists():
        raise HTTPException(status_code=404, detail="Arquivo de origem não encontrado")
    
    if not dest_dir.exists() or not dest_dir.is_dir():
        raise HTTPException(status_code=400, detail="Pasta de destino não existe")
    
    # Check if destination is inside source (cannot move folder into itself)
    if source_abs.is_dir():
        try:
            dest_dir.relative_to(source_abs)
            raise HTTPException(status_code=400, detail="Não é possível mover uma pasta para dentro dela mesma")
        except ValueError:
            pass  # dest is not inside source, this is good
    
    dest_path = dest_dir / source_abs.name
    
    # Handle name conflicts
    if dest_path.exists():
        base = dest_path.stem
        ext = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{base} ({counter}){ext}"
            counter += 1
    
    try:
        shutil.move(str(source_abs), str(dest_path))
        return {"message": "Item movido com sucesso", "new_path": "/" + str(dest_path.relative_to(STORAGE_DIR))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao mover: {str(e)}")

@api_router.post("/storage/copy")
async def copy_storage_item(
    data: MoveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Copy a file or folder to another location"""
    current_user = await get_current_user(credentials)
    import shutil
    
    # Normalize paths
    source = data.source_path if data.source_path.startswith("/") else "/" + data.source_path
    dest = data.destination_path if data.destination_path.startswith("/") else "/" + data.destination_path
    
    source_abs = STORAGE_DIR / source.lstrip("/")
    dest_dir = STORAGE_DIR / dest.lstrip("/")
    
    if not source_abs.exists():
        raise HTTPException(status_code=404, detail="Arquivo de origem não encontrado")
    
    if not dest_dir.exists() or not dest_dir.is_dir():
        raise HTTPException(status_code=400, detail="Pasta de destino não existe")
    
    dest_path = dest_dir / source_abs.name
    
    # Handle name conflicts
    if dest_path.exists():
        base = dest_path.stem
        ext = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{base} - Cópia ({counter}){ext}"
            counter += 1
    
    try:
        if source_abs.is_dir():
            shutil.copytree(str(source_abs), str(dest_path))
        else:
            shutil.copy2(str(source_abs), str(dest_path))
        return {"message": "Item copiado com sucesso", "new_path": "/" + str(dest_path.relative_to(STORAGE_DIR))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao copiar: {str(e)}")

@api_router.delete("/storage/delete")
async def delete_storage_item(
    path: str,
    permanent: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Move a file or folder to trash (or delete permanently if permanent=True)"""
    current_user = await get_current_user(credentials)
    
    # Normalize path
    if not path.startswith("/"):
        path = "/" + path
    
    # Build absolute path
    abs_path = STORAGE_DIR / path.lstrip("/")
    
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    item_name = abs_path.name
    is_folder = abs_path.is_dir()
    
    try:
        if permanent:
            # Delete permanently
            if is_folder:
                import shutil
                shutil.rmtree(abs_path)
            else:
                abs_path.unlink()
            action = "excluir permanentemente"
        else:
            # Move to trash
            import shutil
            trash_item_id = str(uuid.uuid4())
            trash_path = STORAGE_TRASH_DIR / trash_item_id
            
            # Move the item
            shutil.move(str(abs_path), str(trash_path))
            
            # Save metadata to database
            trash_record = {
                "id": trash_item_id,
                "original_name": item_name,
                "original_path": path,
                "type": "folder" if is_folder else "file",
                "deleted_by": current_user["id"],
                "deleted_by_name": current_user["name"],
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Get file size if it's a file
            if not is_folder and trash_path.exists():
                trash_record["size"] = trash_path.stat().st_size
            
            await db.storage_trash.insert_one(trash_record)
            action = "mover para lixeira"
        
        # Auditoria
        await create_audit_log(
            user=current_user,
            action=action,
            entity_type="storage",
            entity_id=item_name,
            entity_name=item_name,
            details=f"{'Pasta' if is_folder else 'Arquivo'}: {path}",
            module="Armazenamento"
        )
        
        return {"message": "Item movido para lixeira" if not permanent else "Item excluído permanentemente"}
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {str(e)}")

@api_router.get("/storage/trash")
async def list_trash_items(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List all items in trash"""
    await get_current_user(credentials)
    
    items = await db.storage_trash.find({}, {"_id": 0}).sort("deleted_at", -1).to_list(1000)
    return items

@api_router.post("/storage/trash/{item_id}/restore")
async def restore_trash_item(
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Restore an item from trash"""
    current_user = await get_current_user(credentials)
    
    # Find item in trash
    trash_item = await db.storage_trash.find_one({"id": item_id}, {"_id": 0})
    if not trash_item:
        raise HTTPException(status_code=404, detail="Item não encontrado na lixeira")
    
    trash_path = STORAGE_TRASH_DIR / item_id
    if not trash_path.exists():
        # Clean up database record
        await db.storage_trash.delete_one({"id": item_id})
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no sistema")
    
    # Restore to original location
    original_path = trash_item["original_path"]
    restore_path = STORAGE_DIR / original_path.lstrip("/")
    
    # Create parent directories if needed
    restore_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Handle name conflicts
    if restore_path.exists():
        base_name = Path(trash_item["original_name"]).stem
        ext = Path(trash_item["original_name"]).suffix
        counter = 1
        while restore_path.exists():
            new_name = f"{base_name}_{counter}{ext}"
            restore_path = restore_path.parent / new_name
            counter += 1
    
    try:
        import shutil
        shutil.move(str(trash_path), str(restore_path))
        
        # Remove from trash database
        await db.storage_trash.delete_one({"id": item_id})
        
        # Auditoria
        await create_audit_log(
            user=current_user,
            action="restaurar da lixeira",
            entity_type="storage",
            entity_id=trash_item["original_name"],
            entity_name=trash_item["original_name"],
            details=f"Restaurado para: {str(restore_path.relative_to(STORAGE_DIR))}",
            module="Armazenamento"
        )
        
        return {"message": "Item restaurado com sucesso", "restored_path": "/" + str(restore_path.relative_to(STORAGE_DIR)).replace("\\", "/")}
    except Exception as e:
        logger.error(f"Error restoring item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao restaurar: {str(e)}")

@api_router.delete("/storage/trash/{item_id}")
async def delete_trash_item_permanently(
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Permanently delete an item from trash"""
    current_user = await get_current_user(credentials)
    
    # Find item in trash
    trash_item = await db.storage_trash.find_one({"id": item_id}, {"_id": 0})
    if not trash_item:
        raise HTTPException(status_code=404, detail="Item não encontrado na lixeira")
    
    trash_path = STORAGE_TRASH_DIR / item_id
    
    try:
        if trash_path.exists():
            if trash_path.is_dir():
                import shutil
                shutil.rmtree(trash_path)
            else:
                trash_path.unlink()
        
        # Remove from trash database
        await db.storage_trash.delete_one({"id": item_id})
        
        # Auditoria
        await create_audit_log(
            user=current_user,
            action="excluir permanentemente",
            entity_type="storage",
            entity_id=trash_item["original_name"],
            entity_name=trash_item["original_name"],
            details=f"Excluído permanentemente da lixeira",
            module="Armazenamento"
        )
        
        return {"message": "Item excluído permanentemente"}
    except Exception as e:
        logger.error(f"Error deleting trash item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {str(e)}")

@api_router.delete("/storage/trash")
async def empty_trash(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Empty all items from trash"""
    current_user = await get_current_user(credentials)
    
    try:
        import shutil
        
        # Get all items from trash
        trash_items = await db.storage_trash.find({}, {"_id": 0}).to_list(1000)
        count = len(trash_items)
        
        # Delete all files/folders in trash directory
        for item in trash_items:
            trash_path = STORAGE_TRASH_DIR / item["id"]
            if trash_path.exists():
                if trash_path.is_dir():
                    shutil.rmtree(trash_path)
                else:
                    trash_path.unlink()
        
        # Clear trash database
        await db.storage_trash.delete_many({})
        
        # Auditoria
        await create_audit_log(
            user=current_user,
            action="esvaziar lixeira",
            entity_type="storage",
            entity_id="trash",
            entity_name="Lixeira",
            details=f"{count} itens excluídos permanentemente",
            module="Armazenamento"
        )
        
        return {"message": f"Lixeira esvaziada. {count} itens excluídos."}
    except Exception as e:
        logger.error(f"Error emptying trash: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao esvaziar lixeira: {str(e)}")

@api_router.patch("/storage/rename")
async def rename_storage_item(
    data: RenameItem,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Rename a file or folder in storage"""
    current_user = await get_current_user(credentials)
    
    # Validate new name
    if not data.new_name or "/" in data.new_name or "\\" in data.new_name:
        raise HTTPException(status_code=400, detail="Nome inválido")
    
    # Normalize path
    path = data.path if data.path.startswith("/") else "/" + data.path
    
    # Build absolute paths
    abs_path = STORAGE_DIR / path.lstrip("/")
    new_path = abs_path.parent / data.new_name
    
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    if new_path.exists():
        raise HTTPException(status_code=400, detail="Já existe um item com esse nome")
    
    old_name = abs_path.name
    
    try:
        abs_path.rename(new_path)
        
        # Auditoria
        await create_audit_log(
            user=current_user,
            action="renomear",
            entity_type="storage",
            entity_id=data.new_name,
            entity_name=data.new_name,
            details=f"Renomeado de '{old_name}' para '{data.new_name}'",
            module="Armazenamento"
        )
        
        return {
            "message": "Item renomeado com sucesso",
            "new_path": "/" + str(new_path.relative_to(STORAGE_DIR)).replace("\\", "/")
        }
    except Exception as e:
        logger.error(f"Error renaming item: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao renomear: {str(e)}")


# Include modular routers first
api_router.include_router(rh_router)
api_router.include_router(admin_router)
api_router.include_router(machines_router)
api_router.include_router(chatbot_router)
api_router.include_router(storage_router)
api_router.include_router(export_router)
api_router.include_router(stock_router)
api_router.include_router(obras_router)

# Include the router in the main app
app.include_router(api_router)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
