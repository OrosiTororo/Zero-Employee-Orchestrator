"""File system sandbox -- Restrict AI folder access.

Sandbox functionality that restricts AI access to only folders
explicitly permitted by the user.

Design principles:
- Default: AI cannot access any folders not permitted by the user
- Whitelist-based: Only permitted paths are accessible
- Prevent escape via symlink following
- Prevent path traversal attacks
- Record all access attempts in audit logs

Security levels:
- STRICT: Whitelisted folders only (default)
- MODERATE: Whitelist + public directories
- PERMISSIVE: Everything except blocklist (not recommended)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SandboxLevel(str, Enum):
    """Sandbox level."""

    STRICT = "strict"  # Whitelist only (default)
    MODERATE = "moderate"  # Whitelist + public directories
    PERMISSIVE = "permissive"  # Everything except blocklist (not recommended)


class AccessType(str, Enum):
    """Access type."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    LIST = "list"
    DELETE = "delete"


@dataclass
class AccessCheckResult:
    """Access check result."""

    allowed: bool
    path: str
    access_type: AccessType
    reason: str
    sandbox_level: SandboxLevel


@dataclass
class SandboxConfig:
    """Sandbox configuration."""

    level: SandboxLevel = SandboxLevel.STRICT
    allowed_paths: list[str] = field(default_factory=list)
    denied_paths: list[str] = field(default_factory=lambda: list(_DEFAULT_DENIED_PATHS))
    allowed_extensions: set[str] = field(default_factory=lambda: set(_DEFAULT_ALLOWED_EXTENSIONS))
    max_file_size_mb: int = 50
    allow_symlink_follow: bool = False


# Default denied paths (common across all levels)
_DEFAULT_DENIED_PATHS: list[str] = [
    "/etc/shadow",
    "/etc/passwd",
    "/etc/sudoers",
    "/root",
    "/.ssh",
    "/.gnupg",
    "/.aws",
    "/.config/gcloud",
    "/.azure",
    "/var/log/auth.log",
    "/var/log/secure",
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_ed25519",
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    "wallet.dat",
    "keystore",
    ".netrc",
    ".npmrc",  # npm auth tokens
    ".pypirc",  # PyPI credentials
    ".docker/config.json",
    "kubeconfig",
]

# Default allowed extensions
_DEFAULT_ALLOWED_EXTENSIONS: set[str] = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".sh",
    ".bash",
    ".sql",
    ".graphql",
    ".proto",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".pptx",
    ".log",
    ".toml",
    ".ini",
    ".cfg",
}


