from __future__ import annotations

class SmritixException(Exception):
    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(self.message)

class NotFoundError(SmritixException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(404, "NOT_FOUND", message)

class ForbiddenError(SmritixException):
    def __init__(self, message: str = "Access forbidden") -> None:
        super().__init__(403, "FORBIDDEN", message)

class UnauthorizedError(SmritixException):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(401, "UNAUTHORIZED", message)

class ValidationError(SmritixException):
    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(422, "VALIDATION_ERROR", message)

class ConflictError(SmritixException):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(409, "CONFLICT", message)

class ExternalServiceError(SmritixException):
    def __init__(self, message: str = "External service failed") -> None:
        super().__init__(502, "EXTERNAL_SERVICE_ERROR", message)
