"""
Stock Routes - Inventory management module
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
stock_router = APIRouter(prefix="/stock", tags=["Stock"])


# ============ MODELS ============

class StockCategoryCreate(BaseModel):
    name: str


class StockCategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    subcategories_count: int = 0
    created_at: str


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
    category: Optional[str] = ""
    subcategory_id: Optional[str] = None
    unit: str = "un"
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


# ============ STOCK CATEGORIES ============

@stock_router.post("/categories", response_model=StockCategoryResponse)
async def create_stock_category(category: StockCategoryCreate, current_user: dict = Depends(get_current_user)):
    """Criar categoria de estoque"""
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
    
    return StockCategoryResponse(
        id=category_id,
        name=category.name,
        created_at=category_doc["created_at"]
    )


@stock_router.get("/categories", response_model=List[StockCategoryResponse])
async def get_stock_categories(current_user: dict = Depends(get_current_user)):
    """Listar categorias de estoque"""
    categories = await db.stock_categories.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    return [StockCategoryResponse(
        id=c["id"],
        name=c["name"],
        created_at=c["created_at"]
    ) for c in categories]


@stock_router.delete("/categories/{category_id}")
async def delete_stock_category(category_id: str, current_user: dict = Depends(get_current_user)):
    """Excluir categoria de estoque"""
    existing = await db.stock_categories.find_one({"id": category_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    await db.stock_categories.delete_one({"id": category_id})
    return {"message": "Categoria removida com sucesso"}


# ============ STOCK SUBCATEGORIES ============

@stock_router.post("/subcategories", response_model=StockSubcategoryResponse)
async def create_stock_subcategory(subcategory: StockSubcategoryCreate, current_user: dict = Depends(get_current_user)):
    """Criar subcategoria de estoque"""
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
    
    return StockSubcategoryResponse(**doc, category_name=category["name"])


@stock_router.get("/subcategories", response_model=List[StockSubcategoryResponse])
async def list_stock_subcategories(category_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Listar subcategorias de estoque"""
    query = {"category_id": category_id} if category_id else {}
    subcategories = await db.stock_subcategories.find(query, {"_id": 0}).to_list(500)
    
    categories = await db.stock_categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    return [StockSubcategoryResponse(**s, category_name=category_map.get(s["category_id"], "")) for s in subcategories]


@stock_router.delete("/subcategories/{subcategory_id}")
async def delete_stock_subcategory(subcategory_id: str, current_user: dict = Depends(get_current_user)):
    """Excluir subcategoria de estoque"""
    subcategory = await db.stock_subcategories.find_one({"id": subcategory_id}, {"_id": 0})
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    
    await db.stock_items.update_many({"subcategory_id": subcategory_id}, {"$set": {"subcategory_id": None}})
    await db.stock_subcategories.delete_one({"id": subcategory_id})
    
    return {"message": "Subcategoria removida com sucesso"}


# ============ STOCK ITEMS ============

@stock_router.post("/items", response_model=StockItemResponse)
async def create_stock_item(item: StockItemCreate, current_user: dict = Depends(get_current_user)):
    """Criar item de estoque"""
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Gerar código se não fornecido
    code = item.code
    if not code:
        count = await db.stock_items.count_documents({})
        code = f"EST{count + 1:04d}"
    
    item_doc = {
        "id": item_id,
        "name": item.name,
        "code": code,
        "category": item.category or "",
        "subcategory_id": item.subcategory_id,
        "unit": item.unit,
        "quantity": item.quantity,
        "min_quantity": item.min_quantity,
        "unit_price": item.unit_price or 0,
        "location": item.location or "",
        "notes": item.notes or "",
        "created_by": current_user["id"],
        "created_at": now
    }
    await db.stock_items.insert_one(item_doc)
    
    # Obter nome da subcategoria
    subcategory_name = ""
    if item.subcategory_id:
        subcat = await db.stock_subcategories.find_one({"id": item.subcategory_id}, {"_id": 0})
        if subcat:
            subcategory_name = subcat["name"]
    
    return StockItemResponse(
        id=item_id,
        name=item.name,
        code=code,
        category=item.category or "",
        subcategory_id=item.subcategory_id,
        subcategory_name=subcategory_name,
        unit=item.unit,
        quantity=item.quantity,
        min_quantity=item.min_quantity,
        unit_price=item.unit_price or 0,
        location=item.location or "",
        notes=item.notes or "",
        is_low_stock=item.quantity <= item.min_quantity,
        created_at=now
    )


