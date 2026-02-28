import time
from collections import defaultdict, deque
from dataclasses import dataclass

from backend.core.config import settings
from backend.services.errors import ServiceError
from backend.services.logging_utils import log_event

_rate_windows: dict[str, deque[float]] = defaultdict(deque)


class RateLimitBackend:
    def check(self, key: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class InMemoryRateLimitBackend(RateLimitBackend):
    def check(self, key: str) -> None:
        now = time.time()
        window = _rate_windows[key]
        while window and now - window[0] > settings.rate_limit_window_s:
            window.popleft()

        if len(window) >= settings.rate_limit_requests:
            raise ServiceError(code="rate_limited", message="Too many requests")

        window.append(now)


@dataclass
class RedisRateLimitBackend(RateLimitBackend):
    def check(self, key: str) -> None:
        log_event("rate_limit_redis_fallback", key=key)
        InMemoryRateLimitBackend().check(key)


def _resolve_backend() -> RateLimitBackend:
    if settings.rate_limit_backend == "redis":
        return RedisRateLimitBackend()
    return InMemoryRateLimitBackend()


def check_rate_limit(key: str) -> None:
    _resolve_backend().check(key)
