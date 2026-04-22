"""
Dashboard — endpoint principal da página inicial do sistema.
Extraído de server.py na Sessão 32 Fase 2 Parte 2.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from utils.auth import get_current_user
from utils.database import db

dashboard_router = APIRouter(tags=["Dashboard"])


# ============================================================================
# MODELS (replicados do server.py para manter compatibilidade do response_model)
# ============================================================================

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


class CategoryMachineCount(BaseModel):
    category_id: str
    category_name: str
    category_color: str
    count: int


class DashboardStats(BaseModel):
    total_machines: int
    total_maintenances: int
    preventive_count: int
    corrective_count: int
    total_spent: float
    recent_maintenances: List[MaintenanceResponse]
    low_stock_count: int = 0
    oil_change_alerts: int = 0
    machines_by_category: List[CategoryMachineCount] = []


# ============================================================================
# ENDPOINT
# ============================================================================

@dashboard_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Estatísticas gerais do dashboard."""
    total_machines = await db.machines.count_documents({})

    maintenances = await db.maintenances.find({}, {"_id": 0}).to_list(1000)
    total_maintenances = len(maintenances)
    preventive_count = len([m for m in maintenances if m["maintenance_type"] == "preventiva"])
    corrective_count = len([m for m in maintenances if m["maintenance_type"] == "corretiva"])
    total_spent = sum(m["part_value"] for m in maintenances)

    recent = await db.maintenances.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)

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
        created_at=m["created_at"],
    ) for m in recent]

    # Oil change alerts
    oil_change_alerts = 0
    today = datetime.now(timezone.utc)
    for machine in machines:
        hours_since_change = machine.get("hours_since_oil_change", 0)
        hours_remaining = 500 - hours_since_change

        last_oil_change_date = machine.get("last_oil_change_date")
        if last_oil_change_date:
            try:
                last_change = datetime.fromisoformat(last_oil_change_date.replace("Z", "+00:00"))
                if last_change.tzinfo is None:
                    last_change = last_change.replace(tzinfo=timezone.utc)
            except Exception:
                last_change = datetime.strptime(last_oil_change_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_remaining = 365 - (today - last_change).days
        else:
            days_remaining = 365

        if hours_remaining <= 50 or days_remaining <= 60:
            oil_change_alerts += 1

    # Machines by category
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    category_map = {c["id"]: {"name": c["name"], "color": c.get("color", "#E31A1A")} for c in categories}

    category_counts: dict = {}
    for machine in machines:
        cat_id = machine.get("category_id")
        if cat_id:
            category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

    machines_by_category = []
    for cat_id, count in category_counts.items():
        cat_info = category_map.get(cat_id, {"name": "Sem categoria", "color": "#gray"})
        machines_by_category.append(CategoryMachineCount(
            category_id=cat_id,
            category_name=cat_info["name"],
            category_color=cat_info["color"],
            count=count,
        ))
    machines_by_category.sort(key=lambda x: x.count, reverse=True)

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
        oil_change_alerts=oil_change_alerts,
        machines_by_category=machines_by_category,
    )
