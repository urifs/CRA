# Routes module initialization
from .rh import rh_router
from .admin import admin_router
from .machines import machines_router

__all__ = ["rh_router", "admin_router", "machines_router"]
