from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.enrichment import router as enrichment_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(uploads_router)
api_router.include_router(enrichment_router)
