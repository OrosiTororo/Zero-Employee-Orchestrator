"""AI organization management service -- Dynamic agent addition, removal, and role customization.

Allows users to make requests to the AI organization in natural language,
defining and modifying roles such as secretary and advisor.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, String, Text, Uuid, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import generate_uuid
from app.models.agent import Agent
from app.models.audit import AuditLog

# ---------------------------------------------------------------------------
# プリセット役割定義
# ---------------------------------------------------------------------------


class AgentRolePreset(str, Enum):
    """プリセットのエージェント役割."""

    SECRETARY = "secretary"  # 秘書
    ADVISOR = "advisor"  # 相談役（壁打ち相手）
    PM = "product_manager"  # プロダクトマネージャー
    RESEARCHER = "researcher"  # リサーチャー
    ENGINEER = "engineer"  # エンジニア
    MARKETER = "marketer"  # マーケター
    DESIGNER = "designer"  # デザイナー
    ANALYST = "analyst"  # アナリスト
    SUPPORT = "support"  # カスタマーサポート
    CONTENT = "content_creator"  # コンテンツクリエイター
    CUSTOM = "custom"  # ユーザー定義


ROLE_DEFINITIONS: dict[str, dict[str, Any]] = {
    AgentRolePreset.SECRETARY: {
        "name": "秘書",
        "title": "AI Secretary",
        "description": (
            "AI組織とユーザーの繋ぎ役。システムの情報の保管庫やファイル、"
            "ユーザーとAI組織との会話からナレッジを貯め、ユーザーのお手伝いをする。"
            "ブレインダンプの整理、スケジュール管理、情報の蓄積と活用を担当。"
        ),
        "autonomy_level": "semi-autonomous",
        "can_delegate": True,
        "system_prompt": (
            "あなたはAI組織の秘書です。ユーザーとAI組織の橋渡し役として、"
            "情報の整理・蓄積・検索を行い、ユーザーの業務を効率化します。"
            "過去の会話やナレッジベースを活用して、的確な提案を行ってください。"
            "ユーザーの過去の発言や決定事項を記憶し、必要に応じて参照してください。"
        ),
    },
    AgentRolePreset.ADVISOR: {
        "name": "相談役",
        "title": "AI Advisor",
        "description": (
            "ユーザーが困った時にサポートしたり壁打ち相手になり、"
            "秘書とユーザーを繋ぐ。多角的な視点からアドバイスを提供し、"
            "アイデアの深掘り、課題の整理、意思決定のサポートを行う。"
        ),
        "autonomy_level": "semi-autonomous",
        "can_delegate": True,
        "system_prompt": (
            "あなたはAI組織の相談役です。ユーザーの壁打ち相手として、"
            "多角的な視点からアドバイスを提供してください。"
            "質問を投げかけ、アイデアを深掘りし、課題を整理し、"
            "意思決定をサポートしてください。"
            "ユーザーの過去の相談内容や決定事項を覚えておき、一貫したサポートを提供してください。"
        ),
    },
    AgentRolePreset.PM: {
        "name": "プロダクトマネージャー",
        "title": "Product Manager",
        "description": "プロジェクトの進捗管理、優先順位付け、タスクの割り振りを行う。",
        "autonomy_level": "semi-autonomous",
        "can_delegate": True,
        "system_prompt": (
            "あなたはAI組織のプロダクトマネージャーです。"
            "プロジェクト全体の進捗を把握し、タスクの優先順位を管理してください。"
        ),
    },
    AgentRolePreset.RESEARCHER: {
        "name": "リサーチャー",
        "title": "Research Analyst",
        "description": "競合調査、トレンド分析、市場データの収集と分析を行う。",
        "autonomy_level": "supervised",
        "can_delegate": False,
        "system_prompt": (
            "あなたはAI組織のリサーチャーです。"
            "データの収集・分析を行い、客観的な調査結果を提供してください。"
        ),
    },
    AgentRolePreset.ENGINEER: {
        "name": "エンジニア",
        "title": "Software Engineer",
        "description": "プロダクトの開発、技術調査、コードレビュー、バグ修正を行う。",
        "autonomy_level": "supervised",
        "can_delegate": False,
        "system_prompt": (
            "あなたはAI組織のエンジニアです。技術的な課題解決とコード品質の維持に注力してください。"
        ),
    },
    AgentRolePreset.MARKETER: {
        "name": "マーケター",
        "title": "Marketing Specialist",
        "description": "SNSコンテンツの企画、投稿案の作成、集客施策の立案を行う。",
        "autonomy_level": "supervised",
        "can_delegate": False,
        "system_prompt": (
            "あなたはAI組織のマーケターです。集客と認知拡大のための施策を提案してください。"
        ),
    },
    AgentRolePreset.CONTENT: {
        "name": "コンテンツクリエイター",
        "title": "Content Creator",
        "description": "記事、動画台本、広告コピー、ブログ記事の制作を行う。",
        "autonomy_level": "supervised",
        "can_delegate": False,
        "system_prompt": (
            "あなたはAI組織のコンテンツクリエイターです。魅力的なコンテンツを制作してください。"
        ),
    },
}


# ---------------------------------------------------------------------------
# 機能リクエスト DB モデル
# ---------------------------------------------------------------------------


class FeatureRequestRecord(Base):
    """ユーザーからの自然言語による機能リクエスト."""

    __tablename__ = "feature_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    request_text: Mapped[str] = mapped_column(Text)
    interpreted_action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # add_agent | remove_agent | modify_role | change_model | add_feature | other
    interpreted_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending | approved | executed | rejected | failed
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())


class CustomAgentRole(Base):
    """ユーザー定義のカスタムエージェント役割."""

    __tablename__ = "custom_agent_roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    role_key: Mapped[str] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    autonomy_level: Mapped[str] = mapped_column(String(30), default="supervised")
    can_delegate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# 自然言語リクエスト解釈
# ---------------------------------------------------------------------------

_ACTION_KEYWORDS: dict[str, list[str]] = {
    "add_agent": [
        "追加",
        "新しく",
        "増やす",
        "作成",
        "配属",
        "雇う",
        "入れて",
        "add",
        "create",
        "hire",
        "new agent",
    ],
    "remove_agent": [
        "削除",
        "外す",
        "解雇",
        "除く",
        "なくす",
        "remove",
        "delete",
        "fire",
    ],
    "modify_role": [
        "役割を変更",
        "役割変更",
        "担当を変更",
        "変更",
        "修正",
        "role change",
        "modify role",
        "update role",
    ],
    "change_model": [
        "モデルを変更",
        "モデル変更",
        "GPT",
        "Claude",
        "Gemini",
        "切り替え",
        "change model",
        "switch model",
    ],
    "add_feature": [
        "機能追加",
        "機能を追加",
        "できるように",
        "対応して",
        "実装",
        "add feature",
        "implement",
        "new feature",
    ],
}

_ROLE_KEYWORDS: dict[str, list[str]] = {
    "secretary": ["秘書", "secretary", "アシスタント", "assistant"],
    "advisor": ["相談役", "壁打ち", "アドバイザー", "advisor", "consultant"],
    "product_manager": ["PM", "プロマネ", "プロダクトマネージャー", "product manager"],
    "researcher": ["リサーチ", "調査", "research", "analyst"],
    "engineer": ["エンジニア", "開発", "engineer", "developer", "プログラマー"],
    "marketer": ["マーケ", "集客", "marketing", "SNS"],
    "content_creator": ["コンテンツ", "クリエイター", "ライター", "content", "writer"],
    "support": ["サポート", "カスタマー", "support", "customer"],
    "designer": ["デザイナー", "デザイン", "designer", "UI", "UX"],
}


def interpret_natural_language_request(text: str) -> dict[str, Any]:
    """自然言語リクエストをアクションに解釈する."""
    text_lower = text.lower()

    # アクション推定
    action = "other"
    max_matches = 0
    for act, keywords in _ACTION_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        if matches > max_matches:
            max_matches = matches
            action = act

    # 役割推定
    target_role = None
    for role, keywords in _ROLE_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            target_role = role
            break

    return {
        "action": action,
        "target_role": target_role,
        "original_text": text,
        "confidence": min(max_matches / 3.0, 1.0) if max_matches > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# AI 組織管理サービス
# ---------------------------------------------------------------------------


class AgentOrgService:
    """AI 組織のエージェント動的管理サービス."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add_agent_by_role(
        self,
        company_id: str,
        role: str,
        *,
        name: str | None = None,
        description: str | None = None,
        model_name: str | None = None,
        provider_name: str = "openrouter",
        team_id: str | None = None,
        custom_system_prompt: str | None = None,
    ) -> Agent:
        """プリセットまたはカスタム役割でエージェントを追加."""
        cid = uuid.UUID(company_id)

        # プリセット役割から定義を取得
        role_def = ROLE_DEFINITIONS.get(role)
        if not role_def:
            # カスタム役割を検索
            result = await self._db.execute(
                select(CustomAgentRole).where(
                    CustomAgentRole.company_id == cid,
                    CustomAgentRole.role_key == role,
                    CustomAgentRole.is_active.is_(True),
                )
            )
            custom_role = result.scalar_one_or_none()
            if custom_role:
                role_def = {
                    "name": custom_role.name,
                    "title": custom_role.title,
                    "description": custom_role.description,
                    "autonomy_level": custom_role.autonomy_level,
                    "can_delegate": custom_role.can_delegate,
                    "system_prompt": custom_role.system_prompt,
                }
            else:
                role_def = {
                    "name": name or role,
                    "title": name or role,
                    "description": description or f"{role} エージェント",
                    "autonomy_level": "supervised",
                    "can_delegate": False,
                    "system_prompt": None,
                }

        agent = Agent(
            id=generate_uuid(),
            company_id=cid,
            team_id=uuid.UUID(team_id) if team_id else None,
            name=name or role_def["name"],
            title=role_def["title"],
            description=description or role_def["description"],
            agent_type="llm",
            runtime_type="api",
            provider_name=provider_name,
            model_name=model_name,
            status="idle",
            autonomy_level=role_def["autonomy_level"],
            can_delegate=role_def.get("can_delegate", False),
            can_write_external=False,
            can_spend_budget=False,
            config_json={
                "role": role,
                "system_prompt": custom_system_prompt or role_def.get("system_prompt"),
            },
        )
        self._db.add(agent)

        # 監査ログ
        audit = AuditLog(
            id=generate_uuid(),
            company_id=cid,
            actor_type="user",
            event_type="agent.added_by_role",
            target_type="agent",
            target_id=agent.id,
            details_json={"role": role, "name": agent.name},
        )
        self._db.add(audit)
        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def remove_agent(
        self,
        agent_id: str,
        *,
        reason: str = "",
    ) -> bool:
        """エージェントを組織から削除（廃止状態にする）."""
        result = await self._db.execute(select(Agent).where(Agent.id == uuid.UUID(agent_id)))
        agent = result.scalar_one_or_none()
        if not agent:
            return False

        agent.status = "decommissioned"

        audit = AuditLog(
            id=generate_uuid(),
            company_id=agent.company_id,
            actor_type="user",
            event_type="agent.removed",
            target_type="agent",
            target_id=agent.id,
            details_json={"reason": reason, "name": agent.name},
        )
        self._db.add(audit)
        await self._db.commit()
        return True

    async def update_agent_role(
        self,
        agent_id: str,
        *,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        model_name: str | None = None,
        provider_name: str | None = None,
        autonomy_level: str | None = None,
        system_prompt: str | None = None,
    ) -> Agent | None:
        """エージェントの役割設定を更新."""
        result = await self._db.execute(select(Agent).where(Agent.id == uuid.UUID(agent_id)))
        agent = result.scalar_one_or_none()
        if not agent:
            return None

        if name is not None:
            agent.name = name
        if title is not None:
            agent.title = title
        if description is not None:
            agent.description = description
        if model_name is not None:
            agent.model_name = model_name
        if provider_name is not None:
            agent.provider_name = provider_name
        if autonomy_level is not None:
            agent.autonomy_level = autonomy_level
        if system_prompt is not None:
            config = agent.config_json or {}
            config["system_prompt"] = system_prompt
            agent.config_json = config

        audit = AuditLog(
            id=generate_uuid(),
            company_id=agent.company_id,
            actor_type="user",
            event_type="agent.role_updated",
            target_type="agent",
            target_id=agent.id,
            details_json={"name": agent.name},
        )
        self._db.add(audit)
        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def create_custom_role(
        self,
        company_id: str,
        role_key: str,
        name: str,
        title: str,
        description: str,
        *,
        system_prompt: str | None = None,
        autonomy_level: str = "supervised",
        can_delegate: bool = False,
    ) -> CustomAgentRole:
        """カスタムエージェント役割を作成."""
        role = CustomAgentRole(
            id=uuid.uuid4(),
            company_id=uuid.UUID(company_id),
            role_key=role_key,
            name=name,
            title=title,
            description=description,
            system_prompt=system_prompt,
            autonomy_level=autonomy_level,
            can_delegate=can_delegate,
        )
        self._db.add(role)
        await self._db.flush()
        return role

    async def list_custom_roles(
        self,
        company_id: str,
    ) -> list[CustomAgentRole]:
        """カスタム役割一覧を取得."""
        stmt = (
            select(CustomAgentRole)
            .where(
                CustomAgentRole.company_id == uuid.UUID(company_id),
                CustomAgentRole.is_active.is_(True),
            )
            .order_by(CustomAgentRole.created_at.desc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def delete_custom_role(
        self,
        role_id: str,
    ) -> bool:
        """カスタム役割を削除."""
        result = await self._db.execute(
            select(CustomAgentRole).where(CustomAgentRole.id == uuid.UUID(role_id))
        )
        role = result.scalar_one_or_none()
        if not role:
            return False
        role.is_active = False
        await self._db.flush()
        return True

    async def get_available_roles(
        self,
        company_id: str,
    ) -> list[dict]:
        """利用可能な全役割を取得（プリセット + カスタム）."""
        roles: list[dict] = []

        # プリセット役割
        for key, defn in ROLE_DEFINITIONS.items():
            roles.append(
                {
                    "role_key": key if isinstance(key, str) else key.value,
                    "name": defn["name"],
                    "title": defn["title"],
                    "description": defn["description"],
                    "is_preset": True,
                }
            )

        # カスタム役割
        custom_roles = await self.list_custom_roles(company_id)
        for cr in custom_roles:
            roles.append(
                {
                    "role_key": cr.role_key,
                    "name": cr.name,
                    "title": cr.title,
                    "description": cr.description,
                    "is_preset": False,
                }
            )

        return roles

    async def process_natural_language_request(
        self,
        company_id: str,
        request_text: str,
        *,
        user_id: str | None = None,
        auto_execute: bool = False,
    ) -> FeatureRequestRecord:
        """自然言語の要望を解釈し、機能リクエストとして記録."""
        interpretation = interpret_natural_language_request(request_text)

        record = FeatureRequestRecord(
            id=uuid.uuid4(),
            company_id=uuid.UUID(company_id),
            user_id=uuid.UUID(user_id) if user_id else None,
            request_text=request_text,
            interpreted_action=interpretation["action"],
            interpreted_details=interpretation,
            status="pending",
        )
        self._db.add(record)

        # 自動実行が有効で信頼度が高い場合
        if auto_execute and interpretation["confidence"] >= 0.5:
            try:
                result = await self._execute_interpreted_action(company_id, interpretation)
                record.status = "executed"
                record.result_json = result
            except Exception as e:
                record.status = "failed"
                record.result_json = {"error": str(e)}

        await self._db.flush()
        return record

    async def _execute_interpreted_action(
        self,
        company_id: str,
        interpretation: dict,
    ) -> dict:
        """解釈されたアクションを実行."""
        action = interpretation["action"]
        target_role = interpretation.get("target_role")

        if action == "add_agent" and target_role:
            agent = await self.add_agent_by_role(company_id, target_role)
            return {
                "action": "add_agent",
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "role": target_role,
            }
        elif action == "remove_agent":
            return {
                "action": "remove_agent",
                "status": "requires_agent_id",
                "message": "削除対象のエージェントを指定してください",
            }
        elif action == "modify_role":
            return {
                "action": "modify_role",
                "status": "requires_details",
                "message": "変更内容の詳細を指定してください",
            }
        elif action == "change_model":
            return {
                "action": "change_model",
                "status": "requires_details",
                "message": "変更するモデルとエージェントを指定してください",
            }
        else:
            return {
                "action": action,
                "status": "recorded",
                "message": "リクエストを記録しました。管理者による確認が必要です。",
            }

    async def list_feature_requests(
        self,
        company_id: str,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[FeatureRequestRecord]:
        """機能リクエスト一覧を取得."""
        stmt = select(FeatureRequestRecord).where(
            FeatureRequestRecord.company_id == uuid.UUID(company_id)
        )
        if status:
            stmt = stmt.where(FeatureRequestRecord.status == status)
        stmt = stmt.order_by(FeatureRequestRecord.created_at.desc()).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
