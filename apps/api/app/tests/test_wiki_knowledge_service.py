"""Tests for the Karpathy-style wiki and arscontexta-style context engine.

These tests run offline — no LLM calls, no network — because both services
ship deterministic fallbacks. They exercise the core workflow a user would
hit through ``/ingest``, ``/query``, ``/lint``, and ``/ralph``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.context_engine_service import ContextEngineService
from app.services.wiki_knowledge_service import WikiKnowledgeService


@pytest.mark.asyncio
async def test_ingest_creates_pages_and_index(tmp_path: Path) -> None:
    service = WikiKnowledgeService(tmp_path / "vault")
    raw = (
        "# Harness Engineering\n\n"
        "The harness is the runtime around the model.\n\n"
        "# Plan Mode\n\n"
        "Claude Code enters plan mode before execution."
    )
    result = await service.ingest(source="doc.md", content=raw)

    assert "harness-engineering" in result.pages_created
    assert "plan-mode" in result.pages_created
    assert (tmp_path / "vault" / "wiki" / "harness-engineering.md").exists()
    index_text = (tmp_path / "vault" / "wiki" / "index.md").read_text(encoding="utf-8")
    assert "Harness Engineering" in index_text
    assert "Plan Mode" in index_text


@pytest.mark.asyncio
async def test_query_returns_citations_and_optionally_saves(tmp_path: Path) -> None:
    service = WikiKnowledgeService(tmp_path / "vault")
    await service.ingest(
        source="doc.md",
        content="# Context Engine\n\nA context engine feeds agents durable memory.",
    )

    # /query without --save
    answer = await service.query("context engine")
    assert "context-engine" in answer.citations
    assert answer.saved_page is None

    # /query --save
    saved = await service.query("context engine", save=True)
    assert saved.saved_page is not None
    assert (tmp_path / "vault" / "wiki" / f"{saved.saved_page}.md").exists()


@pytest.mark.asyncio
async def test_lint_detects_and_fixes_empty_pages(tmp_path: Path) -> None:
    service = WikiKnowledgeService(tmp_path / "vault")
    service.initialize()
    # Plant an empty page to trigger the lint rule.
    empty_path = tmp_path / "vault" / "wiki" / "ghost.md"
    empty_path.write_text("---\ntitle: Ghost\n---\n\n", encoding="utf-8")

    report = await service.lint(fix=False)
    assert "ghost" in report.empty_pages
    assert not report.ok

    report_fixed = await service.lint(fix=True)
    assert report_fixed.ok
    assert not empty_path.exists()


@pytest.mark.asyncio
async def test_ralph_pipeline_processes_inbox(tmp_path: Path) -> None:
    vault = tmp_path / "brain"
    service = ContextEngineService(vault)
    service.setup(language="en")
    (vault / "Inbox" / "note.md").write_text(
        "# Second Brain\n\nThe context engine beats RAG for small corpora.\n",
        encoding="utf-8",
    )

    report = await service.ralph()

    assert report.finished_at is not None
    assert "note.md" in report.recorded
    assert any("second-brain" in slug for slug in report.atoms_created)
    # The processed Inbox note should have been archived out of Inbox/.
    assert not (vault / "Inbox" / "note.md").exists()
    assert (vault / "ops" / "queue" / "note.md").exists()
    # The session report should have been written.
    assert Path(report.report_path).exists()


@pytest.mark.asyncio
async def test_setup_is_idempotent(tmp_path: Path) -> None:
    service = ContextEngineService(tmp_path / "brain")
    first = service.setup()
    second = service.setup()
    assert first == second
    for folder in ("self", "knowledge", "ops", "Inbox", "Context"):
        assert (tmp_path / "brain" / folder).is_dir()


@pytest.mark.asyncio
async def test_query_uses_llm_synthesis_when_opted_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``use_llm_synthesis=True`` routes the answer through the LLM gateway."""
    from app.providers import gateway as gateway_mod

    class _Resp:
        content = "Context engines beat RAG because [[context-engine]] is durable."

    calls: list[str] = []

    async def _fake_complete(req):
        # Verify the external wiki page content was wrapped before embedding.
        user_msg = next(m["content"] for m in req.messages if m["role"] == "user")
        assert "EXTERNAL_DATA_" in user_msg
        calls.append("called")
        return _Resp()

    monkeypatch.setattr(gateway_mod.llm_gateway, "complete", _fake_complete)

    service = WikiKnowledgeService(tmp_path / "vault", use_llm_synthesis=True)
    await service.ingest(
        source="doc.md",
        content="# Context Engine\n\nA context engine feeds agents durable memory.",
    )
    answer = await service.query("context engine")
    assert calls == ["called"]
    assert "llm-synthesised" in answer.answer
    assert "context-engine" in answer.citations


@pytest.mark.asyncio
async def test_query_falls_back_to_heuristic_on_llm_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the LLM gateway raises, /query still returns the deterministic answer."""
    from app.providers import gateway as gateway_mod

    async def _boom(req):
        raise RuntimeError("gateway unavailable")

    monkeypatch.setattr(gateway_mod.llm_gateway, "complete", _boom)

    service = WikiKnowledgeService(tmp_path / "vault", use_llm_synthesis=True)
    await service.ingest(
        source="doc.md",
        content="# Context Engine\n\nA context engine feeds agents durable memory.",
    )
    answer = await service.query("context engine")
    assert "wiki-synthesized" in answer.answer
    assert "context-engine" in answer.citations


@pytest.mark.asyncio
async def test_default_query_does_not_touch_llm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the default flag off, the gateway must never be called."""
    from app.providers import gateway as gateway_mod

    calls: list[str] = []

    async def _should_not_be_called(req):
        calls.append("called")
        raise AssertionError("LLM gateway must not be called with default config")

    monkeypatch.setattr(gateway_mod.llm_gateway, "complete", _should_not_be_called)

    service = WikiKnowledgeService(tmp_path / "vault")  # default: False
    await service.ingest(
        source="doc.md",
        content="# Context Engine\n\nA context engine feeds agents durable memory.",
    )
    await service.query("context engine")
    assert calls == []
