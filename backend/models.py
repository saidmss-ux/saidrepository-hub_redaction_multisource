from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

ExtractMode = Literal["text", "summary"]


class ErrorObject(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class BaseResponse(BaseModel):
    success: bool
    data: dict[str, Any] | None = None
    error: ErrorObject | None = None


class UploadRequest(BaseModel):
    file_name: str = Field(..., min_length=1)
    file_type: str = Field(..., min_length=1)
    content: str = Field(default="")


class DownloadFromUrlRequest(BaseModel):
    url: HttpUrl


class ExtractRequest(BaseModel):
    file_id: int = Field(..., ge=1)
    mode: ExtractMode = "text"


class VideoToTextRequest(BaseModel):
    source: str = Field(..., min_length=1)


class AIAssistRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    api_key_enabled: bool = False
