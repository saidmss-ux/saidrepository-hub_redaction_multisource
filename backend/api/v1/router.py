from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_auth_context, get_tenant_id, require_role
from backend.db.session import get_db_session
from backend.models import (
    AIAssistRequest,
    AuthTokenRequest,
    BaseResponse,
    DownloadFromUrlRequest,
    ExtractRequest,
    ProjectBatchExtractRequest,
    ProjectCreateRequest,
    ProjectDocumentCreateRequest,
    UploadRequest,
    VideoToTextRequest,
)
from backend.services import product_service, source_service
from backend.services.auth_service import AuthContext, create_access_token
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


@router.post("/projects", response_model=BaseResponse)
async def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db_session),
    auth: AuthContext = Depends(require_role("admin", "user")),
    tenant_id: str = Depends(get_tenant_id),
) -> BaseResponse:
    return ok(
        product_service.create_project(
            db,
            name=payload.name,
            description=payload.description,
            tenant_id=tenant_id,
            actor_id=auth.user_id,
        )
    )


@router.get("/projects", response_model=BaseResponse)
async def list_projects(
    db: Session = Depends(get_db_session),
    _auth=Depends(require_role("admin", "user")),
    tenant_id: str = Depends(get_tenant_id),
) -> BaseResponse:
    return ok(product_service.list_projects(db, tenant_id=tenant_id))


@router.post("/projects/{project_id}/documents", response_model=BaseResponse)
async def add_project_document(
    project_id: int,
    payload: ProjectDocumentCreateRequest,
    db: Session = Depends(get_db_session),
    auth: AuthContext = Depends(require_role("admin", "user")),
    tenant_id: str = Depends(get_tenant_id),
) -> BaseResponse:
    return ok(
        product_service.add_document_to_project(
            db,
            project_id=project_id,
            source_id=payload.source_id,
            title=payload.title,
            tenant_id=tenant_id,
            actor_id=auth.user_id,
        )
    )


@router.get("/projects/{project_id}/documents", response_model=BaseResponse)
async def list_project_documents(
    project_id: int,
    db: Session = Depends(get_db_session),
    _auth=Depends(require_role("admin", "user")),
    tenant_id: str = Depends(get_tenant_id),
) -> BaseResponse:
    return ok(product_service.list_project_documents(db, project_id=project_id, tenant_id=tenant_id))


@router.post("/projects/{project_id}/batches/extract", response_model=BaseResponse)
async def run_project_batch_extract(
    project_id: int,
    payload: ProjectBatchExtractRequest,
    db: Session = Depends(get_db_session),
    auth: AuthContext = Depends(require_role("admin", "user")),
    tenant_id: str = Depends(get_tenant_id),
) -> BaseResponse:
    return ok(
        product_service.run_project_batch_extract(
            db,
            project_id=project_id,
            mode=payload.mode,
            tenant_id=tenant_id,
            actor_id=auth.user_id,
        )
    )


@router.post("/auth/token", response_model=BaseResponse)
async def issue_token(payload: AuthTokenRequest) -> BaseResponse:
    token = create_access_token(sub=payload.user_id, role=payload.role, tenant_id=payload.tenant_id)
    return ok({"access_token": token, "token_type": "bearer"})


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
