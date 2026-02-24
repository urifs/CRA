from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
import uuid

import sys
sys.path.insert(0, '/app/backend')

from utils.database import db
from utils.auth import hash_password, verify_password, create_token, get_current_user, security
from utils.audit import create_audit_log
from models.core import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    AdminCreate, AdminSetupRequest, UserRoleUpdate
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
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
        "role": "gerenciamento",
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

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
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

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        role=current_user.get("role", "gerenciamento"),
        created_at=current_user["created_at"]
    )

@router.post("/create-admin")
async def create_admin_account(data: AdminCreate):
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
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    return {"message": "Conta administrador criada com sucesso!", "email": data.email}

@router.post("/setup-admin")
async def setup_admin(request: AdminSetupRequest):
    SETUP_SECRET = "CRA-SETUP-2026-ADMIN"
    
    if request.secret_key != SETUP_SECRET:
        raise HTTPException(status_code=403, detail="Chave secreta inválida")
    
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"role": "admin"}}
    )
    
    return {
        "message": f"Usuário {request.email} promovido para administrador com sucesso!",
        "email": request.email,
        "new_role": "admin"
    }
