"""Model Catalog Auto-Update — OpenRouter API からモデル一覧を更新。"""

import json
from pathlib import Path
from typing import Optional

import httpx

from app.main import resource_path
from app.auth import token_store


async def fetch_model_catalog() -> list[dict]:
    """OpenRouter からモデルカタログを取得。"""
    tok = await token_store.load_token("openrouter")
    if not tok or "key" not in tok:
        return []

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {tok['key']}"},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", [])
    return []


async def update_providers_if_needed() -> bool:
    """新しいモデルが利用可能な場合、providers.json を更新。"""
    # MVP では手動更新のみ。自動更新は将来実装。
    return False
