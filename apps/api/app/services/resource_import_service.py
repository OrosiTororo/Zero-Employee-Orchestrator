"""User resource import service.

Imports and manages business manuals, rules, document folders, etc.
so that AI can learn from and reference them.
Provides text extraction and summary generation capabilities.
"""

from __future__ import annotations

import logging
import mimetypes
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# テキスト抽出可能なファイル拡張子
TEXT_EXTENSIONS: set[str] = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".htm",
    ".py",
    ".js",
    ".ts",
    ".rst",
    ".log",
    ".ini",
    ".toml",
    ".cfg",
}

# インポート対象のデフォルトファイル拡張子
DEFAULT_FILE_TYPES: set[str] = {
    ".txt",
    ".md",
    ".pdf",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".docx",
    ".xlsx",
    ".pptx",
    ".html",
    ".htm",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
}


class ResourceType(str, Enum):
    """リソースの種別."""

    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PDF = "pdf"
    IMAGE = "image"
    FOLDER = "folder"
    ARCHIVE = "archive"
    URL = "url"
    MANUAL = "manual"


class ImportStatus(str, Enum):
    """インポートステータス."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


@dataclass
class ImportedResource:
    """インポートされたリソースを表すデータクラス."""

    id: str
    name: str
    resource_type: ResourceType
    source_path: str
    status: ImportStatus = ImportStatus.PENDING
    size_bytes: int = 0
    content_summary: str = ""
    extracted_text: str = ""
    tags: list[str] = field(default_factory=list)
    imported_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None


def _detect_resource_type(file_path: str) -> ResourceType:
    """ファイルパスからリソース種別を推定する."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return ResourceType.PDF
    if ext in {".xlsx", ".xls", ".csv", ".ods"}:
        return ResourceType.SPREADSHEET
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}:
        return ResourceType.IMAGE
    if ext in {".zip", ".tar", ".gz", ".7z", ".rar"}:
        return ResourceType.ARCHIVE
    return ResourceType.DOCUMENT


