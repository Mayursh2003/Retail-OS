from datetime import datetime, timezone
from typing import Any, Dict

from app.core.config import get_settings


class HealthService:
    """
    Service responsible for exposing runtime health information.

    This class is intentionally lightweight and designed for future
    expansion with health checks for cameras, streaming, inference,
    resources, and dependencies.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def service_health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "service": "edge-runtime",
            "version": self._settings.APP_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def readiness(self) -> Dict[str, str]:
        return {
            "status": "ready",
        }

    def liveness(self) -> Dict[str, str]:
        return {
            "status": "alive",
        }