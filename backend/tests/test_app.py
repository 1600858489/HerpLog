from collections.abc import Callable, Awaitable

import pytest
from fastapi import APIRouter
from redis.exceptions import RedisError

from app.core.errors import BusinessError, ErrorCode
from main import app, lifespan


async def business_error_endpoint() -> None:
    raise BusinessError(ErrorCode.PET_NOT_FOUND)


async def unexpected_error_endpoint() -> None:
    raise RuntimeError("database password leaked")


async def validation_error_endpoint(value: int) -> int:
    return value


def include_test_route(path: str, handler: Callable[..., Awaitable[object]]) -> None:
    router = APIRouter()
    router.add_api_route(path, handler, methods=["GET"])
    app.include_router(router)


async def test_lifespan_tolerates_redis_unavailable(monkeypatch) -> None:
    async def fail_ping(client) -> None:
        raise RedisError("redis unavailable")

    disposed = False

    async def fake_dispose() -> None:
        nonlocal disposed
        disposed = True

    monkeypatch.setattr("main.check_redis_connection", fail_ping)
    monkeypatch.setattr("main.dispose_database", fake_dispose)
    async with lifespan(app):
        assert app.state.redis is None
    assert disposed


async def test_lifespan_closes_redis_and_database(monkeypatch) -> None:
    closed = False

    class FakeRedis:
        async def aclose(self) -> None:
            nonlocal closed
            closed = True

    disposed = False

    async def fake_dispose() -> None:
        nonlocal disposed
        disposed = True

    async def fake_ping(client) -> None:
        return None

    monkeypatch.setattr("main.create_redis_client", lambda: FakeRedis())
    monkeypatch.setattr("main.check_redis_connection", fake_ping)
    monkeypatch.setattr("main.dispose_database", fake_dispose)
    async with lifespan(app):
        assert isinstance(app.state.redis, FakeRedis)
    assert closed
    assert disposed


async def test_validation_error_is_safe(client) -> None:
    include_test_route("/test-validation-error", validation_error_endpoint)
    response = await client.get("/test-validation-error", params={"value": "invalid"})
    assert response.status_code == 422
    assert response.json()["code"] == int(ErrorCode.INVALID_REQUEST)
    assert "Traceback" not in response.text


async def test_health_uses_response_envelope(client) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok"},
    }


async def test_business_error_is_safe_and_mapped(client) -> None:
    include_test_route("/test-business-error", business_error_endpoint)
    response = await client.get("/test-business-error")
    assert response.status_code == 404
    assert response.json()["code"] == int(ErrorCode.PET_NOT_FOUND)
    assert response.json()["message"]
    assert "Traceback" not in response.text


async def test_unexpected_error_does_not_leak_python_text(client) -> None:
    include_test_route("/test-unexpected-error", unexpected_error_endpoint)
    response = await client.get("/test-unexpected-error")
    assert response.status_code == 500
    assert response.json()["message"]
    assert "database password leaked" not in response.text
    assert "Traceback" not in response.text
