"""Local RAG (Retrieval-Augmented Generation) — file-based vector DB.

Inspired by vibe-local's approach: implements a vector database using only
file storage and trigonometric functions (cosine similarity) for semantic
search. No external vector DB dependency required.

Architecture
------------
* **TF-IDF vectorization** using Python standard library ``math`` + ``re``
* **Cosine similarity** for document ranking
* **JSON file storage** for persistence (no database dependency)
* **Document chunking** with overlap for long texts
* **Ollama embedding support** — can optionally use Ollama's embedding API
  for higher-quality vectors when available

This enables the Knowledge Pipeline and Experience Memory to perform
semantic search even in fully offline / local-only deployments.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_STORE_DIR = ".zero_employee/rag_store"
CHUNK_SIZE = 512  # tokens (approximate by words)
CHUNK_OVERLAP = 64


# ---------------------------------------------------------------------------
# Text processing utilities
# ---------------------------------------------------------------------------

# CJK character ranges for proper tokenization
_CJK_RANGES = (
    r"\u4e00-\u9fff"  # CJK Unified Ideographs
    r"\u3040-\u309f"  # Hiragana
    r"\u30a0-\u30ff"  # Katakana
    r"\uff00-\uffef"  # Fullwidth Forms
    r"\u3400-\u4dbf"  # CJK Unified Ideographs Extension A
)

_TOKEN_PATTERN = re.compile(
    rf"[{_CJK_RANGES}]|[a-zA-Z0-9_]+",
    re.UNICODE,
)

_STOPWORDS_EN = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "don",
        "now",
        "and",
        "but",
        "or",
        "if",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "they",
        "them",
        "their",
        "what",
        "which",
        "who",
        "whom",
    }
)

_STOPWORDS_JA = frozenset(
    {
        "の",
        "に",
        "は",
        "を",
        "た",
        "が",
        "で",
        "て",
        "と",
        "し",
        "れ",
        "さ",
        "ある",
        "いる",
        "も",
        "する",
        "から",
        "な",
        "こと",
        "として",
        "い",
        "や",
        "れる",
        "など",
        "なっ",
        "ない",
        "この",
        "ため",
        "その",
        "あっ",
        "よう",
        "また",
        "もの",
        "という",
        "あり",
        "まで",
        "られ",
        "なる",
        "へ",
        "か",
        "だ",
        "これ",
        "によって",
        "により",
        "おり",
        "より",
        "による",
        "ず",
        "なり",
        "られる",
        "において",
        "ば",
        "なかっ",
        "なく",
        "しかし",
        "について",
        "せ",
        "だっ",
        "み",
        "え",
        "よ",
        "ね",
    }
)

STOPWORDS = _STOPWORDS_EN | _STOPWORDS_JA


_CJK_CHAR_RE = re.compile(rf"[{_CJK_RANGES}]")


def tokenize(text: str) -> list[str]:
    """Tokenize text into words, handling both Latin and CJK scripts.

    CJK characters are kept even as single characters since they are
    semantically meaningful on their own (unlike single Latin letters).
    """
    tokens = _TOKEN_PATTERN.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS and (len(t) > 1 or _CJK_CHAR_RE.match(t))]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks for indexing."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# ---------------------------------------------------------------------------
# TF-IDF Vector
# ---------------------------------------------------------------------------


@dataclass
class TFIDFVector:
    """Sparse TF-IDF vector represented as a dict of term→weight."""

    weights: dict[str, float] = field(default_factory=dict)

    def norm(self) -> float:
        """L2 norm of the vector."""
        if not self.weights:
            return 0.0
        return math.sqrt(sum(w * w for w in self.weights.values()))

    def dot(self, other: TFIDFVector) -> float:
        """Dot product with another vector."""
        result = 0.0
        # Iterate over the smaller vector for efficiency
        if len(self.weights) > len(other.weights):
            small, big = other.weights, self.weights
        else:
            small, big = self.weights, other.weights

        for term, weight in small.items():
            if term in big:
                result += weight * big[term]
        return result


def cosine_similarity(a: TFIDFVector, b: TFIDFVector) -> float:
    """Compute cosine similarity between two TF-IDF vectors.

    Returns a value between 0.0 (completely dissimilar) and 1.0 (identical).
    This is the core of the "trigonometric" vector DB approach from vibe-local.
    """
    norm_a = a.norm()
    norm_b = b.norm()
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return a.dot(b) / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Document store
# ---------------------------------------------------------------------------


@dataclass
class Document:
    """A stored document with its vector representation."""

    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    vector: TFIDFVector = field(default_factory=TFIDFVector)
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "vector_weights": self.vector.weights,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Document:
        return cls(
            id=d["id"],
            content=d["content"],
            metadata=d.get("metadata", {}),
            vector=TFIDFVector(weights=d.get("vector_weights", {})),
            created_at=d.get("created_at", 0.0),
        )


@dataclass
class SearchResult:
    """A search result with relevance score."""

    document: Document
    score: float
    chunk_text: str = ""


# ---------------------------------------------------------------------------
# Local Vector Store
# ---------------------------------------------------------------------------


class LocalVectorStore:
    """File-based vector store using TF-IDF + cosine similarity.

    Stores documents as JSON files on disk. No external database needed.
    Suitable for small-to-medium collections (up to ~10k documents).
    """

    def __init__(self, store_dir: str | Path | None = None) -> None:
        self._store_dir = Path(store_dir or DEFAULT_STORE_DIR)
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._documents: dict[str, Document] = {}
        self._idf: dict[str, float] = {}
        self._loaded = False

    @property
    def store_dir(self) -> Path:
        return self._store_dir

    @property
    def document_count(self) -> int:
        self._ensure_loaded()
        return len(self._documents)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _index_path(self) -> Path:
        return self._store_dir / "index.json"

    def _idf_path(self) -> Path:
        return self._store_dir / "idf.json"

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self.load()
        self._loaded = True

    def load(self) -> None:
        """Load documents and IDF from disk."""
        index_path = self._index_path()
        if index_path.exists():
            try:
                data = json.loads(index_path.read_text(encoding="utf-8"))
                self._documents = {
                    doc_id: Document.from_dict(doc_data) for doc_id, doc_data in data.items()
                }
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Failed to load RAG index: %s", exc)
                self._documents = {}

        idf_path = self._idf_path()
        if idf_path.exists():
            try:
                self._idf = json.loads(idf_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                self._idf = {}

        self._loaded = True

    def save(self) -> None:
        """Persist documents and IDF to disk with restricted permissions."""
        import os
        import stat

        self._store_dir.mkdir(parents=True, exist_ok=True)
        # ディレクトリは所有者のみアクセス可能
        try:
            os.chmod(self._store_dir, stat.S_IRWXU)
        except OSError:
            pass

        index_data = {doc_id: doc.to_dict() for doc_id, doc in self._documents.items()}

        idx = self._index_path()
        idx.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            os.chmod(idx, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
        except OSError:
            pass

        idf = self._idf_path()
        idf.write_text(
            json.dumps(self._idf, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            os.chmod(idf, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
        except OSError:
            pass

    # ------------------------------------------------------------------
    # IDF computation
    # ------------------------------------------------------------------

    def _recompute_idf(self) -> None:
        """Recompute inverse document frequency for all terms."""
        n_docs = len(self._documents)
        if n_docs == 0:
            self._idf = {}
            return

        # Count how many documents contain each term
        doc_freq: Counter[str] = Counter()
        for doc in self._documents.values():
            tokens = set(tokenize(doc.content))
            doc_freq.update(tokens)

        # IDF = log(N / df) + 1  (smoothed)
        self._idf = {term: math.log(n_docs / freq) + 1.0 for term, freq in doc_freq.items()}

    def _compute_tfidf(self, text: str) -> TFIDFVector:
        """Compute TF-IDF vector for a piece of text."""
        tokens = tokenize(text)
        if not tokens:
            return TFIDFVector()

        # Term frequency (normalized by document length)
        tf: Counter[str] = Counter(tokens)
        max_freq = max(tf.values()) if tf else 1

        weights: dict[str, float] = {}
        for term, freq in tf.items():
            tf_norm = 0.5 + 0.5 * (freq / max_freq)
            idf = self._idf.get(term, 1.0)
            weights[term] = tf_norm * idf

        return TFIDFVector(weights=weights)

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------

    def _make_id(self, content: str, metadata: dict | None = None) -> str:
        """Generate a deterministic document ID."""
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        return h

    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_METADATA_KEYS = 50

    def add(
        self,
        content: str,
        metadata: dict | None = None,
        doc_id: str | None = None,
        auto_chunk: bool = True,
    ) -> list[str]:
        """Add a document (or chunked documents) to the store.

        Returns the list of document IDs added.
        """
        if len(content) > self.MAX_CONTENT_SIZE:
            raise ValueError(f"Content exceeds maximum size ({self.MAX_CONTENT_SIZE} bytes)")
        self._ensure_loaded()
        metadata = metadata or {}
        if len(metadata) > self.MAX_METADATA_KEYS:
            raise ValueError(f"Metadata has too many keys (max {self.MAX_METADATA_KEYS})")
        ids: list[str] = []

        if auto_chunk:
            chunks = chunk_text(content)
        else:
            chunks = [content]

        for i, chunk in enumerate(chunks):
            chunk_id = doc_id or self._make_id(chunk)
            if len(chunks) > 1:
                chunk_id = f"{chunk_id}_chunk{i}"

            doc = Document(
                id=chunk_id,
                content=chunk,
                metadata={**metadata, "chunk_index": i, "total_chunks": len(chunks)},
                created_at=time.time(),
            )
            self._documents[chunk_id] = doc
            ids.append(chunk_id)

        # Recompute IDF and re-vectorize all documents
        self._recompute_idf()
        for doc in self._documents.values():
            doc.vector = self._compute_tfidf(doc.content)

        return ids

    def add_many(
        self,
        documents: Sequence[tuple[str, dict | None]],
    ) -> list[str]:
        """Add multiple documents at once (more efficient than individual adds).

        Args:
            documents: Sequence of (content, metadata) tuples.
        """
        self._ensure_loaded()
        all_ids: list[str] = []

        for content, metadata in documents:
            metadata = metadata or {}
            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                chunk_id = self._make_id(chunk)
                if len(chunks) > 1:
                    chunk_id = f"{chunk_id}_chunk{i}"

                doc = Document(
                    id=chunk_id,
                    content=chunk,
                    metadata={
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                    created_at=time.time(),
                )
                self._documents[chunk_id] = doc
                all_ids.append(chunk_id)

        # Batch recompute
        self._recompute_idf()
        for doc in self._documents.values():
            doc.vector = self._compute_tfidf(doc.content)

        return all_ids

    def remove(self, doc_id: str) -> bool:
        """Remove a document by ID."""
        self._ensure_loaded()
        if doc_id in self._documents:
            del self._documents[doc_id]
            self._recompute_idf()
            return True
        return False

    def clear(self) -> None:
        """Remove all documents."""
        self._documents.clear()
        self._idf.clear()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.05,
        metadata_filter: dict | None = None,
    ) -> list[SearchResult]:
        """Search for documents similar to the query.

        Uses TF-IDF vectorization and cosine similarity — the same
        approach as vibe-local's file-based vector DB.

        Args:
            query:           Natural language search query.
            top_k:           Maximum number of results.
            min_score:       Minimum similarity score threshold.
            metadata_filter: Optional dict of metadata key-value pairs to filter by.

        Returns:
            List of SearchResult sorted by descending relevance score.
        """
        self._ensure_loaded()
        if not self._documents:
            return []

        query_vector = self._compute_tfidf(query)
        if query_vector.norm() == 0.0:
            return []

        results: list[SearchResult] = []
        for doc in self._documents.values():
            # Apply metadata filter
            if metadata_filter:
                if not all(doc.metadata.get(k) == v for k, v in metadata_filter.items()):
                    continue

            score = cosine_similarity(query_vector, doc.vector)
            if score >= min_score:
                results.append(
                    SearchResult(
                        document=doc,
                        score=score,
                        chunk_text=doc.content,
                    )
                )

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def search_with_context(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> str:
        """Search and format results as context for LLM prompt augmentation.

        Returns a formatted string suitable for injecting into a system
        prompt or user message for RAG.
        """
        results = self.search(query, top_k=top_k, min_score=min_score)
        if not results:
            return ""

        sections: list[str] = []
        for i, r in enumerate(results, 1):
            source = r.document.metadata.get("source", "unknown")
            sections.append(
                f"[Reference {i}] (score: {r.score:.3f}, source: {source})\n{r.chunk_text}"
            )

        return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Ollama Embedding support (optional, higher quality)
# ---------------------------------------------------------------------------


class OllamaEmbeddingStore(LocalVectorStore):
    """Extended vector store that can use Ollama's embedding API.

    Falls back to TF-IDF when Ollama is unavailable.
    """

    def __init__(
        self,
        store_dir: str | Path | None = None,
        ollama_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        super().__init__(store_dir)
        self._ollama_url = ollama_url.rstrip("/")
        self._embedding_model = embedding_model
        self._use_ollama_embeddings = False

    async def check_embedding_support(self) -> bool:
        """Check if Ollama embedding model is available."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{self._ollama_url}/api/embeddings",
                    json={"model": self._embedding_model, "prompt": "test"},
                )
                self._use_ollama_embeddings = resp.status_code == 200
        except Exception:
            self._use_ollama_embeddings = False
        return self._use_ollama_embeddings

    async def get_embedding(self, text: str) -> list[float] | None:
        """Get embedding vector from Ollama."""
        if not self._use_ollama_embeddings:
            return None
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self._ollama_url}/api/embeddings",
                    json={"model": self._embedding_model, "prompt": text},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("embedding")
        except Exception as exc:
            logger.debug("Ollama embedding failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Global convenience instance
# ---------------------------------------------------------------------------

local_rag = LocalVectorStore()
