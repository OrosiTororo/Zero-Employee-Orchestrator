# Zero-Employee Orchestrator — 構築ガイド

> 最終更新: 2026-03-10 (v0.1)
> 本ドキュメントは、Zero-Employee Orchestrator をゼロから構築する手順をフェーズごとにコード付きで解説します。

---

## 目次

- [前提条件](#前提条件)
- [Phase 0: 開発基盤の構築](#phase-0-開発基盤の構築)
- [Phase 1: 認証と会社スコープ](#phase-1-認証と会社スコープ)
- [Phase 2: Design Interview と Spec](#phase-2-design-interview-と-spec)
- [Phase 3: Plan と承認フロー](#phase-3-plan-と承認フロー)
- [Phase 4: Task 実行基盤](#phase-4-task-実行基盤)
- [Phase 5: Judge と再計画](#phase-5-judge-と再計画)
- [Phase 6: Skill / Local Context](#phase-6-skill--local-context)
- [Phase 7: UI 構築](#phase-7-ui-構築)
- [Phase 8: Registry / 共有](#phase-8-registry--共有)
- [Phase 9: 高度化（Heartbeat / Goal / Multi-company）](#phase-9-高度化)
- [デプロイ](#デプロイ)

---

## 前提条件

| ツール | バージョン |
|--------|-----------|
| Python | 3.12 以上 |
| Node.js | 20 以上 |
| pnpm | 9 以上 |
| Rust | 最新 stable（Tauri ビルド時のみ） |

### クイックセットアップ

```bash
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # 依存関係の自動インストール・環境構築
./start.sh   # バックエンド + フロントエンドを起動
```

---

## Phase 0: 開発基盤の構築

モノレポ構成、パッケージ管理、開発ツールチェーンを整備します。

### 0-1. ディレクトリ構成

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/              # FastAPI バックエンド (Python)
│   │   ├── app/
│   │   │   ├── core/     # 設定・DB・セキュリティ
│   │   │   ├── api/      # ルーティング
│   │   │   ├── models/   # SQLAlchemy ORM モデル
│   │   │   ├── schemas/  # Pydantic DTO
│   │   │   ├── services/ # ビジネスロジック
│   │   │   ├── orchestration/  # オーケストレーション層
│   │   │   ├── providers/      # LLM ゲートウェイ
│   │   │   ├── audit/          # 監査ログ
│   │   │   └── tests/          # テスト
│   │   ├── alembic/      # DB マイグレーション
│   │   └── pyproject.toml
│   ├── desktop/          # Tauri + React UI
│   │   ├── src-tauri/    # Rust (Tauri)
│   │   └── ui/           # React フロントエンド
│   ├── edge/             # Cloudflare Workers
│   └── worker/           # バックグラウンドワーカー
├── docs/                 # ドキュメント
├── skills/               # Skill 定義
├── plugins/              # Plugin 定義
├── extensions/           # Extension 定義
├── pnpm-workspace.yaml
├── setup.sh
└── start.sh
```

### 0-2. Python バックエンド初期化

```bash
mkdir -p apps/api/app/{core,api,models,schemas,services,orchestration,providers,audit,tests}
cd apps/api
```

**`pyproject.toml`** — Python プロジェクト定義:

```toml
[project]
name = "zero-employee-orchestrator-api"
version = "0.1.0"
description = "Zero-Employee Orchestrator – API backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "aiosqlite>=0.20",
    "alembic>=1.14",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "litellm>=1.60",
    "python-jose[cryptography]>=3.3",
    "cryptography>=44",
    "httpx>=0.28",
    "websockets>=12.0",
    "apscheduler>=3.10",
    "structlog>=24.0",
]

[project.scripts]
zero-employee = "app.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```bash
# 仮想環境の作成とインストール
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

### 0-3. 環境変数設定

**`.env`**:

```env
DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db
SECRET_KEY=change-this-to-a-random-secret-key
CORS_ORIGINS=["http://localhost:5173","http://localhost:1420"]
DEBUG=true
# OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
# OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

### 0-4. 設定モジュール

**`app/core/config.py`**:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        case_sensitive=True, extra="ignore",
    )

    PROJECT_NAME: str = "Zero-Employee Orchestrator"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "CHANGE-ME-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    DATABASE_URL: str = "sqlite+aiosqlite:///./zero_employee_orchestrator.db"


settings = Settings()
```

### 0-5. データベース基盤

**`app/core/database.py`**:

```python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now(),
    )


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
```

### 0-6. セキュリティユーティリティ

**`app/core/security.py`**:

```python
import hashlib
import secrets
import uuid


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def hash_sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def verify_hash(plain: str, hashed: str) -> bool:
    return secrets.compare_digest(hash_sha256(plain), hashed)
```

### 0-7. FastAPI アプリケーションエントリーポイント

**`app/main.py`**:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.routes import api_router
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/healthz", tags=["health"])
async def health_check():
    return {"status": "ok"}
```

### 0-8. 起動確認

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 18234 --reload
# → http://localhost:18234/healthz → {"status": "ok"}
```

---

## Phase 1: 認証と会社スコープ

ユーザー認証、会社（Company）スコープの基盤を構築します。

### 1-1. User モデル

**`app/models/user.py`**:

```python
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(30), default="user")
    status: Mapped[str] = mapped_column(String(30), default="active")
    auth_provider: Mapped[str] = mapped_column(String(50), default="local")
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

### 1-2. Company モデル

**`app/models/company.py`**:

```python
import uuid
from sqlalchemy import String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
```

### 1-3. 認証サービス

**`app/services/auth_service.py`**:

```python
from datetime import datetime, timedelta, timezone
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import generate_uuid, hash_sha256, verify_hash
from app.models.user import User
from app.models.company import Company

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


async def register_user(db: AsyncSession, email: str, password: str, display_name: str) -> User:
    user = User(
        id=generate_uuid(), email=email, display_name=display_name,
        role="owner", status="active", auth_provider="local",
        password_hash=hash_sha256(password),
    )
    db.add(user)

    company = Company(
        id=generate_uuid(), slug=f"company-{str(user.id)[:8]}",
        name=f"{display_name}'s Organization", status="active",
    )
    db.add(company)
    await db.commit()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user and user.password_hash and verify_hash(password, user.password_hash):
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user
    return None
```

### 1-4. 認証エンドポイント

**`app/api/routes/auth.py`**:

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps.database import get_db
from app.services.auth_service import register_user, authenticate_user, create_access_token

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, req.email, req.password, req.display_name)
    token = create_access_token(str(user.id))
    return {"access_token": token, "user_id": str(user.id), "display_name": user.display_name}


@router.post("/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return {"access_token": token, "user_id": str(user.id), "display_name": user.display_name}
```

---

## Phase 2: Design Interview と Spec

自然言語入力を構造化された仕様書（Spec）に変換するパイプラインを構築します。

### 2-1. Interview セッション

**`app/orchestration/interview.py`**:

```python
from dataclasses import dataclass, field


@dataclass
class InterviewQuestion:
    question: str
    category: str  # "objective" | "constraint" | "acceptance" | "risk" | "priority"
    required: bool = True
    answered: bool = False
    answer: str | None = None


@dataclass
class InterviewSession:
    ticket_id: str
    questions: list[InterviewQuestion] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    status: str = "in_progress"

    @property
    def is_complete(self) -> bool:
        return all(q.answered for q in self.questions if q.required)

    def add_answer(self, question_index: int, answer: str) -> None:
        if 0 <= question_index < len(self.questions):
            self.questions[question_index].answered = True
            self.questions[question_index].answer = answer
            self.answers[self.questions[question_index].question] = answer

    def get_pending_questions(self) -> list[InterviewQuestion]:
        return [q for q in self.questions if not q.answered and q.required]


STANDARD_INTERVIEW_TEMPLATE = [
    InterviewQuestion(question="この業務の最終的な目的は何ですか？", category="objective"),
    InterviewQuestion(question="守るべき制約条件はありますか？", category="constraint"),
    InterviewQuestion(question="完了条件（受け入れ基準）は何ですか？", category="acceptance"),
    InterviewQuestion(question="想定されるリスクや注意点はありますか？", category="risk", required=False),
    InterviewQuestion(question="優先順位はどの程度ですか？（高/中/低）", category="priority"),
    InterviewQuestion(question="外部サービスへの接続や送信は必要ですか？", category="constraint"),
    InterviewQuestion(question="人間の承認が必要な工程はありますか？", category="acceptance"),
]


def create_interview_session(ticket_id: str) -> InterviewSession:
    return InterviewSession(
        ticket_id=ticket_id,
        questions=[
            InterviewQuestion(question=q.question, category=q.category, required=q.required)
            for q in STANDARD_INTERVIEW_TEMPLATE
        ],
    )


def generate_spec_from_interview(session: InterviewSession) -> dict:
    objective, constraints, acceptance_criteria, risks = "", [], [], []
    for q in session.questions:
        if q.answer:
            if q.category == "objective":
                objective = q.answer
            elif q.category == "constraint":
                constraints.append(q.answer)
            elif q.category == "acceptance":
                acceptance_criteria.append(q.answer)
            elif q.category == "risk":
                risks.append(q.answer)
    return {
        "objective": objective,
        "constraints_json": {"items": constraints},
        "acceptance_criteria_json": {"items": acceptance_criteria},
        "risk_notes": "\n".join(risks) if risks else None,
    }
```

### 2-2. Spec モデル

**`app/models/spec.py`**:

```python
import uuid
from sqlalchemy import ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base, TimestampMixin


class Spec(Base, TimestampMixin):
    __tablename__ = "specs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tickets.id"), index=True)
    version_no: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    objective: Mapped[str] = mapped_column(Text)
    constraints_json: Mapped[dict] = mapped_column(JSON, default=dict)
    acceptance_criteria_json: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_type: Mapped[str] = mapped_column(String(30), default="ai")
```

### 2-3. Interview → Spec 連携エンドポイント

チケット作成時に Interview セッションが自動生成され、質問回答が完了すると Spec が自動生成されます。

```python
# POST /api/v1/companies/{id}/tickets
#   → チケット作成 + Interview セッション初期化
# POST /api/v1/tickets/{id}/interview/answer
#   → 質問に回答
# POST /api/v1/tickets/{id}/interview/generate-spec
#   → Interview 回答から Spec を自動生成
```

---

## Phase 3: Plan と承認フロー

Spec に基づいて実行計画（Plan）を生成し、承認フローを構築します。

### 3-1. Cost Guard — コスト見積もり

**`app/orchestration/cost_guard.py`**:

```python
from dataclasses import dataclass
from enum import Enum


class CostDecision(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


DEFAULT_COST_TABLE: dict[str, dict[str, float]] = {
    "gpt-5.4": {"input": 0.005, "output": 0.015},
    "gpt-5-mini": {"input": 0.00015, "output": 0.0006},
    "claude-opus-4-6": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5-20251001": {"input": 0.001, "output": 0.005},
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.5-flash-lite": {"input": 0.00005, "output": 0.0002},
}


@dataclass
class CostEstimate:
    model_name: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    breakdown: dict[str, float]


def estimate_cost(model_name: str, estimated_input_tokens: int = 1000,
                  estimated_output_tokens: int = 500) -> CostEstimate:
    rates = {"input": 0.002, "output": 0.002}
    model_lower = model_name.lower()
    best_match_len = 0
    for key, value in DEFAULT_COST_TABLE.items():
        if model_lower.startswith(key.lower()) and len(key) > best_match_len:
            rates = value
            best_match_len = len(key)

    input_cost = (estimated_input_tokens / 1000) * rates["input"]
    output_cost = (estimated_output_tokens / 1000) * rates["output"]
    return CostEstimate(
        model_name=model_name, estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        estimated_cost_usd=round(input_cost + output_cost, 6),
        breakdown={"input_cost": round(input_cost, 6), "output_cost": round(output_cost, 6)},
    )


def check_budget(estimated_cost_usd: float, budget_limit_usd: float,
                 current_usage_usd: float, warn_threshold_pct: float = 80.0) -> CostDecision:
    if budget_limit_usd <= 0:
        return CostDecision.ALLOW
    projected = current_usage_usd + estimated_cost_usd
    usage_pct = (projected / budget_limit_usd) * 100
    if usage_pct >= 100:
        return CostDecision.BLOCK
    elif usage_pct >= warn_threshold_pct:
        return CostDecision.WARN
    return CostDecision.ALLOW
```

### 3-2. Quality SLA — 品質モードとモデル選択

**`app/orchestration/quality_sla.py`**:

```python
from dataclasses import dataclass
from enum import Enum


class QualityMode(str, Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualitySLAConfig:
    mode: QualityMode
    preferred_models: list[str]
    fallback_models: list[str]
    max_retries: int
    judge_pass_threshold: float
    requires_human_review: bool
    cross_model_verification: bool
    max_tokens: int


DEFAULT_SLA_CONFIGS = {
    QualityMode.DRAFT: QualitySLAConfig(
        mode=QualityMode.DRAFT, preferred_models=["gpt-5-mini", "claude-haiku-4-5-20251001"],
        fallback_models=["gemini-2.5-flash-lite"], max_retries=1,
        judge_pass_threshold=0.5, requires_human_review=False,
        cross_model_verification=False, max_tokens=2000,
    ),
    QualityMode.STANDARD: QualitySLAConfig(
        mode=QualityMode.STANDARD, preferred_models=["gpt-5.4", "claude-sonnet-4-6"],
        fallback_models=["gpt-5-mini", "claude-haiku-4-5-20251001"], max_retries=2,
        judge_pass_threshold=0.7, requires_human_review=False,
        cross_model_verification=False, max_tokens=4000,
    ),
    QualityMode.HIGH: QualitySLAConfig(
        mode=QualityMode.HIGH, preferred_models=["gpt-5.4", "claude-sonnet-4-6"],
        fallback_models=["claude-opus-4-6", "gemini-2.5-pro"], max_retries=3,
        judge_pass_threshold=0.85, requires_human_review=False,
        cross_model_verification=True, max_tokens=8000,
    ),
    QualityMode.CRITICAL: QualitySLAConfig(
        mode=QualityMode.CRITICAL, preferred_models=["claude-opus-4-6", "gpt-5.4"],
        fallback_models=["claude-sonnet-4-6", "gemini-2.5-pro"], max_retries=5,
        judge_pass_threshold=0.95, requires_human_review=True,
        cross_model_verification=True, max_tokens=16000,
    ),
}
```

### 3-3. DAG — タスク依存関係グラフ

**`app/orchestration/dag.py`**:

```python
from dataclasses import dataclass, field
from enum import Enum


class TaskNodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    id: str
    title: str
    task_type: str = "execute"
    depends_on: list[str] = field(default_factory=list)
    status: TaskNodeStatus = TaskNodeStatus.PENDING
    requires_approval: bool = False
    estimated_cost_usd: float = 0.0
    estimated_minutes: int = 0


@dataclass
class ExecutionDAG:
    plan_id: str
    nodes: list[TaskNode] = field(default_factory=list)
    _node_map: dict[str, TaskNode] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._node_map = {n.id: n for n in self.nodes}

    def add_node(self, node: TaskNode):
        self.nodes.append(node)
        self._node_map[node.id] = node

    def get_ready_nodes(self) -> list[TaskNode]:
        ready = []
        for node in self.nodes:
            if node.status != TaskNodeStatus.PENDING:
                continue
            deps_ok = all(
                self._node_map.get(d, TaskNode(id="")).status == TaskNodeStatus.SUCCEEDED
                for d in node.depends_on
            )
            if deps_ok:
                ready.append(node)
        return ready

    def mark_completed(self, node_id: str, success: bool = True) -> list[TaskNode]:
        node = self._node_map.get(node_id)
        if node:
            node.status = TaskNodeStatus.SUCCEEDED if success else TaskNodeStatus.FAILED
        return self.get_ready_nodes()

    def get_total_estimated_cost(self) -> float:
        return sum(n.estimated_cost_usd for n in self.nodes)

    def get_critical_path_minutes(self) -> int:
        if not self.nodes:
            return 0
        longest = {}
        for node in self.nodes:
            dep_max = max((longest.get(d, 0) for d in node.depends_on), default=0)
            longest[node.id] = dep_max + node.estimated_minutes
        return max(longest.values()) if longest else 0
```

### 3-4. 承認フローの実装

Plan の承認後にのみ Tasks が生成・実行されるフローを構築します。

```python
# POST /api/v1/tickets/{id}/plans        → Plan 生成（Cost Guard + Quality SLA 付き）
# POST /api/v1/plans/{id}/approve        → Plan 承認 → Tasks 自動生成
# POST /api/v1/plans/{id}/reject         → Plan 却下 → Re-Propose トリガー
```

---

## Phase 4: Task 実行基盤

状態機械による厳密なライフサイクル管理とバックグラウンドワーカーを構築します。

### 4-1. 状態機械

**`app/orchestration/state_machine.py`**:

```python
from datetime import datetime, timezone


class StateMachineError(Exception):
    pass


class BaseStateMachine:
    transitions: dict[str, list[str]] = {}

    def __init__(self, initial_state: str):
        if initial_state not in self.transitions:
            raise StateMachineError(f"不明な初期状態: {initial_state}")
        self._state = initial_state
        self._history: list[dict[str, str]] = []

    @property
    def state(self) -> str:
        return self._state

    def can_transition(self, target: str) -> bool:
        return target in self.transitions.get(self._state, [])

    def transition(self, target: str, reason: str = "") -> str:
        if not self.can_transition(target):
            raise StateMachineError(
                f"遷移不可: {self._state} → {target} (許可: {self.transitions.get(self._state, [])})"
            )
        old = self._state
        self._state = target
        self._history.append({
            "from": old, "to": target, "reason": reason,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        return self._state


class TicketStateMachine(BaseStateMachine):
    transitions = {
        "draft": ["open", "cancelled"],
        "open": ["interviewing", "planning", "cancelled"],
        "interviewing": ["open", "planning", "cancelled"],
        "planning": ["ready", "open", "cancelled"],
        "ready": ["in_progress", "cancelled"],
        "in_progress": ["review", "blocked", "cancelled"],
        "blocked": ["in_progress", "cancelled"],
        "review": ["done", "rework", "cancelled"],
        "done": ["closed", "reopened"],
        "closed": ["reopened"],
        "cancelled": [],
    }


class TaskStateMachine(BaseStateMachine):
    transitions = {
        "pending": ["ready", "cancelled"],
        "ready": ["running", "blocked"],
        "running": ["succeeded", "failed", "awaiting_approval", "blocked"],
        "awaiting_approval": ["running", "cancelled"],
        "failed": ["retrying", "cancelled"],
        "retrying": ["running", "failed"],
        "succeeded": ["verified", "archived"],
        "cancelled": [],
        "archived": [],
    }
```

### 4-2. バックグラウンドワーカー

**`apps/worker/main.py`**:

```python
import asyncio
import logging
import signal
from app.runners.task_runner import TaskRunner
from app.runners.heartbeat_runner import HeartbeatRunner
from app.dispatchers.event_dispatcher import EventDispatcher

logger = logging.getLogger(__name__)
shutdown_event = asyncio.Event()


def handle_signal(sig, frame):
    shutdown_event.set()


async def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    task_runner = TaskRunner()
    heartbeat_runner = HeartbeatRunner()
    event_dispatcher = EventDispatcher()

    tasks = [
        asyncio.create_task(task_runner.run(shutdown_event)),
        asyncio.create_task(heartbeat_runner.run(shutdown_event)),
        asyncio.create_task(event_dispatcher.run(shutdown_event)),
    ]

    await shutdown_event.wait()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
```

### 4-3. TaskRunner — タスク実行エンジン

**`apps/worker/app/runners/task_runner.py`** (抜粋):

```python
class TaskRunner:
    def __init__(self, poll_interval: float = 5.0):
        self.poll_interval = poll_interval

    async def run(self, shutdown_event):
        while not shutdown_event.is_set():
            await self._process_ready_tasks()
            await asyncio.sleep(self.poll_interval)

    async def _process_ready_tasks(self):
        async with async_session_factory() as db:
            result = await db.execute(
                select(Task).where(Task.status == "ready").limit(10)
            )
            for task in result.scalars().all():
                await self._execute_single_task(db, task)

    async def _execute_single_task(self, db, task):
        # 1. Mark as running
        task.status = "running"
        # 2. Execute via LLM or Sandbox executor
        exec_result = await self._dispatch_execution(task)
        # 3. Judge output quality
        judge_result = self._judge_output(exec_result, task)
        # 4. Update status (success/retry/fail)
        # 5. Record audit log
```

---

## Phase 5: Judge と再計画

品質検証と失敗時の自動再計画メカニズムを構築します。

### 5-1. Judge Layer — 品質検証

**`app/orchestration/judge.py`** (抜粋):

```python
from dataclasses import dataclass
from enum import Enum


class JudgeVerdict(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


@dataclass
class JudgeResult:
    verdict: JudgeVerdict
    score: float  # 0.0 - 1.0
    reasons: list[str]
    suggestions: list[str]
    policy_violations: list[str]
    requires_human_review: bool = False


class RuleBasedJudge:
    """Stage 1: 高速ルールベースチェック"""
    def evaluate(self, output: dict, context: dict | None = None) -> JudgeResult: ...


class PolicyPackJudge:
    """Stage 2: ポリシー準拠チェック + 危険操作検出 + 認証情報漏洩チェック"""
    def evaluate(self, output: dict, operations: list[str] | None = None) -> JudgeResult: ...


class CrossModelJudge:
    """Stage 3: 複数モデル出力の一致度検証"""
    def evaluate(self, outputs: list[dict]) -> JudgeResult: ...


def judge_output(output: dict, operations=None, context=None) -> JudgeResult:
    """Two-stage judge: ルールベース → ポリシーチェック"""
    rule_result = rule_judge.evaluate(output, context)
    if rule_result.verdict == JudgeVerdict.FAIL:
        return rule_result
    policy_result = policy_judge.evaluate(output, operations)
    # ... 結果を統合して返す
```

### 5-2. Failure Taxonomy — 障害分類

**`app/orchestration/failure_taxonomy.py`** (抜粋):

```python
class FailureCategory(str, Enum):
    LLM_ERROR = "llm_error"
    TOOL_ERROR = "tool_error"
    VALIDATION_ERROR = "validation_error"
    BUDGET_ERROR = "budget_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_ERROR = "permission_error"
    DEPENDENCY_ERROR = "dependency_error"
    HUMAN_REJECTION = "human_rejection"
    SYSTEM_ERROR = "system_error"


class FailureSeverity(str, Enum):
    LOW = "low"          # 自動リトライで回復可能
    MEDIUM = "medium"    # 代替手段で回復可能
    HIGH = "high"        # 人間介入が必要
    CRITICAL = "critical"  # 即座にエスカレーション


class FailureTaxonomy:
    def record_failure(self, category, subcategory, severity, description, prevention_strategy): ...
    def record_recovery(self, category, subcategory): ...
    def get_frequent_failures(self, min_count=2): ...
    def get_prevention_strategies(self, category=None): ...
```

### 5-3. Re-Propose — 再提案

**`app/orchestration/repropose.py`** (抜粋):

```python
@dataclass
class PlanDiff:
    added_tasks: list[str] = field(default_factory=list)
    removed_tasks: list[str] = field(default_factory=list)
    modified_tasks: list[str] = field(default_factory=list)
    cost_change_usd: float = 0.0
    time_change_minutes: int = 0
    reason: str = ""


def classify_failure(error_code, error_message) -> ReworkReason:
    """エラーを Failure Taxonomy に基づいて分類"""
    ...

def generate_reproposal(original_plan, rework_reasons, constraints=None) -> ReproposalResult:
    """失敗分析に基づいて再提案を生成"""
    ...
```

### 5-4. Self-Healing DAG

```python
def rebuild_dag_after_failure(dag, failed_node_id, strategy="retry") -> ExecutionDAG:
    """
    戦略:
    - retry:  失敗ノードを pending に戻してリトライ
    - skip:   失敗ノードをスキップし依存制約を解除
    - replan: DAG 全体の再計画をトリガー
    """
    node = dag._node_map.get(failed_node_id)
    if strategy == "retry":
        node.status = TaskNodeStatus.PENDING
    elif strategy == "skip":
        node.status = TaskNodeStatus.SKIPPED
        for n in dag.nodes:
            if failed_node_id in n.depends_on:
                n.depends_on.remove(failed_node_id)
    elif strategy == "replan":
        for n in dag.nodes:
            if n.status == TaskNodeStatus.PENDING:
                n.status = TaskNodeStatus.BLOCKED
    return dag
```

---

## Phase 6: Skill / Local Context

Skill 実行基盤と Local Context アクセスを構築します。

### 6-1. LLM Gateway

**`app/providers/gateway.py`** (抜粋):

```python
class LLMGateway:
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        model = request.model or self.select_model(request.mode)
        response = await litellm.acompletion(
            model=model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=request.tools,
        )
        return CompletionResponse(
            content=response.choices[0].message.content,
            model_used=model,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens,
        )
```

### 6-2. Sandbox Executor

**`apps/worker/app/executors/sandbox_executor.py`** (抜粋):

```python
@dataclass
class SandboxConfig:
    max_memory_mb: int = 256
    max_cpu_seconds: int = 30
    allowed_network: bool = False


class SandboxExecutor:
    async def execute_python(self, code: str, inputs: dict | None = None) -> SandboxResult:
        """Python コードを安全なサブプロセスで実行（時間制限付き）"""
        proc = await asyncio.create_subprocess_exec(
            "python3", script_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=self.config.max_cpu_seconds,
        )
        return SandboxResult(success=proc.returncode == 0, stdout=stdout.decode(), stderr=stderr.decode())
```

### 6-3. Experience Memory

**`app/orchestration/state_machine.py`** (Experience Memory セクション):

```python
class ExperienceMemory:
    def add_success_pattern(self, title, content, category, source_ticket_id=None): ...
    def add_failure(self, category, subcategory, description, prevention_strategy): ...
    def search(self, query, category=None) -> list[ExperienceMemoryEntry]: ...
    def get_frequent_failures(self, min_count=2) -> list[FailureTaxonomyEntry]: ...
```

---

## Phase 7: UI 構築

React 19 + TypeScript + Tailwind CSS でフロントエンドを構築します。

### 7-1. プロジェクト初期化

```bash
cd apps/desktop/ui
pnpm create vite . --template react-ts
pnpm add react-router-dom @tanstack/react-query zustand tailwindcss @tailwindcss/vite
pnpm add recharts lucide-react clsx tailwind-merge
```

**`package.json`** (主要依存関係):

```json
{
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.13.1",
    "@tanstack/react-query": "^5.62.0",
    "zustand": "^5.0.0",
    "tailwindcss": "^4.2.1",
    "recharts": "^3.7.0",
    "lucide-react": "^0.576.0"
  }
}
```

### 7-2. API クライアント

**`src/shared/api/client.ts`**:

```typescript
const BASE_URL = "http://localhost:18234/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
```

### 7-3. ルーティング

**`src/app/router.tsx`**:

```tsx
import { createBrowserRouter } from "react-router-dom";
import { Layout } from "../shared/ui/Layout";
// ... 各ページコンポーネントをインポート

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/setup", element: <SetupPage /> },
  {
    element: <Layout />,
    children: [
      { path: "/", element: <DashboardPage /> },
      { path: "/tickets", element: <TicketListPage /> },
      { path: "/tickets/:id", element: <TicketDetailPage /> },
      { path: "/tickets/:id/interview", element: <InterviewPage /> },
      { path: "/tickets/:id/spec-plan", element: <SpecPlanPage /> },
      { path: "/approvals", element: <ApprovalsPage /> },
      { path: "/artifacts", element: <ArtifactsPage /> },
      { path: "/heartbeats", element: <HeartbeatsPage /> },
      { path: "/costs", element: <CostsPage /> },
      { path: "/audit", element: <AuditPage /> },
      { path: "/skills", element: <SkillsPage /> },
      { path: "/skills/create", element: <SkillCreatePage /> },
      { path: "/plugins", element: <PluginsPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "/org-chart", element: <OrgChartPage /> },
    ],
  },
]);
```

### 7-4. 主要画面

**20+ 画面**を提供:

| 画面 | 主な機能 |
|------|---------|
| ダッシュボード | 統計、自然言語入力、クイックナビ |
| チケット一覧/詳細 | CRUD、状態遷移、コメント |
| Design Interview | 7 つの質問への回答 UI |
| Spec/Plan | レビュー・承認 |
| 承認キュー | リスクレベル付き承認/却下 |
| 監査ログ | フィルタリング付きログビューア |
| コスト管理 | 予算ポリシー、支出追跡 |
| Heartbeat | 定期実行ポリシー・履歴 |
| 組織図 | 部門・チーム・エージェントの可視化 |

---

## Phase 8: Registry / 共有

Skill / Plugin / Extension のパッケージングと配布基盤を構築します。

### 8-1. Registry API

```python
# GET  /api/v1/skills                → Skill 一覧
# POST /api/v1/skills/install        → Skill インストール
# GET  /api/v1/plugins               → Plugin 一覧
# POST /api/v1/plugins/install       → Plugin インストール
# GET  /api/v1/extensions            → Extension 一覧
# POST /api/v1/extensions/install    → Extension インストール
```

### 8-2. ステータス管理

Skill / Plugin / Extension は以下のステータスを持ちます:

```python
class RegistryStatus(str, Enum):
    VERIFIED = "verified"          # 検証済み
    EXPERIMENTAL = "experimental"  # 実験的
    PRIVATE = "private"            # 非公開
    DEPRECATED = "deprecated"      # 非推奨
```

---

## Phase 9: 高度化

Heartbeat、Goal Alignment、Multi-company 対応などの高度な機能を追加します。

### 9-1. 監査ログ

**`app/audit/logger.py`**:

```python
async def record_audit_event(
    db, company_id, event_type, target_type, *,
    actor_type="system", actor_user_id=None, actor_agent_id=None,
    target_id=None, ticket_id=None, task_id=None, details=None,
):
    """監査イベントを記録"""
    log = AuditLog(
        id=generate_uuid(), company_id=company_id,
        actor_type=actor_type, event_type=event_type,
        target_type=target_type, target_id=target_id, details_json=details or {},
    )
    db.add(log)
    await db.commit()
    return log


async def record_state_change(db, company_id, target_type, target_id, old_status, new_status, **kwargs):
    """状態遷移を監査ログに記録"""
    ...

async def record_dangerous_operation(db, company_id, operation_type, target_type, target_id, **kwargs):
    """危険操作の実行を監査ログに記録"""
    ...
```

### 9-2. WebSocket リアルタイム通信

```python
# /ws/events — リアルタイムイベントストリーミング
# - タスク進捗更新
# - 承認リクエスト通知
# - エージェント状態変化
# - エラー即座通知
```

### 9-3. Heartbeat ポリシー

```python
# Cron 式スケジューリング、ジッター設定、並列実行制御
# GET  /api/v1/companies/{id}/heartbeat-policies
# POST /api/v1/companies/{id}/heartbeat-policies
# GET  /api/v1/companies/{id}/heartbeat-runs
```

---

## デプロイ

### ローカル開発

```bash
# 一括起動
./start.sh

# 個別起動
# バックエンド
cd apps/api && source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 18234 --reload

# フロントエンド
cd apps/desktop/ui && pnpm dev

# ワーカー
cd apps/worker && python main.py
```

### 本番環境

```env
# PostgreSQL の使用
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zero_employee_orchestrator

# セキュリティ設定
SECRET_KEY=<ランダム文字列>
DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

### Cloudflare Workers デプロイ

```bash
# 方式 A: Proxy
cd apps/edge/proxy && npm install && npm run dev

# 方式 B: Full Workers (サーバーレス)
cd apps/edge/full && npm install && npm run db:init && npm run dev

# フロントエンド (Cloudflare Pages)
cd apps/desktop/ui && pnpm build
npx wrangler pages deploy dist --project-name=zeo-ui
```

### Tauri デスクトップビルド

```bash
cd apps/desktop
cargo tauri build
# → Windows: .msi / .exe
# → macOS: .dmg
# → Linux: .AppImage / .deb
```

---

## テスト

```bash
# バックエンドテスト
cd apps/api
source .venv/bin/activate
pip install pytest pytest-asyncio httpx
pytest app/tests/ -v

# 主なテストファイル:
# - test_state_machine.py   → 状態遷移の検証
# - test_cost_guard.py      → コスト見積もり・予算チェック
# - test_failure_taxonomy.py → 障害分類
# - test_auth.py            → 認証（登録・ログイン・トークン）
# - test_tickets.py         → チケット CRUD
# - test_companies.py       → 会社管理
# - test_registry.py        → Skill レジストリ
# - test_health.py          → ヘルスチェック
# - test_audit_logger.py    → 監査ログ

# フロントエンドリント
cd apps/desktop/ui
pnpm lint
```

---

## 参照文書

| 文書 | 役割 |
|------|------|
| `docs/Zero-Employee Orchestrator.md` | 最上位基準文書（思想・要件） |
| `docs/dev/DESIGN.md` | 実装設計書（DB・API・画面・状態遷移） |
| `docs/dev/MASTER_GUIDE.md` | 実装運用ガイド |
| `docs/FEATURES.md` | 機能一覧（本ガイドの姉妹文書） |
| `docs/dev/instructions_section2〜7` | 各領域の実装指示 |
