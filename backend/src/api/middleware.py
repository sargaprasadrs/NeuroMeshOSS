import logging
import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jwt.exceptions import PyJWTError
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        process_time = time.perf_counter() - start_time
        
        # Append correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response


class JwtAuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check authorization header
        auth_header = request.headers.get("Authorization")
        request.state.user = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = AuthService.decode_access_token(token)
                request.state.user = payload
            except PyJWTError:
                # Malformed or expired token: set user to None
                # Endpoints that require authentication will fail at the dependency injection level
                pass
        
        return await call_next(request)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.error(f"Unhandled Exception [Correlation ID: {correlation_id}]: {exc}", exc_info=True)
        
        # Return RFC 7807 compliant JSON problem details
        return JSONResponse(
            status_code=500,
            content={
                "type": "/errors/internal-server-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": str(exc) if request.app.debug else "An unexpected error occurred. Please contact system administrators.",
                "instance": request.url.path,
                "correlation_id": correlation_id,
            },
            headers={"Content-Type": "application/problem+json"},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        return JSONResponse(
            status_code=400,
            content={
                "type": "/errors/bad-request",
                "title": "Bad Request",
                "status": 400,
                "detail": str(exc),
                "instance": request.url.path,
                "correlation_id": correlation_id,
            },
            headers={"Content-Type": "application/problem+json"},
        )
