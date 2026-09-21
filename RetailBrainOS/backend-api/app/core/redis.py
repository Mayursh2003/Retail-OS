from __future__ import annotations

from redis import Redis

from app.core.config import settings

_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """
    Return a singleton Redis client.

    The client is lazily initialized on first use and reused for the
    lifetime of the application.
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    return _redis_client


def close_redis_connection() -> None:
    """
    Close the Redis connection if it has been initialized.
    """
    global _redis_client

    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None