"""Tests for configurable provider selection.

Feature 1: Task-level provider override
Feature 2: Dynamic media provider registry
"""

import pytest

from app.integrations.media_generation import (
    MediaProviderEntry,
    MediaProviderRegistry,
    MediaType,
)
from app.orchestration.dag import ExecutionDAG, TaskNode
from app.services.task_service import resolve_task_provider

# ---------- Feature 1: Task provider override ----------


class TestResolveTaskProvider:
    """resolve_task_provider のテスト."""

    def _make_task_stub(self, override_json=None):
        """Task モデルの軽量スタブ."""

        class TaskStub:
            provider_override_json = override_json

        return TaskStub()

    def test_no_override_uses_company_defaults(self):
        task = self._make_task_stub()
        result = resolve_task_provider(task, "anthropic", "quality")
        assert result["provider"] == "anthropic"
        assert result["model"] is None
        assert result["execution_mode"] == "quality"

    def test_task_override_provider(self):
        task = self._make_task_stub({"provider": "openai"})
        result = resolve_task_provider(task, "anthropic", "quality")
        assert result["provider"] == "openai"

    def test_task_override_model(self):
        task = self._make_task_stub({"model": "openai/gpt"})
        result = resolve_task_provider(task, "anthropic", "quality")
        assert result["provider"] == "anthropic"  # fallback to company default
        assert result["model"] == "openai/gpt"

    def test_task_override_execution_mode(self):
        task = self._make_task_stub({"execution_mode": "speed"})
        result = resolve_task_provider(task, "anthropic", "quality")
        assert result["execution_mode"] == "speed"

    def test_full_override(self):
        task = self._make_task_stub(
            {"provider": "ollama", "model": "llama3", "execution_mode": "cost"}
        )
        result = resolve_task_provider(task)
        assert result["provider"] == "ollama"
        assert result["model"] == "llama3"
        assert result["execution_mode"] == "cost"

    def test_none_override_falls_back(self):
        task = self._make_task_stub(None)
        result = resolve_task_provider(task)
        assert result["provider"] is None
        assert result["model"] is None
        assert result["execution_mode"] == "quality"

    def test_empty_dict_override_falls_back(self):
        task = self._make_task_stub({})
        result = resolve_task_provider(task, "anthropic", "speed")
        assert result["provider"] == "anthropic"
        assert result["execution_mode"] == "speed"


class TestTaskNodeProviderOverride:
    """DAG TaskNode の provider_override テスト."""

    def test_task_node_default_no_override(self):
        node = TaskNode(id="t1", title="Test")
        assert node.provider_override is None

    def test_task_node_with_override(self):
        node = TaskNode(
            id="t1",
            title="Test",
            provider_override={"provider": "openai", "model": "openai/gpt"},
        )
        assert node.provider_override["provider"] == "openai"

    def test_dag_to_dict_includes_override(self):
        dag = ExecutionDAG(
            plan_id="p1",
            nodes=[
                TaskNode(
                    id="t1",
                    title="Task 1",
                    provider_override={"provider": "anthropic"},
                ),
                TaskNode(id="t2", title="Task 2"),
            ],
        )
        d = dag.to_dict()
        assert d["nodes"][0]["provider_override"] == {"provider": "anthropic"}
        assert d["nodes"][1]["provider_override"] is None


# ---------- Feature 2: Dynamic media provider registry ----------


class TestMediaProviderRegistry:
    """MediaProviderRegistry のテスト."""

    def _make_registry(self):
        return MediaProviderRegistry()

    def test_builtin_providers_loaded(self):
        reg = self._make_registry()
        assert reg.get("openai_dalle") is not None
        assert reg.get("openai_dalle").builtin is True
        assert len(reg.list_all()) >= 10

    def test_list_by_media_type(self):
        reg = self._make_registry()
        images = reg.list_all("image")
        assert all(e.media_type == "image" for e in images)
        assert len(images) >= 3

    def test_register_new_provider(self):
        reg = self._make_registry()
        entry = MediaProviderEntry(
            id="meshy_3d",
            media_type="3d",
            api_base="https://api.meshy.ai/v1/generate",
            env_key="MESHY_API_KEY",
            models=["meshy-v2"],
            default_model="meshy-v2",
            cost_per_generation=0.30,
        )
        reg.register(entry)
        assert reg.get("meshy_3d") is not None
        assert reg.get("meshy_3d").media_type == "3d"
        assert reg.get("meshy_3d").builtin is False

    def test_register_appears_in_list(self):
        reg = self._make_registry()
        entry = MediaProviderEntry(
            id="blender_cloud",
            media_type="3d",
            api_base="https://api.blender.cloud/v1",
            env_key="BLENDER_API_KEY",
            models=["blender-3d-v1"],
            default_model="blender-3d-v1",
        )
        reg.register(entry)
        all_3d = reg.list_all("3d")
        assert any(e.id == "blender_cloud" for e in all_3d)

    def test_unregister_user_provider(self):
        reg = self._make_registry()
        entry = MediaProviderEntry(
            id="custom_img",
            media_type="image",
            api_base="https://example.com/api",
            env_key="CUSTOM_KEY",
        )
        reg.register(entry)
        assert reg.get("custom_img") is not None
        removed = reg.unregister("custom_img")
        assert removed is True
        assert reg.get("custom_img") is None

    def test_cannot_unregister_builtin(self):
        reg = self._make_registry()
        with pytest.raises(ValueError, match="(?i)builtin"):
            reg.unregister("openai_dalle")

    def test_cannot_overwrite_builtin(self):
        reg = self._make_registry()
        entry = MediaProviderEntry(
            id="openai_dalle",
            media_type="image",
            api_base="https://evil.com",
            env_key="X",
        )
        with pytest.raises(ValueError, match="(?i)builtin"):
            reg.register(entry)

    def test_unregister_nonexistent(self):
        reg = self._make_registry()
        removed = reg.unregister("does_not_exist")
        assert removed is False

    def test_overwrite_user_provider(self):
        reg = self._make_registry()
        entry1 = MediaProviderEntry(
            id="my_tool",
            media_type="3d",
            api_base="https://v1.example.com",
            env_key="KEY1",
            cost_per_generation=0.10,
        )
        reg.register(entry1)
        entry2 = MediaProviderEntry(
            id="my_tool",
            media_type="3d",
            api_base="https://v2.example.com",
            env_key="KEY2",
            cost_per_generation=0.20,
        )
        reg.register(entry2)
        updated = reg.get("my_tool")
        assert updated.api_base == "https://v2.example.com"
        assert updated.cost_per_generation == 0.20

    def test_get_available_includes_builtin_flag(self):
        reg = self._make_registry()
        entry = MediaProviderEntry(
            id="test_tool",
            media_type="3d",
            api_base="https://test.com",
            env_key="TEST_KEY",
        )
        reg.register(entry)
        available = reg.get_available()
        user_entries = [p for p in available if p["provider"] == "test_tool"]
        assert len(user_entries) == 1
        assert user_entries[0]["builtin"] is False

    def test_media_type_3d_valid(self):
        assert MediaType.THREE_D.value == "3d"

    def test_entry_to_dict(self):
        entry = MediaProviderEntry(
            id="test",
            media_type="3d",
            api_base="https://test.com",
            env_key="KEY",
            models=["m1"],
            default_model="m1",
            cost_per_generation=0.5,
            extra_config={"format": "glb"},
        )
        d = entry.to_dict()
        assert d["id"] == "test"
        assert d["media_type"] == "3d"
        assert d["extra_config"] == {"format": "glb"}
        assert d["builtin"] is False
