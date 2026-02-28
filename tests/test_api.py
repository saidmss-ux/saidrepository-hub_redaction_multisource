import asyncio
import os
import tempfile

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import (
    ai_assist,
    extract,
    get_source,
    health,
    list_sources,
    upload,
)
from backend.models import AIAssistRequest, ExtractRequest, UploadRequest
from backend.db import Base, Source, SessionLocal, engine


def _run(coro):
    return asyncio.run(coro)


def _setup_test_db():
    """Create a fresh test database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _cleanup_test_db():
    """Clean up after tests."""
    Base.metadata.drop_all(bind=engine)


def _assert_base_contract(payload: dict, response_type: str) -> None:
    assert payload["type"] == response_type
    assert payload["version"] == 1
    assert isinstance(payload["success"], bool)
    assert isinstance(payload["data"], dict)


def test_health_contract() -> None:
    _setup_test_db()
    try:
        payload = _run(health()).model_dump()
        _assert_base_contract(payload, "health_response")
        assert payload["success"] is True
        assert payload["error"] is None
    finally:
        _cleanup_test_db()


def test_upload_then_extract_success() -> None:
    _setup_test_db()
    try:
        uploaded = _run(
            upload(UploadRequest(file_name="doc.txt", file_type="txt", content="hello world"))
        ).model_dump()
        file_id = uploaded["data"]["file_id"]

        extracted = _run(extract(ExtractRequest(file_id=file_id, mode="text"))).model_dump()
        _assert_base_contract(extracted, "extract_response")
        assert extracted["success"] is True
        assert extracted["data"]["content"] == "hello world"
    finally:
        _cleanup_test_db()


def test_extract_summary_mode() -> None:
    _setup_test_db()
    try:
        uploaded = _run(
            upload(UploadRequest(file_name="doc.txt", file_type="txt", content="x" * 800))
        ).model_dump()
        file_id = uploaded["data"]["file_id"]

        extracted = _run(extract(ExtractRequest(file_id=file_id, mode="summary"))).model_dump()
        assert extracted["success"] is True
        assert extracted["data"]["chars"] == 400
    finally:
        _cleanup_test_db()


def test_extract_validation_mode_error() -> None:
    try:
        ExtractRequest(file_id="abc", mode="invalid")
    except ValidationError:
        assert True
    else:
        assert False, "ExtractRequest should validate extract mode enum"


def test_extract_not_found() -> None:
    _setup_test_db()
    try:
        payload = _run(extract(ExtractRequest(file_id="missing-id", mode="text"))).model_dump()
        _assert_base_contract(payload, "extract_response")
        assert payload["success"] is False
        assert payload["error"] == "file_not_found"
    finally:
        _cleanup_test_db()


def test_list_and_get_sources() -> None:
    _setup_test_db()
    try:
        uploaded = _run(
            upload(UploadRequest(file_name="doc.txt", file_type="txt", content="hello"))
        ).model_dump()
        file_id = uploaded["data"]["file_id"]

        listed = _run(list_sources()).model_dump()
        _assert_base_contract(listed, "sources_response")
        assert listed["data"]["count"] == 1

        single = _run(get_source(file_id)).model_dump()
        _assert_base_contract(single, "source_response")
        assert single["success"] is True
        assert single["data"]["file_id"] == file_id
    finally:
        _cleanup_test_db()


def test_get_source_not_found() -> None:
    _setup_test_db()
    try:
        payload = _run(get_source("missing-id")).model_dump()
        _assert_base_contract(payload, "source_response")
        assert payload["success"] is False
        assert payload["error"] == "file_not_found"
    finally:
        _cleanup_test_db()


def test_ai_assist_without_key_is_structured_error() -> None:
    _setup_test_db()
    try:
        payload = _run(
            ai_assist(AIAssistRequest(prompt="Summarize this source", api_key_enabled=False))
        ).model_dump()
        _assert_base_contract(payload, "ai_assist_response")
        assert payload["success"] is False
        assert payload["error"] == "api_key_disabled"
    finally:
        _cleanup_test_db()


def test_ai_assist_with_key_success() -> None:
    _setup_test_db()
    try:
        payload = _run(
            ai_assist(AIAssistRequest(prompt="Summarize this source", api_key_enabled=True))
        ).model_dump()
        _assert_base_contract(payload, "ai_assist_response")
        assert payload["success"] is True
        assert payload["error"] is None
    finally:
        _cleanup_test_db()
