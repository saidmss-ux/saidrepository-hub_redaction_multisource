from datetime import UTC, datetime
from typing import Dict
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

from fastapi import FastAPI

from backend.models import (
    AIAssistRequest,
    BaseResponse,
    DownloadFromUrlRequest,
    ExtractRequest,
    UploadRequest,
    VideoToTextRequest,
)

app = FastAPI(title="DocuHub API", version="0.2.0")

# MVP in-memory source store (to be moved to SQLite in next phase)
SOURCES: Dict[str, dict] = {}


def _ts() -> str:
    return datetime.now(UTC).isoformat()


def _ok(response_type: str, data: dict) -> BaseResponse:
    return BaseResponse(type=response_type, version=1, success=True, data=data, error=None)


def _err(response_type: str, error: str, data: dict | None = None) -> BaseResponse:
    return BaseResponse(
        type=response_type,
        version=1,
        success=False,
        data=data or {},
        error=error,
    )


@app.get("/health", response_model=BaseResponse)
async def health() -> BaseResponse:
    return _ok("health_response", {"status": "ok", "timestamp": _ts()})


@app.post("/upload", response_model=BaseResponse)
async def upload(payload: UploadRequest) -> BaseResponse:
    file_id = str(uuid4())
    SOURCES[file_id] = {
        "file_name": payload.file_name,
        "file_type": payload.file_type.lower(),
        "content": payload.content,
        "created_at": _ts(),
    }
    return _ok(
        "upload_response",
        {
            "file_id": file_id,
            "file_name": payload.file_name,
            "file_type": payload.file_type.lower(),
            "stored": True,
        },
    )


@app.post("/download-from-url", response_model=BaseResponse)
async def download_from_url(payload: DownloadFromUrlRequest) -> BaseResponse:
    try:
        with urlopen(str(payload.url), timeout=5) as response:  # nosec B310 (MVP trusted flow)
            raw = response.read(20000)
            content = raw.decode("utf-8", errors="replace")
    except URLError as exc:
        return _err(
            "download_response",
            error=f"download_failed: {exc}",
            data={"source_url": str(payload.url), "downloaded": False},
        )

    file_id = str(uuid4())
    SOURCES[file_id] = {
        "file_name": str(payload.url).rstrip("/").split("/")[-1] or "downloaded.txt",
        "file_type": "txt",
        "content": content,
        "created_at": _ts(),
    }
    return _ok(
        "download_response",
        {
            "file_id": file_id,
            "source_url": str(payload.url),
            "downloaded": True,
            "bytes_previewed": len(content),
        },
    )


@app.post("/extract", response_model=BaseResponse)
async def extract(payload: ExtractRequest) -> BaseResponse:
    source = SOURCES.get(payload.file_id)
    if not source:
        return _err(
            "extract_response",
            error="file_not_found",
            data={"file_id": payload.file_id, "mode": payload.mode},
        )

    content = source.get("content", "")
    if payload.mode == "summary":
        extracted = content[:400]
    else:
        extracted = content

    return _ok(
        "extract_response",
        {
            "file_id": payload.file_id,
            "mode": payload.mode,
            "content": extracted,
            "chars": len(extracted),
        },
    )


@app.post("/video-to-text", response_model=BaseResponse)
async def video_to_text(payload: VideoToTextRequest) -> BaseResponse:
    return _ok(
        "video_to_text_response",
        {
            "source": payload.source,
            "transcript": f"[MVP transcript placeholder] {payload.source}",
        },
    )


@app.post("/ai-assist", response_model=BaseResponse)
async def ai_assist(payload: AIAssistRequest) -> BaseResponse:
    if not payload.api_key_enabled:
        return _err(
            "ai_assist_response",
            error="api_key_disabled",
            data={"result": "API key disabled; assistance unavailable"},
        )

    return _ok(
        "ai_assist_response",
        data={"result": f"AI-assisted draft for: {payload.prompt.strip()}"},
    )
