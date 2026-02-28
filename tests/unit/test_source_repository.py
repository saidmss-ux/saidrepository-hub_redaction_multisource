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
        created = repo.create_source(file_name="a.txt", file_type="txt", content="hello")

        fetched = repo.get_source(created.id)
        listed = repo.list_sources()

        assert fetched is not None
        assert fetched.file_name == "a.txt"
        assert len(listed) == 1
        assert listed[0].id == created.id
    finally:
        session.close()
