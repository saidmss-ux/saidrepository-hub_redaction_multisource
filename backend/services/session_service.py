import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.repositories.refresh_token_repository import RefreshTokenRepository
from backend.services.audit_service import record_audit_event
from backend.services.auth_service import create_access_token
from backend.services.errors import ServiceError


def _repo(session: Session) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl_s)


def issue_token_pair(session: Session, *, user_id: str, role: str, tenant_id: str) -> dict:
    access_token = create_access_token(sub=user_id, role=role, tenant_id=tenant_id)
    refresh_token = secrets.token_urlsafe(48)
    _repo(session).create_token(
        tenant_id=tenant_id,
        user_id=user_id,
        token_hash=_hash_token(refresh_token),
        expires_at=_expires_at(),
        role=role,
    )
    record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=user_id,
        action="auth.token.issue",
        target_type="session",
        target_id=user_id,
        outcome="success",
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_token_pair(session: Session, *, refresh_token: str) -> dict:
    hashed = _hash_token(refresh_token)
    record = _repo(session).get_by_hash(hashed)
    if not record:
        raise ServiceError(code="auth_refresh_invalid", message="Invalid refresh token")

    now = datetime.now(UTC)
    record_expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=UTC)
    if record_expires_at <= now:
        raise ServiceError(code="auth_refresh_expired", message="Refresh token expired")

    if record.revoked_at is not None:
        if settings.refresh_reuse_detection:
            _repo(session).revoke_user_tokens(tenant_id=record.tenant_id, user_id=record.user_id)
        raise ServiceError(code="auth_refresh_revoked", message="Refresh token revoked")

    if settings.refresh_rotation_enabled:
        _repo(session).revoke_hash(hashed)
        next_refresh = secrets.token_urlsafe(48)
        _repo(session).create_token(
            tenant_id=record.tenant_id,
            user_id=record.user_id,
            token_hash=_hash_token(next_refresh),
            parent_token_hash=hashed,
            expires_at=_expires_at(),
            role=record.role,
        )
    else:
        next_refresh = refresh_token

    access_token = create_access_token(sub=record.user_id, role=record.role, tenant_id=record.tenant_id)
    record_audit_event(
        session,
        tenant_id=record.tenant_id,
        actor_id=record.user_id,
        action="auth.token.refresh",
        target_type="session",
        target_id=record.user_id,
        outcome="success",
    )
    return {
        "access_token": access_token,
        "refresh_token": next_refresh,
        "token_type": "bearer",
        "tenant_id": record.tenant_id,
    }


def revoke_user_sessions(session: Session, *, tenant_id: str, user_id: str) -> dict:
    revoked = _repo(session).revoke_user_tokens(tenant_id=tenant_id, user_id=user_id)
    record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=user_id,
        action="auth.token.revoke",
        target_type="session",
        target_id=user_id,
        outcome="success",
        metadata={"revoked": revoked},
    )
    return {"revoked": revoked, "tenant_id": tenant_id, "user_id": user_id}
