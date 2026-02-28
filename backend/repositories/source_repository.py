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
        source_url: str | None = None,
    ) -> Source:
        source = Source(
            file_name=file_name,
            file_type=file_type,
            content=content,
            source_url=source_url,
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def get_source(self, source_id: int) -> Source | None:
        return self.session.get(Source, source_id)

    def list_sources(self) -> list[Source]:
        return list(self.session.execute(select(Source).order_by(Source.id.desc())).scalars())
