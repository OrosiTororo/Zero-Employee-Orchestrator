"""API route registration."""

from fastapi import APIRouter

from app.api.routes import (
    agents,
    ai_tools,
    approvals,
    artifacts,
    audit,
    auth,
    browser_assist,
    budgets,
    companies,
    config,
    heartbeats,
    knowledge,
    media_generation,
    models,
    multi_model,
    observability,
    ollama,
    org_setup,
    platform,
    projects,
    registry,
    secretary,
    security_settings,
    self_improvement,
    settings,
    specs_plans,
    tasks,
    tickets,
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
api_router.include_router(security_settings.router, tags=["security"])
api_router.include_router(media_generation.router, tags=["media-generation"])
api_router.include_router(ai_tools.router, tags=["ai-tools"])
