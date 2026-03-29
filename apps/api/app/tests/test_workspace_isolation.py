"""Tests for WorkspaceIsolation -- AI agent environment separation."""

import pytest

from app.security.workspace_isolation import (
    AccessScope,
    StorageLocation,
    TaskWorkspaceOverride,
    WorkspaceConfig,
    WorkspaceIsolation,
)


@pytest.fixture
def ws() -> WorkspaceIsolation:
    """Create a workspace isolation instance with a temporary internal storage."""
    config = WorkspaceConfig(internal_storage_path="/tmp/zeo-test-workspace")
    return WorkspaceIsolation(config=config)


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------


class TestDefaultConfig:
    def test_default_scope_is_internal_only(self, ws: WorkspaceIsolation):
        assert ws.get_access_scope() == AccessScope.INTERNAL_ONLY

    def test_default_local_access_disabled(self, ws: WorkspaceIsolation):
        assert ws.config.local_access_enabled is False

    def test_default_cloud_access_disabled(self, ws: WorkspaceIsolation):
        assert ws.config.cloud_access_enabled is False

    def test_default_storage_is_internal(self, ws: WorkspaceIsolation):
        assert ws.config.storage_location == StorageLocation.INTERNAL


# ---------------------------------------------------------------------------
# Internal storage access
# ---------------------------------------------------------------------------


class TestInternalStorageAccess:
    def test_access_to_internal_storage_allowed(self, ws: WorkspaceIsolation):
        result = ws.check_access("/tmp/zeo-test-workspace/knowledge/file.md")
        assert result.allowed is True

    def test_knowledge_path(self, ws: WorkspaceIsolation):
        assert "knowledge" in ws.get_knowledge_path()

    def test_artifacts_path(self, ws: WorkspaceIsolation):
        assert "artifacts" in ws.get_artifacts_path()

    def test_temp_path(self, ws: WorkspaceIsolation):
        assert "temp" in ws.get_temp_path()


# ---------------------------------------------------------------------------
# Local access denied by default
# ---------------------------------------------------------------------------


class TestLocalAccessDenied:
    def test_external_path_denied(self, ws: WorkspaceIsolation):
        result = ws.check_access("/home/user/documents/secret.txt")
        assert result.allowed is False
        assert result.requires_user_approval is True
        assert "disabled" in result.reason.lower()

    def test_root_path_denied(self, ws: WorkspaceIsolation):
        result = ws.check_access("/etc/passwd")
        assert result.allowed is False

    def test_invalid_path(self, ws: WorkspaceIsolation):
        result = ws.check_access("\x00invalid")
        assert result.allowed is False


# ---------------------------------------------------------------------------
# Local access enabled
# ---------------------------------------------------------------------------


class TestLocalAccessEnabled:
    @pytest.fixture
    def ws_local(self) -> WorkspaceIsolation:
        config = WorkspaceConfig(
            internal_storage_path="/tmp/zeo-test-workspace",
            local_access_enabled=True,
            allowed_local_paths=["/home/user/projects"],
        )
        return WorkspaceIsolation(config=config)

    def test_allowed_local_path(self, ws_local: WorkspaceIsolation):
        result = ws_local.check_access("/home/user/projects/myapp/src/main.py")
        assert result.allowed is True

    def test_disallowed_local_path(self, ws_local: WorkspaceIsolation):
        result = ws_local.check_access("/home/user/secret/key.pem")
        assert result.allowed is False
        assert result.requires_user_approval is True

    def test_access_scope_local_allowed(self, ws_local: WorkspaceIsolation):
        assert ws_local.get_access_scope() == AccessScope.LOCAL_ALLOWED


# ---------------------------------------------------------------------------
# Cloud access
# ---------------------------------------------------------------------------


class TestCloudAccess:
    def test_cloud_disabled_by_default(self, ws: WorkspaceIsolation):
        result = ws.check_cloud_access("google_drive", "Documents/report.pdf")
        assert result.allowed is False
        assert result.requires_user_approval is True

    def test_cloud_enabled_but_provider_not_configured(self):
        config = WorkspaceConfig(
            internal_storage_path="/tmp/zeo-test-workspace",
            cloud_access_enabled=True,
            cloud_providers=["google_drive"],
        )
        ws = WorkspaceIsolation(config=config)
        result = ws.check_cloud_access("dropbox", "file.txt")
        assert result.allowed is False
        assert "not configured" in result.reason.lower()

    def test_cloud_enabled_and_provider_configured(self):
        config = WorkspaceConfig(
            internal_storage_path="/tmp/zeo-test-workspace",
            cloud_access_enabled=True,
            cloud_providers=["google_drive"],
        )
        ws = WorkspaceIsolation(config=config)
        result = ws.check_cloud_access("google_drive", "Documents/report.pdf")
        assert result.allowed is True


# ---------------------------------------------------------------------------
# Task overrides
# ---------------------------------------------------------------------------


