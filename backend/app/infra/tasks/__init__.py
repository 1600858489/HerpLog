from backend.app.infra.tasks.base import BaseTask
from backend.app.infra.tasks.celery import get_celery_config

__all__ = ["BaseTask", "get_celery_config"]
