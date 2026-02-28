import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.migrations import bootstrap_schema
from backend.services.errors import ServiceError
from backend.services.product_service import (
    add_document_to_project,
    create_project,
    list_project_documents,
    run_project_batch_extract,
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
