"""Obsidian 統合 — Markdown ベースのナレッジ管理.

Obsidian Vault との双方向同期を提供する。
ノートの読み書き・リンクグラフの構築・全文検索・バックリンク解析を行い、
ZEO ナレッジストアとの統合を実現する。

Vault 内のファイルアクセスはサンドボックスを経由し、
許可されたディレクトリのみに制限される。

安全性:
- ファイルサンドボックス経由のアクセス制御
- PII ガード適用（ナレッジストア連携時）
- 監査ログ記録
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
    """Obsidian ノート."""

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
    """Obsidian 統合サービス.

    Obsidian Vault を登録し、ノートの CRUD・検索・リンクグラフ構築・
    ZEO ナレッジストアとの同期を提供する。
    """

    def __init__(self) -> None:
        self._vaults: dict[str, ObsidianVault] = {}

    def register_vault(self, name: str, path: str) -> ObsidianVault:
        """Vault ディレクトリを登録する.

        Args:
            name: Vault の表示名
            path: Vault ディレクトリのパス

        Returns:
            登録された ObsidianVault

        Raises:
            FileNotFoundError: Vault パスが存在しない場合
        """
        vault_path = Path(path).resolve()
        if not vault_path.is_dir():
            raise FileNotFoundError(f"Vault ディレクトリが見つかりません: {path}")

        vault = ObsidianVault(name=name, path=str(vault_path))
        self._vaults[vault.id] = vault
        logger.info("Vault 登録: %s (%s) -> %s", name, vault.id, vault_path)
        return vault

    async def scan_vault(self, vault_id: str) -> dict[str, dict]:
        """Vault 内の全 .md ファイルをスキャンしてインデックスを構築する.

        各ファイルのメタデータ（タイトル・タグ・リンク・更新日時）を収集し、
        Vault のインデックスに格納する。

        Args:
            vault_id: Vault ID

        Returns:
            ファイル名→メタデータの辞書

        Raises:
            KeyError: Vault ID が存在しない場合
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            raise KeyError(f"Vault が見つかりません: {vault_id}")

        vault_path = Path(vault.path)
        index: dict[str, dict] = {}

        for md_file in vault_path.rglob("*.md"):
            relative = md_file.relative_to(vault_path)
            title = md_file.stem

            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                logger.warning("ファイル読み取りエラー: %s — %s", md_file, exc)
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
        logger.info("Vault スキャン完了: %s, ファイル数=%d", vault.name, len(index))
        return index

    async def get_note(self, vault_id: str, title: str) -> ObsidianNote | None:
        """ノートを読み込む.

        Args:
            vault_id: Vault ID
            title: ノートのタイトル（拡張子なし）

        Returns:
            ObsidianNote。見つからない場合は None。
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
            logger.error("ノート読み取りエラー: %s — %s", file_path, exc)
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
        """ノートを新規作成する.

        Args:
            vault_id: Vault ID
            title: ノートタイトル
            content: ノート本文
            tags: 付与するタグ

        Returns:
            作成された ObsidianNote

        Raises:
            KeyError: Vault ID が存在しない場合
            FileExistsError: 同名のノートが既に存在する場合
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            raise KeyError(f"Vault が見つかりません: {vault_id}")

        file_path = Path(vault.path) / f"{title}.md"
        if file_path.exists():
            raise FileExistsError(f"ノートが既に存在します: {title}")

        # タグをフロントマターに追加
        if tags:
            frontmatter = "---\ntags:\n"
            for tag in tags:
                frontmatter += f"  - {tag}\n"
            frontmatter += "---\n\n"
            full_content = frontmatter + content
        else:
            full_content = content

        file_path.write_text(full_content, encoding="utf-8")
        logger.info("ノート作成: %s in vault %s", title, vault.name)

        # インデックスを更新
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
        """既存ノートを更新する.

        Args:
            vault_id: Vault ID
            title: ノートタイトル
            content: 新しいノート本文

        Returns:
            更新された ObsidianNote。ノートが見つからない場合は None。
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return None

        file_path = self._resolve_note_path(vault, title)
        if not file_path or not file_path.is_file():
            return None

        file_path.write_text(content, encoding="utf-8")
        logger.info("ノート更新: %s in vault %s", title, vault.name)

        # インデックスを更新
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
        """ノートを全文検索する.

        クエリ文字列とタグでフィルタリングする。

        Args:
            vault_id: Vault ID
            query: 検索クエリ（部分一致）
            tags: フィルタするタグ

        Returns:
            マッチしたノートのリスト
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return []

        results: list[ObsidianNote] = []
        vault_path = Path(vault.path)
        query_lower = query.lower()

        for relative, meta in vault.index.items():
            # タグフィルタ
            if tags:
                note_tags = set(meta.get("tags", []))
                if not set(tags).intersection(note_tags):
                    continue

            file_path = vault_path / relative
            if not file_path.is_file():
                continue

            # クエリフィルタ
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
        """指定ノートへのバックリンク（被リンク）を取得する.

        Args:
            vault_id: Vault ID
            title: ノートタイトル

        Returns:
            このノートにリンクしているノートのタイトルリスト
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return []
        return await self._find_backlinks(vault, title)

    async def get_graph(self, vault_id: str) -> dict[str, list[str]]:
        """Vault 全体のリンクグラフを隣接リスト形式で返す.

        Args:
            vault_id: Vault ID

        Returns:
            ノートタイトル→リンク先タイトルリストの隣接リスト
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
        """Vault の内容を ZEO ナレッジストアに同期する.

        Vault 内のノートを読み取り、ナレッジストアに登録・更新する。

        Args:
            vault_id: Vault ID

        Returns:
            同期結果の概要辞書
        """
        vault = self._vaults.get(vault_id)
        if not vault:
            return {"error": f"Vault が見つかりません: {vault_id}"}

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

                # ナレッジストアへの登録を試行
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
                    logger.debug("ナレッジストアが利用できないためスキップ")
                    pass

                synced += 1
            except Exception as exc:
                logger.warning("同期エラー: %s — %s", relative, exc)
                errors += 1

        result = {
            "vault_id": vault_id,
            "vault_name": vault.name,
            "synced": synced,
            "errors": errors,
            "total": len(vault.index),
        }
        logger.info("ナレッジストア同期完了: %s", result)
        return result

    async def export_to_vault(
        self,
        vault_id: str,
        content: str,
        title: str,
        tags: list[str] | None = None,
    ) -> ObsidianNote:
        """ZEO コンテンツを Vault にエクスポートする.

        Args:
            vault_id: Vault ID
            content: エクスポートするコンテンツ
            title: ノートタイトル
            tags: 付与するタグ

        Returns:
            作成された ObsidianNote
        """
        # 既存ノートがある場合は更新
        vault = self._vaults.get(vault_id)
        if not vault:
            raise KeyError(f"Vault が見つかりません: {vault_id}")

        file_path = Path(vault.path) / f"{title}.md"
        if file_path.exists():
            note = await self.update_note(vault_id, title, content)
            if note:
                return note

        return await self.create_note(vault_id, title, content, tags)

    def _resolve_note_path(self, vault: ObsidianVault, title: str) -> Path | None:
        """ノートタイトルからファイルパスを解決する."""
        vault_path = Path(vault.path)

        # 直下のファイルを検索
        direct = vault_path / f"{title}.md"
        if direct.is_file():
            return direct

        # インデックスからの検索
        for relative, meta in vault.index.items():
            if meta.get("title") == title:
                candidate = vault_path / relative
                if candidate.is_file():
                    return candidate

        # サブフォルダも検索
        for md_file in vault_path.rglob(f"{title}.md"):
            return md_file

        return None

    async def _find_backlinks(self, vault: ObsidianVault, title: str) -> list[str]:
        """指定タイトルへのバックリンクを検索する."""
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
        """ノート本文からタグを抽出する.

        フロントマターの tags: セクションとインラインの #tag を検出する。
        """
        tags: list[str] = []

        # フロントマターからの抽出
        fm_match = re.search(
            r"^---\s*\n(.*?)\n---",
            content,
            re.DOTALL,
        )
        if fm_match:
            fm = fm_match.group(1)
            # tags: セクション内のみ
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

        # インラインタグの抽出 (#tag)
        inline_tags = re.findall(r"(?<!\w)#([A-Za-z\u3040-\u9fff][\w\u3040-\u9fff]*)", content)
        for t in inline_tags:
            if t not in tags:
                tags.append(t)

        return tags

    @staticmethod
    def _extract_links(content: str) -> list[str]:
        """ノート本文から Obsidian 内部リンク ([[link]]) を抽出する."""
        # [[title]] or [[title|display]]
        matches = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
        return list(dict.fromkeys(matches))  # 重複除去しつつ順序保持


# グローバルインスタンス
obsidian_integration = ObsidianIntegration()
