"""LSP integration — code understanding via Language Server Protocol.

Provides code understanding features such as completion, go-to-definition,
reference search, diagnostics, and formatting using the Language Server
Protocol (LSP).

Supported languages:
- Python, TypeScript, JavaScript, Rust, Go, Java

Starts and manages LSP servers for each language as subprocesses,
communicating via JSON-RPC.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

from app.security.sandbox import AccessType, filesystem_sandbox

logger = logging.getLogger(__name__)


class LanguageId(str, Enum):
    """Supported languages."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"


class LSPCapability(str, Enum):
    """LSP capability."""

    COMPLETION = "completion"
    HOVER = "hover"
    DEFINITION = "definition"
    REFERENCES = "references"
    DIAGNOSTICS = "diagnostics"
    FORMATTING = "formatting"
    RENAME = "rename"


class DiagnosticSeverity(str, Enum):
    """Diagnostic severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ServerStatus(str, Enum):
    """LSP server status."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class LSPServerConfig:
    """LSP server configuration."""

    language: LanguageId = LanguageId.PYTHON
    command: str = ""
    args: list[str] = field(default_factory=list)
    root_path: str = "."
    capabilities: list[LSPCapability] = field(default_factory=list)


@dataclass
class Diagnostic:
    """Diagnostic information."""

    file_path: str = ""
    line: int = 0
    character: int = 0
    message: str = ""
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    source: str = ""


@dataclass
class CompletionItem:
    """Completion item."""

    label: str = ""
    kind: str = "text"
    detail: str = ""
    documentation: str = ""


@dataclass
class HoverInfo:
    """Hover information."""

    contents: str = ""
    language: str = ""
    range_start: tuple[int, int] = (0, 0)
    range_end: tuple[int, int] = (0, 0)


@dataclass
class LocationInfo:
    """File location information."""

    file_path: str = ""
    line: int = 0
    character: int = 0


# Default LSP server configurations
_DEFAULT_CONFIGS: dict[LanguageId, LSPServerConfig] = {
    LanguageId.PYTHON: LSPServerConfig(
        language=LanguageId.PYTHON,
        command="pyright-langserver",
        args=["--stdio"],
        capabilities=list(LSPCapability),
    ),
    LanguageId.TYPESCRIPT: LSPServerConfig(
        language=LanguageId.TYPESCRIPT,
        command="typescript-language-server",
        args=["--stdio"],
        capabilities=list(LSPCapability),
    ),
    LanguageId.JAVASCRIPT: LSPServerConfig(
        language=LanguageId.JAVASCRIPT,
        command="typescript-language-server",
        args=["--stdio"],
        capabilities=list(LSPCapability),
    ),
    LanguageId.RUST: LSPServerConfig(
        language=LanguageId.RUST,
        command="rust-analyzer",
        args=[],
        capabilities=list(LSPCapability),
    ),
    LanguageId.GO: LSPServerConfig(
        language=LanguageId.GO,
        command="gopls",
        args=["serve"],
        capabilities=list(LSPCapability),
    ),
    LanguageId.JAVA: LSPServerConfig(
        language=LanguageId.JAVA,
        command="jdtls",
        args=[],
        capabilities=[
            LSPCapability.COMPLETION,
            LSPCapability.HOVER,
            LSPCapability.DEFINITION,
            LSPCapability.REFERENCES,
            LSPCapability.DIAGNOSTICS,
            LSPCapability.FORMATTING,
        ],
    ),
}


