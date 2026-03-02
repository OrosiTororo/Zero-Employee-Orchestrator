"""State Machine テスト"""

import pytest

from app.state.machine import init_db, create_task, get_task, transition_task, list_tasks


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    db_path = str(tmp_path / "test_tasks.db")
    await init_db(db_path)


@pytest.mark.asyncio
async def test_create_and_get():
    task = await create_task("test-skill", {"key": "value"})
    assert task.state == "draft"
    assert task.skill_name == "test-skill"

    loaded = await get_task(task.id)
    assert loaded is not None
    assert loaded.id == task.id


@pytest.mark.asyncio
async def test_transitions():
    task = await create_task("test-skill", {})
    assert task.state == "draft"

    task = await transition_task(task.id, "start_execution")
    assert task.state == "ai_executing"

    task = await transition_task(task.id, "complete_execution")
    assert task.state == "ai_completed"


@pytest.mark.asyncio
async def test_list_tasks():
    await create_task("skill-a", {})
    await create_task("skill-b", {})
    tasks = await list_tasks()
    assert len(tasks) >= 2
