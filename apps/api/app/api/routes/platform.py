"""Platform API — MCP・外部スキル・Sentry・IAM・仮説検証・セッション管理.

v0.1 で追加されたプラットフォーム横断的な機能のAPIエンドポイント。
"""

from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db

router = APIRouter()


# ===================================================================
# MCP エンドポイント
# ===================================================================


class MCPToolCallRequest(BaseModel):
    name: str
    arguments: dict = {}


@router.get("/mcp/capabilities")
async def mcp_capabilities():
    """MCP サーバーのケイパビリティを取得."""
    from app.integrations.mcp_server import mcp_server

    return mcp_server.get_capabilities()


@router.get("/mcp/tools")
async def mcp_list_tools():
    """MCP ツール一覧."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_list_tools()


@router.post("/mcp/tools/call")
async def mcp_call_tool(req: MCPToolCallRequest):
    """MCP ツール実行."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_call_tool(req.name, req.arguments)


@router.get("/mcp/resources")
async def mcp_list_resources():
    """MCP リソース一覧."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_list_resources()


@router.get("/mcp/prompts")
async def mcp_list_prompts():
    """MCP プロンプト一覧."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_list_prompts()


# ===================================================================
# 外部スキルインポート エンドポイント
# ===================================================================


class SkillSearchRequest(BaseModel):
    query: str
    source_type: str | None = None
    limit: int = 20


class SkillImportRequest(BaseModel):
    source_type: (
        str  # github_agent_skills, skills_sh, openclaw, claude_code, git_repo, url
    )
    source_uri: str


@router.post("/skills/external/search")
async def search_external_skills(req: SkillSearchRequest):
    """外部ソースからスキルを検索."""
    from app.integrations.external_skills import skill_importer, SkillSourceType

    source = SkillSourceType(req.source_type) if req.source_type else None
    results = await skill_importer.search_skills(req.query, source, req.limit)
    return {
        "results": [
            {
                "name": r.name,
                "slug": r.slug,
                "description": r.description,
                "source_type": r.source_type,
                "source_uri": r.source_uri,
                "author": r.author,
                "stars": r.stars,
                "downloads": r.downloads,
            }
            for r in results
        ],
        "total": len(results),
    }


