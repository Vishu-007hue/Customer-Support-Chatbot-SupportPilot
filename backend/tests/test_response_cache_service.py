from app.services.response_cache_service import ResponseCacheService


def test_cache_set_and_get() -> None:
    cache = ResponseCacheService()
    cache.set("Greeting", "Hello")
    assert cache.get("Greeting") == "Hello"


def test_cache_missing_returns_none() -> None:
    cache = ResponseCacheService()
    assert cache.get("UnknownIntent") is None
