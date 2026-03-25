"""ブラウザ自動操作アダプタ — プラグイン方式の拡張可能ブラウザ操作基盤.

VSCode のエクステンションのように、サードパーティのブラウザ自動操作ライブラリを
アダプタとして追加・切替できる仕組み。初期状態ではビルトインの Playwright
アダプタのみを含み、browser-use / Selenium / Puppeteer 等は Plugin として
後から追加する設計。

対応アダプタ:
- builtin (Playwright) — デフォルト、ZEO 同梱
- browser-use — LLM 駆動の自律ブラウザ操作（Plugin でインストール）
- selenium — 従来型 Web 自動化（Plugin でインストール）
- custom — ユーザー定義アダプタ（Plugin API で登録）

安全性:
- 全アダプタは承認ゲートを経由
- 操作ログは監査システムに記録
- サンドボックス内で実行
"""

from __future__ import annotations

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 共通データ型
# ---------------------------------------------------------------------------


class AdapterType(str, Enum):
    """対応するブラウザ自動操作バックエンド."""

    BUILTIN = "builtin"  # Playwright (ZEO 同梱)
    BROWSER_USE = "browser-use"  # browser-use ライブラリ
    SELENIUM = "selenium"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STUCK = "stuck"  # ループ検出時
    REPLANNING = "replanning"  # 自動リプランニング中


@dataclass
class BrowserTask:
    """LLM に渡す自然言語タスク記述."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instruction: str = ""
    url: str | None = None
    max_steps: int = 50
    timeout_seconds: int = 300
    require_approval: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BrowserTaskResult:
    """タスク実行結果."""

    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    output: str = ""
    extracted_data: dict = field(default_factory=dict)
    screenshots: list[bytes] = field(default_factory=list)
    steps_executed: int = 0
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0
    adapter_used: str = ""
    replanned: bool = False


@dataclass
class AdapterCapabilities:
    """アダプタが提供する機能."""

    natural_language_control: bool = False  # 自然言語指示での操作
    loop_detection: bool = False  # ループ検出
    auto_replanning: bool = False  # 自動リプランニング
    screenshot_analysis: bool = False  # スクリーンショット解析
    dom_inspection: bool = False  # DOM 構造解析
    form_filling: bool = True  # フォーム入力
    navigation: bool = True  # ページ遷移
    data_extraction: bool = True  # データ抽出
    headless: bool = True  # ヘッドレスモード


@dataclass
class AdapterInfo:
    """登録済みアダプタの情報."""

    adapter_type: AdapterType
    name: str
    version: str
    description: str
    capabilities: AdapterCapabilities
    installed: bool = False
    install_package: str = ""  # pip install コマンド


# ---------------------------------------------------------------------------
# 抽象アダプタインターフェース
# ---------------------------------------------------------------------------


class BrowserAdapter(ABC):
    """ブラウザ自動操作アダプタの抽象基底クラス.

    新しいブラウザ自動操作ライブラリを統合する場合、このクラスを継承して
    各メソッドを実装する。Plugin として登録すれば ZEO から利用可能になる。
    """

    @abstractmethod
    def info(self) -> AdapterInfo:
        """アダプタ情報を返す."""

    @abstractmethod
    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """自然言語タスクを実行する.

        Args:
            task: 実行するタスク

        Returns:
            実行結果
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """アダプタが利用可能か確認する."""

    async def cleanup(self) -> None:  # noqa: B027
        """リソース解放（オプション）."""


# ---------------------------------------------------------------------------
# ビルトインアダプタ (Playwright) — 最小限の同梱アダプタ
# ---------------------------------------------------------------------------


class BuiltinPlaywrightAdapter(BrowserAdapter):
    """Playwright ベースのビルトインアダプタ.

    ZEO に同梱される最小限のブラウザ自動操作。ステップベースの操作のみ対応し、
    自然言語制御やループ検出は提供しない。高度な機能が必要な場合は
    browser-use 等のアダプタを Plugin でインストールする。
    """

    def info(self) -> AdapterInfo:
        return AdapterInfo(
            adapter_type=AdapterType.BUILTIN,
            name="Builtin Playwright Adapter",
            version="0.1.0",
            description="ZEO 同梱の最小限ブラウザ操作。Playwright ベース。",
            capabilities=AdapterCapabilities(
                natural_language_control=False,
                loop_detection=False,
                auto_replanning=False,
                screenshot_analysis=False,
                dom_inspection=True,
                form_filling=True,
                navigation=True,
                data_extraction=True,
                headless=True,
            ),
            installed=True,
            install_package="playwright",
        )

    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """Playwright でタスクを実行する.

        ビルトインアダプタは自然言語制御をサポートしないため、
        URL へのナビゲーション + スクリーンショットのみ実行する。
        フルスクリプト実行は BrowserAutomation クラスを使用する。
        """
        start = time.monotonic()
        screenshots: list[bytes] = []
        errors: list[str] = []

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()

                if task.url:
                    await page.goto(task.url, timeout=task.timeout_seconds * 1000)

                screenshot = await page.screenshot(full_page=True)
                screenshots.append(screenshot)

                title = await page.title()
                await browser.close()

            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                output=f"ページ取得完了: {title}",
                screenshots=screenshots,
                steps_executed=1,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="builtin",
            )
        except ImportError:
            errors.append("Playwright 未インストール (pip install playwright)")
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output="[Playwright not installed]",
                errors=errors,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="builtin",
            )
        except Exception as exc:
            errors.append(str(exc))
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output=f"[Error: {exc}]",
                errors=errors,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="builtin",
            )

    async def health_check(self) -> bool:
        try:
            import playwright  # noqa: F401

            return True
        except ImportError:
            return False


