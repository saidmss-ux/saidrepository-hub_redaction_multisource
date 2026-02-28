import asyncio
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.api.v1.router import router as v1_router
from backend.api.versioning import version_prefix
from backend.core.config import settings
from backend.db.models import (
    AuditEvent,
    BackgroundJob,
    BatchItem,
    BatchRun,
    Document,
    FeatureFlag,
    Project,
    RefreshToken,
    Source,
)  # noqa: F401
from backend.db.migrations import bootstrap_schema
from backend.db.session import engine
from backend.services.errors import ServiceError
from backend.services.logging_utils import configure_logging, log_event
from backend.services.metrics_service import inc_error_code, observe_request, render_prometheus
from backend.services.rate_limit_service import check_rate_limit
from backend.services.response import fail

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_schema(engine)
    yield


app = FastAPI(title="DocuHub API", version="0.5.0", lifespan=lifespan)
if settings.api_prefix != version_prefix("v1"):
    raise ValueError("API v1 prefix misconfigured; expected /api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
)

app.include_router(v1_router, prefix=settings.api_prefix)
_concurrency_semaphore = asyncio.Semaphore(settings.concurrency_limit)


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(render_prometheus(), media_type="text/plain; version=0.0.4")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id
    request.state.started_at = time.monotonic()

    try:
        check_rate_limit(request.client.host if request.client else "unknown")
    except ServiceError as exc:
        inc_error_code(exc.code)
        payload = fail(exc.code, exc.message, exc.details).model_dump()
        return JSONResponse(status_code=429, content=payload, headers={"x-request-id": request_id})

    try:
        await asyncio.wait_for(_concurrency_semaphore.acquire(), timeout=0.01)
    except TimeoutError:
        inc_error_code("over_capacity")
        payload = fail("over_capacity", "Server concurrency limit reached").model_dump()
        return JSONResponse(status_code=503, content=payload, headers={"x-request-id": request_id})

    try:
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - request.state.started_at) * 1000)
        observe_request(elapsed_ms)
        response.headers["x-request-id"] = request_id
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
        if settings.hsts_enabled:
            response.headers["strict-transport-security"] = "max-age=31536000; includeSubDomains"

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
    inc_error_code(exc.code)
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
    inc_error_code("validation_error")
    log_event(
        "validation_error",
        request_id=getattr(request.state, "request_id", None),
        errors=exc.errors(),
    )
    payload = fail("validation_error", "Invalid request payload", {"errors": exc.errors()}).model_dump()
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    inc_error_code("internal_error")
    log_event(
        "internal_error",
        request_id=getattr(request.state, "request_id", None),
        error=str(exc) if settings.app_env != "production" else "redacted",
    )
    payload = fail("internal_error", "An unexpected internal error occurred").model_dump()
    return JSONResponse(status_code=500, content=payload)
