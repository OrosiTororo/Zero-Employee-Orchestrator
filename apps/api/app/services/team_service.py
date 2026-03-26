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
    """Team role."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    AI_OPERATOR = "ai_operator"


@dataclass
class TeamMember:
    """Team member."""

    user_id: str
    email: str
    role: TeamRole
    joined_at: str = ""
    invited_by: str = ""
    is_active: bool = True


@dataclass
class Team:
    """Team."""

    id: str
    name: str
    company_id: str
    members: list[TeamMember] = field(default_factory=list)
    created_at: str = ""
    settings: dict = field(default_factory=dict)


@dataclass
class TeamInvitation:
    """Team invitation."""

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
    """Team permission rule."""

    resource_type: str
    action: str
    allowed_roles: list[TeamRole]


@dataclass
class TeamActivity:
    """Team activity log entry."""

    id: str
    team_id: str
    user_id: str
    action: str
    details: str
    timestamp: str


# Default permission rules
_DEFAULT_PERMISSIONS: list[TeamPermission] = [
    # Team management
    TeamPermission("team", "update", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("team", "delete", [TeamRole.OWNER]),
    TeamPermission("team", "invite", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("team", "remove_member", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("team", "read", list(TeamRole)),
    # Projects
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
    # Tasks
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
    # AI operations
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
    # Budget
    TeamPermission("budget", "manage", [TeamRole.OWNER, TeamRole.ADMIN]),
    TeamPermission("budget", "read", list(TeamRole)),
    # Security
    TeamPermission("security", "manage", [TeamRole.OWNER]),
    TeamPermission("security", "read", [TeamRole.OWNER, TeamRole.ADMIN]),
    # Audit
    TeamPermission("audit", "read", [TeamRole.OWNER, TeamRole.ADMIN]),
]


class TeamService:
    """Multi-user team service.

    Handles team creation, invitations, permission management, and activity recording.
    """

    def __init__(self) -> None:
        self._teams: dict[str, Team] = {}
        self._invitations: dict[str, TeamInvitation] = {}
        self._permissions: list[TeamPermission] = list(_DEFAULT_PERMISSIONS)
        self._activity_log: list[TeamActivity] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _record_activity(self, team_id: str, user_id: str, action: str, details: str) -> None:
        """Record an activity."""
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
        """Get a team member."""
        for m in team.members:
            if m.user_id == user_id and m.is_active:
                return m
        return None

    # ------------------------------------------------------------------
    # Team CRUD
    # ------------------------------------------------------------------

    async def create_team(self, name: str, company_id: str, owner_user_id: str) -> Team:
        """Create a team."""
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
        self._record_activity(team_id, owner_user_id, "create_team", f"Created team '{name}'")
        logger.info("Team created: id=%s name=%s owner=%s", team_id, name, owner_user_id)
        return team

    async def get_team(self, team_id: str) -> Team | None:
        """Get a team by ID."""
        return self._teams.get(team_id)

    async def list_teams(self, company_id: str) -> list[Team]:
        """Get a list of teams for a company."""
        return [t for t in self._teams.values() if t.company_id == company_id]

    # ------------------------------------------------------------------
    # Invitations & joining
    # ------------------------------------------------------------------

    async def invite_member(
        self,
        team_id: str,
        email: str,
        role: TeamRole,
        invited_by: str,
    ) -> TeamInvitation:
        """Invite a member to a team."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"Team not found: {team_id}")

        # 招待者の権限チェック
        inviter = self._get_member(team, invited_by)
        if inviter is None:
            raise ValueError("Inviter is not a team member")
        if inviter.role not in (TeamRole.OWNER, TeamRole.ADMIN):
            raise PermissionError("No invitation permission")

        # OWNER ロールは招待不可（transfer_ownership を使用）
        if role == TeamRole.OWNER:
            raise ValueError("Cannot invite to OWNER role. Use ownership transfer instead")

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
            f"Invited {email} as {role.value}",
        )
        logger.info(
            "Team invitation: team=%s email=%s role=%s",
            team_id,
            email,
            role.value,
        )
        return invitation

    async def accept_invitation(self, invitation_id: str, user_id: str) -> TeamMember:
        """Accept an invitation and join a team."""
        invitation = self._invitations.get(invitation_id)
        if invitation is None:
            raise ValueError(f"Invitation not found: {invitation_id}")
        if invitation.accepted:
            raise ValueError("This invitation has already been accepted")

        # Expiration check
        expires = datetime.fromisoformat(invitation.expires_at)
        if datetime.now(UTC) > expires:
            raise ValueError("Invitation has expired")

        team = self._teams.get(invitation.team_id)
        if team is None:
            raise ValueError("Team not found")

        # Existing member check
        existing = self._get_member(team, user_id)
        if existing is not None:
            raise ValueError("Already a team member")

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
            f"Accepted invitation (role={invitation.role.value})",
        )
        logger.info(
            "Invitation accepted: team=%s user=%s role=%s",
            invitation.team_id,
            user_id,
            invitation.role.value,
        )
        return member

    # ------------------------------------------------------------------
    # Member management
    # ------------------------------------------------------------------

    async def remove_member(self, team_id: str, user_id: str, removed_by: str) -> bool:
        """Remove a member from a team."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"Team not found: {team_id}")

        remover = self._get_member(team, removed_by)
        if remover is None:
            raise ValueError("Operator is not a team member")
        if remover.role not in (TeamRole.OWNER, TeamRole.ADMIN):
            raise PermissionError("No permission to remove members")

        target = self._get_member(team, user_id)
        if target is None:
            raise ValueError("Target user is not a team member")
        if target.role == TeamRole.OWNER:
            raise ValueError("OWNER cannot be removed")
        if target.role == TeamRole.ADMIN and remover.role != TeamRole.OWNER:
            raise PermissionError("Only OWNER can remove ADMIN")

        target.is_active = False
        self._record_activity(
            team_id,
            removed_by,
            "remove_member",
            f"Removed member {user_id}",
        )
        logger.info("Member removed: team=%s user=%s by=%s", team_id, user_id, removed_by)
        return True

    async def update_role(
        self,
        team_id: str,
        user_id: str,
        new_role: TeamRole,
        updated_by: str,
    ) -> TeamMember:
        """Change a member's role."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"Team not found: {team_id}")

        updater = self._get_member(team, updated_by)
        if updater is None:
            raise ValueError("Operator is not a team member")
        if updater.role != TeamRole.OWNER:
            raise PermissionError("Only OWNER can change roles")

        if new_role == TeamRole.OWNER:
            raise ValueError("Use transfer_ownership to change to OWNER role")

        target = self._get_member(team, user_id)
        if target is None:
            raise ValueError("Target user is not a team member")
        if target.role == TeamRole.OWNER:
            raise ValueError("OWNER role cannot be changed")

        old_role = target.role
        target.role = new_role
        self._record_activity(
            team_id,
            updated_by,
            "update_role",
            f"Changed {user_id} role from {old_role.value} to {new_role.value}",
        )
        logger.info(
            "Role changed: team=%s user=%s %s->%s",
            team_id,
            user_id,
            old_role.value,
            new_role.value,
        )
        return target

    async def get_team_members(self, team_id: str) -> list[TeamMember]:
        """Get a list of active team members."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"Team not found: {team_id}")
        return [m for m in team.members if m.is_active]

    # ------------------------------------------------------------------
    # Permission checks
    # ------------------------------------------------------------------

    async def check_permission(
        self,
        team_id: str,
        user_id: str,
        resource_type: str,
        action: str,
    ) -> bool:
        """Check a user's permissions."""
        team = self._teams.get(team_id)
        if team is None:
            return False

        member = self._get_member(team, user_id)
        if member is None:
            return False

        # OWNER has all permissions
        if member.role == TeamRole.OWNER:
            return True

        for perm in self._permissions:
            if perm.resource_type == resource_type and perm.action == action:
                return member.role in perm.allowed_roles

        # Undefined permissions are only allowed for OWNER/ADMIN
        return member.role in (TeamRole.OWNER, TeamRole.ADMIN)

    # ------------------------------------------------------------------
    # Ownership transfer
    # ------------------------------------------------------------------

    async def transfer_ownership(
        self,
        team_id: str,
        new_owner_id: str,
        current_owner_id: str,
    ) -> Team:
        """Transfer team ownership."""
        team = self._teams.get(team_id)
        if team is None:
            raise ValueError(f"Team not found: {team_id}")

        current_owner = self._get_member(team, current_owner_id)
        if current_owner is None or current_owner.role != TeamRole.OWNER:
            raise PermissionError("Only the current OWNER can transfer ownership")

        new_owner = self._get_member(team, new_owner_id)
        if new_owner is None:
            raise ValueError("Transfer target user is not a team member")

        current_owner.role = TeamRole.ADMIN
        new_owner.role = TeamRole.OWNER
        self._record_activity(
            team_id,
            current_owner_id,
            "transfer_ownership",
            f"Transferred ownership to {new_owner_id}",
        )
        logger.info(
            "Ownership transferred: team=%s %s -> %s",
            team_id,
            current_owner_id,
            new_owner_id,
        )
        return team

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    async def get_activity_log(self, team_id: str, limit: int = 50) -> list[TeamActivity]:
        """Get a team's activity log."""
        activities = [a for a in self._activity_log if a.team_id == team_id]
        return sorted(activities, key=lambda a: a.timestamp, reverse=True)[:limit]


# Global instance
team_service = TeamService()
