"""Artifact Bridge テスト"""

import pytest

from app.state.artifact_bridge import (
    init_artifact_db,
    ArtifactSlot,
    save_artifact,
    find_relevant_artifacts,
)


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    await init_artifact_db(str(tmp_path / "test_artifacts.db"))


@pytest.mark.asyncio
async def test_save_and_retrieve():
    artifact = ArtifactSlot(
        slot_type="insight",
        content="Market analysis shows growth trend",
        tags=["market", "analysis"],
        source_task_id="task-001",
    )
    await save_artifact(artifact)

    results = await find_relevant_artifacts(["market"])
    assert len(results) >= 1
    assert "growth trend" in results[0].content


@pytest.mark.asyncio
async def test_multiple_tags():
    artifact = ArtifactSlot(
        slot_type="data",
        content='{"views": 1000}',
        tags=["youtube", "metrics", "performance"],
        source_task_id="task-002",
    )
    await save_artifact(artifact)

    for tag in ["youtube", "metrics", "performance"]:
        results = await find_relevant_artifacts([tag])
        assert len(results) >= 1
