"""Batch self-improvement runner — APScheduler hook."""

from __future__ import annotations

import logging

from app.services.self_improvement.skill_analyzer import analyze_skill

logger = logging.getLogger(__name__)


async def run_improvement_cycle() -> None:
    """Periodic self-improvement cycle — runs every hour via APScheduler.

    Analyzes up to 5 enabled skills, logs findings, and records metrics.
    Designed to be lightweight and non-disruptive (max_instances=1 in scheduler).
    """
    import logging

    cycle_log = logging.getLogger(__name__)
    cycle_log.info("Self-improvement cycle started")
    try:
        from app.core.database import async_session_factory
        from app.models.skill import Skill

        async with async_session_factory() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Skill).where(Skill.enabled == True).limit(5)  # noqa: E712
            )
            skills = result.scalars().all()

        analyzed = 0
        for skill in skills:
            try:
                report = await analyze_skill(skill.slug)
                score = report.get("overall_score", 1.0)
                cycle_log.debug(
                    "Self-improvement: skill=%s score=%.2f findings=%d",
                    skill.slug,
                    score,
                    len(report.get("findings", [])),
                )
                analyzed += 1
            except Exception as exc:
                cycle_log.debug("Skill analysis failed for %s: %s", skill.slug, exc)

        cycle_log.info("Self-improvement cycle complete: %d skills analyzed", analyzed)
    except Exception as exc:
        cycle_log.warning("Self-improvement cycle error: %s", exc)
