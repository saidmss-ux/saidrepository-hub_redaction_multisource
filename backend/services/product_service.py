from sqlalchemy.orm import Session

from backend.models import ExtractMode
from backend.repositories.product_repository import ProductRepository
from backend.services.errors import ServiceError
from backend.services.logging_utils import log_event


def _repo(session: Session) -> ProductRepository:
    return ProductRepository(session)


def create_project(session: Session, *, name: str, description: str = "") -> dict:
    project = _repo(session).create_project(name=name.strip(), description=description.strip())
    log_event("project_created", project_id=project.id, name=project.name)
    return {
        "project_id": project.id,
        "name": project.name,
        "description": project.description,
    }


def list_projects(session: Session) -> dict:
    projects = _repo(session).list_projects()
    return {
        "items": [
            {
                "project_id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ],
        "count": len(projects),
    }


def add_document_to_project(session: Session, *, project_id: int, source_id: int, title: str) -> dict:
    repo = _repo(session)
    project = repo.get_project(project_id)
    if not project:
        raise ServiceError(code="project_not_found", message="Project not found", details={"project_id": project_id})

    source = repo.get_source(source_id)
    if not source:
        raise ServiceError(code="file_not_found", message="Source file not found", details={"file_id": source_id})

    document = repo.create_document(project_id=project_id, source_id=source_id, title=title.strip())
    log_event("project_document_added", project_id=project_id, document_id=document.id, source_id=source_id)
    return {
        "document_id": document.id,
        "project_id": document.project_id,
        "source_id": document.source_id,
        "title": document.title,
    }


def list_project_documents(session: Session, *, project_id: int) -> dict:
    repo = _repo(session)
    project = repo.get_project(project_id)
    if not project:
        raise ServiceError(code="project_not_found", message="Project not found", details={"project_id": project_id})

    docs = repo.list_documents_by_project(project_id)
    return {
        "items": [
            {
                "document_id": d.id,
                "project_id": d.project_id,
                "source_id": d.source_id,
                "title": d.title,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
        "count": len(docs),
    }


def run_project_batch_extract(session: Session, *, project_id: int, mode: ExtractMode) -> dict:
    repo = _repo(session)
    project = repo.get_project(project_id)
    if not project:
        raise ServiceError(code="project_not_found", message="Project not found", details={"project_id": project_id})

    docs = repo.list_documents_by_project(project_id)
    batch = repo.create_batch_run(project_id=project_id, mode=mode, status="completed")

    results: list[dict] = []
    for doc in docs:
        src = repo.get_source(doc.source_id)
        content = src.content if src else ""
        extracted = content[:400] if mode == "summary" else content
        repo.create_batch_item(batch_id=batch.id, document_id=doc.id, extracted_chars=len(extracted))
        results.append(
            {
                "document_id": doc.id,
                "source_id": doc.source_id,
                "chars": len(extracted),
            }
        )

    log_event("project_batch_completed", project_id=project_id, batch_id=batch.id, item_count=len(results), mode=mode)
    return {
        "batch_id": batch.id,
        "project_id": project_id,
        "mode": mode,
        "items": results,
        "count": len(results),
    }
