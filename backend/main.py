from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.response import ResponseEnvelope, success_response
from app.infra.database import create_all_tables
from app.middlewares import RequestLoggingMiddleware, register_cors, register_exception_handlers
from app.views import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize development database tables during application startup."""
    await create_all_tables()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

register_exception_handlers(app)
register_cors(app, settings)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/", response_model=ResponseEnvelope[dict[str, str]])
async def read_root() -> ResponseEnvelope[dict[str, str]]:
    """Return the API availability message."""
    return success_response({"message": "HerpLog API is running"})


@app.get("/health", response_model=ResponseEnvelope[dict[str, str]])
async def health_check() -> ResponseEnvelope[dict[str, str]]:
    """Return the API health status."""
    return success_response({"status": "ok"})
