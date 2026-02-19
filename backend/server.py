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
    details: str = ""
):
    """Create an audit log entry for tracking user actions."""
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "user_email": user["email"],
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "details": details,
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
    
    token = create_token(user["id"], user["email"])
    user_response = UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"]
    )
    return TokenResponse(token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
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
    return {"message": "Máquina removida com sucesso"}

# ============ MAINTENANCE ROUTES ============

@api_router.post("/maintenances", response_model=MaintenanceResponse)
async def create_maintenance(maintenance: MaintenanceCreate, current_user: dict = Depends(get_current_user)):
    # Check if machine exists
    machine = await db.machines.find_one({"id": maintenance.machine_id, "user_id": current_user["id"]}, {"_id": 0})
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
        "user_id": current_user["id"],
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
    query = {"user_id": current_user["id"]}
    if machine_id:
        query["machine_id"] = machine_id
    if oil_changes_only:
        query["is_oil_change"] = True
    
    maintenances = await db.maintenances.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get all machines
    machines = await db.machines.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
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
    maintenance = await db.maintenances.find_one({"id": maintenance_id, "user_id": current_user["id"]}, {"_id": 0})
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
    result = await db.maintenances.delete_one({"id": maintenance_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Manutenção não encontrada")
    return {"message": "Manutenção removida com sucesso"}

# ============ PHOTO UPLOAD ============

@api_router.post("/maintenances/{maintenance_id}/photos")
async def upload_photo(
    maintenance_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    maintenance = await db.maintenances.find_one({"id": maintenance_id, "user_id": current_user["id"]})
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
    maintenance = await db.maintenances.find_one({"id": maintenance_id, "user_id": current_user["id"]})
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
    machine = await db.machines.find_one({"id": log.machine_id, "user_id": current_user["id"]}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    log_id = str(uuid.uuid4())
    log_doc = {
        "id": log_id,
        "machine_id": log.machine_id,
        "hours": log.hours,
        "notes": log.notes or "",
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.usage_logs.insert_one(log_doc)
    
    # Update machine's hours since oil change
    current_hours = machine.get("hours_since_oil_change", 0)
    await db.machines.update_one(
        {"id": log.machine_id},
        {"$set": {"hours_since_oil_change": current_hours + log.hours}}
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
    query = {"user_id": current_user["id"]}
    if machine_id:
        query["machine_id"] = machine_id
    
    logs = await db.usage_logs.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get machines
    machines = await db.machines.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
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
    machines = await db.machines.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    
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
    machines = await db.machines.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    
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
    stock_items = await db.stock_items.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
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
    maintenances = await db.maintenances.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(10000)
    
    # Get all machines with categories
    machines = await db.machines.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    categories = await db.categories.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
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
    total_machines = await db.machines.count_documents({"user_id": current_user["id"]})
    
    # Count and sum maintenances
    maintenances = await db.maintenances.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    total_maintenances = len(maintenances)
    preventive_count = len([m for m in maintenances if m["maintenance_type"] == "preventiva"])
    corrective_count = len([m for m in maintenances if m["maintenance_type"] == "corretiva"])
    total_spent = sum(m["part_value"] for m in maintenances)
    
    # Get recent maintenances
    recent = await db.maintenances.find({"user_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    # Get machines for recent maintenances
    machines = await db.machines.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
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
            "user_id": current_user["id"],
            "$expr": {"$lte": ["$quantity", "$min_quantity"]}
        }),
        oil_change_alerts=oil_change_alerts
    )

# ============ STOCK ROUTES ============

# Stock Categories
@api_router.post("/stock/categories", response_model=StockCategoryResponse)
async def create_stock_category(category: StockCategoryCreate, current_user: dict = Depends(get_current_user)):
    # Check if category already exists
    existing = await db.stock_categories.find_one({"name": category.name, "user_id": current_user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Categoria já existe")
    
    category_id = str(uuid.uuid4())
    category_doc = {
        "id": category_id,
        "name": category.name,
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_categories.insert_one(category_doc)
    
    return StockCategoryResponse(
        id=category_id,
        name=category.name,
        created_at=category_doc["created_at"]
    )

@api_router.get("/stock/categories", response_model=List[StockCategoryResponse])
async def get_stock_categories(current_user: dict = Depends(get_current_user)):
    categories = await db.stock_categories.find({"user_id": current_user["id"]}, {"_id": 0}).sort("name", 1).to_list(100)
    return [StockCategoryResponse(
        id=c["id"],
        name=c["name"],
        created_at=c["created_at"]
    ) for c in categories]

@api_router.delete("/stock/categories/{category_id}")
async def delete_stock_category(category_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.stock_categories.delete_one({"id": category_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
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
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_items.insert_one(item_doc)
    
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
    query = {"user_id": current_user["id"]}
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
    item = await db.stock_items.find_one({"id": item_id, "user_id": current_user["id"]}, {"_id": 0})
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
    existing = await db.stock_items.find_one({"id": item_id, "user_id": current_user["id"]})
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
    result = await db.stock_items.delete_one({"id": item_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    # Delete related movements
    await db.stock_movements.delete_many({"item_id": item_id})
    return {"message": "Item removido com sucesso"}

@api_router.post("/stock/movements", response_model=StockMovementResponse)
async def create_stock_movement(movement: StockMovementCreate, current_user: dict = Depends(get_current_user)):
    # Check if item exists
    item = await db.stock_items.find_one({"id": movement.item_id, "user_id": current_user["id"]})
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
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_movements.insert_one(movement_doc)
    
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
    query = {"user_id": current_user["id"]}
    if item_id:
        query["item_id"] = item_id
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get item names
    items = await db.stock_items.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
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
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.obras.insert_one(obra_doc)
    
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
    obras = await db.obras.find({"user_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    result = []
    for obra in obras:
        # Count machines in this obra
        machine_count = await db.machines.count_documents({"obra_id": obra["id"], "user_id": current_user["id"]})
        
        # Get machines to calculate maintenance costs
        machines = await db.machines.find({"obra_id": obra["id"], "user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
        machine_ids = [m["id"] for m in machines]
        
        # Calculate total maintenance cost
        total_cost = 0
        if machine_ids:
            maintenances = await db.maintenances.find({
                "machine_id": {"$in": machine_ids},
                "user_id": current_user["id"]
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
    obra = await db.obras.find_one({"id": obra_id, "user_id": current_user["id"]}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    # Get machines in this obra
    machines_db = await db.machines.find({"obra_id": obra_id, "user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    
    # Get categories for machines
    categories = await db.categories.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
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
            "machine_id": {"$in": machine_ids},
            "user_id": current_user["id"]
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
    existing = await db.obras.find_one({"id": obra_id, "user_id": current_user["id"]})
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
    
    # Count machines
    machine_count = await db.machines.count_documents({"obra_id": obra_id, "user_id": current_user["id"]})
    
    # Calculate total cost
    machines = await db.machines.find({"obra_id": obra_id, "user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    machine_ids = [m["id"] for m in machines]
    total_cost = 0
    if machine_ids:
        maintenances = await db.maintenances.find({
            "machine_id": {"$in": machine_ids},
            "user_id": current_user["id"]
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
    result = await db.obras.delete_one({"id": obra_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    # Remove obra_id from all machines that were in this obra
    await db.machines.update_many(
        {"obra_id": obra_id, "user_id": current_user["id"]},
        {"$set": {"obra_id": None}}
    )
    
    return {"message": "Obra removida com sucesso"}

# ============ ROOT ============

@api_router.get("/")
async def root():
    return {"message": "CRA Construtora API"}

# Include the router in the main app
app.include_router(api_router)

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
