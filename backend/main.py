from datetime import UTC, datetime
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

from fastapi import FastAPI
from sqlalchemy.orm import Session

from backend.db import SessionLocal, init_db, Source, Extraction, hash_content, check_duplicate
from backend.models import (
    AIAssistRequest,
    BaseResponse,
    DownloadFromUrlRequest,
    ExtractRequest,
    UploadRequest,
    VideoToTextRequest,
)
from backend.parsers import ParserFactory, ParserError

app = FastAPI(title="DocuHub API", version="0.2.1")

# Initialize database and parser factory on startup
parser_factory = ParserFactory()


@app.on_event("startup")
async def startup_event():
    init_db()


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
    db = SessionLocal()
    try:
        content = payload.content or ""
        content_hash = hash_content(content)

        # Check for duplicate content
        existing = check_duplicate(db, content_hash)
        if existing:
            return _ok(
                "upload_response",
                {
                    "file_id": existing.file_id,
                    "file_name": existing.file_name,
                    "file_type": existing.file_type,
                    "stored": False,
                    "duplicate": True,
                    "existing_id": existing.file_id,
                },
            )

        file_id = str(uuid4())

        # Create source record
        source = Source(
            file_id=file_id,
            file_name=payload.file_name,
            file_type=payload.file_type.lower(),
            file_size=len(content.encode("utf-8")),
            content_preview=content[:1000],  # Store first 1000 chars for preview
            full_content=content,  # Store full content for extraction
            content_hash=content_hash,
            is_url_source=0,
        )

        db.add(source)
        db.commit()
        db.refresh(source)

        return _ok(
            "upload_response",
            {
                "file_id": file_id,
                "file_name": payload.file_name,
                "file_type": payload.file_type.lower(),
                "stored": True,
                "duplicate": False,
            },
        )
    except Exception as exc:
        db.rollback()
        return _err("upload_response", error=f"upload_failed: {str(exc)}")
    finally:
        db.close()


@app.post("/download-from-url", response_model=BaseResponse)
async def download_from_url(payload: DownloadFromUrlRequest) -> BaseResponse:
    db = SessionLocal()
    try:
        # Download content from URL
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

        # Try to extract structured content with BeautifulSoup
        extracted_content = content
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n")

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            extracted_content = "\n".join(line for line in lines if line)
        except Exception:
            # If BeautifulSoup fails, use raw content
            pass

        # Check for duplicate content
        content_hash = hash_content(extracted_content)
        existing = check_duplicate(db, content_hash)
        if existing:
            return _ok(
                "download_response",
                {
                    "file_id": existing.file_id,
                    "source_url": str(payload.url),
                    "downloaded": True,
                    "bytes_previewed": len(extracted_content),
                    "duplicate": True,
                    "existing_id": existing.file_id,
                },
            )

        file_id = str(uuid4())
        file_name = str(payload.url).rstrip("/").split("/")[-1] or "downloaded.txt"

        # Create source record
        source = Source(
            file_id=file_id,
            file_name=file_name,
            file_type="txt",
            file_size=len(extracted_content.encode("utf-8")),
            content_preview=extracted_content[:1000],
            full_content=extracted_content,
            content_hash=content_hash,
            is_url_source=1,
        )

        db.add(source)
        db.commit()
        db.refresh(source)

        return _ok(
            "download_response",
            {
                "file_id": file_id,
                "source_url": str(payload.url),
                "downloaded": True,
                "bytes_previewed": len(extracted_content),
                "duplicate": False,
            },
        )
    except Exception as exc:
        db.rollback()
        return _err(
            "download_response",
            error=f"download_failed: {str(exc)}",
            data={"source_url": str(payload.url), "downloaded": False},
        )
    finally:
        db.close()


