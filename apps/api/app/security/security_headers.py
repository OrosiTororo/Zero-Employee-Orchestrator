"""セキュリティヘッダーミドルウェア — HTTPレスポンスにセキュリティヘッダーを付与する.

OWASP 推奨のセキュリティヘッダーを全レスポンスに自動付与し、
XSS・クリックジャッキング・MIMEスニッフィング等の攻撃を軽減する。
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーを全レスポンスに付与するミドルウェア."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # XSS 防止
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # コンテンツセキュリティポリシー
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )

        # HTTPS 強制（本番環境向け）
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Referrer 制御
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 権限ポリシー（ブラウザ機能の制限）
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # キャッシュ制御（認証済みレスポンスのキャッシュ防止）
        if request.headers.get("Authorization"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """リクエスト検証ミドルウェア — 不正なリクエストを早期に拒否する."""

    # 許可する最大リクエストボディサイズ（10MB）
    MAX_BODY_SIZE: int = 10 * 1024 * 1024

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Content-Length チェック
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return Response(
                content='{"detail": "Request body too large"}',
                status_code=413,
                media_type="application/json",
            )

        # Host ヘッダー検証（Host ヘッダーインジェクション防止）
        host = request.headers.get("host", "")
        if host and not _is_valid_host(host):
            return Response(
                content='{"detail": "Invalid Host header"}',
                status_code=400,
                media_type="application/json",
            )

        return await call_next(request)


def _is_valid_host(host: str) -> bool:
    """Host ヘッダーが正当かどうかを検証する."""
    import re

    # localhost, IP アドレス, 通常のドメイン名を許可
    # ポート番号付きも許可
    pattern = re.compile(
        r"^("
        r"localhost(:\d+)?|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?|"
        r"[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*(:\d+)?"
        r")$"
    )
    return bool(pattern.match(host))