class LSPIntegration:
    """LSP integration service.

    Manages LSP servers per language and provides code understanding features.
    Centrally manages server start/stop and request sending.
    """

    def __init__(self) -> None:
        self._servers: dict[LanguageId, LSPServerConfig] = dict(_DEFAULT_CONFIGS)
        self._running: dict[LanguageId, bool] = {lang: False for lang in LanguageId}
        self._processes: dict[LanguageId, object] = {}
        self._status: dict[LanguageId, ServerStatus] = {
            lang: ServerStatus.STOPPED for lang in LanguageId
        }
        self._request_id: int = 0

    def register_server(self, config: LSPServerConfig) -> None:
        """Register or update LSP server configuration.

        Args:
            config: LSP server configuration
        """
        self._servers[config.language] = config
        logger.info(
            "LSP server config registered: %s -> %s %s",
            config.language.value,
            config.command,
            " ".join(config.args),
        )

    async def start_server(self, language: LanguageId) -> bool:
        """Start an LSP server.

        Starts the LSP server as a subprocess and performs the initialize handshake.

        Args:
            language: Language server to start

        Returns:
            Whether startup was successful
        """
        config = self._servers.get(language)
        if not config:
            logger.error("LSP server config not found: %s", language.value)
            return False

        if self._running.get(language):
            logger.info("LSP server already running: %s", language.value)
            return True

        self._status[language] = ServerStatus.STARTING

        try:
            import asyncio
            import shutil

            # Check command existence
            if not shutil.which(config.command):
                logger.warning(
                    "LSP server command not found: %s (language: %s)",
                    config.command,
                    language.value,
                )
                self._status[language] = ServerStatus.ERROR
                return False

            cmd = [config.command, *config.args]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self._processes[language] = process
            self._running[language] = True
            self._status[language] = ServerStatus.RUNNING

            # Send initialize request
            await self._send_initialize(language, config.root_path)

            logger.info("LSP server started: %s (PID: %s)", language.value, process.pid)
            return True

        except FileNotFoundError:
            logger.error(
                "LSP server command not found: %s",
                config.command,
            )
            self._status[language] = ServerStatus.ERROR
            return False
        except Exception as exc:
            logger.error("LSP server startup failed: %s — %s", language.value, exc)
            self._status[language] = ServerStatus.ERROR
            return False

    async def stop_server(self, language: LanguageId) -> bool:
        """Stop an LSP server.

        Args:
            language: Language server to stop

        Returns:
            Whether shutdown was successful
        """
        if not self._running.get(language):
            return True

        process = self._processes.get(language)
        if process and hasattr(process, "terminate"):
            try:
                # Send shutdown request
                await self._send_request(language, "shutdown", {})
                await self._send_notification(language, "exit", {})
                process.terminate()  # type: ignore[union-attr]
            except Exception as exc:
                logger.warning("Error during LSP server shutdown: %s — %s", language.value, exc)

        self._running[language] = False
        self._status[language] = ServerStatus.STOPPED
        self._processes.pop(language, None)
        logger.info("LSP server stopped: %s", language.value)
        return True

    async def get_diagnostics(self, file_path: str) -> list[Diagnostic]:
        """Get diagnostic information for the specified file.

        Args:
            file_path: Target file path

        Returns:
            List of diagnostics
        """
        language = self._detect_language(file_path)
        if not language or not self._running.get(language):
            return []

        # Send textDocument/didOpen to get diagnostics
        uri = f"file://{file_path}"
        content = self._read_file_content(file_path)
        if content is None:
            return []

        await self._send_notification(
            language,
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": language.value,
                    "version": 1,
                    "text": content,
                },
            },
        )

        # Diagnostics are returned as async notifications, so waiting is needed
        # In actual implementation, they are accumulated in a notification handler; placeholder returned here
        logger.info("Diagnostic request sent: %s", file_path)
        return []

    async def get_completions(
        self,
        file_path: str,
        line: int,
        character: int,
    ) -> list[CompletionItem]:
        """Get completion items at the specified position.

        Args:
            file_path: Target file path
            line: Line number (0-indexed)
            character: Column number (0-indexed)

        Returns:
            List of completion items
        """
        language = self._detect_language(file_path)
        if not language or not self._running.get(language):
            return []

        uri = f"file://{file_path}"
        response = await self._send_request(
            language,
            "textDocument/completion",
            {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
            },
        )

        if not response:
            return []

        items = response.get("items", response) if isinstance(response, dict) else []
        if isinstance(items, list):
            return [
                CompletionItem(
                    label=item.get("label", ""),
                    kind=str(item.get("kind", "text")),
                    detail=item.get("detail", ""),
                    documentation=str(item.get("documentation", "")),
                )
                for item in items
            ]
        return []

    async def get_hover(
        self,
        file_path: str,
        line: int,
        character: int,
    ) -> HoverInfo | None:
        """Get hover information at the specified position.

        Args:
            file_path: Target file path
            line: Line number (0-indexed)
            character: Column number (0-indexed)

        Returns:
            Hover information, or None if unavailable.
        """
        language = self._detect_language(file_path)
        if not language or not self._running.get(language):
            return None

        uri = f"file://{file_path}"
        response = await self._send_request(
            language,
            "textDocument/hover",
            {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
            },
        )

        if not response or not isinstance(response, dict):
            return None

        contents = response.get("contents", "")
        if isinstance(contents, dict):
            return HoverInfo(
                contents=contents.get("value", ""),
                language=contents.get("language", ""),
            )
        return HoverInfo(contents=str(contents))

    async def go_to_definition(
        self,
        file_path: str,
        line: int,
        character: int,
    ) -> LocationInfo | None:
        """Go to the definition of the symbol at the specified position.

        Args:
            file_path: Target file path
            line: Line number (0-indexed)
            character: Column number (0-indexed)

        Returns:
            Location of the definition, or None if unavailable.
        """
        language = self._detect_language(file_path)
        if not language or not self._running.get(language):
            return None

        uri = f"file://{file_path}"
        response = await self._send_request(
            language,
            "textDocument/definition",
            {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
            },
        )

        return self._parse_location(response)

    async def find_references(
        self,
        file_path: str,
        line: int,
        character: int,
    ) -> list[LocationInfo]:
        """Find all references of the symbol at the specified position.

        Args:
            file_path: Target file path
            line: Line number (0-indexed)
            character: Column number (0-indexed)

        Returns:
            List of reference locations
        """
        language = self._detect_language(file_path)
        if not language or not self._running.get(language):
            return []

        uri = f"file://{file_path}"
        response = await self._send_request(
            language,
            "textDocument/references",
            {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": True},
            },
        )

        if not response or not isinstance(response, list):
            return []

        locations: list[LocationInfo] = []
        for item in response:
            loc = self._parse_location(item)
            if loc:
                locations.append(loc)
        return locations

    async def format_document(self, file_path: str) -> str | None:
        """Format the entire file.

        Args:
            file_path: Target file path

        Returns:
            Formatted text, or None on failure.
        """
        language = self._detect_language(file_path)
        if not language or not self._running.get(language):
            return None

        uri = f"file://{file_path}"
        response = await self._send_request(
            language,
            "textDocument/formatting",
            {
                "textDocument": {"uri": uri},
                "options": {"tabSize": 4, "insertSpaces": True},
            },
        )

        if not response or not isinstance(response, list):
            return None

        # Apply text edits
        content = self._read_file_content(file_path)
        if content is None:
            return None

        # Simple text edit application (in practice, range-based editing is used)
        for edit in response:
            if isinstance(edit, dict) and "newText" in edit:
                return edit["newText"]

        return content

    def get_supported_languages(self) -> list[dict[str, object]]:
        """Return a list of configured languages.

        Returns:
            List of dictionaries with language, command, capabilities, and status
        """
        languages: list[dict[str, object]] = []
        for lang, config in self._servers.items():
            languages.append(
                {
                    "language": lang.value,
                    "command": config.command,
                    "capabilities": [c.value for c in config.capabilities],
                    "status": self._status.get(lang, ServerStatus.STOPPED).value,
                    "running": self._running.get(lang, False),
                }
            )
        return languages

    def get_server_status(self, language: LanguageId) -> dict[str, object]:
        """Return the server status for the specified language.

        Args:
            language: Target language

        Returns:
            Status information dictionary
        """
        config = self._servers.get(language)
        return {
            "language": language.value,
            "status": self._status.get(language, ServerStatus.STOPPED).value,
            "running": self._running.get(language, False),
            "command": config.command if config else "",
            "capabilities": ([c.value for c in config.capabilities] if config else []),
        }

    # --- Internal methods ---

    def _next_request_id(self) -> int:
        """Generate a JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id

    async def _send_initialize(self, language: LanguageId, root_path: str) -> dict | None:
        """Send an LSP initialize request."""
        return await self._send_request(
            language,
            "initialize",
            {
                "processId": None,
                "rootUri": f"file://{root_path}",
                "capabilities": {
                    "textDocument": {
                        "completion": {"completionItem": {"snippetSupport": True}},
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "definition": {},
                        "references": {},
                        "formatting": {},
                        "publishDiagnostics": {},
                    },
                },
            },
        )

    async def _send_request(
        self,
        language: LanguageId,
        method: str,
        params: dict,
    ) -> dict | list | None:
        """Send a JSON-RPC request to the LSP server."""
        process = self._processes.get(language)
        if not process or not hasattr(process, "stdin") or not hasattr(process, "stdout"):
            return None

        import json

        request_id = self._next_request_id()
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        try:
            body = json.dumps(message)
            header = f"Content-Length: {len(body)}\r\n\r\n"
            full_message = header + body

            process.stdin.write(full_message.encode("utf-8"))  # type: ignore[union-attr]
            await process.stdin.drain()  # type: ignore[union-attr]

            # Read response
            response_data = await self._read_response(process)
            if response_data and isinstance(response_data, dict):
                return response_data.get("result")
            return response_data

        except Exception as exc:
            logger.error(
                "LSP request failed: %s %s — %s",
                language.value,
                method,
                exc,
            )
            return None

    async def _send_notification(
        self,
        language: LanguageId,
        method: str,
        params: dict,
    ) -> None:
        """Send a JSON-RPC notification to the LSP server (no response)."""
        process = self._processes.get(language)
        if not process or not hasattr(process, "stdin"):
            return

        import json

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        try:
            body = json.dumps(message)
            header = f"Content-Length: {len(body)}\r\n\r\n"
            full_message = header + body

            process.stdin.write(full_message.encode("utf-8"))  # type: ignore[union-attr]
            await process.stdin.drain()  # type: ignore[union-attr]
        except Exception as exc:
            logger.error(
                "LSP notification failed: %s %s — %s",
                language.value,
                method,
                exc,
            )

    async def _read_response(self, process: object) -> dict | None:
        """Read a JSON-RPC response from the LSP server."""
        import asyncio
        import json

        try:
            stdout = process.stdout  # type: ignore[union-attr]

            # Read Content-Length header
            header = b""
            while True:
                line = await asyncio.wait_for(stdout.readline(), timeout=10.0)
                if line == b"\r\n" or line == b"\n":
                    break
                header += line

            content_length = 0
            for h_line in header.decode("utf-8").split("\r\n"):
                if h_line.lower().startswith("content-length:"):
                    content_length = int(h_line.split(":")[1].strip())

            if content_length > 0:
                body = await asyncio.wait_for(
                    stdout.readexactly(content_length),
                    timeout=10.0,
                )
                return json.loads(body.decode("utf-8"))

        except TimeoutError:
            logger.debug("LSP response timeout")
        except Exception as exc:
            logger.debug("LSP response read error: %s", exc)

        return None

    @staticmethod
    def _detect_language(file_path: str) -> LanguageId | None:
        """Detect language from file path."""
        ext_map: dict[str, LanguageId] = {
            ".py": LanguageId.PYTHON,
            ".pyi": LanguageId.PYTHON,
            ".ts": LanguageId.TYPESCRIPT,
            ".tsx": LanguageId.TYPESCRIPT,
            ".js": LanguageId.JAVASCRIPT,
            ".jsx": LanguageId.JAVASCRIPT,
            ".mjs": LanguageId.JAVASCRIPT,
            ".rs": LanguageId.RUST,
            ".go": LanguageId.GO,
            ".java": LanguageId.JAVA,
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return None

    @staticmethod
    def _read_file_content(file_path: str) -> str | None:
        """Read the contents of a file."""
        check = filesystem_sandbox.check_access(file_path, AccessType.READ)
        if not check.allowed:
            logger.warning("LSP sandbox denied read: %s — %s", file_path, check.reason)
            return None
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("File read error: %s — %s", file_path, exc)
            return None

    @staticmethod
    def _parse_location(data: dict | list | None) -> LocationInfo | None:
        """Parse an LSP location response."""
        if not data:
            return None

        # Use first element if array
        if isinstance(data, list):
            if not data:
                return None
            data = data[0]

        if not isinstance(data, dict):
            return None

        uri = data.get("uri", "")
        file_path = uri.replace("file://", "") if uri.startswith("file://") else uri

        range_data = data.get("range", {})
        start = range_data.get("start", {})

        return LocationInfo(
            file_path=file_path,
            line=start.get("line", 0),
            character=start.get("character", 0),
        )


# Global instance
lsp_integration = LSPIntegration()
