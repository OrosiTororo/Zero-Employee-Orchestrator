"""Security headers middleware -- Add security headers to HTTP responses.

Automatically adds OWASP-recommended security headers to all responses,
mitigating attacks such as XSS, clickjacking, and MIME sniffing.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

OAUTH_RESPONSE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'"
    ),
}

_SENSITIVE_GOOGLE_OAUTH_PATH_SUFFIXES = (
    "/auth/google/authorize",
    "/auth/google/callback",
    "/auth/google/poll",
    "/sso/oauth/google/authorize",
    "/sso/oauth/google/callback",
)


def is_sensitive_google_oauth_path(path: str) -> bool:
    """Return whether a request path belongs to a credential-bearing Google OAuth flow."""
    normalized_path = path.rstrip("/")
    return normalized_path.endswith(_SENSITIVE_GOOGLE_OAUTH_PATH_SUFFIXES)


def apply_oauth_response_headers(response: Response) -> None:
    """Apply the non-cacheable, non-referring policy required by OAuth responses."""
    for name, value in OAUTH_RESPONSE_HEADERS.items():
        response.headers[name] = value


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # XSS prevention
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        # Content Security Policy
        response.headers.setdefault(
            "Content-Security-Policy",
            (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'"
            ),
        )

        # HTTPS enforcement (for production)
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

        # Referrer control
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )

        # Permissions Policy (restrict browser features)
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )

        # Cache control (prevent caching of authenticated responses)
        if request.headers.get("Authorization"):
            response.headers.setdefault(
                "Cache-Control",
                "no-store, no-cache, must-revalidate, private",
            )
            response.headers.setdefault("Pragma", "no-cache")

        # OAuth exceptions and validation/rate-limit responses are produced outside
        # the endpoint's injected Response object, so enforce the route policy here.
        if is_sensitive_google_oauth_path(request.url.path):
            apply_oauth_response_headers(response)

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation middleware -- Reject invalid requests early."""

    # Maximum allowed request body size (10MB)
    MAX_BODY_SIZE: int = 10 * 1024 * 1024

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Content-Length check (with safe int conversion)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size < 0 or size > self.MAX_BODY_SIZE:
                    return Response(
                        content='{"detail": "Request body too large"}',
                        status_code=413,
                        media_type="application/json",
                    )
            except (ValueError, OverflowError):
                return Response(
                    content='{"detail": "Invalid Content-Length header"}',
                    status_code=400,
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
    """Validate whether the Host header is legitimate.

    Rejects oversized headers and validates IP octets are in 0-255 range.
    """
    import ipaddress
    import re

    if len(host) > 255:
        return False

    # Separate host and port
    host_part = host
    if ":" in host:
        parts = host.rsplit(":", 1)
        host_part = parts[0]
        try:
            port = int(parts[1])
            if port < 1 or port > 65535:
                return False
        except (ValueError, OverflowError):
            return False

    # Allow localhost
    if host_part.lower() == "localhost":
        return True

    # Validate IP addresses with proper octet range checking
    try:
        ipaddress.ip_address(host_part)
        return True
    except ValueError:
        pass

    # If the host looks like an IP (digits and dots only), reject it here
    # since ipaddress.ip_address() already failed above.
    if re.fullmatch(r"[\d.]+", host_part):
        return False

    # Validate domain names (RFC 1123)
    domain_pattern = re.compile(
        r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
    )
    return bool(domain_pattern.match(host_part))
