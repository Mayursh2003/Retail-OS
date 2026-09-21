from fastapi import FastAPI

from app.api.v1.routes import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger


def create_application() -> FastAPI:
    """
    Application factory.

    Creates and configures the FastAPI application instance.
    """

    # Initialize centralized logging
    configure_logging()

    logger = get_logger(__name__)
    logger.info("Initializing FastAPI application.")

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.DEBUG,
    )

    app.include_router(
        api_router,
        prefix=settings.API_PREFIX,
    )

    logger.info("Application initialized successfully.")

    return app