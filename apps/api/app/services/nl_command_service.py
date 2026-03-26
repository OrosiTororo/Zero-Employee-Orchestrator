"""Natural Language Command Processor — Shared NL control engine for GUI / CLI / TUI.

Parses natural language instructions from users and converts them into
appropriate service calls. This allows users to perform any operation
using only natural language from any interface (GUI / CLI / TUI).

Supported categories:
- Config (config): API keys, execution mode, language, security settings
- Ticket management (ticket): Create, list, update work requests
- Model management (model): List, update, switch, download models
- Skill management (skill): Add, remove, list skills/plugins/extensions
- Agent management (agent): Create, configure, list AI agents
- Security (security): Sandbox, PII, data protection settings
- Audit (audit): Log viewing, operation history
- Approval (approval): Pending approvals list, approve, reject
- Knowledge (knowledge): Search, add knowledge
- Media generation (media): Image, video, audio generation
- Browser automation (browser): Web automation
- System (system): Health check, update, restart
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CommandCategory(str, Enum):
    """Command category."""

    CONFIG = "config"
    TICKET = "ticket"
    MODEL = "model"
    SKILL = "skill"
    AGENT = "agent"
    SECURITY = "security"
    AUDIT = "audit"
    APPROVAL = "approval"
    KNOWLEDGE = "knowledge"
    MEDIA = "media"
    BROWSER = "browser"
    SYSTEM = "system"
    CONVERSATION = "conversation"  # Normal conversation (not a command)


class CommandAction(str, Enum):
    """Command action."""

    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    GET = "get"
    SET = "set"
    ENABLE = "enable"
    DISABLE = "disable"
    SEARCH = "search"
    GENERATE = "generate"
    APPROVE = "approve"
    REJECT = "reject"
    INSTALL = "install"
    UNINSTALL = "uninstall"
    DOWNLOAD = "download"
    STATUS = "status"
    HELP = "help"
    EXECUTE = "execute"


@dataclass
class ParsedCommand:
    """Parsed command."""

    category: CommandCategory
    action: CommandAction
    target: str = ""
    parameters: dict = field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class CommandResult:
    """Command execution result."""

    success: bool
    message: str
    data: dict = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Intent classification rules (keyword-based + pattern matching)
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: list[tuple[CommandCategory, CommandAction, list[str]]] = [
    # ── Config / Settings ──
    (
        CommandCategory.CONFIG,
        CommandAction.SET,
        [
            r"(?:設定|config).*(?:変更|set|change|切替|切り替え|を|に)",
            r"(?:api|API)\s*(?:key|キー).*(?:設定|set|入力|登録)",
            r"(?:実行モード|execution.?mode).*(?:変更|切替|set)",
            r"(?:言語|language).*(?:変更|切替|set|change)",
            r"(?:を|に)\s*(?:使う|使って|使用|利用|切替|切り替え)",
            r"(?:Gemini|OpenAI|Anthropic|Claude|Ollama|GPT).*(?:使う|使って|切替|設定)",
            r"(?:サブスクリプション|subscription).*(?:モード|mode)",
            r"(?:無料|free|フリー).*(?:モード|mode|で使う)",
            r"set\s+\w+",
        ],
    ),
    (
        CommandCategory.CONFIG,
        CommandAction.GET,
        [
            r"(?:設定|config).*(?:確認|表示|見せて|一覧|show|list|get)",
            r"(?:今|現在).*(?:設定|config|モード|mode)",
            r"(?:何|どの).*(?:モデル|model|プロバイダ|provider).*(?:使って|利用)",
        ],
    ),
    # ── Ticket ──
    (
        CommandCategory.TICKET,
        CommandAction.CREATE,
        [
            r"(?:チケット|ticket|業務|タスク).*(?:作成|作って|create|新規|追加|登録)",
            r"(?:依頼|お願い|やって|やりたい|してほしい|して欲しい|してください)",
            r"(?:〜を|を).*(?:して|実行|処理|分析|調査|作成|作って|生成)",
        ],
    ),
    (
        CommandCategory.TICKET,
        CommandAction.LIST,
        [
            r"(?:チケット|ticket|業務|タスク).*(?:一覧|list|表示|確認|見せて)",
            r"(?:今|現在).*(?:チケット|ticket|業務|タスク)",
        ],
    ),
    (
        CommandCategory.TICKET,
        CommandAction.GET,
        [
            r"(?:チケット|ticket).*(?:詳細|detail|状態|status)",
        ],
    ),
    # ── Model ──
    (
        CommandCategory.MODEL,
        CommandAction.LIST,
        [
            r"(?:モデル|model).*(?:一覧|list|表示|確認|見せて|何がある)",
            r"(?:利用可能|available).*(?:モデル|model)",
        ],
    ),
    (
        CommandCategory.MODEL,
        CommandAction.UPDATE,
        [
            r"(?:モデル|model).*(?:更新|update|アップデート|refresh|最新)",
            r"(?:カタログ|catalog).*(?:更新|update|refresh)",
        ],
    ),
    (
        CommandCategory.MODEL,
        CommandAction.DOWNLOAD,
        [
            r"(?:モデル|model).*(?:ダウンロード|download|pull|取得|インストール)",
            r"(?:pull|ダウンロード)\s+\S+",
        ],
    ),
    (
        CommandCategory.MODEL,
        CommandAction.SET,
        [
            r"(?:モデル|model).*(?:変更|切替|set|change|switch)",
            r"(?:デフォルト|default).*(?:モデル|model)",
        ],
    ),
    # ── Skill / Plugin / Extension ──
    (
        CommandCategory.SKILL,
        CommandAction.LIST,
        [
            r"(?:スキル|skill|プラグイン|plugin|拡張|extension).*(?:一覧|list|表示|確認)",
        ],
    ),
    (
        CommandCategory.SKILL,
        CommandAction.INSTALL,
        [
            r"(?:スキル|skill|プラグイン|plugin|拡張|extension).*(?:追加|add|インストール|install|有効|enable)",
            r"(?:追加|add|インストール|install).*(?:スキル|skill|プラグイン|plugin|拡張|extension)",
        ],
    ),
    (
        CommandCategory.SKILL,
        CommandAction.UNINSTALL,
        [
            r"(?:スキル|skill|プラグイン|plugin|拡張|extension).*(?:削除|remove|アンインストール|uninstall|無効|disable)",
        ],
    ),
    (
        CommandCategory.SKILL,
        CommandAction.GENERATE,
        [
            r"(?:スキル|skill).*(?:生成|作成|generate|作って|create)",
            r"(?:新しい|new).*(?:スキル|skill)",
        ],
    ),
    # ── Agent ──
    (
        CommandCategory.AGENT,
        CommandAction.LIST,
        [
            r"(?:エージェント|agent|AI).*(?:一覧|list|表示|確認|見せて)",
        ],
    ),
    (
        CommandCategory.AGENT,
        CommandAction.CREATE,
        [
            r"(?:エージェント|agent|AI).*(?:作成|作って|create|追加|新規)",
        ],
    ),
    # ── Security ──
    (
        CommandCategory.SECURITY,
        CommandAction.STATUS,
        [
            r"(?:セキュリティ|security).*(?:状態|status|確認|表示|見せて)",
        ],
    ),
    (
        CommandCategory.SECURITY,
        CommandAction.SET,
        [
            r"(?:セキュリティ|security|サンドボックス|sandbox|PII|データ保護|data.?protection).*(?:設定|変更|切替|set|change)",
            r"(?:ワークスペース|workspace).*(?:隔離|isolation|設定)",
            r"(?:フォルダ|folder|ディレクトリ|directory).*(?:許可|allow|追加|add)",
        ],
    ),
    # ── Approval ──
    (
        CommandCategory.APPROVAL,
        CommandAction.LIST,
        [
            r"(?:承認|approval).*(?:待ち|pending|一覧|list|確認)",
        ],
    ),
    (
        CommandCategory.APPROVAL,
        CommandAction.APPROVE,
        [
            r"(?:承認|approve|許可)(?:する|して)",
        ],
    ),
    (
        CommandCategory.APPROVAL,
        CommandAction.REJECT,
        [
            r"(?:却下|reject|拒否|deny)(?:する|して)",
        ],
    ),
    # ── Audit ──
    (
        CommandCategory.AUDIT,
        CommandAction.LIST,
        [
            r"(?:監査|audit|ログ|log).*(?:表示|見せて|確認|一覧|list)",
            r"(?:操作|operation).*(?:履歴|history)",
        ],
    ),
    # ── Knowledge ──
    (
        CommandCategory.KNOWLEDGE,
        CommandAction.SEARCH,
        [
            r"(?:ナレッジ|knowledge|知識).*(?:検索|search|探して|調べて)",
        ],
    ),
    (
        CommandCategory.KNOWLEDGE,
        CommandAction.CREATE,
        [
            r"(?:ナレッジ|knowledge|知識).*(?:追加|add|登録|保存|store)",
        ],
    ),
    # ── Media ──
    (
        CommandCategory.MEDIA,
        CommandAction.GENERATE,
        [
            r"(?:画像|image|イメージ).*(?:生成|作成|作って|generate|create)",
            r"(?:動画|video|ビデオ).*(?:生成|作成|作って|generate|create)",
            r"(?:音声|audio|音楽|music).*(?:生成|作成|作って|generate|create)",
        ],
    ),
    # ── Browser ──
    (
        CommandCategory.BROWSER,
        CommandAction.EXECUTE,
        [
            r"(?:ブラウザ|browser|web|ウェブ).*(?:開いて|操作|アクセス|open|navigate)",
            r"(?:ページ|page|サイト|site).*(?:開いて|表示|確認|チェック)",
        ],
    ),
    # ── System ──
    (
        CommandCategory.SYSTEM,
        CommandAction.STATUS,
        [
            r"(?:システム|system|サーバー|server).*(?:状態|status|確認|ヘルス|health)",
        ],
    ),
    (
        CommandCategory.SYSTEM,
        CommandAction.UPDATE,
        [
            r"(?:アップデート|update|更新).*(?:ZEO|システム|system|本体)",
            r"(?:ZEO|システム|system|本体).*(?:アップデート|update|更新)",
        ],
    ),
    (
        CommandCategory.SYSTEM,
        CommandAction.HELP,
        [
            r"(?:ヘルプ|help|使い方|how.?to|何ができる|できること|機能)",
        ],
    ),
]


class NLCommandProcessor:
    """Natural language command processor.

    Can be called from all interfaces (GUI / CLI / TUI).
    Parses natural language input and executes appropriate actions.
    """

    def __init__(self) -> None:
        self._compiled_patterns: list[tuple[CommandCategory, CommandAction, list[re.Pattern]]] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile intent patterns."""
        for category, action, patterns in _INTENT_PATTERNS:
            compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
            self._compiled_patterns.append((category, action, compiled))

    def parse(self, text: str) -> ParsedCommand:
        """Parse a command from natural language text.

        Args:
            text: Natural language input from the user

        Returns:
            Parsed command (CONVERSATION if confidence is low)
        """
        text = text.strip()
        if not text:
            return ParsedCommand(
                category=CommandCategory.CONVERSATION,
                action=CommandAction.HELP,
                raw_text=text,
                confidence=0.0,
            )

        best_match: ParsedCommand | None = None
        best_score = 0

        for category, action, patterns in self._compiled_patterns:
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    score = len(match.group(0)) / max(len(text), 1)
                    if score > best_score:
                        best_score = score
                        params = self._extract_parameters(text, category, action)
                        best_match = ParsedCommand(
                            category=category,
                            action=action,
                            target=params.pop("target", ""),
                            parameters=params,
                            raw_text=text,
                            confidence=min(1.0, score + 0.3),
                        )

        if best_match and best_match.confidence >= 0.2:
            return best_match

        # If no match, treat as normal conversation
        return ParsedCommand(
            category=CommandCategory.CONVERSATION,
            action=CommandAction.EXECUTE,
            raw_text=text,
            confidence=0.0,
        )

    def _extract_parameters(
        self, text: str, category: CommandCategory, action: CommandAction
    ) -> dict:
        """Extract parameters from text."""
        params: dict = {}

        # Extract model name
        model_match = re.search(
            r"(?:gemini|gpt|claude|llama|mistral|qwen|phi|deepseek)"
            r"(?:[-/:][\w.]+)?",
            text,
            re.IGNORECASE,
        )
        if model_match:
            params["model"] = model_match.group(0)

        # Provider name
        provider_match = re.search(
            r"(?:OpenAI|Anthropic|Google|Gemini|Ollama|OpenRouter|g4f)",
            text,
            re.IGNORECASE,
        )
        if provider_match:
            params["provider"] = provider_match.group(0).lower()

        # Language setting
        lang_match = re.search(r"(?:日本語|英語|中国語|Japanese|English|Chinese|ja|en|zh)", text)
        if lang_match:
            lang_map = {
                "日本語": "ja",
                "英語": "en",
                "中国語": "zh",
                "japanese": "ja",
                "english": "en",
                "chinese": "zh",
            }
            params["language"] = lang_map.get(lang_match.group(0).lower(), lang_match.group(0))

        # Execution mode
        mode_match = re.search(
            r"(?:quality|speed|cost|free|subscription|品質|高速|低コスト|無料|サブスクリプション)",
            text,
            re.IGNORECASE,
        )
        if mode_match:
            mode_map = {
                "品質": "quality",
                "高速": "speed",
                "低コスト": "cost",
                "無料": "free",
                "サブスクリプション": "subscription",
            }
            params["mode"] = mode_map.get(mode_match.group(0), mode_match.group(0).lower())

        # Sandbox level
        sandbox_match = re.search(r"(?:strict|moderate|permissive)", text, re.IGNORECASE)
        if sandbox_match:
            params["sandbox_level"] = sandbox_match.group(0).lower()

        # Skill/plugin name
        if category == CommandCategory.SKILL:
            # Extract name from "add ~" pattern
            name_match = re.search(
                r"[「『]([^」』]+)[」』]|(\S+)(?:を|の)(?:追加|インストール|削除)",
                text,
            )
            if name_match:
                params["target"] = (name_match.group(1) or name_match.group(2)).strip()

        return params

    async def execute(self, command: ParsedCommand) -> CommandResult:
        """Execute a parsed command.

        Args:
            command: Parsed command

        Returns:
            Execution result
        """
        handler_map = {
            CommandCategory.CONFIG: self._handle_config,
            CommandCategory.TICKET: self._handle_ticket,
            CommandCategory.MODEL: self._handle_model,
            CommandCategory.SKILL: self._handle_skill,
            CommandCategory.SECURITY: self._handle_security,
            CommandCategory.APPROVAL: self._handle_approval,
            CommandCategory.AUDIT: self._handle_audit,
            CommandCategory.SYSTEM: self._handle_system,
            CommandCategory.KNOWLEDGE: self._handle_knowledge,
            CommandCategory.MEDIA: self._handle_media,
            CommandCategory.AGENT: self._handle_agent,
        }

        handler = handler_map.get(command.category)
        if handler:
            try:
                return await handler(command)
            except Exception as exc:
                logger.error("Command execution failed: %s", exc)
                return CommandResult(
                    success=False,
                    message=f"Error occurred during command execution: {exc}",
                )

        # CONVERSATION or BROWSER — delegate to LLM
        return CommandResult(
            success=True,
            message="",
            data={"delegate_to_llm": True, "raw_text": command.raw_text},
        )

    # ------------------------------------------------------------------
    # Category handlers
    # ------------------------------------------------------------------

    async def _handle_config(self, cmd: ParsedCommand) -> CommandResult:
        """Configuration change handler."""
        from app.core.config_manager import (
            get_all_config,
            set_config_value,
        )

        if cmd.action == CommandAction.GET:
            config = get_all_config()
            lines = []
            for key, info in config.items():
                if info["is_set"]:
                    lines.append(f"  {key} = {info['value']}")
            return CommandResult(
                success=True,
                message="Current settings:\n" + "\n".join(lines) if lines else "No settings configured",
                data={"config": config},
            )

        if cmd.action == CommandAction.SET:
            params = cmd.parameters
            changes = []

            # Execution mode change
            if "mode" in params:
                set_config_value("DEFAULT_EXECUTION_MODE", params["mode"])
                changes.append(f"Execution mode -> {params['mode']}")

            # Language change
            if "language" in params:
                set_config_value("LANGUAGE", params["language"])
                changes.append(f"Language -> {params['language']}")

            # Provider/model related
            if "provider" in params:
                provider = params["provider"]
                provider_key_map = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "gemini": "GEMINI_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                }
                if provider == "ollama":
                    set_config_value("DEFAULT_EXECUTION_MODE", "free")
                    changes.append("Execution mode -> free (Ollama)")
                elif provider == "g4f":
                    set_config_value("DEFAULT_EXECUTION_MODE", "subscription")
                    set_config_value("USE_G4F", "true")
                    changes.append("Execution mode -> subscription (g4f)")
                elif provider in provider_key_map:
                    key_name = provider_key_map[provider]
                    if key_name not in [k for k, v in get_all_config().items() if v["is_set"]]:
                        return CommandResult(
                            success=False,
                            message=(
                                f"An API key is required to use {provider}.\n"
                                f"Setup command: `zero-employee config set {key_name} <your-key>`"
                            ),
                            suggestions=[
                                f"zero-employee config set {key_name} <your-key>",
                                "Ollama does not require an API key",
                            ],
                        )
                    set_config_value("DEFAULT_EXECUTION_MODE", "quality")
                    changes.append(f"Provider -> {provider}")

            # Sandbox level
            if "sandbox_level" in params:
                changes.append(f"Sandbox -> {params['sandbox_level']}")

            if changes:
                return CommandResult(
                    success=True,
                    message="Settings changed:\n" + "\n".join(f"  ✓ {c}" for c in changes),
                    data={"changes": changes},
                )

            # Unable to determine what to change
            return CommandResult(
                success=False,
                message="Could not determine what settings to change.",
                suggestions=[
                    '"Change execution mode to free"',
                    '"Configure to use Gemini"',
                    '"Change language to English"',
                    '"Show me the settings"',
                ],
            )

        return CommandResult(success=False, message="Could not recognize the config command")

    async def _handle_ticket(self, cmd: ParsedCommand) -> CommandResult:
        """Ticket management handler."""
        if cmd.action == CommandAction.CREATE:
            return CommandResult(
                success=True,
                message="",
                data={
                    "delegate_to_llm": True,
                    "context": "ticket_creation",
                    "raw_text": cmd.raw_text,
                    "api_endpoint": "POST /api/v1/tickets",
                },
            )

        if cmd.action == CommandAction.LIST:
            return CommandResult(
                success=True,
                message="",
                data={
                    "api_call": {"method": "GET", "path": "/api/v1/tickets"},
                },
            )

        return CommandResult(
            success=True,
            message="",
            data={"delegate_to_llm": True, "raw_text": cmd.raw_text},
        )

    async def _handle_model(self, cmd: ParsedCommand) -> CommandResult:
        """Model management handler."""
        if cmd.action == CommandAction.LIST:
            from app.providers.model_registry import get_model_registry

            registry = get_model_registry()
            models = registry.list_models()
            lines = []
            for m in models:
                api_id = m.latest_model_id or m.id
                status = "✓" if not m.deprecated else "✗ (deprecated)"
                lines.append(f"  {status} {m.display_name} ({api_id})")
            return CommandResult(
                success=True,
                message=f"Registered models ({len(models)} items):\n" + "\n".join(lines),
                data={"models": [{"id": m.id, "name": m.display_name} for m in models]},
            )

        if cmd.action == CommandAction.UPDATE:
            from app.providers.model_registry import get_model_registry

            registry = get_model_registry()
            updated = await registry.refresh_catalog()
            if updated:
                return CommandResult(
                    success=True,
                    message=f"Model catalog updated ({len(updated)} items):\n"
                    + "\n".join(f"  ✓ {k}: {v}" for k, v in updated.items()),
                    data={"updated": updated},
                )
            return CommandResult(
                success=True,
                message="Model catalog is up to date.",
            )

        if cmd.action == CommandAction.DOWNLOAD:
            model_name = cmd.parameters.get("model", cmd.target)
            if not model_name:
                return CommandResult(
                    success=False,
                    message="Please specify the model name to download.",
                    suggestions=['"Download qwen3:8b"', '"Pull llama3"'],
                )
            return CommandResult(
                success=True,
                message=f"Starting download of model '{model_name}'...",
                data={
                    "api_call": {
                        "method": "POST",
                        "path": "/api/v1/ollama/pull",
                        "body": {"model": model_name},
                    },
                },
            )

        return CommandResult(success=True, message="", data={"delegate_to_llm": True})

    async def _handle_skill(self, cmd: ParsedCommand) -> CommandResult:
        """Skill management handler."""
        if cmd.action == CommandAction.LIST:
            return CommandResult(
                success=True,
                message="",
                data={
                    "api_call": {"method": "GET", "path": "/api/v1/registry/skills"},
                },
            )

        if cmd.action in (CommandAction.INSTALL, CommandAction.ENABLE):
            target = cmd.parameters.get("target", cmd.target)
            if target:
                return CommandResult(
                    success=True,
                    message=f"Installing skill '{target}'...",
                    data={
                        "api_call": {
                            "method": "POST",
                            "path": f"/api/v1/registry/plugins/{target}/install",
                        },
                    },
                )
            return CommandResult(
                success=False,
                message="Please specify the skill/plugin name to install.",
                suggestions=[
                    '"Add the browser-use plugin"',
                    '"Enable AI Secretary"',
                ],
            )

        if cmd.action == CommandAction.GENERATE:
            return CommandResult(
                success=True,
                message="",
                data={
                    "delegate_to_llm": True,
                    "context": "skill_generation",
                    "raw_text": cmd.raw_text,
                    "api_endpoint": "POST /api/v1/registry/skills/generate",
                },
            )

        return CommandResult(success=True, message="", data={"delegate_to_llm": True})

    async def _handle_security(self, cmd: ParsedCommand) -> CommandResult:
        """Security settings handler."""
        if cmd.action == CommandAction.STATUS:
            from app.security.data_protection import data_protection_guard
            from app.security.sandbox import filesystem_sandbox
            from app.security.workspace_isolation import workspace_isolation

            sb = filesystem_sandbox.config
            dp = data_protection_guard.config

            return CommandResult(
                success=True,
                message=(
                    "Security settings:\n"
                    f"  [Workspace] Access scope: {workspace_isolation.get_access_scope().value}\n"
                    f"  [Sandbox] Level: {sb.level.value}\n"
                    f"  [Data Protection] Policy: {dp.transfer_policy.value}\n"
                    f"  [PII Detection] Auto-detect: {'enabled' if dp.pii_auto_detect else 'disabled'}\n"
                    f"  [Password] Upload: {'blocked' if dp.password_upload_blocked else 'allowed'}"
                ),
                data={
                    "workspace": {"scope": workspace_isolation.get_access_scope().value},
                    "sandbox": {"level": sb.level.value},
                    "data_protection": {"policy": dp.transfer_policy.value},
                },
            )

        if cmd.action == CommandAction.SET:
            return CommandResult(
                success=True,
                message="",
                data={
                    "api_call": {"method": "PUT", "path": "/api/v1/security/settings"},
                    "delegate_to_llm": True,
                    "raw_text": cmd.raw_text,
                },
            )

        return CommandResult(success=True, message="", data={"delegate_to_llm": True})

    async def _handle_approval(self, cmd: ParsedCommand) -> CommandResult:
        """Approval management handler."""
        if cmd.action == CommandAction.LIST:
            return CommandResult(
                success=True,
                message="",
                data={
                    "api_call": {"method": "GET", "path": "/api/v1/approvals/pending"},
                },
            )
        return CommandResult(
            success=True,
            message="",
            data={"delegate_to_llm": True, "raw_text": cmd.raw_text},
        )

    async def _handle_audit(self, cmd: ParsedCommand) -> CommandResult:
        """Audit log handler."""
        return CommandResult(
            success=True,
            message="",
            data={
                "api_call": {"method": "GET", "path": "/api/v1/audit"},
            },
        )

    async def _handle_system(self, cmd: ParsedCommand) -> CommandResult:
        """System management handler."""
        if cmd.action == CommandAction.STATUS:
            return CommandResult(
                success=True,
                message="",
                data={
                    "api_call": {"method": "GET", "path": "/healthz"},
                },
            )

        if cmd.action == CommandAction.HELP:
            return CommandResult(
                success=True,
                message=(
                    "Available operations in Zero-Employee Orchestrator:\n\n"
                    "  [Settings]\n"
                    '    "Configure to use Gemini" "Change execution mode to free"\n'
                    '    "Change language to English" "Show me the settings"\n\n'
                    "  [Tickets / Work]\n"
                    '    "Create a competitive analysis report" "Show me the ticket list"\n\n'
                    "  [Model Management]\n"
                    '    "Show available models" "Update models"\n'
                    '    "Download qwen3:8b"\n\n'
                    "  [Skills / Plugins]\n"
                    '    "Show skill list" "Add browser-use"\n'
                    '    "Generate a web scraping skill"\n\n'
                    "  [Security]\n"
                    '    "Check security settings" "Change sandbox to moderate"\n\n'
                    "  [Approvals]\n"
                    '    "Show pending approvals"\n\n'
                    "  [Media Generation]\n"
                    '    "Generate an office image"\n\n'
                    "  [System]\n"
                    '    "Run health check" "Run update"\n\n'
                    "  Any other work request can also be made in natural language."
                ),
            )

        if cmd.action == CommandAction.UPDATE:
            return CommandResult(
                success=True,
                message="Checking for system updates...",
                data={
                    "api_call": {"method": "POST", "path": "/api/v1/models/auto-update"},
                },
            )

        return CommandResult(success=True, message="", data={"delegate_to_llm": True})

    async def _handle_knowledge(self, cmd: ParsedCommand) -> CommandResult:
        """Knowledge management handler."""
        return CommandResult(
            success=True,
            message="",
            data={
                "api_call": {"method": "GET", "path": "/api/v1/knowledge"},
                "delegate_to_llm": True,
                "raw_text": cmd.raw_text,
            },
        )

    async def _handle_media(self, cmd: ParsedCommand) -> CommandResult:
        """Media generation handler."""
        return CommandResult(
            success=True,
            message="",
            data={
                "delegate_to_llm": True,
                "context": "media_generation",
                "raw_text": cmd.raw_text,
                "api_endpoint": "POST /api/v1/media/generate",
            },
        )

    async def _handle_agent(self, cmd: ParsedCommand) -> CommandResult:
        """Agent management handler."""
        if cmd.action == CommandAction.LIST:
            return CommandResult(
                success=True,
                message="",
                data={
                    "api_call": {"method": "GET", "path": "/api/v1/agents"},
                },
            )
        return CommandResult(
            success=True,
            message="",
            data={"delegate_to_llm": True, "raw_text": cmd.raw_text},
        )


# Global instance
nl_command_processor = NLCommandProcessor()