@router.post("/skills/external/import")
async def import_external_skill(
    req: SkillImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """外部ソースからスキルをインポートしてインストール."""
    from app.integrations.external_skills import skill_importer, SkillSourceType
    from app.services import skill_service
    from app.schemas.registry import SkillCreate

    source_type = SkillSourceType(req.source_type)
    manifest = await skill_importer.fetch_skill_manifest(source_type, req.source_uri)
    if not manifest:
        raise HTTPException(
            status_code=404, detail="スキルマニフェストが取得できません"
        )

    data = skill_importer.to_skill_create_data(manifest)

    # 既存チェック
    existing = await skill_service.get_skill_by_slug(db, data["slug"])
    if existing:
        raise HTTPException(
            status_code=409, detail=f"スキル '{data['slug']}' は既に存在します"
        )

    skill = await skill_service.create_skill(db, SkillCreate(**data))
    await db.commit()

    return {
        "installed": True,
        "skill_id": str(skill.id),
        "name": skill.name,
        "slug": skill.slug,
        "source": req.source_type,
    }


# ===================================================================
# Sentry連携 エンドポイント
# ===================================================================


@router.get("/sentry/stats")
async def sentry_stats():
    """Sentryエラー統計."""
    from app.integrations.sentry_integration import sentry

    return sentry.get_error_stats()


@router.get("/sentry/events")
async def sentry_events(
    level: str | None = None,
    event_type: str | None = None,
    limit: int = 50,
):
    """Sentryイベント一覧."""
    from app.integrations.sentry_integration import sentry, SeverityLevel, EventType

    lvl = SeverityLevel(level) if level else None
    et = EventType(event_type) if event_type else None
    events = sentry.get_recent_events(lvl, et, limit)
    return {
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }


@router.post("/sentry/capture")
async def sentry_capture_message(
    message: str = "",
    level: str = "info",
    tags: dict | None = None,
):
    """カスタムイベントをキャプチャ."""
    from app.integrations.sentry_integration import sentry, SeverityLevel

    event_id = sentry.capture_message(message, SeverityLevel(level), tags=tags)
    return {"event_id": event_id, "captured": True}


# ===================================================================
# IAM エンドポイント
# ===================================================================


class CreateAIAccountRequest(BaseModel):
    agent_id: str
    account_name: str
    company_id: str | None = None
    custom_permissions: list[str] | None = None


@router.post("/iam/ai-accounts")
async def create_ai_account(
    req: CreateAIAccountRequest,
    db: AsyncSession = Depends(get_db),
):
    """AIエージェント用サービスアカウントを作成."""
    from app.security.iam import iam_manager

    account, token = await iam_manager.create_ai_account(
        db,
        req.agent_id,
        req.account_name,
        company_id=req.company_id,
        custom_permissions=req.custom_permissions,
    )
    await db.commit()
    return {
        "account_id": str(account.id),
        "agent_id": account.agent_id,
        "account_name": account.account_name,
        "token": token,  # 一度だけ表示
        "permissions": account.permissions,
    }


@router.get("/iam/ai-accounts")
async def list_ai_accounts(
    company_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """AIサービスアカウント一覧."""
    from app.security.iam import iam_manager

    accounts = await iam_manager.list_ai_accounts(db, company_id)
    return {
        "accounts": [
            {
                "id": str(a.id),
                "agent_id": a.agent_id,
                "account_name": a.account_name,
                "account_type": a.account_type,
                "permissions": a.permissions,
                "is_active": a.is_active,
                "last_used_at": str(a.last_used_at) if a.last_used_at else None,
            }
            for a in accounts
        ],
    }


@router.delete("/iam/ai-accounts/{account_id}")
async def revoke_ai_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """AIサービスアカウントを無効化."""
    from app.security.iam import iam_manager

    ok = await iam_manager.revoke_ai_account(db, account_id)
    await db.commit()
    if not ok:
        raise HTTPException(status_code=404, detail="アカウントが見つかりません")
    return {"revoked": True}


# ===================================================================
# AI Investigator エンドポイント
# ===================================================================


class DBQueryRequest(BaseModel):
    query: str = Field(..., description="SELECT文のみ実行可能")
    params: dict | None = None


class AuditSearchRequest(BaseModel):
    action_type: str | None = None
    entity_type: str | None = None
    actor_id: str | None = None
    since_hours: int = 24
    limit: int = 100


@router.post("/investigate/query")
async def investigate_query(
    req: DBQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """AI調査: 安全なDB読み取りクエリ."""
    from app.integrations.ai_investigator import ai_investigator

    result = await ai_investigator.query_db(db, req.query, req.params)
    return result.to_dict()


@router.post("/investigate/audit")
async def investigate_audit(
    req: AuditSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """AI調査: 監査ログ検索."""
    from app.integrations.ai_investigator import ai_investigator

    result = await ai_investigator.search_audit_logs(
        db,
        action_type=req.action_type,
        entity_type=req.entity_type,
        actor_id=req.actor_id,
        since_hours=req.since_hours,
        limit=req.limit,
    )
    return result.to_dict()


@router.get("/investigate/errors")
async def investigate_errors(
    since_hours: int = 24,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """AI調査: エラーパターン分析."""
    from app.integrations.ai_investigator import ai_investigator

    result = await ai_investigator.analyze_errors(db, since_hours, limit)
    return result.to_dict()


@router.get("/investigate/metrics")
async def investigate_metrics(
    db: AsyncSession = Depends(get_db),
):
    """AI調査: システムメトリクス."""
    from app.integrations.ai_investigator import ai_investigator

    return await ai_investigator.get_system_metrics(db)


@router.get("/investigate/history")
async def investigate_history(limit: int = 50):
    """AI調査: 調査履歴."""
    from app.integrations.ai_investigator import ai_investigator

    return {"history": ai_investigator.get_investigation_history(limit)}


# ===================================================================
# 仮説検証 エンドポイント
# ===================================================================


class HypothesisRequest(BaseModel):
    title: str
    description: str
    proposer_agent_id: str
    task_id: str | None = None
    company_id: str | None = None
    priority: int = 0


class EvidenceRequest(BaseModel):
    hypothesis_id: str
    agent_id: str
    supports: bool
    description: str
    source: str = ""
    confidence: float = 0.5
    data: dict | None = None


class ReviewRequest(BaseModel):
    hypothesis_id: str
    reviewer_agent_id: str
    verdict: str  # agree, disagree, needs_more_evidence, partially_agree
    reasoning: str
    confidence: float = 0.5
    suggested_actions: list[str] = []


@router.post("/hypotheses")
async def propose_hypothesis(req: HypothesisRequest):
    """仮説を提案."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    h = hypothesis_engine.propose(
        req.title,
        req.description,
        req.proposer_agent_id,
        task_id=req.task_id,
        company_id=req.company_id,
        priority=req.priority,
    )
    return h.to_dict()


@router.get("/hypotheses")
async def list_hypotheses(
    company_id: str | None = None,
    task_id: str | None = None,
):
    """仮説一覧."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    if task_id:
        hypotheses = hypothesis_engine.get_by_task(task_id)
    else:
        hypotheses = hypothesis_engine.get_active(company_id)
    return {"hypotheses": [h.to_dict() for h in hypotheses]}


@router.get("/hypotheses/{hypothesis_id}")
async def get_hypothesis(hypothesis_id: str):
    """仮説詳細."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    h = hypothesis_engine.get(hypothesis_id)
    if not h:
        raise HTTPException(status_code=404, detail="仮説が見つかりません")
    return h.to_dict()


@router.post("/hypotheses/evidence")
async def add_evidence(req: EvidenceRequest):
    """エビデンスを追加."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    ev = hypothesis_engine.add_evidence(
        req.hypothesis_id,
        req.agent_id,
        req.supports,
        req.description,
        source=req.source,
        confidence=req.confidence,
        data=req.data,
    )
    if not ev:
        raise HTTPException(status_code=404, detail="仮説が見つかりません")
    return {"evidence_id": ev.evidence_id, "added": True}


@router.post("/hypotheses/review")
async def submit_review(req: ReviewRequest):
    """レビューを提出."""
    from app.orchestration.hypothesis_engine import hypothesis_engine, ReviewVerdict

    review = hypothesis_engine.submit_review(
        req.hypothesis_id,
        req.reviewer_agent_id,
        ReviewVerdict(req.verdict),
        req.reasoning,
        confidence=req.confidence,
        suggested_actions=req.suggested_actions,
    )
    if not review:
        raise HTTPException(status_code=404, detail="仮説が見つかりません")
    return {"review_id": review.review_id, "submitted": True}


@router.post("/hypotheses/{hypothesis_id}/resolve")
async def resolve_hypothesis(hypothesis_id: str, confirmed: bool = True):
    """仮説を解決."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    ok = hypothesis_engine.resolve(hypothesis_id, confirmed)
    if not ok:
        raise HTTPException(status_code=404, detail="仮説が見つかりません")
    return {"resolved": True, "confirmed": confirmed}


@router.get("/hypotheses/needing-review")
async def hypotheses_needing_review(company_id: str | None = None):
    """レビューが必要な仮説一覧."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    hypotheses = hypothesis_engine.get_needing_review(company_id)
    return {"hypotheses": [h.to_dict() for h in hypotheses]}


# ===================================================================
# エージェントセッション エンドポイント
# ===================================================================


class CreateSessionRequest(BaseModel):
    agent_id: str
    role: str = "general"
    company_id: str | None = None
    task_id: str | None = None
    initial_context: dict | None = None
    ttl: float = 86400


class SessionMessageRequest(BaseModel):
    session_id: str
    role: str
    content: str
    metadata: dict | None = None


class WorkingMemoryRequest(BaseModel):
    session_id: str
    key: str
    value: dict | str | list | int | float | bool | None


@router.post("/sessions")
async def create_session(req: CreateSessionRequest):
    """エージェントセッションを作成."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.create_session(
        req.agent_id,
        req.role,
        company_id=req.company_id,
        task_id=req.task_id,
        initial_context=req.initial_context,
        ttl=req.ttl,
    )
    return session.to_dict()


@router.get("/sessions")
async def list_sessions(
    company_id: str | None = None,
    status: str | None = None,
    agent_id: str | None = None,
):
    """セッション一覧."""
    from app.orchestration.agent_session import session_manager, SessionStatus

    st = SessionStatus(status) if status else None
    sessions = session_manager.list_sessions(company_id, st, agent_id)
    return {"sessions": [s.to_dict() for s in sessions]}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """セッション詳細."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    return session.to_dict()


@router.get("/sessions/agent/{agent_id}")
async def get_agent_session(agent_id: str):
    """エージェントのアクティブセッションを取得."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_active_session(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="アクティブセッションがありません")
    return session.to_dict()


@router.post("/sessions/agent/{agent_id}/get-or-create")
async def get_or_create_session(agent_id: str, req: CreateSessionRequest):
    """セッションを取得、なければ作成."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_or_create_session(
        agent_id,
        req.role,
        company_id=req.company_id,
        task_id=req.task_id,
        initial_context=req.initial_context,
        ttl=req.ttl,
    )
    return session.to_dict()


@router.post("/sessions/message")
async def add_session_message(req: SessionMessageRequest):
    """セッションにメッセージを追加."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    session.add_message(req.role, req.content, req.metadata)
    return {"added": True, "message_count": session.message_count}


@router.post("/sessions/memory")
async def add_working_memory(req: WorkingMemoryRequest):
    """ワーキングメモリに情報を追加."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    session.add_to_working_memory(req.key, req.value)
    return {"stored": True, "key": req.key}


@router.post("/sessions/{session_id}/idle")
async def set_session_idle(session_id: str):
    """セッションをアイドル状態に."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    session.go_idle()
    return {"status": "idle", "session_id": session_id}


@router.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    """セッションを復帰."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    session.resume()
    return session.get_context_summary()


@router.delete("/sessions/{session_id}")
async def terminate_session(session_id: str):
    """セッションを終了."""
    from app.orchestration.agent_session import session_manager

    ok = session_manager.terminate_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    return {"terminated": True}
