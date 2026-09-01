from starlette.requests import Request

from ..infra.cache.base import CacheClient


class RateLimiter:
    """Define the future cache-backed rate-limit dependency boundary."""

    def __init__(self, cache: CacheClient) -> None:
        self.cache = cache

    async def check(self, request: Request, limit: int, window_seconds: int) -> None:
        """Reserve the interface for a future Redis-backed limit check."""
        raise NotImplementedError("Rate limiting is not enabled")
