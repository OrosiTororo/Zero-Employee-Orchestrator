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

> **AI Orchestration Platform — Design · Execute · Verify · Improve**
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
| **承認フロー** | 危険操作は必ず人間承認を要求 |
| **監査ログ** | 全重要操作を追跡可能 |

### インストール

#### GUI 版（デスクトップアプリ）

[Releases ページ](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases) からインストーラーをダウンロードして実行してください。

| OS | 形式 | ダウンロード |
|----|------|-------------|
| Windows | `.msi` / `.exe` | [最新リリース](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |
| macOS | `.dmg` | [最新リリース](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |
| Linux | `.AppImage` / `.deb` | [最新リリース](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |

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
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # 依存関係の自動インストール・環境構築
./start.sh   # バックエンド + フロントエンドを起動
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

> **⚠️ サブスクリプションと API アクセスは別物です**
>
> ChatGPT Plus・Gemini Advanced・Claude Pro などのサブスクリプションは Web アプリ向けのサービスです。**プログラムから直接呼び出すことはできません。** API アクセスは別途取得・課金が必要です。

#### 無料で始める方法

| 方法 | 説明 | 安定性 |
|------|------|--------|
| **Google Gemini（無料枠）** ⭐ | Google AI Studio でキーを取得。無料枠あり・クレジットカード不要 | 高い |
| **Ollama（ローカル LLM）** | PC 上で LLM を実行。API キー不要・完全オフライン・無制限 | 最高 |
| **サブスクリプションモード** | g4f 経由で無料利用。API キー不要 | 低い（試用向け） |

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

`apps/api/.env` に以下のいずれかを設定してください:

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
| **Approval Flow** | Dangerous operations always require human approval |
| **Audit Log** | All important operations are traceable |

### Install

#### GUI (Desktop App)

Download the installer from the [Releases page](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases).

| OS | Format | Download |
|----|--------|----------|
| Windows | `.msi` / `.exe` | [Latest Release](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |
| macOS | `.dmg` | [Latest Release](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |
| Linux | `.AppImage` / `.deb` | [Latest Release](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |

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
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # Auto-install dependencies & configure environment
./start.sh   # Start backend + frontend
```

After startup, open **http://localhost:5173** in your browser.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:18234 |
| Health Check | http://localhost:18234/healthz |
| API Docs (JSON) | http://localhost:18234/api/v1/openapi.json |

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
| **审批流程** | 危险操作必须获得人类审批 |
| **审计日志** | 所有重要操作可追溯 |

### 安装

#### GUI版（桌面应用）

从 [Releases 页面](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases) 下载安装程序。

| 操作系统 | 格式 | 下载 |
|---------|------|------|
| Windows | `.msi` / `.exe` | [最新版本](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |
| macOS | `.dmg` | [最新版本](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |
| Linux | `.AppImage` / `.deb` | [最新版本](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/latest) |

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
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # 自动安装依赖并配置环境
./start.sh   # 启动后端 + 前端
```

启动后，在浏览器中打开 **http://localhost:5173**。

| 服务 | URL |
|------|-----|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:18234 |
| 健康检查 | http://localhost:18234/healthz |
| API 文档 (JSON) | http://localhost:18234/api/v1/openapi.json |

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

**数据库重置**

```bash
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

</details>

---

## ディレクトリ構成 / Directory Structure

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                # FastAPI バックエンド / Backend
│   │   ├── app/
│   │   │   ├── core/       # 設定・DB・セキュリティ
│   │   │   ├── api/        # ルーティング
│   │   │   ├── models/     # SQLAlchemy ORM モデル
│   │   │   ├── schemas/    # Pydantic DTO
│   │   │   ├── services/   # ビジネスロジック（Skill管理・Plugin/Extension管理）
│   │   │   └── banner.py   # CLI バナー表示
│   │   ├── alembic/        # DB マイグレーション
│   │   └── pyproject.toml
│   ├── desktop/            # Tauri デスクトップアプリ
│   │   └── ui/             # React フロントエンド
│   │       └── src/
│   │           ├── pages/
│   │           ├── shared/
│   │           └── ...
│   ├── edge/               # Cloudflare Workers デプロイ
│   │   ├── proxy/          # 方式A: リバースプロキシ
│   │   └── full/           # 方式B: エッジ完全移植 (Hono + D1)
│   └── worker/             # バックグラウンドワーカー
├── plugins/                # Plugin マニフェスト
│   ├── ai-avatar/          # 分身AI
│   ├── ai-secretary/       # 秘書AI
│   ├── discord-bot/        # Discord Bot
│   ├── slack-bot/          # Slack Bot
│   ├── line-bot/           # LINE Bot
│   ├── youtube/            # YouTube 運用
│   ├── research/           # リサーチ
│   └── backoffice/         # バックオフィス
├── extensions/             # Extension マニフェスト
├── skills/                 # Skill 定義
├── assets/                 # ロゴ・画像
│   └── logo.svg
├── scripts/                # 開発・運用スクリプト
├── setup.sh                # セットアップスクリプト
├── start.sh                # 起動スクリプト
└── README.md
```

---

## Cloudflare Workers デプロイ / Deploy

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

---

## 本番環境 / Production

<details>
<summary>本番環境での運用 / Production Setup</summary>

### PostgreSQL

```env
# apps/api/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zero_employee_orchestrator
```

```bash
cd apps/api && source .venv/bin/activate
pip install asyncpg
```

### セキュリティ / Security

```env
SECRET_KEY=<ランダムな文字列を生成して設定>
DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

</details>

---

## ライセンス / License

プライベートプロジェクト / Private Project

## 関連文書 / Related Documents

- `ABOUT.md` — このシステムのメリット・従来システムとの違い
- `USER_GUIDE.md` — 初心者向けユーザーガイド
- `Zero-Employee Orchestrator.md` — 最上位基準文書（思想・要件・改善方針）
- `DESIGN.md` — 実装設計書（DB・API・画面・状態遷移）
- `MASTER_GUIDE.md` — 実装運用ガイド（進め方と判断基準）
