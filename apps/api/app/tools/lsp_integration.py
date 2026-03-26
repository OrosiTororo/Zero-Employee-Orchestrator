"""LSP 統合 — Language Server Protocol によるコード理解.

Language Server Protocol (LSP) を利用して、コード補完・定義ジャンプ・
参照検索・診断情報・フォーマットなどのコード理解機能を提供する。

対応言語:
- Python, TypeScript, JavaScript, Rust, Go, Java

各言語の LSP サーバーをサブプロセスとして起動・管理し、
JSON-RPC 経由で通信する。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LanguageId(str, Enum):
    """対応言語."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"


class LSPCapability(str, Enum):
    """LSP ケイパビリティ."""

    COMPLETION = "completion"
    HOVER = "hover"
    DEFINITION = "definition"
    REFERENCES = "references"
    DIAGNOSTICS = "diagnostics"
    FORMATTING = "formatting"
    RENAME = "rename"


class DiagnosticSeverity(str, Enum):
    """診断の重大度."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ServerStatus(str, Enum):
    """LSP サーバーの状態."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class LSPServerConfig:
    """LSP サーバー設定."""

    language: LanguageId = LanguageId.PYTHON
    command: str = ""
    args: list[str] = field(default_factory=list)
    root_path: str = "."
    capabilities: list[LSPCapability] = field(default_factory=list)


@dataclass
class Diagnostic:
    """診断情報."""

    file_path: str = ""
    line: int = 0
    character: int = 0
    message: str = ""
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    source: str = ""


@dataclass
class CompletionItem:
    """補完候補."""

    label: str = ""
    kind: str = "text"
    detail: str = ""
    documentation: str = ""


@dataclass
class HoverInfo:
    """ホバー情報."""

    contents: str = ""
    language: str = ""
    range_start: tuple[int, int] = (0, 0)
    range_end: tuple[int, int] = (0, 0)


@dataclass
class LocationInfo:
    """ファイル内位置情報."""

    file_path: str = ""
    line: int = 0
    character: int = 0


