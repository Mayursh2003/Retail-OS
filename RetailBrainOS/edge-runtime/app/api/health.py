from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["Health"])

settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }