import os


class Settings:
    api_prefix: str = "/api/v1"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./docuhub.db")
    url_download_timeout_s: int = int(os.getenv("URL_DOWNLOAD_TIMEOUT_S", "5"))
    extract_timeout_s: int = int(os.getenv("EXTRACT_TIMEOUT_S", "3"))
    max_download_chars: int = int(os.getenv("MAX_DOWNLOAD_CHARS", "20000"))
    max_upload_chars: int = int(os.getenv("MAX_UPLOAD_CHARS", "200000"))
    allowed_file_types: tuple[str, ...] = (
        "pdf",
        "docx",
        "txt",
        "md",
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


settings = Settings()
