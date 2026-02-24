from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional

# ============ USER MODELS ============

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

class AdminCreate(BaseModel):
    name: str
    email: str
    password: str

class AdminSetupRequest(BaseModel):
    email: str
    secret_key: str

class UserRoleUpdate(BaseModel):
    role: str

# ============ CATEGORY MODELS ============

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    created_at: str

# ============ MACHINE MODELS ============

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

# ============ MAINTENANCE MODELS ============

class MaintenanceCreate(BaseModel):
    machine_id: str
    part_name: str
    part_quantity: int = 1
    description: Optional[str] = ""
    cost: float = 0.0
    maintenance_date: Optional[str] = None

class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    machine_id: str
    machine_name: str
    machine_plate: str
    part_name: str
    part_quantity: int
    description: str
    cost: float
    maintenance_date: str
    created_at: str

# ============ STOCK MODELS ============

class StockItemCreate(BaseModel):
    name: str
    quantity: int
    unit: str
    min_quantity: Optional[int] = 0
    category: Optional[str] = ""
    location: Optional[str] = ""
    notes: Optional[str] = ""

class StockItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    quantity: int
    unit: str
    min_quantity: int
    category: str
    location: str
    notes: str
    created_at: str
    updated_at: Optional[str] = None

class StockMovementCreate(BaseModel):
    item_id: str
    type: str  # "entrada" or "saida"
    quantity: int
    reason: Optional[str] = ""

# ============ OBRA MODELS ============

class ObraCreate(BaseModel):
    name: str
    location: Optional[str] = ""
    client: Optional[str] = ""
    start_date: Optional[str] = None
    expected_end_date: Optional[str] = None
    notes: Optional[str] = ""

class ObraResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    location: str
    client: str
    start_date: Optional[str] = None
    expected_end_date: Optional[str] = None
    status: str
    notes: str
    created_at: str

# ============ TASK MODELS ============

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
