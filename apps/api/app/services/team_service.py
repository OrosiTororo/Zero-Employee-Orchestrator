"""Multi-user team service -- Team creation, invitations, and permission management.

Provides team-based authentication and permission management.
Each team consists of 5 roles: owner, admin, member, viewer, and AI operator.

Permission checks:
- Allowed roles determined by resource_type + action combination
- AI_OPERATOR can only operate on AI-related resources
- VIEWER is read-only
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class TeamRole(str, Enum):
    """チームロール."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    AI_OPERATOR = "ai_operator"


@dataclass
class TeamMember:
    """チームメンバー."""

    user_id: str
    email: str
    role: TeamRole
    joined_at: str = ""
    invited_by: str = ""
    is_active: bool = True


@dataclass
class Team:
    """チーム."""

    id: str
    name: str
    company_id: str
    members: list[TeamMember] = field(default_factory=list)
    created_at: str = ""
    settings: dict = field(default_factory=dict)


@dataclass
class TeamInvitation:
    """チーム招待."""

    id: str
    team_id: str
    email: str
    role: TeamRole
    invited_by: str
    created_at: str = ""
    expires_at: str = ""
    accepted: bool = False


@dataclass
class TeamPermission:
    """チーム権限ルール."""

    resource_type: str
    action: str
    allowed_roles: list[TeamRole]


@dataclass
class TeamActivity:
    """チームアクティビティログエントリ."""

    id: str
    team_id: str
    user_id: str
    action: str
    details: str
    timestamp: str


