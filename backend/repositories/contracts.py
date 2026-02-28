from typing import Protocol

from backend.db.models import Source


class SourceRepositoryProtocol(Protocol):
    def create_source(
        self,
        *,
        file_name: str,
        file_type: str,
        content: str,
        source_url: str | None = None,
    ) -> Source: ...

    def get_source(self, source_id: int) -> Source | None: ...

    def list_sources(self) -> list[Source]: ...
