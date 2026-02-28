from sqlalchemy.orm import Session

from backend.repositories.feature_flag_repository import FeatureFlagRepository
from backend.services.audit_service import record_audit_event
from backend.services.errors import ServiceError

_ALLOWED_SCOPES = {"global", "tenant"}


def _repo(session: Session) -> FeatureFlagRepository:
    return FeatureFlagRepository(session)


def set_feature_flag(
    session: Session,
    *,
    key: str,
    enabled: bool,
    scope: str,
    scope_id: str,
    actor_id: str,
    actor_tenant_id: str,
) -> dict:
    normalized_scope = scope.strip().lower()
    if normalized_scope not in _ALLOWED_SCOPES:
        raise ServiceError(code="feature_flag_scope_invalid", message="Invalid feature flag scope")

    if normalized_scope == "tenant" and not scope_id:
        raise ServiceError(code="feature_flag_scope_id_required", message="Tenant scope requires scope_id")

    if normalized_scope == "global":
        scope_id = "*"

    row = _repo(session).upsert(scope=normalized_scope, scope_id=scope_id, key=key.strip(), enabled=enabled)
    record_audit_event(
        session,
        tenant_id=actor_tenant_id,
        actor_id=actor_id,
        action="feature_flag.override",
        target_type="feature_flag",
        target_id=f"{row.scope}:{row.scope_id}:{row.key}",
        outcome="success",
        metadata={"enabled": row.enabled},
    )
    return {
        "key": row.key,
        "scope": row.scope,
        "scope_id": row.scope_id,
        "enabled": bool(row.enabled),
    }


def get_effective_flag(session: Session, *, key: str, tenant_id: str, default: bool = False) -> bool:
    resolved = _repo(session).resolve_for_tenant(key=key, tenant_id=tenant_id)
    if resolved is None:
        return default
    return resolved
