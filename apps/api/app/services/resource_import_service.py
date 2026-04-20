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

from app.security.sandbox import AccessType, filesystem_sandbox

logger = logging.getLogger(__name__)


def _require_path_access(path: str | Path, access_type: AccessType) -> None:
    """Raise PermissionError if the sandbox denies access to ``path``."""
    check = filesystem_sandbox.check_access(str(path), access_type)
    if not check.allowed:
        raise PermissionError(
            f"Sandbox denied {access_type.value} access to {path}: {check.reason}"
        )


# File extensions that support text extraction
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

# Default file extensions for import
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
    """Resource type."""

    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PDF = "pdf"
    IMAGE = "image"
    FOLDER = "folder"
    ARCHIVE = "archive"
    URL = "url"
    MANUAL = "manual"


class ImportStatus(str, Enum):
    """Import status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


@dataclass
class ImportedResource:
    """Data class representing an imported resource."""

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
    """Detect resource type from file path."""
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
    """Service for importing and managing user resources.

    Imports resources from files, folders, and URLs,
    and performs text extraction and summary generation.
    """

    def __init__(self) -> None:
        """Initialize the service."""
        self._resources: dict[str, ImportedResource] = {}

    async def import_file(
        self,
        file_path: str,
        resource_type: ResourceType | None = None,
        *,
        tags: list[str] | None = None,
    ) -> ImportedResource:
        """Import a single file.

        Args:
            file_path: File path to import
            resource_type: Resource type (auto-detected from extension if omitted)
            tags: List of tags

        Returns:
            The imported resource

        Raises:
            FileNotFoundError: If the file does not exist
        """
        _require_path_access(file_path, AccessType.READ)
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

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

        # Attempt text extraction
        resource.status = ImportStatus.PROCESSING
        try:
            resource.extracted_text = await self.extract_text(resource)
            resource.content_summary = await self.generate_summary(resource)
            resource.status = ImportStatus.COMPLETED
            resource.processed_at = datetime.now(UTC)
        except Exception:
            logger.warning("Text extraction failed: %s", file_path, exc_info=True)
            resource.status = ImportStatus.FAILED

        self._resources[resource_id] = resource
        logger.info(
            "File imported: id=%s, name=%s, type=%s",
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
        """Import resources from a folder.

        Args:
            folder_path: Folder path to import
            recursive: Whether to recursively process subfolders
            file_types: Target file extensions (defaults to default set if omitted)

        Returns:
            List of imported resources

        Raises:
            FileNotFoundError: If the folder does not exist
        """
        _require_path_access(folder_path, AccessType.LIST)
        path = Path(folder_path)
        if not path.is_dir():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

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
                logger.warning("Error during folder import: %s", file_path, exc_info=True)

        logger.info("Folder import completed: path=%s, count=%d", folder_path, len(imported))
        return imported

    async def import_url(
        self,
        url: str,
        *,
        tags: list[str] | None = None,
    ) -> ImportedResource:
        """Import a resource from a URL.

        Args:
            url: URL to import
            tags: List of tags

        Returns:
            The imported resource
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

        # NOTE: Actual URL fetching uses an external HTTP client
        # Here we only save metadata; fetching is done asynchronously
        resource.status = ImportStatus.PROCESSING
        self._resources[resource_id] = resource
        logger.info("URL import registered: id=%s, url=%s", resource_id, url)
        return resource

    def get_resource(self, resource_id: str) -> ImportedResource | None:
        """Get a resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            The resource (None if not found)
        """
        return self._resources.get(resource_id)

    async def search_resources(
        self,
        query: str,
        *,
        resource_type: ResourceType | None = None,
        tags: list[str] | None = None,
    ) -> list[ImportedResource]:
        """Search for resources.

        Searches within names, summaries, and extracted text by query.
        Can also filter by resource type and tags.

        Args:
            query: Search query string
            resource_type: Resource type to filter by
            tags: Tags to filter by (any match)

        Returns:
            List of matched resources
        """
        query_lower = query.lower()
        results: list[ImportedResource] = []

        for resource in self._resources.values():
            if resource_type and resource.resource_type != resource_type:
                continue
            if tags and not any(t in resource.tags for t in tags):
                continue

            # Text search
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
        """Get a list of resources.

        Args:
            status: Status to filter by
            resource_type: Resource type to filter by
            limit: Maximum number of items to retrieve
            offset: Number of items to skip

        Returns:
            List of resources
        """
        resources = list(self._resources.values())

        if status:
            resources = [r for r in resources if r.status == status]
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]

        # Sort by imported_at descending
        resources.sort(key=lambda r: r.imported_at, reverse=True)
        return resources[offset : offset + limit]

    async def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource.

        Args:
            resource_id: Resource ID

        Returns:
            True if deletion was successful
        """
        if resource_id not in self._resources:
            return False

        del self._resources[resource_id]
        logger.info("Resource deleted: id=%s", resource_id)
        return True

    async def extract_text(self, resource: ImportedResource) -> str:
        """Extract text from a resource.

        Extracts plain text from supported file formats.
        Currently supports text-based files only.

        Args:
            resource: Target resource

        Returns:
            Extracted text
        """
        if resource.resource_type == ResourceType.URL:
            return ""

        path = Path(resource.source_path)
        if not path.exists():
            return ""
        _require_path_access(path, AccessType.READ)

        ext = path.suffix.lower()
        if ext in TEXT_EXTENSIONS:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                # For files that are too large, only the beginning portion
                max_chars = 100_000
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n... (truncated)"
                return content
            except Exception:
                logger.warning("Text read failed: %s", path, exc_info=True)
                return ""

        # PDF, DOCX, etc. will be supported by dedicated libraries in the future
        mime_type, _ = mimetypes.guess_type(str(path))
        logger.debug("Text extraction not supported: %s (mime=%s)", path.name, mime_type)
        return ""

    async def generate_summary(self, resource: ImportedResource) -> str:
        """Generate a summary for a resource.

        Creates a simple summary from the beginning of the extracted text.
        Will transition to high-quality LLM-based summary generation in the future.

        Args:
            resource: Target resource

        Returns:
            Summary string
        """
        text = resource.extracted_text
        if not text:
            return ""

        # Simple summary: first 200 characters
        summary = text[:200].strip()
        if len(text) > 200:
            summary += "..."
        return summary


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------
resource_import_service = ResourceImportService()
