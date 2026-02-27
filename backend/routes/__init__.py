# Routes module initialization
from .rh import rh_router
from .admin import admin_router
from .machines import machines_router
from .chatbot import chatbot_router
from .storage import storage_router
from .exports import export_router
from .stock import stock_router
from .obras import obras_router

__all__ = ["rh_router", "admin_router", "machines_router", "chatbot_router", "storage_router", "export_router", "stock_router", "obras_router"]
