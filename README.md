# Zero-Employee Orchestrator

<p align="center">
  <img src="assets/logo.svg" alt="Zero-Employee Orchestrator" width="640">
</p>

```
    ███████╗███████╗ ██████╗
    ╚══███╔╝██╔════╝██╔═══██╗
      ███╔╝ █████╗  ██║   ██║
     ███╔╝  ██╔══╝  ██║   ██║
    ███████╗███████╗╚██████╔╝
    ╚══════╝╚══════╝ ╚═════╝
```

> **v0.1 — AI Orchestration Platform — Design · Execute · Verify · Improve**
>
> 自然言語で業務を定義し、複数 AI を役割分担させ、人間の承認と監査可能性を前提に業務を実行・再計画・改善できる AI オーケストレーション基盤。

Define business workflows in natural language, orchestrate multiple AI agents with role-based delegation, and execute tasks with human approval and full auditability.

用自然语言定义业务流程，让多个AI按角色分工协作，在人类审批和可审计的前提下执行、重新规划和改进业务。

---

## 日本語 | [English](#english) | [中文](#中文)

### これは何？

Zero-Employee Orchestrator は、単なる AI チャットや単発自動化ツールではなく、**AI を「組織」として運用するための基盤**です。

- **AI を組織として扱う** — 単一エージェントではなく、計画・実行・検証・改善を役割分担したチーム構造
- **人間の最終承認を外さない** — 投稿・送信・課金・削除・権限変更は必ず承認可能
- **ブラックボックスを減らす** — 誰が何をなぜどのモデルで実行したかを可視化
- **最新性は拡張で担保** — 本体は安定性重視、業務差分は Skill / Plugin / Extension で吸収
- **汎用業務基盤** — YouTube は代表検証テーマ。本質は会社業務全体の実行基盤

### 主な機能

| 機能 | 説明 |
|------|------|
| **Design Interview** | 自然言語で業務依頼を受け、要件を深掘り |
| **Spec / Plan / Tasks** | 中間成果物として構造化保存、再利用・監査・差し戻し可能 |
| **Task Orchestrator** | DAG ベースの計画生成、コスト見積り、品質モード切替 |
| **Judge Layer** | ルールベース一次判定 + Cross-Model 高精度判定 |
| **Self-Healing / Re-Propose** | 障害時の自動再計画・再提案 |
| **Skill / Plugin / Extension** | 3層の拡張体系で業務機能を追加（完全 CRUD 管理対応） |
| **自然言語スキル生成** | 自然言語でスキルを説明するだけで AI が自動生成（安全性チェック付き） |
| **システム保護** | システム必須スキルは削除・無効化不可（6 種のビルトインスキルを保護） |
| **分身AI / 秘書AI** | ユーザーの判断基準を学習する分身AI、AI組織との橋渡しをする秘書AI（Plugin） |
| **チャットツール連携** | Discord / Slack / LINE から AI 組織に指示・対話（Plugin） |
| **コミュニティプラグイン** | GitHub からプラグインを検索・インストール。ユーザー間で共有・公開可能 |
| **外部ツール連携** | gws / gh / AWS CLI 等の CLI ツール、MCP、REST API、GraphQL に対応 |
| **承認フロー** | 危険操作は必ず人間承認を要求 |
| **監査ログ** | 全重要操作を追跡可能 |

### インストール（v0.1）

#### GUI 版（デスクトップアプリ・初めての方はこちら）

[Releases ページ](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) からインストーラーをダウンロードして実行してください。

> **パソコンが苦手な方へ**: Releases ページを開いたら、下にスクロールして「Assets」の中からお使いの OS に合ったファイルをクリックするだけです。

| OS | ファイル名 | 説明 |
|----|-----------|------|
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_ja-JP.msi` | 日本語 Windows インストーラー。ダブルクリックで実行 |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_en-US.msi` | English Windows installer |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_zh-CN.msi` | 中文 Windows 安装程序 |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64-setup.exe` | Windows NSIS インストーラー（.msi が動かない場合） |
| **macOS** | `Zero-Employee-Orchestrator_0.1.0_universal.dmg` | macOS 用（Intel / Apple Silicon 両対応）。開いて Applications にドラッグ |
| **macOS** | `Zero-Employee-Orchestrator_0.1.0_aarch64.dmg` | macOS Apple Silicon 専用 |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_amd64.AppImage` | そのまま実行可能（インストール不要） |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_amd64.deb` | Debian/Ubuntu 用パッケージ |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_x86_64.rpm` | Fedora/RHEL 用パッケージ |
| **ソースコード** | `Source code (zip)` / `Source code (tar.gz)` | ソースからビルドする場合 |

> **最新版**: [こちら](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/latest) からダウンロードできます。

#### CLI / TUI 版（エンジニア向け）

```bash
pip install zero-employee-orchestrator
```

または [uv](https://docs.astral.sh/uv/) を使用:

```bash
uv pip install zero-employee-orchestrator
```

### クイックスタート（ソースから起動）

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # 依存関係の自動インストール・環境構築
./start.sh   # バックエンド + フロントエンドを起動

# LLM API キーを設定（以下のいずれかの方法）
# 方法 1: アプリの「設定」画面から入力（推奨）
# 方法 2: CLI から設定
zero-employee config set GEMINI_API_KEY
# 方法 3: .env を直接編集
```

起動後、ブラウザで **http://localhost:5173** にアクセスしてください。

> `setup.sh` は Python・Node.js・pnpm が未インストールの場合、OS のパッケージマネージャーを使って自動でインストールを試みます。

> 停止するには `Ctrl+C` を押します。

