import os


class Settings:
    api_prefix: str = "/api/v1"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./docuhub.db")
    url_download_timeout_s: int = int(os.getenv("URL_DOWNLOAD_TIMEOUT_S", "5"))
    max_download_chars: int = int(os.getenv("MAX_DOWNLOAD_CHARS", "20000"))
    max_upload_chars: int = int(os.getenv("MAX_UPLOAD_CHARS", "200000"))


settings = Settings()
