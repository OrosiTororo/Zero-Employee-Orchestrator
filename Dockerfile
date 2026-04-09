# Zero-Employee Orchestrator — Rootless Container
# Runs in a container without root privileges
#
# Build: docker build -t zero-employee-orchestrator .
# Run:   docker run --user 1000:1000 -p 18234:18234 zero-employee-orchestrator

FROM python:3.12-slim AS base

# Security: create non-root user
RUN groupadd -r zeapp -g 1000 && \
    useradd -r -u 1000 -g zeapp -m -d /home/zeapp -s /bin/bash zeapp

# System dependency packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY apps/api/pyproject.toml apps/api/uv.lock* ./apps/api/

# Upgrade pip/setuptools/wheel to fix known CVEs before installing project deps
# (python:3.12-slim bundles older versions with CRITICAL/HIGH CVEs that have fixes)
RUN pip install --upgrade "pip>=26.0" "setuptools>=78.1.1" "wheel>=0.46.2" "PyJWT>=2.12.0"

# Install Python dependencies
WORKDIR /app/apps/api
RUN uv sync --frozen 2>/dev/null || uv pip install --system -r pyproject.toml 2>/dev/null || \
    pip install fastapi uvicorn sqlalchemy[asyncio] aiosqlite pydantic-settings python-jose httpx aiohttp || true

WORKDIR /app

# Copy application code
COPY apps/api/ ./apps/api/
COPY skills/ ./skills/

# Create data directories (writable by non-root user)
RUN mkdir -p /app/data /app/.zero_employee /home/zeapp/.zero_employee && \
    chown -R zeapp:zeapp /app /home/zeapp

# Credential store (protected from AI agents at application layer via IAM)
RUN mkdir -p /app/data/credentials && \
    chmod 700 /app/data/credentials && \
    chown zeapp:zeapp /app/data/credentials

# Switch to non-root user
USER zeapp

# Environment variables
ENV PYTHONPATH=/app/apps/api \
    DATABASE_URL=sqlite+aiosqlite:///./data/zero_employee_orchestrator.db \
    DEBUG=${DEBUG:-false} \
    RAG_STORE_DIR=/app/.zero_employee/rag_store \
    CREDENTIAL_DIR=/app/data/credentials

EXPOSE 18234

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:18234/healthz || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18234"]
