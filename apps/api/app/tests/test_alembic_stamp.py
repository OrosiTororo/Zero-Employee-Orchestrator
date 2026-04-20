"""Tests for the Alembic stamp behaviour in the version-migration ladder."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.version_migration import (
    ALEMBIC_HEAD_REVISION,
    _stamp_alembic_head,
    run_migrations,
)


@pytest.fixture
async def fresh_engine() -> AsyncEngine:
    # Each test gets its own in-memory DB so the ladder re-walks from 0.0.0.
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_stamp_writes_head_on_empty_table(fresh_engine: AsyncEngine):
    wrote = await _stamp_alembic_head(fresh_engine)
    assert wrote is True
    async with fresh_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).fetchall()
    assert [row[0] for row in rows] == [ALEMBIC_HEAD_REVISION]


@pytest.mark.asyncio
async def test_stamp_is_idempotent(fresh_engine: AsyncEngine):
    assert (await _stamp_alembic_head(fresh_engine)) is True
    # Re-running must not append a second row.
    assert (await _stamp_alembic_head(fresh_engine)) is False
    async with fresh_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).fetchall()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_stamp_respects_existing_pin(fresh_engine: AsyncEngine):
    async with fresh_engine.begin() as conn:
        await conn.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        )
        await conn.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('manual_pin_v999')")
        )

    wrote = await _stamp_alembic_head(fresh_engine)
    assert wrote is False
    async with fresh_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).fetchall()
    # Operator's explicit pin is preserved.
    assert [row[0] for row in rows] == ["manual_pin_v999"]


@pytest.mark.asyncio
async def test_run_migrations_stamps_alembic_on_fresh_install(fresh_engine: AsyncEngine):
    summary = await run_migrations(fresh_engine)
    assert summary.get("alembic_stamped") == ALEMBIC_HEAD_REVISION
    async with fresh_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).fetchall()
    assert [row[0] for row in rows] == [ALEMBIC_HEAD_REVISION]


@pytest.mark.asyncio
async def test_run_migrations_skips_stamp_when_already_set(fresh_engine: AsyncEngine):
    # First run stamps.
    await run_migrations(fresh_engine)
    # Second run on the same engine — stamp should no-op.
    summary = await run_migrations(fresh_engine)
    assert summary.get("alembic_stamped") is None