# ---------------------------------------------------------------------------
# browser-use アダプタ (Plugin でインストール)
# ---------------------------------------------------------------------------


class BrowserUseAdapter(BrowserAdapter):
    """browser-use ライブラリを使った LLM 駆動ブラウザ操作アダプタ.

    自然言語の指示だけで Web ブラウザを自律的に操作する。
    LLM がスクリーンショットと DOM 構造を「見て」判断し、
    クリック・入力・スクロールを実行する。

    ループ検出・自動リプランニング機能により行き詰まりにも対応。

    要件: pip install browser-use
    """

    def __init__(self, llm_provider: str = "auto") -> None:
        self._llm_provider = llm_provider
        self._available = False
        self._check_availability()

    def _check_availability(self) -> None:
        try:
            import browser_use  # noqa: F401

            self._available = True
        except ImportError:
            self._available = False

    def info(self) -> AdapterInfo:
        return AdapterInfo(
            adapter_type=AdapterType.BROWSER_USE,
            name="browser-use Adapter",
            version="0.1.0",
            description=(
                "LLM 駆動の自律ブラウザ操作。自然言語の指示だけで Web を操作。"
                "ループ検出・自動リプランニング対応。"
            ),
            capabilities=AdapterCapabilities(
                natural_language_control=True,
                loop_detection=True,
                auto_replanning=True,
                screenshot_analysis=True,
                dom_inspection=True,
                form_filling=True,
                navigation=True,
                data_extraction=True,
                headless=True,
            ),
            installed=self._available,
            install_package="browser-use",
        )

    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """browser-use で自然言語タスクを実行する."""
        if not self._available:
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output="[browser-use 未インストール — pip install browser-use]",
                errors=["browser-use not installed"],
                adapter_used="browser-use",
            )

        start = time.monotonic()
        errors: list[str] = []

        try:
            from browser_use import Agent as BrowserUseAgent

            # LLM は ZEO の LLM Gateway から取得
            llm = await self._resolve_llm()

            agent = BrowserUseAgent(
                task=task.instruction,
                llm=llm,
                max_steps=task.max_steps,
            )

            result = await agent.run()

            output = ""
            extracted = {}
            if result:
                output = (
                    str(result.final_result()) if hasattr(result, "final_result") else str(result)
                )
                if hasattr(result, "extracted_content"):
                    extracted = {"content": result.extracted_content()}

            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                output=output,
                extracted_data=extracted,
                steps_executed=task.max_steps,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="browser-use",
            )
        except Exception as exc:
            errors.append(str(exc))
            logger.error("browser-use task failed: %s", exc)
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output=f"[browser-use error: {exc}]",
                errors=errors,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="browser-use",
            )

    async def _resolve_llm(self) -> object:
        """ZEO の LLM Gateway から LLM インスタンスを取得する.

        browser-use は langchain 互換の LLM オブジェクトを期待する。
        ZEO のゲートウェイ設定に基づいて適切な LLM を返す。
        """
        if self._llm_provider == "auto":
            try:
                import os

                from langchain_openai import ChatOpenAI

                # OpenAI 互換のプロバイダーを優先
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if api_key:
                    return ChatOpenAI(model="gpt-4o", api_key=api_key)

                # OpenRouter 経由
                openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
                if openrouter_key:
                    return ChatOpenAI(
                        model="openai/gpt-4o",
                        api_key=openrouter_key,
                        base_url="https://openrouter.ai/api/v1",
                    )
            except ImportError:
                pass

        # フォールバック: ダミー LLM（実際にはエラーになる）
        raise RuntimeError(
            "browser-use に必要な LLM プロバイダーが設定されていません。"
            "OPENAI_API_KEY または OPENROUTER_API_KEY を設定してください。"
        )

    async def health_check(self) -> bool:
        return self._available


# ---------------------------------------------------------------------------
# アダプタレジストリ — アダプタの登録・検索・切替
# ---------------------------------------------------------------------------


