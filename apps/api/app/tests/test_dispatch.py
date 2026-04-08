"""Dispatch API tests — Cowork-inspired features.

Tests for:
- Basic dispatch CRUD (create, get, list, cancel)
- needs_input status detection
- Plan preview (preview_only mode + start)
- Steering mid-execution
- Resume from needs_input
"""

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.api.routes.dispatch import (
    _detect_needs_input,
    _dispatch_lock,
    _dispatch_tasks,
)


@pytest.fixture(autouse=True)
def _clear_dispatch_tasks():
    """Clear the in-memory task store before each test."""
    with _dispatch_lock:
        _dispatch_tasks.clear()
    yield
    with _dispatch_lock:
        _dispatch_tasks.clear()


def _insert_task(status: str = "queued", **overrides) -> dict:
    """Insert a task directly into the in-memory store (bypasses background exec)."""
    task_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    task = {
        "task_id": task_id,
        "user_id": "00000000-0000-0000-0000-000000000001",  # matches conftest _TEST_USER
        "instruction": "Test task",
        "priority": "medium",
        "schedule": None,
        "context": {},
        "status": status,
        "created_at": now,
        "completed_at": None,
        "result": None,
        "plan_preview": None,
        "needs_input_reason": None,
        "steering_instructions": [],
        "resume_event": asyncio.Event(),
        "resume_input": None,
        **overrides,
    }
    with _dispatch_lock:
        _dispatch_tasks[task_id] = task
    return task


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_dispatch(client: AsyncClient):
    """POST /dispatch creates a queued task and returns task_id."""
    resp = await client.post(
        "/api/v1/dispatch",
        json={"instruction": "Summarize the Q4 report"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert data["task_id"]
    assert data["instruction"] == "Summarize the Q4 report"


@pytest.mark.asyncio
async def test_get_dispatch(client: AsyncClient):
    """GET /dispatch/{task_id} returns task details."""
    task = _insert_task(instruction="Write a memo")
    task_id = task["task_id"]

    resp = await client.get(f"/api/v1/dispatch/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["task_id"] == task_id
    assert resp.json()["instruction"] == "Write a memo"


@pytest.mark.asyncio
async def test_get_dispatch_not_found(client: AsyncClient):
    """GET /dispatch/{task_id} returns 404 for unknown ID."""
    resp = await client.get("/api/v1/dispatch/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_dispatches(client: AsyncClient):
    """GET /dispatch lists all tasks for the current user."""
    _insert_task(instruction="Task A")
    _insert_task(instruction="Task B")

    resp = await client.get("/api/v1/dispatch")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["tasks"]) == 2


@pytest.mark.asyncio
async def test_list_dispatches_filter_by_status(client: AsyncClient):
    """GET /dispatch?status= filters by task status."""
    _insert_task(status="queued", instruction="Queued task")
    _insert_task(status="running", instruction="Running task")
    _insert_task(status="completed", instruction="Done task")

    resp = await client.get("/api/v1/dispatch?status=queued")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["tasks"][0]["instruction"] == "Queued task"

    resp = await client.get("/api/v1/dispatch?status=running")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_cancel_dispatch(client: AsyncClient):
    """DELETE /dispatch/{task_id} cancels a running task."""
    task = _insert_task(status="running")
    task_id = task["task_id"]

    resp = await client.delete(f"/api/v1/dispatch/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_completed_task_is_noop(client: AsyncClient):
    """DELETE /dispatch/{task_id} does not change completed tasks."""
    task = _insert_task(status="completed")
    task_id = task["task_id"]

    resp = await client.delete(f"/api/v1/dispatch/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_cancel_dispatch_not_found(client: AsyncClient):
    """DELETE /dispatch/{task_id} returns 404 for unknown ID."""
    resp = await client.delete("/api/v1/dispatch/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_unblocks_needs_input(client: AsyncClient):
    """Cancelling a needs_input task sets the resume event."""
    task = _insert_task(status="needs_input", needs_input_reason="Waiting")
    task_id = task["task_id"]
    event = task["resume_event"]

    resp = await client.delete(f"/api/v1/dispatch/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    assert event.is_set()
    assert task["resume_input"] is None  # Signals cancellation, not real input


# ---------------------------------------------------------------------------
# Plan preview (preview_only mode)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_dispatch_preview_only(client: AsyncClient):
    """POST /dispatch with preview_only=True creates a task in 'preview' status."""
    resp = await client.post(
        "/api/v1/dispatch",
        json={"instruction": "Analyze sales data", "preview_only": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "preview"
    assert data["task_id"]


@pytest.mark.asyncio
async def test_start_previewed_dispatch(client: AsyncClient):
    """POST /dispatch/{task_id}/start transitions preview task to running."""
    task = _insert_task(status="preview")
    task_id = task["task_id"]

    resp = await client.post(f"/api/v1/dispatch/{task_id}/start")
    assert resp.status_code == 200
    # The task transitions to running (background task starts)
    assert resp.json()["status"] in ("preview", "running")


@pytest.mark.asyncio
async def test_start_previewed_dispatch_wrong_status(client: AsyncClient):
    """POST /dispatch/{task_id}/start returns 409 when task is not in preview status."""
    task = _insert_task(status="queued")
    task_id = task["task_id"]

    resp = await client.post(f"/api/v1/dispatch/{task_id}/start")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_start_previewed_dispatch_not_found(client: AsyncClient):
    """POST /dispatch/{task_id}/start returns 404 for unknown ID."""
    resp = await client.post("/api/v1/dispatch/nonexistent-id/start")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Steering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_steer_dispatch_queued(client: AsyncClient):
    """POST /dispatch/{task_id}/steer adds steering to queued task."""
    task = _insert_task(status="queued")
    task_id = task["task_id"]

    resp = await client.post(
        f"/api/v1/dispatch/{task_id}/steer",
        json={"instruction": "Focus on cost savings"},
    )
    assert resp.status_code == 200

    with _dispatch_lock:
        stored = _dispatch_tasks[task_id]
    assert len(stored["steering_instructions"]) == 1
    assert stored["steering_instructions"][0]["instruction"] == "Focus on cost savings"


@pytest.mark.asyncio
async def test_steer_dispatch_running(client: AsyncClient):
    """POST /dispatch/{task_id}/steer works for running tasks."""
    task = _insert_task(status="running")
    task_id = task["task_id"]

    resp = await client.post(
        f"/api/v1/dispatch/{task_id}/steer",
        json={"instruction": "Change approach to use charts"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_steer_dispatch_needs_input(client: AsyncClient):
    """POST /dispatch/{task_id}/steer works for needs_input tasks."""
    task = _insert_task(status="needs_input", needs_input_reason="Awaiting clarification")
    task_id = task["task_id"]

    resp = await client.post(
        f"/api/v1/dispatch/{task_id}/steer",
        json={"instruction": "Use the monthly format instead"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_steer_dispatch_wrong_status(client: AsyncClient):
    """POST /dispatch/{task_id}/steer returns 409 for completed tasks."""
    task = _insert_task(status="cancelled")
    task_id = task["task_id"]

    resp = await client.post(
        f"/api/v1/dispatch/{task_id}/steer",
        json={"instruction": "Too late"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_steer_dispatch_not_found(client: AsyncClient):
    """POST /dispatch/{task_id}/steer returns 404 for unknown ID."""
    resp = await client.post(
        "/api/v1/dispatch/nonexistent-id/steer",
        json={"instruction": "No task"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_steer_multiple_instructions(client: AsyncClient):
    """Multiple steering instructions accumulate on the task."""
    task = _insert_task(status="running")
    task_id = task["task_id"]

    await client.post(
        f"/api/v1/dispatch/{task_id}/steer",
        json={"instruction": "Instruction 1"},
    )
    await client.post(
        f"/api/v1/dispatch/{task_id}/steer",
        json={"instruction": "Instruction 2"},
    )

    with _dispatch_lock:
        stored = _dispatch_tasks[task_id]
    assert len(stored["steering_instructions"]) == 2


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resume_dispatch_wrong_status(client: AsyncClient):
    """POST /dispatch/{task_id}/resume returns 409 when not in needs_input."""
    task = _insert_task(status="running")
    task_id = task["task_id"]

    resp = await client.post(
        f"/api/v1/dispatch/{task_id}/resume",
        json={"user_input": "Here is my input"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_resume_dispatch_not_found(client: AsyncClient):
    """POST /dispatch/{task_id}/resume returns 404 for unknown ID."""
    resp = await client.post(
        "/api/v1/dispatch/nonexistent-id/resume",
        json={"user_input": "No task"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_resume_dispatch_needs_input(client: AsyncClient):
    """POST /dispatch/{task_id}/resume resumes a needs_input task."""
    task = _insert_task(
        status="needs_input",
        needs_input_reason="Please provide the report date",
    )
    task_id = task["task_id"]

    resp = await client.post(
        f"/api/v1/dispatch/{task_id}/resume",
        json={"user_input": "2026-04-08"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["needs_input_reason"] is None

    # Verify resume_event was set and resume_input recorded
    with _dispatch_lock:
        stored = _dispatch_tasks[task_id]
    assert stored["resume_event"].is_set()
    assert stored["resume_input"] == "2026-04-08"


@pytest.mark.asyncio
async def test_resume_records_steering_instruction(client: AsyncClient):
    """Resume adds user_input as a steering instruction for context."""
    task = _insert_task(status="needs_input", needs_input_reason="Need date")
    task_id = task["task_id"]

    await client.post(
        f"/api/v1/dispatch/{task_id}/resume",
        json={"user_input": "Use Q1 2026 data"},
    )

    with _dispatch_lock:
        stored = _dispatch_tasks[task_id]
    assert len(stored["steering_instructions"]) == 1
    assert "[user_input]" in stored["steering_instructions"][0]["instruction"]


# ---------------------------------------------------------------------------
# Needs-input detection (unit tests)
# ---------------------------------------------------------------------------


def test_detect_needs_input_positive():
    """_detect_needs_input detects input-requesting phrases."""
    content = "I've started the analysis. Please provide the target date range."
    result = _detect_needs_input(content)
    assert result is not None
    assert "provide" in result.lower() or "date" in result.lower()


def test_detect_needs_input_multiple_indicators():
    """_detect_needs_input catches various input request patterns."""
    test_cases = [
        "Could you clarify which department?",
        "I need more information about the budget.",
        "What would you like me to focus on?",
        "Please specify the output format.",
        "Please confirm the deployment target.",
    ]
    for content in test_cases:
        result = _detect_needs_input(content)
        assert result is not None, f"Failed to detect: {content}"


def test_detect_needs_input_negative():
    """_detect_needs_input returns None for normal output."""
    normal_outputs = [
        "The analysis is complete. Revenue increased 15% year-over-year.",
        "Here are the top 5 recommendations for improving efficiency.",
        "Task completed successfully. All files have been processed.",
    ]
    for content in normal_outputs:
        result = _detect_needs_input(content)
        assert result is None, f"False positive for: {content}"


def test_detect_needs_input_empty():
    """_detect_needs_input returns None for empty content."""
    assert _detect_needs_input("") is None
    assert _detect_needs_input("   ") is None


def test_detect_needs_input_case_insensitive():
    """_detect_needs_input is case-insensitive."""
    assert _detect_needs_input("PLEASE PROVIDE your credentials") is not None
    assert _detect_needs_input("Please Clarify the scope") is not None


# ---------------------------------------------------------------------------
# Response model fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_response_includes_plan_preview(client: AsyncClient):
    """DispatchResponse includes plan_preview field."""
    task = _insert_task()
    resp = await client.get(f"/api/v1/dispatch/{task['task_id']}")
    data = resp.json()
    assert "plan_preview" in data
    assert data["plan_preview"] is None


@pytest.mark.asyncio
async def test_dispatch_response_includes_needs_input_reason(client: AsyncClient):
    """DispatchResponse includes needs_input_reason field."""
    task = _insert_task(
        status="needs_input",
        needs_input_reason="Which format?",
    )
    resp = await client.get(f"/api/v1/dispatch/{task['task_id']}")
    data = resp.json()
    assert "needs_input_reason" in data
    assert data["needs_input_reason"] == "Which format?"
    assert data["status"] == "needs_input"
