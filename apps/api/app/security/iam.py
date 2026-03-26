"""IAM -- Human/AI account separation and access control.

Use separate accounts for humans and AI, leveraging IAM mechanisms to
appropriately restrict AI permissions. Security measures ensure that AI
cannot access human account authentication tokens.

Design principles:
  - Human and AI accounts are managed in separate tables
  - AI tokens have narrower scopes than human tokens
  - Credentials are protected with file permissions unreadable by AI
  - All access is recorded in audit logs
"""

from __future__ import annotations

import logging
import os
import stat
import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, String, Text, Uuid, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

logger = logging.getLogger(__name__)


class AccountType(str, Enum):
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    SERVICE = "service"


class PermissionScope(str, Enum):
    """Permission scope."""

    READ_TICKETS = "read:tickets"
    WRITE_TICKETS = "write:tickets"
    READ_CODE = "read:code"
    WRITE_CODE = "write:code"
    EXECUTE_TASKS = "execute:tasks"
    READ_SECRETS = "read:secrets"
    MANAGE_AGENTS = "manage:agents"
    APPROVE_ACTIONS = "approve:actions"
    ADMIN = "admin"
    READ_AUDIT = "read:audit"
    MANAGE_SKILLS = "manage:skills"
    READ_KNOWLEDGE = "read:knowledge"
    WRITE_KNOWLEDGE = "write:knowledge"
    ACCESS_DATABASE = "access:database"
    ACCESS_LOGS = "access:logs"
    DEPLOY = "deploy"
    MANAGE_IAM = "manage:iam"


# Default AI agent permissions (more restrictive than human permissions)
DEFAULT_AI_PERMISSIONS = frozenset(
    {
        PermissionScope.READ_TICKETS,
        PermissionScope.WRITE_TICKETS,
        PermissionScope.READ_CODE,
        PermissionScope.WRITE_CODE,
        PermissionScope.EXECUTE_TASKS,
        PermissionScope.READ_KNOWLEDGE,
        PermissionScope.WRITE_KNOWLEDGE,
        PermissionScope.ACCESS_LOGS,
        PermissionScope.READ_AUDIT,
    }
)

# Permissions denied to AI agents
AI_DENIED_PERMISSIONS = frozenset(
    {
        PermissionScope.READ_SECRETS,
        PermissionScope.ADMIN,
        PermissionScope.MANAGE_IAM,
        PermissionScope.APPROVE_ACTIONS,  # Approvals are human-only
    }
)


class IAMPolicy(Base):
    """IAM policy definition."""

    __tablename__ = "iam_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_type: Mapped[str] = mapped_column(String(30))
    permissions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    denied_permissions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())


class AIServiceAccount(Base):
    """AI agent dedicated service account."""

    __tablename__ = "ai_service_accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    agent_id: Mapped[str] = mapped_column(String(255), index=True)
    account_name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(30), default="ai_agent")
    token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permissions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    denied_resources: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())


class IAMManager:
    """IAM access control manager."""

    def __init__(self) -> None:
        self._credential_dir = os.environ.get("CREDENTIAL_DIR", "/etc/zero-employee/credentials")

    async def create_ai_account(
        self,
        db: AsyncSession,
        agent_id: str,
        account_name: str,
        company_id: str | uuid.UUID | None = None,
        custom_permissions: list[str] | None = None,
    ) -> tuple[AIServiceAccount, str]:
        """Create a service account for an AI agent.

        Returns:
            (account, token) - The account and generated token
        """
        from app.core.security import generate_token, hash_sha256

        token = generate_token(48)
        cid = uuid.UUID(str(company_id)) if company_id else None

        permissions = custom_permissions or [p.value for p in DEFAULT_AI_PERMISSIONS]
        # Exclude permissions denied to AI
        permissions = [p for p in permissions if p not in {d.value for d in AI_DENIED_PERMISSIONS}]

        account = AIServiceAccount(
            id=uuid.uuid4(),
            company_id=cid,
            agent_id=agent_id,
            account_name=account_name,
            account_type=AccountType.AI_AGENT.value,
            token_hash=hash_sha256(token),
            permissions={"allowed": permissions},
            denied_resources={"paths": [self._credential_dir]},
        )
        db.add(account)
        await db.flush()

        logger.info("AI service account created: %s for agent %s", account_name, agent_id)
        return account, token

    async def verify_ai_token(self, db: AsyncSession, token: str) -> AIServiceAccount | None:
        """Verify an AI token."""
        from app.core.security import hash_sha256

        token_hash = hash_sha256(token)
        result = await db.execute(
            select(AIServiceAccount).where(
                AIServiceAccount.token_hash == token_hash,
                AIServiceAccount.is_active.is_(True),
            )
        )
        account = result.scalar_one_or_none()
        if account:
            account.last_used_at = datetime.now(UTC)
            await db.flush()
        return account

    def check_permission(
        self,
        account: AIServiceAccount,
        required_permission: PermissionScope | str,
    ) -> bool:
        """Check permission."""
        perm = (
            required_permission.value
            if isinstance(required_permission, PermissionScope)
            else required_permission
        )

        # If explicitly denied
        if perm in {d.value for d in AI_DENIED_PERMISSIONS}:
            if account.account_type == AccountType.AI_AGENT.value:
                return False

        # Check allowlist
        allowed = (account.permissions or {}).get("allowed", [])
        return perm in allowed

    def check_resource_access(self, account: AIServiceAccount, resource_path: str) -> bool:
        """Check access to a resource."""
        denied_paths = (account.denied_resources or {}).get("paths", [])
        for denied_path in denied_paths:
            if resource_path.startswith(denied_path):
                return False
        return True

    @staticmethod
    def protect_credential_file(filepath: str) -> bool:
        """Protect a credential file from being read by AI agents.

        Sets file permissions to owner read only (0o400).
        AI agents run as a different user and thus cannot read the file.
        """
        try:
            os.chmod(filepath, stat.S_IRUSR)  # 0o400
            logger.info("Credential file protected: %s", filepath)
            return True
        except OSError as exc:
            logger.warning("Failed to protect credential file %s: %s", filepath, exc)
            return False

    @staticmethod
    def create_credential_store(base_dir: str) -> str:
        """Create a credential store that AI cannot read."""
        os.makedirs(base_dir, exist_ok=True)
        # Set directory to owner only
        try:
            os.chmod(base_dir, stat.S_IRWXU)  # 0o700
        except OSError:
            pass
        return base_dir

    async def get_account_for_agent(
        self, db: AsyncSession, agent_id: str
    ) -> AIServiceAccount | None:
        """Get the service account for an agent."""
        result = await db.execute(
            select(AIServiceAccount).where(
                AIServiceAccount.agent_id == agent_id,
                AIServiceAccount.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_ai_accounts(
        self, db: AsyncSession, company_id: str | uuid.UUID | None = None
    ) -> list[AIServiceAccount]:
        """List AI service accounts."""
        stmt = select(AIServiceAccount).where(AIServiceAccount.is_active.is_(True))
        if company_id:
            cid = (
                uuid.UUID(str(company_id)) if not isinstance(company_id, uuid.UUID) else company_id
            )
            stmt = stmt.where(AIServiceAccount.company_id == cid)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def revoke_ai_account(self, db: AsyncSession, account_id: str | uuid.UUID) -> bool:
        """Deactivate an AI service account."""
        aid = uuid.UUID(str(account_id)) if not isinstance(account_id, uuid.UUID) else account_id
        result = await db.execute(select(AIServiceAccount).where(AIServiceAccount.id == aid))
        account = result.scalar_one_or_none()
        if account:
            account.is_active = False
            await db.flush()
            return True
        return False


# Global singleton
iam_manager = IAMManager()