@stock_router.get("/items", response_model=List[StockItemResponse])
async def get_stock_items(
    category: Optional[str] = None,
    subcategory_id: Optional[str] = None,
    low_stock_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Listar itens de estoque"""
    query = {}
    if category:
        query["category"] = category
    if subcategory_id:
        query["subcategory_id"] = subcategory_id
    
    items = await db.stock_items.find(query, {"_id": 0}).sort("name", 1).to_list(1000)
    
    # Obter nomes das subcategorias
    subcategories = await db.stock_subcategories.find({}, {"_id": 0}).to_list(500)
    subcat_map = {s["id"]: s["name"] for s in subcategories}
    
    result = []
    for item in items:
        is_low = item.get("quantity", 0) <= item.get("min_quantity", 0)
        
        if low_stock_only and not is_low:
            continue
        
        result.append(StockItemResponse(
            id=item["id"],
            name=item["name"],
            code=item.get("code", ""),
            category=item.get("category", ""),
            subcategory_id=item.get("subcategory_id"),
            subcategory_name=subcat_map.get(item.get("subcategory_id"), ""),
            unit=item.get("unit", "un"),
            quantity=item.get("quantity", 0),
            min_quantity=item.get("min_quantity", 0),
            unit_price=item.get("unit_price", 0),
            location=item.get("location", ""),
            notes=item.get("notes", ""),
            is_low_stock=is_low,
            created_at=item.get("created_at", "")
        ))
    
    return result


@stock_router.get("/items/{item_id}", response_model=StockItemResponse)
async def get_stock_item(item_id: str, current_user: dict = Depends(get_current_user)):
    """Obter item de estoque por ID"""
    item = await db.stock_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    subcategory_name = ""
    if item.get("subcategory_id"):
        subcat = await db.stock_subcategories.find_one({"id": item["subcategory_id"]}, {"_id": 0})
        if subcat:
            subcategory_name = subcat["name"]
    
    return StockItemResponse(
        id=item["id"],
        name=item["name"],
        code=item.get("code", ""),
        category=item.get("category", ""),
        subcategory_id=item.get("subcategory_id"),
        subcategory_name=subcategory_name,
        unit=item.get("unit", "un"),
        quantity=item.get("quantity", 0),
        min_quantity=item.get("min_quantity", 0),
        unit_price=item.get("unit_price", 0),
        location=item.get("location", ""),
        notes=item.get("notes", ""),
        is_low_stock=item.get("quantity", 0) <= item.get("min_quantity", 0),
        created_at=item.get("created_at", "")
    )


@stock_router.put("/items/{item_id}", response_model=StockItemResponse)
async def update_stock_item(item_id: str, item: StockItemCreate, current_user: dict = Depends(get_current_user)):
    """Atualizar item de estoque"""
    existing = await db.stock_items.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    update_data = {
        "name": item.name,
        "code": item.code or existing.get("code", ""),
        "category": item.category or "",
        "subcategory_id": item.subcategory_id,
        "unit": item.unit,
        "quantity": item.quantity,
        "min_quantity": item.min_quantity,
        "unit_price": item.unit_price or 0,
        "location": item.location or "",
        "notes": item.notes or "",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.stock_items.update_one({"id": item_id}, {"$set": update_data})
    
    subcategory_name = ""
    if item.subcategory_id:
        subcat = await db.stock_subcategories.find_one({"id": item.subcategory_id}, {"_id": 0})
        if subcat:
            subcategory_name = subcat["name"]
    
    return StockItemResponse(
        id=item_id,
        name=item.name,
        code=item.code or existing.get("code", ""),
        category=item.category or "",
        subcategory_id=item.subcategory_id,
        subcategory_name=subcategory_name,
        unit=item.unit,
        quantity=item.quantity,
        min_quantity=item.min_quantity,
        unit_price=item.unit_price or 0,
        location=item.location or "",
        notes=item.notes or "",
        is_low_stock=item.quantity <= item.min_quantity,
        created_at=existing.get("created_at", "")
    )


@stock_router.delete("/items/{item_id}")
async def delete_stock_item(item_id: str, current_user: dict = Depends(get_current_user)):
    """Excluir item de estoque"""
    existing = await db.stock_items.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    await db.stock_items.delete_one({"id": item_id})
    return {"message": "Item removido com sucesso"}


# ============ STOCK MOVEMENTS ============

@stock_router.post("/movements", response_model=StockMovementResponse)
async def create_stock_movement(movement: StockMovementCreate, current_user: dict = Depends(get_current_user)):
    """Registrar movimentação de estoque"""
    item = await db.stock_items.find_one({"id": movement.item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    previous_quantity = item.get("quantity", 0)
    
    if movement.movement_type == "entrada":
        new_quantity = previous_quantity + movement.quantity
    elif movement.movement_type == "saida":
        if movement.quantity > previous_quantity:
            raise HTTPException(status_code=400, detail="Quantidade insuficiente em estoque")
        new_quantity = previous_quantity - movement.quantity
    else:
        raise HTTPException(status_code=400, detail="Tipo de movimentação inválido")
    
    # Atualizar quantidade do item
    await db.stock_items.update_one(
        {"id": movement.item_id},
        {"$set": {"quantity": new_quantity, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Registrar movimentação
    movement_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
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
        "created_at": now
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
        created_at=now
    )


@stock_router.get("/movements", response_model=List[StockMovementResponse])
async def get_stock_movements(
    item_id: Optional[str] = None,
    movement_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Listar movimentações de estoque"""
    query = {}
    if item_id:
        query["item_id"] = item_id
    if movement_type:
        query["movement_type"] = movement_type
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Obter nomes dos itens
    items = await db.stock_items.find({}, {"_id": 0}).to_list(1000)
    item_map = {i["id"]: i["name"] for i in items}
    
    return [StockMovementResponse(
        id=m["id"],
        item_id=m["item_id"],
        item_name=item_map.get(m["item_id"], ""),
        movement_type=m["movement_type"],
        quantity=m["quantity"],
        previous_quantity=m.get("previous_quantity", 0),
        new_quantity=m.get("new_quantity", 0),
        reason=m.get("reason", ""),
        notes=m.get("notes", ""),
        created_at=m["created_at"]
    ) for m in movements]


# ============ STOCK ALERTS ============

@stock_router.get("/alerts")
async def get_stock_alerts(current_user: dict = Depends(get_current_user)):
    """Obter alertas de estoque baixo"""
    items = await db.stock_items.find({}, {"_id": 0}).to_list(1000)
    
    alerts = []
    for item in items:
        qty = item.get("quantity", 0)
        min_qty = item.get("min_quantity", 0)
        
        if qty == 0:
            alerts.append({
                "item_id": item["id"],
                "item_name": item["name"],
                "type": "empty",
                "message": f"ESTOQUE ZERADO: {item['name']}",
                "quantity": qty,
                "min_quantity": min_qty,
                "urgency": "critical"
            })
        elif qty <= min_qty:
            alerts.append({
                "item_id": item["id"],
                "item_name": item["name"],
                "type": "low",
                "message": f"Estoque baixo: {item['name']} ({qty} {item.get('unit', 'un')})",
                "quantity": qty,
                "min_quantity": min_qty,
                "urgency": "warning"
            })
    
    return {
        "total": len(alerts),
        "critical": len([a for a in alerts if a["urgency"] == "critical"]),
        "warning": len([a for a in alerts if a["urgency"] == "warning"]),
        "alerts": alerts
    }
