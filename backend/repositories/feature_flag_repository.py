from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import FeatureFlag


class FeatureFlagRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, *, scope: str, scope_id: str, key: str, enabled: bool) -> FeatureFlag:
        stmt = select(FeatureFlag).where(
            FeatureFlag.scope == scope,
            FeatureFlag.scope_id == scope_id,
            FeatureFlag.key == key,
        )
        row = self.session.execute(stmt).scalar_one_or_none()
        if row is None:
            row = FeatureFlag(scope=scope, scope_id=scope_id, key=key, enabled=enabled)
            self.session.add(row)
        else:
            row.enabled = enabled
        self.session.commit()
        self.session.refresh(row)
        return row

    def get(self, *, scope: str, scope_id: str, key: str) -> FeatureFlag | None:
        stmt = select(FeatureFlag).where(
            FeatureFlag.scope == scope,
            FeatureFlag.scope_id == scope_id,
            FeatureFlag.key == key,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def resolve_for_tenant(self, *, key: str, tenant_id: str) -> bool | None:
        tenant_flag = self.get(scope="tenant", scope_id=tenant_id, key=key)
        if tenant_flag is not None:
            return bool(tenant_flag.enabled)

        global_flag = self.get(scope="global", scope_id="*", key=key)
        if global_flag is not None:
            return bool(global_flag.enabled)

        return None
