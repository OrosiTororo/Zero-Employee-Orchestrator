"""入力サニタイゼーションミドルウェア — 全APIリクエストの入力を自動検査する.

全 POST/PUT/PATCH リクエストのボディを自動スキャンし、
プロンプトインジェクション試行を検出・拒否する。
PII 検出はログ記録のみ行い、マスキングはサービス層に委譲する。

これにより、個別ルートでの scan_prompt_injection() 呼び出し漏れを防止する。
"""

from __future__ import annotations

import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection

logger = logging.getLogger(__name__)

# スキャン対象外のパス（認証・ヘルスチェック等）
_SKIP_PATHS: frozenset[str] = frozenset(
    {
        "/healthz",
        "/readyz",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/docs",
        "/openapi.json",
    }
)

# ファイルアップロード系のContent-Typeはスキップ
_SKIP_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "multipart/form-data",
        "application/octet-stream",
    }
)


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """リクエストボディのプロンプトインジェクション検査ミドルウェア.

    POST/PUT/PATCH リクエストの JSON ボディをスキャンし、
    CRITICAL/HIGH レベルの脅威を検出した場合は HTTP 422 で拒否する。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # GET/DELETE/OPTIONS はスキップ
        if request.method in ("GET", "DELETE", "OPTIONS", "HEAD"):
            return await call_next(request)

        # パスベースのスキップ
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        # ファイルアップロードはスキップ（バイナリデータ）
        content_type = request.headers.get("content-type", "")
        for skip_ct in _SKIP_CONTENT_TYPES:
            if skip_ct in content_type:
                return await call_next(request)

        # JSON ボディのみスキャン
        if "application/json" not in content_type:
            return await call_next(request)

        try:
            body = await request.body()
            if not body:
                return await call_next(request)

            text_values = _extract_text_values(body)
            if not text_values:
                return await call_next(request)

            # プロンプトインジェクションスキャン
            combined_text = " ".join(text_values)
            guard_result = scan_prompt_injection(combined_text)

            if not guard_result.is_safe and guard_result.threat_level in (
                ThreatLevel.CRITICAL,
                ThreatLevel.HIGH,
            ):
                logger.warning(
                    "Prompt injection detected [%s] path=%s detections=%s",
                    guard_result.threat_level.value,
                    request.url.path,
                    guard_result.detections,
                )
                return Response(
                    content=json.dumps(
                        {
                            "detail": "Potentially unsafe input detected",
                            "threat_level": guard_result.threat_level.value,
                        }
                    ),
                    status_code=422,
                    media_type="application/json",
                )

            # PII 検出（ログ記録のみ、ブロックしない）
            pii_result = detect_and_mask_pii(combined_text)
            if pii_result.has_pii:
                logger.info(
                    "PII detected in request path=%s categories=%s count=%d",
                    request.url.path,
                    pii_result.detected_types,
                    pii_result.detected_count,
                )

        except Exception:
            # パース失敗時はスキップ（JSONでないリクエスト等）
            pass

        return await call_next(request)


def _extract_text_values(body: bytes, max_depth: int = 5) -> list[str]:
    """JSON ボディから文字列値を再帰的に抽出する."""
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []

    values: list[str] = []
    _walk(data, values, max_depth)
    return values


def _walk(obj: object, values: list[str], depth: int) -> None:
    """再帰的に JSON 値を走査し文字列を収集する."""
    if depth <= 0:
        return
    if isinstance(obj, str) and len(obj) > 5:
        values.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _walk(v, values, depth - 1)
    elif isinstance(obj, list):
        for item in obj:
            _walk(item, values, depth - 1)