# デフォルト権限ルール
_DEFAULT_PERMISSIONS: list[TeamPermission] = [
    # チーム管理
    TeamPermission("team", "update", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("team", "delete", [TeamRole.OWNER]),
    TeamPermission("team", "invite", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("team", "remove_member", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("team", "read", list(TeamRole)),
    # プロジェクト
    TeamPermission(
        "project",
        "create",
        [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER],
    ),
    TeamPermission(
        "project",
        "update",
        [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER],
    ),
    TeamPermission("project", "delete", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("project", "read", list(TeamRole)),
    # タスク
    TeamPermission(
        "task",
        "create",
        [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.AI_OPERATOR],
    ),
    TeamPermission(
        "task",
        "update",
        [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.AI_OPERATOR],
    ),
    TeamPermission("task", "delete", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("task", "read", list(TeamRole)),
    # AI 操作
    TeamPermission(
        "ai",
        "execute",
        [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.AI_OPERATOR],
    ),
    TeamPermission(
        "ai",
        "configure",
        [TeamRole.OWNER, TeamRole.ADMIN],
    ),
    TeamPermission("ai", "read", list(TeamRole)),
    # 予算
    TeamPermission("budget", "manage", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("budget", "read", list(TeamRole)),
    # セキュリティ
    TeamPermission("security", "manage", [TeamRole.OWNER]),
    TeamPermission("security", "read", [TeamRole.OWNER, TeamRole.ADMIN]),
    # 監査
    TeamPermission("audit", "read", [TeamRole.OWNER, TeamRole.ADMIN]),
]


class TeamService:
    """マルチユーザー・チームサービス.

    チームの作成・招待・権限管理・アクティビティ記録を行う。
    """

    def __init__(self) -> None:
        self._teams: dict[str, Team] = {}
        self._invitations: dict[str, TeamInvitation] = {}
        self._permissions: list[TeamPermission] = list(_DEFAULT_PERMISSIONS)
        self._activity_log: list[TeamActivity] = []

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _record_activity(self, team_id: str, user_id: str, action: str, details: str) -> None:
        """アクティビティを記録する."""
        self._activity_log.append(
            TeamActivity(
                id=str(uuid.uuid4()),
                team_id=team_id,
                user_id=user_id,
                action=action,
                details=details,
                timestamp=self._now(),
            )
        )

    def _get_member(self, team: Team, user_id: str) -> TeamMember | None:
        """チームメンバーを取得する."""
        for m in team.members:
            if m.user_id == user_id and m.is_active:
                return m
        return None

    # ------------------------------------------------------------------
    # チーム CRUD
    # ------------------------------------------------------------------

    async def create_team(self, name: str, company_id: str, owner_user_id: str) -> Team:
        """チームを作成する."""
        team_id = str(uuid.uuid4())
        now = self._now()
        owner = TeamMember(
            user_id=owner_user_id,
            email="",
            role=TeamRole.OWNER,
            joined_at=now,
            invited_by=owner_user_id,
            is_active=True,
        )
        team = Team(
            id=team_id,
            name=name,
            company_id=company_id,
            members=[owner],
            created_at=now,
            settings={},
        )
        self._teams[team_id] = team
        self._record_activity(team_id, owner_user_id, "create_team", f"チーム '{name}' を作成")
        logger.info("チーム作成: id=%s name=%s owner=%s", team_id, name, owner_user_id)
        return team

    async def get_team(self, team_id: str) -> Team | None:
        """チームを ID で取得する."""
        return self._teams.get(team_id)

    async def list_teams(self, company_id: str) -> list[Team]:
        """企業のチーム一覧を取得する."""
        return [t for t in self._teams.values() if t.company_id == company_id]

    # ------------------------------------------------------------------
    # 招待・参加
    # ------------------------------------------------------------------

    async def invite_member(
        self,
        team_id: str,
        email: str,
        role: TeamRole,
        invited_by: str,
    ) -> TeamInvitation:
        """メンバーをチームに招待する."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"チームが見つかりません: {team_id}")

        # 招待者の権限チェック
        inviter = self._get_member(team, invited_by)
        if inviter is None:
            raise ValueError("招待者がチームメンバーではありません")
        if inviter.role not in (TeamRole.OWNER, TeamRole.ADMIN):
            raise PermissionError("招待権限がありません")

        # OWNER ロールは招待不可（transfer_ownership を使用）
        if role == TeamRole.OWNER:
            raise ValueError("OWNER ロールは招待できません。ownership 移譲を使用してください")

        now = self._now()
        invitation = TeamInvitation(
            id=str(uuid.uuid4()),
            team_id=team_id,
            email=email,
            role=role,
            invited_by=invited_by,
            created_at=now,
            expires_at=(datetime.now(UTC) + timedelta(days=7)).isoformat(),
            accepted=False,
        )
        self._invitations[invitation.id] = invitation
        self._record_activity(
            team_id,
            invited_by,
            "invite_member",
            f"{email} を {role.value} として招待",
        )
        logger.info(
            "チーム招待: team=%s email=%s role=%s",
            team_id,
            email,
            role.value,
        )
        return invitation

    async def accept_invitation(self, invitation_id: str, user_id: str) -> TeamMember:
        """招待を受諾してチームに参加する."""
        invitation = self._invitations.get(invitation_id)
        if invitation is None:
            raise ValueError(f"招待が見つかりません: {invitation_id}")
        if invitation.accepted:
            raise ValueError("この招待は既に受諾済みです")

        # 有効期限チェック
        expires = datetime.fromisoformat(invitation.expires_at)
        if datetime.now(UTC) > expires:
            raise ValueError("招待の有効期限が切れています")

        team = self._teams.get(invitation.team_id)
        if team is None:
            raise ValueError("チームが見つかりません")

        # 既存メンバーチェック
        existing = self._get_member(team, user_id)
        if existing is not None:
            raise ValueError("既にチームメンバーです")

        member = TeamMember(
            user_id=user_id,
            email=invitation.email,
            role=invitation.role,
            joined_at=self._now(),
            invited_by=invitation.invited_by,
            is_active=True,
        )
        team.members.append(member)
        invitation.accepted = True
        self._record_activity(
            invitation.team_id,
            user_id,
            "accept_invitation",
            f"招待を受諾 (role={invitation.role.value})",
        )
        logger.info(
            "招待受諾: team=%s user=%s role=%s",
            invitation.team_id,
            user_id,
            invitation.role.value,
        )
        return member

    # ------------------------------------------------------------------
    # メンバー管理
    # ------------------------------------------------------------------

    async def remove_member(self, team_id: str, user_id: str, removed_by: str) -> bool:
        """メンバーをチームから除外する."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"チームが見つかりません: {team_id}")

        remover = self._get_member(team, removed_by)
        if remover is None:
            raise ValueError("操作者がチームメンバーではありません")
        if remover.role not in (TeamRole.OWNER, TeamRole.ADMIN):
            raise PermissionError("メンバー除外の権限がありません")

        target = self._get_member(team, user_id)
        if target is None:
            raise ValueError("対象ユーザーがチームメンバーではありません")
        if target.role == TeamRole.OWNER:
            raise ValueError("OWNER は除外できません")
        if target.role == TeamRole.ADMIN and remover.role != TeamRole.OWNER:
            raise PermissionError("ADMIN を除外できるのは OWNER のみです")

        target.is_active = False
        self._record_activity(
            team_id,
            removed_by,
            "remove_member",
            f"メンバー {user_id} を除外",
        )
        logger.info("メンバー除外: team=%s user=%s by=%s", team_id, user_id, removed_by)
        return True

    async def update_role(
        self,
        team_id: str,
        user_id: str,
        new_role: TeamRole,
        updated_by: str,
    ) -> TeamMember:
        """メンバーのロールを変更する."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"チームが見つかりません: {team_id}")

        updater = self._get_member(team, updated_by)
        if updater is None:
            raise ValueError("操作者がチームメンバーではありません")
        if updater.role != TeamRole.OWNER:
            raise PermissionError("ロール変更は OWNER のみ可能です")

        if new_role == TeamRole.OWNER:
            raise ValueError("OWNER ロールへの変更は transfer_ownership を使用してください")

        target = self._get_member(team, user_id)
        if target is None:
            raise ValueError("対象ユーザーがチームメンバーではありません")
        if target.role == TeamRole.OWNER:
            raise ValueError("OWNER のロールは変更できません")

        old_role = target.role
        target.role = new_role
        self._record_activity(
            team_id,
            updated_by,
            "update_role",
            f"{user_id} のロールを {old_role.value} → {new_role.value} に変更",
        )
        logger.info(
            "ロール変更: team=%s user=%s %s->%s",
            team_id,
            user_id,
            old_role.value,
            new_role.value,
        )
        return target

    async def get_team_members(self, team_id: str) -> list[TeamMember]:
        """チームのアクティブメンバー一覧を取得する."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"チームが見つかりません: {team_id}")
        return [m for m in team.members if m.is_active]

    # ------------------------------------------------------------------
    # 権限チェック
    # ------------------------------------------------------------------

    async def check_permission(
        self,
        team_id: str,
        user_id: str,
        resource_type: str,
        action: str,
    ) -> bool:
        """ユーザーの権限をチェックする."""
        team = self._teams.get(team_id)
        if team is None:
            return False

        member = self._get_member(team, user_id)
        if member is None:
            return False

        # OWNER は全権限を持つ
        if member.role == TeamRole.OWNER:
            return True

        for perm in self._permissions:
            if perm.resource_type == resource_type and perm.action == action:
                return member.role in perm.allowed_roles

        # 未定義の権限は OWNER/ADMIN のみ許可
        return member.role in (TeamRole.OWNER, TeamRole.ADMIN)

    # ------------------------------------------------------------------
    # オーナーシップ移譲
    # ------------------------------------------------------------------

    async def transfer_ownership(
        self,
        team_id: str,
        new_owner_id: str,
        current_owner_id: str,
    ) -> Team:
        """チームのオーナーシップを移譲する."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"チームが見つかりません: {team_id}")

        current_owner = self._get_member(team, current_owner_id)
        if current_owner is None or current_owner.role != TeamRole.OWNER:
            raise PermissionError("オーナーシップ移譲は現在の OWNER のみ可能です")

        new_owner = self._get_member(team, new_owner_id)
        if new_owner is None:
            raise ValueError("移譲先ユーザーがチームメンバーではありません")

        current_owner.role = TeamRole.ADMIN
        new_owner.role = TeamRole.OWNER
        self._record_activity(
            team_id,
            current_owner_id,
            "transfer_ownership",
            f"オーナーシップを {new_owner_id} に移譲",
        )
        logger.info(
            "オーナーシップ移譲: team=%s %s -> %s",
            team_id,
            current_owner_id,
            new_owner_id,
        )
        return team

    # ------------------------------------------------------------------
    # アクティビティ
    # ------------------------------------------------------------------

    async def get_activity_log(self, team_id: str, limit: int = 50) -> list[TeamActivity]:
        """チームのアクティビティログを取得する."""
        activities = [a for a in self._activity_log if a.team_id == team_id]
        return sorted(activities, key=lambda a: a.timestamp, reverse=True)[:limit]


# グローバルインスタンス
team_service = TeamService()
