from fastapi import APIRouter

from helix_api.modules.auth.router import router as auth_router
from helix_api.modules.conversations.router import router as conversations_router
from helix_api.modules.customers.router import router as customers_router
from helix_api.modules.tenants.router import router as tenants_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(tenants_router)
api_router.include_router(customers_router)
api_router.include_router(conversations_router)
