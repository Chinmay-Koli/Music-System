from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.library import router as library_router

__all__ = ["admin_router", "auth_router", "catalog_router", "library_router"]
