"""ブラウザ自動操作・プラグインローダー・ツールレジストリ API.

- ブラウザアダプタの一覧・切替・タスク実行
- プラグインの検索・環境チェック・インストール（VSCode 的な拡張管理）
- ツールレジストリ（AI エージェントが動的にツールを選択）
- Web AI セッション（API 料金なしで AI を利用）
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/browser-automation")


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class AdapterInfoResponse(BaseModel):
    adapter_type: str
    name: str
    version: str
    description: str
    installed: bool
    install_package: str
    capabilities: dict


class AdapterListResponse(BaseModel):
    active: str
    adapters: list[AdapterInfoResponse]
    installable: list[AdapterInfoResponse]


class SetActiveRequest(BaseModel):
    adapter_name: str


class BrowserTaskRequest(BaseModel):
    instruction: str = Field(..., min_length=1, max_length=5000)
    url: str | None = None
    max_steps: int = Field(default=30, ge=1, le=100)
    timeout_seconds: int = Field(default=300, ge=10, le=600)


class BrowserTaskResponse(BaseModel):
    task_id: str
    status: str
    output: str
    extracted_data: dict
    steps_executed: int
    errors: list[str]
    duration_ms: int
    adapter_used: str
    replanned: bool


class WebAIServiceInfo(BaseModel):
    service: str
    name: str
    url: str
    free_tier: bool
    free_model: str
    subscription_model: str
    subscription_name: str
    cookie_configured: bool
    cost_usd: float


class FreeOptionInfo(BaseModel):
    method: str
    name: str
    description: str
    setup: str
    stability: str
    rate_limit: str
    cost: float
    recommended: bool


class WebSessionRequest(BaseModel):
    service: str
    message: str = Field(..., min_length=1, max_length=10000)


class WebSessionResponse(BaseModel):
    content: str
    service: str
    model_hint: str
    cost_usd: float
    finish_reason: str


# ---------------------------------------------------------------------------
# アダプタ管理エンドポイント
# ---------------------------------------------------------------------------


@router.get("/adapters", response_model=AdapterListResponse)
async def list_adapters():
    """登録済み・インストール可能なブラウザ自動操作アダプタ一覧."""
    from app.tools.browser_adapter import browser_adapter_registry

    adapters = []
    for info in browser_adapter_registry.list_adapters():
        adapters.append(
            AdapterInfoResponse(
                adapter_type=info.adapter_type.value,
                name=info.name,
                version=info.version,
                description=info.description,
                installed=info.installed,
                install_package=info.install_package,
                capabilities={
                    "natural_language_control": info.capabilities.natural_language_control,
                    "loop_detection": info.capabilities.loop_detection,
                    "auto_replanning": info.capabilities.auto_replanning,
                    "screenshot_analysis": info.capabilities.screenshot_analysis,
                    "dom_inspection": info.capabilities.dom_inspection,
                    "form_filling": info.capabilities.form_filling,
                    "navigation": info.capabilities.navigation,
                    "data_extraction": info.capabilities.data_extraction,
                    "headless": info.capabilities.headless,
                },
            )
        )

    installable = []
    for info in browser_adapter_registry.list_installable():
        installable.append(
            AdapterInfoResponse(
                adapter_type=info.adapter_type.value,
                name=info.name,
                version=info.version,
                description=info.description,
                installed=info.installed,
                install_package=info.install_package,
                capabilities={
                    "natural_language_control": info.capabilities.natural_language_control,
                    "loop_detection": info.capabilities.loop_detection,
                    "auto_replanning": info.capabilities.auto_replanning,
                    "screenshot_analysis": info.capabilities.screenshot_analysis,
                    "dom_inspection": info.capabilities.dom_inspection,
                    "form_filling": info.capabilities.form_filling,
                    "navigation": info.capabilities.navigation,
                    "data_extraction": info.capabilities.data_extraction,
                    "headless": info.capabilities.headless,
                },
            )
        )

    return AdapterListResponse(
        active=browser_adapter_registry.get_active_name(),
        adapters=adapters,
        installable=installable,
    )


@router.post("/adapters/active")
async def set_active_adapter(req: SetActiveRequest):
    """アクティブなブラウザ自動操作アダプタを切り替える."""
    from app.tools.browser_adapter import browser_adapter_registry

    if not browser_adapter_registry.set_active(req.adapter_name):
        raise HTTPException(
            status_code=404,
            detail=f"アダプタが見つかりません: {req.adapter_name}",
        )
    return {
        "active": req.adapter_name,
        "message": f"アダプタを {req.adapter_name} に切り替えました",
    }


@router.post("/tasks", response_model=BrowserTaskResponse)
async def execute_browser_task(req: BrowserTaskRequest):
    """ブラウザ自動操作タスクを実行する.

    アクティブなアダプタ (builtin / browser-use 等) でタスクを実行する。
    """
    from app.tools.browser_adapter import BrowserTask, browser_adapter_registry

    # プロンプトインジェクション検査
    try:
        from app.security.prompt_guard import scan_prompt_injection

        scan_result = scan_prompt_injection(req.instruction)
        if scan_result.threat_level in ("HIGH", "CRITICAL"):
            raise HTTPException(
                status_code=400,
                detail="プロンプトインジェクションの疑いがあります",
            )
    except ImportError:
        pass

    task = BrowserTask(
        instruction=req.instruction,
        url=req.url,
        max_steps=req.max_steps,
        timeout_seconds=req.timeout_seconds,
    )

    result = await browser_adapter_registry.execute_task(task)

    return BrowserTaskResponse(
        task_id=result.task_id,
        status=result.status.value,
        output=result.output,
        extracted_data=result.extracted_data,
        steps_executed=result.steps_executed,
        errors=result.errors,
        duration_ms=result.duration_ms,
        adapter_used=result.adapter_used,
        replanned=result.replanned,
    )


# ---------------------------------------------------------------------------
# Web AI セッションエンドポイント
# ---------------------------------------------------------------------------


@router.get("/web-ai/services", response_model=list[WebAIServiceInfo])
async def list_web_ai_services():
    """API 料金なしで利用可能な Web AI サービス一覧."""
    from app.providers.web_session_provider import web_session_provider

    return web_session_provider.list_services()


@router.get("/web-ai/free-options", response_model=list[FreeOptionInfo])
async def list_free_options():
    """無料で AI を利用する方法の推奨一覧."""
    from app.providers.web_session_provider import web_session_provider

    return web_session_provider.get_recommended_free_options()


@router.post("/web-ai/complete", response_model=WebSessionResponse)
async def web_ai_complete(req: WebSessionRequest):
    """Web AI セッション経由で AI にリクエストを送信する."""
    from app.providers.web_session_provider import WebAIService, web_session_provider

    # プロンプトインジェクション検査
    try:
        from app.security.prompt_guard import scan_prompt_injection

        scan_result = scan_prompt_injection(req.message)
        if scan_result.threat_level in ("HIGH", "CRITICAL"):
            raise HTTPException(
                status_code=400,
                detail="プロンプトインジェクションの疑いがあります",
            )
    except ImportError:
        pass

    try:
        service = WebAIService(req.service)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"未対応のサービス: {req.service}。利用可能: {[s.value for s in WebAIService]}",
        )

    messages = [{"role": "user", "content": req.message}]
    result = await web_session_provider.complete(service=service, messages=messages)

    return WebSessionResponse(
        content=result.content,
        service=result.service,
        model_hint=result.model_hint,
        cost_usd=result.cost_usd,
        finish_reason=result.finish_reason,
    )


# ---------------------------------------------------------------------------
# プラグインローダーエンドポイント — VSCode 的なプラグイン管理
# ---------------------------------------------------------------------------


class PluginSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


class PluginInstallRequest(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    auto_install_packages: bool = False
    dry_run: bool = False


class ToolSelectRequest(BaseModel):
    category: str
    slug: str


class ToolResolveRequest(BaseModel):
    task_description: str = Field(..., min_length=1, max_length=2000)


@router.get("/plugins/available")
async def list_available_plugins():
    """インストール可能なプラグイン一覧（全カテゴリ）.

    ブラウザ操作、画像生成、音楽生成、検索、データ分析など
    あらゆるカテゴリのプラグインを一覧表示。
    """
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.list_available()


@router.post("/plugins/search")
async def search_plugins(req: PluginSearchRequest):
    """自然言語でプラグインを検索する.

    「ブラウザ操作」「画像生成」「browser-use」等のキーワードで検索。
    """
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.search(req.query)


@router.get("/plugins/installed")
async def list_installed_plugins():
    """インストール済みプラグイン一覧."""
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.list_installed()


@router.post("/plugins/check-env")
async def check_plugin_environment(req: PluginInstallRequest):
    """プラグインの環境要件をチェックする（インストール前の確認）."""
    from app.services.plugin_loader import plugin_loader

    report = plugin_loader.check_environment(req.slug)
    return {
        "plugin": report.plugin_name,
        "all_satisfied": report.all_satisfied,
        "checks": [
            {
                "name": r.requirement.name,
                "type": r.requirement.type.value,
                "status": r.status.value,
                "detail": r.detail,
                "install_hint": r.requirement.install_hint,
            }
            for r in report.results
        ],
        "setup_instructions": report.setup_instructions,
    }


@router.post("/plugins/install")
async def install_plugin(req: PluginInstallRequest):
    """プラグインをインストールする.

    依存関係チェック → パッケージインストール → アダプタ登録 → ツールレジストリ登録
    の順に実行。dry_run=true で手順のみ確認可能。

    レスポンスには透明性レポートが含まれ、ユーザーが正確な判断を
    行うための情報（ソース、コスト、リスク、権限等）を提示する。
    """
    from app.orchestration.transparency import build_plugin_install_transparency
    from app.services.plugin_loader import plugin_loader

    # 透明性レポートの生成（インストール前に常にユーザーに提示）
    template = plugin_loader.get_template(req.slug)
    env_report = plugin_loader.check_environment(req.slug)
    transparency = {}
    if template:
        transparency = build_plugin_install_transparency(
            template=template,
            env_report_dict={
                "all_satisfied": env_report.all_satisfied,
                "setup_instructions": env_report.setup_instructions,
            },
        )

    result = await plugin_loader.install_plugin(
        slug=req.slug,
        auto_install_packages=req.auto_install_packages,
        dry_run=req.dry_run,
    )

    # 透明性レポートをレスポンスに含める
    result["transparency"] = transparency
    return result


@router.delete("/plugins/{slug}")
async def uninstall_plugin(slug: str):
    """プラグインをアンインストールする."""
    from app.services.plugin_loader import plugin_loader

    result = plugin_loader.uninstall_plugin(slug)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# ツールレジストリエンドポイント — AI エージェントのツール選択基盤
# ---------------------------------------------------------------------------


@router.get("/tools")
async def list_tools(category: str | None = None):
    """登録済みツール一覧（カテゴリフィルター可）.

    AI エージェント組織が利用可能なツールを一覧表示する。
    """
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.tool_registry.list_tools(category=category)


@router.get("/tools/categories")
async def list_tool_categories():
    """ツールカテゴリ一覧とアクティブツール."""
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.tool_registry.list_categories()


@router.post("/tools/select")
async def select_active_tool(req: ToolSelectRequest):
    """カテゴリのアクティブツールを切り替える.

    ユーザーが「画像生成は ComfyUI を使って」と言った場合、
    image-generation カテゴリのアクティブツールを comfyui に切り替える。
    """
    from app.services.plugin_loader import plugin_loader

    if not plugin_loader.tool_registry.set_active_tool(req.category, req.slug):
        raise HTTPException(
            status_code=404,
            detail=f"カテゴリ '{req.category}' にツール '{req.slug}' が見つかりません",
        )
    return {
        "category": req.category,
        "active_tool": req.slug,
        "message": f"{req.category} のアクティブツールを {req.slug} に変更しました",
    }


@router.post("/tools/resolve")
async def resolve_tool_for_task(req: ToolResolveRequest):
    """タスク記述文から最適なツールを自動選択する.

    AI エージェントがタスクを実行する際に呼ぶ。
    タスクの内容からカテゴリを推定し、アクティブツールを返す。
    """
    from app.services.plugin_loader import plugin_loader

    tool = plugin_loader.tool_registry.resolve_tool_for_task(req.task_description)
    if tool is None:
        return {"resolved": False, "message": "該当するツールが見つかりません"}
    return {"resolved": True, "tool": tool}
