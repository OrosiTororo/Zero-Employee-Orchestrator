"""Tests for the enhanced Ollama provider and local RAG.

These tests validate the core logic without requiring a running Ollama instance.
Network-dependent tests are skipped when Ollama is unavailable.
"""

import json
import os
import tempfile


os.environ.setdefault("DEBUG", "true")


# ---------------------------------------------------------------------------
# Tool-call extraction tests
# ---------------------------------------------------------------------------


class TestToolCallExtraction:
    """Test XML-style tool call extraction from local model output."""

    def test_invoke_pattern(self):
        from app.providers.ollama_provider import extract_tool_calls_from_text

        text = """Here's the result:
<invoke name="ReadFile"><parameter name="path">/tmp/test.py</parameter><parameter name="encoding">utf-8</parameter></invoke>
"""
        calls = extract_tool_calls_from_text(text)
        assert len(calls) == 1
        assert calls[0]["function"] == "ReadFile"
        args = json.loads(calls[0]["arguments"])
        assert args["path"] == "/tmp/test.py"
        assert args["encoding"] == "utf-8"

    def test_function_pattern(self):
        from app.providers.ollama_provider import extract_tool_calls_from_text

        text = """<function=SearchWeb>{"query": "Python async"}</function>"""
        calls = extract_tool_calls_from_text(text)
        assert len(calls) == 1
        assert calls[0]["function"] == "SearchWeb"
        args = json.loads(calls[0]["arguments"])
        assert args["query"] == "Python async"

    def test_tool_call_pattern(self):
        from app.providers.ollama_provider import extract_tool_calls_from_text

        text = """<tool_call>{"name": "Bash", "arguments": {"command": "ls -la"}}</tool_call>"""
        calls = extract_tool_calls_from_text(text)
        assert len(calls) == 1
        assert calls[0]["function"] == "Bash"

    def test_no_tool_calls(self):
        from app.providers.ollama_provider import extract_tool_calls_from_text

        text = "Just a normal response without any tool calls."
        calls = extract_tool_calls_from_text(text)
        assert len(calls) == 0

    def test_multiple_invocations(self):
        from app.providers.ollama_provider import extract_tool_calls_from_text

        text = """
<invoke name="Read"><parameter name="file">/a.txt</parameter></invoke>
<invoke name="Write"><parameter name="file">/b.txt</parameter><parameter name="content">hello</parameter></invoke>
"""
        calls = extract_tool_calls_from_text(text)
        assert len(calls) == 2
        assert calls[0]["function"] == "Read"
        assert calls[1]["function"] == "Write"


# ---------------------------------------------------------------------------
# URL security validation tests
# ---------------------------------------------------------------------------


class TestURLSecurity:
    """Test Ollama URL validation (SSRF prevention)."""

    def test_localhost_is_valid(self):
        from app.providers.ollama_provider import validate_ollama_url

        assert validate_ollama_url("http://localhost:11434") is True

    def test_127_0_0_1_is_valid(self):
        from app.providers.ollama_provider import validate_ollama_url

        assert validate_ollama_url("http://127.0.0.1:11434") is True

    def test_external_url_is_invalid(self):
        from app.providers.ollama_provider import validate_ollama_url

        # Public IPs should be rejected
        assert validate_ollama_url("http://8.8.8.8:11434") is False

    def test_private_ip_is_valid(self):
        from app.providers.ollama_provider import validate_ollama_url

        assert validate_ollama_url("http://192.168.1.100:11434") is True


# ---------------------------------------------------------------------------
# OllamaProvider unit tests (no network)
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    """Test OllamaProvider initialization and configuration."""

    def test_default_init(self):
        from app.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider()
        assert provider.base_url == "http://localhost:11434"
        assert provider.available is None  # not checked yet

    def test_custom_url(self):
        from app.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider(base_url="http://127.0.0.1:11435")
        assert provider.base_url == "http://127.0.0.1:11435"

    def test_strip_trailing_slash(self):
        from app.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider(base_url="http://localhost:11434/")
        assert provider.base_url == "http://localhost:11434"


# ---------------------------------------------------------------------------
# Local RAG tests
# ---------------------------------------------------------------------------


