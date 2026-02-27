"""
Machines Routes - Fleet and equipment management module
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import FileResponse
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
machines_router = APIRouter(tags=["Machines"])


# ============ MODELS ============

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    subcategories_count: int = 0
    created_at: str


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


class FleetCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class FleetResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    machines_count: int = 0
    created_at: str


class SubfleetCreate(BaseModel):
    name: str
    fleet_id: str
    description: Optional[str] = ""


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
    operator_id: Optional[str] = None
    identificador_tipo: Optional[str] = None
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
    maintenance_type: str
    description: Optional[str] = ""
    is_oil_change: bool = False


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


# ============ CATEGORIES ============

@machines_router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate):
    """Criar categoria de máquina"""
    category_id = str(uuid.uuid4())
    category_doc = {
        "id": category_id,
        "name": category.name,
        "description": category.description or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.categories.insert_one(category_doc)
    
    return CategoryResponse(
        id=category_id,
        name=category.name,
        description=category.description or "",
        created_at=category_doc["created_at"]
    )


@machines_router.get("/categories", response_model=List[CategoryResponse])
async def get_categories():
    """Listar categorias"""
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    return [CategoryResponse(
        id=c["id"],
        name=c["name"],
        description=c.get("description", ""),
        created_at=c["created_at"]
    ) for c in categories]


@machines_router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    """Excluir categoria"""
    existing = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    await db.categories.delete_one({"id": category_id})
    return {"message": "Categoria removida com sucesso"}


@machines_router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, category: CategoryCreate):
    """Atualizar categoria"""
    existing = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    await db.categories.update_one(
        {"id": category_id},
        {"$set": {"name": category.name, "description": category.description or ""}}
    )
    
    return CategoryResponse(
        id=category_id,
        name=category.name,
        description=category.description or "",
        created_at=existing["created_at"]
    )


# ============ SUBCATEGORIES ============

@machines_router.post("/subcategories", response_model=SubcategoryResponse)
async def create_subcategory(subcategory: SubcategoryCreate):
    """Criar subcategoria"""
    category = await db.categories.find_one({"id": subcategory.category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    subcategory_id = str(uuid.uuid4())
    subcategory_doc = {
        "id": subcategory_id,
        "name": subcategory.name,
        "category_id": subcategory.category_id,
        "description": subcategory.description or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.subcategories.insert_one(subcategory_doc)
    
    return SubcategoryResponse(
        id=subcategory_id,
        name=subcategory.name,
        category_id=subcategory.category_id,
        category_name=category["name"],
        description=subcategory.description or "",
        created_at=subcategory_doc["created_at"]
    )


@machines_router.get("/subcategories", response_model=List[SubcategoryResponse])
async def get_subcategories(category_id: Optional[str] = None):
    """Listar subcategorias"""
    query = {}
    if category_id:
        query["category_id"] = category_id
    
    subcategories = await db.subcategories.find(query, {"_id": 0}).to_list(100)
    result = []
    for s in subcategories:
        category = await db.categories.find_one({"id": s["category_id"]}, {"_id": 0})
        result.append(SubcategoryResponse(
            id=s["id"],
            name=s["name"],
            category_id=s["category_id"],
            category_name=category["name"] if category else "",
            description=s.get("description", ""),
            created_at=s["created_at"]
        ))
    return result


@machines_router.delete("/subcategories/{subcategory_id}")
async def delete_subcategory(subcategory_id: str):
    """Excluir subcategoria"""
    existing = await db.subcategories.find_one({"id": subcategory_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    await db.subcategories.delete_one({"id": subcategory_id})
    return {"message": "Subcategoria removida com sucesso"}


@machines_router.put("/subcategories/{subcategory_id}", response_model=SubcategoryResponse)
async def update_subcategory(subcategory_id: str, subcategory: SubcategoryCreate):
    """Atualizar subcategoria"""
    existing = await db.subcategories.find_one({"id": subcategory_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    
    await db.subcategories.update_one(
        {"id": subcategory_id},
        {"$set": {"name": subcategory.name, "description": subcategory.description or ""}}
    )
    
    category = await db.categories.find_one({"id": existing["category_id"]}, {"_id": 0})
    return SubcategoryResponse(
        id=subcategory_id,
        name=subcategory.name,
        category_id=existing["category_id"],
        category_name=category["name"] if category else "",
        description=subcategory.description or "",
        created_at=existing["created_at"]
    )


# ============ FLEETS ============

@machines_router.post("/fleets", response_model=FleetResponse)
async def create_fleet(fleet: FleetCreate):
    """Criar frota"""
    fleet_id = str(uuid.uuid4())
    fleet_doc = {
        "id": fleet_id,
        "name": fleet.name,
        "description": fleet.description or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.fleets.insert_one(fleet_doc)
    
    return FleetResponse(
        id=fleet_id,
        name=fleet.name,
        description=fleet.description or "",
        created_at=fleet_doc["created_at"]
    )


@machines_router.get("/fleets", response_model=List[FleetResponse])
async def get_fleets():
    """Listar frotas"""
    fleets = await db.fleets.find({}, {"_id": 0}).to_list(100)
    result = []
    for f in fleets:
        machines_count = await db.machines.count_documents({"fleet_id": f["id"]})
        result.append(FleetResponse(
            id=f["id"],
            name=f["name"],
            description=f.get("description", ""),
            machines_count=machines_count,
            created_at=f["created_at"]
        ))
    return result


@machines_router.delete("/fleets/{fleet_id}")
async def delete_fleet(fleet_id: str):
    """Excluir frota"""
    existing = await db.fleets.find_one({"id": fleet_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Frota não encontrada")
    await db.fleets.delete_one({"id": fleet_id})
    return {"message": "Frota removida com sucesso"}


@machines_router.put("/fleets/{fleet_id}", response_model=FleetResponse)
async def update_fleet(fleet_id: str, fleet: FleetCreate):
    """Atualizar frota"""
    existing = await db.fleets.find_one({"id": fleet_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Frota não encontrada")
    
    await db.fleets.update_one(
        {"id": fleet_id},
        {"$set": {"name": fleet.name, "description": fleet.description or ""}}
    )
    
    return FleetResponse(
        id=fleet_id,
        name=fleet.name,
        description=fleet.description or "",
        created_at=existing["created_at"]
    )


# ============ MACHINES ============

@machines_router.get("/machines", response_model=List[MachineResponse])
async def get_machines(
    category_id: Optional[str] = None,
    fleet_id: Optional[str] = None,
    obra_id: Optional[str] = None,
    status: Optional[str] = None
):
    """Listar máquinas"""
    query = {}
    if category_id:
        query["category_id"] = category_id
    if fleet_id:
        query["fleet_id"] = fleet_id
    if obra_id:
        query["obra_id"] = obra_id
    if status:
        query["status"] = status
    
    machines = await db.machines.find(query, {"_id": 0}).to_list(500)
    result = []
    
    for m in machines:
        category = await db.categories.find_one({"id": m.get("category_id")}, {"_id": 0})
        subcategory = await db.subcategories.find_one({"id": m.get("subcategory_id")}, {"_id": 0}) if m.get("subcategory_id") else None
        fleet = await db.fleets.find_one({"id": m.get("fleet_id")}, {"_id": 0}) if m.get("fleet_id") else None
        obra = await db.obras.find_one({"id": m.get("obra_id")}, {"_id": 0}) if m.get("obra_id") else None
        
        result.append(MachineResponse(
            id=m["id"],
            name=m["name"],
            plate=m.get("plate", ""),
            category_id=m.get("category_id", ""),
            category_name=category["name"] if category else "",
            subcategory_id=m.get("subcategory_id"),
            subcategory_name=subcategory["name"] if subcategory else "",
            brand=m.get("brand", ""),
            model=m.get("model", ""),
            year=m.get("year"),
            notes=m.get("notes", ""),
            status=m.get("status", "active"),
            obra_id=m.get("obra_id"),
            obra_name=obra["nome"] if obra else "",
            fleet_id=m.get("fleet_id"),
            fleet_name=fleet["name"] if fleet else "",
            subfleet_id=m.get("subfleet_id"),
            subfleet_name="",
            operator_id=m.get("operator_id"),
            operator_name=m.get("operator_name", ""),
            identificador_tipo=m.get("identificador_tipo"),
            identificador_numero=m.get("identificador_numero"),
            horimetro_atual=m.get("horimetro_atual"),
            created_at=m.get("created_at", "")
        ))
    
    return result


@machines_router.post("/machines", response_model=MachineResponse)
async def create_machine(machine: MachineCreate):
    """Criar máquina"""
    category = await db.categories.find_one({"id": machine.category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    machine_id = str(uuid.uuid4())
    machine_doc = {
        "id": machine_id,
        "name": machine.name,
        "plate": machine.plate or "",
        "category_id": machine.category_id,
        "subcategory_id": machine.subcategory_id,
        "brand": machine.brand or "",
        "model": machine.model or "",
        "year": machine.year,
        "notes": machine.notes or "",
        "status": "active",
        "obra_id": machine.obra_id,
        "fleet_id": machine.fleet_id,
        "subfleet_id": machine.subfleet_id,
        "operator_id": machine.operator_id,
        "identificador_tipo": machine.identificador_tipo,
        "identificador_numero": machine.identificador_numero,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.machines.insert_one(machine_doc)
    
    return MachineResponse(
        id=machine_id,
        name=machine.name,
        plate=machine.plate or "",
        category_id=machine.category_id,
        category_name=category["name"],
        subcategory_id=machine.subcategory_id,
        brand=machine.brand or "",
        model=machine.model or "",
        year=machine.year,
        notes=machine.notes or "",
        status="active",
        obra_id=machine.obra_id,
        fleet_id=machine.fleet_id,
        subfleet_id=machine.subfleet_id,
        operator_id=machine.operator_id,
        identificador_tipo=machine.identificador_tipo,
        identificador_numero=machine.identificador_numero,
        created_at=machine_doc["created_at"]
    )


@machines_router.get("/machines/{machine_id}", response_model=MachineResponse)
async def get_machine(machine_id: str):
    """Obter máquina por ID"""
    machine = await db.machines.find_one({"id": machine_id}, {"_id": 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    category = await db.categories.find_one({"id": machine.get("category_id")}, {"_id": 0})
    
    return MachineResponse(
        id=machine["id"],
        name=machine["name"],
        plate=machine.get("plate", ""),
        category_id=machine.get("category_id", ""),
        category_name=category["name"] if category else "",
        subcategory_id=machine.get("subcategory_id"),
        brand=machine.get("brand", ""),
        model=machine.get("model", ""),
        year=machine.get("year"),
        notes=machine.get("notes", ""),
        status=machine.get("status", "active"),
        obra_id=machine.get("obra_id"),
        fleet_id=machine.get("fleet_id"),
        subfleet_id=machine.get("subfleet_id"),
        operator_id=machine.get("operator_id"),
        identificador_tipo=machine.get("identificador_tipo"),
        identificador_numero=machine.get("identificador_numero"),
        horimetro_atual=machine.get("horimetro_atual"),
        created_at=machine.get("created_at", "")
    )


@machines_router.put("/machines/{machine_id}", response_model=MachineResponse)
async def update_machine(machine_id: str, machine: MachineCreate):
    """Atualizar máquina"""
    existing = await db.machines.find_one({"id": machine_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    update_data = machine.dict()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.machines.update_one({"id": machine_id}, {"$set": update_data})
    
    category = await db.categories.find_one({"id": machine.category_id}, {"_id": 0})
    
    return MachineResponse(
        id=machine_id,
        name=machine.name,
        plate=machine.plate or "",
        category_id=machine.category_id,
        category_name=category["name"] if category else "",
        subcategory_id=machine.subcategory_id,
        brand=machine.brand or "",
        model=machine.model or "",
        year=machine.year,
        notes=machine.notes or "",
        status=existing.get("status", "active"),
        obra_id=machine.obra_id,
        fleet_id=machine.fleet_id,
        subfleet_id=machine.subfleet_id,
        operator_id=machine.operator_id,
        identificador_tipo=machine.identificador_tipo,
        identificador_numero=machine.identificador_numero,
        created_at=existing.get("created_at", "")
    )


@machines_router.delete("/machines/{machine_id}")
async def delete_machine(machine_id: str):
    """Excluir máquina"""
    existing = await db.machines.find_one({"id": machine_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    await db.machines.delete_one({"id": machine_id})
    return {"message": "Máquina removida com sucesso"}


# ============ MAINTENANCES ============

@machines_router.get("/maintenances", response_model=List[MaintenanceResponse])
async def get_maintenances(
    machine_id: Optional[str] = None,
    maintenance_type: Optional[str] = None
):
    """Listar manutenções"""
    query = {}
    if machine_id:
        query["machine_id"] = machine_id
    if maintenance_type:
        query["maintenance_type"] = maintenance_type
    
    maintenances = await db.maintenances.find(query, {"_id": 0}).sort("replacement_date", -1).to_list(500)
    result = []
    
    for m in maintenances:
        machine = await db.machines.find_one({"id": m.get("machine_id")}, {"_id": 0})
        result.append(MaintenanceResponse(
            id=m["id"],
            machine_id=m.get("machine_id", ""),
            machine_name=machine["name"] if machine else "",
            machine_plate=machine.get("plate", "") if machine else "",
            part_name=m.get("part_name", ""),
            replacement_date=m.get("replacement_date", ""),
            part_value=m.get("part_value", 0),
            maintenance_type=m.get("maintenance_type", ""),
            description=m.get("description", ""),
            photos=m.get("photos", []),
            is_oil_change=m.get("is_oil_change", False),
            created_at=m.get("created_at", "")
        ))
    
    return result


@machines_router.post("/maintenances", response_model=MaintenanceResponse)
async def create_maintenance(maintenance: MaintenanceCreate):
    """Criar manutenção"""
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
        "photos": [],
        "is_oil_change": maintenance.is_oil_change,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.maintenances.insert_one(maintenance_doc)
    
    return MaintenanceResponse(
        id=maintenance_id,
        machine_id=maintenance.machine_id,
        machine_name=machine["name"],
        machine_plate=machine.get("plate", ""),
        part_name=maintenance.part_name,
        replacement_date=maintenance.replacement_date,
        part_value=maintenance.part_value,
        maintenance_type=maintenance.maintenance_type,
        description=maintenance.description or "",
        photos=[],
        is_oil_change=maintenance.is_oil_change,
        created_at=maintenance_doc["created_at"]
    )


@machines_router.delete("/maintenances/{maintenance_id}")
async def delete_maintenance(maintenance_id: str):
    """Excluir manutenção"""
    existing = await db.maintenances.find_one({"id": maintenance_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Manutenção não encontrada")
    await db.maintenances.delete_one({"id": maintenance_id})
    return {"message": "Manutenção removida com sucesso"}
