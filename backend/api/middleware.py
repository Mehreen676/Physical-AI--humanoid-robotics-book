"""
API middleware for logging and error handling.

Provides request/response logging and standardized error handling.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
from utils.errors import RAGError, get_http_status_code, build_error_response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging incoming requests and outgoing responses."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response details."""
        # Record start time
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            # Log exception and return error response
            logger.error(f"Unhandled exception: {exc}", exc_info=True)

            if isinstance(exc, RAGError):
                status_code = exc.http_status
                error_response = build_error_response(exc)
            else:
                status_code = 500
                error_response = {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred."
                }

            return JSONResponse(
                status_code=status_code,
                content=error_response
            )

        # Record response time
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration:.3f}s)"
        )

        # Add response time header
        response.headers["X-Process-Time"] = str(duration)

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for standardized error handling."""

    async def dispatch(self, request: Request, call_next):
        """Handle errors and convert to JSON responses."""
        try:
            response = await call_next(request)
            return response
        except RAGError as exc:
            logger.error(f"RAG error: {exc.message}")
            return JSONResponse(
                status_code=exc.http_status,
                content=build_error_response(exc)
            )
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please try again later."
                }
            )
