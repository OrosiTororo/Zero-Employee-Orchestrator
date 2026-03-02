# Section 2 — リポジトリ初期化（Claude Code 用）v11.2

> 担当: Claude Code（全ステップ）
> 前提: Section 1 の確認コマンドが全て PASS していること
> 完了条件: 7 項目の動作確認が全て PASS
> v11.2 追加: local_context Skill ディレクトリ、CLAUDE.md にローカル特権・Self-Healing・Skill Registry 記述追加

---

## ステップ 2.1 — プロジェクト作成

```powershell
mkdir zpcos
cd zpcos
git init
```

---

## ステップ 2.2 — ディレクトリツリー一括作成

```powershell
$dirs = @(
  ".github/workflows"
  "backend/app/auth/connectors"
  "backend/app/gateway"
  "backend/app/interview"
  "backend/app/judge"
  "backend/app/orchestrator"
  "backend/app/policy"
  "backend/app/skills/builtins/yt_script"
  "backend/app/skills/builtins/yt_rival"
  "backend/app/skills/builtins/yt_trend"
  "backend/app/skills/builtins/yt_performance"
  "backend/app/skills/builtins/yt_next_move"
  "backend/app/skills/builtins/local_context"
  "backend/app/engine"
  "backend/app/state"
  "backend/tests"
  "backend/scripts"
  "frontend/src/components/ui"
  "frontend/src/pages"
  "frontend/src/hooks"
  "frontend/src/lib"
  "frontend/src/styles"
  "frontend/src-tauri/src"
  "frontend/src-tauri/binaries"
  "frontend/src-tauri/capabilities"
  "frontend/src-tauri/icons"
  "docs"
  "shared/types"
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path $d }
```

---

## ステップ 2.3 — .gitignore

ファイル: `zpcos/.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
*.egg
*.spec

# 秘密情報
.env
.env.local
client_secret.json
*.enc

# Node
node_modules/
.next/

# Tauri
frontend/src-tauri/target/
frontend/src-tauri/binaries/*.exe

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# テスト
.coverage
htmlcov/
.pytest_cache/

# ビルド成果物
*.msi
*.nsis
*.AppImage
*.dmg
```

---

## ステップ 2.4 — バックエンド Python 環境

```powershell
cd backend
uv init --name zpcos-backend --python 3.12
```

以下で `pyproject.toml` を上書き:

ファイル: `backend/pyproject.toml`

```toml
[project]
name = "zpcos-backend"
version = "0.1.0"
description = "ZPCOS — Zero-Prompt Cross-model Orchestration System Backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "litellm>=1.55.0",
    "pydantic>=2.10.0",
    "transitions>=0.9.2",
    "aiosqlite>=0.20.0",
    "keyring>=25.5.0",
    "cryptography>=44.0.0",
    "google-auth-oauthlib>=1.2.1",
    "google-api-python-client>=2.155.0",
    "httpx>=0.28.0",
    "pyinstaller>=6.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

インストール:

```powershell
uv sync
uv sync --extra dev
```

確認:

```powershell
uv run python -c "import fastapi; import litellm; import transitions; import keyring; import cryptography; print('OK')"
```

---

## ステップ 2.5 — __init__.py 配置

connectors/ は JSON データディレクトリなので含めない。

```powershell
$pyPackages = @(
  "backend/app"
  "backend/app/auth"
  "backend/app/gateway"
  "backend/app/interview"
  "backend/app/judge"
  "backend/app/orchestrator"
  "backend/app/policy"
  "backend/app/skills"
  "backend/app/skills/builtins"
  "backend/app/engine"
  "backend/app/state"
  "backend/tests"
)
foreach ($d in $pyPackages) {
  New-Item -ItemType File -Force -Path "$d/__init__.py"
}
```

---

## ステップ 2.6 — CLAUDE.md

ファイル: `zpcos/CLAUDE.md`

```markdown
# ZPCOS — Claude Code 開発ガイド

## プロジェクト概要
ZPCOS（Zero-Prompt Cross-model Orchestration System）は、複数の LLM を自動的に
使い分け、ユーザーが AI のモデル名やパラメータを意識することなく最適な回答を得られる
Windows デスクトップアプリケーションである。

## 9層アーキテクチャ（v11.2）
1. User Layer — 自然言語で目的を伝える
2. Design Interview — 壁打ち・すり合わせで要件を深掘り
3. Task Orchestrator — タスク分解・Skill割当・進行管理 + Self-Healing DAG
4. Skill Layer — 単一目的の専門Skill + Local Context Skill（ローカルファイル分析）
5. Judge Layer — Two-stage Detection + Cross-Model Verificationで品質保証
6. Re-Propose Layer — 差し戻し時の再提案 + 動的DAG再構築
7. State & Memory — 永続的な実行環境・履歴・Experience Memory
8. Provider Interface — OpenRouter経由のLLMゲートウェイ
9. Skill Registry — コミュニティSkillの公開・検索・インストール

