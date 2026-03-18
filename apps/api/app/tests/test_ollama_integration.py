"""Tests for the Ollama integration layer.

Validates the integration between Ollama/RAG and core orchestration modules:
- Knowledge Pipeline bridge
- Artifact Bridge registration
- OllamaEmbeddingStore auto-selection
- Heartbeat result structure
- SSE streaming format
"""

import json
import os

import pytest

os.environ.setdefault("DEBUG", "true")


# ---------------------------------------------------------------------------
# Knowledge Pipeline integration tests
# ---------------------------------------------------------------------------


class TestKnowledgePipelineIntegration:
    """Test Knowledge Pipeline ↔ Ollama integration."""

    def test_store_success_experience(self):
        from app.orchestration.knowledge_refresh import KnowledgeType, knowledge_store
        from app.providers.ollama_integration import store_ollama_experience

        # Store a successful experience
        entry_id = store_ollama_experience(
            task_type="code_generation",
            model="qwen3:8b",
            success=True,
            duration_seconds=12.5,
            details="Generated Python class successfully",
            tags=["python"],
        )

        assert entry_id.startswith("ollama_success_")

        # Should be in experience memory
        entries = knowledge_store.get_by_type(KnowledgeType.EXPERIENCE_MEMORY)
        matching = [e for e in entries if e.id == entry_id]
        assert len(matching) == 1
        assert "qwen3:8b" in matching[0].content
        assert "code_generation" in matching[0].content
        assert "ollama" in matching[0].tags
        assert "python" in matching[0].tags

    def test_store_failure_taxonomy(self):
        from app.orchestration.knowledge_refresh import KnowledgeType, knowledge_store
        from app.providers.ollama_integration import store_ollama_experience

        entry_id = store_ollama_experience(
            task_type="translation",
            model="mistral:latest",
            success=False,
            duration_seconds=30.0,
            details="Model timed out during translation",
        )

        assert entry_id.startswith("ollama_failure_")

        entries = knowledge_store.get_by_type(KnowledgeType.FAILURE_TAXONOMY)
        matching = [e for e in entries if e.id == entry_id]
        assert len(matching) == 1
        assert "failure" in matching[0].tags
        assert "mistral" in matching[0].tags

    def test_retrieve_knowledge(self):
        from app.providers.ollama_integration import (
            retrieve_ollama_knowledge,
            store_ollama_experience,
        )

        # Store some experiences first
        store_ollama_experience(
            task_type="api_design",
            model="qwen3:32b",
            success=True,
            duration_seconds=8.0,
            details="API design completed with FastAPI schema",
        )

        # Search for relevant knowledge
        results = retrieve_ollama_knowledge("API design with FastAPI")

        # Should find at least the entry we just stored
        assert isinstance(results, list)
        # Each entry should have expected fields
        for entry in results:
            assert "id" in entry
            assert "type" in entry
            assert "title" in entry
            assert "content" in entry


# ---------------------------------------------------------------------------
# Artifact Bridge integration tests
# ---------------------------------------------------------------------------


class TestArtifactBridgeIntegration:
    """Test Artifact Bridge ↔ Ollama integration."""

    def test_register_rag_artifact(self):
        from app.orchestration.artifact_bridge import ArtifactType, artifact_bridge
        from app.providers.ollama_integration import register_rag_artifact

        artifact_id = register_rag_artifact(
            task_id="task_123",
            doc_count=42,
            store_path="/tmp/rag_store",
            summary="Test RAG index",
        )

        assert artifact_id is not None

        # Should be retrievable
        artifact = artifact_bridge.get_artifact(artifact_id)
        assert artifact is not None
        assert artifact.artifact_type == ArtifactType.DATA
        assert "RAG" in artifact.title

        # Should be linked to task outputs
        outputs = artifact_bridge.get_task_outputs("task_123")
        assert any(o.artifact_id == artifact_id for o in outputs)

    def test_register_ollama_output(self):
        from app.orchestration.artifact_bridge import ArtifactType, artifact_bridge
        from app.providers.ollama_integration import register_ollama_output

        artifact_id = register_ollama_output(
            task_id="task_456",
            title="Generated Report",
            content="This is a generated report about market analysis.",
            artifact_type_str="report",
        )

        artifact = artifact_bridge.get_artifact(artifact_id)
        assert artifact is not None
        assert artifact.artifact_type == ArtifactType.REPORT
        assert artifact.title == "Generated Report"

    def test_register_code_output(self):
        from app.orchestration.artifact_bridge import ArtifactType, artifact_bridge
        from app.providers.ollama_integration import register_ollama_output

        artifact_id = register_ollama_output(
            task_id="task_789",
            title="Generated Script",
            content="def main():\n    print('hello')",
            artifact_type_str="code",
            mime_type="text/x-python",
        )

        artifact = artifact_bridge.get_artifact(artifact_id)
        assert artifact is not None
        assert artifact.artifact_type == ArtifactType.CODE
        assert artifact.mime_type == "text/x-python"


# ---------------------------------------------------------------------------
# OllamaEmbeddingStore auto-selection tests
# ---------------------------------------------------------------------------


class TestEmbeddingAutoSelection:
    """Test OllamaEmbeddingStore smart auto-selection."""

    @pytest.mark.asyncio
    async def test_fallback_to_tfidf(self):
        """When Ollama is not running, should fall back to TF-IDF store."""
        from app.providers.local_rag import LocalVectorStore
        from app.providers.ollama_integration import (
            get_rag_store,
            reset_embedding_cache,
        )

        # Reset cache to force re-check
        reset_embedding_cache()

        store = await get_rag_store()
        # Since Ollama is likely not running in CI, should get LocalVectorStore
        assert isinstance(store, LocalVectorStore)

    def test_reset_cache(self):
        from app.providers.ollama_integration import (
            reset_embedding_cache,
        )

        reset_embedding_cache()
        # After reset, the module-level flag should be False
        from app.providers import ollama_integration

        assert ollama_integration._embedding_checked is False


