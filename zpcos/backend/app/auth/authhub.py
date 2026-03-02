"""AuthHub — 統合認証マネージャー.
POST   /api/auth/connect/{service}
GET    /api/auth/connections
DELETE /api/auth/disconnect/{service}
GET    /api/auth/token/{service}
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.main import resource_path
from app.auth import token_store
from app.auth import openrouter_oauth
from app.auth import google_oauth

router = APIRouter(prefix="/api/auth", tags=["auth"])

_connectors: dict[str, dict] = {}


def load_connectors() -> None:
    """connectors/ ディレクトリの JSON を全読み込み。"""
    global _connectors
    connectors_dir = resource_path("auth/connectors")
    for f in Path(connectors_dir).glob("*.json"):
        if f.name.startswith("_"):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        _connectors[data["service"]] = data


@router.post("/login")
async def login():
    """OpenRouter PKCE フローを開始。"""
    return await openrouter_oauth.start_pkce_flow()


@router.get("/status")
async def auth_status():
    """OpenRouter 認証状態を返す。"""
    return await openrouter_oauth.get_auth_status()


@router.post("/logout")
async def logout():
    """OpenRouter ログアウト。"""
    await openrouter_oauth.logout()
    return {"status": "ok"}


@router.post("/connect/{service}")
async def connect_service(service: str):
    """外部サービスに接続。"""
    if service == "openrouter":
        return await openrouter_oauth.start_pkce_flow()
    elif service == "google":
        return await google_oauth.connect_google()
    else:
        raise HTTPException(404, f"Unknown service: {service}")


@router.get("/connections")
async def list_connections():
    """全コネクターの接続状態を返す。"""
    result = []
    for svc, meta in _connectors.items():
        connected = await token_store.has_token(svc)
        result.append({
            "service": svc,
            "display_name": meta["display_name"],
            "connected": connected,
        })
    return result


@router.delete("/disconnect/{service}")
async def disconnect_service(service: str):
    """サービスを切断。"""
    if service == "google":
        await google_oauth.disconnect_google()
    else:
        await token_store.delete_token(service)
    return {"status": "ok"}


@router.get("/token/{service}")
async def get_token(service: str):
    """内部 API: 有効なトークンを返す。"""
    if service == "google":
        creds = await google_oauth.get_google_credentials()
        if not creds:
            raise HTTPException(401, "Google not connected or token expired")
        return {"token": creds.token, "scopes": list(creds.scopes or [])}
    tok = await token_store.load_token(service)
    if not tok:
        raise HTTPException(401, f"{service} not connected")
    return tok
