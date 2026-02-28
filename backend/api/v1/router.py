from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db_session
from backend.models import (
    AIAssistRequest,
    BaseResponse,
    DownloadFromUrlRequest,
    ExtractRequest,
    UploadRequest,
    VideoToTextRequest,
)
from backend.services import source_service
from backend.services.response import ok

router = APIRouter()


@router.get("/health", response_model=BaseResponse)
async def health() -> BaseResponse:
    return ok({"status": "ok"})


@router.post("/upload", response_model=BaseResponse)
async def upload(payload: UploadRequest, db: Session = Depends(get_db_session)) -> BaseResponse:
    data = source_service.upload_source(
        db,
        file_name=payload.file_name,
        file_type=payload.file_type,
        content=payload.content,
    )
    return ok(data)


@router.post("/download-from-url", response_model=BaseResponse)
async def download_from_url(
    payload: DownloadFromUrlRequest,
    db: Session = Depends(get_db_session),
) -> BaseResponse:
    data = source_service.download_from_url(db, url=str(payload.url))
    return ok(data)


@router.post("/extract", response_model=BaseResponse)
async def extract(payload: ExtractRequest, db: Session = Depends(get_db_session)) -> BaseResponse:
    data = source_service.extract_content(db, file_id=payload.file_id, mode=payload.mode)
    return ok(data)


@router.get("/sources", response_model=BaseResponse)
async def list_sources(db: Session = Depends(get_db_session)) -> BaseResponse:
    data = source_service.list_sources(db)
    return ok(data)


@router.get("/source/{file_id}", response_model=BaseResponse)
async def get_source(file_id: int, db: Session = Depends(get_db_session)) -> BaseResponse:
    data = source_service.get_source(db, file_id=file_id)
    return ok(data)


@router.post("/video-to-text", response_model=BaseResponse)
async def video_to_text(payload: VideoToTextRequest) -> BaseResponse:
    return ok(source_service.video_to_text(source=payload.source))


@router.post("/ai-assist", response_model=BaseResponse)
async def ai_assist(payload: AIAssistRequest) -> BaseResponse:
    return ok(
        source_service.ai_assist(
            prompt=payload.prompt,
            api_key_enabled=payload.api_key_enabled,
        )
    )
