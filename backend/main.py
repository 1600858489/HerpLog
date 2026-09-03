import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.response import ResponseEnvelope, success_response
from app.infra.database import dispose_database
from app.infra.redis import check_redis_connection, close_redis_client, create_redis_client
from app.middlewares import RequestLoggingMiddleware, register_cors, register_exception_handlers
from app.views import auth_router, pet_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize optional Redis, then release Redis and database resources on shutdown."""
    redis_client = None
    try:
        redis_client = create_redis_client()
        await check_redis_connection(redis_client)
        app.state.redis = redis_client
    except RedisError as exc:
        logger.warning("Redis unavailable, continuing without it: %s", exc)
        app.state.redis = None
    try:
        yield
    finally:
        await close_redis_client(redis_client)
        await dispose_database()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

register_exception_handlers(app)
register_cors(app, settings)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(pet_router, prefix="/api/v1", tags=["pets"])


@app.get("/", response_model=ResponseEnvelope[dict[str, str]])
async def read_root() -> ResponseEnvelope[dict[str, str]]:
    """Return the API availability message."""
    return success_response({"message": "HerpLog API is running"})


@app.get("/health", response_model=ResponseEnvelope[dict[str, str]])
async def health_check() -> ResponseEnvelope[dict[str, str]]:
    """Return the API health status."""
    return success_response({"status": "ok"})
