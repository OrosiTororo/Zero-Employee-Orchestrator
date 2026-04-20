"""Tests for UserInputService (task-runtime user-input prompts)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.user_input_service import (
    InputRequestStatus,
    InputRequestType,
    UserInputService,
)


@pytest.mark.asyncio
async def test_request_input_returns_id_and_stores_request():
    svc = UserInputService()
    rid = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.TEXT,
        prompt_text="Name?",
    )
    assert rid
    req = svc.get_request(rid)
    assert req is not None
    assert req.status == InputRequestStatus.PENDING


@pytest.mark.asyncio
async def test_choice_without_options_rejected():
    svc = UserInputService()
    with pytest.raises(ValueError):
        await svc.request_input(
            task_id="t-1",
            request_type=InputRequestType.CHOICE,
            prompt_text="Pick one",
        )


@pytest.mark.asyncio
async def test_answer_input_happy_path():
    svc = UserInputService()
    rid = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.TEXT,
        prompt_text="Name?",
    )
    req = await svc.answer_input(rid, response="Alice")
    assert req.status == InputRequestStatus.ANSWERED
    assert req.response == "Alice"
    assert req.answered_at is not None


@pytest.mark.asyncio
async def test_answer_invalid_choice_rejected():
    svc = UserInputService()
    rid = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.CHOICE,
        prompt_text="Pick",
        options=["a", "b"],
    )
    with pytest.raises(ValueError):
        await svc.answer_input(rid, response="c")


@pytest.mark.asyncio
async def test_cannot_answer_twice():
    svc = UserInputService()
    rid = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.TEXT,
        prompt_text="Name?",
    )
    await svc.answer_input(rid, response="first")
    with pytest.raises(ValueError):
        await svc.answer_input(rid, response="second")


@pytest.mark.asyncio
async def test_get_pending_filters_by_task():
    svc = UserInputService()
    r1 = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.TEXT,
        prompt_text="A",
    )
    await svc.request_input(
        task_id="t-2",
        request_type=InputRequestType.TEXT,
        prompt_text="B",
    )
    pending = await svc.get_pending_requests("t-1")
    assert len(pending) == 1
    assert pending[0].id == r1


@pytest.mark.asyncio
async def test_cancel_pending_marks_cancelled():
    svc = UserInputService()
    rid = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.TEXT,
        prompt_text="A",
    )
    req = await svc.cancel_request(rid)
    assert req.status == InputRequestStatus.CANCELLED


@pytest.mark.asyncio
async def test_cannot_cancel_answered():
    svc = UserInputService()
    rid = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.TEXT,
        prompt_text="A",
    )
    await svc.answer_input(rid, response="ok")
    with pytest.raises(ValueError):
        await svc.cancel_request(rid)


@pytest.mark.asyncio
async def test_expire_stale_flips_timed_out_requests():
    svc = UserInputService()
    rid = await svc.request_input(
        task_id="t-1",
        request_type=InputRequestType.TEXT,
        prompt_text="A",
        timeout_seconds=1,
    )
    # Back-date the created_at to force a timeout.
    svc._requests[rid].created_at = datetime.now(UTC) - timedelta(seconds=5)
    expired = await svc.expire_stale_requests()
    assert rid in expired
    assert svc.get_request(rid).status == InputRequestStatus.EXPIRED
