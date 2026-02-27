import asyncio

from pydantic import ValidationError

from backend.main import SOURCES, ai_assist, download_from_url, extract, health, upload
from backend.models import (
    AIAssistRequest,
    DownloadFromUrlRequest,
    ExtractRequest,
    UploadRequest,
)


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


def test_extract_not_found() -> None:
    SOURCES.clear()
    payload = _run(extract(ExtractRequest(file_id="missing-id", mode="text"))).model_dump()
    _assert_base_contract(payload, "extract_response")
    assert payload["success"] is False
    assert payload["error"] == "file_not_found"


def test_download_validation_error() -> None:
    try:
        DownloadFromUrlRequest(url="not-a-url")
    except ValidationError:
        assert True
    else:
        assert False, "DownloadFromUrlRequest should validate URL format"


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
