import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import BackgroundJob


class BackgroundJobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_job(self, *, tenant_id: str, job_type: str, payload: dict) -> BackgroundJob:
        job = BackgroundJob(
            tenant_id=tenant_id,
            job_type=job_type,
            status="queued",
            payload_json=json.dumps(payload, separators=(",", ":")),
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_job(self, *, tenant_id: str, job_id: int) -> BackgroundJob | None:
        stmt = select(BackgroundJob).where(BackgroundJob.id == job_id, BackgroundJob.tenant_id == tenant_id)
        return self.session.execute(stmt).scalar_one_or_none()