@app.post("/extract", response_model=BaseResponse)
async def extract(payload: ExtractRequest) -> BaseResponse:
    db = SessionLocal()
    import tempfile
    import os

    try:
        # Query source by file_id
        source = db.query(Source).filter(Source.file_id == payload.file_id).first()
        if not source:
            return _err(
                "extract_response",
                error="file_not_found",
                data={"file_id": payload.file_id, "mode": payload.mode},
            )

        # Get full content
        content = source.full_content or source.content_preview or ""

        # For text files, use content directly; for binary formats, try parser
        extracted = content

        if source.file_type.lower() in ["pdf", "docx", "doc"]:
            try:
                # Write content to temp file for parser
                with tempfile.NamedTemporaryFile(
                    suffix=f".{source.file_type.lower()}", delete=False
                ) as tmp:
                    # For MVP, assume content is text representation; real files would be binary
                    tmp.write(content.encode("utf-8"))
                    tmp_path = tmp.name

                try:
                    # Try to parse with the appropriate parser
                    parse_result = parser_factory.parse(tmp_path, source.file_type.lower())
                    extracted = parse_result.get("text", content)
                except ParserError:
                    # Fall back to raw content if parsing fails
                    extracted = content
                finally:
                    os.unlink(tmp_path)
            except Exception as exc:
                # If temporary file handling fails, use raw content
                extracted = content

        # Apply extraction mode
        if payload.mode == "summary":
            extracted = extracted[:400]

        # Store extraction result
        extraction = Extraction(
            source_id=source.id,
            mode=payload.mode,
            extracted_text=extracted,
        )
        db.add(extraction)
        db.commit()

        return _ok(
            "extract_response",
            {
                "file_id": payload.file_id,
                "mode": payload.mode,
                "content": extracted,
                "chars": len(extracted),
            },
        )
    except Exception as exc:
        db.rollback()
        return _err(
            "extract_response",
            error=f"extract_failed: {str(exc)}",
            data={"file_id": payload.file_id, "mode": payload.mode},
        )
    finally:
        db.close()


@app.get("/sources", response_model=BaseResponse)
async def list_sources() -> BaseResponse:
    db = SessionLocal()
    try:
        sources = db.query(Source).all()
        items = [
            {
                "file_id": source.file_id,
                "file_name": source.file_name,
                "file_type": source.file_type,
                "created_at": source.upload_timestamp.isoformat(),
            }
            for source in sources
        ]
        return _ok("sources_response", {"items": items, "count": len(items)})
    except Exception as exc:
        return _err("sources_response", error=f"list_failed: {str(exc)}")
    finally:
        db.close()


@app.get("/source/{file_id}", response_model=BaseResponse)
async def get_source(file_id: str) -> BaseResponse:
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.file_id == file_id).first()
        if not source:
            return _err("source_response", error="file_not_found", data={"file_id": file_id})

        return _ok(
            "source_response",
            {
                "file_id": file_id,
                "file_name": source.file_name,
                "file_type": source.file_type,
                "content": source.content_preview or "",
                "created_at": source.upload_timestamp.isoformat(),
            },
        )
    except Exception as exc:
        return _err("source_response", error=f"get_failed: {str(exc)}", data={"file_id": file_id})
    finally:
        db.close()


@app.post("/video-to-text", response_model=BaseResponse)
async def video_to_text(payload: VideoToTextRequest) -> BaseResponse:
    try:
        # Try to get file extension from source path
        import os
        if os.path.exists(payload.source):
            file_type = os.path.splitext(payload.source)[1].lstrip(".")
            try:
                # Try to parse with VideoParser
                parse_result = parser_factory.parse(payload.source, file_type)
                return _ok(
                    "video_to_text_response",
                    {
                        "source": payload.source,
                        "transcript": parse_result.get("text", ""),
                        "model": "whisper-base",
                    },
                )
            except ParserError as exc:
                return _err(
                    "video_to_text_response",
                    error=f"transcription_failed: {str(exc)}",
                    data={"source": payload.source},
                )
        else:
            return _err(
                "video_to_text_response",
                error="source_not_found",
                data={"source": payload.source},
            )
    except Exception as exc:
        return _err(
            "video_to_text_response",
            error=f"transcription_error: {str(exc)}",
            data={"source": payload.source},
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
