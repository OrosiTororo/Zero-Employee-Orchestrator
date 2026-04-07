"""API route registration."""

from fastapi import APIRouter

from app.api.routes import (
    agents,
    ai_tools,
    app_integrations,
    approvals,
    artifacts,
    audit,
    auth,
    browser_assist,
    browser_automation,
    budgets,
    companies,
    compliance,
    config,
    dispatch,
    export,
    file_upload,
    governance,
    heartbeats,
    ipaas,
    knowledge,
    language_packs,
    marketplace,
    media_generation,
    models,
    multi_model,
    nl_command,
    observability,
    ollama,
    operator_profile,
    org_setup,
    platform,
    projects,
    quality_insights,
    registry,
    resource_import,
    secretary,
    security_settings,
    self_improvement,
    settings,
    specs_plans,
    sso,
    tasks,
    team,
    themes,
    tickets,
    user_input,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(tickets.router, tags=["tickets"])
api_router.include_router(specs_plans.router, tags=["specs-plans"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(artifacts.router, tags=["artifacts"])
api_router.include_router(approvals.router, tags=["approvals"])
api_router.include_router(heartbeats.router, tags=["heartbeats"])
api_router.include_router(budgets.router, tags=["budgets"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(registry.router, prefix="/registry", tags=["registry"])
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(config.router, tags=["config"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(observability.router, tags=["observability"])
api_router.include_router(ollama.router, tags=["ollama"])
api_router.include_router(knowledge.router, tags=["knowledge"])
api_router.include_router(platform.router, tags=["platform"])
api_router.include_router(org_setup.router, prefix="/org-setup", tags=["org-setup"])
api_router.include_router(secretary.router, tags=["secretary"])
api_router.include_router(
    multi_model.router, tags=["multi-model", "brainstorm", "conversation-memory"]
)
api_router.include_router(self_improvement.router, tags=["self-improvement"])
api_router.include_router(browser_assist.router, tags=["browser-assist"])
api_router.include_router(browser_automation.router, tags=["browser-automation", "web-ai"])
api_router.include_router(security_settings.router, tags=["security"])
api_router.include_router(media_generation.router, tags=["media-generation"])
api_router.include_router(ai_tools.router, tags=["ai-tools"])
api_router.include_router(app_integrations.router, tags=["app-integrations"])
api_router.include_router(file_upload.router, tags=["files"])
api_router.include_router(user_input.router, tags=["user-input"])
api_router.include_router(resource_import.router, tags=["resources"])
api_router.include_router(ipaas.router, tags=["ipaas"])
api_router.include_router(export.router, tags=["export"])
api_router.include_router(marketplace.router, tags=["marketplace"])
api_router.include_router(team.router, tags=["teams"])
api_router.include_router(governance.router, tags=["governance"])
api_router.include_router(language_packs.router, tags=["language-packs"])
api_router.include_router(themes.router, tags=["themes"])
api_router.include_router(nl_command.router, tags=["nl-command"])
api_router.include_router(operator_profile.router, tags=["operator-profile"])
api_router.include_router(dispatch.router, tags=["dispatch"])
api_router.include_router(
    quality_insights.router,
    tags=[
        "quality-insights",
        "prerequisite-monitor",
        "spec-contradiction",
        "task-replay",
        "judgment-review",
        "plan-quality",
    ],
)
api_router.include_router(sso.router, tags=["sso", "saml", "enterprise"])
api_router.include_router(compliance.router, tags=["compliance", "audit-export", "enterprise"])
