"""Application-level exceptions mapped to HTTP responses in main.py."""
from typing import Optional


class AppError(Exception):
    status_code = 500
    message = "Internal server error"

    def __init__(self, message: Optional[str] = None):
        if message:
            self.message = message
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    message = "Invalid request"


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    message = "Conflict"


class PermissionDeniedError(AppError):
    status_code = 403
    message = "Insufficient permissions"


class ModelUnavailableError(AppError):
    status_code = 503
    message = "The fraud detection model is not available. Predictions cannot be produced."


class PredictionError(AppError):
    status_code = 500
    message = "The model failed to produce a prediction."


class ExplanationError(AppError):
    status_code = 500
    message = "The explanation could not be generated."


class ModelLoadError(Exception):
    """Raised during startup when artifacts are missing or invalid."""