## ローカルOS としての設計意図
- ローカル特権アクセスにより、機密データを含むファイルをクラウドに送信せず安全に処理
- Self-Healing DAG により、失敗時にAI組織が自律的にDAGを再構築してリトライ
- Skill Registry により、世界中の開発者が業務自動化Skillを共有するエコシステムを形成

## 技術スタック
- バックエンド: Python 3.12 / FastAPI / uvicorn
- LLM ゲートウェイ: LiteLLM Router SDK（openrouter/ プレフィックスで全モデルアクセス）
- LLM プロバイダー: OpenRouter（OAuth PKCE 認証、ユーザー課金）
- 認証: AuthHub（OpenRouter OAuth PKCE + Google OAuth InstalledAppFlow）
- トークン保存: keyring（暗号鍵のみ）+ AES-GCM 暗号化ファイル（トークン本体）
- 状態機械: python-transitions AsyncMachine / aiosqlite 永続化
- フロントエンド: React 19 + TypeScript + Vite + shadcn/ui
- デスクトップ: Tauri v2（Rust）、Python バックエンドはサイドカー（PyInstaller .exe）
- パッケージ管理: uv（Python）、pnpm（Node.js）

## コーディング規約
- Python: ruff でフォーマット・リント、型ヒント必須、docstring は日本語可
- TypeScript: strict モード、関数コンポーネントのみ
- テスト: pytest + pytest-asyncio、テストファイルは tests/test_*.py
- コミット: Conventional Commits（feat:, fix:, docs:, refactor:, test:）
- エラーハンドリング: 例外は具体的にキャッチ、ログ出力必須

## ディレクトリの役割
- backend/app/auth/ — OpenRouter OAuth、Google OAuth、AuthHub、トークン保存
- backend/app/auth/connectors/ — サービス定義 JSON（Python パッケージではない）
- backend/app/gateway/ — LiteLLM Router 初期化、providers.json
- backend/app/interview/ — Design Interview + Spec Writer
- backend/app/judge/ — Cross-Model Judge パイプライン + Two-stage Detection
- backend/app/orchestrator/ — Task Orchestrator + Self-Healing DAG + Cost Guard
- backend/app/policy/ — Policy Pack（コンプライアンスチェック）
- backend/app/skills/ — Skill フレームワーク、ビルトイン Skills、Skill Registry
- backend/app/skills/builtins/local_context/ — ローカルファイル分析 Skill（★v11.2）
- backend/app/engine/ — Skill 自動生成エンジン
- backend/app/state/ — AsyncMachine 状態機械、SQLite 永続化、Experience Memory

## セキュリティ制約
- Skill executor.py インポートホワイトリスト: httpx, json, re, datetime, pydantic, math, typing
- 関数ブラックリスト: eval, exec, compile, __import__, open（書込）, os.system, subprocess
- トークン: keyring に AES-256 鍵、%APPDATA%/zpcos/tokens/{service}.enc にトークン

## 非同期ルール
- FastAPI エンドポイントは全て async def
- ブロッキング呼び出しは asyncio.to_thread()
- 状態機械は AsyncMachine
- LiteLLM は router.acompletion()
- google-api-python-client の service は毎回 build() で新規作成

## PyInstaller 対応ルール
- ファイルパスは必ず resource_path() 経由で解決
- client_secret.json 探索順: %APPDATA%/zpcos/ → sys._MEIPASS → backend/
- uvicorn は uvicorn.run(app, ...) オブジェクト参照方式
- multiprocessing.freeze_support() を if __name__ 内で必ず呼ぶ
- JSON は build_sidecar.ps1 の --add-data でバンドル

## LiteLLM モデル名規則
OpenRouter 経由モデルは openrouter/ プレフィックス必須。
エイリアス（fast, think, quality 等）は providers.json の model_name で定義。

## 認証アーキテクチャ
- OpenRouter OAuth PKCE: http://localhost:3000/callback 固定
- AuthHub: connectors/ の JSON で管理
- Google OAuth: InstalledAppFlow + PKCE。port=0（自動）
- Skill の executor.py は authhub.get_token("service") でトークン取得
```

---

## ステップ 2.7 — main.py スケルトン

ファイル: `backend/app/main.py`

```python
"""ZPCOS Backend — FastAPI entry point.

開発時:  cd backend && uv run python -m app.main
本番時:  PyInstaller .exe が直接起動（Tauri サイドカー経由）
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def resource_path(relative_path: str) -> Path:
    """PyInstaller --onefile ビルド後は sys._MEIPASS 内、開発時は app/ 基準。"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


