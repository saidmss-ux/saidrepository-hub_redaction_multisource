from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    type: str = Field(..., description="Response type identifier")
    version: int = Field(default=1, ge=1)
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class UploadRequest(BaseModel):
    file_name: str
    file_type: str


class DownloadFromUrlRequest(BaseModel):
    url: str


class ExtractRequest(BaseModel):
    file_id: str
    mode: str = Field(default="text")


class VideoToTextRequest(BaseModel):
    source: str


class AIAssistRequest(BaseModel):
    prompt: str
    api_key_enabled: bool = False
