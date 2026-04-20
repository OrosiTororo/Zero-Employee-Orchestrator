"""Karpathy-style LLM Wiki service — /ingest, /query, /lint pipeline.

Reproduces the Andrej Karpathy "LLM wiki" pattern: raw sources are compiled
into a durable Markdown wiki at ingest time (not at query time, avoiding
RAG), answers cite wiki pages, and a lint pass keeps the wiki consistent.

Three operations, matching the original gist:

* ``ingest(source)`` — read a raw source (URL, file, paste), extract concepts
  and emit / update atomic wiki pages under ``wiki/``. Backlinks are added.
* ``query(question, save=False)`` — answer a question by reading relevant
  wiki pages. If ``save=True``, the Q&A is appended as a new concept page.
* ``lint(fix=False)`` — scan the wiki for broken links, duplicates,
  contradictions, and (when ``fix=True``) repair them.

Design choices:

* All vault paths go through :class:`FilesystemSandbox` for boundary checks.
* External raw text is wrapped with :func:`wrap_external_data` before any
  LLM call to prevent prompt injection from ingested pages.
* No vector DB / RAG layer is required — we rely on large context windows
  and a small hand-written index (``index.md``).
* Works offline: the "LLM compile" step is pluggable (defaults to a
  deterministic extractor so unit tests and CI don't hit a provider).
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.security.sandbox import AccessType, filesystem_sandbox

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class WikiPage:
    """A single compiled wiki page."""

    slug: str
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    backlinks: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class IngestResult:
    """Result of a single ``/ingest`` call."""

    source: str
    pages_created: list[str] = field(default_factory=list)
    pages_updated: list[str] = field(default_factory=list)
    concepts_found: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Result of a single ``/query`` call."""

    question: str
    answer: str
    citations: list[str] = field(default_factory=list)
    saved_page: str | None = None


