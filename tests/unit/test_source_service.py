from urllib.error import URLError

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.session import Base
from backend.services.errors import ServiceError
from backend.services.source_service import (
    ai_assist,
    download_from_url,
    extract_content,
    get_source,
    list_sources,
    upload_source,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_upload_and_extract_success(db_session):
    saved = upload_source(db_session, file_name="doc.txt", file_type="txt", content="hello")
    extracted = extract_content(db_session, file_id=saved["file_id"], mode="text")
    assert extracted["content"] == "hello"


def test_extract_not_found(db_session):
    with pytest.raises(ServiceError) as err:
        extract_content(db_session, file_id=999, mode="text")
    assert err.value.code == "file_not_found"


def test_sources_list_and_get(db_session):
    saved = upload_source(db_session, file_name="doc.txt", file_type="txt", content="hello")
    listed = list_sources(db_session)
    single = get_source(db_session, file_id=saved["file_id"])
    assert listed["count"] == 1
    assert single["file_id"] == saved["file_id"]


def test_ai_assist_disabled_error():
    with pytest.raises(ServiceError) as err:
        ai_assist(prompt="test", api_key_enabled=False)
    assert err.value.code == "api_key_disabled"


def test_download_blocks_localhost(db_session):
    with pytest.raises(ServiceError) as err:
        download_from_url(db_session, url="http://localhost/test.txt")
    assert err.value.code in {"blocked_host", "blocked_private_network"}


def test_download_network_error_is_normalized(db_session, monkeypatch):
    def _raise(*args, **kwargs):
        raise URLError("offline")

    monkeypatch.setattr("backend.services.source_service.urlopen", _raise)

    with pytest.raises(ServiceError) as err:
        download_from_url(db_session, url="https://example.com/file.txt")
    assert err.value.code == "network_url_error"


def test_upload_too_large(db_session, monkeypatch):
    monkeypatch.setattr("backend.services.source_service.settings.max_upload_chars", 3)
    with pytest.raises(ServiceError) as err:
        upload_source(db_session, file_name="doc.txt", file_type="txt", content="hello")
    assert err.value.code == "upload_too_large"


def test_upload_unsupported_type(db_session):
    with pytest.raises(ServiceError) as err:
        upload_source(db_session, file_name="doc.bin", file_type="application/octet-stream", content="abc")
    assert err.value.code == "unsupported_file_type"