# デフォルトの LSP サーバー設定
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
    """LSP 統合サービス.

    言語ごとの LSP サーバーを管理し、コード理解機能を提供する。
    サーバーの起動・停止・リクエスト送信を一元的に管理する。
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
        """LSP サーバーの設定を登録・更新する.

        Args:
            config: LSP サーバー設定
        """
        self._servers[config.language] = config
        logger.info(
            "LSP サーバー設定登録: %s -> %s %s",
            config.language.value,
            config.command,
            " ".join(config.args),
        )

    async def start_server(self, language: LanguageId) -> bool:
        """LSP サーバーを起動する.

        サブプロセスとして LSP サーバーを起動し、initialize ハンドシェイクを行う。

        Args:
            language: 起動する言語のサーバー

        Returns:
            起動に成功したかどうか
        """
        config = self._servers.get(language)
        if not config:
            logger.error("LSP サーバー設定が見つかりません: %s", language.value)
            return False

        if self._running.get(language):
            logger.info("LSP サーバーは既に起動中: %s", language.value)
            return True

        self._status[language] = ServerStatus.STARTING

        try:
            import asyncio
            import shutil

            # コマンドの存在確認
            if not shutil.which(config.command):
                logger.warning(
                    "LSP サーバーコマンドが見つかりません: %s (言語: %s)",
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

            # initialize リクエスト送信
            await self._send_initialize(language, config.root_path)

            logger.info("LSP サーバー起動: %s (PID: %s)", language.value, process.pid)
            return True

        except FileNotFoundError:
            logger.error(
                "LSP サーバーコマンドが見つかりません: %s",
                config.command,
            )
            self._status[language] = ServerStatus.ERROR
            return False
        except Exception as exc:
            logger.error("LSP サーバー起動失敗: %s — %s", language.value, exc)
            self._status[language] = ServerStatus.ERROR
            return False

    async def stop_server(self, language: LanguageId) -> bool:
        """LSP サーバーを停止する.

        Args:
            language: 停止する言語のサーバー

        Returns:
            停止に成功したかどうか
        """
        if not self._running.get(language):
            return True

        process = self._processes.get(language)
        if process and hasattr(process, "terminate"):
            try:
                # shutdown リクエスト送信
                await self._send_request(language, "shutdown", {})
                await self._send_notification(language, "exit", {})
                process.terminate()  # type: ignore[union-attr]
            except Exception as exc:
                logger.warning("LSP サーバー停止中にエラー: %s — %s", language.value, exc)

        self._running[language] = False
        self._status[language] = ServerStatus.STOPPED
        self._processes.pop(language, None)
        logger.info("LSP サーバー停止: %s", language.value)
        return True

    async def get_diagnostics(self, file_path: str) -> list[Diagnostic]:
        """指定ファイルの診断情報を取得する.

        Args:
            file_path: 対象ファイルのパス

        Returns:
            診断情報のリスト
        """
        language = self._detect_language(file_path)
        if not language or not self._running.get(language):
            return []

        # textDocument/didOpen を送信して診断を取得
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

        # 診断は非同期通知で返るため、待機が必要
        # 実際の実装では通知ハンドラーで蓄積するが、ここではプレースホルダーを返す
        logger.info("診断リクエスト送信: %s", file_path)
        return []

    async def get_completions(
        self,
        file_path: str,
        line: int,
        character: int,
    ) -> list[CompletionItem]:
        """指定位置の補完候補を取得する.

        Args:
            file_path: 対象ファイルのパス
            line: 行番号（0-indexed）
            character: 列番号（0-indexed）

        Returns:
            補完候補のリスト
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
        """指定位置のホバー情報を取得する.

        Args:
            file_path: 対象ファイルのパス
            line: 行番号（0-indexed）
            character: 列番号（0-indexed）

        Returns:
            ホバー情報。取得できない場合は None。
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
        """指定位置のシンボルの定義元にジャンプする.

        Args:
            file_path: 対象ファイルのパス
            line: 行番号（0-indexed）
            character: 列番号（0-indexed）

        Returns:
            定義元の位置情報。取得できない場合は None。
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
        """指定位置のシンボルの全参照を検索する.

        Args:
            file_path: 対象ファイルのパス
            line: 行番号（0-indexed）
            character: 列番号（0-indexed）

        Returns:
            参照位置のリスト
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
        """ファイル全体をフォーマットする.

        Args:
            file_path: 対象ファイルのパス

        Returns:
            フォーマット済みテキスト。失敗時は None。
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

        # テキスト編集を適用
        content = self._read_file_content(file_path)
        if content is None:
            return None

        # 簡易的なテキスト編集適用（実際には range ベースの編集を行う）
        for edit in response:
            if isinstance(edit, dict) and "newText" in edit:
                return edit["newText"]

        return content

    def get_supported_languages(self) -> list[dict[str, object]]:
        """設定済みの言語一覧を返す.

        Returns:
            言語名・コマンド・ケイパビリティ・ステータスの辞書リスト
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
        """指定言語のサーバーステータスを返す.

        Args:
            language: 対象言語

        Returns:
            ステータス情報の辞書
        """
        config = self._servers.get(language)
        return {
            "language": language.value,
            "status": self._status.get(language, ServerStatus.STOPPED).value,
            "running": self._running.get(language, False),
            "command": config.command if config else "",
            "capabilities": ([c.value for c in config.capabilities] if config else []),
        }

    # --- 内部メソッド ---

    def _next_request_id(self) -> int:
        """JSON-RPC リクエスト ID を生成する."""
        self._request_id += 1
        return self._request_id

    async def _send_initialize(self, language: LanguageId, root_path: str) -> dict | None:
        """LSP initialize リクエストを送信する."""
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
        """LSP サーバーに JSON-RPC リクエストを送信する."""
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

            # レスポンスを読み取る
            response_data = await self._read_response(process)
            if response_data and isinstance(response_data, dict):
                return response_data.get("result")
            return response_data

        except Exception as exc:
            logger.error(
                "LSP リクエスト失敗: %s %s — %s",
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
        """LSP サーバーに JSON-RPC 通知を送信する（レスポンスなし）."""
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
                "LSP 通知失敗: %s %s — %s",
                language.value,
                method,
                exc,
            )

    async def _read_response(self, process: object) -> dict | None:
        """LSP サーバーからの JSON-RPC レスポンスを読み取る."""
        import asyncio
        import json

        try:
            stdout = process.stdout  # type: ignore[union-attr]

            # Content-Length ヘッダーの読み取り
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
            logger.debug("LSP レスポンスタイムアウト")
        except Exception as exc:
            logger.debug("LSP レスポンス読み取りエラー: %s", exc)

        return None

    @staticmethod
    def _detect_language(file_path: str) -> LanguageId | None:
        """ファイルパスから言語を推定する."""
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
        """ファイルの内容を読み取る."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("ファイル読み取りエラー: %s — %s", file_path, exc)
            return None

    @staticmethod
    def _parse_location(data: dict | list | None) -> LocationInfo | None:
        """LSP のロケーションレスポンスをパースする."""
        if not data:
            return None

        # 配列の場合は最初の要素を使用
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
