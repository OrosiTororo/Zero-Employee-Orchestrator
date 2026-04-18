"""Cross-version upgrade helper for old ZEO installs.

Users that installed early builds (``v0.1.0``, ``v0.1.1``, ``v0.1.2``, …)
don't have Alembic migrations, so when they run ``zero-employee update``
the schema silently drifts. This module fills that gap with a small,
hand-written migration ladder that the ``update`` and ``db upgrade``
commands call before the app boots.

Design choices
--------------

* **Additive-only** — every step adds columns / tables with ``IF NOT
  EXISTS`` semantics. Nothing is dropped, so a failed step never loses
  data; we roll forward instead of rolling back.
* **Idempotent** — each step checks its own preconditions and no-ops if
  they are already satisfied, so re-running the CLI is safe.
* **Explicit version ladder** — `_STEPS` is an ordered list of
  ``(from_version, target_version, fn)`` triples. Users on ``v0.1.0``
  walk the entire ladder in one command; users on ``v0.1.5`` only run
  the tail.
* **Outside the request path** — this is called from the CLI, not from
  route handlers, so it can block on slow DDL without tripping the
  rate limiter.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from packaging.version import InvalidVersion, Version
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

SCHEMA_VERSION_TABLE = "zeo_schema_version"


@dataclass
class MigrationStep:
    """A single step on the upgrade ladder."""

    from_version: str  # exclusive lower bound — run if installed > from_version
    target_version: str  # this step upgrades the DB to this version
    description: str
    run: Callable[[AsyncEngine], Awaitable[None]]


async def _ensure_schema_version_table(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                f"CREATE TABLE IF NOT EXISTS {SCHEMA_VERSION_TABLE} ("
                "  version VARCHAR(32) PRIMARY KEY,"
                "  applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                "  note VARCHAR(255)"
                ")"
            )
        )


async def _get_recorded_version(engine: AsyncEngine) -> str | None:
    """Return the semver-highest recorded version.

    Ordering by ``applied_at`` alone is not enough — multiple inserts in a
    single migration run can share a timestamp and then SQLite returns them
    in an undefined order. We pull every row and pick the semver-max so
    the ladder is stable even on fast hardware.
    """
    async with engine.begin() as conn:
        result = await conn.execute(text(f"SELECT version FROM {SCHEMA_VERSION_TABLE}"))
        rows = [row[0] for row in result.fetchall() if row and row[0]]
    if not rows:
        return None
    best: str | None = None
    best_v: Version | None = None
    for v in rows:
        try:
            parsed = Version(v)
        except InvalidVersion:
            continue
        if best_v is None or parsed > best_v:
            best = v
            best_v = parsed
    return best or rows[-1]


async def _record_version(engine: AsyncEngine, version: str, note: str = "") -> None:
    # ON CONFLICT DO NOTHING — re-running the ladder with an already-recorded
    # bookmark is not an error. We rely on explicit existence check first
    # because SQLite < 3.24, PostgreSQL, and MySQL need different syntax.
    async with engine.begin() as conn:
        exists = await conn.execute(
            text(f"SELECT 1 FROM {SCHEMA_VERSION_TABLE} WHERE version = :v"),
            {"v": version},
        )
        if exists.fetchone() is not None:
            return
        await conn.execute(
            text(f"INSERT INTO {SCHEMA_VERSION_TABLE} (version, note) VALUES (:v, :n)"),
            {"v": version, "n": note[:255]},
        )


# ---------------------------------------------------------------------------
# Individual step implementations
# ---------------------------------------------------------------------------


async def _step_0_1_0_to_0_1_3(engine: AsyncEngine) -> None:
    """v0.1.0 → v0.1.3 — add knowledge_store and approval tracking columns.

    Pre-v0.1.3 installs only had tickets / companies / users. Newer code
    paths expect the knowledge_store, approval_request, and audit tables.
    SQLAlchemy's ``create_all`` covers the happy path; this step exists to
    make absolutely sure old DBs gain these tables before the app tries
    to write to them.
    """
    # create_all() on the metadata covers us — import app.models so every
    # Base subclass (including orchestration/service tables) is attached first.
    import app.models  # noqa: F401
    from app.core.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _step_0_1_3_to_0_1_5(engine: AsyncEngine) -> None:
    """v0.1.3 → v0.1.5 — widen operator profile columns + add dispatch fields.

    Older users hit ``IntegrityError`` when their operator profile ``role``
    exceeded the original VARCHAR(64). We widen to VARCHAR(255) where the
    backing store supports it; otherwise we no-op (SQLite ignores length).
    """
    async with engine.begin() as conn:
        dialect = engine.dialect.name
        if dialect == "postgresql":
            await conn.execute(
                text("ALTER TABLE IF EXISTS operator_profiles ALTER COLUMN role TYPE VARCHAR(255)")
            )
        elif dialect == "mysql":
            await conn.execute(text("ALTER TABLE operator_profiles MODIFY role VARCHAR(255)"))
        # SQLite: VARCHAR length is advisory, nothing to do.


async def _step_0_1_5_to_0_1_6(engine: AsyncEngine) -> None:
    """v0.1.5 → v0.1.6 — register the MCP tool-registration table.

    The MCP JSON-RPC server added in v0.1.6 persists tool annotations so
    clients can resume mid-session. Install the table via metadata.
    """
    import app.models  # noqa: F401 — populate Base.metadata with every ORM class
    from app.core.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _step_0_1_6_to_0_1_7(engine: AsyncEngine) -> None:
    """v0.1.6 → v0.1.7 — install orchestration / service tables.

    v0.1.7 introduced ORM tables declared outside ``app/models/`` (knowledge
    store, experience memory, agent sessions, multi-model comparisons,
    secretary summaries, etc.). Importing ``app.models`` runs the side-effect
    imports that register every Base subclass, so ``create_all`` picks them up.
    """
    import app.models  # noqa: F401
    from app.core.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------------------------------------------------------------------
# Ladder
# ---------------------------------------------------------------------------


_STEPS: list[MigrationStep] = [
    MigrationStep(
        from_version="0.0.0",
        target_version="0.1.3",
        description="Pre-v0.1.3 → v0.1.3 (knowledge store, approvals, audit)",
        run=_step_0_1_0_to_0_1_3,
    ),
    MigrationStep(
        from_version="0.1.3",
        target_version="0.1.5",
        description="v0.1.3 → v0.1.5 (widen operator profile, dispatch fields)",
        run=_step_0_1_3_to_0_1_5,
    ),
    MigrationStep(
        from_version="0.1.5",
        target_version="0.1.6",
        description="v0.1.5 → v0.1.6 (MCP tool-registration table)",
        run=_step_0_1_5_to_0_1_6,
    ),
    MigrationStep(
        from_version="0.1.6",
        target_version="0.1.7",
        description="v0.1.6 → v0.1.7 (wiki / context-engine scaffolding)",
        run=_step_0_1_6_to_0_1_7,
    ),
]


def _needs_run(recorded: str | None, step: MigrationStep) -> bool:
    """Decide whether ``step`` applies given the recorded schema version."""
    try:
        current = Version(recorded) if recorded else Version("0.0.0")
        target = Version(step.target_version)
    except InvalidVersion:
        logger.warning("Invalid version encountered; running step defensively")
        return True
    return current < target


async def run_migrations(engine: AsyncEngine) -> dict[str, Any]:
    """Walk every pending migration step. Returns a structured summary.

    Safe to call on a fresh install — the schema-version table will be
    empty, every step runs once, and the recorded version advances to
    the current app version.
    """
    from app.core.version_check import get_current_version

    await _ensure_schema_version_table(engine)
    recorded = await _get_recorded_version(engine)

    summary: dict[str, Any] = {
        "from": recorded or "unrecorded",
        "steps_run": [],
        "skipped": [],
        "to": recorded,
    }

    for step in _STEPS:
        if not _needs_run(recorded, step):
            summary["skipped"].append(step.target_version)
            continue
        logger.info("Applying migration %s", step.description)
        try:
            await step.run(engine)
        except Exception as exc:  # pragma: no cover — surfaced to operator
            logger.exception("Migration %s failed: %s", step.target_version, exc)
            summary["error"] = f"{step.target_version}: {exc}"
            return summary
        await _record_version(engine, step.target_version, note=step.description)
        summary["steps_run"].append(step.target_version)
        recorded = step.target_version

    # Final bookmark — make sure the latest app version is recorded even if
    # no step moved the needle.
    current = get_current_version()
    if recorded != current:
        try:
            if not recorded or Version(recorded) < Version(current):
                await _record_version(engine, current, note="final-bookmark")
                recorded = current
        except InvalidVersion:
            pass

    summary["to"] = recorded
    return summary


async def current_schema_version(engine: AsyncEngine) -> str | None:
    """Return the latest recorded schema version, or ``None`` if unknown."""
    await _ensure_schema_version_table(engine)
    return await _get_recorded_version(engine)
