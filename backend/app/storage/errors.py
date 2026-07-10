from app.api.errors import AppError


class ArtifactValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("artifact_validation_failed", message, status_code=500)
