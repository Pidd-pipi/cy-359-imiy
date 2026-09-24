class AppError(Exception):
    """业务异常，view 层统一转成 JSON 响应。"""

    status_code = 400
    error_code = "bad_request"

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload or {}


class ValidationError(AppError):
    status_code = 400
    error_code = "invalid"


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


ERROR_MESSAGES = {
    "overview_unavailable": "Overview data is unavailable",
}
