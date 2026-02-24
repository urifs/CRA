from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

import sys
sys.path.insert(0, '/app/backend')

from utils.database import db
from utils.auth import get_current_user
from utils.audit import create_audit_log
from models.core import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("", response_model=CategoryResponse)
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
    
    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="categoria",
        entity_id=category_id,
        entity_name=category.name,
        details=f"Categoria criada: {category.name}",
        module="Gerenciamento"
    )
    
    return CategoryResponse(**category_doc)

@router.get("")
async def list_categories(current_user: dict = Depends(get_current_user)):
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    return categories

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str, current_user: dict = Depends(get_current_user)):
    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return CategoryResponse(**category)

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, category: CategoryCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.categories.find_one({"id": category_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    await db.categories.update_one(
        {"id": category_id},
        {"$set": {"name": category.name, "description": category.description or ""}}
    )
    
    await create_audit_log(
        user=current_user,
        action="atualizar",
        entity_type="categoria",
        entity_id=category_id,
        entity_name=category.name,
        details=f"Categoria atualizada: {category.name}",
        module="Gerenciamento"
    )
    
    updated = await db.categories.find_one({"id": category_id}, {"_id": 0})
    return CategoryResponse(**updated)

@router.delete("/{category_id}")
async def delete_category(category_id: str, current_user: dict = Depends(get_current_user)):
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    machines_count = await db.machines.count_documents({"category_id": category_id})
    if machines_count > 0:
        raise HTTPException(status_code=400, detail=f"Não é possível excluir. Existem {machines_count} máquinas nesta categoria.")
    
    await db.categories.delete_one({"id": category_id})
    
    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="categoria",
        entity_id=category_id,
        entity_name=category.get("name", ""),
        details=f"Categoria excluída: {category.get('name', '')}",
        module="Gerenciamento"
    )
    
    return {"message": "Categoria excluída com sucesso"}
