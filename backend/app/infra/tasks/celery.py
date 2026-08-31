from backend.app.core.config import get_settings


def get_celery_config() -> dict[str, str]:
    """Return future Celery broker and result backend configuration."""
    settings = get_settings()
    return {
        "broker_url": settings.redis_url,
        "result_backend": settings.redis_url,
    }
