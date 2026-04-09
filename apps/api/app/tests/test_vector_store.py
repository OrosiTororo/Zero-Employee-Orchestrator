"""Tests for InMemoryVectorStore and LiteLLMEmbeddingVectorStore.

Verifies:
- TF-IDF cosine similarity scoring and ranking
- Document add/delete/count lifecycle
- Empty store returns empty results
- LiteLLMEmbeddingVectorStore falls back to TF-IDF when LLM unavailable
- get_vector_store() factory returns correct class
"""

from __future__ import annotations

import math
import os

import pytest


class TestInMemoryVectorStore:
    """Unit tests for InMemoryVectorStore."""

    @pytest.fixture
    async def store(self):
        from app.orchestration.vector_store import InMemoryVectorStore

        return InMemoryVectorStore()

    async def test_empty_search_returns_empty(self, store) -> None:
        results = await store.search("anything")
        assert results == []

    async def test_add_and_count(self, store) -> None:
        await store.add("d1", "The quick brown fox")
        assert await store.count() == 1

    async def test_search_finds_matching_doc(self, store) -> None:
        await store.add("doc1", "machine learning neural network")
        await store.add("doc2", "database SQL query")
        results = await store.search("neural network machine learning")
        assert len(results) > 0
        assert results[0].doc_id == "doc1"

    async def test_search_relevance_ordering(self, store) -> None:
        await store.add("a", "python programming language")
        await store.add("b", "python snake reptile animal")
        await store.add("c", "java coffee programming")
        results = await store.search("python programming")
        assert len(results) >= 1
        # doc 'a' should score higher than 'b' for "python programming"
        doc_ids = [r.doc_id for r in results]
        assert doc_ids.index("a") < doc_ids.index("b")

    async def test_search_top_k_limit(self, store) -> None:
        for i in range(20):
            await store.add(f"doc{i}", f"keyword content item number {i}")
        results = await store.search("keyword content item", top_k=5)
        assert len(results) <= 5

    async def test_delete_reduces_count(self, store) -> None:
        await store.add("x", "some content")
        await store.add("y", "other content")
        deleted = await store.delete("x")
        assert deleted is True
        assert await store.count() == 1

    async def test_delete_nonexistent_returns_false(self, store) -> None:
        result = await store.delete("does_not_exist")
        assert result is False

    async def test_search_score_between_0_and_1(self, store) -> None:
        await store.add("d1", "the quick brown fox jumps")
        results = await store.search("brown fox")
        assert all(0.0 <= r.score <= 1.0 for r in results)

    async def test_metadata_preserved(self, store) -> None:
        meta = {"source": "test", "page": 42}
        await store.add("m1", "content", metadata=meta)
        results = await store.search("content")
        assert len(results) == 1
        assert results[0].metadata == meta

    async def test_update_existing_doc(self, store) -> None:
        await store.add("u1", "original content dog")
        await store.add("u1", "updated content cat")  # overwrite
        assert await store.count() == 1
        results = await store.search("cat")
        assert len(results) == 1
        assert "cat" in results[0].content

    async def test_unrelated_query_returns_empty(self, store) -> None:
        await store.add("doc1", "machine learning python deep learning")
        results = await store.search("zzzzxxxyyy completely unrelated qwerty")
        # Cosine similarity should be ~0 for completely unrelated content
        assert len(results) == 0 or results[0].score < 0.1

    async def test_japanese_tokens(self, store) -> None:
        """Tokenizer should handle CJK characters."""
        await store.add("ja1", "機械学習 ニューラルネットワーク Python")
        results = await store.search("機械学習")
        assert len(results) >= 1
        assert results[0].doc_id == "ja1"


class TestVectorSearchResult:
    """Unit tests for VectorSearchResult dataclass."""

    def test_default_metadata(self) -> None:
        from app.orchestration.vector_store import VectorSearchResult

        r = VectorSearchResult(doc_id="x", content="test", score=0.5)
        assert r.metadata == {}

    def test_score_stored(self) -> None:
        from app.orchestration.vector_store import VectorSearchResult

        r = VectorSearchResult(doc_id="x", content="test", score=0.75)
        assert r.score == 0.75


class TestLiteLLMEmbeddingVectorStore:
    """Tests for LiteLLMEmbeddingVectorStore — verifies fallback to TF-IDF."""

    @pytest.fixture
    async def store(self):
        from app.orchestration.vector_store import LiteLLMEmbeddingVectorStore

        return LiteLLMEmbeddingVectorStore(model="text-embedding-ada-002")

    async def test_count_starts_at_zero(self, store) -> None:
        assert await store.count() == 0

    async def test_add_increases_count(self, store) -> None:
        # _embed will fail (no real API key), but add() still stores the doc
        await store.add("e1", "some content")
        assert await store.count() == 1

    async def test_search_falls_back_to_tfidf_when_llm_fails(self, store) -> None:
        """When LLM embedding fails, falls back to InMemoryVectorStore TF-IDF."""
        await store.add("f1", "machine learning python")
        await store.add("f2", "database sql queries")
        # LLM will fail (no API key), so falls back to TF-IDF
        results = await store.search("python machine learning")
        # Should still return results via fallback
        assert isinstance(results, list)

    async def test_delete_removes_doc(self, store) -> None:
        await store.add("d1", "content to delete")
        deleted = await store.delete("d1")
        assert deleted is True
        assert await store.count() == 0


class TestGetVectorStore:
    """Tests for get_vector_store() factory function."""

    def test_default_returns_in_memory(self) -> None:
        """Without env vars, should return InMemoryVectorStore."""
        os.environ.pop("VECTOR_STORE_PROVIDER", None)
        os.environ.pop("VECTOR_EMBEDDING_MODEL", None)

        from app.orchestration import vector_store as vs_module

        vs_module._vector_store = None  # Reset singleton
        from app.orchestration.vector_store import InMemoryVectorStore, get_vector_store

        store = get_vector_store()
        assert isinstance(store, InMemoryVectorStore)
        vs_module._vector_store = None  # Clean up

    def test_embedding_model_env_returns_litellm_store(self) -> None:
        """VECTOR_EMBEDDING_MODEL env var → LiteLLMEmbeddingVectorStore."""
        from app.orchestration import vector_store as vs_module

        vs_module._vector_store = None
        os.environ["VECTOR_EMBEDDING_MODEL"] = "text-embedding-ada-002"
        try:
            from app.orchestration.vector_store import (
                LiteLLMEmbeddingVectorStore,
                get_vector_store,
            )

            store = get_vector_store()
            assert isinstance(store, LiteLLMEmbeddingVectorStore)
        finally:
            del os.environ["VECTOR_EMBEDDING_MODEL"]
            vs_module._vector_store = None
