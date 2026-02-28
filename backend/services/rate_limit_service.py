import socket
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from urllib.parse import urlparse

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
    def _resp_encode(self, *parts: str) -> bytes:
        payload = [f"*{len(parts)}\r\n".encode("utf-8")]
        for part in parts:
            b = part.encode("utf-8")
            payload.append(f"${len(b)}\r\n".encode("utf-8"))
            payload.append(b + b"\r\n")
        return b"".join(payload)

    def _read_line(self, sock: socket.socket) -> bytes:
        data = bytearray()
        while True:
            ch = sock.recv(1)
            if not ch:
                raise RuntimeError("redis connection closed")
            data += ch
            if data.endswith(b"\r\n"):
                return bytes(data[:-2])

    def _read_resp(self, sock: socket.socket):
        first = sock.recv(1)
        if not first:
            raise RuntimeError("redis connection closed")
        if first == b":":
            return int(self._read_line(sock))
        if first == b"+":
            return self._read_line(sock).decode("utf-8")
        if first == b"-":
            raise RuntimeError(self._read_line(sock).decode("utf-8"))
        if first == b"$":
            size = int(self._read_line(sock))
            if size == -1:
                return None
            data = sock.recv(size)
            sock.recv(2)
            return data.decode("utf-8")
        raise RuntimeError("unsupported redis response")

    def _redis_incr(self, key: str) -> int:
        parsed = urlparse(settings.rate_limit_redis_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        db_index = (parsed.path or "/0").lstrip("/") or "0"

        with socket.create_connection((host, port), timeout=1.0) as sock:
            if parsed.password:
                sock.sendall(self._resp_encode("AUTH", parsed.password))
                self._read_resp(sock)

            sock.sendall(self._resp_encode("SELECT", db_index))
            self._read_resp(sock)

            sock.sendall(self._resp_encode("INCR", key))
            count = self._read_resp(sock)
            sock.sendall(self._resp_encode("EXPIRE", key, str(settings.rate_limit_window_s)))
            self._read_resp(sock)
            return int(count)

    def check(self, key: str) -> None:
        redis_key = f"rate:{key}"
        try:
            current = self._redis_incr(redis_key)
        except Exception as exc:
            log_event("rate_limit_redis_fallback", key=key, reason=str(exc))
            InMemoryRateLimitBackend().check(key)
            return

        if current > settings.rate_limit_requests:
            raise ServiceError(code="rate_limited", message="Too many requests")


def _resolve_backend() -> RateLimitBackend:
    if settings.rate_limit_backend == "redis":
        return RedisRateLimitBackend()
    return InMemoryRateLimitBackend()


def check_rate_limit(key: str) -> None:
    _resolve_backend().check(key)
