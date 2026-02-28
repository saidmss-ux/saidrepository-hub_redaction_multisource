import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.migrations import bootstrap_schema
from backend.services.errors import ServiceError
from backend.services.feature_flag_service import set_feature_flag
from backend.services.product_service import (
    add_document_to_project,
    create_project,
    list_project_documents,
    run_project_batch_extract,
    get_background_job_status,
)
from backend.services.source_service import upload_source


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    bootstrap_schema(engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_create_project_and_add_document(db_session):
    project = create_project(db_session, name="My Project", description="desc")
    source = upload_source(db_session, file_name="a.txt", file_type="txt", content="hello")

    doc = add_document_to_project(
        db_session,
        project_id=project["project_id"],
        source_id=source["file_id"],
        title="Doc 1",
    )
    assert doc["project_id"] == project["project_id"]


def test_project_batch_extract_summary(db_session):
    project = create_project(db_session, name="P", description="")
    source = upload_source(db_session, file_name="a.txt", file_type="txt", content="x" * 800)
    add_document_to_project(
        db_session,
        project_id=project["project_id"],
        source_id=source["file_id"],
        title="Doc 1",
    )

    batch = run_project_batch_extract(db_session, project_id=project["project_id"], mode="summary")
    assert batch["count"] == 1
    assert batch["items"][0]["chars"] == 400


def test_project_not_found(db_session):
    with pytest.raises(ServiceError) as err:
        list_project_documents(db_session, project_id=999)
    assert err.value.code == "project_not_found"


def test_project_tenant_isolation(db_session):
    project = create_project(db_session, name="A", description="", tenant_id="tenant-a")
    with pytest.raises(ServiceError) as err:
        list_project_documents(db_session, project_id=project["project_id"], tenant_id="tenant-b")
    assert err.value.code == "project_not_found"


def test_project_batch_extract_queued_when_async_flag_on(db_session, monkeypatch):
    monkeypatch.setattr("backend.services.product_service.settings.worker_enabled", True)
    monkeypatch.setattr("backend.services.product_service.settings.batch_async_enabled", True)

    set_feature_flag(
        db_session,
        key="batch.async.enabled",
        enabled=True,
        scope="tenant",
        scope_id="default",
        actor_id="admin",
        actor_tenant_id="default",
    )

    project = create_project(db_session, name="Q", description="")
    source = upload_source(db_session, file_name="a.txt", file_type="txt", content="hello")
    add_document_to_project(
        db_session,
        project_id=project["project_id"],
        source_id=source["file_id"],
        title="Doc 1",
    )

    batch = run_project_batch_extract(db_session, project_id=project["project_id"], mode="summary")
    assert batch["status"] == "queued"
    assert batch["count"] == 0
    assert batch["items"] == []
    assert batch["job_id"] >= 1


def test_get_background_job_status_queued(db_session, monkeypatch):
    monkeypatch.setattr("backend.services.product_service.settings.worker_enabled", True)
    monkeypatch.setattr("backend.services.product_service.settings.batch_async_enabled", True)

    set_feature_flag(
        db_session,
        key="batch.async.enabled",
        enabled=True,
        scope="tenant",
        scope_id="default",
        actor_id="admin",
        actor_tenant_id="default",
    )

    project = create_project(db_session, name="JobProject", description="")
    source = upload_source(db_session, file_name="a.txt", file_type="txt", content="hello")
    add_document_to_project(
        db_session,
        project_id=project["project_id"],
        source_id=source["file_id"],
        title="Doc 1",
    )

    batch = run_project_batch_extract(db_session, project_id=project["project_id"], mode="summary")
    status = get_background_job_status(db_session, job_id=batch["job_id"], tenant_id="default")

    assert status["job_id"] == batch["job_id"]
    assert status["status"] == "queued"
    assert status["payload"]["project_id"] == project["project_id"]


def test_get_background_job_status_not_found(db_session):
    with pytest.raises(ServiceError) as err:
        get_background_job_status(db_session, job_id=99999, tenant_id="default")
    assert err.value.code == "job_not_found"
