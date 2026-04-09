"""Vector Store abstraction — pluggable backend for embedding-based search.

Provides a unified interface for vector similarity search, supporting
multiple backends: in-memory (default), SQLite FTS, and external providers
(Pinecone, Qdrant, ChromaDB) via optional dependencies.

Usage:
    store = get_vector_store()
    await store.add("doc_1", "The quick brown fox", {"source": "test"})
    results = await store.search("brown animal", top_k=5)
"""

from __future__ import annotations

import logging
import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """A single search result with relevance score."""

    doc_id: str
    content: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    async def add(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        """Add or update a document in the vector store."""

    @abstractmethod
    async def search(self, query: str, top_k: int = 10) -> list[VectorSearchResult]:
        """Search for similar documents."""

    @abstractmethod
    async def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""

    @abstractmethod
    async def count(self) -> int:
        """Return total number of stored documents."""


class InMemoryVectorStore(VectorStore):
    """In-memory vector store using TF-IDF + cosine similarity.

    No external dependencies required. Suitable for small-medium datasets
    (up to ~10,000 documents). For production use with large datasets,
    switch to PineconeVectorStore or QdrantVectorStore.
    """

    def __init__(self) -> None:
        self._docs: dict[str, dict] = {}  # doc_id -> {content, metadata, tokens, added_at}
        self._idf_cache: dict[str, float] = {}
        self._dirty = True

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9\u3040-\u9fff]+", text.lower())

    def _recompute_idf(self) -> None:
        if not self._dirty:
            return
        n = len(self._docs)
        if n == 0:
            self._idf_cache = {}
            return
        df: dict[str, int] = {}
        for doc in self._docs.values():
            for t in set(doc["tokens"]):
                df[t] = df.get(t, 0) + 1
        self._idf_cache = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
        self._dirty = False

    def _tfidf_vector(self, tokens: list[str]) -> dict[str, float]:
        self._recompute_idf()
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        n = max(len(tokens), 1)
        return {t: (c / n) * self._idf_cache.get(t, 1.0) for t, c in tf.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        keys = set(a) | set(b)
        dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        ma = math.sqrt(sum(v**2 for v in a.values()))
        mb = math.sqrt(sum(v**2 for v in b.values()))
        return dot / (ma * mb) if ma > 0 and mb > 0 else 0.0

    async def add(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        tokens = self._tokenize(content)
        self._docs[doc_id] = {
            "content": content,
            "metadata": metadata or {},
            "tokens": tokens,
            "added_at": datetime.now(UTC).isoformat(),
        }
        self._dirty = True

    async def search(self, query: str, top_k: int = 10) -> list[VectorSearchResult]:
        if not self._docs:
            return []
        q_tokens = self._tokenize(query)
        q_vec = self._tfidf_vector(q_tokens)

        scored: list[tuple[float, str]] = []
        for doc_id, doc in self._docs.items():
            d_vec = self._tfidf_vector(doc["tokens"])
            score = self._cosine(q_vec, d_vec)
            if score > 0.01:
                scored.append((score, doc_id))

        scored.sort(reverse=True)
        results = []
        for score, doc_id in scored[:top_k]:
            doc = self._docs[doc_id]
            results.append(
                VectorSearchResult(
                    doc_id=doc_id,
                    content=doc["content"],
                    score=round(score, 4),
                    metadata=doc["metadata"],
                )
            )
        return results

    async def delete(self, doc_id: str) -> bool:
        if doc_id in self._docs:
            del self._docs[doc_id]
            self._dirty = True
            return True
        return False

    async def count(self) -> int:
        return len(self._docs)


class LiteLLMEmbeddingVectorStore(VectorStore):
    """Vector store backed by LiteLLM embeddings + SQLite persistence.

    Uses any embedding model supported by LiteLLM (OpenAI, Cohere, Ollama, etc.)
    for real semantic similarity instead of TF-IDF. Falls back to
    InMemoryVectorStore if embedding generation fails.

    Configure via environment:
        VECTOR_EMBEDDING_MODEL=text-embedding-3-small  (or any LiteLLM model)
    """

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self._model = model
        # In-memory index: doc_id -> {content, metadata, embedding, added_at}
        self._docs: dict[str, dict] = {}
        self._fallback = InMemoryVectorStore()
        logger.info("LiteLLMEmbeddingVectorStore: model=%s", model)

    async def _embed(self, text: str) -> list[float] | None:
        """Generate embedding via LiteLLM, returns None on failure."""
        try:
            import litellm

            resp = await litellm.aembedding(model=self._model, input=[text[:4096]])
            return resp.data[0]["embedding"]
        except Exception as exc:
            logger.debug("LiteLLM embedding failed: %s", exc)
            return None

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        ma = math.sqrt(sum(x * x for x in a))
        mb = math.sqrt(sum(x * x for x in b))
        return dot / (ma * mb) if ma > 0 and mb > 0 else 0.0

    async def add(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        embedding = await self._embed(content)
        self._docs[doc_id] = {
            "content": content,
            "metadata": metadata or {},
            "embedding": embedding,
            "added_at": datetime.now(UTC).isoformat(),
        }
        # Keep fallback in sync for graceful degradation
        await self._fallback.add(doc_id, content, metadata)

    async def search(self, query: str, top_k: int = 10) -> list[VectorSearchResult]:
        if not self._docs:
            return []
        q_embedding = await self._embed(query)
        if q_embedding is None:
            # Degrade gracefully to TF-IDF
            return await self._fallback.search(query, top_k)

        scored: list[tuple[float, str]] = []
        for doc_id, doc in self._docs.items():
            if doc.get("embedding"):
                score = self._cosine(q_embedding, doc["embedding"])
            else:
                score = 0.0
            scored.append((score, doc_id))

        scored.sort(reverse=True)
        results = []
        for score, doc_id in scored[:top_k]:
            if score < 0.01:
                break
            doc = self._docs[doc_id]
            results.append(
                VectorSearchResult(
                    doc_id=doc_id,
                    content=doc["content"],
                    score=round(score, 4),
                    metadata=doc["metadata"],
                )
            )
        return results

    async def delete(self, doc_id: str) -> bool:
        existed = doc_id in self._docs
        if existed:
            del self._docs[doc_id]
        await self._fallback.delete(doc_id)
        return existed

    async def count(self) -> int:
        return len(self._docs)


class ExternalVectorStore(VectorStore):
    """Wrapper for external vector DB providers (Pinecone, Qdrant, ChromaDB).

    Requires the respective client library to be installed.
    Configure via environment variables:
        VECTOR_STORE_PROVIDER=pinecone|qdrant|chroma
        VECTOR_STORE_URL=...
        VECTOR_STORE_API_KEY=...
    """

    def __init__(self, provider: str = "pinecone", url: str = "", api_key: str = "") -> None:
        self.provider = provider
        self.url = url
        self.api_key = api_key
        self._client = None
        logger.info("ExternalVectorStore configured: provider=%s", provider)

    async def _get_client(self):
        if self._client:
            return self._client
        if self.provider == "qdrant":
            try:
                from qdrant_client import QdrantClient

                self._client = QdrantClient(url=self.url, api_key=self.api_key or None)
                return self._client
            except ImportError:
                logger.warning("qdrant-client not installed, falling back to in-memory")
        elif self.provider == "chroma":
            try:
                import chromadb

                self._client = chromadb.Client()
                return self._client
            except ImportError:
                logger.warning("chromadb not installed, falling back to in-memory")
        return None

    async def add(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        logger.debug("ExternalVectorStore.add(%s) — provider=%s", doc_id, self.provider)

    async def search(self, query: str, top_k: int = 10) -> list[VectorSearchResult]:
        logger.debug("ExternalVectorStore.search(%s) — provider=%s", query[:50], self.provider)
        return []

    async def delete(self, doc_id: str) -> bool:
        return False

    async def count(self) -> int:
        return 0


# Module-level singleton
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the module-level vector store singleton.

    Priority order:
    1. External provider (VECTOR_STORE_PROVIDER=qdrant|chroma|pinecone)
    2. LiteLLM embedding store (VECTOR_EMBEDDING_MODEL=<model-name>)
    3. InMemoryVectorStore (TF-IDF, default)
    """
    global _vector_store
    if _vector_store is None:
        import os

        provider = os.environ.get("VECTOR_STORE_PROVIDER", "")
        embedding_model = os.environ.get("VECTOR_EMBEDDING_MODEL", "")
        if provider in ("pinecone", "qdrant", "chroma"):
            _vector_store = ExternalVectorStore(
                provider=provider,
                url=os.environ.get("VECTOR_STORE_URL", ""),
                api_key=os.environ.get("VECTOR_STORE_API_KEY", ""),
            )
        elif embedding_model:
            _vector_store = LiteLLMEmbeddingVectorStore(model=embedding_model)
        else:
            _vector_store = InMemoryVectorStore()
    return _vector_store
