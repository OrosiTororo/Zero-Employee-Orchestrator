"""Tests for cross-version upgrade ladder (v0.1.x → latest)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.version_migration import (
    SCHEMA_VERSION_TABLE,
    current_schema_version,
    run_migrations,
)


@pytest.mark.asyncio
async def test_migrations_record_version_on_fresh_db() -> None:
    # Fresh in-memory DB — nothing recorded yet.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    # Register metadata so the step_* callbacks have something to create.
    import app.models as _models  # noqa: F401 — registers ORM models

    summary = await run_migrations(engine)

    assert "error" not in summary, f"migration hit an error: {summary.get('error')}"
    assert summary["steps_run"], "expected the ladder to run against a fresh DB"
    recorded = await current_schema_version(engine)
    assert recorded is not None
    # The bookmarking logic must always land on a real version string.
    assert recorded.count(".") == 2


@pytest.mark.asyncio
async def test_migrations_idempotent() -> None:
    """Running the ladder twice is a no-op the second time."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    import app.models as _models  # noqa: F401

    first = await run_migrations(engine)
    second = await run_migrations(engine)

    # Second pass either runs nothing or at most a final bookmark — no duplicate
    # step targets between the two runs.
    overlap = set(first.get("steps_run", [])) & set(second.get("steps_run", []))
    assert not overlap, f"migration step re-ran: {overlap}"


@pytest.mark.asyncio
async def test_schema_version_table_created() -> None:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    import app.models as _models  # noqa: F401

    assert await current_schema_version(engine) is None
    await run_migrations(engine)
    assert await current_schema_version(engine) is not None

    # Table name is stable — CLIs and external tooling rely on it.
    from sqlalchemy import text

    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
                {"n": SCHEMA_VERSION_TABLE},
            )
        ).fetchone()
        assert row is not None
