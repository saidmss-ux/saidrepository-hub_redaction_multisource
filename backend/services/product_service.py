import json
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models import ExtractMode
from backend.repositories.background_job_repository import BackgroundJobRepository
from backend.repositories.product_repository import ProductRepository
from backend.services.audit_service import record_audit_event
from backend.services.errors import ServiceError
from backend.services.feature_flag_service import get_effective_flag
from backend.services.logging_utils import log_event
from backend.services.metrics_service import observe_batch_size
from backend.services.task_runner import get_task_runner


def _repo(session: Session) -> ProductRepository:
    return ProductRepository(session)


def create_project(
    session: Session,
    *,
    name: str,
    description: str = "",
    tenant_id: str | None = None,
    actor_id: str = "system",
) -> dict:
    resolved_tenant = tenant_id or settings.default_tenant_id
    project = _repo(session).create_project(name=name.strip(), description=description.strip(), tenant_id=resolved_tenant)
    log_event("project_created", project_id=project.id, name=project.name, tenant_id=resolved_tenant)
    record_audit_event(
        session,
        tenant_id=resolved_tenant,
        actor_id=actor_id,
        action="project.create",
        target_type="project",
        target_id=str(project.id),
        outcome="success",
    )
    return {
        "project_id": project.id,
        "name": project.name,
        "description": project.description,
    }


def list_projects(session: Session, *, tenant_id: str | None = None) -> dict:
    resolved_tenant = tenant_id or settings.default_tenant_id
    projects = _repo(session).list_projects(tenant_id=resolved_tenant)
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


def add_document_to_project(
    session: Session,
    *,
    project_id: int,
    source_id: int,
    title: str,
    tenant_id: str | None = None,
    actor_id: str = "system",
) -> dict:
    resolved_tenant = tenant_id or settings.default_tenant_id
    repo = _repo(session)
    project = repo.get_project(project_id, tenant_id=resolved_tenant)
    if not project:
        raise ServiceError(code="project_not_found", message="Project not found", details={"project_id": project_id})

    source = repo.get_source(source_id, tenant_id=resolved_tenant)
    if not source:
        raise ServiceError(code="file_not_found", message="Source file not found", details={"file_id": source_id})

    document = repo.create_document(project_id=project_id, source_id=source_id, title=title.strip(), tenant_id=resolved_tenant)
    log_event("project_document_added", project_id=project_id, document_id=document.id, source_id=source_id, tenant_id=resolved_tenant)
    record_audit_event(
        session,
        tenant_id=resolved_tenant,
        actor_id=actor_id,
        action="document.create",
        target_type="document",
        target_id=str(document.id),
        outcome="success",
    )
    return {
        "document_id": document.id,
        "project_id": document.project_id,
        "source_id": document.source_id,
        "title": document.title,
    }


def list_project_documents(session: Session, *, project_id: int, tenant_id: str | None = None) -> dict:
    resolved_tenant = tenant_id or settings.default_tenant_id
    repo = _repo(session)
    project = repo.get_project(project_id, tenant_id=resolved_tenant)
    if not project:
        raise ServiceError(code="project_not_found", message="Project not found", details={"project_id": project_id})

    docs = repo.list_documents_by_project(project_id, tenant_id=resolved_tenant)
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


def run_project_batch_extract(
    session: Session,
    *,
    project_id: int,
    mode: ExtractMode,
    tenant_id: str | None = None,
    actor_id: str = "system",
) -> dict:
    resolved_tenant = tenant_id or settings.default_tenant_id
    repo = _repo(session)
    project = repo.get_project(project_id, tenant_id=resolved_tenant)
    if not project:
        raise ServiceError(code="project_not_found", message="Project not found", details={"project_id": project_id})

    docs = repo.list_documents_by_project(project_id, tenant_id=resolved_tenant)

    use_async_batch = (
        settings.worker_enabled
        and settings.batch_async_enabled
        and get_effective_flag(session, key="batch.async.enabled", tenant_id=resolved_tenant, default=False)
    )

    if use_async_batch:
        queued_batch = repo.create_batch_run(project_id=project_id, mode=mode, status="queued", tenant_id=resolved_tenant)
        job = BackgroundJobRepository(session).create_job(
            tenant_id=resolved_tenant,
            job_type="batch_extract",
            payload={"project_id": project_id, "batch_id": queued_batch.id, "mode": mode, "count": len(docs)},
        )
        log_event(
            "project_batch_queued",
            project_id=project_id,
            batch_id=queued_batch.id,
            job_id=job.id,
            tenant_id=resolved_tenant,
        )
        record_audit_event(
            session,
            tenant_id=resolved_tenant,
            actor_id=actor_id,
            action="batch.extract.queued",
            target_type="batch",
            target_id=str(queued_batch.id),
            outcome="success",
            metadata={"job_id": job.id, "mode": mode, "count": len(docs)},
        )
        return {
            "batch_id": queued_batch.id,
            "project_id": project_id,
            "mode": mode,
            "status": "queued",
            "job_id": job.id,
            "items": [],
            "count": 0,
        }

    batch = repo.create_batch_run(project_id=project_id, mode=mode, status="completed", tenant_id=resolved_tenant)

    def _execute_batch() -> list[dict]:
        local_results: list[dict] = []
        for doc in docs:
            src = repo.get_source(doc.source_id, tenant_id=resolved_tenant)
            content = src.content if src else ""
            extracted = content[:400] if mode == "summary" else content
            repo.create_batch_item(batch_id=batch.id, document_id=doc.id, extracted_chars=len(extracted))
            local_results.append(
                {
                    "document_id": doc.id,
                    "source_id": doc.source_id,
                    "chars": len(extracted),
                }
            )
        return local_results

    results = get_task_runner().run(_execute_batch)

    observe_batch_size(len(results))
    log_event(
        "project_batch_completed",
        project_id=project_id,
        batch_id=batch.id,
        item_count=len(results),
        mode=mode,
        tenant_id=resolved_tenant,
    )
    record_audit_event(
        session,
        tenant_id=resolved_tenant,
        actor_id=actor_id,
        action="batch.extract",
        target_type="batch",
        target_id=str(batch.id),
        outcome="success",
        metadata={"mode": mode, "count": len(results)},
    )
    return {
        "batch_id": batch.id,
        "project_id": project_id,
        "mode": mode,
        "items": results,
        "count": len(results),
    }


def get_background_job_status(session: Session, *, job_id: int, tenant_id: str | None = None) -> dict:
    resolved_tenant = tenant_id or settings.default_tenant_id
    job = BackgroundJobRepository(session).get_job(tenant_id=resolved_tenant, job_id=job_id)
    if not job:
        raise ServiceError(code="job_not_found", message="Background job not found", details={"job_id": job_id})

    payload = {}
    if job.payload_json:
        try:
            payload = json.loads(job.payload_json)
        except json.JSONDecodeError:
            payload = {}

    result = None
    if job.result_json:
        try:
            result = json.loads(job.result_json)
        except json.JSONDecodeError:
            result = job.result_json

    return {
        "job_id": job.id,
        "tenant_id": job.tenant_id,
        "job_type": job.job_type,
        "status": job.status,
        "payload": payload,
        "result": result,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }
