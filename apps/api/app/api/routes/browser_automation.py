"""Browser automation, plugin loader, and tool registry API.

- Browser adapter listing, switching, and task execution
- Plugin search, environment check, and installation (Cowork-style plugin management)
- Tool registry (AI agents dynamically select optimal tools)
- Web AI sessions (use AI without API fees)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User

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
# Response models — adapter management
# ---------------------------------------------------------------------------


class SetActiveAdapterResponse(BaseModel):
    active: str
    message: str


# ---------------------------------------------------------------------------
# Response models — plugin loader
# ---------------------------------------------------------------------------


class AvailablePluginResponse(BaseModel):
    slug: str
    name: str
    name_ja: str
    description: str
    description_ja: str
    version: str
    source_uri: str
    category: str
    license: str
    installed: bool
    pypi_package: str | None = None


class PluginSearchResultResponse(BaseModel):
    slug: str
    name: str
    name_ja: str
    description: str
    description_ja: str
    version: str
    source_uri: str
    category: str
    license: str
    installed: bool


class InstalledPluginResponse(BaseModel):
    slug: str
    name: str
    adapter_registered: bool


class EnvCheckItemResponse(BaseModel):
    name: str
    type: str
    status: str
    detail: str
    install_hint: str


class PluginEnvCheckResponse(BaseModel):
    plugin: str
    all_satisfied: bool
    checks: list[EnvCheckItemResponse]
    setup_instructions: list[str]


class PluginInstallEnvironment(BaseModel):
    all_satisfied: bool
    setup_instructions: list[str]
    checks: list[EnvCheckItemResponse] | None = None


class PluginInstallResponse(BaseModel):
    success: bool
    plugin: str | None = None
    slug: str | None = None
    category: str | None = None
    adapter_registered: bool | None = None
    environment: PluginInstallEnvironment | None = None
    transparency: dict = Field(default_factory=dict)
    dry_run: bool | None = None
    error: str | None = None
    available_plugins: list[str] | None = None


class PluginUninstallResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Response models — tool registry
# ---------------------------------------------------------------------------


class ToolInfoResponse(BaseModel):
    slug: str
    category: str
    name: str
    is_active: bool

    model_config = {"extra": "allow"}


class ToolCategoryResponse(BaseModel):
    category: str
    active_tool: str
    tool_count: int
    tools: list[str]


class ToolSelectResponse(BaseModel):
    category: str
    active_tool: str
    message: str


class ToolResolveResponse(BaseModel):
    resolved: bool
    tool: dict | None = None
    message: str | None = None


# ---------------------------------------------------------------------------
# Adapter management endpoints
# ---------------------------------------------------------------------------


@router.get("/adapters", response_model=AdapterListResponse)
async def list_adapters(user: User = Depends(get_current_user)):
    """List registered and installable browser automation adapters."""
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


@router.post("/adapters/active", response_model=SetActiveAdapterResponse)
async def set_active_adapter(req: SetActiveRequest, user: User = Depends(get_current_user)):
    """Switch the active browser automation adapter."""
    from app.tools.browser_adapter import browser_adapter_registry

    if not browser_adapter_registry.set_active(req.adapter_name):
        raise HTTPException(
            status_code=404,
            detail=f"Adapter not found: {req.adapter_name}",
        )
    return {
        "active": req.adapter_name,
        "message": f"Switched active adapter to {req.adapter_name}",
    }


@router.post("/tasks", response_model=BrowserTaskResponse)
async def execute_browser_task(req: BrowserTaskRequest, user: User = Depends(get_current_user)):
    """Execute a browser automation task.

    Runs the task using the active adapter (builtin / browser-use, etc.).
    """
    from app.tools.browser_adapter import BrowserTask, browser_adapter_registry

    # Prompt injection check
    try:
        from app.security.prompt_guard import scan_prompt_injection

        scan_result = scan_prompt_injection(req.instruction)
        if scan_result.threat_level in ("HIGH", "CRITICAL"):
            raise HTTPException(
                status_code=400,
                detail="Suspected prompt injection detected",
            )
    except ImportError:
        logger.warning("prompt_guard module not available — skipping injection check")

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
# Web AI session endpoints
# ---------------------------------------------------------------------------


@router.get("/web-ai/services", response_model=list[WebAIServiceInfo])
async def list_web_ai_services(user: User = Depends(get_current_user)):
    """List Web AI services available without API fees."""
    from app.providers.web_session_provider import web_session_provider

    return web_session_provider.list_services()


@router.get("/web-ai/free-options", response_model=list[FreeOptionInfo])
async def list_free_options(user: User = Depends(get_current_user)):
    """List recommended free AI usage options."""
    from app.providers.web_session_provider import web_session_provider

    return web_session_provider.get_recommended_free_options()


@router.post("/web-ai/complete", response_model=WebSessionResponse)
async def web_ai_complete(req: WebSessionRequest, user: User = Depends(get_current_user)):
    """Send a request to AI via a Web AI session."""
    from app.providers.web_session_provider import WebAIService, web_session_provider

    # Prompt injection check
    try:
        from app.security.prompt_guard import scan_prompt_injection

        scan_result = scan_prompt_injection(req.message)
        if scan_result.threat_level in ("HIGH", "CRITICAL"):
            raise HTTPException(
                status_code=400,
                detail="Suspected prompt injection detected",
            )
    except ImportError:
        logger.warning("prompt_guard module not available — skipping injection check")

    try:
        service = WebAIService(req.service)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported service: {req.service}. Available: {[s.value for s in WebAIService]}",
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
# Plugin loader endpoints — Cowork-style plugin management
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


@router.get("/plugins/available", response_model=list[AvailablePluginResponse])
async def list_available_plugins(user: User = Depends(get_current_user)):
    """List available plugins across all categories.

    Displays plugins for browser automation, image generation, music generation,
    search, data analysis, and more.
    """
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.list_available()


@router.post("/plugins/search", response_model=list[PluginSearchResultResponse])
async def search_plugins(req: PluginSearchRequest, user: User = Depends(get_current_user)):
    """Search for plugins using natural language.

    Search by keywords such as 'browser automation', 'image generation', 'browser-use', etc.
    """
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.search(req.query)


@router.get("/plugins/installed", response_model=list[InstalledPluginResponse])
async def list_installed_plugins(user: User = Depends(get_current_user)):
    """List installed plugins."""
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.list_installed()


@router.post("/plugins/check-env", response_model=PluginEnvCheckResponse)
async def check_plugin_environment(
    req: PluginInstallRequest, user: User = Depends(get_current_user)
):
    """Check plugin environment requirements (pre-install verification)."""
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


@router.post("/plugins/install", response_model=PluginInstallResponse)
async def install_plugin(req: PluginInstallRequest, user: User = Depends(get_current_user)):
    """Install a plugin.

    Executes: dependency check -> package install -> adapter registration -> tool registry.
    Use dry_run=true to preview the steps without installing.

    Response includes a transparency report with source, cost, risk, and permission
    information to help users make informed decisions.
    """
    from app.orchestration.transparency import build_plugin_install_transparency
    from app.services.plugin_loader import plugin_loader

    # Generate transparency report (always shown to user before install)
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

    # Include transparency report in response
    result["transparency"] = transparency
    return result


@router.delete("/plugins/{slug}", response_model=PluginUninstallResponse)
async def uninstall_plugin(slug: str, user: User = Depends(get_current_user)):
    """Uninstall a plugin."""
    from app.services.plugin_loader import plugin_loader

    result = plugin_loader.uninstall_plugin(slug)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Tool registry endpoints — AI agent tool selection infrastructure
# ---------------------------------------------------------------------------


@router.get("/tools", response_model=list[ToolInfoResponse])
async def list_tools(category: str | None = None, user: User = Depends(get_current_user)):
    """List registered tools (filterable by category).

    Displays tools available to AI agent organizations.
    """
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.tool_registry.list_tools(category=category)


@router.get("/tools/categories", response_model=list[ToolCategoryResponse])
async def list_tool_categories(user: User = Depends(get_current_user)):
    """List tool categories and active tools."""
    from app.services.plugin_loader import plugin_loader

    return plugin_loader.tool_registry.list_categories()


@router.post("/tools/select", response_model=ToolSelectResponse)
async def select_active_tool(req: ToolSelectRequest, user: User = Depends(get_current_user)):
    """Switch the active tool for a category.

    For example, when a user says 'use ComfyUI for image generation',
    this switches the active tool for the image-generation category to comfyui.
    """
    from app.services.plugin_loader import plugin_loader

    if not plugin_loader.tool_registry.set_active_tool(req.category, req.slug):
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{req.slug}' not found in category '{req.category}'",
        )
    return {
        "category": req.category,
        "active_tool": req.slug,
        "message": f"Switched active tool for {req.category} to {req.slug}",
    }


@router.post("/tools/resolve", response_model=ToolResolveResponse)
async def resolve_tool_for_task(req: ToolResolveRequest, user: User = Depends(get_current_user)):
    """Auto-select the optimal tool for a task description.

    Called by AI agents when executing tasks.
    Infers the category from the task content and returns the active tool.
    """
    from app.services.plugin_loader import plugin_loader

    tool = plugin_loader.tool_registry.resolve_tool_for_task(req.task_description)
    if tool is None:
        return {"resolved": False, "message": "No matching tool found"}
    return {"resolved": True, "tool": tool}
