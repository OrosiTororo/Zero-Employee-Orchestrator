"""Security headers middleware -- Add security headers to HTTP responses.

Automatically adds OWASP-recommended security headers to all responses,
mitigating attacks such as XSS, clickjacking, and MIME sniffing.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # XSS prevention
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )

        # HTTPS enforcement (for production)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Referrer control
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (restrict browser features)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Cache control (prevent caching of authenticated responses)
        if request.headers.get("Authorization"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation middleware -- Reject invalid requests early."""

    # Maximum allowed request body size (10MB)
    MAX_BODY_SIZE: int = 10 * 1024 * 1024

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Content-Length check
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return Response(
                content='{"detail": "Request body too large"}',
                status_code=413,
                media_type="application/json",
            )

        # Host header validation (prevent Host header injection)
        host = request.headers.get("host", "")
        if host and not _is_valid_host(host):
            return Response(
                content='{"detail": "Invalid Host header"}',
                status_code=400,
                media_type="application/json",
            )

        return await call_next(request)


def _is_valid_host(host: str) -> bool:
    """Validate whether the Host header is legitimate."""
    import re

    # Allow localhost, IP addresses, and standard domain names
    # Also allow with port numbers
    pattern = re.compile(
        r"^("
        r"localhost(:\d+)?|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?|"
        r"[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*(:\d+)?"
        r")$"
    )
    return bool(pattern.match(host))
