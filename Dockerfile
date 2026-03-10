# Zero-Employee Orchestrator — Rootless Container
# root権限なしでコンテナ上で動作可能
#
# ビルド: docker build -t zero-employee-orchestrator .
# 実行:   docker run --user 1000:1000 -p 18234:18234 zero-employee-orchestrator

FROM python:3.12-slim AS base

# セキュリティ: non-root ユーザーを作成
RUN groupadd -r zeapp -g 1000 && \
    useradd -r -u 1000 -g zeapp -m -d /home/zeapp -s /bin/bash zeapp

# システム依存パッケージ
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# uv のインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存関係ファイルをコピー
COPY apps/api/pyproject.toml apps/api/uv.lock* ./apps/api/

# Python依存関係のインストール
WORKDIR /app/apps/api
RUN uv sync --frozen 2>/dev/null || uv pip install --system -r pyproject.toml 2>/dev/null || \
    pip install fastapi uvicorn sqlalchemy[asyncio] aiosqlite pydantic-settings python-jose httpx aiohttp || true

WORKDIR /app

# アプリケーションコードをコピー
COPY apps/api/ ./apps/api/
COPY skills/ ./skills/

# データディレクトリの作成（non-rootユーザーが書き込み可能に）
RUN mkdir -p /app/data /app/.zero_employee /home/zeapp/.zero_employee && \
    chown -R zeapp:zeapp /app /home/zeapp

# 認証情報ストア（AIエージェントからアクセス不可）
RUN mkdir -p /etc/zero-employee/credentials && \
    chmod 700 /etc/zero-employee/credentials && \
    chown root:root /etc/zero-employee/credentials

# non-root ユーザーに切り替え
USER zeapp

# 環境変数
ENV PYTHONPATH=/app/apps/api \
    DATABASE_URL=sqlite+aiosqlite:///./data/zero_employee_orchestrator.db \
    DEBUG=true \
    RAG_STORE_DIR=/app/.zero_employee/rag_store \
    CREDENTIAL_DIR=/etc/zero-employee/credentials

EXPOSE 18234

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:18234/healthz || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18234"]
