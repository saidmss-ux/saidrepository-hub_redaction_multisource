import json

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.models import AuditEvent
from backend.services.logging_utils import log_event


def record_audit_event(
    session: Session,
    *,
    tenant_id: str,
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str,
    outcome: str,
    request_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    if not settings.audit_enabled:
        return

    event = AuditEvent(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome=outcome,
        request_id=request_id,
        metadata_json=json.dumps(metadata or {}, separators=(",", ":")),
    )
    try:
        session.add(event)
        session.commit()
    except Exception:
        session.rollback()
        log_event("audit_write_failed", tenant_id=tenant_id, action=action, target_type=target_type, target_id=target_id)
        if settings.audit_strict_mode:
            raise
