from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import Source


class SourceRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_source(
        self,
        *,
        file_name: str,
        file_type: str,
        content: str,
        tenant_id: str,
        source_url: str | None = None,
    ) -> Source:
        source = Source(
            file_name=file_name,
            file_type=file_type,
            content=content,
            tenant_id=tenant_id,
            source_url=source_url,
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def get_source(self, source_id: int, *, tenant_id: str) -> Source | None:
        stmt = select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_sources(self, *, tenant_id: str) -> list[Source]:
        stmt = select(Source).where(Source.tenant_id == tenant_id).order_by(Source.id.desc())
        return list(self.session.execute(stmt).scalars())