app = FastAPI(
    title="ZPCOS Backend",
    version="0.1.0",
    description="Zero-Prompt Cross-model Orchestration System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18234, reload=False, workers=1)
```

---

## ステップ 2.8 — スケルトンファイル群

以下の各ファイルに docstring のみ記載:

`backend/app/gateway/__init__.py`:
```python
"""LiteLLM Router Gateway.
providers.json を読み込み litellm.Router を構築。
全呼び出しは router.acompletion() 経由。openrouter/ プレフィックス必須。
"""
```

`backend/app/auth/authhub.py`:
```python
"""AuthHub — 統合認証マネージャー.
POST   /api/auth/connect/{service}
GET    /api/auth/connections
DELETE /api/auth/disconnect/{service}
GET    /api/auth/token/{service}
"""
```

`backend/app/auth/token_store.py`:
```python
"""Token Store — ハイブリッド暗号化保存.
keyring → AES-256 鍵のみ
ファイル → %APPDATA%/zpcos/tokens/{service}.enc に AES-GCM 暗号化 JSON
"""
```

`backend/app/auth/google_oauth.py`:
```python
"""Google OAuth — InstalledAppFlow PKCE.
run_local_server(port=0) を asyncio.to_thread でスレッドオフロード。
"""
```

`backend/app/auth/openrouter_oauth.py`:
```python
"""OpenRouter OAuth — PKCE 認証.
ポート 3000 で一時 HTTP サーバー。全体を run_in_executor でスレッドオフロード。
"""
```

`backend/app/judge/__init__.py`:
```python
"""Cross-Model Judge Pipeline.
pipeline.py → segmenter.py → sampler.py → evaluator.py → improver.py
"""
```

`backend/app/orchestrator/__init__.py`:
```python
"""Task Orchestrator — ZPCOS の司令塔.
自然言語の指示を受け取り、Skill の選択・実行計画・連携を管理する。
orchestrator.py → planner.py → integrator.py
"""
```

`backend/app/state/__init__.py`:
```python
"""State Machine — AsyncMachine (python-transitions).
状態: draft → ai_executing → ai_completed → judging → judge_completed
      → human_review → approved/rejected → committed
aiosqlite で永続化。
"""
```

`backend/app/skills/__init__.py`:
```python
"""Skill Framework.
SKILL.json + executor.py の 2 ファイル構成。
SkillBase 抽象クラスと SkillRegistry。
"""
```

`backend/app/engine/__init__.py`:
```python
"""Skill Auto-Generation Engine.
LLM に SKILL.json + executor.py を生成させ、セキュリティバリデーション後に登録。
"""
```

---

## ステップ 2.9 — 認証コネクタ JSON

`backend/app/auth/connectors/google.json`:
```json
{
  "service": "google",
  "display_name": "Google アカウント",
  "auth_type": "oauth2_installed_app",
  "client_secrets_file": "client_secret.json",
  "scopes": [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
  ],
  "setup_instructions": "Google Cloud Console で「デスクトップアプリ」タイプの OAuth クライアント ID を作成し、client_secret.json をダウンロード。"
}
```

`backend/app/auth/connectors/openrouter.json`:
```json
{
  "service": "openrouter",
  "display_name": "OpenRouter",
  "auth_type": "oauth2_pkce",
  "authorize_url": "https://openrouter.ai/auth",
  "token_url": "https://openrouter.ai/api/v1/auth/keys",
  "callback_url": "http://localhost:3000/callback",
  "scopes": [],
  "params": {
    "limit": 5,
    "usage_limit_type": "monthly",
    "code_challenge_method": "S256"
  }
}
```

`backend/app/auth/connectors/_template.json`:
```json
{
  "service": "",
  "display_name": "",
  "auth_type": "oauth2_code | oauth2_pkce | oauth2_installed_app | api_key",
  "authorize_url": "",
  "token_url": "",
  "callback_url": "",
  "scopes": [],
  "params": {},
  "setup_instructions": ""
}
```

---

## ステップ 2.10 — providers.json

ファイル: `backend/app/gateway/providers.json`

```json
{
  "models": [
    {
      "model_name": "fast",
      "litellm_params": {
        "model": "openrouter/google/gemini-3-flash-preview",
        "api_key_env": "OPENROUTER_API_KEY"
      }
    },
    {
      "model_name": "think",
      "litellm_params": {
        "model": "openrouter/google/gemini-3.1-pro-preview",
        "api_key_env": "OPENROUTER_API_KEY"
      }
    },
    {
      "model_name": "quality",
      "litellm_params": {
        "model": "openrouter/anthropic/claude-sonnet-4.6",
        "api_key_env": "OPENROUTER_API_KEY"
      }
    },
    {
      "model_name": "free",
      "litellm_params": {
        "model": "openrouter/meta-llama/llama-4-maverick:free",
        "api_key_env": "OPENROUTER_API_KEY"
      }
    },
    {
      "model_name": "reason",
      "litellm_params": {
        "model": "openrouter/deepseek/deepseek-r1",
        "api_key_env": "OPENROUTER_API_KEY"
      }
    },
    {
      "model_name": "value",
      "litellm_params": {
        "model": "openrouter/deepseek/deepseek-v3.2",
        "api_key_env": "OPENROUTER_API_KEY"
      }
    }
  ],
  "router_settings": {
    "routing_strategy": "simple-shuffle",
    "num_retries": 3,
    "retry_after": 2,
    "allowed_fails": 3,
    "cooldown_time": 30,
    "cache_responses": false
  },
  "_note": "api_key_env は参照名。実際のキーは token_store 経由で取得し Router 初期化時に注入。"
}
```

---

## ステップ 2.11 — フロントエンド初期化

```powershell
cd frontend
pnpm create vite . --template react-ts
pnpm install
```

確認: `pnpm dev` → http://localhost:5173 で Vite 初期画面。Ctrl+C で停止。

---

## ステップ 2.12 — Tauri v2 初期化

```powershell
pnpm add -D @tauri-apps/cli@next
pnpm tauri init
```

対話入力: App name=ZPCOS, Window title=ZPCOS, Web assets=../dist,
Dev URL=http://localhost:5173, Dev cmd=pnpm dev, Build cmd=pnpm build

```powershell
cd src-tauri
cargo add tauri-plugin-shell
cd ..
```

---

## ステップ 2.13 — Tauri サイドカー設定

`frontend/src-tauri/tauri.conf.json`（マージ）:
```json
{
  "bundle": {
    "externalBin": ["binaries/zpcos-backend"]
  }
}
```

`frontend/src-tauri/capabilities/default.json`:
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-open",
    {
      "identifier": "shell:allow-execute",
      "allow": [
        {
          "name": "binaries/zpcos-backend",
          "sidecar": true,
          "args": [{ "validator": "\\S+" }]
        }
      ]
    }
  ]
}
```

---

## ステップ 2.14 — ビルドスクリプト

`backend/scripts/build_sidecar.ps1`:
```powershell
$ErrorActionPreference = "Stop"
$targetTriple = (rustc -Vv | Select-String "host:").Line.Split(" ")[1]
Write-Host "Target triple: $targetTriple" -ForegroundColor Cyan

Push-Location $PSScriptRoot/..
uv run pyinstaller --onefile --name zpcos-backend `
  --add-data "app/auth/connectors;app/auth/connectors" `
  --add-data "app/gateway/providers.json;app/gateway" `
  app/main.py
Pop-Location

$src = Join-Path $PSScriptRoot ".." "dist" "zpcos-backend.exe"
$dstDir = Join-Path $PSScriptRoot ".." ".." "frontend" "src-tauri" "binaries"
$dst = Join-Path $dstDir "zpcos-backend-${targetTriple}.exe"
if (!(Test-Path $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir }
Copy-Item $src $dst -Force
Write-Host "Sidecar: $dst ($([math]::Round((Get-Item $dst).Length/1MB,1)) MB)" -ForegroundColor Green
```

---

## ステップ 2.15 — 初回コミット

```powershell
cd zpcos
git add -A
git commit -m "feat: initialize repository structure (Section 2 v11.2)"
```

---

## ステップ 2.16 — 動作確認（7項目全て PASS で完了）

```powershell
# 1. ディレクトリ構造
tree zpcos /F | Select-String "(auth|gateway|judge|orchestrator|skills|engine|state|connectors)"

# 2. Git
git log --oneline

# 3. Python
cd backend
uv run python -c "
import fastapi, litellm, transitions, keyring, cryptography
from transitions.extensions.asyncio import AsyncMachine
print('Python imports: ALL OK')
"

# 4. バックエンド
uv run python -m app.main
# 別ターミナル: curl http://127.0.0.1:18234/api/health
# → {"status":"ok","version":"0.1.0"}

# 5. フロントエンド
cd ../frontend && pnpm dev
# → http://localhost:5173

# 6. JSON
cd ../backend
uv run python -c "
import json; from pathlib import Path
for f in ['app/auth/connectors/google.json','app/auth/connectors/openrouter.json','app/gateway/providers.json']:
    d = json.loads(Path(f).read_text(encoding='utf-8'))
    print(f'{f}: OK ({len(json.dumps(d))} bytes)')
"

# 7. resource_path
uv run python -c "
from app.main import resource_path
p = resource_path('gateway/providers.json')
print(f'path={p}, exists={p.exists()}')
"
```

全 7 項目 PASS でセクション 2 完了。コミット後、セクション 3 に進む。
