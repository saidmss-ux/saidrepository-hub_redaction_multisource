from fastapi import Depends, Header

from backend.services.auth_service import AuthContext, decode_access_token
from backend.services.errors import ServiceError


def get_auth_context(authorization: str | None = Header(default=None)) -> AuthContext:
    if not authorization:
        raise ServiceError(code="auth_missing", message="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise ServiceError(code="auth_invalid_scheme", message="Authorization must be Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    return decode_access_token(token)


def require_role(*allowed_roles: str):
    def _checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.role not in allowed_roles:
            raise ServiceError(code="auth_forbidden", message="Insufficient role privileges")
        return ctx

    return _checker
