"""Plugin Loader — VSCode 的なプラグイン動的読み込み・環境解決基盤.

VSCode のエクステンションのように、ユーザーが自然言語で「browser-use を追加して」
「画像生成に Flux を使いたい」「音楽生成ツールを追加して」と言うだけで
プラグインをインストール・設定・有効化できる仕組み。

設計思想:
- **マニフェスト駆動**: プラグインは manifest.json で自己記述（依存関係・設定・権限）
- **環境自動解決**: pip パッケージ、API キー、環境変数を自動検出・セットアップ案内
- **軽量コア**: ZEO 本体は最小限。全ての拡張機能はプラグインとして後から追加
- **コミュニティ対応**: 誰でもプラグインを作成・公開・インストールできる
- **ツール非固定**: 特定ツールを推奨せず、ユーザーが自由に選択・切替可能
- **汎用カテゴリ**: ブラウザ操作・画像生成・音楽生成・コード生成等、あらゆる用途に対応
- **AI エージェント連携**: エージェント組織がタスクに最適なツールを動的に選択

ツールカテゴリ:
- browser-automation: ブラウザ自動操作 (browser-use, Playwright, Selenium, ...)
- image-generation: 画像生成 (DALL-E, Stable Diffusion, Flux, Midjourney, ...)
- video-generation: 動画生成 (Runway, Pika, Sora, ...)
- audio-generation: 音声合成 (OpenAI TTS, ElevenLabs, VOICEVOX, ...)
- music-generation: 音楽生成 (Suno, Udio, MusicGen, ...)
- code-generation: コード生成 (Cursor, Copilot, ...)
- data-analysis: データ分析 (pandas-ai, ...)
- document-processing: 文書処理 (OCR, PDF, ...)
- communication: コミュニケーション (Slack, Discord, ...)
- search: 検索 (Perplexity, Tavily, ...)
- three-d: 3D モデル (Meshy, TripoSR, ...)
- custom: ユーザー定義

プラグイン追加フロー:
1. ユーザー: 「browser-use を追加して」or 「画像生成ツールを追加して」
2. システム: カテゴリ・名前でレジストリ検索 → マニフェスト取得 → 依存関係チェック
3. システム: 不足パッケージのインストール案内 → API キー設定案内
4. システム: プラグイン登録 → ツールレジストリに登録 → AI エージェントが利用可能に
"""

from __future__ import annotations

import importlib
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# プラグイン要件の種別
# ---------------------------------------------------------------------------


class RequirementType(str, Enum):
    """プラグインが要求するリソースの種別."""

    PIP_PACKAGE = "pip_package"  # Python パッケージ
    SYSTEM_COMMAND = "system_command"  # OS コマンド (chromium 等)
    API_KEY = "api_key"  # 外部 API キー
    ENV_VAR = "env_var"  # 環境変数
    LLM_PROVIDER = "llm_provider"  # LLM プロバイダー
    BROWSER = "browser"  # ブラウザ実行環境


class RequirementStatus(str, Enum):
    SATISFIED = "satisfied"
    MISSING = "missing"
    OPTIONAL = "optional"


@dataclass
class PluginRequirement:
    """プラグインの 1 つの要件."""

    type: RequirementType
    name: str
    description: str = ""
    required: bool = True
    install_hint: str = ""  # 解決方法のヒント
    alternatives: list[str] = field(default_factory=list)  # 代替手段


@dataclass
class RequirementCheckResult:
    """要件チェックの結果."""

    requirement: PluginRequirement
    status: RequirementStatus
    detail: str = ""


@dataclass
class EnvironmentReport:
    """プラグインの環境チェック全体結果."""

    plugin_name: str
    all_satisfied: bool
    results: list[RequirementCheckResult]
    setup_instructions: list[str]  # ユーザー向けセットアップ手順


# ---------------------------------------------------------------------------
# プラグインテンプレートカタログ（コミュニティレジストリの代替）
# ---------------------------------------------------------------------------

# 既知のツール → プラグインマニフェストのマッピング
# ユーザーが「browser-use を追加して」と言った時にここから検索する
# 将来的にはリモートレジストリ (plugins.zeo.dev) から動的取得

