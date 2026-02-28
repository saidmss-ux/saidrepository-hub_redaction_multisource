import base64
import hashlib
import hmac
import json
import time
from typing import Any

from backend.core.config import settings
from backend.services.errors import ServiceError


class AuthContext(dict):
    @property
    def user_id(self) -> str:
        return self.get("sub", "")

    @property
    def role(self) -> str:
        return self.get("role", "user")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def create_access_token(*, sub: str, role: str = "user", ttl_seconds: int | None = None) -> str:
    ttl = ttl_seconds or settings.jwt_ttl_seconds
    now = int(time.time())
    payload = {"sub": sub, "role": role, "iat": now, "exp": now + ttl}
    header = {"alg": "HS256", "typ": "JWT"}

    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = _b64url_encode(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def decode_access_token(token: str) -> AuthContext:
    parts = token.split(".")
    if len(parts) != 3:
        raise ServiceError(code="auth_invalid_token", message="Invalid authentication token")

    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_signature = _b64url_decode(encoded_signature)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise ServiceError(code="auth_invalid_signature", message="Invalid authentication signature")

    payload: dict[str, Any] = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    if int(payload.get("exp", 0)) <= int(time.time()):
        raise ServiceError(code="auth_token_expired", message="Authentication token expired")

    role = payload.get("role", "user")
    if role not in settings.auth_roles:
        raise ServiceError(code="auth_invalid_role", message="Invalid authentication role")

    return AuthContext(payload)
