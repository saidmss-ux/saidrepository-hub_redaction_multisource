import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

# Load environment variables from .env file
_env_file = os.path.join(os.path.dirname(__file__), '../.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)


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


    jwt_secret: str = Field(default="change-me-local-secret")
    jwt_ttl_seconds: int = Field(default=3600, ge=60)
    auth_roles: tuple[str, ...] = ("admin", "user")
    default_tenant_id: str = Field(default="default")
    tenancy_enforced: bool = Field(default=False)

    rate_limit_requests: int = Field(default=120, ge=1)
    rate_limit_window_s: int = Field(default=60, ge=1)
    rate_limit_backend: str = Field(default="memory")
    rate_limit_redis_url: str = Field(default="")

    audit_enabled: bool = Field(default=False)
    audit_strict_mode: bool = Field(default=False)

    worker_enabled: bool = Field(default=False)
    queue_backend_url: str = Field(default="")
    batch_async_enabled: bool = Field(default=False)

    feature_flags_backend: str = Field(default="memory")
    feature_flags_cache_ttl: int = Field(default=30, ge=1)

    refresh_token_ttl_s: int = Field(default=604800, ge=300)
    refresh_rotation_enabled: bool = Field(default=False)
    refresh_reuse_detection: bool = Field(default=False)

    cors_allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    hsts_enabled: bool = Field(default=False)

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
        # Map development to local for compatibility
        if normalized == "development":
            normalized = "local"
        if normalized not in {"local", "staging", "production"}:
            raise ValueError("app_env must be one of: local, staging, production")
        return normalized

    @field_validator("api_prefix")
    @classmethod
    def _validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/api/"):
            raise ValueError("api_prefix must start with /api/")
        return value

    @field_validator("rate_limit_backend")
    @classmethod
    def _validate_rate_limit_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "redis"}:
            raise ValueError("rate_limit_backend must be one of: memory, redis")
        return normalized

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

        if self.app_env in {"staging", "production"} and self.jwt_secret == "change-me-local-secret":
            raise ValueError("jwt_secret must be customized in staging/production")

        if self.rate_limit_backend == "redis" and not self.rate_limit_redis_url:
            raise ValueError("rate_limit_redis_url must be set when rate_limit_backend=redis")

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
            "jwt_secret": source.get("JWT_SECRET", "change-me-local-secret"),
            "jwt_ttl_seconds": int(source.get("JWT_TTL_SECONDS", "3600")),
            "default_tenant_id": source.get("DEFAULT_TENANT_ID", "default"),
            "tenancy_enforced": source.get("TENANCY_ENFORCED", "false").lower() == "true",
            "rate_limit_requests": int(source.get("RATE_LIMIT_REQUESTS", "120")),
            "rate_limit_window_s": int(source.get("RATE_LIMIT_WINDOW_S", "60")),
            "rate_limit_backend": source.get("RATE_LIMIT_BACKEND", "memory"),
            "rate_limit_redis_url": source.get("RATE_LIMIT_REDIS_URL", ""),
            "audit_enabled": source.get("AUDIT_ENABLED", "false").lower() == "true",
            "audit_strict_mode": source.get("AUDIT_STRICT_MODE", "false").lower() == "true",
            "worker_enabled": source.get("WORKER_ENABLED", "false").lower() == "true",
            "queue_backend_url": source.get("QUEUE_BACKEND_URL", ""),
            "batch_async_enabled": source.get("BATCH_ASYNC_ENABLED", "false").lower() == "true",
            "feature_flags_backend": source.get("FEATURE_FLAGS_BACKEND", "memory"),
            "feature_flags_cache_ttl": int(source.get("FEATURE_FLAGS_CACHE_TTL", "30")),
            "refresh_token_ttl_s": int(source.get("REFRESH_TOKEN_TTL_S", "604800")),
            "refresh_rotation_enabled": source.get("REFRESH_ROTATION_ENABLED", "false").lower() == "true",
            "refresh_reuse_detection": source.get("REFRESH_REUSE_DETECTION", "false").lower() == "true",
            "cors_allowed_origins": tuple(filter(None, source.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(","))),
            "hsts_enabled": source.get("HSTS_ENABLED", "false").lower() == "true",
        }
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid settings: {exc}") from exc


settings = Settings.from_env()
