"""OpenRouter OAuth — PKCE 認証.
ポート 3000 で一時 HTTP サーバー。全体を run_in_executor でスレッドオフロード。
"""

import os
import hashlib
import base64
import socket
import webbrowser
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode

import httpx

from app.auth import token_store

_CALLBACK_PORT = 3000
_CALLBACK_URL = f"http://localhost:{_CALLBACK_PORT}/callback"
_AUTH_URL = "https://openrouter.ai/auth"
_TOKEN_URL = "https://openrouter.ai/api/v1/auth/keys"
_TIMEOUT = 120


def _generate_pkce() -> tuple[str, str]:
    """PKCE code_verifier と code_challenge を生成。"""
    verifier_bytes = os.urandom(64)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def _is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _run_pkce_flow() -> dict:
    """同期版 PKCE フロー。"""
    if not _is_port_available(_CALLBACK_PORT):
        raise RuntimeError(f"ポート {_CALLBACK_PORT} が使用中です。他のアプリケーションを終了してください。")

    code_verifier, code_challenge = _generate_pkce()

    params = urlencode({
        "callback_url": _CALLBACK_URL,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "limit": "5",
        "usage_limit_type": "monthly",
    })
    auth_url = f"{_AUTH_URL}?{params}"

    received_code = None

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal received_code
            parsed = urlparse(self.path)
            if parsed.path == "/callback":
                qs = parse_qs(parsed.query)
                received_code = qs.get("code", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = "<html><body><h1>認証完了</h1><p>このタブを閉じてください。</p></body></html>"
                self.wfile.write(html.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # サイレント

    server = HTTPServer(("127.0.0.1", _CALLBACK_PORT), CallbackHandler)
    server.timeout = _TIMEOUT

    webbrowser.open(auth_url)
    server.handle_request()
    server.server_close()

    if not received_code:
        raise RuntimeError("認証コードを受信できませんでした。タイムアウトした可能性があります。")

    with httpx.Client() as client:
        resp = client.post(_TOKEN_URL, json={
            "code": received_code,
            "code_verifier": code_verifier,
            "code_challenge_method": "S256",
        })
        resp.raise_for_status()
        data = resp.json()

    api_key = data.get("key", "")
    if not api_key:
        raise RuntimeError("API キーの取得に失敗しました。")

    return {"key": api_key}


async def start_pkce_flow() -> dict:
    """PKCE フローを開始し、結果を返す。"""
    token_data = await asyncio.to_thread(_run_pkce_flow)
    await token_store.save_token("openrouter", token_data)
    return {"status": "ok", "message": "認証完了"}


async def get_auth_status() -> dict:
    """OpenRouter 認証状態を返す。"""
    tok = await token_store.load_token("openrouter")
    if tok and "key" in tok:
        return {"authenticated": True}
    return {"authenticated": False}


async def logout() -> None:
    """OpenRouter のトークンを削除。"""
    await token_store.delete_token("openrouter")
