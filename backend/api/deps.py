from fastapi import Depends, Header

from backend.core.config import settings
from backend.services.auth_service import AuthContext, decode_access_token
from backend.services.errors import ServiceError


def get_auth_context(authorization: str | None = Header(default=None)) -> AuthContext:
    if not authorization:
        raise ServiceError(code="auth_missing", message="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise ServiceError(code="auth_invalid_scheme", message="Authorization must be Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    return decode_access_token(token)


def get_tenant_id(ctx: AuthContext = Depends(get_auth_context)) -> str:
    tenant_id = ctx.tenant_id
    if settings.tenancy_enforced and not tenant_id:
        raise ServiceError(code="tenant_missing", message="Missing tenant context")
    return tenant_id or settings.default_tenant_id


def require_role(*allowed_roles: str):
    def _checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.role not in allowed_roles:
            raise ServiceError(code="auth_forbidden", message="Insufficient role privileges")
        return ctx

    return _checker