| サービス | URL |
|---------|-----|
| フロントエンド | http://localhost:5173 |
| バックエンド API | http://localhost:18234 |
| ヘルスチェック | http://localhost:18234/healthz |
| API ドキュメント (JSON) | http://localhost:18234/api/v1/openapi.json |

### LLM API キーの設定

AI によるタスク実行機能を使うには、LLM プロバイダーの API 接続が必要です。
**API キーは 3 通りの方法で設定できます**: アプリ設定画面 / CLI コマンド / .env ファイル

> **⚠️ サブスクリプションと API アクセスは別物です**
>
> ChatGPT Plus・Gemini Advanced・Claude Pro などのサブスクリプションは Web アプリ向けのサービスです。**プログラムから直接呼び出すことはできません。** API アクセスは別途取得・課金が必要です。

#### 無料で始める方法

| 方法 | 説明 | 安定性 |
|------|------|--------|
| **Google Gemini（無料枠）** ⭐ | Google AI Studio でキーを取得。無料枠あり・クレジットカード不要 | 高い |
| **Ollama（ローカル LLM）** | PC 上で LLM を実行。API キー不要・完全オフライン・無制限 | 最高 |
| **サブスクリプションモード** | g4f 経由で無料利用。API キー不要 | 低い（試用向け） |

#### API キーの設定方法（3 通り）

**方法 1: アプリの設定画面から（推奨）**

アプリを起動し、サイドバーの「設定」画面 → 「LLM API キー設定」から各プロバイダーのキーを入力して保存します。.env ファイルの編集は不要です。

**方法 2: CLI コマンドから**

```bash
# API キーを安全に入力（パスワードのようにエコーなし）
zero-employee config set GEMINI_API_KEY
zero-employee config set DEFAULT_EXECUTION_MODE free

# 現在の設定を確認
zero-employee config list

# 設定可能なキーの一覧
zero-employee config keys
```

**方法 3: .env ファイルを直接編集**

<details>
<summary>無料 API キーの取得手順</summary>

