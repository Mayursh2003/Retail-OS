from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()


def create_application() -> FastAPI:
    """
    Application factory for the Edge Runtime service.
    """

    configure_logging()

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    application.include_router(api_router)

    return application