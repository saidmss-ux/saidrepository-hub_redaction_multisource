from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_token(
        self,
        *,
        tenant_id: str,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        role: str = "user",
        parent_token_hash: str | None = None,
    ) -> RefreshToken:
        record = RefreshToken(
            tenant_id=tenant_id,
            user_id=user_id,
            token_hash=token_hash,
            role=role,
            expires_at=expires_at,
            parent_token_hash=parent_token_hash,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.session.execute(stmt).scalar_one_or_none()

    def revoke_hash(self, token_hash: str) -> None:
        record = self.get_by_hash(token_hash)
        if not record or record.revoked_at is not None:
            return
        record.revoked_at = datetime.now(UTC)
        self.session.commit()

    def revoke_user_tokens(self, *, tenant_id: str, user_id: str) -> int:
        stmt = select(RefreshToken).where(
            RefreshToken.tenant_id == tenant_id,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        rows = list(self.session.execute(stmt).scalars())
        now = datetime.now(UTC)
        for row in rows:
            row.revoked_at = now
        if rows:
            self.session.commit()
        return len(rows)
