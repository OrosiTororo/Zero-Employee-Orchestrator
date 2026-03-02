"""Webhook Module テスト"""

import pytest
import tempfile
from pathlib import Path

from app.webhook.models import WebhookConfig, WebhookEvent, WebhookPayload
from app.webhook.dispatcher import (
    init_webhooks,
    register_webhook,
    list_webhooks,
    get_webhook,
    update_webhook,
    delete_webhook,
    get_deliveries,
)


@pytest.fixture(autouse=True)
def setup_webhooks(tmp_path):
    init_webhooks(tmp_path / "webhooks.json")
    # Clear any existing webhooks
    for wh in list_webhooks():
        delete_webhook(wh.id)


def test_register_and_list():
    config = WebhookConfig(
        name="test-n8n",
        url="https://n8n.example.com/webhook/test",
    )
    registered = register_webhook(config)
    assert registered.id == config.id
    assert registered.name == "test-n8n"

    all_hooks = list_webhooks()
    assert len(all_hooks) == 1
    assert all_hooks[0].url == "https://n8n.example.com/webhook/test"


def test_get_webhook():
    config = WebhookConfig(name="get-test", url="https://example.com/wh")
    register_webhook(config)

    fetched = get_webhook(config.id)
    assert fetched is not None
    assert fetched.name == "get-test"


def test_update_webhook():
    config = WebhookConfig(name="old-name", url="https://example.com/wh")
    register_webhook(config)

    updated = update_webhook(config.id, {"name": "new-name", "active": False})
    assert updated is not None
    assert updated.name == "new-name"
    assert updated.active is False


def test_delete_webhook():
    config = WebhookConfig(name="delete-me", url="https://example.com/wh")
    register_webhook(config)
    assert len(list_webhooks()) == 1

    result = delete_webhook(config.id)
    assert result is True
    assert len(list_webhooks()) == 0


def test_delete_nonexistent():
    result = delete_webhook("nonexistent-id")
    assert result is False


def test_webhook_events():
    config = WebhookConfig(
        name="events-test",
        url="https://example.com/wh",
        events=[WebhookEvent.ORCHESTRATION_COMPLETED, WebhookEvent.SKILL_GENERATED],
    )
    register_webhook(config)

    fetched = get_webhook(config.id)
    assert fetched is not None
    assert len(fetched.events) == 2
    assert WebhookEvent.ORCHESTRATION_COMPLETED in fetched.events


def test_webhook_payload_model():
    payload = WebhookPayload(
        event="orchestration.completed",
        data={"orchestration_id": "abc123", "results": {"key": "value"}},
    )
    dumped = payload.model_dump()
    assert dumped["event"] == "orchestration.completed"
    assert dumped["source"] == "zpcos"
    assert "timestamp" in dumped


def test_default_events_all():
    config = WebhookConfig(name="all-events", url="https://example.com/wh")
    assert len(config.events) == len(WebhookEvent)


def test_secret_auto_generated():
    config = WebhookConfig(name="secret-test", url="https://example.com/wh")
    assert len(config.secret) > 0
