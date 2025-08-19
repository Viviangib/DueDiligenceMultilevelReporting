from fastapi import APIRouter
from routers.auth import router as auth_router
from routers.regulation import router as regulation_router
from routers.indicator import router as indicator_router
from routers.analysis import router as analysis_router
from routers.report import router as report_router
import logging
import os

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(regulation_router)
api_router.include_router(indicator_router)
api_router.include_router(analysis_router)
api_router.include_router(report_router)
