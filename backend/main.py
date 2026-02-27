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

app = FastAPI(title="DocuHub API", version="0.1.0")


@app.get("/health", response_model=BaseResponse)
async def health() -> BaseResponse:
    return BaseResponse(
        type="health_response",
        version=1,
        success=True,
        data={"status": "ok"},
        error=None,
    )


@app.post("/upload", response_model=BaseResponse)
async def upload(payload: UploadRequest) -> BaseResponse:
    return BaseResponse(
        type="upload_response",
        version=1,
        success=True,
        data={
            "file_id": str(uuid4()),
            "file_name": payload.file_name,
            "file_type": payload.file_type,
            "stored": True,
        },
        error=None,
    )


@app.post("/download-from-url", response_model=BaseResponse)
async def download_from_url(payload: DownloadFromUrlRequest) -> BaseResponse:
    return BaseResponse(
        type="download_response",
        version=1,
        success=True,
        data={"file_id": str(uuid4()), "source_url": payload.url, "downloaded": True},
        error=None,
    )


@app.post("/extract", response_model=BaseResponse)
async def extract(payload: ExtractRequest) -> BaseResponse:
    return BaseResponse(
        type="extract_response",
        version=1,
        success=True,
        data={
            "file_id": payload.file_id,
            "mode": payload.mode,
            "content": "Sample extracted content",
        },
        error=None,
    )


@app.post("/video-to-text", response_model=BaseResponse)
async def video_to_text(payload: VideoToTextRequest) -> BaseResponse:
    return BaseResponse(
        type="video_to_text_response",
        version=1,
        success=True,
        data={"source": payload.source, "transcript": "Sample transcript"},
        error=None,
    )


@app.post("/ai-assist", response_model=BaseResponse)
async def ai_assist(payload: AIAssistRequest) -> BaseResponse:
    assisted_text = (
        f"AI-assisted draft for: {payload.prompt}"
        if payload.api_key_enabled
        else "API key disabled; assistance unavailable"
    )
    return BaseResponse(
        type="ai_assist_response",
        version=1,
        success=True,
        data={"result": assisted_text},
        error=None,
    )
