"""Tests for the Alembic stamp behaviour in the version-migration ladder."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.version_migration import (
    _ALEMBIC_FALLBACK_REVISION,
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


# ---------------------------------------------------------------------------
# Dynamic Alembic head discovery
# ---------------------------------------------------------------------------


def test_head_is_discovered_from_versions_dir():
    """The module-level constant was computed from the Alembic scripts."""
    assert ALEMBIC_HEAD_REVISION
    assert ALEMBIC_HEAD_REVISION.startswith(("0", "1", "2"))


def test_fallback_used_when_versions_dir_missing(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """A module in a wheel without alembic/versions/ falls back to the pinned id."""
    import app.core.version_migration as vm

    class _FakePath:
        """Minimal Path-alike that reports nonexistent versions dir."""

        def __init__(self, *_args, **_kwargs):
            pass

        @property
        def parents(self):
            return [_FakePath(), _FakePath(), _FakePath()]

        def __truediv__(self, _other):
            return _FakePath()

        def is_dir(self):
            return False

        def resolve(self):
            return self

        def glob(self, _pattern):
            return []

    monkeypatch.setattr(vm, "__file__", "/nonexistent/version_migration.py")
    # Re-run discovery with a broken Path stand-in.
    monkeypatch.setattr("pathlib.Path", _FakePath)
    assert vm._discover_alembic_head() == _ALEMBIC_FALLBACK_REVISION


def test_discover_picks_single_head_from_chain(tmp_path, monkeypatch):
    """Given a three-script linear chain, discovery returns the tail."""
    import app.core.version_migration as vm

    versions = tmp_path / "alembic" / "versions"
    versions.mkdir(parents=True)
    (versions / "001.py").write_text('revision = "001"\ndown_revision = None\n', encoding="utf-8")
    (versions / "002.py").write_text('revision = "002"\ndown_revision = "001"\n', encoding="utf-8")
    (versions / "003.py").write_text('revision = "003"\ndown_revision = "002"\n', encoding="utf-8")

    # Point the module-file lookup at our fake layout by monkeypatching __file__.
    fake_module = tmp_path / "apps" / "api" / "app" / "core" / "version_migration.py"
    fake_module.parent.mkdir(parents=True)
    # Move versions into the expected relative location.
    import shutil

    dest = tmp_path / "apps" / "api" / "alembic" / "versions"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(versions, dest)

    monkeypatch.setattr(vm, "__file__", str(fake_module))
    assert vm._discover_alembic_head() == "003"