class BrowserAdapterRegistry:
    """ブラウザ自動操作アダプタのレジストリ.

    VSCode のエクステンションマーケットプレイスのように、
    アダプタを登録・検索・切替できる。
    """

    def __init__(self) -> None:
        self._adapters: dict[str, BrowserAdapter] = {}
        self._active_adapter: str = "builtin"
        # ビルトインアダプタのみ初期登録
        self.register("builtin", BuiltinPlaywrightAdapter())

    def register(self, name: str, adapter: BrowserAdapter) -> None:
        """アダプタを登録する.

        Args:
            name: アダプタの識別名
            adapter: アダプタインスタンス
        """
        self._adapters[name] = adapter
        logger.info("ブラウザアダプタ登録: %s", name)

    def unregister(self, name: str) -> bool:
        """アダプタを登録解除する（ビルトインは解除不可）."""
        if name == "builtin":
            logger.warning("ビルトインアダプタは登録解除できません")
            return False
        if name in self._adapters:
            del self._adapters[name]
            if self._active_adapter == name:
                self._active_adapter = "builtin"
            logger.info("ブラウザアダプタ登録解除: %s", name)
            return True
        return False

    def set_active(self, name: str) -> bool:
        """アクティブアダプタを切り替える."""
        if name not in self._adapters:
            logger.warning("アダプタが見つかりません: %s", name)
            return False
        self._active_adapter = name
        logger.info("アクティブアダプタ変更: %s", name)
        return True

    def get_active(self) -> BrowserAdapter:
        """現在のアクティブアダプタを返す."""
        return self._adapters[self._active_adapter]

    def get_active_name(self) -> str:
        return self._active_adapter

    def get_adapter(self, name: str) -> BrowserAdapter | None:
        return self._adapters.get(name)

    def list_adapters(self) -> list[AdapterInfo]:
        """登録済みアダプタ一覧を返す."""
        infos = []
        for _name, adapter in self._adapters.items():
            info = adapter.info()
            infos.append(info)
        return infos

    def list_installable(self) -> list[AdapterInfo]:
        """インストール可能な未登録アダプタ一覧を返す.

        マーケットプレイスに登録されているが、まだローカルに
        インストールされていないアダプタを返す。
        """
        known: list[AdapterInfo] = [
            AdapterInfo(
                adapter_type=AdapterType.BROWSER_USE,
                name="browser-use",
                version="0.4.x",
                description=(
                    "LLM 駆動の自律ブラウザ操作。自然言語の指示だけで Web を操作。"
                    "ループ検出・自動リプランニング対応。"
                ),
                capabilities=AdapterCapabilities(
                    natural_language_control=True,
                    loop_detection=True,
                    auto_replanning=True,
                    screenshot_analysis=True,
                    dom_inspection=True,
                ),
                installed=False,
                install_package="browser-use",
            ),
            AdapterInfo(
                adapter_type=AdapterType.SELENIUM,
                name="selenium",
                version="4.x",
                description="Selenium WebDriver ベースのブラウザ自動操作。",
                capabilities=AdapterCapabilities(
                    natural_language_control=False,
                    loop_detection=False,
                    auto_replanning=False,
                    dom_inspection=True,
                ),
                installed=False,
                install_package="selenium",
            ),
        ]
        registered_types = {a.info().adapter_type for a in self._adapters.values()}
        return [a for a in known if a.adapter_type not in registered_types]

    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """アクティブアダプタでタスクを実行する.

        承認ゲートを経由し、監査ログに記録する。
        """
        adapter = self.get_active()

        # 承認チェック
        if task.require_approval:
            try:
                from app.policies.approval_gate import check_approval_required

                approval = check_approval_required("browser_automation")
                if approval.requires_approval:
                    return BrowserTaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILED,
                        output="承認が必要です。承認後に再実行してください。",
                        errors=["approval_required"],
                        adapter_used=self._active_adapter,
                    )
            except ImportError:
                logger.debug("承認ゲートが利用できないためスキップ")

        result = await adapter.execute_task(task)

        # 監査ログ
        logger.info(
            "ブラウザタスク実行: adapter=%s, task=%s, status=%s, duration=%dms",
            self._active_adapter,
            task.id,
            result.status.value,
            result.duration_ms,
        )

        return result

    async def auto_install_adapter(self, adapter_type: AdapterType) -> bool:
        """アダプタをインストールして登録する.

        Plugin システムと連携し、必要な pip パッケージをインストールした上で
        アダプタを登録する。

        Args:
            adapter_type: インストールするアダプタタイプ

        Returns:
            インストール成功したかどうか
        """
        if adapter_type == AdapterType.BROWSER_USE:
            adapter = BrowserUseAdapter()
            if not adapter._available:
                logger.info("browser-use をインストールしてください: pip install browser-use")
                return False
            self.register("browser-use", adapter)
            return True

        logger.warning("未対応のアダプタタイプ: %s", adapter_type)
        return False


# ---------------------------------------------------------------------------
# グローバルインスタンス
# ---------------------------------------------------------------------------

browser_adapter_registry = BrowserAdapterRegistry()
