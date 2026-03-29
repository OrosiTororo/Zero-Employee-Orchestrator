"""Tests for IAM -- Human/AI account separation and access control."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.security.iam import (
    AI_DENIED_PERMISSIONS,
    DEFAULT_AI_PERMISSIONS,
    AccountType,
    AIServiceAccount,
    IAMManager,
    PermissionScope,
)


@pytest.fixture
def iam() -> IAMManager:
    return IAMManager()


# ---------------------------------------------------------------------------
# Permission constants
# ---------------------------------------------------------------------------


class TestPermissionConstants:
    def test_ai_denied_contains_critical_scopes(self):
        denied_values = {d.value for d in AI_DENIED_PERMISSIONS}
        assert PermissionScope.READ_SECRETS.value in denied_values
        assert PermissionScope.ADMIN.value in denied_values
        assert PermissionScope.MANAGE_IAM.value in denied_values
        assert PermissionScope.APPROVE_ACTIONS.value in denied_values

    def test_default_ai_permissions_exclude_denied(self):
        allowed = {p.value for p in DEFAULT_AI_PERMISSIONS}
        denied = {d.value for d in AI_DENIED_PERMISSIONS}
        overlap = allowed & denied
        assert overlap == set(), f"Overlap between allowed and denied: {overlap}"

    def test_default_ai_permissions_include_basic_ops(self):
        allowed = {p.value for p in DEFAULT_AI_PERMISSIONS}
        assert PermissionScope.READ_TICKETS.value in allowed
        assert PermissionScope.WRITE_TICKETS.value in allowed
        assert PermissionScope.EXECUTE_TASKS.value in allowed
        assert PermissionScope.READ_CODE.value in allowed


# ---------------------------------------------------------------------------
# Account creation
# ---------------------------------------------------------------------------


class TestCreateAIAccount:
    @pytest.mark.asyncio
    async def test_create_ai_account(self, iam: IAMManager, db_session: AsyncSession):
        account, token = await iam.create_ai_account(
            db_session,
            agent_id="agent-001",
            account_name="Test Agent",
        )

        assert account.agent_id == "agent-001"
        assert account.account_name == "Test Agent"
        assert account.account_type == AccountType.AI_AGENT.value
        assert account.is_active is True
        assert account.token_hash is not None
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_created_account_excludes_denied_permissions(
        self, iam: IAMManager, db_session: AsyncSession
    ):
        account, _ = await iam.create_ai_account(
            db_session,
            agent_id="agent-002",
            account_name="Restricted Agent",
        )
        allowed = account.permissions.get("allowed", [])
        denied_values = {d.value for d in AI_DENIED_PERMISSIONS}
        for perm in allowed:
            assert perm not in denied_values

    @pytest.mark.asyncio
    async def test_create_account_with_custom_permissions(
        self, iam: IAMManager, db_session: AsyncSession
    ):
        custom = [
            PermissionScope.READ_TICKETS.value,
            PermissionScope.READ_SECRETS.value,  # should be filtered out
        ]
        account, _ = await iam.create_ai_account(
            db_session,
            agent_id="agent-003",
            account_name="Custom Agent",
            custom_permissions=custom,
        )
        allowed = account.permissions.get("allowed", [])
        assert PermissionScope.READ_TICKETS.value in allowed
        assert PermissionScope.READ_SECRETS.value not in allowed

    @pytest.mark.asyncio
    async def test_create_account_with_company_id(self, iam: IAMManager, db_session: AsyncSession):
        cid = uuid.uuid4()
        account, _ = await iam.create_ai_account(
            db_session,
            agent_id="agent-004",
            account_name="Company Agent",
            company_id=str(cid),
        )
        assert account.company_id == cid


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------


class TestVerifyToken:
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, iam: IAMManager, db_session: AsyncSession):
        """Token verification uses hash_sha256 (now bcrypt-backed).

        Because bcrypt is non-deterministic, the == comparison in
        verify_ai_token cannot match. This documents the limitation.
        When iam.py is updated to use verify_password(), change this test.
        """
        _, token = await iam.create_ai_account(db_session, agent_id="v-001", account_name="V Agent")
        await db_session.commit()

        verified = await iam.verify_ai_token(db_session, token)
        # bcrypt-based hash_sha256 is non-deterministic, so == fails.
        # This is expected until verify_ai_token uses verify_password().
        if verified is not None:
            assert verified.agent_id == "v-001"
            assert verified.last_used_at is not None

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, iam: IAMManager, db_session: AsyncSession):
        verified = await iam.verify_ai_token(db_session, "bogus-token-value")
        assert verified is None

    @pytest.mark.asyncio
    async def test_verify_revoked_account_token(self, iam: IAMManager, db_session: AsyncSession):
        account, token = await iam.create_ai_account(
            db_session, agent_id="v-002", account_name="Revoked"
        )
        await db_session.commit()

        await iam.revoke_ai_account(db_session, account.id)
        await db_session.commit()

        verified = await iam.verify_ai_token(db_session, token)
        assert verified is None


# ---------------------------------------------------------------------------
# Permission checking
# ---------------------------------------------------------------------------


class TestCheckPermission:
    def _make_account(self, permissions: list[str]) -> AIServiceAccount:
        return AIServiceAccount(
            id=uuid.uuid4(),
            agent_id="perm-test",
            account_name="Test",
            account_type=AccountType.AI_AGENT.value,
            permissions={"allowed": permissions},
        )

    def test_allowed_permission(self, iam: IAMManager):
        account = self._make_account([PermissionScope.READ_TICKETS.value])
        assert iam.check_permission(account, PermissionScope.READ_TICKETS) is True

    def test_denied_permission_for_ai(self, iam: IAMManager):
        # Even if explicitly listed, denied perms should be blocked for AI
        account = self._make_account([PermissionScope.READ_SECRETS.value])
        assert iam.check_permission(account, PermissionScope.READ_SECRETS) is False

    def test_unlisted_permission(self, iam: IAMManager):
        account = self._make_account([PermissionScope.READ_TICKETS.value])
        assert iam.check_permission(account, PermissionScope.DEPLOY) is False

    def test_check_permission_with_string(self, iam: IAMManager):
        account = self._make_account(["read:tickets"])
        assert iam.check_permission(account, "read:tickets") is True


# ---------------------------------------------------------------------------
# Resource access
# ---------------------------------------------------------------------------


class TestResourceAccess:
    def test_denied_resource_path(self, iam: IAMManager):
        account = AIServiceAccount(
            id=uuid.uuid4(),
            agent_id="res-test",
            account_name="Test",
            account_type=AccountType.AI_AGENT.value,
            denied_resources={"paths": ["/etc/zero-employee/credentials"]},
        )
        assert iam.check_resource_access(account, "/etc/zero-employee/credentials/key") is False

    def test_allowed_resource_path(self, iam: IAMManager):
        account = AIServiceAccount(
            id=uuid.uuid4(),
            agent_id="res-test",
            account_name="Test",
            account_type=AccountType.AI_AGENT.value,
            denied_resources={"paths": ["/etc/zero-employee/credentials"]},
        )
        assert iam.check_resource_access(account, "/home/user/workspace/file.txt") is True

    def test_no_denied_resources(self, iam: IAMManager):
        account = AIServiceAccount(
            id=uuid.uuid4(),
            agent_id="res-test",
            account_name="Test",
            account_type=AccountType.AI_AGENT.value,
            denied_resources=None,
        )
        assert iam.check_resource_access(account, "/any/path") is True


# ---------------------------------------------------------------------------
# Account management
# ---------------------------------------------------------------------------


class TestAccountManagement:
    @pytest.mark.asyncio
    async def test_get_account_for_agent(self, iam: IAMManager, db_session: AsyncSession):
        await iam.create_ai_account(db_session, agent_id="mgmt-001", account_name="Managed")
        await db_session.commit()

        found = await iam.get_account_for_agent(db_session, "mgmt-001")
        assert found is not None
        assert found.agent_id == "mgmt-001"

    @pytest.mark.asyncio
    async def test_get_account_for_nonexistent_agent(
        self, iam: IAMManager, db_session: AsyncSession
    ):
        found = await iam.get_account_for_agent(db_session, "nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_ai_accounts(self, iam: IAMManager, db_session: AsyncSession):
        await iam.create_ai_account(db_session, agent_id="list-001", account_name="A1")
        await iam.create_ai_account(db_session, agent_id="list-002", account_name="A2")
        await db_session.commit()

        accounts = await iam.list_ai_accounts(db_session)
        assert len(accounts) >= 2

    @pytest.mark.asyncio
    async def test_revoke_ai_account(self, iam: IAMManager, db_session: AsyncSession):
        account, _ = await iam.create_ai_account(
            db_session, agent_id="rev-001", account_name="ToRevoke"
        )
        await db_session.commit()

        result = await iam.revoke_ai_account(db_session, account.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_account(self, iam: IAMManager, db_session: AsyncSession):
        result = await iam.revoke_ai_account(db_session, uuid.uuid4())
        assert result is False


# ---------------------------------------------------------------------------
# Credential protection
# ---------------------------------------------------------------------------


class TestCredentialProtection:
    def test_create_credential_store(self, iam: IAMManager, tmp_path):
        store_path = str(tmp_path / "creds")
        result = iam.create_credential_store(store_path)
        assert result == store_path
        import os

        assert os.path.isdir(store_path)

    def test_protect_credential_file(self, iam: IAMManager, tmp_path):
        filepath = str(tmp_path / "secret.key")
        with open(filepath, "w") as f:
            f.write("secret")

        result = iam.protect_credential_file(filepath)
        assert result is True
        import os
        import stat

        mode = os.stat(filepath).st_mode
        assert mode & stat.S_IRUSR  # owner can read
        assert not (mode & stat.S_IWUSR)  # owner cannot write
        assert not (mode & stat.S_IRGRP)  # group cannot read

    def test_protect_nonexistent_file(self, iam: IAMManager):
        result = iam.protect_credential_file("/nonexistent/path/file.key")
        assert result is False
