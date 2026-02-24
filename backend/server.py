from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
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

class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    created_at: str

class MachineCreate(BaseModel):
    name: str
    plate: str
    category_id: str
    brand: Optional[str] = ""
    model: Optional[str] = ""
    year: Optional[int] = None
    notes: Optional[str] = ""
    obra_id: Optional[str] = None

class MachineResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    plate: str
    category_id: str
    category_name: Optional[str] = ""
    brand: str
    model: str
    year: Optional[int] = None
    notes: str
    status: str
    obra_id: Optional[str] = None
    obra_name: Optional[str] = ""
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
    created_at: str

class StockItemCreate(BaseModel):
    name: str
    code: Optional[str] = ""
    category: Optional[str] = ""  # filtro, óleo, correia, etc.
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
            module = "Gerenciamento Geral"
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

# ============ CATEGORY ROUTES ============

@api_router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, current_user: dict = Depends(get_current_user)):
    category_id = str(uuid.uuid4())
    category_doc = {
        "id": category_id,
        "name": category.name,
        "description": category.description or "",
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
        created_at=category_doc["created_at"]
    )

@api_router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(current_user: dict = Depends(get_current_user)):
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    return [CategoryResponse(
        id=c["id"],
        name=c["name"],
        description=c.get("description", ""),
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
        {"$set": {"name": category.name, "description": category.description or ""}}
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
        created_at=existing["created_at"]
    )

# ============ MACHINE ROUTES ============

@api_router.post("/machines", response_model=MachineResponse)
async def create_machine(machine: MachineCreate, current_user: dict = Depends(get_current_user)):
    # Check if plate already exists
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
    
    machine_id = str(uuid.uuid4())
    machine_doc = {
        "id": machine_id,
        "name": machine.name,
        "plate": machine.plate.upper(),
        "category_id": machine.category_id,
        "brand": machine.brand or "",
        "model": machine.model or "",
        "year": machine.year,
        "notes": machine.notes or "",
        "obra_id": machine.obra_id,
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
        entity_name=f"{machine.name} ({machine.plate.upper()})"
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
        obra_id=machine.obra_id,
        obra_name=obra_name,
        status="operational",
        created_at=machine_doc["created_at"]
    )

@api_router.get("/machines", response_model=List[MachineResponse])
async def get_machines(obra_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if obra_id:
        query["obra_id"] = obra_id
    
    machines = await db.machines.find(query, {"_id": 0}).to_list(1000)
    
    # Get all categories
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    # Get all obras
    obras = await db.obras.find({}, {"_id": 0}).to_list(100)
    obra_map = {o["id"]: o["name"] for o in obras}
    
    return [MachineResponse(
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
        obra_name=obra_map.get(m.get("obra_id", ""), ""),
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
    
    return MachineResponse(
        id=machine["id"],
        name=machine["name"],
        plate=machine["plate"],
        category_id=machine["category_id"],
        category_name=category_name,
        brand=machine.get("brand", ""),
        model=machine.get("model", ""),
        year=machine.get("year"),
        notes=machine.get("notes", ""),
        status=machine.get("status", "operational"),
        obra_id=machine.get("obra_id"),
        obra_name=obra_name,
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
        id=l["id"],
        user_id=l["user_id"],
        user_name=l["user_name"],
        user_email=l["user_email"],
        action=l["action"],
        entity_type=l["entity_type"],
        entity_id=l["entity_id"],
        entity_name=l["entity_name"],
        details=l.get("details", ""),
        created_at=l["created_at"]
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
    contas_pagar_vencidas = len([c for c in contas_pagar_abertas if c.get("data_vencimento", "") < hoje_str])
    
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
    contas_receber_vencidas = len([c for c in contas_receber_abertas if c.get("data_vencimento", "") < hoje_str])
    
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
        "contasProximas": contas_proximas[:10]
    }

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
    
    # Validate role
    valid_roles = ["gerenciamento", "administrativo", "ambos", "admin"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Tipo de acesso inválido")
    
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
        "gerenciamento": "Gerenciamento Geral",
        "administrativo": "Administrativo",
        "ambos": "Gerenciamento + Administrativo",
        "admin": "Administrador"
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
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar permissões")
    
    valid_roles = ["gerenciamento", "administrativo", "ambos", "admin"]
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

def require_admin(user: dict):
    """Verifica se o usuário é admin"""
    if user.get("role") != "admin":
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
        {
            "id": "auditoria",
            "label": "Auditoria",
            "icon": "clipboard",
            "subcategories": [
                {"id": "audit_logs", "label": "Logs de Auditoria", "description": "Todas as atividades registradas"},
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
            "id": "usuarios_admin",
            "label": "Usuários",
            "icon": "users",
            "subcategories": [
                {"id": "users", "label": "Lista de Usuários", "description": "Todos os usuários"},
            ]
        },
        {
            "id": "auditoria_admin",
            "label": "Auditoria",
            "icon": "clipboard",
            "subcategories": [
                {"id": "audit_logs", "label": "Logs de Auditoria", "description": "Atividades registradas"},
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
            logo = RLImage(logo_path, width=4*cm, height=1.5*cm)
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
        "contas_pagar_pendente": {"collection": "contas_pagar", "title": "Contas a Pagar Pendentes", "filter": {"status": "pendente"}},
        "contas_pagar_quitada": {"collection": "contas_pagar", "title": "Contas a Pagar Quitadas", "filter": {"status": "quitada"}},
        "contas_pagar_vencidas": {"collection": "contas_pagar", "title": "Contas a Pagar Vencidas", "filter": {"status": "pendente", "data_vencimento": {"$lt": datetime.now().strftime("%Y-%m-%d")}}},
        
        # Contas a Receber
        "contas_receber": {"collection": "contas_receber", "title": "Contas a Receber", "filter": {}},
        "contas_receber_pendente": {"collection": "contas_receber", "title": "Contas a Receber Pendentes", "filter": {"status": "pendente"}},
        "contas_receber_quitada": {"collection": "contas_receber", "title": "Contas a Receber Recebidas", "filter": {"status": "quitada"}},
        "contas_receber_vencidas": {"collection": "contas_receber", "title": "Contas a Receber Vencidas", "filter": {"status": "pendente", "data_vencimento": {"$lt": datetime.now().strftime("%Y-%m-%d")}}},
        
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
        
        # Contabilidade
        "plano_contas": {"collection": "plano_contas", "title": "Plano de Contas", "filter": {}},
        "plano_contas_receita": {"collection": "plano_contas", "title": "Contas de Receita", "filter": {"tipo": "receita"}},
        "plano_contas_despesa": {"collection": "plano_contas", "title": "Contas de Despesa", "filter": {"tipo": "despesa"}},
        "centros_custo": {"collection": "centros_custo", "title": "Centros de Custo", "filter": {}},
        "formas_pagamento": {"collection": "formas_pagamento", "title": "Formas de Pagamento", "filter": {}},
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

@api_router.get("/attachments/{entity_type}/{entity_id}")
async def get_attachments(entity_type: str, entity_id: str, current_user: dict = Depends(get_current_user)):
    """Lista anexos de uma entidade"""
    attachments = await db.attachments.find(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return attachments

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
    
    if current_user.get("role") != "admin":
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
    
    if current_user.get("role") != "admin":
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
    
    if current_user.get("role") != "admin":
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
    
    if current_user.get("role") != "admin":
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
