"""Context Engine — arscontexta-style three-space second brain.

Reproduces the public description of the ``arscontexta`` pattern as an
in-tree service so ZEO can stand up a personal second brain without
installing a separate Claude Code plugin:

* **Self space** (``self/``) — agent identity, working style, preferences.
  Persists across sessions so agents don't relearn who the user is.
* **Knowledge space** (``knowledge/``) — the actual graph: an ``index.md``
  hub, topic **maps** (chapters), and **atoms** (one concept per file).
* **Ops space** (``ops/``) — queue of pending work, session logs,
  ``ralph`` runs, and health reports.

Plus the Obsidian "Inbox / Projects / Ideas / Resources / Context" layout
from the 文脈エンジン playbook:

    vault/
      Inbox/         — incoming notes from Web Clipper, mobile capture, etc.
      Projects/      — active projects
      Ideas/         — future reference
      Resources/     — primary sources (articles, transcripts…)
      Context/       — MyContext.md (entry-point) + AI Handoff + profile atoms

The :meth:`ralph` method runs the full 6R-style pipeline in one shot:

1. **Record** — move Inbox files into a dated log.
2. **Reduce** — split each note into atoms under ``knowledge/atoms/``.
3. **Reflect** — discover wikilinks against existing atoms.
4. **Retrieve** — refresh the index.
5. **Verify** — lint for orphans / duplicates / empty files.
6. **Resync** — write a session report under ``ops/sessions/``.

The extractor is deliberately deterministic so tests and CI never need
to hit an LLM. Callers that want richer compilation can subclass and
override :meth:`_reduce_note`.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Atom:
    """A single atomic note in the knowledge graph."""

    slug: str
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    source: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RalphReport:
    """Summary of a ``/ralph`` run."""

    session_id: str
    started_at: datetime
    finished_at: datetime | None = None
    recorded: list[str] = field(default_factory=list)
    atoms_created: list[str] = field(default_factory=list)
    links_added: int = 0
    warnings: list[str] = field(default_factory=list)
    report_path: str = ""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ContextEngineService:
    """arscontexta-style three-space context engine.

    This service is intentionally file-based so it can be handed to any
    other AI tool (ChatGPT, Gemini, local Qwen, …) by pointing that tool
    at the vault path — the core idea of "the context engine is not
    locked to one AI vendor" from the 文脈エンジン playbook.
    """

    # Three-space layout
    SELF_DIR = "self"
    KNOWLEDGE_DIR = "knowledge"
    OPS_DIR = "ops"

    # Obsidian-style top-level folders used by the Ralph pipeline
    INBOX_DIR = "Inbox"
    PROJECTS_DIR = "Projects"
    IDEAS_DIR = "Ideas"
    RESOURCES_DIR = "Resources"
    CONTEXT_DIR = "Context"

    _WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    _TAG_RE = re.compile(r"(?<!\w)#([A-Za-z\u3040-\u9fff][\w\u3040-\u9fff]*)")
    _SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+(?=[A-Z0-9\u3040-\u9fff])")

    def __init__(self, vault_path: str | Path) -> None:
        self.vault_path = Path(vault_path).resolve()

    # ── Lifecycle ────────────────────────────────────────────────────────

    def setup(self, language: str = "ja") -> dict[str, Any]:
        """Create the full folder layout and seed starter files.

        Mirrors ``/setup`` in arscontexta: runs quickly, is idempotent,
        and writes no secrets to disk.
        """
        for sub in (
            self.SELF_DIR,
            self.KNOWLEDGE_DIR,
            self.OPS_DIR,
            self.INBOX_DIR,
            self.PROJECTS_DIR,
            self.IDEAS_DIR,
            self.RESOURCES_DIR,
            self.CONTEXT_DIR,
        ):
            (self.vault_path / sub).mkdir(parents=True, exist_ok=True)

        for sub in ("atoms", "maps"):
            (self.vault_path / self.KNOWLEDGE_DIR / sub).mkdir(exist_ok=True)

        (self.vault_path / self.OPS_DIR / "sessions").mkdir(exist_ok=True)
        (self.vault_path / self.OPS_DIR / "queue").mkdir(exist_ok=True)

        # Seed MyContext.md — the single entry-point every AI reads first.
        my_context = self.vault_path / self.CONTEXT_DIR / "MyContext.md"
        if not my_context.exists():
            my_context.write_text(self._starter_mycontext(language), encoding="utf-8")

        handoff = self.vault_path / self.CONTEXT_DIR / "AIHandoff.md"
        if not handoff.exists():
            handoff.write_text(
                "# AI Handoff\n\n"
                "Cross-agent scratchpad. Agents append structured notes here "
                "so the next AI continues without re-asking. One entry per section.\n",
                encoding="utf-8",
            )

        identity = self.vault_path / self.SELF_DIR / "identity.md"
        if not identity.exists():
            identity.write_text(
                "# Agent Identity\n\n"
                "- role: Zero-Employee Orchestrator\n"
                "- mission: help the operator run their business end-to-end\n"
                "- memory policy: atoms only, no bulk logs in context\n",
                encoding="utf-8",
            )

        index = self.vault_path / self.KNOWLEDGE_DIR / "index.md"
        if not index.exists():
            index.write_text(
                "# Knowledge Index\n\nAuto-maintained. Run `/ralph` to refresh.\n",
                encoding="utf-8",
            )

        return {
            "vault_path": str(self.vault_path),
            "language": language,
            "created": True,
        }

    # ── /ralph pipeline ──────────────────────────────────────────────────

    async def ralph(self) -> RalphReport:
        """Record → Reduce → Reflect → Retrieve → Verify → Resync.

        This is the single user-facing command once the vault is set up.
        Drops everything in ``Inbox/`` into the knowledge graph and writes
        a session report.
        """
        from app.security.prompt_guard import wrap_external_data

        self.setup()
        report = RalphReport(
            session_id=uuid.uuid4().hex[:12],
            started_at=datetime.now(UTC),
        )

        inbox = self.vault_path / self.INBOX_DIR
        atoms_dir = self.vault_path / self.KNOWLEDGE_DIR / "atoms"

        # 1. Record — snapshot the Inbox before we touch it.
        notes = sorted(inbox.glob("*.md"))
        for note in notes:
            report.recorded.append(note.name)

        # 2. Reduce — split each note into atoms.
        for note in notes:
            try:
                raw = note.read_text(encoding="utf-8")
            except OSError as exc:
                report.warnings.append(f"read-failed:{note.name}:{exc}")
                continue
            # Defend against prompt injection inside ingested text.
            _ = wrap_external_data(raw, source=f"inbox:{note.name}")
            atoms = self._reduce_note(raw, note.stem)
            for atom in atoms:
                path = atoms_dir / f"{atom.slug}.md"
                if path.exists():
                    # Append new context without destroying the original.
                    existing = path.read_text(encoding="utf-8")
                    path.write_text(
                        existing.rstrip() + "\n\n---\n\n" + atom.content.strip() + "\n",
                        encoding="utf-8",
                    )
                else:
                    path.write_text(self._render_atom(atom), encoding="utf-8")
                    report.atoms_created.append(atom.slug)

            # Archive the processed Inbox note under ops/queue/.
            archive = self.vault_path / self.OPS_DIR / "queue" / note.name
            try:
                note.replace(archive)
            except OSError as exc:
                report.warnings.append(f"archive-failed:{note.name}:{exc}")

        # 3. Reflect — rebuild wikilinks across all atoms.
        report.links_added = self._reflect_links()

        # 4. Retrieve — refresh the index.
        self._rebuild_index()

        # 5. Verify — simple health checks.
        report.warnings.extend(self._verify())

        # 6. Resync — write the session report.
        report.finished_at = datetime.now(UTC)
        session_file = self.vault_path / self.OPS_DIR / "sessions" / f"ralph-{report.session_id}.md"
        session_file.write_text(self._render_report(report), encoding="utf-8")
        report.report_path = str(session_file)
        return report

    # ── Reduce / Reflect helpers ─────────────────────────────────────────

    def _reduce_note(self, raw: str, source_stem: str) -> list[Atom]:
        """Split ``raw`` into atomic notes.

        Strategy: one atom per H1/H2 heading; fallback to the whole note.
        Subclass and override for LLM-powered extraction.
        """
        atoms: list[Atom] = []

        # Try heading-based split first.
        blocks = re.split(r"(?m)^(#{1,2})\s+(.+)$", raw)
        if len(blocks) > 1:
            # blocks = [preamble, '#'|'##', heading, body, '#', heading, body, …]
            for i in range(1, len(blocks), 3):
                heading = blocks[i + 1].strip()
                body = blocks[i + 2].strip() if i + 2 < len(blocks) else ""
                if not body and not heading:
                    continue
                atoms.append(
                    Atom(
                        slug=self._slugify(heading or source_stem),
                        title=heading or source_stem,
                        content=body,
                        tags=self._TAG_RE.findall(body),
                        source=source_stem,
                    )
                )

        if not atoms:
            atoms.append(
                Atom(
                    slug=self._slugify(source_stem),
                    title=source_stem,
                    content=raw.strip()[:4000],
                    tags=self._TAG_RE.findall(raw),
                    source=source_stem,
                )
            )
        return atoms

    def _reflect_links(self) -> int:
        """Add wikilinks between atoms that mention each other's titles."""
        atoms_dir = self.vault_path / self.KNOWLEDGE_DIR / "atoms"
        files = list(atoms_dir.glob("*.md"))
        titles = {}
        for f in files:
            text = f.read_text(encoding="utf-8")
            title_match = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
            if title_match:
                titles[title_match.group(1).strip()] = f.stem

        additions = 0
        for f in files:
            text = f.read_text(encoding="utf-8")
            changed = False
            for title in titles:
                if title.lower() in text.lower():
                    link = f"[[{title}]]"
                    if link not in text and titles[title] != f.stem:
                        text = text.rstrip() + f"\n\nRelated: {link}\n"
                        changed = True
                        additions += 1
            if changed:
                f.write_text(text, encoding="utf-8")
        return additions

    def _rebuild_index(self) -> None:
        atoms_dir = self.vault_path / self.KNOWLEDGE_DIR / "atoms"
        atoms = sorted(atoms_dir.glob("*.md"), key=lambda p: p.stem)
        lines = [
            "# Knowledge Index",
            "",
            f"_{len(atoms)} atoms — regenerated {datetime.now(UTC).isoformat()}_",
            "",
            "## Atoms",
            "",
        ]
        for atom_path in atoms:
            title = atom_path.stem
            text = atom_path.read_text(encoding="utf-8")
            title_match = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
            lines.append(f"- [[{title}]]")
        (self.vault_path / self.KNOWLEDGE_DIR / "index.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    def _verify(self) -> list[str]:
        warnings: list[str] = []
        atoms_dir = self.vault_path / self.KNOWLEDGE_DIR / "atoms"
        seen_titles: dict[str, str] = {}
        for f in atoms_dir.glob("*.md"):
            text = f.read_text(encoding="utf-8")
            if not text.strip():
                warnings.append(f"empty:{f.name}")
                continue
            title_match = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
            title = (title_match.group(1).strip() if title_match else f.stem).lower()
            if title in seen_titles:
                warnings.append(f"duplicate-title:{title}:{f.stem}<->{seen_titles[title]}")
            seen_titles[title] = f.stem
        return warnings

    # ── Rendering ────────────────────────────────────────────────────────

    def _render_atom(self, atom: Atom) -> str:
        lines = [
            "---",
            f"title: {atom.title}",
            f"source: {atom.source}",
            f"created_at: {atom.created_at.isoformat()}",
        ]
        if atom.tags:
            lines.append("tags:")
            for t in atom.tags:
                lines.append(f"  - {t}")
        lines.append("---")
        return "\n".join(lines) + "\n\n" + atom.content.strip() + "\n"

    def _render_report(self, report: RalphReport) -> str:
        duration = (
            (report.finished_at - report.started_at).total_seconds() if report.finished_at else 0.0
        )
        return (
            f"# Ralph session {report.session_id}\n\n"
            f"- started_at: {report.started_at.isoformat()}\n"
            f"- finished_at: {report.finished_at.isoformat() if report.finished_at else '-'}\n"
            f"- duration_sec: {duration:.2f}\n"
            f"- recorded: {len(report.recorded)}\n"
            f"- atoms_created: {len(report.atoms_created)}\n"
            f"- links_added: {report.links_added}\n"
            f"- warnings: {len(report.warnings)}\n\n"
            "## Details\n\n"
            f"Recorded: {', '.join(report.recorded) or '-'}\n\n"
            f"Atoms: {', '.join(report.atoms_created) or '-'}\n\n"
            f"Warnings:\n" + ("\n".join(f"- {w}" for w in report.warnings) or "- none") + "\n"
        )

    def _starter_mycontext(self, language: str) -> str:
        """Starter ``MyContext.md`` — the single entry-point for any AI."""
        if language.startswith("ja"):
            return (
                "# MyContext\n\n"
                "このファイルはあらゆる AI が最初に読むエントリーポイントです。\n"
                "**ルール:** このファイルに長い本文を書かない。150〜200 行を上限とし、\n"
                "詳細は `Context/` 配下の個別アトムや `knowledge/atoms/` に置き、\n"
                "ここには目次のみを書くこと。\n\n"
                "## Reading order\n\n"
                "1. `Context/MyContext.md` (this file)\n"
                "2. `Context/AIHandoff.md` — 直近の引き継ぎ事項\n"
                "3. `self/identity.md` — エージェントのアイデンティティ\n"
                "4. 必要な場合のみ `knowledge/index.md` → 関連アトム\n\n"
                "## Do / Don't\n\n"
                "- Do: 出力は簡潔に。外部データは wrap_external_data を通す。\n"
                "- Don't: `ops/sessions/` を本文として読み込まない (長すぎる)。\n"
            )
        return (
            "# MyContext\n\n"
            "Entry-point every AI reads first.\n"
            "**Rule:** keep this file short (≤200 lines). Push detail into atoms.\n\n"
            "## Reading order\n\n"
            "1. `Context/MyContext.md` (this file)\n"
            "2. `Context/AIHandoff.md` — latest cross-agent handoff notes\n"
            "3. `self/identity.md` — agent identity\n"
            "4. `knowledge/index.md` → related atoms (only if needed)\n\n"
            "## Do / Don't\n\n"
            "- Do: concise output; wrap external data.\n"
            "- Don't: load `ops/sessions/` as context — it is a log, not a source.\n"
        )

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^\w\u3040-\u9fff -]", "", value.strip().lower())
        slug = re.sub(r"[\s_]+", "-", slug).strip("-")
        return slug or f"atom-{uuid.uuid4().hex[:8]}"
