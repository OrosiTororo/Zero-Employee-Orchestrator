"""ZPCOS Backend — FastAPI entry point.

開発時:  cd backend && uv run python -m app.main
本番時:  PyInstaller .exe が直接起動（Tauri サイドカー経由）
"""

import sys
import os
import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger("zpcos")


def resource_path(relative_path: str) -> Path:
    """PyInstaller --onefile ビルド後は sys._MEIPASS 内、開発時は app/ 基準。"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


# --- Skill Registry (singleton) ---
_skill_registry = None


def get_skill_registry():
    global _skill_registry
    if _skill_registry is None:
        from app.skills.framework import SkillRegistry
        _skill_registry = SkillRegistry()
        builtins_dir = resource_path("skills/builtins")
        _skill_registry.scan_builtins(Path(builtins_dir))
    return _skill_registry


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時の初期化。"""
    from app.auth.authhub import load_connectors
    from app.gateway import init_gateway
    from app.state.machine import init_db
    from app.state.experience import init_experience_db
    from app.state.artifact_bridge import init_artifact_db

    load_connectors()
    await init_gateway()

    db_dir = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "zpcos"
    db_dir.mkdir(parents=True, exist_ok=True)
    await init_db(str(db_dir / "zpcos_tasks.db"))
    await init_experience_db(str(db_dir / "zpcos_experience.db"))
    await init_artifact_db(str(db_dir / "zpcos_artifacts.db"))

    get_skill_registry()

    from app.webhook.dispatcher import init_webhooks
    init_webhooks()

    logger.info("ZPCOS Backend initialized")
    yield


