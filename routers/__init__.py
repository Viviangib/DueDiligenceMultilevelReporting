

from fastapi import APIRouter
from routers.auth import router as auth_router
from routers.regulation import router as regulation_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(regulation_router)

