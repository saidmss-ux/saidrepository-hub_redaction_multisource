from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import BatchItem, BatchRun, Document, Project, Source


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_project(self, *, name: str, description: str, tenant_id: str) -> Project:
        project = Project(name=name, description=description, tenant_id=tenant_id)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def get_project(self, project_id: int, *, tenant_id: str) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_projects(self, *, tenant_id: str) -> list[Project]:
        stmt = select(Project).where(Project.tenant_id == tenant_id).order_by(Project.id.desc())
        return list(self.session.execute(stmt).scalars())

    def create_document(self, *, project_id: int, source_id: int, title: str, tenant_id: str) -> Document:
        document = Document(project_id=project_id, source_id=source_id, title=title, tenant_id=tenant_id)
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def list_documents_by_project(self, project_id: int, *, tenant_id: str) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.project_id == project_id, Document.tenant_id == tenant_id)
            .order_by(Document.id.desc())
        )
        return list(self.session.execute(stmt).scalars())

    def get_source(self, source_id: int, *, tenant_id: str) -> Source | None:
        stmt = select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def create_batch_run(self, *, project_id: int, mode: str, tenant_id: str, status: str = "completed") -> BatchRun:
        batch = BatchRun(project_id=project_id, mode=mode, status=status, tenant_id=tenant_id)
        self.session.add(batch)
        self.session.commit()
        self.session.refresh(batch)
        return batch

    def create_batch_item(self, *, batch_id: int, document_id: int, extracted_chars: int) -> BatchItem:
        item = BatchItem(batch_id=batch_id, document_id=document_id, extracted_chars=extracted_chars)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item
