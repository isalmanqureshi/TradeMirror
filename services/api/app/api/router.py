from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.enrichment import router as enrichment_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(uploads_router)
api_router.include_router(enrichment_router)

api_router.include_router(analytics_router)

api_router.include_router(chat_router)
