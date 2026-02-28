import pytest
from pydantic import ValidationError

from backend.models import DownloadFromUrlRequest, ExtractRequest, UploadRequest


def test_extract_request_valid_mode() -> None:
    model = ExtractRequest(file_id=1, mode="summary")
    assert model.mode == "summary"


def test_extract_request_invalid_mode() -> None:
    with pytest.raises(ValidationError):
        ExtractRequest(file_id=1, mode="invalid")


def test_download_request_rejects_non_http_scheme() -> None:
    with pytest.raises(ValidationError):
        DownloadFromUrlRequest(url="ftp://example.com/file.txt")


def test_upload_request_requires_non_empty_fields() -> None:
    with pytest.raises(ValidationError):
        UploadRequest(file_name="", file_type="txt", content="x")
