from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.v1.router import router as v1_router
from backend.core.config import settings
from backend.db.models import Source  # noqa: F401 (metadata registration)
from backend.db.session import Base, engine
from backend.services.response import fail

app = FastAPI(title="DocuHub API", version="0.3.0")
app.include_router(v1_router, prefix=settings.api_prefix)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    payload = fail("validation_error", "Invalid request payload", {"errors": exc.errors()}).model_dump()
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    payload = fail("internal_error", "An unexpected internal error occurred").model_dump()
    return JSONResponse(status_code=500, content=payload)
