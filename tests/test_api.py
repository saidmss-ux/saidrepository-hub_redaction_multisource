import asyncio

from pydantic import ValidationError

from backend.main import (
    SOURCES,
    ai_assist,
    extract,
    get_source,
    health,
    list_sources,
    upload,
)
from backend.models import AIAssistRequest, ExtractRequest, UploadRequest


def _run(coro):
    return asyncio.run(coro)


def _assert_base_contract(payload: dict, response_type: str) -> None:
    assert payload["type"] == response_type
    assert payload["version"] == 1
    assert isinstance(payload["success"], bool)
    assert isinstance(payload["data"], dict)


def test_health_contract() -> None:
    payload = _run(health()).model_dump()
    _assert_base_contract(payload, "health_response")
    assert payload["success"] is True
    assert payload["error"] is None


def test_upload_then_extract_success() -> None:
    SOURCES.clear()
    uploaded = _run(
        upload(UploadRequest(file_name="doc.txt", file_type="txt", content="hello world"))
    ).model_dump()
    file_id = uploaded["data"]["file_id"]

    extracted = _run(extract(ExtractRequest(file_id=file_id, mode="text"))).model_dump()
    _assert_base_contract(extracted, "extract_response")
    assert extracted["success"] is True
    assert extracted["data"]["content"] == "hello world"


def test_extract_summary_mode() -> None:
    SOURCES.clear()
    uploaded = _run(
        upload(UploadRequest(file_name="doc.txt", file_type="txt", content="x" * 800))
    ).model_dump()
    file_id = uploaded["data"]["file_id"]

    extracted = _run(extract(ExtractRequest(file_id=file_id, mode="summary"))).model_dump()
    assert extracted["success"] is True
    assert extracted["data"]["chars"] == 400


def test_extract_validation_mode_error() -> None:
    try:
        ExtractRequest(file_id="abc", mode="invalid")
    except ValidationError:
        assert True
    else:
        assert False, "ExtractRequest should validate extract mode enum"


def test_extract_not_found() -> None:
    SOURCES.clear()
    payload = _run(extract(ExtractRequest(file_id="missing-id", mode="text"))).model_dump()
    _assert_base_contract(payload, "extract_response")
    assert payload["success"] is False
    assert payload["error"] == "file_not_found"


def test_list_and_get_sources() -> None:
    SOURCES.clear()
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


def test_get_source_not_found() -> None:
    SOURCES.clear()
    payload = _run(get_source("missing-id")).model_dump()
    _assert_base_contract(payload, "source_response")
    assert payload["success"] is False
    assert payload["error"] == "file_not_found"


def test_ai_assist_without_key_is_structured_error() -> None:
    payload = _run(
        ai_assist(AIAssistRequest(prompt="Summarize this source", api_key_enabled=False))
    ).model_dump()
    _assert_base_contract(payload, "ai_assist_response")
    assert payload["success"] is False
    assert payload["error"] == "api_key_disabled"


def test_ai_assist_with_key_success() -> None:
    payload = _run(
        ai_assist(AIAssistRequest(prompt="Summarize this source", api_key_enabled=True))
    ).model_dump()
    _assert_base_contract(payload, "ai_assist_response")
    assert payload["success"] is True
    assert payload["error"] is None
