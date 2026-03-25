"""ブラウザ自動操作アダプタ + プラグインローダー + 透明性レイヤーのテスト."""

import pytest
from httpx import AsyncClient

from app.orchestration.transparency import (
    SourceType,
    TransparencyBuilder,
    build_plugin_install_transparency,
)
from app.providers.web_session_provider import (
    WebAIService,
    WebSessionProvider,
)
from app.services.plugin_loader import (
    PluginLoader,
    ToolRegistry,
)
from app.tools.browser_adapter import (
    AdapterType,
    BrowserAdapterRegistry,
    BrowserTask,
    BrowserUseAdapter,
    BuiltinPlaywrightAdapter,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# ユニットテスト — BrowserAdapterRegistry
# ---------------------------------------------------------------------------


class TestBrowserAdapterRegistry:
    def test_initial_state_has_only_builtin(self):
        """初期状態ではビルトインアダプタのみ登録されている."""
        registry = BrowserAdapterRegistry()
        adapters = registry.list_adapters()
        assert len(adapters) == 1
        assert adapters[0].adapter_type == AdapterType.BUILTIN

    def test_active_adapter_default_is_builtin(self):
        registry = BrowserAdapterRegistry()
        assert registry.get_active_name() == "builtin"

    def test_register_and_switch_adapter(self):
        """アダプタの登録と切替が正しく動作する."""
        registry = BrowserAdapterRegistry()
        adapter = BrowserUseAdapter()
        registry.register("browser-use", adapter)

        assert len(registry.list_adapters()) == 2
        assert registry.set_active("browser-use")
        assert registry.get_active_name() == "browser-use"

    def test_unregister_builtin_fails(self):
        """ビルトインアダプタは登録解除できない."""
        registry = BrowserAdapterRegistry()
        assert not registry.unregister("builtin")

    def test_unregister_custom_adapter(self):
        """カスタムアダプタは登録解除できる."""
        registry = BrowserAdapterRegistry()
        registry.register("browser-use", BrowserUseAdapter())
        registry.set_active("browser-use")

        assert registry.unregister("browser-use")
        # ビルトインにフォールバック
        assert registry.get_active_name() == "builtin"

    def test_set_active_unknown_adapter_fails(self):
        registry = BrowserAdapterRegistry()
        assert not registry.set_active("nonexistent")

    def test_list_installable_excludes_registered(self):
        """登録済みアダプタはインストール可能リストに含まれない."""
        registry = BrowserAdapterRegistry()
        installable = registry.list_installable()
        # browser-use と selenium がインストール可能
        types = [a.adapter_type for a in installable]
        assert AdapterType.BROWSER_USE in types
        assert AdapterType.SELENIUM in types

        # browser-use を登録するとリストから消える
        registry.register("browser-use", BrowserUseAdapter())
        installable = registry.list_installable()
        types = [a.adapter_type for a in installable]
        assert AdapterType.BROWSER_USE not in types


# ---------------------------------------------------------------------------
# ユニットテスト — BuiltinPlaywrightAdapter
# ---------------------------------------------------------------------------


class TestBuiltinPlaywrightAdapter:
    def test_info(self):
        adapter = BuiltinPlaywrightAdapter()
        info = adapter.info()
        assert info.adapter_type == AdapterType.BUILTIN
        assert info.capabilities.navigation is True
        assert info.capabilities.natural_language_control is False

    @pytest.mark.asyncio
    async def test_execute_task_without_playwright(self):
        """Playwright 未インストール時はエラーを返す."""
        adapter = BuiltinPlaywrightAdapter()
        task = BrowserTask(instruction="test", url="https://example.com")
        result = await adapter.execute_task(task)
        # Playwright がインストールされていない CI 環境では FAILED
        assert result.task_id == task.id
        assert result.adapter_used == "builtin"


# ---------------------------------------------------------------------------
# ユニットテスト — BrowserUseAdapter
# ---------------------------------------------------------------------------


class TestBrowserUseAdapter:
    def test_info(self):
        adapter = BrowserUseAdapter()
        info = adapter.info()
        assert info.adapter_type == AdapterType.BROWSER_USE
        assert info.capabilities.natural_language_control is True
        assert info.capabilities.loop_detection is True
        assert info.capabilities.auto_replanning is True

    @pytest.mark.asyncio
    async def test_execute_task_without_browser_use(self):
        """browser-use 未インストール時はエラーを返す."""
        adapter = BrowserUseAdapter()
        task = BrowserTask(instruction="Search for something")
        result = await adapter.execute_task(task)
        assert result.status == TaskStatus.FAILED
        assert "browser-use" in result.output


# ---------------------------------------------------------------------------
# ユニットテスト — WebSessionProvider
# ---------------------------------------------------------------------------


class TestWebSessionProvider:
    def test_list_services(self):
        provider = WebSessionProvider()
        services = provider.list_services()
        assert len(services) > 0
        names = [s["service"] for s in services]
        assert "chatgpt" in names
        assert "gemini" in names
        assert "claude" in names

    def test_all_services_have_zero_cost(self):
        """Web AI セッションは全て cost_usd=0."""
        provider = WebSessionProvider()
        for service in provider.list_services():
            assert service["cost_usd"] == 0.0

    def test_free_options(self):
        provider = WebSessionProvider()
        options = provider.get_recommended_free_options()
        assert len(options) >= 3
        methods = [o["method"] for o in options]
        assert "gemini_free_api" in methods
        assert "g4f" in methods
        assert "ollama" in methods

    @pytest.mark.asyncio
    async def test_complete_fallback(self):
        """g4f も browser-use もない場合はエラーレスポンスを返す."""
        provider = WebSessionProvider()
        result = await provider.complete(
            service=WebAIService.CHATGPT,
            messages=[{"role": "user", "content": "Hello"}],
        )
        # g4f 未インストール環境ではエラー
        assert result.service == "chatgpt"
        assert result.cost_usd == 0.0


# ---------------------------------------------------------------------------
# API エンドポイントテスト
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_adapters_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/browser-automation/adapters")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] == "builtin"
    assert len(data["adapters"]) >= 1


@pytest.mark.asyncio
async def test_set_active_adapter_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/v1/browser-automation/adapters/active",
        json={"adapter_name": "nonexistent"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_web_ai_services_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/browser-automation/web-ai/services")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert all(s["cost_usd"] == 0.0 for s in data)


@pytest.mark.asyncio
async def test_web_ai_free_options_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/browser-automation/web-ai/free-options")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_web_ai_complete_invalid_service(client: AsyncClient):
    resp = await client.post(
        "/api/v1/browser-automation/web-ai/complete",
        json={"service": "invalid", "message": "Hello"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# ユニットテスト — PluginLoader (汎用プラグインシステム)
# ---------------------------------------------------------------------------


class TestPluginLoader:
    def test_search_by_name(self):
        """プラグイン名で検索できる."""
        loader = PluginLoader()
        results = loader.search("browser-use")
        assert any(r["slug"] == "browser-use" for r in results)

    def test_search_by_category_japanese(self):
        """日本語カテゴリキーワードで検索できる."""
        loader = PluginLoader()
        assert any(r["slug"] in ("comfyui", "flux") for r in loader.search("画像"))
        assert any(r["slug"] in ("suno-api", "musicgen") for r in loader.search("音楽"))

    def test_list_available_covers_multiple_categories(self):
        """全カテゴリのプラグインが一覧に含まれる."""
        loader = PluginLoader()
        available = loader.list_available()
        categories = {a["category"] for a in available}
        assert "browser-automation" in categories
        assert "image-generation" in categories
        assert "music-generation" in categories

    def test_environment_check(self):
        """環境チェックがレポートを返す."""
        loader = PluginLoader()
        report = loader.check_environment("browser-use")
        assert report.plugin_name
        assert len(report.results) > 0

    def test_environment_check_unknown_plugin(self):
        loader = PluginLoader()
        report = loader.check_environment("nonexistent")
        assert not report.all_satisfied


# ---------------------------------------------------------------------------
# ユニットテスト — ToolRegistry (AI エージェントのツール選択)
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_register_and_active_default(self):
        """最初に登録したツールがデフォルトでアクティブ."""
        registry = ToolRegistry()
        registry.register_tool("comfyui", "image-generation", {"name": "ComfyUI"})
        registry.register_tool("flux", "image-generation", {"name": "Flux"})
        assert registry.get_active_tool("image-generation") == "comfyui"

    def test_switch_active_tool(self):
        """アクティブツールを切り替えられる."""
        registry = ToolRegistry()
        registry.register_tool("comfyui", "image-generation", {"name": "ComfyUI"})
        registry.register_tool("flux", "image-generation", {"name": "Flux"})
        assert registry.set_active_tool("image-generation", "flux")
        assert registry.get_active_tool("image-generation") == "flux"

    def test_resolve_tool_for_task_japanese(self):
        """日本語タスク記述からツールを自動解決できる."""
        registry = ToolRegistry()
        registry.register_tool("comfyui", "image-generation", {"name": "ComfyUI"})
        registry.register_tool("bu", "browser-automation", {"name": "browser-use"})

        tool = registry.resolve_tool_for_task("この画像を生成してください")
        assert tool is not None
        assert tool["name"] == "ComfyUI"

        tool = registry.resolve_tool_for_task("ブラウザでページを開いて")
        assert tool is not None
        assert tool["name"] == "browser-use"

    def test_resolve_returns_none_for_unknown(self):
        registry = ToolRegistry()
        assert registry.resolve_tool_for_task("天気を教えて") is None

    def test_unregister_with_fallback(self):
        """ツール削除時にアクティブが別ツールにフォールバック."""
        registry = ToolRegistry()
        registry.register_tool("a", "cat", {"name": "A"})
        registry.register_tool("b", "cat", {"name": "B"})
        registry.set_active_tool("cat", "b")
        registry.unregister_tool("b")
        assert registry.get_active_tool("cat") == "a"


# ---------------------------------------------------------------------------
# ユニットテスト — TransparencyBuilder (透明性・ファクトチェック)
# ---------------------------------------------------------------------------


class TestTransparencyBuilder:
    def test_build_report(self):
        """透明性レポートを正しく構築できる."""
        builder = TransparencyBuilder()
        builder.add_source(SourceType.WEB_PAGE, "Test", "https://example.com")
        builder.add_fact_check("Claim", needs_verification=True)
        builder.add_approval_info("cost", "Cost", "Free")
        builder.set_reasoning("Reasoning")
        builder.add_uncertainty("Uncertain")
        builder.add_question("Confirm?")

        d = builder.to_dict()
        assert len(d["sources"]) == 1
        assert d["fact_checks"][0]["needs_verification"] is True
        assert len(d["approval_info"]) == 1
        assert d["reasoning_summary"] == "Reasoning"
        assert len(d["uncertainties"]) == 1
        assert len(d["questions_for_user"]) == 1

    def test_plugin_install_transparency(self):
        """プラグインインストール時の透明性レポートが情報を含む."""
        template = {
            "name": "Test",
            "source_uri": "https://github.com/test/test",
            "pypi_package": "test",
            "category": "test",
            "license": "MIT",
            "requirements": [
                {
                    "type": "api_key",
                    "name": "KEY",
                    "required": True,
                    "install_hint": "Set KEY",
                },
            ],
            "safety": {"dangerous_operations": ["write"]},
            "required_permissions": ["internet"],
        }
        report = build_plugin_install_transparency(
            template, {"all_satisfied": False, "setup_instructions": ["Install"]}
        )
        assert len(report["sources"]) >= 2  # repo + pypi + catalog
        assert len(report["approval_info"]) >= 3  # cost + external + perm + reverse
        assert report["reasoning_summary"]
