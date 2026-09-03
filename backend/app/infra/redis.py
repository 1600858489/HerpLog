import logging

from redis.asyncio import Redis

from ..core.config import get_settings


logger = logging.getLogger(__name__)


def create_redis_client() -> Redis:
    """Create the process-level Redis client with configured pool behavior."""
    settings = get_settings()
    return Redis.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        socket_connect_timeout=settings.redis_connect_timeout,
        socket_timeout=settings.redis_socket_timeout,
        health_check_interval=settings.redis_health_check_interval,
        decode_responses=True,
    )


async def check_redis_connection(client: Redis) -> None:
    """Verify Redis reachability with one ping."""
    await client.ping()


async def close_redis_client(client: Redis | None) -> None:
    """Close the Redis client and release its connection pool when present."""
    if client is None:
        return
    try:
        await client.aclose()
    except Exception:
        logger.warning("failed to close Redis client cleanly", exc_info=True)


__all__ = ["check_redis_connection", "close_redis_client", "create_redis_client"]
