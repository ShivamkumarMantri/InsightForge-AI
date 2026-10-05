from typing import Optional, Any, Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import app_logger

class InsightForgeAPIException(Exception):
    """Base API Exception with code and status."""
    def __init__(
        self,
        message: str,
        code: str = "BAD_REQUEST",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.extra = extra or {}

class RateLimitException(InsightForgeAPIException):
    def __init__(self, message: str = "Rate limit exceeded. Please wait a moment before sending another request."):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class RequestTimeoutException(InsightForgeAPIException):
    def __init__(self, message: str = "The request timed out. Please try again with a more focused query."):
        super().__init__(
            message=message,
            code="REQUEST_TIMEOUT",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT
        )

class DatasetNotFoundException(InsightForgeAPIException):
    def __init__(self, dataset_id: str):
        super().__init__(
            message=f"Dataset with ID '{dataset_id}' was not found or has expired. Please upload the dataset again.",
            code="DATASET_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )

class FileSecurityException(InsightForgeAPIException):
    def __init__(self, message: str, code: str = "INVALID_FILE", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message=message, code=code, status_code=status_code)

class UnsupportedOperationException(InsightForgeAPIException):
    def __init__(self, operation: str):
        super().__init__(
            message=f"Operation '{operation}' is not supported. InsightForge strictly permits only approved analytical operations.",
            code="UNSUPPORTED_OPERATION",
            status_code=status.HTTP_400_BAD_REQUEST
        )

def format_error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """Standardized error response conforming to Step 9 specifications."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message
            }
        }
    )

# Exception handlers for FastAPI
async def custom_api_exception_handler(request: Request, exc: InsightForgeAPIException):
    app_logger.warning(
        f"API Error [{exc.code}] on {request.method} {request.url.path}: {exc.message}",
        extra={"extra_data": {"path": request.url.path, "code": exc.code, **exc.extra}}
    )
    return format_error_response(exc.code, exc.message, exc.status_code)

async def http_exception_handler(request: Request, exc: HTTPException):
    # Derive an appropriate code from status code
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        413: "PAYLOAD_TOO_LARGE",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        504: "REQUEST_TIMEOUT"
    }
    code = code_map.get(exc.status_code, "ERROR")
    message = str(exc.detail) if exc.detail else "An error occurred."
    
    app_logger.warning(f"HTTP {exc.status_code} [{code}] on {request.method} {request.url.path}: {message}")
    return format_error_response(code, message, exc.status_code)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    loc = " -> ".join(str(l) for l in first_error.get("loc", []))
    msg = first_error.get("msg", "Invalid request body")
    user_msg = f"Validation failed at '{loc}': {msg}" if loc else msg

    app_logger.warning(f"Validation Error on {request.method} {request.url.path}: {user_msg}")
    return format_error_response("VALIDATION_ERROR", user_msg, status.HTTP_422_UNPROCESSABLE_ENTITY)

async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exceptions: log stack trace internally, return clean error without leaking paths."""
    app_logger.error(
        f"Unhandled Internal Server Error on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )
    # Never expose internal paths or stack traces to clients
    safe_message = "An unexpected error occurred while processing your request. Please try again."
    return format_error_response("INTERNAL_SERVER_ERROR", safe_message, status.HTTP_500_INTERNAL_SERVER_ERROR)
