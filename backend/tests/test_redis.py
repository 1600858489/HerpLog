import pytest
from redis.exceptions import RedisError

from app.infra.redis import check_redis_connection, close_redis_client, create_redis_client


class FakeRedisClient:
    def __init__(self) -> None:
        self.closed = False

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        self.closed = True


async def test_redis_client_pings() -> None:
    client = FakeRedisClient()
    await check_redis_connection(client)


async def test_redis_client_is_closed() -> None:
    client = FakeRedisClient()
    await close_redis_client(client)
    assert client.closed


async def test_close_redis_client_without_client_is_noop() -> None:
    await close_redis_client(None)


def test_create_redis_client_uses_configured_settings() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    client = create_redis_client()
    kwargs = client.connection_pool.connection_kwargs
    assert kwargs["socket_timeout"] == settings.redis_socket_timeout
    assert kwargs["socket_connect_timeout"] == settings.redis_connect_timeout
    assert kwargs["health_check_interval"] == settings.redis_health_check_interval
    assert client.connection_pool.max_connections == settings.redis_max_connections


async def test_redis_ping_against_container() -> None:
    client = create_redis_client()
    try:
        assert await client.ping() is True
    finally:
        await client.aclose()