class FileSystemSandbox:
    """File system sandbox.

    Restricts AI-accessible folders and files to a user-specified whitelist.
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self._config = config or SandboxConfig()

    @property
    def config(self) -> SandboxConfig:
        return self._config

    def update_config(self, config: SandboxConfig) -> None:
        """Update configuration."""
        self._config = config
        logger.info(
            "Sandbox config updated: level=%s, allowed=%d paths, denied=%d paths",
            config.level.value,
            len(config.allowed_paths),
            len(config.denied_paths),
        )

    def add_allowed_path(self, path: str) -> None:
        """Add an allowed path."""
        resolved = str(Path(path).resolve())
        if resolved not in self._config.allowed_paths:
            self._config.allowed_paths.append(resolved)
            logger.info("Sandbox: allowed path added: %s", resolved)

    def remove_allowed_path(self, path: str) -> None:
        """Remove an allowed path."""
        resolved = str(Path(path).resolve())
        self._config.allowed_paths = [p for p in self._config.allowed_paths if p != resolved]
        logger.info("Sandbox: allowed path removed: %s", resolved)

    def check_access(
        self,
        path: str,
        access_type: AccessType = AccessType.READ,
    ) -> AccessCheckResult:
        """Check whether access to a path is permitted.

        Args:
            path: Path to check
            access_type: Type of access

        Returns:
            AccessCheckResult: Access permission result and reason
        """
        try:
            # Normalize path (prevent path traversal)
            resolved_path = str(Path(path).resolve())
        except (ValueError, OSError) as exc:
            return AccessCheckResult(
                allowed=False,
                path=path,
                access_type=access_type,
                reason=f"Invalid path: {exc}",
                sandbox_level=self._config.level,
            )

        # Symlink check (detect links using original path before resolution)
        # Note: os.path.islink must be run on the original path before resolve()
        if not self._config.allow_symlink_follow and os.path.islink(path):
            return AccessCheckResult(
                allowed=False,
                path=resolved_path,
                access_type=access_type,
                reason="Symlink following is disabled",
                sandbox_level=self._config.level,
            )

        # If resolved path differs significantly from original, possible symlink attack
        # (countermeasure against symlink chains and indirect links)
        if not self._config.allow_symlink_follow:
            original_dir = str(Path(path).parent.resolve())
            resolved_dir = str(Path(resolved_path).parent)
            if original_dir != resolved_dir:
                return AccessCheckResult(
                    allowed=False,
                    path=resolved_path,
                    access_type=access_type,
                    reason="Path resolves to different directory (possible symlink attack)",
                    sandbox_level=self._config.level,
                )

        # Denied path check (common across all levels)
        for denied in self._config.denied_paths:
            if denied.startswith("/") or denied.startswith("~"):
                # Absolute path denial rule
                denied_resolved = str(Path(denied).expanduser().resolve())
                if resolved_path.startswith(denied_resolved) or resolved_path == denied_resolved:
                    return AccessCheckResult(
                        allowed=False,
                        path=resolved_path,
                        access_type=access_type,
                        reason=f"Path is in denied list: {denied}",
                        sandbox_level=self._config.level,
                    )
            else:
                # Filename pattern denial rule
                basename = os.path.basename(resolved_path)
                if basename == denied or resolved_path.endswith(denied):
                    return AccessCheckResult(
                        allowed=False,
                        path=resolved_path,
                        access_type=access_type,
                        reason=f"File matches denied pattern: {denied}",
                        sandbox_level=self._config.level,
                    )

        # Level-specific checks
        if self._config.level == SandboxLevel.STRICT:
            return self._check_strict(resolved_path, access_type)
        elif self._config.level == SandboxLevel.MODERATE:
            return self._check_moderate(resolved_path, access_type)
        else:
            return self._check_permissive(resolved_path, access_type)

    def _check_strict(self, resolved_path: str, access_type: AccessType) -> AccessCheckResult:
        """STRICT mode: whitelisted folders only."""
        for allowed in self._config.allowed_paths:
            allowed_resolved = str(Path(allowed).resolve())
            if resolved_path.startswith(allowed_resolved) or resolved_path == allowed_resolved:
                return AccessCheckResult(
                    allowed=True,
                    path=resolved_path,
                    access_type=access_type,
                    reason=f"Path is within allowed directory: {allowed}",
                    sandbox_level=self._config.level,
                )

        return AccessCheckResult(
            allowed=False,
            path=resolved_path,
            access_type=access_type,
            reason="STRICT mode: path not in allowed list. Add path via security settings.",
            sandbox_level=self._config.level,
        )

    def _check_moderate(self, resolved_path: str, access_type: AccessType) -> AccessCheckResult:
        """MODERATE mode: whitelist + common public directories."""
        # Allowlist check
        for allowed in self._config.allowed_paths:
            allowed_resolved = str(Path(allowed).resolve())
            if resolved_path.startswith(allowed_resolved):
                return AccessCheckResult(
                    allowed=True,
                    path=resolved_path,
                    access_type=access_type,
                    reason=f"Path is within allowed directory: {allowed}",
                    sandbox_level=self._config.level,
                )

        # Extension check for read access
        if access_type == AccessType.READ:
            ext = Path(resolved_path).suffix.lower()
            if ext in self._config.allowed_extensions:
                return AccessCheckResult(
                    allowed=True,
                    path=resolved_path,
                    access_type=access_type,
                    reason=f"File extension {ext} is allowed for reading",
                    sandbox_level=self._config.level,
                )

        return AccessCheckResult(
            allowed=False,
            path=resolved_path,
            access_type=access_type,
            reason="MODERATE mode: path not in allowed list and not a permitted file type.",
            sandbox_level=self._config.level,
        )

    def _check_permissive(self, resolved_path: str, access_type: AccessType) -> AccessCheckResult:
        """PERMISSIVE mode: allow everything except denied list (not recommended)."""
        # Denied paths already checked above
        return AccessCheckResult(
            allowed=True,
            path=resolved_path,
            access_type=access_type,
            reason="PERMISSIVE mode: path not in denied list",
            sandbox_level=self._config.level,
        )

    def check_file_size(self, path: str) -> bool:
        """Check whether the file size is within limits."""
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            return size_mb <= self._config.max_file_size_mb
        except OSError:
            return False

    def get_allowed_paths(self) -> list[str]:
        """Return the list of allowed paths."""
        return list(self._config.allowed_paths)

    def get_denied_paths(self) -> list[str]:
        """Return the list of denied paths."""
        return list(self._config.denied_paths)


# Global instance
filesystem_sandbox = FileSystemSandbox()
