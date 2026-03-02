"""Experience Memory テスト"""

import pytest

from app.state.experience import (
    init_experience_db,
    ExperienceCard,
    save_experience,
    get_relevant_experiences,
)


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    await init_experience_db(str(tmp_path / "test_exp.db"))


@pytest.mark.asyncio
async def test_save_and_query():
    card = ExperienceCard(
        task_type="analysis",
        success_factors=["fast execution"],
        model_used="fast",
        score=0.95,
        context="File analysis completed successfully",
    )
    await save_experience(card)

    results = await get_relevant_experiences("analysis")
    assert len(results) >= 1
    assert results[0].model_used == "fast"
    assert results[0].score == 0.95


@pytest.mark.asyncio
async def test_ordering():
    for i, score in enumerate([0.5, 0.9, 0.7]):
        card = ExperienceCard(
            task_type="ordered",
            success_factors=[f"factor-{i}"],
            model_used=f"model-{i}",
            score=score,
            context=f"Test {i}",
        )
        await save_experience(card)

    results = await get_relevant_experiences("ordered")
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
