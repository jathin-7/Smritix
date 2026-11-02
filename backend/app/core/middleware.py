from __future__ import annotations
import uuid
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import SmritixException

logger = structlog.get_logger()

def setup_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next): # type: ignore
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(SmritixException)
    async def smritix_exception_handler(request: Request, exc: SmritixException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "Smritix business exception handled",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                },
                "meta": {
                    "request_id": request_id,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        first_error_msg = errors[0].get("msg", "Invalid request parameters") if errors else "Validation error"
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": first_error_msg,
                    "details": errors,
                },
                "meta": {
                    "request_id": request_id,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Unhandled server exception",
            error=str(exc),
            exc_info=True,
            request_id=request_id,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred.",
                },
                "meta": {
                    "request_id": request_id,
                },
            },
        )