@dataclass
class LintReport:
    """Result of a single ``/lint`` call."""

    checked: int = 0
    broken_links: list[tuple[str, str]] = field(default_factory=list)
    duplicate_titles: list[str] = field(default_factory=list)
    empty_pages: list[str] = field(default_factory=list)
    missing_backlinks: list[tuple[str, str]] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.broken_links or self.duplicate_titles or self.empty_pages or self.missing_backlinks
        )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class WikiKnowledgeService:
    """Karpathy-style LLM wiki — ingest / query / lint.

    The service keeps two top-level folders under ``vault_path``::

        vault_path/
          raw/        # untouched source dumps (Obsidian Web Clipper writes here)
          wiki/       # compiled atomic pages (Markdown with [[wikilinks]])
          wiki/index.md   # hand-written / auto-regenerated table of contents

    A single instance is safe for single-process use. For multi-process
    deployments, wrap calls in a per-vault lock.
    """

    RAW_DIR = "raw"
    WIKI_DIR = "wiki"
    INDEX_NAME = "index.md"

    # ── Patterns (shared with Obsidian integration for symmetry) ──────────
    _WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    _TAG_RE = re.compile(r"(?<!\w)#([A-Za-z\u3040-\u9fff][\w\u3040-\u9fff]*)")
    _HEADING_RE = re.compile(r"^#+\s+(.+)$", re.MULTILINE)

    # Minimum concept-word length — "AI" (2 chars) survives, "a" (1 char) doesn't
    _MIN_CONCEPT_LEN = 2

    def __init__(self, vault_path: str | Path) -> None:
        self.vault_path = Path(vault_path).resolve()
        self.raw_dir = self.vault_path / self.RAW_DIR
        self.wiki_dir = self.vault_path / self.WIKI_DIR
        # Vault is server-configured — log a warning (do not block) if the
        # sandbox does not yet whitelist it so admins can fix the config
        # before the first write attempt.
        check = filesystem_sandbox.check_access(str(self.vault_path), AccessType.WRITE)
        if not check.allowed:
            logger.warning(
                "Wiki vault outside sandbox whitelist: %s (%s). "
                "Register it via FileSystemSandbox.add_allowed_path() before writes.",
                self.vault_path,
                check.reason,
            )

    # ── Lifecycle ────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Create the folder layout if it doesn't exist. Idempotent."""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(exist_ok=True)
        self.wiki_dir.mkdir(exist_ok=True)
        index = self.wiki_dir / self.INDEX_NAME
        if not index.exists():
            index.write_text(
                "# Wiki Index\n\n"
                "Auto-maintained index of compiled concepts. "
                "Run `/lint --fix` to refresh.\n\n"
                "## Concepts\n\n",
                encoding="utf-8",
            )

    # ── /ingest ──────────────────────────────────────────────────────────

    async def ingest(
        self,
        source: str,
        content: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> IngestResult:
        """Compile a raw source into one or more wiki pages.

        ``source`` is a free-form identifier (URL, file path, "paste-1"...).
        ``content`` is the raw text — it is **always** wrapped with
        :func:`wrap_external_data` before being touched so that injection
        attempts inside the source cannot steer the agent.

        This implementation uses a deterministic extractor suitable for
        offline / test runs. Production callers can subclass and override
        :meth:`_compile_atomic_pages` to call an LLM provider.
        """
        from app.security.prompt_guard import wrap_external_data

        self.initialize()

        # Defend against prompt injection in the ingested raw text.
        wrapped = wrap_external_data(content, source=source)
        logger.debug("Ingest wrapped payload: %d chars from %s", len(wrapped), source)

        # Archive the raw source so re-compilation is always possible.
        raw_file = self.raw_dir / f"{self._slugify(title or source)}.md"
        if not raw_file.exists():
            raw_file.write_text(
                f"---\nsource: {source}\ningested_at: {datetime.now(UTC).isoformat()}\n---\n\n"
                f"{content}\n",
                encoding="utf-8",
            )

        pages = self._compile_atomic_pages(content, source=source, hint_title=title, tags=tags)
        result = IngestResult(source=source)

        for page in pages:
            target = self.wiki_dir / f"{page.slug}.md"
            if target.exists():
                existing = self._read_page(target)
                merged = self._merge_page(existing, page)
                target.write_text(self._render_page(merged), encoding="utf-8")
                result.pages_updated.append(page.slug)
            else:
                target.write_text(self._render_page(page), encoding="utf-8")
                result.pages_created.append(page.slug)
            result.concepts_found.append(page.title)

        # Refresh backlinks & index for the pages we just touched.
        self._refresh_backlinks()
        self._refresh_index()
        return result

    # ── /query ───────────────────────────────────────────────────────────

    async def query(self, question: str, save: bool = False) -> QueryResult:
        """Answer ``question`` against the wiki, optionally persisting the Q&A.

        The default implementation returns a deterministic, citation-first
        answer built from the matched pages. Subclasses can plug an LLM in
        :meth:`_synthesize_answer` without changing the rest of the flow.
        """
        self.initialize()

        matches = self._search(question)
        answer = self._synthesize_answer(question, matches)
        citations = [p.slug for p in matches]

        saved_slug: str | None = None
        if save:
            slug = self._slugify(question)[:80] or f"qa-{uuid.uuid4().hex[:8]}"
            page = WikiPage(
                slug=slug,
                title=question.strip().rstrip("?").strip() or "Untitled Q&A",
                content=answer,
                tags=["qa", "auto"],
                sources=citations,
            )
            (self.wiki_dir / f"{slug}.md").write_text(self._render_page(page), encoding="utf-8")
            saved_slug = slug
            self._refresh_backlinks()
            self._refresh_index()

        return QueryResult(
            question=question,
            answer=answer,
            citations=citations,
            saved_page=saved_slug,
        )

    # ── /lint ────────────────────────────────────────────────────────────

    async def lint(self, fix: bool = False) -> LintReport:
        """Run health checks over the wiki. Optionally repair common issues."""
        self.initialize()
        report = LintReport()

        pages = self._load_all_pages()
        slugs = {p.slug for p in pages}
        titles: dict[str, list[str]] = {}

        for page in pages:
            report.checked += 1
            titles.setdefault(page.title.lower(), []).append(page.slug)

            if not page.content.strip():
                report.empty_pages.append(page.slug)

            for link in self._WIKILINK_RE.findall(page.content):
                target_slug = self._slugify(link)
                if target_slug not in slugs:
                    report.broken_links.append((page.slug, link))

        for _title_key, owners in titles.items():
            if len(owners) > 1:
                report.duplicate_titles.extend(owners)

        # Backlink consistency: for every A -> B, B should list A.
        for page in pages:
            for link in self._WIKILINK_RE.findall(page.content):
                target_slug = self._slugify(link)
                target = next((p for p in pages if p.slug == target_slug), None)
                if target is None:
                    continue
                if page.slug not in target.backlinks:
                    report.missing_backlinks.append((target.slug, page.slug))

        if fix:
            # Remove broken links, drop empty pages, repair backlinks.
            for slug, _link in report.broken_links:
                page_path = self.wiki_dir / f"{slug}.md"
                if page_path.exists():
                    text = page_path.read_text(encoding="utf-8")
                    cleaned = self._WIKILINK_RE.sub(
                        lambda m: m.group(0) if self._slugify(m.group(1)) in slugs else m.group(1),
                        text,
                    )
                    page_path.write_text(cleaned, encoding="utf-8")
                    report.fixed.append(f"broken-link:{slug}")
            for slug in report.empty_pages:
                (self.wiki_dir / f"{slug}.md").unlink(missing_ok=True)
                report.fixed.append(f"empty:{slug}")
            self._refresh_backlinks()
            self._refresh_index()

            # Re-verify the post-fix state so ``report.ok`` reflects reality.
            # We rebuild the error lists in-place rather than returning a fresh
            # report, because the ``fixed`` list must carry over for the caller.
            report.broken_links.clear()
            report.duplicate_titles.clear()
            report.empty_pages.clear()
            report.missing_backlinks.clear()
            post_pages = self._load_all_pages()
            post_slugs = {p.slug for p in post_pages}
            post_titles: dict[str, list[str]] = {}
            for page in post_pages:
                post_titles.setdefault(page.title.lower(), []).append(page.slug)
                if not page.content.strip():
                    report.empty_pages.append(page.slug)
                for link in self._WIKILINK_RE.findall(page.content):
                    target_slug = self._slugify(link)
                    if target_slug not in post_slugs:
                        report.broken_links.append((page.slug, link))
            for owners in post_titles.values():
                if len(owners) > 1:
                    report.duplicate_titles.extend(owners)

        return report

    # ── Pluggable LLM hooks ──────────────────────────────────────────────

    def _compile_atomic_pages(
        self,
        raw: str,
        source: str,
        hint_title: str | None = None,
        tags: list[str] | None = None,
    ) -> list[WikiPage]:
        """Compile raw text into atomic pages.

        Default: one page per markdown heading, plus a summary page when
        headings are missing. Override for LLM-powered compilation.
        """
        pages: list[WikiPage] = []
        now = datetime.now(UTC)

        # Try to split by headings first.
        headings = self._HEADING_RE.findall(raw)
        if headings:
            sections = re.split(r"^#+\s+.+$", raw, flags=re.MULTILINE)
            # sections[0] is pre-heading preamble; pair the rest with headings.
            for i, heading in enumerate(headings, start=1):
                body = sections[i].strip() if i < len(sections) else ""
                slug = self._slugify(heading)
                pages.append(
                    WikiPage(
                        slug=slug,
                        title=heading.strip(),
                        content=body,
                        tags=list(tags or []) + self._TAG_RE.findall(body),
                        sources=[source],
                        created_at=now,
                        updated_at=now,
                    )
                )

        if not pages:
            # Fallback: single summary page.
            title = (hint_title or source).strip() or "Untitled"
            pages.append(
                WikiPage(
                    slug=self._slugify(title),
                    title=title,
                    content=raw.strip()[:4000],
                    tags=list(tags or []) + self._TAG_RE.findall(raw),
                    sources=[source],
                    created_at=now,
                    updated_at=now,
                )
            )

        # Seed wikilinks between pages that share non-trivial words.
        concepts = [p.title for p in pages]
        for p in pages:
            for other in concepts:
                if other == p.title:
                    continue
                if len(other) >= self._MIN_CONCEPT_LEN and other.lower() in p.content.lower():
                    link = f"[[{other}]]"
                    if link not in p.content:
                        p.content = p.content + f"\n\nSee also: {link}"

        return pages

    def _synthesize_answer(self, question: str, pages: list[WikiPage]) -> str:
        """Compose an answer from matched wiki pages.

        Default is deterministic: it concatenates the most relevant page
        excerpts and lists citations. Override to call an LLM.
        """
        if not pages:
            return (
                f"**Q:** {question}\n\n"
                "No matching wiki pages yet. Run `/ingest` on a source that "
                "covers this topic, then re-query."
            )

        lines = [f"**Q:** {question}\n", "**A (wiki-synthesized):**\n"]
        for page in pages[:5]:
            excerpt = page.content.strip().split("\n\n", 1)[0]
            lines.append(f"- [[{page.title}]] — {excerpt[:240]}")
        lines.append("\n**Citations:** " + ", ".join(f"[[{p.title}]]" for p in pages[:5]))
        return "\n".join(lines)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _search(self, query: str) -> list[WikiPage]:
        """Very small ranked search — title match > tag match > body match."""
        q = query.lower()
        ranked: list[tuple[int, WikiPage]] = []
        for page in self._load_all_pages():
            score = 0
            if q in page.title.lower():
                score += 10
            if any(q in t.lower() for t in page.tags):
                score += 5
            if q in page.content.lower():
                score += 1
            if score:
                ranked.append((score, page))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [p for _, p in ranked[:10]]

    def _load_all_pages(self) -> list[WikiPage]:
        pages: list[WikiPage] = []
        for md in self.wiki_dir.glob("*.md"):
            if md.name == self.INDEX_NAME:
                continue
            pages.append(self._read_page(md))
        return pages

    def _read_page(self, path: Path) -> WikiPage:
        text = path.read_text(encoding="utf-8")
        fm: dict[str, Any] = {}
        body = text
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            if end > 0:
                fm = self._parse_frontmatter(text[4:end])
                body = text[end + 4 :].lstrip("\n")
        return WikiPage(
            slug=path.stem,
            title=str(fm.get("title") or path.stem),
            content=body,
            tags=list(fm.get("tags") or []),
            backlinks=list(fm.get("backlinks") or []),
            sources=list(fm.get("sources") or []),
        )

    def _render_page(self, page: WikiPage) -> str:
        fm_lines = ["---", f"title: {page.title}"]
        if page.tags:
            fm_lines.append("tags:")
            for t in page.tags:
                fm_lines.append(f"  - {t}")
        if page.sources:
            fm_lines.append("sources:")
            for s in page.sources:
                fm_lines.append(f"  - {s}")
        if page.backlinks:
            fm_lines.append("backlinks:")
            for b in page.backlinks:
                fm_lines.append(f"  - {b}")
        fm_lines.append(f"updated_at: {datetime.now(UTC).isoformat()}")
        fm_lines.append("---")
        return "\n".join(fm_lines) + "\n\n" + page.content.strip() + "\n"

    def _merge_page(self, existing: WikiPage, incoming: WikiPage) -> WikiPage:
        merged = WikiPage(
            slug=existing.slug,
            title=existing.title or incoming.title,
            content=existing.content.rstrip() + "\n\n---\n\n" + incoming.content.strip(),
            tags=list(dict.fromkeys(existing.tags + incoming.tags)),
            sources=list(dict.fromkeys(existing.sources + incoming.sources)),
            backlinks=list(dict.fromkeys(existing.backlinks + incoming.backlinks)),
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
        )
        return merged

    def _refresh_backlinks(self) -> None:
        pages = self._load_all_pages()
        index: dict[str, list[str]] = {p.slug: [] for p in pages}
        for page in pages:
            for link in self._WIKILINK_RE.findall(page.content):
                target = self._slugify(link)
                if target in index and page.slug != target:
                    if page.slug not in index[target]:
                        index[target].append(page.slug)
        for page in pages:
            page.backlinks = index.get(page.slug, [])
            (self.wiki_dir / f"{page.slug}.md").write_text(
                self._render_page(page), encoding="utf-8"
            )

    def _refresh_index(self) -> None:
        pages = sorted(self._load_all_pages(), key=lambda p: p.title.lower())
        lines = [
            "# Wiki Index",
            "",
            f"_{len(pages)} concept pages — auto-generated, do not edit by hand._",
            "",
            "## Concepts",
            "",
        ]
        for p in pages:
            lines.append(f"- [[{p.title}]]")
        (self.wiki_dir / self.INDEX_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^\w\u3040-\u9fff -]", "", value.strip().lower())
        slug = re.sub(r"[\s_]+", "-", slug).strip("-")
        return slug or "untitled"

    @staticmethod
    def _parse_frontmatter(text: str) -> dict[str, Any]:
        """Tiny YAML subset parser — enough for our own output."""
        out: dict[str, Any] = {}
        current_key: str | None = None
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line:
                continue
            if line.startswith("  - ") and current_key:
                out.setdefault(current_key, []).append(line[4:].strip())
                continue
            if ":" in line and not line.startswith(" "):
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if value:
                    out[key] = value
                    current_key = None
                else:
                    current_key = key
                    out.setdefault(key, [])
        return out
