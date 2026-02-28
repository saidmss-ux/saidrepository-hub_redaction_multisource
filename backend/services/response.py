from backend.models import BaseResponse, ErrorObject


def ok(data: dict | None) -> BaseResponse:
    return BaseResponse(success=True, data=data, error=None)


def fail(code: str, message: str, details: dict | None = None) -> BaseResponse:
    return BaseResponse(
        success=False,
        data=None,
        error=ErrorObject(code=code, message=message, details=details or {}),
    )
