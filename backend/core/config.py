import os
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class Settings(BaseModel):
    api_prefix: str = Field(default="/api/v1")
    database_url: str = Field(default="sqlite:///./docuhub.db")
    url_download_timeout_s: int = Field(default=5, ge=1)
    extract_timeout_s: int = Field(default=3, ge=1)
    max_download_chars: int = Field(default=20000, ge=1)
    max_upload_chars: int = Field(default=200000, ge=1)
    concurrency_limit: int = Field(default=20, ge=1)
    allowed_file_types: tuple[str, ...] = (
        "pdf",
        "docx",
        "txt",
        "md",
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    @field_validator("api_prefix")
    @classmethod
    def _validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/api/"):
            raise ValueError("api_prefix must start with /api/")
        return value

    @classmethod
    def from_env(cls, env: dict[str, Any] | None = None) -> "Settings":
        source = env or os.environ
        payload = {
            "api_prefix": source.get("API_PREFIX", "/api/v1"),
            "database_url": source.get("DATABASE_URL", "sqlite:///./docuhub.db"),
            "url_download_timeout_s": int(source.get("URL_DOWNLOAD_TIMEOUT_S", "5")),
            "extract_timeout_s": int(source.get("EXTRACT_TIMEOUT_S", "3")),
            "max_download_chars": int(source.get("MAX_DOWNLOAD_CHARS", "20000")),
            "max_upload_chars": int(source.get("MAX_UPLOAD_CHARS", "200000")),
            "concurrency_limit": int(source.get("CONCURRENCY_LIMIT", "20")),
        }
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid settings: {exc}") from exc


settings = Settings.from_env()
