import asyncio

from pydantic import ValidationError

from backend.models import BaseResponse, ErrorObject, ExtractRequest
from backend.services.response import fail, ok


def _run(coro):
    return asyncio.run(coro)


def test_base_response_success_contract() -> None:
    payload = ok({"status": "ok"}).model_dump()
    assert payload == {"success": True, "data": {"status": "ok"}, "error": None}


def test_base_response_error_contract() -> None:
    payload = fail("file_not_found", "Source file not found", {"file_id": 1}).model_dump()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"] == {
        "code": "file_not_found",
        "message": "Source file not found",
        "details": {"file_id": 1},
    }


def test_extract_request_mode_validation() -> None:
    try:
        ExtractRequest(file_id=1, mode="invalid")
    except ValidationError:
        assert True
    else:
        assert False, "ExtractRequest should enforce text|summary"


def test_base_response_model_types() -> None:
    model = BaseResponse(success=False, data=None, error=ErrorObject(code="x", message="y"))
    assert model.success is False
    assert model.data is None
    assert model.error is not None
