from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.migrations import bootstrap_schema
from backend.repositories.source_repository import SourceRepository


def test_repository_create_get_list() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    bootstrap_schema(engine)

    session = Session()
    try:
        repo = SourceRepository(session)
        created = repo.create_source(file_name="a.txt", file_type="txt", content="hello", tenant_id="tenant-a")

        fetched = repo.get_source(created.id, tenant_id="tenant-a")
        listed = repo.list_sources(tenant_id="tenant-a")

        assert fetched is not None
        assert fetched.file_name == "a.txt"
        assert len(listed) == 1
        assert listed[0].id == created.id
    finally:
        session.close()


def test_repository_tenant_isolation() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    bootstrap_schema(engine)

    session = Session()
    try:
        repo = SourceRepository(session)
        created = repo.create_source(file_name="a.txt", file_type="txt", content="hello", tenant_id="tenant-a")
        assert repo.get_source(created.id, tenant_id="tenant-b") is None
        assert repo.list_sources(tenant_id="tenant-b") == []
    finally:
        session.close()
