from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(status_code=401, code="AUTHENTICATION_REQUIRED", message=message)


class AuthorizationError(AppError):
    def __init__(self, message: str = "You are not authorised to perform this action") -> None:
        super().__init__(status_code=403, code="FORBIDDEN", message=message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(status_code=404, code="NOT_FOUND", message=message)


class ModelConfigurationError(AppError):
    def __init__(self, message: str = "The model provider is not configured") -> None:
        super().__init__(status_code=503, code="MODEL_NOT_CONFIGURED", message=message)


class ModelProviderError(AppError):
    def __init__(self, message: str = "The model provider could not complete the request") -> None:
        super().__init__(status_code=502, code="MODEL_PROVIDER_ERROR", message=message)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def _error_payload(
    request: Request,
    *,
    code: str,
    message: str,
    details: Any | None = None,
) -> Mapping[str, Any]:
    return {
        "success": False,
        "code": code,
        "message": message,
        "correlation_id": _correlation_id(request),
        "details": details or [],
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                request,
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                request,
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                request,
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
            ),
        )