app = FastAPI(
    title="ZPCOS Backend",
    version="0.1.0",
    description="Zero-Prompt Cross-model Orchestration System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Router ---
from app.auth.authhub import router as auth_router  # noqa: E402
app.include_router(auth_router)


# --- Health ---
@app.get("/api/health")
async def health_check():
    from app.gateway import is_ready
    return {"status": "ok", "version": "0.1.0", "gateway_ready": is_ready()}


# --- Interview ---
class InterviewStartRequest(BaseModel):
    input: str


class InterviewRespondRequest(BaseModel):
    session_id: str
    answers: dict


class InterviewFinalizeRequest(BaseModel):
    session_id: str


@app.post("/api/interview/start")
async def interview_start(req: InterviewStartRequest):
    from app.interview.interviewer import start_interview
    session = await start_interview(req.input)
    return session.model_dump()


@app.post("/api/interview/respond")
async def interview_respond(req: InterviewRespondRequest):
    from app.interview.interviewer import process_response
    session = await process_response(req.session_id, req.answers)
    return session.model_dump()


@app.post("/api/interview/finalize")
async def interview_finalize(req: InterviewFinalizeRequest):
    from app.interview.interviewer import finalize
    spec = await finalize(req.session_id)
    return spec.model_dump()


# --- Orchestrate ---
class OrchestrateRequest(BaseModel):
    input: str
    quality_mode: str = "balanced"


class ReproposeRequest(BaseModel):
    feedback: str
    mode: str = "plan_modify"


@app.post("/api/orchestrate")
async def orchestrate(req: OrchestrateRequest):
    from app.orchestrator.orchestrator import start_orchestration
    orch = await start_orchestration(req.input, get_skill_registry(), req.quality_mode)
    return orch.model_dump()


@app.get("/api/orchestrate/{orch_id}")
async def get_orchestration(orch_id: str):
    from app.orchestrator.orchestrator import get_orchestration
    orch = get_orchestration(orch_id)
    if not orch:
        raise HTTPException(404, "Orchestration not found")
    return orch.model_dump()


@app.post("/api/orchestrate/{orch_id}/approve-plan")
async def approve_plan(orch_id: str):
    from app.orchestrator.orchestrator import approve_and_execute
    orch = await approve_and_execute(orch_id, get_skill_registry())
    return orch.model_dump()


@app.post("/api/orchestrate/{orch_id}/repropose")
async def repropose(orch_id: str, req: ReproposeRequest):
    from app.orchestrator.orchestrator import get_orchestration
    from app.orchestrator.repropose import repropose as do_repropose, ReExecuteMode
    orch = get_orchestration(orch_id)
    if not orch or not orch.plan:
        raise HTTPException(404, "Orchestration or plan not found")
    mode = ReExecuteMode(req.mode)
    skills = [s.name for s in get_skill_registry().list_skills()]
    new_plan, diff = await do_repropose(orch.plan, req.feedback, mode, skills)
    orch.plan = new_plan
    return {"plan": new_plan.model_dump(), "diff": diff.model_dump()}


@app.get("/api/orchestrate/{orch_id}/cost")
async def get_cost(orch_id: str):
    from app.orchestrator.orchestrator import get_orchestration
    orch = get_orchestration(orch_id)
    if not orch:
        raise HTTPException(404, "Orchestration not found")
    return orch.cost_estimate or {}


@app.get("/api/orchestrate/{orch_id}/diff")
async def get_diff(orch_id: str):
    return {"diff": "No previous version to compare"}


@app.post("/api/orchestrate/{orch_id}/self-heal")
async def trigger_self_heal(orch_id: str):
    from app.orchestrator.self_healing import self_heal
    from app.state.failure import FailureRecord, FailureType
    from app.orchestrator.orchestrator import get_orchestration
    orch = get_orchestration(orch_id)
    if not orch:
        raise HTTPException(404, "Orchestration not found")
    failure = FailureRecord(
        failure_type=FailureType.UNKNOWN,
        original_error=json.dumps(orch.results.get("error", "Unknown error")),
        message="Self-heal triggered", recoverable=True,
    )
    attempt = await self_heal(orch_id, failure)
    return attempt.model_dump()


@app.get("/api/orchestrate/{orch_id}/heal-history")
async def heal_history(orch_id: str):
    from app.orchestrator.self_healing import get_heal_history
    history = await get_heal_history(orch_id)
    return [h.model_dump() for h in history]


# --- Chat ---
class ChatRequest(BaseModel):
    messages: list[dict]
    model_group: str = "fast"


@app.post("/api/chat")
async def chat(req: ChatRequest):
    from app.gateway import call_llm
    response = await call_llm(req.messages, req.model_group)
    return {"response": response.choices[0].message.content}


# --- Judge ---
class JudgeRequest(BaseModel):
    text: str
    context: str = ""


@app.post("/api/judge")
async def judge_endpoint(req: JudgeRequest):
    from app.judge.pipeline import judge
    result = await judge(req.text, req.context)
    return result.model_dump()


# --- Tasks ---
class CreateTaskRequest(BaseModel):
    skill_name: str
    input_data: dict


class TransitionRequest(BaseModel):
    trigger: str


@app.post("/api/tasks")
async def create_task_endpoint(req: CreateTaskRequest):
    from app.state.machine import create_task
    task = await create_task(req.skill_name, req.input_data)
    return task.model_dump()


@app.get("/api/tasks/{task_id}")
async def get_task_endpoint(task_id: str):
    from app.state.machine import get_task
    task = await get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.model_dump()


@app.post("/api/tasks/{task_id}/transition")
async def transition_task_endpoint(task_id: str, req: TransitionRequest):
    from app.state.machine import transition_task
    task = await transition_task(task_id, req.trigger)
    return task.model_dump()


# --- Skills ---
@app.get("/api/skills")
async def list_skills():
    registry = get_skill_registry()
    return [s.model_dump() for s in registry.list_skills()]


class ExecuteSkillRequest(BaseModel):
    skill_name: str
    input: dict = {}


@app.post("/api/skills/execute")
async def execute_skill(req: ExecuteSkillRequest):
    registry = get_skill_registry()
    skill = registry.get_skill(req.skill_name)
    if not skill:
        raise HTTPException(404, f"Skill '{req.skill_name}' not found")
    result = await skill.execute(req.input)
    return result


class GenerateSkillRequest(BaseModel):
    description: str


@app.post("/api/skills/generate")
async def generate_skill_endpoint(req: GenerateSkillRequest):
    from app.engine.skill_generator import generate_skill
    result = await generate_skill(req.description, get_skill_registry())
    return result.model_dump()


@app.get("/api/skills/gaps")
async def get_skill_gaps():
    return []


# --- Skill Registry ---
@app.get("/api/registry/search")
async def registry_search(q: str = ""):
    from app.skills.registry import search_registry
    results = await search_registry(q)
    return [r.model_dump() for r in results]


class PublishRequest(BaseModel):
    skill_dir: str
    author: str = ""


@app.post("/api/registry/publish")
async def registry_publish(req: PublishRequest):
    from app.skills.registry import publish_skill
    pkg = await publish_skill(req.skill_dir, req.author)
    return pkg.model_dump()


class InstallRequest(BaseModel):
    skill_name: str


@app.post("/api/registry/install")
async def registry_install(req: InstallRequest):
    from app.skills.registry import install_skill
    success = await install_skill(req.skill_name)
    return {"installed": success}


@app.get("/api/registry/popular")
async def registry_popular():
    from app.skills.registry import get_popular
    results = await get_popular()
    return [r.model_dump() for r in results]


# --- Settings ---
_settings = {
    "quality_mode": "balanced",
    "allowed_dirs": [],
}


@app.get("/api/settings")
async def get_settings():
    return _settings


class UpdateSettingsRequest(BaseModel):
    quality_mode: str | None = None
    allowed_dirs: list[str] | None = None


@app.put("/api/settings")
async def update_settings(req: UpdateSettingsRequest):
    if req.quality_mode is not None:
        _settings["quality_mode"] = req.quality_mode
    if req.allowed_dirs is not None:
        _settings["allowed_dirs"] = req.allowed_dirs
        # allowed_dirs.json に保存
        config_dir = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "zpcos"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "allowed_dirs.json").write_text(
            json.dumps(req.allowed_dirs, ensure_ascii=False), encoding="utf-8"
        )
    return _settings


