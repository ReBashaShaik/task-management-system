"""Turn service errors into consistent, beginner-friendly API responses."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services.errors import AuthenticationError, ServiceError


def register_exception_handlers(app: FastAPI) -> None:
    """Tell FastAPI how to return errors raised by the service layer."""

    @app.exception_handler(ServiceError)
    async def handle_service_error(_request: Request, error: ServiceError):
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(error, AuthenticationError) else None
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.message},
            headers=headers,
        )
