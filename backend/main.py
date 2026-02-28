import asyncio
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.v1.router import router as v1_router
from backend.api.versioning import version_prefix
from backend.core.config import settings
from backend.db.models import Source  # noqa: F401 (metadata registration)
from backend.db.session import Base, engine
from backend.services.errors import ServiceError
from backend.services.logging_utils import configure_logging, log_event
from backend.services.response import fail

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="DocuHub API", version="0.4.0", lifespan=lifespan)
if settings.api_prefix != version_prefix("v1"):
    raise ValueError("API v1 prefix misconfigured; expected /api/v1")
app.include_router(v1_router, prefix=settings.api_prefix)
_concurrency_semaphore = asyncio.Semaphore(settings.concurrency_limit)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id

    started_at = time.monotonic()
    try:
        await asyncio.wait_for(_concurrency_semaphore.acquire(), timeout=0.01)
    except TimeoutError:
        payload = fail("over_capacity", "Server concurrency limit reached").model_dump()
        return JSONResponse(status_code=503, content=payload, headers={"x-request-id": request_id})
    try:
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - started_at) * 1000)
        response.headers["x-request-id"] = request_id
        log_event(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )
        return response
    finally:
        _concurrency_semaphore.release()


@app.exception_handler(ServiceError)
async def service_exception_handler(request: Request, exc: ServiceError) -> JSONResponse:
    log_event(
        "service_error",
        request_id=getattr(request.state, "request_id", None),
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )
    payload = fail(exc.code, exc.message, exc.details).model_dump()
    return JSONResponse(status_code=400, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    log_event(
        "validation_error",
        request_id=getattr(request.state, "request_id", None),
        errors=exc.errors(),
    )
    payload = fail("validation_error", "Invalid request payload", {"errors": exc.errors()}).model_dump()
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log_event(
        "internal_error",
        request_id=getattr(request.state, "request_id", None),
        error=str(exc),
    )
    payload = fail("internal_error", "An unexpected internal error occurred").model_dump()
    return JSONResponse(status_code=500, content=payload)
