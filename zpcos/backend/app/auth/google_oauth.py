"""Google OAuth — InstalledAppFlow PKCE.
run_local_server(port=0) を asyncio.to_thread でスレッドオフロード。
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.main import resource_path
from app.auth import token_store


def _find_client_secrets() -> Path:
    """client_secret.json を 3段階で探索。"""
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "zpcos" / "client_secret.json",
        resource_path("client_secret.json"),
        Path(__file__).parent.parent.parent / "client_secret.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(
        "client_secret.json が見つかりません。"
        "Google Cloud Console からダウンロードし、設定画面からインポートしてください。"
    )


def _load_scopes() -> list[str]:
    """connectors/google.json からスコープを読み込み。"""
    p = resource_path("auth/connectors/google.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)["scopes"]


async def connect_google() -> dict:
    """Google OAuth フローを開始。ブラウザが開く。"""
    secrets_path = _find_client_secrets()
    scopes = _load_scopes()
    flow = InstalledAppFlow.from_client_secrets_file(
        str(secrets_path), scopes, autogenerate_code_verifier=True
    )
    credentials = await asyncio.to_thread(
        flow.run_local_server, port=0, open_browser=True
    )
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or []),
    }
    await token_store.save_token("google", token_data)
    return {"status": "ok", "scopes": token_data["scopes"]}


async def get_google_credentials() -> Optional[Credentials]:
    """有効な Google Credentials を返す。期限切れなら自動更新。"""
    token_data = await token_store.load_token("google")
    if not token_data:
        return None
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )
    if creds.expired and creds.refresh_token:
        try:
            await asyncio.to_thread(creds.refresh, Request())
            token_data["token"] = creds.token
            await token_store.save_token("google", token_data)
        except Exception:
            return None
    return creds


async def disconnect_google() -> None:
    """Google トークンを削除。"""
    await token_store.delete_token("google")