# --- Webhooks ---
class WebhookCreateRequest(BaseModel):
    name: str = ""
    url: str
    events: list[str] | None = None
    active: bool = True


class WebhookUpdateRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    active: bool | None = None


@app.get("/api/webhooks")
async def list_webhooks_endpoint():
    from app.webhook.dispatcher import list_webhooks
    return [w.model_dump() for w in list_webhooks()]


@app.post("/api/webhooks")
async def create_webhook(req: WebhookCreateRequest):
    from app.webhook.dispatcher import register_webhook
    from app.webhook.models import WebhookConfig, WebhookEvent
    events = [WebhookEvent(e) for e in req.events] if req.events else list(WebhookEvent)
    config = WebhookConfig(name=req.name, url=req.url, events=events, active=req.active)
    return register_webhook(config).model_dump()


@app.get("/api/webhooks/{webhook_id}")
async def get_webhook_endpoint(webhook_id: str):
    from app.webhook.dispatcher import get_webhook
    wh = get_webhook(webhook_id)
    if not wh:
        raise HTTPException(404, "Webhook not found")
    return wh.model_dump()


@app.put("/api/webhooks/{webhook_id}")
async def update_webhook_endpoint(webhook_id: str, req: WebhookUpdateRequest):
    from app.webhook.dispatcher import update_webhook
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if req.events is not None:
        from app.webhook.models import WebhookEvent
        updates["events"] = [WebhookEvent(e) for e in req.events]
    wh = update_webhook(webhook_id, updates)
    if not wh:
        raise HTTPException(404, "Webhook not found")
    return wh.model_dump()


@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook_endpoint(webhook_id: str):
    from app.webhook.dispatcher import delete_webhook
    if not delete_webhook(webhook_id):
        raise HTTPException(404, "Webhook not found")
    return {"deleted": True}


@app.post("/api/webhooks/{webhook_id}/test")
async def test_webhook_endpoint(webhook_id: str):
    from app.webhook.dispatcher import test_webhook
    delivery = await test_webhook(webhook_id)
    if not delivery:
        raise HTTPException(404, "Webhook not found")
    return delivery.model_dump()


@app.get("/api/webhooks/{webhook_id}/deliveries")
async def get_deliveries_endpoint(webhook_id: str):
    from app.webhook.dispatcher import get_deliveries
    return [d.model_dump() for d in get_deliveries(webhook_id)]


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18234, reload=False, workers=1)
