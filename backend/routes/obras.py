"""
Obras Routes - Projects/Construction sites management module
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
obras_router = APIRouter(prefix="/obras", tags=["Obras"])


# ============ MODELS ============

class ObraCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    location: Optional[str] = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "em_andamento"


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


class MachineInObra(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    plate: str
    category_name: str = ""
    brand: str = ""
    model: str = ""
    status: str = "operational"


class MaintenanceInObra(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_name: str
    part_name: str
    replacement_date: str
    part_value: float
    maintenance_type: str


class ObraDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    location: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    machines: List[MachineInObra] = []
    maintenances: List[MaintenanceInObra] = []
    total_maintenance_cost: float = 0
    preventive_cost: float = 0
    corrective_cost: float = 0
    created_at: str


# ============ OBRAS ROUTES ============

@obras_router.post("", response_model=ObraResponse)
async def create_obra(obra: ObraCreate, current_user: dict = Depends(get_current_user)):
    """Criar nova obra/projeto"""
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


@obras_router.get("", response_model=List[ObraResponse])
async def get_obras(current_user: dict = Depends(get_current_user)):
    """Listar todas as obras"""
    obras = await db.obras.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    result = []
    for obra in obras:
        machine_count = await db.machines.count_documents({"obra_id": obra["id"]})
        
        machines = await db.machines.find({"obra_id": obra["id"]}, {"_id": 0}).to_list(1000)
        machine_ids = [m["id"] for m in machines]
        
        total_cost = 0
        if machine_ids:
            maintenances = await db.maintenances.find({
                "machine_id": {"$in": machine_ids}
            }, {"_id": 0}).to_list(10000)
            total_cost = sum(m.get("part_value", 0) for m in maintenances)
        
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


@obras_router.get("/{obra_id}", response_model=ObraDetailResponse)
async def get_obra(obra_id: str, current_user: dict = Depends(get_current_user)):
    """Obter detalhes de uma obra"""
    obra = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    # Obter máquinas da obra
    machines_db = await db.machines.find({"obra_id": obra_id}, {"_id": 0}).to_list(1000)
    
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    machines = [MachineInObra(
        id=m["id"],
        name=m["name"],
        plate=m.get("plate", ""),
        category_name=category_map.get(m.get("category_id"), ""),
        brand=m.get("brand", ""),
        model=m.get("model", ""),
        status=m.get("status", "operational")
    ) for m in machines_db]
    
    # Obter manutenções das máquinas da obra
    machine_ids = [m["id"] for m in machines_db]
    machine_map = {m["id"]: m["name"] for m in machines_db}
    
    maintenances = []
    total_cost = 0
    preventive_cost = 0
    corrective_cost = 0
    
    if machine_ids:
        maint_db = await db.maintenances.find({
            "machine_id": {"$in": machine_ids}
        }, {"_id": 0}).sort("replacement_date", -1).to_list(10000)
        
        for m in maint_db:
            cost = m.get("part_value", 0)
            total_cost += cost
            
            if m.get("maintenance_type") == "preventiva":
                preventive_cost += cost
            else:
                corrective_cost += cost
            
            maintenances.append(MaintenanceInObra(
                id=m["id"],
                machine_name=machine_map.get(m.get("machine_id"), ""),
                part_name=m.get("part_name", ""),
                replacement_date=m.get("replacement_date", ""),
                part_value=cost,
                maintenance_type=m.get("maintenance_type", "")
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
        maintenances=maintenances[:50],  # Limitar a 50 mais recentes
        total_maintenance_cost=total_cost,
        preventive_cost=preventive_cost,
        corrective_cost=corrective_cost,
        created_at=obra["created_at"]
    )


@obras_router.put("/{obra_id}", response_model=ObraResponse)
async def update_obra(obra_id: str, obra: ObraCreate, current_user: dict = Depends(get_current_user)):
    """Atualizar obra"""
    existing = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    update_data = {
        "name": obra.name,
        "description": obra.description or "",
        "location": obra.location or "",
        "start_date": obra.start_date,
        "end_date": obra.end_date,
        "status": obra.status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.obras.update_one({"id": obra_id}, {"$set": update_data})
    
    machine_count = await db.machines.count_documents({"obra_id": obra_id})
    
    return ObraResponse(
        id=obra_id,
        name=obra.name,
        description=obra.description or "",
        location=obra.location or "",
        start_date=obra.start_date,
        end_date=obra.end_date,
        status=obra.status,
        machine_count=machine_count,
        total_maintenance_cost=0,
        created_at=existing["created_at"]
    )


@obras_router.delete("/{obra_id}")
async def delete_obra(obra_id: str, current_user: dict = Depends(get_current_user)):
    """Excluir obra"""
    existing = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    # Remover obra das máquinas
    await db.machines.update_many({"obra_id": obra_id}, {"$set": {"obra_id": None}})
    
    await db.obras.delete_one({"id": obra_id})
    return {"message": "Obra removida com sucesso"}


@obras_router.get("/{obra_id}/machines")
async def get_obra_machines(obra_id: str, current_user: dict = Depends(get_current_user)):
    """Listar máquinas de uma obra"""
    obra = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    machines = await db.machines.find({"obra_id": obra_id}, {"_id": 0}).to_list(1000)
    
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    return [MachineInObra(
        id=m["id"],
        name=m["name"],
        plate=m.get("plate", ""),
        category_name=category_map.get(m.get("category_id"), ""),
        brand=m.get("brand", ""),
        model=m.get("model", ""),
        status=m.get("status", "operational")
    ) for m in machines]


@obras_router.post("/{obra_id}/machines/{machine_id}")
async def add_machine_to_obra(obra_id: str, machine_id: str, current_user: dict = Depends(get_current_user)):
    """Adicionar máquina a uma obra"""
    obra = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    machine = await db.machines.find_one({"id": machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    await db.machines.update_one(
        {"id": machine_id},
        {"$set": {"obra_id": obra_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Máquina {machine['name']} adicionada à obra {obra['name']}"}


@obras_router.delete("/{obra_id}/machines/{machine_id}")
async def remove_machine_from_obra(obra_id: str, machine_id: str, current_user: dict = Depends(get_current_user)):
    """Remover máquina de uma obra"""
    machine = await db.machines.find_one({"id": machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    if machine.get("obra_id") != obra_id:
        raise HTTPException(status_code=400, detail="Máquina não pertence a esta obra")
    
    await db.machines.update_one(
        {"id": machine_id},
        {"$set": {"obra_id": None, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Máquina removida da obra"}


@obras_router.get("/{obra_id}/costs")
async def get_obra_costs(obra_id: str, current_user: dict = Depends(get_current_user)):
    """Obter resumo de custos da obra"""
    obra = await db.obras.find_one({"id": obra_id}, {"_id": 0})
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    machines = await db.machines.find({"obra_id": obra_id}, {"_id": 0}).to_list(1000)
    machine_ids = [m["id"] for m in machines]
    
    if not machine_ids:
        return {
            "obra_id": obra_id,
            "obra_name": obra["name"],
            "total_cost": 0,
            "preventive_cost": 0,
            "corrective_cost": 0,
            "machine_count": 0,
            "maintenance_count": 0
        }
    
    maintenances = await db.maintenances.find({
        "machine_id": {"$in": machine_ids}
    }, {"_id": 0}).to_list(10000)
    
    total_cost = 0
    preventive_cost = 0
    corrective_cost = 0
    
    for m in maintenances:
        cost = m.get("part_value", 0)
        total_cost += cost
        if m.get("maintenance_type") == "preventiva":
            preventive_cost += cost
        else:
            corrective_cost += cost
    
    return {
        "obra_id": obra_id,
        "obra_name": obra["name"],
        "total_cost": total_cost,
        "preventive_cost": preventive_cost,
        "corrective_cost": corrective_cost,
        "machine_count": len(machines),
        "maintenance_count": len(maintenances)
    }
