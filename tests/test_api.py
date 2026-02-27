import asyncio

from pydantic import ValidationError

from backend.main import ai_assist, extract, health, upload
from backend.models import AIAssistRequest, ExtractRequest, UploadRequest


def _run(coro):
    return asyncio.run(coro)


def test_health_contract() -> None:
    payload = _run(health()).model_dump()
    assert payload["type"] == "health_response"
    assert payload["version"] == 1
    assert payload["success"] is True
    assert payload["error"] is None


def test_upload_contract() -> None:
    payload = _run(upload(UploadRequest(file_name="doc.pdf", file_type="pdf"))).model_dump()
    assert payload["type"] == "upload_response"
    assert payload["version"] == 1
    assert payload["success"] is True
    assert payload["data"]["stored"] is True


def test_extract_validation_error() -> None:
    try:
        ExtractRequest(mode="text")
    except ValidationError:
        assert True
    else:
        assert False, "ExtractRequest should require file_id"


def test_ai_assist_without_key() -> None:
    payload = _run(
        ai_assist(AIAssistRequest(prompt="Summarize this source", api_key_enabled=False))
    ).model_dump()
    assert payload["type"] == "ai_assist_response"
    assert payload["success"] is True
    assert "disabled" in payload["data"]["result"]
