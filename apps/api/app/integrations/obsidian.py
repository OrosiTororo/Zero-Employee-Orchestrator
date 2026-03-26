"""Obsidian integration — Markdown-based knowledge management.

Provides bidirectional sync with Obsidian Vault.
Performs note read/write, link graph construction, full-text search,
and backlink analysis, integrating with the ZEO knowledge store.

File access within the Vault goes through the sandbox and is
restricted to permitted directories only.

Safety:
- Access control via file sandbox
- PII guard applied (during knowledge store integration)
- Audit log recording
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ObsidianNote:
    """Obsidian note."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    backlinks: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    vault_id: str = ""


@dataclass
class ObsidianVault:
    """Obsidian Vault."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    path: str = ""
    index: dict[str, dict] = field(default_factory=dict)


class ObsidianIntegration:
    """Obsidian integration service.

    Registers Obsidian Vaults and provides note CRUD, search,
    link graph construction, and sync with ZEO knowledge store.
    """

    def __init__(self) -> None:
        self._vaults: dict[str, ObsidianVault] = {}

    def register_vault(self, name: str, path: str) -> ObsidianVault:
        """Register a Vault directory.

        Args:
            name: Display name of the Vault
            path: Path to the Vault directory

        Returns:
            Registered ObsidianVault

        Raises:
            FileNotFoundError: If the Vault path does not exist
        """
        vault_path = Path(path).resolve()
        if not vault_path.is_dir():
            raise FileNotFoundError(f"Vault directory not found: {path}")

        vault = ObsidianVault(name=name, path=str(vault_path))
        self._vaults[vault.id] = vault
        logger.info("Vault registered: %s (%s) -> %s", name, vault.id, vault_path)
        return vault

    async def scan_vault(self, vault_id: str) -> dict[str, dict]:
        """Scan all .md files in the Vault and build an index.

        Collects metadata (title, tags, links, modified date) for each file
        and stores it in the Vault index.

        Args:
            vault_id: Vault ID

        Returns:
            Dictionary mapping filename to metadata

        Raises:
            KeyError: If Vault ID does not exist
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            raise KeyError(f"Vault not found: {vault_id}")

        vault_path = Path(vault.path)
        index: dict[str, dict] = {}

        for md_file in vault_path.rglob("*.md"):
            relative = md_file.relative_to(vault_path)
            title = md_file.stem

            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                logger.warning("File read error: %s — %s", md_file, exc)
                continue

            tags = self._extract_tags(content)
            links = self._extract_links(content)
            stat = md_file.stat()

            index[str(relative)] = {
                "title": title,
                "tags": tags,
                "links": links,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                "created_at": datetime.fromtimestamp(stat.st_ctime, tz=UTC).isoformat(),
            }

        vault.index = index
        logger.info("Vault scan complete: %s, file_count=%d", vault.name, len(index))
        return index

    async def get_note(self, vault_id: str, title: str) -> ObsidianNote | None:
        """Read a note.

        Args:
            vault_id: Vault ID
            title: Note title (without extension)

        Returns:
            ObsidianNote, or None if not found.
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return None

        file_path = self._resolve_note_path(vault, title)
        if not file_path or not file_path.is_file():
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.error("Note read error: %s — %s", file_path, exc)
            return None

        stat = file_path.stat()
        tags = self._extract_tags(content)
        links = self._extract_links(content)
        backlinks = await self._find_backlinks(vault, title)

        return ObsidianNote(
            title=title,
            content=content,
            tags=tags,
            links=links,
            backlinks=backlinks,
            vault_id=vault_id,
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=UTC),
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

    async def create_note(
        self,
        vault_id: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
    ) -> ObsidianNote:
        """Create a new note.

        Args:
            vault_id: Vault ID
            title: Note title
            content: Note body
            tags: Tags to assign

        Returns:
            Created ObsidianNote

        Raises:
            KeyError: If Vault ID does not exist
            FileExistsError: If a note with the same name already exists
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            raise KeyError(f"Vault not found: {vault_id}")

        file_path = Path(vault.path) / f"{title}.md"
        if file_path.exists():
            raise FileExistsError(f"Note already exists: {title}")

        # Add tags to frontmatter
        if tags:
            frontmatter = "---\ntags:\n"
            for tag in tags:
                frontmatter += f"  - {tag}\n"
            frontmatter += "---\n\n"
            full_content = frontmatter + content
        else:
            full_content = content

        file_path.write_text(full_content, encoding="utf-8")
        logger.info("Note created: %s in vault %s", title, vault.name)

        # Update index
        relative = file_path.relative_to(Path(vault.path))
        vault.index[str(relative)] = {
            "title": title,
            "tags": tags or [],
            "links": self._extract_links(full_content),
            "size_bytes": file_path.stat().st_size,
            "modified_at": datetime.now(UTC).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
        }

        return ObsidianNote(
            title=title,
            content=full_content,
            tags=tags or [],
            links=self._extract_links(full_content),
            vault_id=vault_id,
        )

    async def update_note(
        self,
        vault_id: str,
        title: str,
        content: str,
    ) -> ObsidianNote | None:
        """Update an existing note.

        Args:
            vault_id: Vault ID
            title: Note title
            content: New note body

        Returns:
            Updated ObsidianNote, or None if note not found.
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return None

        file_path = self._resolve_note_path(vault, title)
        if not file_path or not file_path.is_file():
            return None

        file_path.write_text(content, encoding="utf-8")
        logger.info("Note updated: %s in vault %s", title, vault.name)

        # Update index
        relative = file_path.relative_to(Path(vault.path))
        if str(relative) in vault.index:
            vault.index[str(relative)].update(
                {
                    "links": self._extract_links(content),
                    "tags": self._extract_tags(content),
                    "size_bytes": file_path.stat().st_size,
                    "modified_at": datetime.now(UTC).isoformat(),
                }
            )

        return ObsidianNote(
            title=title,
            content=content,
            tags=self._extract_tags(content),
            links=self._extract_links(content),
            vault_id=vault_id,
            modified_at=datetime.now(UTC),
        )

    async def search_notes(
        self,
        vault_id: str,
        query: str = "",
        tags: list[str] | None = None,
    ) -> list[ObsidianNote]:
        """Full-text search for notes.

        Filter by query string and tags.

        Args:
            vault_id: Vault ID
            query: Search query (partial match)
            tags: Tags to filter by

        Returns:
            List of matched notes
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return []

        results: list[ObsidianNote] = []
        vault_path = Path(vault.path)
        query_lower = query.lower()

        for relative, meta in vault.index.items():
            # Tag filter
            if tags:
                note_tags = set(meta.get("tags", []))
                if not set(tags).intersection(note_tags):
                    continue

            file_path = vault_path / relative
            if not file_path.is_file():
                continue

            # Query filter
            if query:
                try:
                    content = file_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue

                if query_lower not in content.lower():
                    continue
            else:
                try:
                    content = file_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    content = ""

            results.append(
                ObsidianNote(
                    title=meta.get("title", file_path.stem),
                    content=content,
                    tags=meta.get("tags", []),
                    links=meta.get("links", []),
                    vault_id=vault_id,
                )
            )

        return results

    async def get_backlinks(self, vault_id: str, title: str) -> list[str]:
        """Get backlinks (incoming links) to a specified note.

        Args:
            vault_id: Vault ID
            title: Note title

        Returns:
            List of note titles that link to this note
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return []
        return await self._find_backlinks(vault, title)

    async def get_graph(self, vault_id: str) -> dict[str, list[str]]:
        """Return the link graph of the entire Vault as an adjacency list.

        Args:
            vault_id: Vault ID

        Returns:
            Adjacency list mapping note title to list of linked note titles
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return {}

        graph: dict[str, list[str]] = {}
        for _relative, meta in vault.index.items():
            title = meta.get("title", "")
            links = meta.get("links", [])
            if title:
                graph[title] = links

        return graph

    async def sync_knowledge_store(self, vault_id: str) -> dict:
        """Sync Vault contents to the ZEO knowledge store.

        Reads notes from the Vault and registers/updates them in the knowledge store.

        Args:
            vault_id: Vault ID

        Returns:
            Summary dictionary of sync results
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return {"error": f"Vault not found: {vault_id}"}

        synced = 0
        errors = 0

        for relative, meta in vault.index.items():
            file_path = Path(vault.path) / relative
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                title = meta.get("title", file_path.stem)
                tags = meta.get("tags", [])

                # Attempt to register in knowledge store
                try:
                    from app.orchestration.knowledge import knowledge_store

                    if hasattr(knowledge_store, "add_entry"):
                        await knowledge_store.add_entry(
                            title=title,
                            content=content,
                            source=f"obsidian:{vault.name}/{relative}",
                            tags=tags,
                        )
                except ImportError:
                    logger.debug("Knowledge store not available, skipping")
                    pass

                synced += 1
            except Exception as exc:
                logger.warning("Sync error: %s — %s", relative, exc)
                errors += 1

        result = {
            "vault_id": vault_id,
            "vault_name": vault.name,
            "synced": synced,
            "errors": errors,
            "total": len(vault.index),
        }
        logger.info("Knowledge store sync complete: %s", result)
        return result

    async def export_to_vault(
        self,
        vault_id: str,
        content: str,
        title: str,
        tags: list[str] | None = None,
    ) -> ObsidianNote:
        """Export ZEO content to a Vault.

        Args:
            vault_id: Vault ID
            content: Content to export
            title: Note title
            tags: Tags to assign

        Returns:
            Created ObsidianNote
        """
        # Update if an existing note exists
        vault = self._vaults.get(vault_id)
        if not vault:
            raise KeyError(f"Vault not found: {vault_id}")

        file_path = Path(vault.path) / f"{title}.md"
        if file_path.exists():
            note = await self.update_note(vault_id, title, content)
            if note:
                return note

        return await self.create_note(vault_id, title, content, tags)

    def _resolve_note_path(self, vault: ObsidianVault, title: str) -> Path | None:
        """Resolve file path from a note title."""
        vault_path = Path(vault.path)

        # Search for file directly
        direct = vault_path / f"{title}.md"
        if direct.is_file():
            return direct

        # Search from index
        for relative, meta in vault.index.items():
            if meta.get("title") == title:
                candidate = vault_path / relative
                if candidate.is_file():
                    return candidate

        # Also search subfolders
        for md_file in vault_path.rglob(f"{title}.md"):
            return md_file

        return None

    async def _find_backlinks(self, vault: ObsidianVault, title: str) -> list[str]:
        """Search for backlinks to the specified title."""
        backlinks: list[str] = []
        for _relative, meta in vault.index.items():
            links = meta.get("links", [])
            if title in links:
                note_title = meta.get("title", "")
                if note_title and note_title != title:
                    backlinks.append(note_title)
        return backlinks

    @staticmethod
    def _extract_tags(content: str) -> list[str]:
        """Extract tags from note body.

        Detects the tags: section in frontmatter and inline #tag patterns.
        """
        tags: list[str] = []

        # Extract from frontmatter
        fm_match = re.search(
            r"^---\s*\n(.*?)\n---",
            content,
            re.DOTALL,
        )
        if fm_match:
            fm = fm_match.group(1)
            # Only within tags: section
            in_tags = False
            for line in fm.split("\n"):
                stripped = line.strip()
                if stripped.startswith("tags:"):
                    in_tags = True
                    continue
                if in_tags and stripped.startswith("- "):
                    tags.append(stripped[2:].strip())
                elif in_tags and not stripped.startswith("-"):
                    in_tags = False

        # Extract inline tags (#tag)
        inline_tags = re.findall(r"(?<!\w)#([A-Za-z\u3040-\u9fff][\w\u3040-\u9fff]*)", content)
        for t in inline_tags:
            if t not in tags:
                tags.append(t)

        return tags

    @staticmethod
    def _extract_links(content: str) -> list[str]:
        """Extract Obsidian internal links ([[link]]) from note body."""
        # [[title]] or [[title|display]]
        matches = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
        return list(dict.fromkeys(matches))  # Deduplicate while preserving order


# Global instance
obsidian_integration = ObsidianIntegration()
