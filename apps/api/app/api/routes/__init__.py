"""API route registration."""

from fastapi import APIRouter

from app.api.routes import (
    agents,
    approvals,
    artifacts,
    audit,
    auth,
    budgets,
    companies,
    heartbeats,
    projects,
    registry,
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
