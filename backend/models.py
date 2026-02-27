from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class BaseResponse(BaseModel):
    type: str = Field(..., description="Response type identifier")
    version: int = Field(default=1, ge=1)
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class UploadRequest(BaseModel):
    file_name: str = Field(..., min_length=1)
    file_type: str = Field(..., min_length=1)
    content: str = Field(default="")


class DownloadFromUrlRequest(BaseModel):
    url: HttpUrl


class ExtractRequest(BaseModel):
    file_id: str = Field(..., min_length=1)
    mode: Literal["text", "summary"] = "text"


class VideoToTextRequest(BaseModel):
    source: str = Field(..., min_length=1)


class AIAssistRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    api_key_enabled: bool = False