class TestTokenization:
    """Test text tokenization for RAG."""

    def test_english_tokenization(self):
        from app.providers.local_rag import tokenize

        tokens = tokenize("Hello world, this is a test.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        # Stopwords should be filtered
        assert "this" not in tokens
        assert "is" not in tokens

    def test_japanese_tokenization(self):
        from app.providers.local_rag import tokenize

        tokens = tokenize("東京タワーを訪問しました")
        # CJK characters should be individually tokenized
        assert len(tokens) > 0
        # Check that individual CJK chars are captured
        assert "東" in tokens
        assert "京" in tokens

    def test_mixed_tokenization(self):
        from app.providers.local_rag import tokenize

        tokens = tokenize("Python3で東京のデータを解析")
        assert "python3" in tokens
        assert "東" in tokens


class TestChunking:
    """Test text chunking."""

    def test_short_text_no_chunking(self):
        from app.providers.local_rag import chunk_text

        text = "Short text"
        chunks = chunk_text(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_chunking(self):
        from app.providers.local_rag import chunk_text

        text = " ".join(f"word{i}" for i in range(200))
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) > 1
        # All original words should appear in at least one chunk
        all_words = set()
        for chunk in chunks:
            all_words.update(chunk.split())
        for i in range(200):
            assert f"word{i}" in all_words


class TestCosineSimilarity:
    """Test cosine similarity computation."""

    def test_identical_vectors(self):
        from app.providers.local_rag import TFIDFVector, cosine_similarity

        a = TFIDFVector(weights={"hello": 1.0, "world": 1.0})
        b = TFIDFVector(weights={"hello": 1.0, "world": 1.0})
        assert abs(cosine_similarity(a, b) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        from app.providers.local_rag import TFIDFVector, cosine_similarity

        a = TFIDFVector(weights={"hello": 1.0})
        b = TFIDFVector(weights={"world": 1.0})
        assert cosine_similarity(a, b) == 0.0

    def test_empty_vectors(self):
        from app.providers.local_rag import TFIDFVector, cosine_similarity

        a = TFIDFVector()
        b = TFIDFVector(weights={"hello": 1.0})
        assert cosine_similarity(a, b) == 0.0

    def test_similar_vectors(self):
        from app.providers.local_rag import TFIDFVector, cosine_similarity

        a = TFIDFVector(weights={"hello": 1.0, "world": 0.5, "python": 0.3})
        b = TFIDFVector(weights={"hello": 0.8, "world": 0.6, "java": 0.4})
        score = cosine_similarity(a, b)
        assert 0.0 < score < 1.0

    def test_symmetry(self):
        from app.providers.local_rag import TFIDFVector, cosine_similarity

        a = TFIDFVector(weights={"a": 1.0, "b": 2.0})
        b = TFIDFVector(weights={"b": 1.0, "c": 3.0})
        assert abs(cosine_similarity(a, b) - cosine_similarity(b, a)) < 1e-10


class TestLocalVectorStore:
    """Test the file-based vector store."""

    def test_add_and_search(self):
        from app.providers.local_rag import LocalVectorStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(store_dir=tmpdir)

            store.add("Python is a great programming language for data science")
            store.add("JavaScript is used for web development")
            store.add("Rust is known for memory safety and performance")

            results = store.search("programming language")
            assert len(results) > 0
            # The Python document should rank highest for "programming language"
            assert (
                "Python" in results[0].chunk_text
                or "programming" in results[0].chunk_text
            )

    def test_persistence(self):
        from app.providers.local_rag import LocalVectorStore

        with tempfile.TemporaryDirectory() as tmpdir:
            # Add documents
            store1 = LocalVectorStore(store_dir=tmpdir)
            store1.add("Document about machine learning", metadata={"source": "test"})
            store1.save()

            # Load in new instance
            store2 = LocalVectorStore(store_dir=tmpdir)
            assert store2.document_count == 1

            results = store2.search("machine learning")
            assert len(results) > 0

    def test_metadata_filter(self):
        from app.providers.local_rag import LocalVectorStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(store_dir=tmpdir)

            store.add("Python coding tutorial", metadata={"category": "programming"})
            store.add("Cooking recipe for pasta", metadata={"category": "cooking"})

            # Search with filter
            results = store.search(
                "tutorial",
                metadata_filter={"category": "programming"},
            )
            assert all(
                r.document.metadata.get("category") == "programming" for r in results
            )

    def test_search_with_context(self):
        from app.providers.local_rag import LocalVectorStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(store_dir=tmpdir)
            store.add(
                "AI orchestration platform for business automation",
                metadata={"source": "docs"},
            )
            store.add("Multi-agent task execution system", metadata={"source": "docs"})

            context = store.search_with_context("orchestration")
            assert isinstance(context, str)
            if context:  # might be empty if no match above threshold
                assert "Reference" in context

    def test_remove_document(self):
        from app.providers.local_rag import LocalVectorStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(store_dir=tmpdir)
            ids = store.add("Test document", auto_chunk=False)
            assert store.document_count == 1

            store.remove(ids[0])
            assert store.document_count == 0

    def test_clear(self):
        from app.providers.local_rag import LocalVectorStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(store_dir=tmpdir)
            store.add("Doc 1")
            store.add("Doc 2")
            assert store.document_count >= 2

            store.clear()
            assert store.document_count == 0

    def test_add_many(self):
        from app.providers.local_rag import LocalVectorStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(store_dir=tmpdir)
            ids = store.add_many(
                [
                    ("First document about Python", {"lang": "en"}),
                    ("Second document about Java", {"lang": "en"}),
                    ("Third document about Rust", {"lang": "en"}),
                ]
            )
            assert len(ids) >= 3


# ---------------------------------------------------------------------------
# i18n tests
# ---------------------------------------------------------------------------


class TestI18n:
    """Test internationalization."""

    def test_japanese(self):
        from app.core.i18n import t, set_language

        set_language("ja")
        result = t("chat_welcome")
        assert "自然言語" in result

    def test_english(self):
        from app.core.i18n import t, set_language

        set_language("en")
        result = t("chat_welcome")
        assert "natural language" in result.lower()

    def test_chinese(self):
        from app.core.i18n import t, set_language

        set_language("zh")
        result = t("chat_welcome")
        assert "自然语言" in result

    def test_format_params(self):
        from app.core.i18n import t, set_language

        set_language("en")
        result = t("orch_task_created", title="My Task")
        assert "My Task" in result

    def test_unknown_key_returns_key(self):
        from app.core.i18n import t

        result = t("nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"

    def test_fallback_language(self):
        from app.core.i18n import set_language, get_language

        set_language("xx")  # unsupported
        assert get_language() == "en"  # falls back to English
