"""Plugin Loader — Cowork-style dynamic plugin loading and environment resolution.

Users can simply say in natural language "add browser-use",
"I want to use Flux for image generation", or "add a music generation tool"
to install, configure, and enable plugins.

Design philosophy:
- **Manifest-driven**: Plugins self-describe via manifest.json (dependencies, settings, permissions)
- **Auto environment resolution**: Auto-detect pip packages, API keys, env vars and guide setup
- **Lightweight core**: ZEO core is minimal. All extensions are added later as plugins
- **Community-ready**: Anyone can create, publish, and install plugins
- **No tool lock-in**: No specific tool is recommended; users freely choose and switch
- **Universal categories**: Covers all use cases: browser automation, image/music/code generation, etc.
- **AI agent integration**: Agent organization dynamically selects optimal tools per task

Tool categories:
- browser-automation: Browser automation (browser-use, Playwright, Selenium, ...)
- image-generation: Image generation (DALL-E, Stable Diffusion, Flux, Midjourney, ...)
- video-generation: Video generation (Runway, Pika, Sora, ...)
- audio-generation: Speech synthesis (OpenAI TTS, ElevenLabs, VOICEVOX, ...)
- music-generation: Music generation (Suno, Udio, MusicGen, ...)
- code-generation: Code generation (Cursor, Copilot, ...)
- data-analysis: Data analysis (pandas-ai, ...)
- document-processing: Document processing (OCR, PDF, ...)
- communication: Communication (Slack, Discord, ...)
- social-media: Social media (Twitter/X, Instagram, TikTok, YouTube, ...)
- video-generation: Video generation (Runway ML, Pika, ...)
- agent-framework: External AI agents (CrewAI, AutoGen, LangChain, OpenClaw, Dify, ...)
- search: Search (Perplexity, Tavily, ...)
- three-d: 3D models (Meshy, TripoSR, ...)
- custom: User-defined

Plugin installation flow:
1. User: "add browser-use" or "add an image generation tool"
2. System: Search registry by category/name -> fetch manifest -> check dependencies
3. System: Guide missing package installation -> guide API key setup
4. System: Register plugin -> register in tool registry -> available for AI agents
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
# Plugin requirement types
# ---------------------------------------------------------------------------


class RequirementType(str, Enum):
    """Type of resource required by a plugin."""

    PIP_PACKAGE = "pip_package"  # Python package
    SYSTEM_COMMAND = "system_command"  # OS command (chromium, etc.)
    API_KEY = "api_key"  # External API key
    ENV_VAR = "env_var"  # Environment variable
    LLM_PROVIDER = "llm_provider"  # LLM provider
    BROWSER = "browser"  # Browser runtime environment


class RequirementStatus(str, Enum):
    SATISFIED = "satisfied"
    MISSING = "missing"
    OPTIONAL = "optional"


@dataclass
class PluginRequirement:
    """A single requirement for a plugin."""

    type: RequirementType
    name: str
    description: str = ""
    required: bool = True
    install_hint: str = ""  # Hint for resolution
    alternatives: list[str] = field(default_factory=list)  # Alternative options


@dataclass
class RequirementCheckResult:
    """Result of a requirement check."""

    requirement: PluginRequirement
    status: RequirementStatus
    detail: str = ""


@dataclass
class EnvironmentReport:
    """Overall environment check result for a plugin."""

    plugin_name: str
    all_satisfied: bool
    results: list[RequirementCheckResult]
    setup_instructions: list[str]  # Setup instructions for the user


# ---------------------------------------------------------------------------
# Plugin template catalog (substitute for community registry)
# ---------------------------------------------------------------------------

# Known tool -> plugin manifest mapping
# Searched when a user says "add browser-use"
# In the future, dynamically fetched from remote registry (plugins.zeo.dev)

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
                "description": "LLM required for browser-use AI decision-making",
                "install_hint": (
                    "Set one of the following:\n"
                    "  - BROWSER_USE_API_KEY (dedicated for browser-use, recommended)\n"
                    "  - OPENAI_API_KEY (OpenAI)\n"
                    "  - ANTHROPIC_API_KEY (Anthropic)\n"
                    "  - GEMINI_API_KEY (Google, free tier available)\n"
                    "  - Ollama (local, free)\n"
                    "  - g4f (no API key required mode)"
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
            "class": None,  # Not implemented — expecting community contribution
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
    # ── Image Generation ──────────────────────────────────────────────────
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
                "install_hint": "COMFYUI_URL=http://localhost:8188 (URL of the ComfyUI server)",
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
                "install_hint": "Set BFL_API_KEY (for API access). Local execution is also possible.",
                "alternatives": ["BFL_API_KEY", "REPLICATE_API_TOKEN"],
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    # ── Music Generation ──────────────────────────────────────────────────
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
                "install_hint": "Get session cookie from Suno Web UI and set it as SUNO_COOKIE",
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
    # ── Speech Synthesis ──────────────────────────────────────────────────
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
                "install_hint": "Start VOICEVOX Engine and set VOICEVOX_URL=http://localhost:50021",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    # ── Search / Research ────────────────────────────────────────────────
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
                "install_hint": "Get API key at https://tavily.com",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    # ── Data Analysis ────────────────────────────────────────────────────
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
                "description": "LLM required for data analysis",
                "install_hint": "Set OPENAI_API_KEY or another LLM provider",
                "alternatives": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ollama", "g4f"],
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    # ── 3D Models ─────────────────────────────────────────────────────────
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
    # ── Communication ────────────────────────────────────────────────────
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
                "install_hint": "Create a Slack App and obtain a Bot Token",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    # ── Video Generation ─────────────────────────────────────────────────
    "runway-ml": {
        "slug": "runway-ml",
        "name": "Runway ML",
        "name_ja": "Runway ML",
        "description": "AI video generation and editing. Gen-3 Alpha Turbo.",
        "description_ja": "AI 動画生成・編集。Gen-3 Alpha Turbo 対応。",
        "version": "latest",
        "source_uri": "https://github.com/runwayml/sdk-python",
        "pypi_package": "runwayml",
        "category": "video-generation",
        "license": "Proprietary",
        "requirements": [
            {
                "type": "api_key",
                "name": "RUNWAY_API_KEY",
                "required": True,
                "install_hint": "Get API key at https://app.runwayml.com/",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    "pika": {
        "slug": "pika",
        "name": "Pika",
        "name_ja": "Pika",
        "description": "AI video generation from text and images.",
        "description_ja": "テキスト・画像から AI 動画生成。",
        "version": "latest",
        "source_uri": "https://pika.art",
        "pypi_package": None,
        "category": "video-generation",
        "license": "Proprietary",
        "requirements": [
            {
                "type": "api_key",
                "name": "PIKA_API_KEY",
                "required": True,
                "install_hint": "Get API key at https://pika.art",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    # ── Social Media ────────────────────────────────────────────────────
    "twitter-x": {
        "slug": "twitter-x",
        "name": "Twitter / X API",
        "name_ja": "Twitter / X API",
        "description": "Post tweets, threads, schedule content on X (formerly Twitter).",
        "description_ja": "X (旧Twitter) への投稿・スレッド作成・予約投稿。",
        "version": "latest",
        "source_uri": "https://github.com/tweepy/tweepy",
        "pypi_package": "tweepy",
        "category": "social-media",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "tweepy",
                "required": True,
                "install_hint": "pip install tweepy",
            },
            {
                "type": "api_key",
                "name": "TWITTER_API_KEY",
                "required": True,
                "install_hint": "Get API key at https://developer.x.com",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    "instagram-api": {
        "slug": "instagram-api",
        "name": "Instagram Graph API",
        "name_ja": "Instagram Graph API",
        "description": "Post images, reels, stories via Instagram Graph API.",
        "description_ja": "Instagram Graph API 経由で画像・リール・ストーリー投稿。",
        "version": "latest",
        "source_uri": "https://developers.facebook.com/docs/instagram-api",
        "pypi_package": None,
        "category": "social-media",
        "license": "Proprietary",
        "requirements": [
            {
                "type": "api_key",
                "name": "INSTAGRAM_ACCESS_TOKEN",
                "required": True,
                "install_hint": "Get access token via Meta Business Suite",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    "youtube-api": {
        "slug": "youtube-api",
        "name": "YouTube Data API",
        "name_ja": "YouTube Data API",
        "description": "Upload videos, manage playlists, community posts.",
        "description_ja": "動画アップロード・プレイリスト管理・コミュニティ投稿。",
        "version": "latest",
        "source_uri": "https://github.com/googleapis/google-api-python-client",
        "pypi_package": "google-api-python-client",
        "category": "social-media",
        "license": "Apache-2.0",
        "requirements": [
            {
                "type": "pip_package",
                "name": "google-api-python-client",
                "required": True,
                "install_hint": "pip install google-api-python-client",
            },
            {
                "type": "api_key",
                "name": "YOUTUBE_API_KEY",
                "required": True,
                "install_hint": "Get API key at https://console.cloud.google.com",
            },
        ],
        "adapter": {"type": "python_module", "module": None, "class": None},
    },
    "tiktok-api": {
        "slug": "tiktok-api",
        "name": "TikTok API",
        "name_ja": "TikTok API",
        "description": "Post and manage video content on TikTok.",
        "description_ja": "TikTok への動画投稿・コンテンツ管理。",
        "version": "latest",
        "source_uri": "https://developers.tiktok.com",
        "pypi_package": None,
        "category": "social-media",
        "license": "Proprietary",
        "requirements": [
            {
                "type": "api_key",
                "name": "TIKTOK_ACCESS_TOKEN",
                "required": True,
                "install_hint": "Get access token at https://developers.tiktok.com",
            },
        ],
        "adapter": {"type": "rest_api", "module": None, "class": None},
    },
    # ── Agent Frameworks ────────────────────────────────────────────────
    "crewai-orchestrator": {
        "slug": "crewai-orchestrator",
        "name": "CrewAI Orchestrator",
        "name_ja": "CrewAI オーケストレーター",
        "description": "Multi-agent AI orchestration. Define crews with roles, goals, and tools.",
        "description_ja": "マルチエージェント AI オーケストレーション。役割・目標・ツールを定義。",
        "version": "latest",
        "source_uri": "https://github.com/crewAIInc/crewAI",
        "pypi_package": "crewai",
        "category": "agent-framework",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "crewai",
                "required": True,
                "install_hint": "pip install crewai",
            },
            {
                "type": "llm_provider",
                "name": "LLM provider",
                "required": True,
                "description": "LLM required for agent operations",
                "alternatives": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ollama"],
            },
        ],
        "adapter": {
            "type": "agent_framework",
            "framework": "crewai",
            "module": "app.tools.agent_adapter",
            "class": "CrewAIAdapter",
        },
    },
    "autogen-orchestrator": {
        "slug": "autogen-orchestrator",
        "name": "AutoGen (Microsoft)",
        "name_ja": "AutoGen (Microsoft)",
        "description": "Microsoft's multi-agent conversation framework.",
        "description_ja": "Microsoft のマルチエージェント会話フレームワーク。",
        "version": "latest",
        "source_uri": "https://github.com/microsoft/autogen",
        "pypi_package": "autogen-agentchat",
        "category": "agent-framework",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "autogen-agentchat",
                "required": True,
                "install_hint": "pip install autogen-agentchat",
            },
        ],
        "adapter": {
            "type": "agent_framework",
            "framework": "autogen",
            "module": "app.tools.agent_adapter",
            "class": "AutoGenAdapter",
        },
    },
    "langchain-agent": {
        "slug": "langchain-agent",
        "name": "LangChain Agent",
        "name_ja": "LangChain エージェント",
        "description": "LangChain agent executor with tool use and memory.",
        "description_ja": "LangChain エージェントエグゼキューター。ツール使用・メモリ対応。",
        "version": "latest",
        "source_uri": "https://github.com/langchain-ai/langchain",
        "pypi_package": "langchain",
        "category": "agent-framework",
        "license": "MIT",
        "requirements": [
            {
                "type": "pip_package",
                "name": "langchain",
                "required": True,
                "install_hint": "pip install langchain langchain-openai",
            },
        ],
        "adapter": {
            "type": "agent_framework",
            "framework": "langchain",
            "module": "app.tools.agent_adapter",
            "class": "LangChainAdapter",
        },
    },
    "openclaw-agent": {
        "slug": "openclaw-agent",
        "name": "OpenClaw Agent",
        "name_ja": "OpenClaw エージェント",
        "description": "OpenClaw AI agent integration.",
        "description_ja": "OpenClaw AI エージェント連携。",
        "version": "latest",
        "source_uri": "https://github.com/openclaw",
        "pypi_package": None,
        "category": "agent-framework",
        "license": "MIT",
        "requirements": [],
        "adapter": {
            "type": "agent_framework",
            "framework": "openclaw",
            "module": "app.tools.agent_adapter",
            "class": "OpenClawAdapter",
        },
    },
    "dify-workflow": {
        "slug": "dify-workflow",
        "name": "Dify Workflow",
        "name_ja": "Dify ワークフロー",
        "description": "Execute Dify workflows and chatflows from ZEO.",
        "description_ja": "ZEO から Dify ワークフロー・チャットフローを実行。",
        "version": "latest",
        "source_uri": "https://github.com/langgenius/dify",
        "pypi_package": None,
        "category": "agent-framework",
        "license": "MIT",
        "requirements": [
            {
                "type": "api_key",
                "name": "DIFY_API_KEY",
                "required": True,
                "install_hint": "Get API key from your Dify instance",
            },
        ],
        "adapter": {
            "type": "agent_framework",
            "framework": "dify",
            "module": "app.tools.agent_adapter",
            "class": "DifyAdapter",
        },
    },
    "n8n-agent": {
        "slug": "n8n-agent",
        "name": "n8n Workflow-as-Agent",
        "name_ja": "n8n ワークフローエージェント",
        "description": "Delegate tasks to an n8n workflow that behaves as an AI agent via webhook.",
        "description_ja": "n8n の Webhook を介して、ワークフローを AI エージェントとして実行します。",
        "version": "latest",
        "source_uri": "https://github.com/n8n-io/n8n",
        "pypi_package": None,
        "category": "agent-framework",
        "license": "Sustainable Use License",
        "requirements": [
            {
                "type": "env_var",
                "name": "N8N_AGENT_WEBHOOK_URL",
                "required": True,
                "install_hint": "Point this to an n8n webhook that accepts {instruction, context}.",
            },
        ],
        "adapter": {
            "type": "agent_framework",
            "framework": "n8n",
            "module": "app.tools.agent_adapter",
            "class": "N8NAgentAdapter",
        },
    },
}


# ---------------------------------------------------------------------------
# Universal tool registry — foundation for AI agents to dynamically select tools
# ---------------------------------------------------------------------------


class ToolRegistry:
    """Registry that manages tools across all categories.

    Foundation for the AI agent organization to dynamically select the optimal
    tool per task. Rather than locking in specific tools, users configure their
    preferred tool per category, and agents use that selection.

    Examples:
    - Image generation task -> user-configured image tool (ComfyUI or DALL-E or Flux)
    - Browser automation task -> user-configured browser tool (browser-use or Playwright)
    - Music generation task -> user-configured music tool (Suno or MusicGen)
    """

    def __init__(self) -> None:
        # Category -> list of registered tool names
        self._tools: dict[str, list[str]] = {}
        # Category -> active tool name
        self._active: dict[str, str] = {}
        # Tool name -> configuration
        self._configs: dict[str, dict] = {}

    def register_tool(
        self,
        slug: str,
        category: str,
        config: dict,
    ) -> None:
        """Register a tool in the registry.

        Args:
            slug: Tool identifier
            category: Tool category
            config: Tool configuration (manifest info, etc.)
        """
        if category not in self._tools:
            self._tools[category] = []
        if slug not in self._tools[category]:
            self._tools[category].append(slug)
        self._configs[slug] = {**config, "category": category}

        # Set as active if this is the first tool in the category
        if category not in self._active:
            self._active[category] = slug

        logger.info("Tool registered: %s (category: %s)", slug, category)

    def unregister_tool(self, slug: str) -> bool:
        """Unregister a tool."""
        config = self._configs.pop(slug, None)
        if config is None:
            return False

        category = config["category"]
        if category in self._tools and slug in self._tools[category]:
            self._tools[category].remove(slug)

        # Switch to another tool if the active one was removed
        if self._active.get(category) == slug:
            remaining = self._tools.get(category, [])
            self._active[category] = remaining[0] if remaining else ""

        return True

    def set_active_tool(self, category: str, slug: str) -> bool:
        """Switch the active tool for a category.

        When a user says "use ComfyUI for image generation",
        switch the active tool for the image-generation category to comfyui.
        """
        if category not in self._tools or slug not in self._tools[category]:
            return False
        self._active[category] = slug
        logger.info("Active tool changed: %s -> %s", category, slug)
        return True

    def get_active_tool(self, category: str) -> str | None:
        """Get the active tool for a category.

        Called when an AI agent wants to perform e.g. "image generation".
        """
        return self._active.get(category)

    def get_tool_config(self, slug: str) -> dict | None:
        """Get configuration for a tool."""
        return self._configs.get(slug)

    def list_tools(self, category: str | None = None) -> list[dict]:
        """Return a list of registered tools."""
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
        """Return a list of categories and their active tools."""
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
        """Infer category from task description and return the active tool.

        Called when the AI agent organization executes a task.

        Args:
            task_description: Natural language description of the task

        Returns:
            Tool configuration, or None if no match
        """
        desc_lower = task_description.lower()

        # Category keyword mapping
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
                "Runway",
                "Pika",
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
            "social-media": [
                "SNS",
                "Twitter",
                "Instagram",
                "TikTok",
                "YouTube",
                "投稿",
                "ツイート",
                "post",
                "tweet",
                "ソーシャル",
                "social",
            ],
            "agent-framework": [
                "エージェント",
                "agent",
                "CrewAI",
                "AutoGen",
                "LangChain",
                "OpenClaw",
                "Dify",
                "マルチエージェント",
                "multi-agent",
                "オーケストレーション",
                "orchestration",
                "フレームワーク",
                "framework",
            ],
        }

        for category, keywords in category_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                active = self.get_active_tool(category)
                if active:
                    return self.get_tool_config(active)

        return None


# ---------------------------------------------------------------------------
# Environment checker
# ---------------------------------------------------------------------------


class EnvironmentResolver:
    """Verify and resolve plugin dependencies and environment requirements.

    Inspects each requirement and generates setup instructions for missing ones.
    """

    def check_pip_package(self, package_name: str) -> bool:
        """Check whether a pip package is installed."""
        try:
            importlib.import_module(package_name.replace("-", "_"))
            return True
        except ImportError:
            return False

    def check_system_command(self, command: str) -> bool:
        """Check whether a system command is available."""
        import shutil

        return shutil.which(command) is not None

    def check_env_var(self, var_name: str) -> bool:
        """Check whether an environment variable is set."""
        import os

        return bool(os.environ.get(var_name, ""))

    def check_llm_provider(self, alternatives: list[str]) -> tuple[bool, str]:
        """Check whether at least one LLM provider is available.

        Returns:
            (is_available, available_provider_name)
        """
        import os

        # API key checks
        for alt in alternatives:
            if alt in ("ollama", "g4f"):
                continue
            if os.environ.get(alt, ""):
                return True, alt

        # Ollama check
        if "ollama" in alternatives:
            try:
                from app.providers.ollama_provider import ollama_provider

                if ollama_provider:
                    return True, "ollama"
            except ImportError:
                pass

        # g4f check
        if "g4f" in alternatives:
            try:
                from app.providers.g4f_provider import g4f_provider

                if g4f_provider.available:
                    return True, "g4f"
            except ImportError:
                pass

        return False, ""

    def check_browser(self) -> bool:
        """Check whether a browser is available."""
        import shutil

        browsers = ["chromium", "chromium-browser", "google-chrome", "chrome"]
        return any(shutil.which(b) is not None for b in browsers)

    def check_requirements(
        self,
        requirements: list[dict],
    ) -> EnvironmentReport:
        """Check all plugin requirements and generate a report."""
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
                    detail = f"{req.name} is installed"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} not found"
                    setup_instructions.append(f"Install package: {req.install_hint}")

            elif req.type == RequirementType.SYSTEM_COMMAND:
                if self.check_system_command(req.name):
                    detail = f"{req.name} command is available"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} command not found"
                    setup_instructions.append(f"Install command: {req.install_hint}")

            elif req.type == RequirementType.API_KEY:
                if self.check_env_var(req.name):
                    detail = f"{req.name} is configured"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} is not set"
                    setup_instructions.append(f"Set API key: {req.install_hint}")

            elif req.type == RequirementType.ENV_VAR:
                if self.check_env_var(req.name):
                    detail = f"{req.name} is configured"
                else:
                    status = RequirementStatus.MISSING
                    detail = f"{req.name} is not set"
                    setup_instructions.append(f"Set environment variable: {req.install_hint}")

            elif req.type == RequirementType.LLM_PROVIDER:
                available, provider_name = self.check_llm_provider(req.alternatives)
                if available:
                    detail = f"LLM provider available: {provider_name}"
                else:
                    status = RequirementStatus.MISSING
                    detail = "No LLM provider available"
                    setup_instructions.append(f"Set up LLM provider:\n{req.install_hint}")

            elif req.type == RequirementType.BROWSER:
                if self.check_browser():
                    detail = "Browser is available"
                else:
                    status = RequirementStatus.MISSING
                    detail = "Browser not found"
                    setup_instructions.append(f"Install browser: {req.install_hint}")

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
# Plugin loader
# ---------------------------------------------------------------------------


class PluginLoader:
    """Manages plugin search, environment check, installation, and activation.

    Plugin lifecycle management:
    1. Search: Users search by name or keyword (natural language supported)
    2. Check: Automatic inspection of dependencies and environment requirements
    3. Install: Assistance with pip package installation
    4. Activate: Register and activate adapters/services
    5. Tool switch: Switch active tools per category

    Integration with AI agent organization:
    - Agents select the optimal tool per task via tool_registry.resolve_tool_for_task()
    - Agents automatically use the active tool configured by the user
    """

    def __init__(self) -> None:
        self._env_resolver = EnvironmentResolver()
        self._installed_plugins: dict[str, dict] = {}
        self.tool_registry = ToolRegistry()

    # ----- Search -----

    def search(self, query: str) -> list[dict]:
        """Search plugins with a natural language query.

        Returns appropriate plugins when users enter queries like
        "browser automation", "browser-use", "web automation", etc.

        Args:
            query: Search query (natural language or plugin name)

        Returns:
            List of matching plugin templates
        """
        query_lower = query.lower()
        results = []

        for slug, template in _KNOWN_PLUGIN_TEMPLATES.items():
            # Match by slug, name, description, category
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
        """Get a plugin template."""
        return _KNOWN_PLUGIN_TEMPLATES.get(slug)

    # ----- Environment check -----

    def check_environment(self, slug: str) -> EnvironmentReport:
        """Check the environment requirements for a plugin.

        Presents what is needed to the user before installation.

        Args:
            slug: Plugin slug

        Returns:
            Environment check report
        """
        template = _KNOWN_PLUGIN_TEMPLATES.get(slug)
        if not template:
            return EnvironmentReport(
                plugin_name=slug,
                all_satisfied=False,
                results=[],
                setup_instructions=[f"Plugin '{slug}' not found"],
            )

        requirements = template.get("requirements", [])
        report = self._env_resolver.check_requirements(requirements)
        report.plugin_name = template["name"]
        return report

    # ----- Install -----

    async def install_plugin(
        self,
        slug: str,
        *,
        auto_install_packages: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """Install a plugin.

        Args:
            slug: Plugin slug
            auto_install_packages: Whether to auto-install pip packages
            dry_run: Only return instructions without actually installing

        Returns:
            Installation result
        """
        template = _KNOWN_PLUGIN_TEMPLATES.get(slug)
        if not template:
            return {
                "success": False,
                "error": f"Plugin '{slug}' not found",
                "available_plugins": list(_KNOWN_PLUGIN_TEMPLATES.keys()),
            }

        # Environment check
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

        # Auto-install pip packages
        if auto_install_packages and not env_report.all_satisfied:
            for result in env_report.results:
                if (
                    result.status == RequirementStatus.MISSING
                    and result.requirement.type == RequirementType.PIP_PACKAGE
                ):
                    package = result.requirement.name
                    logger.info("Auto-installing: %s", package)
                    try:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", package],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=120,
                        )
                        result.status = RequirementStatus.SATISFIED
                        result.detail = f"{package} has been installed"
                    except Exception as exc:
                        logger.error("Package installation failed %s: %s", package, exc)

            # Re-check
            env_report = self.check_environment(slug)

        # Adapter registration
        adapter_config = template.get("adapter", {})
        adapter_registered = False

        if adapter_config.get("class") and adapter_config.get("module"):
            try:
                module = importlib.import_module(adapter_config["module"])
                adapter_cls = getattr(module, adapter_config["class"])
                adapter_instance = adapter_cls()

                adapter_type = adapter_config.get("type", "browser")
                if adapter_type == "agent_framework":
                    from app.tools.agent_adapter import agent_adapter_registry

                    framework = adapter_config.get("framework", slug)
                    agent_adapter_registry.register(framework, adapter_instance)
                    logger.info("Agent-framework adapter registered: %s", framework)
                else:
                    from app.tools.browser_adapter import browser_adapter_registry

                    browser_adapter_registry.register(slug, adapter_instance)
                    logger.info("Browser adapter registered: %s", slug)
                adapter_registered = True
            except Exception as exc:
                logger.warning("Adapter registration failed: %s — %s", slug, exc)

        self._installed_plugins[slug] = {
            "template": template,
            "adapter_registered": adapter_registered,
        }

        # Register in tool registry (makes it available to AI agents)
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

    # ----- Uninstall -----

    def uninstall_plugin(self, slug: str) -> dict:
        """Unregister a plugin (does not remove pip packages)."""
        if slug not in self._installed_plugins:
            return {"success": False, "error": f"Plugin '{slug}' is not installed"}

        # Also unregister from browser adapter registry
        try:
            from app.tools.browser_adapter import browser_adapter_registry

            browser_adapter_registry.unregister(slug)
        except Exception:
            pass

        # Also unregister from tool registry
        self.tool_registry.unregister_tool(slug)

        del self._installed_plugins[slug]
        return {"success": True, "message": f"Plugin '{slug}' has been removed"}

    # ----- List -----

    def list_installed(self) -> list[dict]:
        """Return a list of installed plugins."""
        return [
            {
                "slug": slug,
                "name": info["template"]["name"],
                "adapter_registered": info["adapter_registered"],
            }
            for slug, info in self._installed_plugins.items()
        ]

    def list_available(self) -> list[dict]:
        """Return a list of all available plugins."""
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
# Global instance
# ---------------------------------------------------------------------------

plugin_loader = PluginLoader()
