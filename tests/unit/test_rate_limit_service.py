import pytest

from backend.services.errors import ServiceError
from backend.services.rate_limit_service import (
    RedisRateLimitBackend,
    _rate_windows,
    check_rate_limit,
)


def test_rate_limit_blocks_when_threshold_reached(monkeypatch):
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_requests", 1)
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_window_s", 60)
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_backend", "memory")
    _rate_windows.clear()

    check_rate_limit("k1")
    with pytest.raises(ServiceError) as err:
        check_rate_limit("k1")
    assert err.value.code == "rate_limited"


def test_redis_backend_uses_counter_and_blocks(monkeypatch):
    backend = RedisRateLimitBackend()
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_requests", 2)
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_backend", "redis")

    values = iter([1, 2, 3])
    monkeypatch.setattr(backend, "_redis_incr", lambda _key: next(values))

    backend.check("tenant:user:route")
    backend.check("tenant:user:route")
    with pytest.raises(ServiceError) as err:
        backend.check("tenant:user:route")
    assert err.value.code == "rate_limited"


def test_redis_backend_falls_back_to_memory(monkeypatch):
    backend = RedisRateLimitBackend()
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_requests", 1)
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_window_s", 60)
    monkeypatch.setattr(backend, "_redis_incr", lambda _key: (_ for _ in ()).throw(RuntimeError("redis down")))
    _rate_windows.clear()

    backend.check("k2")
    with pytest.raises(ServiceError) as err:
        backend.check("k2")
    assert err.value.code == "rate_limited"