class ResourceImportService:
    """ユーザーリソースのインポート・管理を行うサービス.

    ファイル、フォルダ、URLからリソースをインポートし、
    テキスト抽出やサマリー生成を行う。
    """

    def __init__(self) -> None:
        """サービスを初期化する."""
        self._resources: dict[str, ImportedResource] = {}

    async def import_file(
        self,
        file_path: str,
        resource_type: ResourceType | None = None,
        *,
        tags: list[str] | None = None,
    ) -> ImportedResource:
        """単一ファイルをインポートする.

        Args:
            file_path: インポート対象のファイルパス
            resource_type: リソース種別（省略時は拡張子から推定）
            tags: タグのリスト

        Returns:
            インポートされたリソース

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        if resource_type is None:
            resource_type = _detect_resource_type(file_path)

        stat = path.stat()
        resource_id = str(uuid.uuid4())
        resource = ImportedResource(
            id=resource_id,
            name=path.name,
            resource_type=resource_type,
            source_path=str(path.resolve()),
            size_bytes=stat.st_size,
            tags=tags or [],
        )

        # テキスト抽出を試行
        resource.status = ImportStatus.PROCESSING
        try:
            resource.extracted_text = await self.extract_text(resource)
            resource.content_summary = await self.generate_summary(resource)
            resource.status = ImportStatus.COMPLETED
            resource.processed_at = datetime.now(UTC)
        except Exception:
            logger.warning("テキスト抽出失敗: %s", file_path, exc_info=True)
            resource.status = ImportStatus.FAILED

        self._resources[resource_id] = resource
        logger.info(
            "ファイルインポート: id=%s, name=%s, type=%s",
            resource_id,
            path.name,
            resource_type.value,
        )
        return resource

    async def import_folder(
        self,
        folder_path: str,
        *,
        recursive: bool = True,
        file_types: set[str] | None = None,
    ) -> list[ImportedResource]:
        """フォルダからリソースをインポートする.

        Args:
            folder_path: インポート対象のフォルダパス
            recursive: サブフォルダも再帰的に処理するか
            file_types: 対象ファイル拡張子（省略時はデフォルトセット）

        Returns:
            インポートされたリソースのリスト

        Raises:
            FileNotFoundError: フォルダが存在しない場合
        """
        path = Path(folder_path)
        if not path.is_dir():
            raise FileNotFoundError(f"フォルダが見つかりません: {folder_path}")

        allowed = file_types or DEFAULT_FILE_TYPES
        imported: list[ImportedResource] = []

        pattern = "**/*" if recursive else "*"
        for file_path in sorted(path.glob(pattern)):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in allowed:
                continue
            try:
                resource = await self.import_file(str(file_path))
                imported.append(resource)
            except Exception:
                logger.warning("フォルダインポート中のエラー: %s", file_path, exc_info=True)

        logger.info("フォルダインポート完了: path=%s, count=%d", folder_path, len(imported))
        return imported

    async def import_url(
        self,
        url: str,
        *,
        tags: list[str] | None = None,
    ) -> ImportedResource:
        """URLからリソースをインポートする.

        Args:
            url: インポート対象のURL
            tags: タグのリスト

        Returns:
            インポートされたリソース
        """
        resource_id = str(uuid.uuid4())
        resource = ImportedResource(
            id=resource_id,
            name=url.split("/")[-1] or url,
            resource_type=ResourceType.URL,
            source_path=url,
            tags=tags or [],
            status=ImportStatus.PENDING,
        )

        # NOTE: 実際のURL取得は外部HTTPクライアントを使用する
        # ここではメタデータのみ保存し、非同期処理で取得を行う
        resource.status = ImportStatus.PROCESSING
        self._resources[resource_id] = resource
        logger.info("URLインポート登録: id=%s, url=%s", resource_id, url)
        return resource

    def get_resource(self, resource_id: str) -> ImportedResource | None:
        """リソースをIDで取得する.

        Args:
            resource_id: リソースID

        Returns:
            リソース（存在しない場合は None）
        """
        return self._resources.get(resource_id)

    async def search_resources(
        self,
        query: str,
        *,
        resource_type: ResourceType | None = None,
        tags: list[str] | None = None,
    ) -> list[ImportedResource]:
        """リソースを検索する.

        名前、サマリー、抽出テキスト内をクエリで検索する。
        リソース種別やタグでフィルタリングも可能。

        Args:
            query: 検索クエリ文字列
            resource_type: フィルタするリソース種別
            tags: フィルタするタグ（いずれか一致）

        Returns:
            マッチしたリソースのリスト
        """
        query_lower = query.lower()
        results: list[ImportedResource] = []

        for resource in self._resources.values():
            if resource_type and resource.resource_type != resource_type:
                continue
            if tags and not any(t in resource.tags for t in tags):
                continue

            # テキスト検索
            searchable = (
                f"{resource.name} {resource.content_summary} {resource.extracted_text}"
            ).lower()
            if query_lower in searchable:
                results.append(resource)

        return results

    async def list_resources(
        self,
        *,
        status: ImportStatus | None = None,
        resource_type: ResourceType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImportedResource]:
        """リソース一覧を取得する.

        Args:
            status: フィルタするステータス
            resource_type: フィルタするリソース種別
            limit: 取得件数上限
            offset: スキップ件数

        Returns:
            リソースのリスト
        """
        resources = list(self._resources.values())

        if status:
            resources = [r for r in resources if r.status == status]
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]

        # imported_at で降順ソート
        resources.sort(key=lambda r: r.imported_at, reverse=True)
        return resources[offset : offset + limit]

    async def delete_resource(self, resource_id: str) -> bool:
        """リソースを削除する.

        Args:
            resource_id: リソースID

        Returns:
            削除成功の場合 True
        """
        if resource_id not in self._resources:
            return False

        del self._resources[resource_id]
        logger.info("リソース削除: id=%s", resource_id)
        return True

    async def extract_text(self, resource: ImportedResource) -> str:
        """リソースからテキストを抽出する.

        対応するファイル形式からプレーンテキストを抽出する。
        現在はテキストベースのファイルのみ対応。

        Args:
            resource: 対象リソース

        Returns:
            抽出されたテキスト
        """
        if resource.resource_type == ResourceType.URL:
            return ""

        path = Path(resource.source_path)
        if not path.exists():
            return ""

        ext = path.suffix.lower()
        if ext in TEXT_EXTENSIONS:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                # 大きすぎるファイルは先頭部分のみ
                max_chars = 100_000
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n... (truncated)"
                return content
            except Exception:
                logger.warning("テキスト読み取り失敗: %s", path, exc_info=True)
                return ""

        # PDF, DOCX などは将来的に専用ライブラリで対応
        mime_type, _ = mimetypes.guess_type(str(path))
        logger.debug("テキスト抽出未対応: %s (mime=%s)", path.name, mime_type)
        return ""

    async def generate_summary(self, resource: ImportedResource) -> str:
        """リソースのサマリーを生成する.

        抽出テキストの先頭から簡易サマリーを作成する。
        将来的にはLLMを使用した高品質なサマリー生成に移行予定。

        Args:
            resource: 対象リソース

        Returns:
            サマリー文字列
        """
        text = resource.extracted_text
        if not text:
            return ""

        # 簡易サマリー: 先頭200文字
        summary = text[:200].strip()
        if len(text) > 200:
            summary += "..."
        return summary


# ---------------------------------------------------------------------------
# グローバルインスタンス
# ---------------------------------------------------------------------------
resource_import_service = ResourceImportService()