**Google Gemini 無料 API キーの取得:**
1. [Google AI Studio](https://aistudio.google.com/) にアクセス
2. 「Get API key」 → 「Create API key」 でキーを生成
3. `apps/api/.env` に追記:
   ```env
   GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxxxx
   DEFAULT_EXECUTION_MODE=free
   ```

**Ollama（ローカルモデル）の設定:**
1. [ollama.com](https://ollama.com/) からインストール
2. ターミナルでモデルをダウンロード: `ollama pull llama3.2`
3. `apps/api/.env` に追記:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   DEFAULT_EXECUTION_MODE=free
   ```

</details>

<details>
<summary>有料 API キーを使う場合</summary>

`apps/api/.env` に以下のいずれかを設定してください（または設定画面・CLI から入力）:

```env
# OpenRouter（複数モデル対応 — 推奨）
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Google Gemini
GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxx
```

</details>

### 9層アーキテクチャ

```
┌──────────────────────────────────────────────────────────┐
│  1. User Layer          自然言語入力から AI 組織を起動     │
├──────────────────────────────────────────────────────────┤
│  2. Design Interview    要件を深掘りする質問生成と回答蓄積 │
├──────────────────────────────────────────────────────────┤
│  3. Task Orchestrator   Plan/DAG 生成、Skill 割当、       │
│                         コスト見積り                      │
├──────────────────────────────────────────────────────────┤
│  4. Skill Layer         単一目的の専門 Skill              │
│                         + Local Context Skill            │
├──────────────────────────────────────────────────────────┤
│  5. Judge Layer         Two-stage Detection               │
│                         + Cross-Model Verification        │
├──────────────────────────────────────────────────────────┤
│  6. Re-Propose Layer    差し戻し時の再提案                 │
│                         + 動的 DAG 再構築                 │
├──────────────────────────────────────────────────────────┤
│  7. State & Memory      永続的な実行環境                   │
│                         Experience Memory                │
│                         Failure Taxonomy                  │
├──────────────────────────────────────────────────────────┤
│  8. Provider Interface  LLM ゲートウェイ (LiteLLM)        │
├──────────────────────────────────────────────────────────┤
│  9. Skill Registry      Skill/Plugin の公開・検索          │
│                         ・インストール                     │
└──────────────────────────────────────────────────────────┘
```

### 技術スタック

| レイヤー | 技術 |
|---------|------|
| デスクトップ | Tauri v2 (Rust) |
| フロントエンド | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| バックエンド | Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic |
| LLM接続 | LiteLLM Gateway (OpenRouter, 複数Provider対応) |
| 認証 | OAuth PKCE, ローカル暗号化ストア |
| データベース | SQLite (開発), PostgreSQL (本番推奨) |

### ディレクトリ構成

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                    # FastAPI バックエンド
│   │   ├── app/
│   │   │   ├── core/           # 設定・DB・セキュリティ・i18n
│   │   │   ├── api/
│   │   │   │   ├── routes/     # REST API エンドポイント（20 ルート）
│   │   │   │   ├── ws/         # WebSocket
│   │   │   │   └── deps/       # 依存性注入
│   │   │   ├── models/         # SQLAlchemy ORM モデル（18 ファイル）
│   │   │   ├── schemas/        # Pydantic DTO（16 ファイル）
│   │   │   ├── services/       # ビジネスロジック（9 サービス）
│   │   │   ├── repositories/   # DB 入出力抽象化
│   │   │   ├── orchestration/  # DAG・Judge・状態機械・Memory（18 モジュール）
│   │   │   ├── heartbeat/      # 定期実行スケジューラ
│   │   │   ├── providers/      # LLM Gateway・Ollama・g4f・RAG
│   │   │   ├── tools/          # 外部ツール接続（MCP/Webhook/API/CLI）
│   │   │   ├── policies/       # 承認ゲート・自律実行境界
│   │   │   ├── security/       # Secret Manager・Sanitizer・IAM
│   │   │   ├── integrations/   # Sentry・MCP Server・外部スキル
│   │   │   ├── audit/          # 監査ログ
│   │   │   └── tests/          # テスト
│   │   ├── alembic/            # DB マイグレーション
│   │   └── model_catalog.json  # LLM モデルカタログ（動的管理）
│   ├── desktop/                # Tauri v2 デスクトップアプリ
│   │   ├── src-tauri/          # Rust バックエンド
│   │   └── ui/src/             # React フロントエンド
│   │       ├── pages/          # 21 画面コンポーネント
│   │       ├── features/       # 機能別モジュール
│   │       ├── shared/         # 共通 API・型・hooks・UI
│   │       └── app/            # ルーティング・エントリ
│   ├── edge/                   # Cloudflare Workers
│   │   ├── proxy/              # 方式A: リバースプロキシ
│   │   └── full/               # 方式B: Hono + D1 完全移植
│   └── worker/                 # バックグラウンドワーカー
│       ├── runners/            # タスク・Heartbeat 実行
│       ├── executors/          # LLM・サンドボックス実行
│       ├── sandbox/            # 隔離実行環境（Local/Docker/Workers）
│       └── dispatchers/        # イベント配信
├── skills/
│   ├── builtin/                # 組み込み Skill（6 個・システム保護）
│   └── templates/              # Skill テンプレート
├── plugins/                    # Plugin マニフェスト（8 Plugin）
│   ├── ai-avatar/              # 分身AI
│   ├── ai-secretary/           # 秘書AI
│   ├── discord-bot/            # Discord Bot
│   ├── slack-bot/              # Slack Bot
│   ├── line-bot/               # LINE Bot
│   ├── youtube/                # YouTube 運用
│   ├── research/               # リサーチ
│   └── backoffice/             # バックオフィス
├── extensions/                 # Extension マニフェスト（4 Extension）
│   ├── oauth/                  # OAuth 認証
│   ├── mcp/                    # MCP 接続
│   ├── notifications/          # 通知
│   └── obsidian/               # Obsidian 連携
├── packages/                   # 共有 NPM パッケージ
├── docs/                       # 利用者向けドキュメント
│   └── dev/                    # 開発者向けドキュメント
├── examples/                   # サンプル・例
├── assets/                     # ロゴ・画像
├── scripts/                    # 開発・運用スクリプト
├── Dockerfile                  # Rootless コンテナ
├── docker-compose.yml          # 全サービス一括起動
├── setup.sh                    # セットアップスクリプト
├── start.sh                    # 起動スクリプト
└── README.md
```

### 権限モデル

| ロール | 権限 |
|--------|------|
| Owner | 全権限 |
| Admin | 組織設定、一部承認、監査ログ |
| User | 業務依頼、計画確認、成果物確認 |
| Auditor | 実行履歴・監査ログの閲覧のみ |
| Developer | Skill/Plugin/Extension の開発 |

### 自律実行の境界

| 自律実行可能 | 承認必須 |
|-------------|---------|
| 調査・分析 | 公開・投稿 |
| 下書き作成 | 課金・削除 |
| 情報整理 | 権限変更・外部送信 |

### Cloudflare Workers デプロイ / Deploy

Workers 上での実行に対応しています。2つの方式から選択できます:

| 方式 / Method | ディレクトリ / Directory | 概要 / Overview |
|--------------|------------------------|----------------|
| **A: Proxy** | `apps/edge/proxy/` | 既存 FastAPI の前段にリバースプロキシ配置 |
| **B: Full Workers** | `apps/edge/full/` | 主要 API を Hono + D1 でエッジ上に完全再実装 |

```bash
# Method A: Proxy
cd apps/edge/proxy && npm install && npm run dev

# Method B: Full Workers
cd apps/edge/full && npm install && npm run db:init && npm run dev
```

詳細 / Details: [apps/edge/README.md](apps/edge/README.md)

## 本番環境

<details>
<summary>本番環境での運用

### PostgreSQL

```env
# apps/api/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zero_employee_orchestrator
```

```bash
cd apps/api && source .venv/bin/activate
pip install asyncpg
```

### セキュリティ

```env
SECRET_KEY=<ランダムな文字列を生成して設定>
DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

</details>

---

## ライセンス

プライベートプロジェクト

## 関連文書

**利用者向け（`docs/`）:**
- [`docs/ABOUT.md`](docs/ABOUT.md) — このシステムのメリット・従来システムとの違い
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — 初心者向けユーザーガイド
- [`docs/OVERVIEW.md`](docs/OVERVIEW.md) — 思想・機能・構造の総合ガイド
- [`docs/FEATURES.md`](docs/FEATURES.md) — 実装済み機能一覧
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — 変更履歴

**開発者向け（`docs/dev/`）:**
- [`docs/dev/DESIGN.md`](docs/dev/DESIGN.md) — 実装設計書（DB・API・画面・状態遷移）
- [`docs/dev/MASTER_GUIDE.md`](docs/dev/MASTER_GUIDE.md) — 実装運用ガイド（進め方と判断基準）
- [`docs/dev/BUILD_GUIDE.md`](docs/dev/BUILD_GUIDE.md) — ゼロからの構築手順

### トラブルシューティング

<details>
<summary>よくある問題と解決法</summary>

**`./setup.sh` が実行できない**

```bash
chmod +x setup.sh start.sh
./setup.sh
```

**ポートが使用中**

```bash
lsof -i :18234   # バックエンド
lsof -i :5173    # フロントエンド
kill <PID>
./start.sh
```

**Python の仮想環境エラー**

```bash
cd apps/api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

**pnpm install が失敗する**

```bash
cd apps/desktop/ui
rm -rf node_modules
pnpm install
```

**データベースをリセットしたい**

```bash
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

</details>

---

## English

### What is this?

Zero-Employee Orchestrator is not just another AI chatbot or one-off automation tool — it is a **platform for running AI as an organization**.

- **Treat AI as an organization** — not a single agent, but a team structure with planning, execution, verification, and improvement roles
- **Human approval is always required** — posting, sending, billing, deletion, and permission changes are always approvable
- **Reduce black boxes** — visualize who did what, why, and with which model
- **Extensibility for freshness** — the core prioritizes stability; business-specific differences are absorbed by Skills / Plugins / Extensions
- **General-purpose business platform** — YouTube is a representative demo theme; the essence is an execution platform for all company operations

### Key Features

| Feature | Description |
|---------|-------------|
| **Design Interview** | Receive business requests in natural language and deepen requirements |
| **Spec / Plan / Tasks** | Structured storage as intermediate artifacts; reusable, auditable, returnable |
| **Task Orchestrator** | DAG-based plan generation, cost estimation, quality mode switching |
| **Judge Layer** | Rule-based primary judgment + Cross-Model high-precision judgment |
| **Self-Healing / Re-Propose** | Automatic re-planning and re-proposal on failure |
| **Skill / Plugin / Extension** | 3-layer extension system with full CRUD management |
| **Natural Language Skill Generation** | Describe skills in natural language and AI auto-generates them (with safety checks) |
| **System Protection** | System-essential skills cannot be deleted or disabled (6 built-in skills protected) |
| **AI Avatar / AI Secretary** | Avatar AI learns your judgment criteria; Secretary AI bridges you and the AI org (Plugin) |
| **Chat Tool Integration** | Command your AI org from Discord / Slack / LINE (Plugin) |
| **Community Plugins** | Search & install plugins from GitHub. Users can share & publish plugins |
| **External Tool Integration** | Supports gws / gh / AWS CLI, MCP, REST API, GraphQL |
| **Approval Flow** | Dangerous operations always require human approval |
| **Audit Log** | All important operations are traceable |

### Install (v0.1)

#### GUI (Desktop App — Start Here)

Download the installer from the [Releases page](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases).

> **Non-technical users**: Go to the Releases page, scroll down to "Assets", and click the file that matches your operating system.

| OS | File | Description |
|----|------|-------------|
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_en-US.msi` | English Windows installer. Double-click to run |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_ja-JP.msi` | Japanese Windows installer |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_zh-CN.msi` | Chinese Windows installer |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64-setup.exe` | Windows NSIS installer (if .msi doesn't work) |
| **macOS** | `Zero-Employee-Orchestrator_0.1.0_universal.dmg` | For macOS (Intel / Apple Silicon). Open and drag to Applications |
| **macOS** | `Zero-Employee-Orchestrator_0.1.0_aarch64.dmg` | macOS Apple Silicon only |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_amd64.AppImage` | Runs directly (no install needed) |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_amd64.deb` | Debian/Ubuntu package |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_x86_64.rpm` | Fedora/RHEL package |
| **Source** | `Source code (zip)` / `Source code (tar.gz)` | Build from source |

> **Latest**: Download from [here](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/latest).

#### CLI / TUI (For Engineers)

```bash
pip install zero-employee-orchestrator
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install zero-employee-orchestrator
```

### Quick Start (From Source)

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # Auto-install dependencies & configure environment
./start.sh   # Start backend + frontend

# Configure LLM API keys (choose one method):
# Method 1: From the Settings page in the app (recommended)
# Method 2: From the CLI
zero-employee config set GEMINI_API_KEY
# Method 3: Edit .env file directly
```

After startup, open **http://localhost:5173** in your browser.

> `setup.sh` will attempt to automatically install Python, Node.js, and pnpm using your OS package manager if they are not already installed.

> Press `Ctrl+C` to stop.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:18234 |
| Health Check | http://localhost:18234/healthz |
| API Docs (JSON) | http://localhost:18234/api/v1/openapi.json |

### LLM API Key Configuration

To use AI task execution, you need API access to an LLM provider.
**API keys can be configured in 3 ways**: from the app settings screen / CLI command / .env file

> **⚠️ Subscriptions and API access are separate**
>
> Subscriptions like ChatGPT Plus, Gemini Advanced, and Claude Pro are services for web app users. **They cannot be called directly from a program.** API access requires separate registration and billing.

#### Getting Started for Free

| Method | Description | Stability |
|--------|-------------|-----------|
| **Google Gemini (free tier)** ⭐ | Get a key from Google AI Studio. Free tier available, no credit card required | High |
| **Ollama (local LLM)** | Run LLM on your PC. No API key required, fully offline, unlimited | Highest |
| **Subscription mode** | Free use via g4f. No API key required | Low (for trial) |

#### Setting API Keys (3 Methods)

**Method 1: From the app settings screen (recommended)**

Launch the app, go to the "Settings" screen in the sidebar → "LLM API Key Settings" to enter and save each provider's key. No need to edit .env files.

**Method 2: From the CLI**

```bash
# Securely input API keys (no echo, like a password)
zero-employee config set GEMINI_API_KEY
zero-employee config set DEFAULT_EXECUTION_MODE free

# Check current settings
zero-employee config list

# List configurable keys
zero-employee config keys
```

**Method 3: Edit .env file directly**

<details>
<summary>How to get free API keys</summary>

**Getting a Google Gemini free API key:**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API key" → "Create API key" to generate a key
3. Add to `apps/api/.env`:
   ```env
   GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxxxx
   DEFAULT_EXECUTION_MODE=free
   ```

**Setting up Ollama (local model):**
1. Install from [ollama.com](https://ollama.com/)
2. Download a model in terminal: `ollama pull llama3.2`
3. Add to `apps/api/.env`:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   DEFAULT_EXECUTION_MODE=free
   ```

</details>

<details>
<summary>Using paid API keys</summary>

Set any of the following in `apps/api/.env` (or enter via the settings screen or CLI):

```env
# OpenRouter (multi-model support — recommended)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Google Gemini
GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxx
```

</details>

### 9-Layer Architecture

1. **User Layer** — Activate AI organization from natural language input
2. **Design Interview** — Generate deepening questions and accumulate answers
3. **Task Orchestrator** — Plan/DAG generation, Skill assignment, cost estimation
4. **Skill Layer** — Single-purpose specialist Skills + Local Context Skills
5. **Judge Layer** — Two-stage Detection + Cross-Model Verification
6. **Re-Propose Layer** — Re-proposal on rejection + dynamic DAG reconstruction
7. **State & Memory** — Persistent execution environment, Experience Memory, Failure Taxonomy
8. **Provider Interface** — LLM Gateway (LiteLLM)
9. **Skill Registry** — Publish, search, and install Skills/Plugins

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop | Tauri v2 (Rust) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic |
| LLM Gateway | LiteLLM (OpenRouter, multi-provider) |
| Auth | OAuth PKCE, local encrypted store |
| Database | SQLite (dev), PostgreSQL (production) |

### Directory Structure

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                    # FastAPI Backend
│   │   ├── app/
│   │   │   ├── core/           # Config, DB, Security, i18n
│   │   │   ├── api/
│   │   │   │   ├── routes/     # REST API Endpoints (20 routes)
│   │   │   │   ├── ws/         # WebSocket
│   │   │   │   └── deps/       # Dependency Injection
│   │   │   ├── models/         # SQLAlchemy ORM Models (18 files)
│   │   │   ├── schemas/        # Pydantic DTOs (16 files)
│   │   │   ├── services/       # Business Logic (9 services)
│   │   │   ├── repositories/   # DB Abstraction Layer
│   │   │   ├── orchestration/  # DAG, Judge, State Machine, Memory (18 modules)
│   │   │   ├── heartbeat/      # Scheduled Execution
│   │   │   ├── providers/      # LLM Gateway, Ollama, g4f, RAG
│   │   │   ├── tools/          # External Tool Connectors (MCP/Webhook/API/CLI)
│   │   │   ├── policies/       # Approval Gates, Autonomy Boundaries
│   │   │   ├── security/       # Secret Manager, Sanitizer, IAM
│   │   │   ├── integrations/   # Sentry, MCP Server, External Skills
│   │   │   ├── audit/          # Audit Logging
│   │   │   └── tests/          # Tests
│   │   ├── alembic/            # DB Migrations
│   │   └── model_catalog.json  # LLM Model Catalog (dynamic management)
│   ├── desktop/                # Tauri v2 Desktop App
│   │   ├── src-tauri/          # Rust Backend
│   │   └── ui/src/             # React Frontend
│   │       ├── pages/          # 21 Page Components
│   │       ├── features/       # Feature Modules
│   │       ├── shared/         # Shared API, Types, Hooks, UI
│   │       └── app/            # Routing & Entry
│   ├── edge/                   # Cloudflare Workers
│   │   ├── proxy/              # Method A: Reverse Proxy
│   │   └── full/               # Method B: Hono + D1 Full Migration
│   └── worker/                 # Background Worker
│       ├── runners/            # Task & Heartbeat Runners
│       ├── executors/          # LLM & Sandbox Executors
│       ├── sandbox/            # Isolated Execution (Local/Docker/Workers)
│       └── dispatchers/        # Event Dispatching
├── skills/
│   ├── builtin/                # Built-in Skills (6, system-protected)
│   └── templates/              # Skill Templates
├── plugins/                    # Plugin Manifests (8 Plugins)
│   ├── ai-avatar/              # Avatar AI
│   ├── ai-secretary/           # Secretary AI
│   ├── discord-bot/            # Discord Bot
│   ├── slack-bot/              # Slack Bot
│   ├── line-bot/               # LINE Bot
│   ├── youtube/                # YouTube Operations
│   ├── research/               # Research
│   └── backoffice/             # Back Office
├── extensions/                 # Extension Manifests (4 Extensions)
│   ├── oauth/                  # OAuth Authentication
│   ├── mcp/                    # MCP Connection
│   ├── notifications/          # Notifications
│   └── obsidian/               # Obsidian Integration
├── packages/                   # Shared NPM Packages
├── docs/                       # Documentation
├── assets/                     # Logo & Images
├── scripts/                    # Dev & Deploy Scripts
├── Dockerfile                  # Rootless Container
├── docker-compose.yml          # Full Stack Orchestration
├── setup.sh                    # Setup Script
├── start.sh                    # Start Script
└── README.md
```

### Permission Model

| Role | Permissions |
|------|-------------|
| Owner | Full access |
| Admin | Organization settings, partial approvals, audit logs |
| User | Business requests, plan review, artifact review |
| Auditor | View-only access to execution history and audit logs |
| Developer | Develop Skills/Plugins/Extensions |

### Autonomous Execution Boundaries

| Can Execute Autonomously | Requires Approval |
|--------------------------|-------------------|
| Research & analysis | Publishing & posting |
| Draft creation | Billing & deletion |
| Information organization | Permission changes & external transmission |

### Cloudflare Workers Deploy

Execution on Workers is supported. Choose from two methods:

| Method | Directory | Overview |
|--------|-----------|---------|
| **A: Proxy** | `apps/edge/proxy/` | Place a reverse proxy in front of the existing FastAPI |
| **B: Full Workers** | `apps/edge/full/` | Fully re-implement key APIs on the edge with Hono + D1 |

```bash
# Method A: Proxy
cd apps/edge/proxy && npm install && npm run dev

# Method B: Full Workers
cd apps/edge/full && npm install && npm run db:init && npm run dev
```

Details: [apps/edge/README.md](apps/edge/README.md)

### Production Environment

<details>
<summary>Running in production

### PostgreSQL

```env
# apps/api/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zero_employee_orchestrator
```

```bash
cd apps/api && source .venv/bin/activate
pip install asyncpg
```

### Security

```env
SECRET_KEY=<generate and set a random string>
DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

</details>

### License

Private project

### Related Documents

**For Users (`docs/`):**
- [`docs/ABOUT.md`](docs/ABOUT.md) — Benefits of this system and differences from conventional systems
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — Beginner's user guide
- [`docs/OVERVIEW.md`](docs/OVERVIEW.md) — Comprehensive guide (philosophy, features, architecture)
- [`docs/FEATURES.md`](docs/FEATURES.md) — Full feature list
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — Changelog

**For Developers (`docs/dev/`):**
- [`docs/dev/DESIGN.md`](docs/dev/DESIGN.md) — Implementation design document (DB, API, screens, state transitions)
- [`docs/dev/MASTER_GUIDE.md`](docs/dev/MASTER_GUIDE.md) — Implementation & operations guide (process and decision criteria)
- [`docs/dev/BUILD_GUIDE.md`](docs/dev/BUILD_GUIDE.md) — Step-by-step build guide

### Troubleshooting

<details>
<summary>Common issues and solutions</summary>

**`./setup.sh` won't execute**

```bash
chmod +x setup.sh start.sh
./setup.sh
```

**Port already in use**

```bash
lsof -i :18234   # Backend
lsof -i :5173    # Frontend
kill <PID>
./start.sh
```

**Python virtual environment error**

```bash
cd apps/api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

**pnpm install fails**

```bash
cd apps/desktop/ui
rm -rf node_modules
pnpm install
```

**Database reset**

```bash
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

</details>

---

## 中文

### 这是什么？

Zero-Employee Orchestrator 不是简单的AI聊天或一次性自动化工具，而是一个**将AI作为组织来运营的平台**。

- **将AI视为组织** — 不是单一代理，而是具有规划、执行、验证和改进角色的团队结构
- **始终保留人类最终审批** — 发布、发送、计费、删除、权限变更必须可审批
- **减少黑箱** — 可视化谁在何时用哪个模型做了什么以及为什么
- **通过扩展保持时效性** — 核心注重稳定性，业务差异由 Skill / Plugin / Extension 吸收
- **通用业务平台** — YouTube 是代表性验证主题，本质是整个公司业务的执行平台

### 主要功能

| 功能 | 说明 |
|------|------|
| **Design Interview** | 以自然语言接收业务需求，深入挖掘需求 |
| **Spec / Plan / Tasks** | 作为中间产物结构化保存，可复用、可审计、可退回 |
| **Task Orchestrator** | 基于DAG的计划生成、成本估算、质量模式切换 |
| **Judge Layer** | 基于规则的一次判定 + Cross-Model 高精度判定 |
| **Self-Healing / Re-Propose** | 故障时自动重新规划和再提案 |
| **Skill / Plugin / Extension** | 3层扩展体系添加业务功能（完整 CRUD 管理） |
| **自然语言技能生成** | 用自然语言描述技能，AI自动生成（带安全性检查） |
| **系统保护** | 系统必需技能不可删除或禁用（保护6个内置技能） |
| **分身AI / 秘书AI** | 学习用户判断标准的分身AI、连接用户与AI组织的秘书AI（插件） |
| **聊天工具集成** | 通过 Discord / Slack / LINE 向AI组织发送指令（插件） |
| **社区插件** | 从 GitHub 搜索安装插件。用户可分享和发布插件 |
| **外部工具集成** | 支持 gws / gh / AWS CLI、MCP、REST API、GraphQL |
| **审批流程** | 危险操作必须获得人类审批 |
| **审计日志** | 所有重要操作可追溯 |

### 安装 (v0.1)

#### GUI版（桌面应用 —— 从这里开始）

从 [Releases 页面](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) 下载安装程序。

> **非技术用户**：打开 Releases 页面，向下滚动到 "Assets"，点击与您操作系统匹配的文件即可。

| 操作系统 | 文件名 | 说明 |
|---------|--------|------|
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_zh-CN.msi` | 中文 Windows 安装程序。双击运行 |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_en-US.msi` | English Windows installer |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64_ja-JP.msi` | 日本語 Windows インストーラー |
| **Windows** | `Zero-Employee-Orchestrator_0.1.0_x64-setup.exe` | Windows NSIS 安装程序（.msi 无法运行时使用） |
| **macOS** | `Zero-Employee-Orchestrator_0.1.0_universal.dmg` | macOS 用（Intel / Apple Silicon 通用）。打开后拖到 Applications |
| **macOS** | `Zero-Employee-Orchestrator_0.1.0_aarch64.dmg` | macOS Apple Silicon 专用 |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_amd64.AppImage` | 直接运行（无需安装） |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_amd64.deb` | Debian/Ubuntu 软件包 |
| **Linux** | `Zero-Employee-Orchestrator_0.1.0_x86_64.rpm` | Fedora/RHEL 软件包 |
| **源代码** | `Source code (zip)` / `Source code (tar.gz)` | 从源代码构建 |

> **最新版本**：从[这里](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/latest)下载。

#### CLI / TUI版（面向工程师）

```bash
pip install zero-employee-orchestrator
```

或使用 [uv](https://docs.astral.sh/uv/):

```bash
uv pip install zero-employee-orchestrator
```

### 快速开始（从源码启动）

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # 自动安装依赖并配置环境
./start.sh   # 启动后端 + 前端

# 配置 LLM API 密钥（选择以下任一方法）：
# 方法 1：从应用的"设置"页面输入（推荐）
# 方法 2：通过 CLI 配置
zero-employee config set GEMINI_API_KEY
# 方法 3：直接编辑 .env 文件
```

启动后，在浏览器中打开 **http://localhost:5173**。

> `setup.sh` 如果未安装 Python、Node.js 或 pnpm，将尝试使用操作系统的包管理器自动安装。

> 按 `Ctrl+C` 停止。

| 服务 | URL |
|------|-----|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:18234 |
| 健康检查 | http://localhost:18234/healthz |
| API 文档 (JSON) | http://localhost:18234/api/v1/openapi.json |

### LLM API 密钥配置

使用AI任务执行功能需要连接 LLM 提供商的 API。
**API 密钥可通过 3 种方式配置**：从应用设置页面 / CLI 命令 / .env 文件

> **⚠️ 订阅服务与 API 访问是两回事**
>
> ChatGPT Plus、Gemini Advanced、Claude Pro 等订阅服务是面向 Web 应用用户的服务。**无法从程序直接调用。** API 访问需要单独申请和付费。

#### 免费开始使用

| 方法 | 说明 | 稳定性 |
|------|------|--------|
| **Google Gemini（免费额度）** ⭐ | 从 Google AI Studio 获取密钥。有免费额度，无需信用卡 | 高 |
| **Ollama（本地 LLM）** | 在 PC 上运行 LLM。无需 API 密钥，完全离线，无限制 | 最高 |
| **订阅模式** | 通过 g4f 免费使用。无需 API 密钥 | 低（适合试用） |

#### API 密钥配置方法（3 种）

**方法 1：从应用设置页面（推荐）**

启动应用，进入侧边栏"设置"页面 → "LLM API 密钥设置"，输入并保存各提供商的密钥。无需编辑 .env 文件。

**方法 2：通过 CLI 命令**

```bash
# 安全输入 API 密钥（无回显，类似密码）
zero-employee config set GEMINI_API_KEY
zero-employee config set DEFAULT_EXECUTION_MODE free

# 查看当前设置
zero-employee config list

# 查看可配置的密钥列表
zero-employee config keys
```

**方法 3：直接编辑 .env 文件**

<details>
<summary>如何获取免费 API 密钥</summary>

**获取 Google Gemini 免费 API 密钥：**
1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 点击 "Get API key" → "Create API key" 生成密钥
3. 添加到 `apps/api/.env`：
   ```env
   GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxxxx
   DEFAULT_EXECUTION_MODE=free
   ```

**配置 Ollama（本地模型）：**
1. 从 [ollama.com](https://ollama.com/) 安装
2. 在终端下载模型：`ollama pull llama3.2`
3. 添加到 `apps/api/.env`：
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   DEFAULT_EXECUTION_MODE=free
   ```

</details>

<details>
<summary>使用付费 API 密钥</summary>

在 `apps/api/.env` 中设置以下任一内容（也可通过设置页面或 CLI 输入）：

```env
# OpenRouter（支持多模型 — 推荐）
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Google Gemini
GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxx
```

</details>

### 9层架构

1. **User Layer** — 从自然语言输入启动AI组织
2. **Design Interview** — 生成深入提问并积累回答
3. **Task Orchestrator** — Plan/DAG 生成、Skill 分配、成本估算
4. **Skill Layer** — 单一目的的专业 Skill + 本地上下文 Skill
5. **Judge Layer** — 两阶段检测 + Cross-Model 验证
6. **Re-Propose Layer** — 退回时的再提案 + 动态 DAG 重构
7. **State & Memory** — 持久化执行环境、经验记忆、故障分类
8. **Provider Interface** — LLM 网关 (LiteLLM)
9. **Skill Registry** — Skill/Plugin 的发布、搜索、安装

### 目录结构

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                    # FastAPI 后端
│   │   ├── app/
│   │   │   ├── core/           # 配置、数据库、安全、国际化
│   │   │   ├── api/
│   │   │   │   ├── routes/     # REST API 端点（20 个路由）
│   │   │   │   ├── ws/         # WebSocket
│   │   │   │   └── deps/       # 依赖注入
│   │   │   ├── models/         # SQLAlchemy ORM 模型（18 个文件）
│   │   │   ├── schemas/        # Pydantic DTO（16 个文件）
│   │   │   ├── services/       # 业务逻辑（9 个服务）
│   │   │   ├── repositories/   # 数据库抽象层
│   │   │   ├── orchestration/  # DAG、Judge、状态机、Memory（18 个模块）
│   │   │   ├── heartbeat/      # 定时执行调度器
│   │   │   ├── providers/      # LLM 网关、Ollama、g4f、RAG
│   │   │   ├── tools/          # 外部工具连接（MCP/Webhook/API/CLI）
│   │   │   ├── policies/       # 审批门控、自主执行边界
│   │   │   ├── security/       # 密钥管理、数据脱敏、IAM
│   │   │   ├── integrations/   # Sentry、MCP Server、外部技能
│   │   │   ├── audit/          # 审计日志
│   │   │   └── tests/          # 测试
│   │   ├── alembic/            # 数据库迁移
│   │   └── model_catalog.json  # LLM 模型目录（动态管理）
│   ├── desktop/                # Tauri v2 桌面应用
│   │   ├── src-tauri/          # Rust 后端
│   │   └── ui/src/             # React 前端
│   │       ├── pages/          # 21 个页面组件
│   │       ├── features/       # 功能模块
│   │       ├── shared/         # 共享 API、类型、hooks、UI
│   │       └── app/            # 路由和入口
│   ├── edge/                   # Cloudflare Workers
│   │   ├── proxy/              # 方式A：反向代理
│   │   └── full/               # 方式B：Hono + D1 完全迁移
│   └── worker/                 # 后台工作进程
│       ├── runners/            # 任务和 Heartbeat 执行器
│       ├── executors/          # LLM 和沙箱执行器
│       ├── sandbox/            # 隔离执行环境（本地/Docker/Workers）
│       └── dispatchers/        # 事件分发
├── skills/
│   ├── builtin/                # 内置技能（6 个，系统保护）
│   └── templates/              # 技能模板
├── plugins/                    # 插件清单（8 个插件）
│   ├── ai-avatar/              # 分身AI
│   ├── ai-secretary/           # 秘书AI
│   ├── discord-bot/            # Discord Bot
│   ├── slack-bot/              # Slack Bot
│   ├── line-bot/               # LINE Bot
│   ├── youtube/                # YouTube 运营
│   ├── research/               # 调研
│   └── backoffice/             # 后台办公
├── extensions/                 # 扩展清单（4 个扩展）
│   ├── oauth/                  # OAuth 认证
│   ├── mcp/                    # MCP 连接
│   ├── notifications/          # 通知
│   └── obsidian/               # Obsidian 集成
├── packages/                   # 共享 NPM 包
├── docs/                       # 文档
├── assets/                     # 标志和图片
├── scripts/                    # 开发和部署脚本
├── Dockerfile                  # Rootless 容器
├── docker-compose.yml          # 全栈编排
├── setup.sh                    # 安装脚本
├── start.sh                    # 启动脚本
└── README.md
```

### 权限模型

| 角色 | 权限 |
|------|------|
| Owner | 全部权限 |
| Admin | 组织设置、部分审批、审计日志 |
| User | 业务委托、计划确认、产出物确认 |
| Auditor | 仅查看执行历史和审计日志 |
| Developer | Skill/Plugin/Extension 的开发 |

### 自主执行边界

| 可自主执行 | 需要审批 |
|-----------|---------|
| 调查・分析 | 发布・投稿 |
| 草稿创建 | 计费・删除 |
| 信息整理 | 权限变更・对外发送 |

### Cloudflare Workers 部署

支持在 Workers 上运行。可从两种方式中选择：

| 方式 | 目录 | 概述 |
|------|------|------|
| **A: Proxy** | `apps/edge/proxy/` | 在现有 FastAPI 前端部署反向代理 |
| **B: Full Workers** | `apps/edge/full/` | 使用 Hono + D1 在边缘完全重新实现主要 API |

```bash
# 方式 A：Proxy
cd apps/edge/proxy && npm install && npm run dev

# 方式 B：Full Workers
cd apps/edge/full && npm install && npm run db:init && npm run dev
```

详情：[apps/edge/README.md](apps/edge/README.md)

### 生产环境

<details>
<summary>生产环境运营

### PostgreSQL

```env
# apps/api/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zero_employee_orchestrator
```

```bash
cd apps/api && source .venv/bin/activate
pip install asyncpg
```

### 安全设置

```env
SECRET_KEY=<生成并设置随机字符串>
DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

</details>

### 许可证

私有项目

### 相关文档

**面向用户（`docs/`）：**
- [`docs/ABOUT.md`](docs/ABOUT.md) — 本系统的优势及与传统系统的差异
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — 面向初学者的用户指南
- [`docs/OVERVIEW.md`](docs/OVERVIEW.md) — 理念、功能、架构的综合指南
- [`docs/FEATURES.md`](docs/FEATURES.md) — 完整功能列表
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — 变更日志

**面向开发者（`docs/dev/`）：**
- [`docs/dev/DESIGN.md`](docs/dev/DESIGN.md) — 实现设计文档（数据库、API、界面、状态转换）
- [`docs/dev/MASTER_GUIDE.md`](docs/dev/MASTER_GUIDE.md) — 实现运营指南（推进方式和判断标准）
- [`docs/dev/BUILD_GUIDE.md`](docs/dev/BUILD_GUIDE.md) — 从零开始的构建指南

### 故障排除

<details>
<summary>常见问题及解决方法</summary>

**`./setup.sh` 无法执行**

```bash
chmod +x setup.sh start.sh
./setup.sh
```

**端口被占用**

```bash
lsof -i :18234   # 后端
lsof -i :5173    # 前端
kill <PID>
./start.sh
```

**Python 虚拟环境错误**

```bash
cd apps/api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

**pnpm install 失败**

```bash
cd apps/desktop/ui
rm -rf node_modules
pnpm install
```

**数据库重置**

```bash
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

</details>
