"""Tests for context_engine_service (arscontexta-style vault)."""

from __future__ import annotations

import pytest

from app.security.sandbox import filesystem_sandbox
from app.services.context_engine_service import ContextEngineService


@pytest.fixture
def vault(tmp_path):
    # Whitelist the tmp vault so the service can write without sandbox denial.
    filesystem_sandbox.add_allowed_path(str(tmp_path))
    yield tmp_path
    filesystem_sandbox.remove_allowed_path(str(tmp_path))


def test_setup_creates_expected_folders(vault):
    svc = ContextEngineService(vault)
    result = svc.setup(language="en")
    assert result["created"] is True
    for sub in ("self", "knowledge", "ops", "Inbox", "Projects", "Ideas", "Resources", "Context"):
        assert (vault / sub).is_dir()


def test_setup_is_idempotent(vault):
    svc = ContextEngineService(vault)
    svc.setup()
    svc.setup()  # second call must not raise
    assert (vault / "knowledge" / "index.md").is_file()


@pytest.mark.asyncio
async def test_ralph_ingests_inbox_note(vault):
    svc = ContextEngineService(vault)
    svc.setup()
    inbox_note = vault / "Inbox" / "hello.md"
    inbox_note.write_text("# First\n\nWelcome to ZEO.\n\n# Second\n\nAtoms everywhere.", encoding="utf-8")

    report = await svc.ralph()
    assert "hello.md" in report.recorded
    assert len(report.atoms_created) >= 1
    assert report.finished_at is not None

    atoms_dir = vault / "knowledge" / "atoms"
    assert any(atoms_dir.glob("*.md"))


@pytest.mark.asyncio
async def test_ralph_without_inbox_returns_empty_report(vault):
    svc = ContextEngineService(vault)
    svc.setup()
    report = await svc.ralph()
    assert report.recorded == []
    assert report.atoms_created == []
    assert report.finished_at is not None


@pytest.mark.asyncio
async def test_ralph_writes_session_report(vault):
    svc = ContextEngineService(vault)
    svc.setup()
    report = await svc.ralph()
    assert report.report_path
    assert (vault / "ops" / "sessions").is_dir()
