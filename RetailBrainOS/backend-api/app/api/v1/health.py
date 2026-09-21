from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check",
    response_description="Backend service health status",
)
async def health() -> dict:
    """
    Health endpoint.

    Used to verify that the backend service is running.
    """

    return {
        "status": "healthy",
        "service": "backend-api",
        "version": "0.1.0",
    }