# Section 2 — リポジトリ初期化（Zero-Employee Orchestrator）

> 担当: Claude Code
> 基準文書: `Zero-Employee Orchestrator.md`
> 目的: 後続 Section の実装土台を、基準文書の責務分離に沿って初期化する
> 完了条件: backend / frontend / tauri / docs / tests の骨組みが揃い、Section 3 以降に進めること

---

## 0. 実装前提

このプロジェクトは単発の AI チャットアプリではない。  
**会社・組織・目標・チケット・spec / plan / tasks・承認・監査**を扱う、ローカルファーストの業務実行基盤として初期化すること。

必須原則:

- プロジェクト名は **Zero-Employee Orchestrator**
- YouTube は代表デモであり、本体は汎用基盤
- Skill / Plugin / Extension を分離可能な構成にする
- 承認・監査・再実行・中間成果物保存を前提にする
- 人間の最終承認を外さない

---

## 1. ディレクトリ構成

```text
zero-employee-orchestrator/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ auth/
│  │  ├─ companies/
│  │  ├─ org/
│  │  ├─ goals/
│  │  ├─ tickets/
│  │  ├─ specs/
│  │  ├─ plans/
│  │  ├─ tasks/
│  │  ├─ execution/
│  │  ├─ approvals/
│  │  ├─ heartbeat/
│  │  ├─ skills/
│  │  ├─ plugins/
│  │  ├─ extensions/
│  │  ├─ providers/
│  │  ├─ audit/
│  │  ├─ state/
│  │  ├─ db/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  └─ main.py
│  ├─ tests/
│  └─ scripts/
├─ frontend/
│  ├─ src/
│  └─ src-tauri/
├─ docs/
├─ examples/
├─ .github/workflows/
├─ CLAUDE.md
├─ AGENTS.md
└─ README.md
```

---

## 2. 初期化手順

### 2.1 プロジェクト作成

```powershell
mkdir zero-employee-orchestrator
cd zero-employee-orchestrator
git init
```

### 2.2 ディレクトリ作成

```powershell
$dirs = @(
  ".github/workflows",
  "backend/app/api",
  "backend/app/auth",
  "backend/app/companies",
  "backend/app/org",
  "backend/app/goals",
  "backend/app/tickets",
  "backend/app/specs",
  "backend/app/plans",
  "backend/app/tasks",
  "backend/app/execution",
  "backend/app/approvals",
  "backend/app/heartbeat",
  "backend/app/skills/builtins",
  "backend/app/plugins",
  "backend/app/extensions",
  "backend/app/providers",
  "backend/app/audit",
  "backend/app/state",
  "backend/app/db",
  "backend/app/schemas",
  "backend/app/services",
  "backend/tests/unit",
  "backend/tests/integration",
  "backend/tests/e2e",
  "backend/scripts",
  "frontend/src",
  "frontend/src-tauri",
  "docs/api",
  "docs/flows",
  "docs/demos",
  "examples"
)
$dirs | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
```

### 2.3 バックエンド依存導入

```powershell
cd backend
uv init
uv add fastapi uvicorn sqlmodel sqlalchemy alembic pydantic pydantic-settings
uv add pyjwt passlib[bcrypt] python-multipart cryptography keyring
uv add httpx tenacity orjson structlog
uv add pytest pytest-asyncio pytest-cov respx
cd ..
```

### 2.4 フロントエンド初期化

```powershell
pnpm create vite frontend --template react-ts
cd frontend
pnpm add react-router-dom @tanstack/react-query zustand zod
pnpm add tailwindcss @tailwindcss/vite lucide-react recharts
pnpm dlx shadcn@latest init -d
pnpm dlx shadcn@latest add button card input textarea dialog tabs table badge select toast alert scroll-area separator
cd ..
```

### 2.5 Tauri 導入

```powershell
cd frontend
pnpm add -D @tauri-apps/cli
pnpm add @tauri-apps/api @tauri-apps/plugin-shell @tauri-apps/plugin-dialog
pnpm tauri init
cd ..
```

---

## 3. 最初に置く設定ファイル

### 3.1 `CLAUDE.md`

必ず以下を明記すること。

- 基準文書は `Zero-Employee Orchestrator.md`
- spec / plan / tasks を中間成果物として保存する
- 破壊的変更前は Plan Diff を出す
- 承認が必要な操作を自律実行しない
- Skill / Plugin / Extension の責務を混同しない
- 監査ログを欠落させない

### 3.2 `AGENTS.md`

- Claude Code: backend, schema, state machine, tests
- Antigravity: frontend, tauri UI, visual flows
- 共通: 基準文書の用語と責務境界を守る

---

## 4. この Section で最低限作る雛形

- `backend/app/main.py`
- `backend/app/db/session.py`
- `backend/app/db/models.py`
- `backend/app/api/router.py`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/lib/api.ts`
- `README.md`
- `CLAUDE.md`
- `AGENTS.md`

---

## 5. 完了確認

以下を満たせば Section 2 完了。

1. `uv run uvicorn app.main:app --reload --port 18234` が起動する
2. `pnpm dev` で frontend が起動する
3. `pnpm tauri dev` の初期起動準備が整っている
4. backend の責務分離ディレクトリが存在する
5. `CLAUDE.md` と `AGENTS.md` に実装原則が書かれている
6. 基準文書の用語がファイル名・説明文に反映されている
7. Section 3 に進める状態になっている
