from datetime import datetime, timedelta

from app.config import settings


class ResponseCacheService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, datetime]] = {}

    def get(self, intent: str) -> str | None:
        cached = self._cache.get(intent)
        if not cached:
            return None
        value, expires_at = cached
        if datetime.utcnow() > expires_at:
            self._cache.pop(intent, None)
            return None
        return value

    def set(self, intent: str, reply: str) -> None:
        expires_at = datetime.utcnow() + timedelta(
            seconds=settings.response_cache_ttl_seconds
        )
        self._cache[intent] = (reply, expires_at)
