import time
from collections import defaultdict, deque

from backend.core.config import settings
from backend.services.errors import ServiceError

_rate_windows: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(key: str) -> None:
    now = time.time()
    window = _rate_windows[key]
    while window and now - window[0] > settings.rate_limit_window_s:
        window.popleft()

    if len(window) >= settings.rate_limit_requests:
        raise ServiceError(code="rate_limited", message="Too many requests")

    window.append(now)