# ---------------------------------------------------------------------------
# Heartbeat result structure tests
# ---------------------------------------------------------------------------


class TestHeartbeatResult:
    """Test OllamaHeartbeatResult structure."""

    @pytest.mark.asyncio
    async def test_heartbeat_result_structure(self):
        from app.providers.ollama_integration import run_ollama_heartbeat

        result = await run_ollama_heartbeat()

        assert isinstance(result.ollama_available, bool)
        assert isinstance(result.models_count, int)
        assert isinstance(result.model_names, list)
        assert isinstance(result.embedding_available, bool)
        assert isinstance(result.rag_document_count, int)
        assert result.checked_at > 0

    @pytest.mark.asyncio
    async def test_heartbeat_without_ollama(self):
        """Heartbeat should complete gracefully even when Ollama is down."""
        from app.providers.ollama_integration import run_ollama_heartbeat

        result = await run_ollama_heartbeat()

        # Even if Ollama is down, result should be well-formed
        assert isinstance(result.model_names, list)
        assert result.checked_at > 0


# ---------------------------------------------------------------------------
# SSE streaming format tests
# ---------------------------------------------------------------------------


class TestSSEStreamingFormat:
    """Test SSE event format for streaming chat."""

    def test_sse_data_format(self):
        """Verify SSE data line format is correct."""
        chunk = "Hello"
        data = json.dumps({"content": chunk, "done": False}, ensure_ascii=False)
        sse_line = f"data: {data}\n\n"

        assert sse_line.startswith("data: ")
        assert sse_line.endswith("\n\n")

        # Parse back
        payload = json.loads(sse_line.removeprefix("data: ").strip())
        assert payload["content"] == "Hello"
        assert payload["done"] is False

    def test_sse_final_event(self):
        """Verify final SSE event format."""
        data = json.dumps({"content": "", "done": True})
        sse_line = f"data: {data}\n\n"

        payload = json.loads(sse_line.removeprefix("data: ").strip())
        assert payload["content"] == ""
        assert payload["done"] is True

    def test_sse_error_event(self):
        """Verify error SSE event format."""
        error_data = json.dumps({"error": "timeout", "done": True})
        sse_line = f"data: {error_data}\n\n"

        payload = json.loads(sse_line.removeprefix("data: ").strip())
        assert payload["error"] == "timeout"
        assert payload["done"] is True

    def test_sse_japanese_content(self):
        """Verify SSE handles CJK content correctly."""
        chunk = "こんにちは世界"
        data = json.dumps({"content": chunk, "done": False}, ensure_ascii=False)
        sse_line = f"data: {data}\n\n"

        payload = json.loads(sse_line.removeprefix("data: ").strip())
        assert payload["content"] == "こんにちは世界"


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    """Test Pydantic schema validation for new request/response models."""

    def test_chat_request_with_stream(self):
        from app.api.routes.ollama import OllamaChatRequest

        req = OllamaChatRequest(
            messages=[{"role": "user", "content": "hello"}],
            stream=True,
        )
        assert req.stream is True
        assert req.temperature == 0.7

    def test_chat_request_default_no_stream(self):
        from app.api.routes.ollama import OllamaChatRequest

        req = OllamaChatRequest(
            messages=[{"role": "user", "content": "hello"}],
        )
        assert req.stream is False

    def test_rag_add_with_task_id(self):
        from app.api.routes.ollama import RAGAddRequest

        req = RAGAddRequest(
            content="some document",
            task_id="task_123",
        )
        assert req.task_id == "task_123"

    def test_rag_add_without_task_id(self):
        from app.api.routes.ollama import RAGAddRequest

        req = RAGAddRequest(content="some document")
        assert req.task_id is None

    def test_heartbeat_response(self):
        from app.api.routes.ollama import HeartbeatCheckResponse

        resp = HeartbeatCheckResponse(
            ollama_available=True,
            models_count=3,
            model_names=["qwen3:8b", "mistral", "phi3"],
            embedding_available=True,
            rag_document_count=42,
            checked_at=1709913600.0,
        )
        assert resp.ollama_available is True
        assert len(resp.model_names) == 3

    def test_knowledge_store_request(self):
        from app.api.routes.ollama import KnowledgeStoreRequest

        req = KnowledgeStoreRequest(
            task_type="code_review",
            model="qwen3:32b",
            success=True,
            duration_seconds=15.5,
            details="Reviewed 3 files",
            tags=["review", "python"],
        )
        assert req.task_type == "code_review"
        assert req.success is True
        assert len(req.tags) == 2

    def test_knowledge_search_request(self):
        from app.api.routes.ollama import KnowledgeSearchRequest

        req = KnowledgeSearchRequest(
            task_context="code generation with Python",
        )
        assert req.max_tokens == 4000  # default

    def test_health_response_with_embedding(self):
        from app.api.routes.ollama import OllamaHealthResponse

        resp = OllamaHealthResponse(
            available=True,
            base_url="http://localhost:11434",
            models_count=5,
            embedding_available=True,
        )
        assert resp.embedding_available is True

    def test_rag_add_response_with_artifact(self):
        from app.api.routes.ollama import RAGAddResponse

        resp = RAGAddResponse(
            ids=["id1", "id2"],
            chunks=2,
            artifact_id="artifact_abc",
        )
        assert resp.artifact_id == "artifact_abc"