_KNOWN_PLUGIN_TEMPLATES: dict[str, dict] = {
    "browser-use": {
        "slug": "browser-use",
        "name": "Browser Use - LLM Autonomous Browser Control",
        "name_ja": "Browser Use - LLM 自律ブラウザ操作",
        "description": (
            "LLM-driven autonomous web browsing. The AI agent sees screenshots "
            "and DOM, then clicks, types, scrolls like a human. "
            "Loop detection and auto-replanning included."
        ),
        "description_ja": (
            "LLM 駆動の自律的ウェブブラウジング。AI がスクリーンショットと "
            "DOM を見て判断し、クリック・入力・スクロールを実行。"
            "ループ検出・自動リプランニング機能付き。"
        ),
        "version": "0.12.x",
        "source_uri": "https://github.com/browser-use/browser-use",
        "pypi_package": "browser-use",
        "category": "browser-automation",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "browser-use",
                "required": True,
                "install_hint": "pip install browser-use",
            },
            {
                "type": "browser",
                "name": "chromium",
                "required": True,
                "install_hint": "uvx browser-use install  # or: playwright install chromium",
            },
            {
                "type": "llm_provider",
                "name": "LLM provider",
                "required": True,
                "description": "browser-use の AI 判断に LLM が必要",
                "install_hint": (
                    "以下のいずれかを設定:\n"
                    "  - BROWSER_USE_API_KEY (browser-use 専用、推奨)\n"
                    "  - OPENAI_API_KEY (OpenAI)\n"
                    "  - ANTHROPIC_API_KEY (Anthropic)\n"
                    "  - GEMINI_API_KEY (Google、無料枠あり)\n"
                    "  - Ollama (ローカル、無料)\n"
                    "  - g4f (API キー不要モード)"
                ),
                "alternatives": [
                    "BROWSER_USE_API_KEY",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "GEMINI_API_KEY",
                    "ollama",
                    "g4f",
                ],
            },
        ],
        "adapter": {
            "type": "browser-use",
            "module": "app.tools.browser_adapter",
            "class": "BrowserUseAdapter",
        },
        "settings_schema": {
            "max_steps": {"type": "integer", "default": 30, "min": 1, "max": 100},
            "timeout_seconds": {"type": "integer", "default": 300, "min": 10, "max": 600},
            "headless": {"type": "boolean", "default": True},
            "llm_provider": {
                "type": "string",
                "default": "auto",
                "enum": ["auto", "browser-use", "openai", "anthropic", "gemini", "ollama", "g4f"],
            },
        },
        "safety": {
            "requires_user_consent": True,
            "approval_required": True,
            "sandbox_execution": True,
            "dangerous_operations": ["autonomous_browse", "form_submit", "file_download"],
        },
    },
    "selenium": {
        "slug": "selenium",
        "name": "Selenium WebDriver",
        "name_ja": "Selenium WebDriver",
        "description": "Classic browser automation with Selenium WebDriver.",
        "description_ja": "Selenium WebDriver による従来型ブラウザ自動操作。",
        "version": "4.x",
        "source_uri": "https://github.com/SeleniumHQ/selenium",
        "pypi_package": "selenium",
        "category": "browser-automation",
        "license": "Apache-2.0",
        "requirements": [
            {
                "type": "pip_package",
                "name": "selenium",
                "required": True,
                "install_hint": "pip install selenium",
            },
            {
                "type": "system_command",
                "name": "chromedriver",
                "required": True,
                "install_hint": "pip install webdriver-manager",
            },
        ],
        "adapter": {
            "type": "selenium",
            "module": "app.tools.browser_adapter",
            "class": None,  # 未実装 — コミュニティ貢献を期待
        },
        "settings_schema": {
            "headless": {"type": "boolean", "default": True},
            "browser": {"type": "string", "default": "chrome", "enum": ["chrome", "firefox"]},
        },
    },
    "playwright-extra": {
        "slug": "playwright-extra",
        "name": "Playwright Enhanced",
        "name_ja": "Playwright 拡張",
        "description": "Extended Playwright automation with stealth and anti-detection.",
        "description_ja": "ステルス・アンチ検出機能付き Playwright 拡張自動操作。",
        "version": "1.x",
        "source_uri": "https://github.com/nicbou/playwright-extra",
        "pypi_package": "playwright",
        "category": "browser-automation",
        "license": "Apache-2.0",
        "requirements": [
            {
                "type": "pip_package",
                "name": "playwright",
                "required": True,
                "install_hint": "pip install playwright && playwright install",
            },
        ],
        "adapter": {
            "type": "builtin",
            "module": "app.tools.browser_adapter",
            "class": "BuiltinPlaywrightAdapter",
        },
    },
    "mcp-browser": {
        "slug": "mcp-browser",
        "name": "MCP Browser Tools",
        "name_ja": "MCP ブラウザツール",
        "description": "Browser automation via Model Context Protocol servers.",
        "description_ja": "MCP サーバー経由のブラウザ自動操作。",
        "version": "0.1.x",
        "source_uri": "https://github.com/anthropics/mcp",
        "pypi_package": None,
        "category": "browser-automation",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "mcp",
                "required": True,
                "install_hint": "pip install mcp",
            },
        ],
        "adapter": {"type": "mcp", "module": None, "class": None},
    },
    # ── 画像生成 ──────────────────────────────────────────────────────────
    "comfyui": {
        "slug": "comfyui",
        "name": "ComfyUI",
        "name_ja": "ComfyUI",
        "description": "Node-based Stable Diffusion GUI. Local image generation with full control.",
        "description_ja": "ノードベースの Stable Diffusion GUI。ローカルで画像生成。",
        "version": "latest",
        "source_uri": "https://github.com/comfyanonymous/ComfyUI",
        "pypi_package": None,
        "category": "image-generation",
        "license": "GPL-3.0",
        "requirements": [
            {
                "type": "system_command",
                "name": "python",
                "required": True,
                "install_hint": "git clone https://github.com/comfyanonymous/ComfyUI && cd ComfyUI && pip install -r requirements.txt",
            },
            {
                "type": "env_var",
                "name": "COMFYUI_URL",
                "required": True,
                "install_hint": "COMFYUI_URL=http://localhost:8188 (ComfyUI サーバーの URL)",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
        "settings_schema": {
            "base_url": {"type": "string", "default": "http://localhost:8188"},
        },
    },
    "flux": {
        "slug": "flux",
        "name": "Flux Image Generation",
        "name_ja": "Flux 画像生成",
        "description": "High-quality image generation via Flux models (Black Forest Labs).",
        "description_ja": "Flux モデルによる高品質画像生成。",
        "version": "latest",
        "source_uri": "https://github.com/black-forest-labs/flux",
        "pypi_package": "flux",
        "category": "image-generation",
        "license": "Apache-2.0",
        "requirements": [
            {
                "type": "api_key",
                "name": "BFL_API_KEY",
                "required": False,
                "install_hint": "BFL_API_KEY を設定 (API 経由の場合)。ローカル実行も可能。",
                "alternatives": ["BFL_API_KEY", "REPLICATE_API_TOKEN"],
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    # ── 音楽生成 ──────────────────────────────────────────────────────────
    "suno-api": {
        "slug": "suno-api",
        "name": "Suno Music Generation",
        "name_ja": "Suno 音楽生成",
        "description": "AI music generation via Suno. Create songs from text descriptions.",
        "description_ja": "Suno による AI 音楽生成。テキストから楽曲を作成。",
        "version": "latest",
        "source_uri": "https://github.com/SunoAI-API/Suno-API",
        "pypi_package": None,
        "category": "music-generation",
        "license": "MIT",
        "requirements": [
            {
                "type": "api_key",
                "name": "SUNO_COOKIE",
                "required": True,
                "install_hint": "Suno の Web UI からセッション Cookie を取得して SUNO_COOKIE に設定",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    "musicgen": {
        "slug": "musicgen",
        "name": "MusicGen (Meta)",
        "name_ja": "MusicGen (Meta)",
        "description": "Open-source music generation by Meta. Runs locally, no API key needed.",
        "description_ja": "Meta のオープンソース音楽生成。ローカル実行、API キー不要。",
        "version": "latest",
        "source_uri": "https://github.com/facebookresearch/audiocraft",
        "pypi_package": "audiocraft",
        "category": "music-generation",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "audiocraft",
                "required": True,
                "install_hint": "pip install audiocraft",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    # ── 音声合成 ──────────────────────────────────────────────────────────
    "voicevox": {
        "slug": "voicevox",
        "name": "VOICEVOX",
        "name_ja": "VOICEVOX",
        "description": "Free Japanese text-to-speech engine. Local execution, no API key.",
        "description_ja": "無料の日本語音声合成エンジン。ローカル実行、API キー不要。",
        "version": "latest",
        "source_uri": "https://github.com/VOICEVOX/voicevox_engine",
        "pypi_package": None,
        "category": "audio-generation",
        "license": "LGPL-3.0",
        "requirements": [
            {
                "type": "env_var",
                "name": "VOICEVOX_URL",
                "required": True,
                "install_hint": "VOICEVOX Engine を起動して VOICEVOX_URL=http://localhost:50021 を設定",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    # ── 検索・リサーチ ────────────────────────────────────────────────────
    "tavily": {
        "slug": "tavily",
        "name": "Tavily Search",
        "name_ja": "Tavily 検索",
        "description": "AI-optimized search API for agents. Fast, accurate web search.",
        "description_ja": "AI エージェント向け検索 API。高速・高精度の Web 検索。",
        "version": "latest",
        "source_uri": "https://github.com/tavily-ai/tavily-python",
        "pypi_package": "tavily-python",
        "category": "search",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "tavily-python",
                "required": True,
                "install_hint": "pip install tavily-python",
            },
            {
                "type": "api_key",
                "name": "TAVILY_API_KEY",
                "required": True,
                "install_hint": "https://tavily.com で API キーを取得",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    # ── データ分析 ────────────────────────────────────────────────────────
    "pandas-ai": {
        "slug": "pandas-ai",
        "name": "PandasAI",
        "name_ja": "PandasAI",
        "description": "Chat with your data using natural language. LLM-powered data analysis.",
        "description_ja": "自然言語でデータを分析。LLM 駆動のデータ分析。",
        "version": "latest",
        "source_uri": "https://github.com/Sinaptik-AI/pandas-ai",
        "pypi_package": "pandasai",
        "category": "data-analysis",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "pandasai",
                "required": True,
                "install_hint": "pip install pandasai",
            },
            {
                "type": "llm_provider",
                "name": "LLM provider",
                "required": True,
                "description": "データ分析の LLM が必要",
                "install_hint": "OPENAI_API_KEY または他の LLM プロバイダーを設定",
                "alternatives": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ollama", "g4f"],
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    # ── 3D モデル ─────────────────────────────────────────────────────────
    "triposr": {
        "slug": "triposr",
        "name": "TripoSR",
        "name_ja": "TripoSR",
        "description": "Fast 3D model generation from a single image. Open-source.",
        "description_ja": "1 枚の画像から高速 3D モデル生成。オープンソース。",
        "version": "latest",
        "source_uri": "https://github.com/VAST-AI-Research/TripoSR",
        "pypi_package": None,
        "category": "three-d",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "torch",
                "required": True,
                "install_hint": "pip install torch",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    # ── コミュニケーション ────────────────────────────────────────────────
    "slack-sdk": {
        "slug": "slack-sdk",
        "name": "Slack Integration",
        "name_ja": "Slack 連携",
        "description": "Send and receive messages via Slack. Bot and webhook support.",
        "description_ja": "Slack でのメッセージ送受信。Bot・Webhook 対応。",
        "version": "latest",
        "source_uri": "https://github.com/slackapi/python-slack-sdk",
        "pypi_package": "slack-sdk",
        "category": "communication",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "slack-sdk",
                "required": True,
                "install_hint": "pip install slack-sdk",
            },
            {
                "type": "api_key",
                "name": "SLACK_BOT_TOKEN",
                "required": True,
                "install_hint": "Slack App を作成して Bot Token を取得",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
}


# ---------------------------------------------------------------------------
# 汎用ツールレジストリ — AI エージェントがツールを動的に選択する基盤
# ---------------------------------------------------------------------------


class ToolRegistry:
    """あらゆるカテゴリのツールを統合管理するレジストリ.

    AI エージェント組織がタスクに最適なツールを動的に選択するための基盤。
    特定のツールを固定するのではなく、ユーザーがカテゴリごとに
    好みのツールを設定し、エージェントがそれを利用する。

    例:
    - 画像生成タスク → ユーザーが設定した画像生成ツール (ComfyUI or DALL-E or Flux)
    - ブラウザ操作タスク → ユーザーが設定したブラウザツール (browser-use or Playwright)
    - 音楽生成タスク → ユーザーが設定した音楽ツール (Suno or MusicGen)
    """

    def __init__(self) -> None:
        # カテゴリ → 登録済みツール名のリスト
        self._tools: dict[str, list[str]] = {}
        # カテゴリ → アクティブツール名
        self._active: dict[str, str] = {}
        # ツール名 → 設定
        self._configs: dict[str, dict] = {}

    def register_tool(
        self,
        slug: str,
        category: str,
        config: dict,
    ) -> None:
        """ツールをレジストリに登録する.

        Args:
            slug: ツール識別子
            category: ツールカテゴリ
            config: ツール設定（マニフェスト情報等）
        """
        if category not in self._tools:
            self._tools[category] = []
        if slug not in self._tools[category]:
            self._tools[category].append(slug)
        self._configs[slug] = {**config, "category": category}

        # そのカテゴリで初めてのツールならアクティブに設定
        if category not in self._active:
            self._active[category] = slug

        logger.info("ツール登録: %s (カテゴリ: %s)", slug, category)

    def unregister_tool(self, slug: str) -> bool:
        """ツールを登録解除する."""
        config = self._configs.pop(slug, None)
        if config is None:
            return False

        category = config["category"]
        if category in self._tools and slug in self._tools[category]:
            self._tools[category].remove(slug)

        # アクティブツールが削除されたら別のツールに切替
        if self._active.get(category) == slug:
            remaining = self._tools.get(category, [])
            self._active[category] = remaining[0] if remaining else ""

        return True

    def set_active_tool(self, category: str, slug: str) -> bool:
        """カテゴリのアクティブツールを切り替える.

        ユーザーが「画像生成は ComfyUI を使って」と言った場合、
        image-generation カテゴリのアクティブツールを comfyui に切り替える。
        """
        if category not in self._tools or slug not in self._tools[category]:
            return False
        self._active[category] = slug
        logger.info("アクティブツール変更: %s → %s", category, slug)
        return True

    def get_active_tool(self, category: str) -> str | None:
        """カテゴリのアクティブツールを取得する.

        AI エージェントが「画像生成をしたい」時に呼ぶ。
        """
        return self._active.get(category)

    def get_tool_config(self, slug: str) -> dict | None:
        """ツールの設定情報を取得する."""
        return self._configs.get(slug)

    def list_tools(self, category: str | None = None) -> list[dict]:
        """登録済みツール一覧を返す."""
        results = []
        for slug, config in self._configs.items():
            if category and config.get("category") != category:
                continue
            cat = config.get("category", "")
            results.append(
                {
                    "slug": slug,
                    "category": cat,
                    "name": config.get("name", slug),
                    "is_active": self._active.get(cat) == slug,
                    **{k: v for k, v in config.items() if k not in ("slug", "category")},
                }
            )
        return results

    def list_categories(self) -> list[dict]:
        """カテゴリ一覧とアクティブツールを返す."""
        return [
            {
                "category": cat,
                "active_tool": self._active.get(cat, ""),
                "tool_count": len(tools),
                "tools": tools,
            }
            for cat, tools in self._tools.items()
        ]

    def resolve_tool_for_task(self, task_description: str) -> dict | None:
        """タスクの説明文からカテゴリを推定し、アクティブツールを返す.

        AI エージェント組織がタスクを実行する際に呼ぶ。

        Args:
            task_description: タスクの自然言語記述

        Returns:
            ツール設定、またはマッチしない場合 None
        """
        desc_lower = task_description.lower()

        # カテゴリキーワードマッピング
        category_keywords: dict[str, list[str]] = {
            "browser-automation": [
                "ブラウザ",
                "web",
                "ウェブ",
                "スクレイピング",
                "クリック",
                "browser",
                "scrape",
                "navigate",
                "browse",
            ],
            "image-generation": [
                "画像",
                "イラスト",
                "写真",
                "image",
                "picture",
                "photo",
                "illustration",
                "生成",
                "描",
                "draw",
            ],
            "video-generation": [
                "動画",
                "ビデオ",
                "映像",
                "video",
                "movie",
                "animation",
            ],
            "audio-generation": [
                "音声",
                "読み上げ",
                "TTS",
                "speech",
                "voice",
                "ナレーション",
            ],
            "music-generation": [
                "音楽",
                "楽曲",
                "BGM",
                "music",
                "song",
                "melody",
            ],
            "code-generation": [
                "コード",
                "プログラム",
                "code",
                "programming",
                "implement",
            ],
            "data-analysis": [
                "データ分析",
                "グラフ",
                "統計",
                "data",
                "analysis",
                "chart",
                "CSV",
                "Excel",
            ],
            "search": [
                "検索",
                "調査",
                "リサーチ",
                "search",
                "research",
                "find",
            ],
            "three-d": [
                "3D",
                "モデル",
                "3d",
                "model",
                "メッシュ",
                "mesh",
            ],
            "communication": [
                "Slack",
                "Discord",
                "メッセージ",
                "通知",
                "message",
                "notify",
            ],
        }

        for category, keywords in category_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                active = self.get_active_tool(category)
                if active:
                    return self.get_tool_config(active)

        return None


# ---------------------------------------------------------------------------
# 環境チェッカー
# ---------------------------------------------------------------------------


class EnvironmentResolver:
    """プラグインの依存関係・環境要件を検証・解決する.

    各要件を検査し、不足しているものについてはセットアップ手順を生成する。
    """

    def check_pip_package(self, package_name: str) -> bool:
        """pip パッケージがインストール済みか確認する."""
        try:
            importlib.import_module(package_name.replace("-", "_"))
            return True
        except ImportError:
            return False

    def check_system_command(self, command: str) -> bool:
        """システムコマンドが利用可能か確認する."""
        import shutil

        return shutil.which(command) is not None

    def check_env_var(self, var_name: str) -> bool:
        """環境変数が設定されているか確認する."""
        import os

        return bool(os.environ.get(var_name, ""))

    def check_llm_provider(self, alternatives: list[str]) -> tuple[bool, str]:
        """LLM プロバイダーが少なくとも 1 つ利用可能か確認する.

        Returns:
            (利用可能か, 利用可能なプロバイダー名)
        """
        import os

        # API キー系
        for alt in alternatives:
            if alt in ("ollama", "g4f"):
                continue
            if os.environ.get(alt, ""):
                return True, alt

        # Ollama チェック
        if "ollama" in alternatives:
            try:
                from app.providers.ollama_provider import ollama_provider

                if ollama_provider:
                    return True, "ollama"
            except ImportError:
                pass

        # g4f チェック
        if "g4f" in alternatives:
            try:
                from app.providers.g4f_provider import g4f_provider

                if g4f_provider.available:
                    return True, "g4f"
            except ImportError:
                pass

        return False, ""

    def check_browser(self) -> bool:
        """ブラウザが利用可能か確認する."""
        import shutil

        browsers = ["chromium", "chromium-browser", "google-chrome", "chrome"]
        return any(shutil.which(b) is not None for b in browsers)

    def check_requirements(
        self,
        requirements: list[dict],
    ) -> EnvironmentReport:
        """プラグインの全要件をチェックし、レポートを生成する."""
        results: list[RequirementCheckResult] = []
        setup_instructions: list[str] = []
        all_satisfied = True

        for req_dict in requirements:
            req = PluginRequirement(
                type=RequirementType(req_dict["type"]),
                name=req_dict["name"],
                description=req_dict.get("description", ""),
                required=req_dict.get("required", True),
                install_hint=req_dict.get("install_hint", ""),
                alternatives=req_dict.get("alternatives", []),
            )

            status = RequirementStatus.SATISFIED
            detail = ""

            if req.type == RequirementType.PIP_PACKAGE:
                if self.check_pip_package(req.name):
                    detail = f"{req.name} はインストール済み"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} が見つかりません"
                    setup_instructions.append(f"パッケージをインストール: {req.install_hint}")

            elif req.type == RequirementType.SYSTEM_COMMAND:
                if self.check_system_command(req.name):
                    detail = f"{req.name} コマンドが利用可能"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} コマンドが見つかりません"
                    setup_instructions.append(f"コマンドをインストール: {req.install_hint}")

            elif req.type == RequirementType.API_KEY:
                if self.check_env_var(req.name):
                    detail = f"{req.name} が設定済み"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} が未設定"
                    setup_instructions.append(f"API キーを設定: {req.install_hint}")

            elif req.type == RequirementType.ENV_VAR:
                if self.check_env_var(req.name):
                    detail = f"{req.name} が設定済み"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} が未設定"
                    setup_instructions.append(f"環境変数を設定: {req.install_hint}")

            elif req.type == RequirementType.LLM_PROVIDER:
                available, provider_name = self.check_llm_provider(req.alternatives)
                if available:
                    detail = f"LLM プロバイダー利用可能: {provider_name}"
                else:
                    status = RequirementStatus.MISSING
                    detail = "利用可能な LLM プロバイダーがありません"
                    setup_instructions.append(f"LLM プロバイダーを設定:\n{req.install_hint}")

            elif req.type == RequirementType.BROWSER:
                if self.check_browser():
                    detail = "ブラウザが利用可能"
                else:
                    status = RequirementStatus.MISSING
                    detail = "ブラウザが見つかりません"
                    setup_instructions.append(f"ブラウザをインストール: {req.install_hint}")

            if status == RequirementStatus.MISSING and not req.required:
                status = RequirementStatus.OPTIONAL

            if status == RequirementStatus.MISSING and req.required:
                all_satisfied = False

            results.append(
                RequirementCheckResult(
                    requirement=req,
                    status=status,
                    detail=detail,
                )
            )

        return EnvironmentReport(
            plugin_name="",
            all_satisfied=all_satisfied,
            results=results,
            setup_instructions=setup_instructions,
        )


# ---------------------------------------------------------------------------
# プラグインローダー
# ---------------------------------------------------------------------------


class PluginLoader:
    """プラグインの検索・環境チェック・インストール・有効化を統合管理する.

    VSCode のエクステンション管理と同様に:
    1. 検索: ユーザーが名前やキーワードで検索（自然言語対応）
    2. チェック: 依存関係・環境要件を自動検査
    3. インストール: pip パッケージのインストール支援
    4. 有効化: アダプタ/サービスの登録と有効化
    5. ツール切替: カテゴリごとにアクティブツールを切り替え

    AI エージェント組織との連携:
    - エージェントは tool_registry.resolve_tool_for_task() でタスクに最適なツールを選択
    - ユーザーが設定したアクティブツールをエージェントが自動的に使用
    """

    def __init__(self) -> None:
        self._env_resolver = EnvironmentResolver()
        self._installed_plugins: dict[str, dict] = {}
        self.tool_registry = ToolRegistry()

    # ----- 検索 -----

    def search(self, query: str) -> list[dict]:
        """自然言語クエリでプラグインを検索する.

        ユーザーが「ブラウザ操作」「browser-use」「Web 自動化」等と
        入力したときに適切なプラグインを返す。

        Args:
            query: 検索クエリ（自然言語 or プラグイン名）

        Returns:
            マッチしたプラグインテンプレートのリスト
        """
        query_lower = query.lower()
        results = []

        for slug, template in _KNOWN_PLUGIN_TEMPLATES.items():
            # スラッグ・名前・説明・カテゴリでマッチ
            searchable = " ".join(
                [
                    slug,
                    template.get("name", ""),
                    template.get("name_ja", ""),
                    template.get("description", ""),
                    template.get("description_ja", ""),
                    template.get("category", ""),
                    template.get("pypi_package", "") or "",
                ]
            ).lower()

            if query_lower in searchable or any(word in searchable for word in query_lower.split()):
                results.append(
                    {
                        "slug": slug,
                        "name": template["name"],
                        "name_ja": template.get("name_ja", template["name"]),
                        "description": template["description"],
                        "description_ja": template.get("description_ja", template["description"]),
                        "version": template.get("version", ""),
                        "source_uri": template.get("source_uri", ""),
                        "category": template.get("category", ""),
                        "license": template.get("license", ""),
                        "installed": slug in self._installed_plugins,
                    }
                )

        return results

    def get_template(self, slug: str) -> dict | None:
        """プラグインテンプレートを取得する."""
        return _KNOWN_PLUGIN_TEMPLATES.get(slug)

    # ----- 環境チェック -----

    def check_environment(self, slug: str) -> EnvironmentReport:
        """プラグインの環境要件をチェックする.

        インストール前にユーザーに何が必要かを提示する。

        Args:
            slug: プラグインスラッグ

        Returns:
            環境チェックレポート
        """
        template = _KNOWN_PLUGIN_TEMPLATES.get(slug)
        if not template:
            return EnvironmentReport(
                plugin_name=slug,
                all_satisfied=False,
                results=[],
                setup_instructions=[f"プラグイン '{slug}' が見つかりません"],
            )

        requirements = template.get("requirements", [])
        report = self._env_resolver.check_requirements(requirements)
        report.plugin_name = template["name"]
        return report

    # ----- インストール -----

    async def install_plugin(
        self,
        slug: str,
        *,
        auto_install_packages: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """プラグインをインストールする.

        Args:
            slug: プラグインスラッグ
            auto_install_packages: pip パッケージを自動インストールするか
            dry_run: 実際にはインストールせず、手順のみ返す

        Returns:
            インストール結果
        """
        template = _KNOWN_PLUGIN_TEMPLATES.get(slug)
        if not template:
            return {
                "success": False,
                "error": f"プラグイン '{slug}' が見つかりません",
                "available_plugins": list(_KNOWN_PLUGIN_TEMPLATES.keys()),
            }

        # 環境チェック
        env_report = self.check_environment(slug)

        if dry_run:
            return {
                "success": False,
                "dry_run": True,
                "plugin": template["name"],
                "environment": {
                    "all_satisfied": env_report.all_satisfied,
                    "checks": [
                        {
                            "name": r.requirement.name,
                            "type": r.requirement.type.value,
                            "status": r.status.value,
                            "detail": r.detail,
                            "install_hint": r.requirement.install_hint,
                        }
                        for r in env_report.results
                    ],
                    "setup_instructions": env_report.setup_instructions,
                },
            }

        # pip パッケージの自動インストール
        if auto_install_packages and not env_report.all_satisfied:
            for result in env_report.results:
                if (
                    result.status == RequirementStatus.MISSING
                    and result.requirement.type == RequirementType.PIP_PACKAGE
                ):
                    package = result.requirement.name
                    logger.info("自動インストール: %s", package)
                    try:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", package],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=120,
                        )
                        result.status = RequirementStatus.SATISFIED
                        result.detail = f"{package} をインストールしました"
                    except Exception as exc:
                        logger.error("パッケージインストール失敗 %s: %s", package, exc)

            # 再チェック
            env_report = self.check_environment(slug)

        # アダプタ登録
        adapter_config = template.get("adapter", {})
        adapter_registered = False

        if adapter_config.get("class") and adapter_config.get("module"):
            try:
                module = importlib.import_module(adapter_config["module"])
                adapter_cls = getattr(module, adapter_config["class"])
                adapter_instance = adapter_cls()

                # ブラウザアダプタレジストリに登録
                from app.tools.browser_adapter import browser_adapter_registry

                browser_adapter_registry.register(slug, adapter_instance)
                adapter_registered = True
                logger.info("アダプタ登録完了: %s", slug)
            except Exception as exc:
                logger.warning("アダプタ登録失敗: %s — %s", slug, exc)

        self._installed_plugins[slug] = {
            "template": template,
            "adapter_registered": adapter_registered,
        }

        # ツールレジストリに登録（AI エージェントが利用可能に）
        category = template.get("category", "custom")
        self.tool_registry.register_tool(
            slug=slug,
            category=category,
            config={
                "name": template["name"],
                "name_ja": template.get("name_ja", template["name"]),
                "description": template["description"],
                "source_uri": template.get("source_uri", ""),
                "adapter": template.get("adapter", {}),
                "settings_schema": template.get("settings_schema", {}),
            },
        )

        return {
            "success": True,
            "plugin": template["name"],
            "slug": slug,
            "category": category,
            "adapter_registered": adapter_registered,
            "environment": {
                "all_satisfied": env_report.all_satisfied,
                "setup_instructions": env_report.setup_instructions,
            },
        }

    # ----- アンインストール -----

    def uninstall_plugin(self, slug: str) -> dict:
        """プラグインを登録解除する（pip パッケージは削除しない）."""
        if slug not in self._installed_plugins:
            return {"success": False, "error": f"プラグイン '{slug}' はインストールされていません"}

        # ブラウザアダプタレジストリからも解除
        try:
            from app.tools.browser_adapter import browser_adapter_registry

            browser_adapter_registry.unregister(slug)
        except Exception:
            pass

        # ツールレジストリからも解除
        self.tool_registry.unregister_tool(slug)

        del self._installed_plugins[slug]
        return {"success": True, "message": f"プラグイン '{slug}' を削除しました"}

    # ----- 一覧 -----

    def list_installed(self) -> list[dict]:
        """インストール済みプラグイン一覧を返す."""
        return [
            {
                "slug": slug,
                "name": info["template"]["name"],
                "adapter_registered": info["adapter_registered"],
            }
            for slug, info in self._installed_plugins.items()
        ]

    def list_available(self) -> list[dict]:
        """利用可能な全プラグイン一覧を返す."""
        return [
            {
                "slug": slug,
                "name": t["name"],
                "name_ja": t.get("name_ja", t["name"]),
                "description": t["description"],
                "description_ja": t.get("description_ja", t["description"]),
                "version": t.get("version", ""),
                "source_uri": t.get("source_uri", ""),
                "category": t.get("category", ""),
                "license": t.get("license", ""),
                "installed": slug in self._installed_plugins,
                "pypi_package": t.get("pypi_package"),
            }
            for slug, t in _KNOWN_PLUGIN_TEMPLATES.items()
        ]


# ---------------------------------------------------------------------------
# グローバルインスタンス
# ---------------------------------------------------------------------------

plugin_loader = PluginLoader()
