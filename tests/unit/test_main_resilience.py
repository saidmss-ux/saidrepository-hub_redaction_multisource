import asyncio

from starlette.requests import Request

from backend.core.config import settings
from backend.main import (
    _concurrency_semaphore,
    request_context_middleware,
    service_exception_handler,
    unhandled_exception_handler,
)
from backend.services.errors import ServiceError


def _request(path: str = "/api/v1/health") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_service_error_handler_contract() -> None:
    response = asyncio.run(
        service_exception_handler(
            _request(),
            ServiceError(code="file_not_found", message="missing", details={"file_id": 1}),
        )
    )
    assert response.status_code == 400
    assert b'"success":false' in response.body


def test_unhandled_error_handler_contract() -> None:
    response = asyncio.run(unhandled_exception_handler(_request(), RuntimeError("boom")))
    assert response.status_code == 500
    assert b'"internal_error"' in response.body


def test_over_capacity_returns_503() -> None:
    async def _execute():
        for _ in range(settings.concurrency_limit):
            await _concurrency_semaphore.acquire()

        async def _call_next(request: Request):
            raise AssertionError("call_next should not execute when over capacity")

        try:
            return await request_context_middleware(_request(), _call_next)
        finally:
            for _ in range(settings.concurrency_limit):
                _concurrency_semaphore.release()

    response = asyncio.run(_execute())
    assert response.status_code == 503
    assert b'"over_capacity"' in response.body
