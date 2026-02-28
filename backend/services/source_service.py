from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models import ExtractMode
from backend.repositories.contracts import SourceRepositoryProtocol
from backend.repositories.source_repository import SourceRepository
from backend.services.errors import ServiceError
from backend.services.logging_utils import log_event
from backend.services.metrics_service import observe_extract
from backend.services.security import validate_public_http_url


def _repo(session: Session) -> SourceRepositoryProtocol:
    return SourceRepository(session)


def _validate_upload_type(file_type: str) -> str:
    normalized = file_type.strip().lower()
    if normalized not in settings.allowed_file_types:
        raise ServiceError(
            code="unsupported_file_type",
            message="Provided file type is not supported",
            details={"allowed_file_types": list(settings.allowed_file_types)},
        )
    return normalized


def upload_source(session: Session, *, file_name: str, file_type: str, content: str) -> dict:
    content_len = len(content)
    if content_len > settings.max_upload_chars:
        raise ServiceError(
            code="upload_too_large",
            message="Upload content exceeds configured limit",
            details={"max_upload_chars": settings.max_upload_chars, "upload_chars": content_len},
        )

    normalized_type = _validate_upload_type(file_type)
    source = _repo(session).create_source(file_name=file_name, file_type=normalized_type, content=content)
    log_event("upload_saved", file_id=source.id, file_type=source.file_type, upload_chars=content_len)
    return {
        "file_id": source.id,
        "file_name": source.file_name,
        "file_type": source.file_type,
        "stored": True,
    }


def download_from_url(session: Session, *, url: str) -> dict:
    safe_url = validate_public_http_url(url)
    try:
        with urlopen(safe_url, timeout=settings.url_download_timeout_s) as response:  # nosec B310
            raw = response.read(settings.max_download_chars)
            content = raw.decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise ServiceError(code="network_http_error", message="HTTP error while downloading", details={"status": exc.code})
    except URLError as exc:
        raise ServiceError(code="network_url_error", message="Network error while downloading", details={"reason": str(exc.reason)})
    except TimeoutError:
        raise ServiceError(code="network_timeout", message="Download timeout")

    file_name = safe_url.rstrip("/").split("/")[-1] or "downloaded.txt"
    source = _repo(session).create_source(
        file_name=file_name,
        file_type="txt",
        content=content,
        source_url=safe_url,
    )
    log_event("download_saved", file_id=source.id, source_url=safe_url, bytes_previewed=len(content))
    return {
        "file_id": source.id,
        "source_url": safe_url,
        "downloaded": True,
        "bytes_previewed": len(content),
    }


def extract_content(session: Session, *, file_id: int, mode: ExtractMode) -> dict:
    start_time = monotonic()
    source = _repo(session).get_source(file_id)
    if not source:
        raise ServiceError(code="file_not_found", message="Source file not found", details={"file_id": file_id})

    extracted = source.content[:400] if mode == "summary" else source.content
    elapsed = monotonic() - start_time
    if elapsed > settings.extract_timeout_s:
        raise ServiceError(code="extract_timeout", message="Extraction timeout")

    elapsed_ms = int(elapsed * 1000)
    observe_extract(elapsed_ms)
    log_event("extract_done", file_id=source.id, mode=mode, elapsed_ms=elapsed_ms, chars=len(extracted))
    return {
        "file_id": source.id,
        "mode": mode,
        "content": extracted,
        "chars": len(extracted),
    }


def list_sources(session: Session) -> dict:
    items = _repo(session).list_sources()
    return {
        "items": [
            {
                "file_id": source.id,
                "file_name": source.file_name,
                "file_type": source.file_type,
                "created_at": source.created_at.isoformat() if source.created_at else None,
            }
            for source in items
        ],
        "count": len(items),
    }


def get_source(session: Session, *, file_id: int) -> dict:
    source = _repo(session).get_source(file_id)
    if not source:
        raise ServiceError(code="file_not_found", message="Source file not found", details={"file_id": file_id})
    return {
        "file_id": source.id,
        "file_name": source.file_name,
        "file_type": source.file_type,
        "content": source.content,
        "created_at": source.created_at.isoformat() if source.created_at else None,
    }


def video_to_text(*, source: str) -> dict:
    return {"source": source, "transcript": f"[MVP transcript placeholder] {source}"}


def ai_assist(*, prompt: str, api_key_enabled: bool) -> dict:
    if not api_key_enabled:
        raise ServiceError(code="api_key_disabled", message="API key disabled; assistance unavailable")
    return {"result": f"AI-assisted draft for: {prompt.strip()}"}