class TestTaskOverrides:
    def test_unapproved_override_does_not_grant_access(self, ws: WorkspaceIsolation):
        override = TaskWorkspaceOverride(
            task_id="task-001",
            additional_local_paths=["/home/user/override"],
            approved_by_user=False,
        )
        ws.set_task_override(override)
        result = ws.check_access("/home/user/override/file.txt", task_id="task-001")
        assert result.allowed is False

    def test_approved_override_grants_access(self, ws: WorkspaceIsolation):
        override = TaskWorkspaceOverride(
            task_id="task-002",
            additional_local_paths=["/home/user/override"],
            approved_by_user=True,
        )
        ws.set_task_override(override)
        result = ws.check_access("/home/user/override/file.txt", task_id="task-002")
        assert result.allowed is True

    def test_approve_task_override(self, ws: WorkspaceIsolation):
        override = TaskWorkspaceOverride(
            task_id="task-003",
            additional_local_paths=["/home/user/data"],
            approved_by_user=False,
        )
        ws.set_task_override(override)
        assert ws.approve_task_override("task-003") is True

        result = ws.check_access("/home/user/data/file.csv", task_id="task-003")
        assert result.allowed is True

    def test_approve_nonexistent_override(self, ws: WorkspaceIsolation):
        assert ws.approve_task_override("nonexistent") is False

    def test_remove_task_override(self, ws: WorkspaceIsolation):
        override = TaskWorkspaceOverride(
            task_id="task-004",
            additional_local_paths=["/home/user/temp"],
            approved_by_user=True,
        )
        ws.set_task_override(override)
        ws.remove_task_override("task-004")
        result = ws.check_access("/home/user/temp/file.txt", task_id="task-004")
        assert result.allowed is False

    def test_cloud_task_override(self, ws: WorkspaceIsolation):
        override = TaskWorkspaceOverride(
            task_id="task-005",
            additional_cloud_sources=["google_drive://shared"],
            approved_by_user=True,
        )
        ws.set_task_override(override)
        result = ws.check_cloud_access("google_drive", "shared/doc.pdf", task_id="task-005")
        assert result.allowed is True

    def test_effective_storage_with_override(self, ws: WorkspaceIsolation):
        override = TaskWorkspaceOverride(
            task_id="task-006",
            storage_location=StorageLocation.LOCAL,
            approved_by_user=True,
        )
        ws.set_task_override(override)
        assert ws.get_effective_storage_location("task-006") == StorageLocation.LOCAL
        assert ws.get_effective_storage_location() == StorageLocation.INTERNAL


# ---------------------------------------------------------------------------
# Path management
# ---------------------------------------------------------------------------


class TestPathManagement:
    def test_add_allowed_local_path(self, ws: WorkspaceIsolation):
        ws.config.local_access_enabled = True
        ws.add_allowed_local_path("/home/user/new-path")
        result = ws.check_access("/home/user/new-path/file.txt")
        assert result.allowed is True

    def test_remove_allowed_local_path(self, ws: WorkspaceIsolation):
        ws.config.local_access_enabled = True
        ws.add_allowed_local_path("/home/user/removable")
        ws.remove_allowed_local_path("/home/user/removable")
        result = ws.check_access("/home/user/removable/file.txt")
        assert result.allowed is False

    def test_add_cloud_provider(self, ws: WorkspaceIsolation):
        ws.add_cloud_provider("dropbox")
        assert "dropbox" in ws.config.cloud_providers

    def test_remove_cloud_provider(self, ws: WorkspaceIsolation):
        ws.add_cloud_provider("onedrive")
        ws.remove_cloud_provider("onedrive")
        assert "onedrive" not in ws.config.cloud_providers


# ---------------------------------------------------------------------------
# Access scope
# ---------------------------------------------------------------------------


class TestAccessScope:
    def test_internal_only(self):
        config = WorkspaceConfig(internal_storage_path="/tmp/test")
        ws = WorkspaceIsolation(config=config)
        assert ws.get_access_scope() == AccessScope.INTERNAL_ONLY

    def test_local_allowed(self):
        config = WorkspaceConfig(internal_storage_path="/tmp/test", local_access_enabled=True)
        ws = WorkspaceIsolation(config=config)
        assert ws.get_access_scope() == AccessScope.LOCAL_ALLOWED

    def test_cloud_allowed(self):
        config = WorkspaceConfig(internal_storage_path="/tmp/test", cloud_access_enabled=True)
        ws = WorkspaceIsolation(config=config)
        assert ws.get_access_scope() == AccessScope.CLOUD_ALLOWED

    def test_full(self):
        config = WorkspaceConfig(
            internal_storage_path="/tmp/test",
            local_access_enabled=True,
            cloud_access_enabled=True,
        )
        ws = WorkspaceIsolation(config=config)
        assert ws.get_access_scope() == AccessScope.FULL


# ---------------------------------------------------------------------------
# should_request_approval
# ---------------------------------------------------------------------------


class TestShouldRequestApproval:
    def test_no_issues_returns_none(self, ws: WorkspaceIsolation):
        result = ws.should_request_approval()
        assert result is None

    def test_local_path_needs_approval(self, ws: WorkspaceIsolation):
        result = ws.should_request_approval(requested_paths=["/home/user/outside"])
        assert result is not None
        assert result.allowed is False
        assert result.requires_user_approval is True

    def test_cloud_needs_approval(self, ws: WorkspaceIsolation):
        result = ws.should_request_approval(requested_cloud=["google_drive://Documents"])
        assert result is not None
        assert result.allowed is False

    def test_storage_change_needs_approval(self, ws: WorkspaceIsolation):
        result = ws.should_request_approval(requested_storage=StorageLocation.LOCAL)
        assert result is not None
        assert "beyond current" in result.reason.lower()

    def test_config_update(self, ws: WorkspaceIsolation):
        new_config = WorkspaceConfig(
            internal_storage_path="/tmp/zeo-test-workspace",
            local_access_enabled=True,
            allowed_local_paths=["/home/user"],
        )
        ws.update_config(new_config)
        assert ws.config.local_access_enabled is True
