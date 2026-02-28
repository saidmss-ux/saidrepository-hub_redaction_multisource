from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import BatchItem, BatchRun, Document, Project, Source


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_project(self, *, name: str, description: str) -> Project:
        project = Project(name=name, description=description)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def get_project(self, project_id: int) -> Project | None:
        return self.session.get(Project, project_id)

    def list_projects(self) -> list[Project]:
        return list(self.session.execute(select(Project).order_by(Project.id.desc())).scalars())

    def create_document(self, *, project_id: int, source_id: int, title: str) -> Document:
        document = Document(project_id=project_id, source_id=source_id, title=title)
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def list_documents_by_project(self, project_id: int) -> list[Document]:
        stmt = select(Document).where(Document.project_id == project_id).order_by(Document.id.desc())
        return list(self.session.execute(stmt).scalars())

    def get_source(self, source_id: int) -> Source | None:
        return self.session.get(Source, source_id)

    def create_batch_run(self, *, project_id: int, mode: str, status: str = "completed") -> BatchRun:
        batch = BatchRun(project_id=project_id, mode=mode, status=status)
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
