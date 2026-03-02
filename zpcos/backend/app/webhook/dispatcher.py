"""Webhook Dispatcher — イベント発火・配信・リトライ"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .models import (
    WebhookConfig,
    WebhookDelivery,
    WebhookEvent,
    WebhookPayload,
)

logger = logging.getLogger("zpcos.webhook")

# In-memory store (persistent JSON file backed)
_webhooks: dict[str, WebhookConfig] = {}
_deliveries: list[WebhookDelivery] = []
_config_path: Path | None = None


def _store_path() -> Path:
    import os
    if _config_path:
        return _config_path
    base = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "zpcos"
    base.mkdir(parents=True, exist_ok=True)
    return base / "webhooks.json"


def _save():
    """永続化"""
    data = {wid: w.model_dump() for wid, w in _webhooks.items()}
    _store_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load():
    """起動時ロード"""
    global _webhooks
    path = _store_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            _webhooks = {k: WebhookConfig(**v) for k, v in raw.items()}
            logger.info(f"Loaded {len(_webhooks)} webhook(s)")
        except Exception as e:
            logger.warning(f"Failed to load webhooks: {e}")


def init_webhooks(config_path: Path | None = None):
    """初期化"""
    global _config_path
    _config_path = config_path
    _load()


# --- CRUD ---

def register_webhook(config: WebhookConfig) -> WebhookConfig:
    _webhooks[config.id] = config
    _save()
    logger.info(f"Webhook registered: {config.id} → {config.url}")
    return config


def update_webhook(webhook_id: str, updates: dict) -> WebhookConfig | None:
    wh = _webhooks.get(webhook_id)
    if not wh:
        return None
    for k, v in updates.items():
        if hasattr(wh, k) and k not in ("id", "created_at", "secret"):
            setattr(wh, k, v)
    _save()
    return wh


def delete_webhook(webhook_id: str) -> bool:
    if webhook_id in _webhooks:
        del _webhooks[webhook_id]
        _save()
        return True
    return False


def list_webhooks() -> list[WebhookConfig]:
    return list(_webhooks.values())


def get_webhook(webhook_id: str) -> WebhookConfig | None:
    return _webhooks.get(webhook_id)


def get_deliveries(webhook_id: str | None = None, limit: int = 50) -> list[WebhookDelivery]:
    filtered = _deliveries
    if webhook_id:
        filtered = [d for d in filtered if d.webhook_id == webhook_id]
    return sorted(filtered, key=lambda d: d.timestamp, reverse=True)[:limit]


# --- Signature ---

def _compute_signature(payload_bytes: bytes, secret: str) -> str:
    """HMAC-SHA256 署名（n8n Header Auth 互換）"""
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


# --- Dispatch ---

async def _send_webhook(
    client: httpx.AsyncClient,
    webhook: WebhookConfig,
    payload: WebhookPayload,
    attempt: int = 1,
) -> WebhookDelivery:
    """単一Webhook送信"""
    payload_bytes = json.dumps(payload.model_dump(), ensure_ascii=False).encode()
    signature = _compute_signature(payload_bytes, webhook.secret)

    headers = {
        "Content-Type": "application/json",
        "X-ZPCOS-Signature": signature,
        "X-ZPCOS-Event": payload.event,
        "User-Agent": "ZPCOS-Webhook/0.1",
    }

    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event=WebhookEvent(payload.event),
        payload=payload.model_dump(),
        attempt=attempt,
    )

    try:
        resp = await client.post(
            webhook.url,
            content=payload_bytes,
            headers=headers,
            timeout=10.0,
        )
        delivery.status_code = resp.status_code
        delivery.response_body = resp.text[:500]
        delivery.success = 200 <= resp.status_code < 300

        if delivery.success:
            webhook.failure_count = 0
        else:
            webhook.failure_count += 1

    except Exception as e:
        delivery.success = False
        delivery.response_body = str(e)[:500]
        webhook.failure_count += 1
        logger.warning(f"Webhook delivery failed: {webhook.url} — {e}")

    webhook.last_triggered = datetime.now(timezone.utc).isoformat()
    _deliveries.append(delivery)
    _save()
    return delivery


async def dispatch_event(event: WebhookEvent, data: dict[str, Any]):
    """イベントを全登録済みWebhookに配信（非同期・リトライ付き）"""
    payload = WebhookPayload(event=event.value, data=data)

    targets = [
        wh for wh in _webhooks.values()
        if wh.active and event in wh.events
    ]

    if not targets:
        return

    logger.info(f"Dispatching {event.value} to {len(targets)} webhook(s)")

    async with httpx.AsyncClient() as client:
        tasks = [_send_webhook(client, wh, payload) for wh in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Retry failed deliveries
        for wh, result in zip(targets, results):
            if isinstance(result, WebhookDelivery) and not result.success:
                for attempt in range(2, wh.max_retries + 1):
                    await asyncio.sleep(attempt * 2)  # exponential-ish backoff
                    retry = await _send_webhook(client, wh, payload, attempt)
                    if retry.success:
                        break


# --- Test ---

async def test_webhook(webhook_id: str) -> WebhookDelivery | None:
    """テスト配信"""
    wh = _webhooks.get(webhook_id)
    if not wh:
        return None
    payload = WebhookPayload(
        event="test.ping",
        data={"message": "ZPCOS webhook test", "webhook_id": webhook_id},
    )
    async with httpx.AsyncClient() as client:
        return await _send_webhook(client, wh, payload)
