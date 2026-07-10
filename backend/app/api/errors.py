from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    app_error = exc if isinstance(exc, AppError) else AppError("internal_error", "internal server error")
    return JSONResponse(
        status_code=app_error.status_code,
        content={
            "error": {
                "code": app_error.code,
                "message": app_error.message,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "artifact_validation_failed",
                "message": "stored artifact failed validation",
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )
