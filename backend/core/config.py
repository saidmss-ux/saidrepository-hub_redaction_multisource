import os
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class Settings(BaseModel):
    app_env: str = Field(default="local")
    api_prefix: str = Field(default="/api/v1")
    database_url: str = Field(default="sqlite:///./docuhub.db")
    debug: bool = Field(default=False)

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

    @field_validator("app_env")
    @classmethod
    def _validate_env(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"local", "staging", "production"}:
            raise ValueError("app_env must be one of: local, staging, production")
        return normalized

    @field_validator("api_prefix")
    @classmethod
    def _validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/api/"):
            raise ValueError("api_prefix must start with /api/")
        return value

    @model_validator(mode="after")
    def _validate_environment_db_rules(self) -> "Settings":
        is_sqlite = self.database_url.startswith("sqlite")
        is_postgres = self.database_url.startswith("postgresql")

        if self.app_env == "local" and not is_sqlite:
            raise ValueError("local environment must use sqlite database_url")

        if self.app_env in {"staging", "production"} and not is_postgres:
            raise ValueError("staging/production environment must use postgresql database_url")

        if self.app_env in {"staging", "production"} and self.debug:
            raise ValueError("debug must be false in staging/production")

        return self

    @classmethod
    def from_env(cls, env: dict[str, Any] | None = None) -> "Settings":
        source = env or os.environ
        payload = {
            "app_env": source.get("APP_ENV", "local"),
            "api_prefix": source.get("API_PREFIX", "/api/v1"),
            "database_url": source.get("DATABASE_URL", "sqlite:///./docuhub.db"),
            "debug": source.get("DEBUG", "false").lower() == "true",
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
