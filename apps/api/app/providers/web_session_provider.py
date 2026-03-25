"""Web ブラウザ経由 AI セッションプロバイダー.

GPT・Gemini・Claude 等の AI サービスを Web ブラウザ UI 経由で利用し、
API 料金なしでシステムに組み込む方式。

仕組み:
1. ブラウザ自動操作（browser-use 等）で AI の Web UI にアクセス
2. プロンプトを入力し、レスポンスを取得
3. ZEO の LLM Gateway に統合

利用パターン:
- Pattern A: g4f (gpt4free) — Web エンドポイントを自動的にルーティング（既存）
- Pattern B: ブラウザセッション — 実際のブラウザで AI Web UI を操作
- Pattern C: Cookie/セッション認証 — ログイン済みセッションを再利用

注意:
- 各 AI サービスの利用規約を確認すること
- API キーを使った公式 API が最も安定・確実
- Web UI 経由はレート制限やブロックのリスクがある
- 本番環境では公式 API を推奨
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Web AI サービス定義
# ---------------------------------------------------------------------------


class WebAIService(str, Enum):
    """ブラウザ経由で利用可能な AI サービス."""

    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    CLAUDE = "claude"
    COPILOT = "copilot"
    DEEPSEEK = "deepseek"
    PERPLEXITY = "perplexity"


@dataclass
class WebSessionConfig:
    """Web AI セッションの設定."""

    service: WebAIService
    session_cookies: dict | None = None  # ブラウザからエクスポートした Cookie
    profile_dir: str | None = None  # Chrome プロファイルディレクトリ
    headless: bool = True
    timeout_seconds: int = 120


@dataclass
class WebSessionResponse:
    """Web セッション経由の AI レスポンス."""

    content: str
    service: str
    model_hint: str = ""  # Web UI で選択されたモデル（取得可能な場合）
    cost_usd: float = 0.0  # Web UI 経由は常に 0
    finish_reason: str = "stop"
    tokens_input: int = 0
    tokens_output: int = 0


# ---------------------------------------------------------------------------
# Web AI セッションカタログ
# ---------------------------------------------------------------------------

_WEB_AI_CATALOG: dict[WebAIService, dict] = {
    WebAIService.CHATGPT: {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "free_tier": True,
        "free_model": "GPT-4o mini",
        "subscription_model": "GPT-4o / o1",
        "subscription_name": "ChatGPT Plus",
        "input_selector": "#prompt-textarea",
        "submit_selector": "button[data-testid='send-button']",
        "response_selector": ".markdown",
        "env_cookie_key": "CHATGPT_SESSION_COOKIE",
    },
    WebAIService.GEMINI: {
        "name": "Google Gemini",
        "url": "https://gemini.google.com",
        "free_tier": True,
        "free_model": "Gemini 2.5 Flash",
        "subscription_model": "Gemini 2.5 Pro",
        "subscription_name": "Gemini Advanced",
        "input_selector": ".ql-editor",
        "submit_selector": "button[aria-label='Send message']",
        "response_selector": ".model-response-text",
        "env_cookie_key": "GEMINI_SESSION_COOKIE",
    },
    WebAIService.CLAUDE: {
        "name": "Claude",
        "url": "https://claude.ai",
        "free_tier": True,
        "free_model": "Claude Sonnet 4",
        "subscription_model": "Claude Opus 4",
        "subscription_name": "Claude Pro",
        "input_selector": ".ProseMirror",
        "submit_selector": "button[aria-label='Send Message']",
        "response_selector": ".font-claude-message",
        "env_cookie_key": "CLAUDE_SESSION_COOKIE",
    },
    WebAIService.COPILOT: {
        "name": "Microsoft Copilot",
        "url": "https://copilot.microsoft.com",
        "free_tier": True,
        "free_model": "GPT-4o",
        "subscription_model": "GPT-4o + DALL-E",
        "subscription_name": "Copilot Pro",
        "input_selector": "#userInput",
        "submit_selector": "button[aria-label='Submit']",
        "response_selector": ".ac-textBlock",
        "env_cookie_key": "COPILOT_SESSION_COOKIE",
    },
    WebAIService.DEEPSEEK: {
        "name": "DeepSeek",
        "url": "https://chat.deepseek.com",
        "free_tier": True,
        "free_model": "DeepSeek V3",
        "subscription_model": "DeepSeek R1",
        "subscription_name": "DeepSeek (free)",
        "input_selector": "textarea",
        "submit_selector": "button[type='submit']",
        "response_selector": ".markdown-body",
        "env_cookie_key": "DEEPSEEK_SESSION_COOKIE",
    },
    WebAIService.PERPLEXITY: {
        "name": "Perplexity",
        "url": "https://www.perplexity.ai",
        "free_tier": True,
        "free_model": "Default",
        "subscription_model": "Pro Search",
        "subscription_name": "Perplexity Pro",
        "input_selector": "textarea",
        "submit_selector": "button[aria-label='Submit']",
        "response_selector": ".prose",
        "env_cookie_key": "PERPLEXITY_SESSION_COOKIE",
    },
}


# ---------------------------------------------------------------------------
# プロバイダークラス
# ---------------------------------------------------------------------------


class WebSessionProvider:
    """Web ブラウザ経由で AI サービスを利用するプロバイダー.

    3 つの方式を提供:
    1. g4f 経由 (推奨) — 最も簡単。g4f が Web エンドポイントを自動ルーティング
    2. ブラウザセッション — browser-use 等でブラウザを自動操作
    3. Cookie 認証 — ログイン済みセッションの Cookie を再利用

    推奨利用順序:
    1. 無料枠のある公式 API (Gemini free tier, etc.)
    2. g4f (既存の g4f_provider.py)
    3. Ollama (ローカル)
    4. ブラウザセッション (本クラス)
    """

    def __init__(self) -> None:
        self._sessions: dict[str, WebSessionConfig] = {}

    def list_services(self) -> list[dict]:
        """利用可能な Web AI サービス一覧を返す."""
        services = []
        for service, info in _WEB_AI_CATALOG.items():
            has_cookie = bool(os.environ.get(info["env_cookie_key"], ""))
            services.append(
                {
                    "service": service.value,
                    "name": info["name"],
                    "url": info["url"],
                    "free_tier": info["free_tier"],
                    "free_model": info["free_model"],
                    "subscription_model": info["subscription_model"],
                    "subscription_name": info["subscription_name"],
                    "cookie_configured": has_cookie,
                    "cost_usd": 0.0,
                }
            )
        return services

    def get_recommended_free_options(self) -> list[dict]:
        """API 料金なしで利用できるオプションを推奨順に返す.

        ユーザーがコストをかけずに AI を利用する方法を整理:
        1. 無料 API キー (Gemini free tier)
        2. g4f (Web エンドポイント自動ルーティング)
        3. Ollama (ローカル)
        4. Web AI セッション (本プロバイダー)
        """
        options = [
            {
                "method": "gemini_free_api",
                "name": "Google Gemini 無料 API",
                "description": (
                    "Google AI Studio から無料 API キーを取得。レート制限はあるが安定性が高い。"
                ),
                "setup": "GEMINI_API_KEY を設定",
                "stability": "high",
                "rate_limit": "15 RPM (free tier)",
                "cost": 0.0,
                "recommended": True,
            },
            {
                "method": "g4f",
                "name": "g4f (gpt4free)",
                "description": (
                    "Web エンドポイントを自動ルーティング。複数プロバイダーにフォールバック。"
                ),
                "setup": "pip install g4f (USE_G4F=true がデフォルト)",
                "stability": "medium",
                "rate_limit": "プロバイダーにより異なる",
                "cost": 0.0,
                "recommended": True,
            },
            {
                "method": "ollama",
                "name": "Ollama (ローカル LLM)",
                "description": (
                    "ローカルで LLM を実行。完全オフライン・無料。"
                    "GPUがあれば高品質なモデルも利用可能。"
                ),
                "setup": "Ollama をインストールし、モデルを pull",
                "stability": "high",
                "rate_limit": "ハードウェア依存",
                "cost": 0.0,
                "recommended": True,
            },
            {
                "method": "web_session",
                "name": "Web AI セッション",
                "description": (
                    "ChatGPT / Gemini / Claude 等の Web UI をブラウザ経由で利用。"
                    "各サービスのサブスクリプション料金のみで API 料金不要。"
                ),
                "setup": "browser-use Plugin をインストール、または Cookie を設定",
                "stability": "low",
                "rate_limit": "Web UI のレート制限に依存",
                "cost": 0.0,
                "recommended": False,
            },
        ]
        return options

    async def complete(
        self,
        service: WebAIService,
        messages: list[dict],
        config: WebSessionConfig | None = None,
    ) -> WebSessionResponse:
        """Web AI セッション経由で補完リクエストを送信する.

        現在の実装では g4f へのフォールバックを行う。
        browser-use アダプタがインストールされている場合はブラウザ操作モードも利用可能。

        Args:
            service: 利用する AI サービス
            messages: メッセージリスト
            config: セッション設定（省略時はデフォルト）

        Returns:
            AI レスポンス
        """
        catalog_entry = _WEB_AI_CATALOG.get(service)
        if not catalog_entry:
            return WebSessionResponse(
                content=f"[未対応のサービス: {service.value}]",
                service=service.value,
                finish_reason="error",
            )

        # 方式 1: g4f 経由（推奨・最も安定）
        g4f_result = await self._try_g4f(service, messages)
        if g4f_result and g4f_result.finish_reason != "error":
            return g4f_result

        # 方式 2: ブラウザセッション経由
        browser_result = await self._try_browser_session(service, messages, catalog_entry, config)
        if browser_result:
            return browser_result

        # フォールバック
        return WebSessionResponse(
            content=(
                f"[{catalog_entry['name']} へのアクセスに失敗しました。"
                "g4f をインストールするか、browser-use Plugin を追加してください。]"
            ),
            service=service.value,
            finish_reason="error",
        )

    async def _try_g4f(
        self,
        service: WebAIService,
        messages: list[dict],
    ) -> WebSessionResponse | None:
        """g4f 経由でリクエストを試みる."""
        g4f_model_map: dict[WebAIService, str] = {
            WebAIService.CHATGPT: "g4f/OpenaiChat",
            WebAIService.GEMINI: "g4f/GeminiPro",
            WebAIService.CLAUDE: "g4f/Claude",
            WebAIService.COPILOT: "g4f/Copilot",
            WebAIService.DEEPSEEK: "g4f/DeepInfra",
        }

        model = g4f_model_map.get(service)
        if not model:
            return None

        try:
            from app.providers.g4f_provider import g4f_provider

            if not g4f_provider.available:
                return None

            resp = await g4f_provider.complete(model=model, messages=messages)
            if resp.finish_reason == "error":
                return None

            return WebSessionResponse(
                content=resp.content,
                service=service.value,
                model_hint=resp.model_used,
                cost_usd=0.0,
                finish_reason=resp.finish_reason,
            )
        except Exception as exc:
            logger.debug("g4f fallback failed for %s: %s", service.value, exc)
            return None

    async def _try_browser_session(
        self,
        service: WebAIService,
        messages: list[dict],
        catalog_entry: dict,
        config: WebSessionConfig | None,
    ) -> WebSessionResponse | None:
        """ブラウザセッション経由でリクエストを試みる."""
        try:
            from app.tools.browser_adapter import BrowserTask, browser_adapter_registry

            adapter = browser_adapter_registry.get_adapter("browser-use")
            if adapter is None:
                return None

            # メッセージを結合してプロンプトを作成
            prompt = "\n".join(m.get("content", "") for m in messages if m.get("role") != "system")

            task = BrowserTask(
                instruction=(
                    f"{catalog_entry['url']} にアクセスして、"
                    f"以下のプロンプトを入力し、AIの回答を取得してください:\n\n{prompt}"
                ),
                url=catalog_entry["url"],
                max_steps=20,
                timeout_seconds=config.timeout_seconds if config else 120,
                require_approval=False,  # Web AI セッションは承認不要
            )

            result = await adapter.execute_task(task)
            if result.status.value == "completed" and result.output:
                return WebSessionResponse(
                    content=result.output,
                    service=service.value,
                    model_hint=catalog_entry.get("free_model", ""),
                    cost_usd=0.0,
                    finish_reason="stop",
                )
        except Exception as exc:
            logger.debug("Browser session failed for %s: %s", service.value, exc)

        return None


# ---------------------------------------------------------------------------
# グローバルインスタンス
# ---------------------------------------------------------------------------

web_session_provider = WebSessionProvider()
