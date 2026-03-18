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
- **汎用業務基盤** — 会社業務全体の実行基盤として設計

---

## インストール

### PyPI からインストール

```bash
pip install zero-employee-orchestrator
```

### ソースからインストール

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install .
```

### Docker

```bash
docker compose up -d
```

### 動作確認

```bash
zero-employee health
zero-employee --help
```

---

## クイックスタート

### 1. API キー不要で始める（3 通り）

```bash
# 方法 1: サブスクリプションモード（設定不要）
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# 方法 2: Google Gemini 無料 API キー
zero-employee config set GEMINI_API_KEY

# 方法 3: Ollama ローカル LLM（完全オフライン）
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b
```

### 2. サーバー起動

```bash
zero-employee serve
# → http://localhost:18234
```

### 3. ローカルチャットモード（Ollama）

```bash
zero-employee local
zero-employee local --model qwen3:8b --lang ja
```

---

## 主な機能

| 機能 | 説明 |
|------|------|
| **Design Interview** | 自然言語で業務依頼を受け、要件を深掘り |
| **Spec / Plan / Tasks** | 中間成果物として構造化保存、再利用・監査・差し戻し可能 |
| **Task Orchestrator** | DAG ベースの計画生成、コスト見積り、品質モード切替 |
| **Judge Layer** | ルールベース一次判定 + Cross-Model 高精度判定 |
| **Self-Healing / Re-Propose** | 障害時の自動再計画・再提案 |
| **Skill / Plugin / Extension** | 3 層の拡張体系で業務機能を追加（完全 CRUD 管理対応） |
| **自然言語スキル生成** | 自然言語でスキルを説明するだけで AI が自動生成（安全性チェック付き） |
| **システム保護** | システム必須スキルは削除・無効化不可（6 種のビルトインスキルを保護） |
| **分身AI / 秘書AI** | ユーザーの判断基準を学習する分身AI、AI組織との橋渡しをする秘書AI（Plugin） |
| **ブラウザアシスト** | ユーザーの画面を見て操作方法を案内・エラー診断（Extension） |
| **プロンプトインジェクション防御** | 外部からの不正指示を検出・遮断 |
| **Self-Improvement** | AI が自身のスキルを分析・改善・テスト生成（承認必須） |
| **自律運用** | Docker / Cloudflare Workers で PC がオフでもバックグラウンド実行 |

---

## 9 層アーキテクチャ

```
┌─────────────────────────────────────────┐
│  1. User Layer     — 自然言語で目的を伝える    │
│  2. Design Interview — 壁打ち・要件深掘り      │
│  3. Task Orchestrator — DAG分解・進行管理     │
│  4. Skill Layer    — 専門Skill + Context     │
│  5. Judge Layer    — Two-stage + Cross-Model │
│  6. Re-Propose     — 差し戻し・動的DAG再構築   │
│  7. State & Memory — Experience Memory      │
│  8. Provider       — LLMゲートウェイ (LiteLLM)  │
│  9. Skill Registry — Skill公開・検索・Import   │
└─────────────────────────────────────────┘
```

---

## セキュリティ

Zero-Employee Orchestrator は**セキュリティファースト**で設計されています。

### 多層防御

| レイヤー | 機能 |
|---------|------|
| **プロンプトインジェクション防御** | 外部入力からの指示注入を検出・遮断（5 カテゴリ・40+ パターン） |
| **承認ゲート** | 12 カテゴリの危険操作（送信・削除・課金・権限変更等）を人間承認必須化 |
| **自律実行境界** | AI が自律実行できる操作を明示的に制限 |
| **IAM** | 人間/AI アカウント分離、AI に対するシークレット・管理権限の拒否 |
| **シークレット管理** | Fernet 暗号化・自動マスキング・ローテーション支援 |
| **サニタイズ** | API キー・トークン・個人情報の自動除去 |
| **セキュリティヘッダー** | CSP・HSTS・X-Frame-Options 等を全レスポンスに付与 |
| **リクエスト検証** | ボディサイズ制限・Host ヘッダー検証 |
| **レート制限** | slowapi による API レート制限 |
| **監査ログ** | 全重要操作を記録（後付けではなく設計段階から組込み） |

### プロンプトインジェクション防御

外部ソース（ウェブページ、メール本文、ファイル内容、API レスポンス等）に埋め込まれた不正な指示を自動検出・遮断します。

- **CRITICAL**: システムプロンプト書き換え試行（"ignore previous instructions" 等）
- **HIGH**: 権限昇格・データ漏洩試行
- **MEDIUM**: 間接的インジェクション・境界操作
- 外部データは構造的に分離（境界マーカー方式）
- 全検出はログに記録

### 本番環境デプロイ前チェックリスト

```bash
# セキュリティチェックスクリプト
./scripts/security-check.sh

# 必須設定
SECRET_KEY=<ランダム生成値>  # python -c "import secrets; print(secrets.token_urlsafe(32))"
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
```

脆弱性の報告は [SECURITY.md](SECURITY.md) を参照してください。

---

## 自律運用（PC がオフでも稼働）

### Docker Compose（推奨）

```bash
docker compose up -d
# API + Worker がバックグラウンドで自動稼働
# restart: unless-stopped で自動再起動
```

### Cloudflare Workers（サーバーレス）

```bash
cd apps/edge/full
npm run deploy
# サーバー不要、D1 データベースで永続化
```

### Heartbeat スケジューラ

9 種類の発火契機に対応:
- スケジュール（cron 形式）
- チケット作成・タスク割当・差し戻し
- 外部イベント・予算閾値・承認完了
- マネージャー指示・依存完了

---

## ブラウザアシスト（Extension）

ユーザーが Chrome 等のウェブブラウザやアプリケーションを使用中に、AI が同じ画面を見て操作方法を案内します。

```bash
# API 経由で利用
POST /api/v1/browser-assist/consent  # 同意を付与
POST /api/v1/browser-assist/analyze  # スクリーンショット分析
```

### 機能

- **画面分析**: スクリーンショットから UI 要素を特定
- **操作案内**: ステップバイステップで操作手順を提示
- **エラー診断**: 画面上のエラーメッセージを読み取り、解決策を提案
- **フォーム入力支援**: 各フィールドの入力方法を案内
- **UI 説明**: 各要素の役割と使い方を解説

### プライバシーと安全性

- スクリーンショットは一時的にのみ処理（永続保存しない）
- パスワードフィールドは自動ぼかし対応
- ユーザーの明示的な同意が必須
- 自律的なクリック操作は行わない（案内のみ）
- 全キャプチャは監査ログに記録

---

## CLI コマンド

```bash
zero-employee serve              # API サーバーを起動
zero-employee serve --port 8000  # ポート指定
zero-employee serve --reload     # ホットリロード

zero-employee local              # ローカルチャットモード (Ollama)
zero-employee local --model qwen3:8b --lang ja

zero-employee models             # インストール済みモデル一覧
zero-employee pull qwen3:8b      # モデルダウンロード

zero-employee config list        # 全設定値を表示
zero-employee config set <KEY>   # 設定値を保存
zero-employee config get <KEY>   # 設定値を取得
zero-employee config delete <KEY> # 設定値を削除
zero-employee config keys        # 設定可能なキーの一覧

zero-employee db upgrade         # DB マイグレーション
zero-employee health             # ヘルスチェック
```

---

## 対応 LLM モデル

`model_catalog.json` で一元管理。コード変更なしにモデルを入れ替え可能。

| 実行モード | 説明 | 例 |
|-----------|------|-----|
| **Quality** | 最高品質 | Claude Opus, GPT-5.4, Gemini 2.5 Pro |
| **Speed** | 高速応答 | Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash |
| **Cost** | 低コスト | Haiku, Mini, Flash Lite, DeepSeek |
| **Free** | 無料 | Gemini 無料枠, Ollama ローカル |
| **Subscription** | API キー不要 | g4f 経由 |

### Ollama ローカルモード

```bash
# 推奨モデル
zero-employee pull qwen3:8b
zero-employee pull qwen3:32b
zero-employee pull deepseek-coder-v2
```

---

## Skill / Plugin / Extension

### 3 層の拡張体系

| 種別 | 説明 | 例 |
|------|------|-----|
| **Skill** | 単一目的の専門処理 | spec-writer, review-assistant, browser-assist |
| **Plugin** | 複数 Skill をバンドル | ai-secretary, ai-self-improvement, youtube |
| **Extension** | システム連携・インフラ | mcp, oauth, notifications, browser-assist |

### 自然言語でスキル生成

```bash
POST /api/v1/registry/skills/generate
{
  "description": "長文ドキュメントを3つの要点にまとめるスキル"
}
```

16 種類の危険パターンを自動検出。安全性チェック通過後にのみ登録。

### 外部スキルのインポート

```bash
POST /api/v1/registry/plugins/search-external
{ "query": "document summarizer" }

POST /api/v1/registry/plugins/import
{ "source_uri": "https://github.com/user/agent-skills-repo" }
```

---

## API エンドポイント

バージョンプレフィックス: `/api/v1`

<details>
<summary>全エンドポイント一覧（クリックで展開）</summary>

| グループ | パス | 説明 |
|---------|------|------|
| 認証 | `/auth` | 認証・セッション |
| 組織 | `/companies` | 会社・組織 |
| エージェント | `/companies/{id}/agents` | エージェント管理 |
| チケット | `/companies/{id}/tickets` | チケット管理 |
| 仕様・計画 | `/tickets/{id}/specs` | Spec/Plan/Tasks |
| タスク | `/tasks/{id}` | タスク実行 |
| 承認 | `/approvals` | 承認管理 |
| 予算 | `/companies/{id}/budgets` | 予算・コスト |
| 監査 | `/companies/{id}/audit-logs` | 監査ログ |
| レジストリ | `/registry` | Skill/Plugin/Extension |
| モデル | `/models` | モデルカタログ |
| 推論トレース | `/traces` | エージェント判断過程 |
| 通信ログ | `/communications` | エージェント間通信 |
| 監視 | `/monitor` | リアルタイム実行監視 |
| WebSocket | `/ws/events` | リアルタイムイベント |
| ナレッジ | `/knowledge` | ナレッジストア |
| Ollama | `/ollama` | ローカル LLM |
| MCP | `/mcp` | MCP サーバー |
| IAM | `/iam` | アクセス制御 |
| 設定 | `/config` | ランタイム設定 |
| Self-Improvement | `/self-improvement` | AI 自己改善 |
| ブラウザアシスト | `/browser-assist` | 画面分析・操作案内 |
| 壁打ち | `/companies/{id}/brainstorm` | ブレインストーミング |
| 会話記憶 | `/companies/{id}/conversation-memory` | 会話永続保管 |
| 仮説検証 | `/hypotheses` | 並行検証 |
| セッション | `/sessions` | エージェントセッション |

</details>

---

## 技術スタック

### バックエンド
- Python 3.12+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- SQLite (開発) / PostgreSQL (本番推奨)
- LiteLLM Router SDK
- bcrypt / Fernet 暗号化
- slowapi レート制限

### フロントエンド
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand

### デスクトップ
- Tauri v2 (Rust) + Python サイドカー

### デプロイ
- Docker + docker-compose
- Cloudflare Workers (サーバーレス)

---

## ディレクトリ構成

```
apps/
├── api/              # FastAPI バックエンド
│   └── app/
│       ├── core/           # 設定・DB・セキュリティ・i18n
│       ├── api/routes/     # 26 REST API エンドポイント
│       ├── api/ws/         # WebSocket
│       ├── models/         # SQLAlchemy ORM
│       ├── schemas/        # Pydantic DTO
│       ├── services/       # ビジネスロジック
│       ├── repositories/   # DB 入出力抽象化
│       ├── orchestration/  # DAG・Judge・状態機械
│       ├── providers/      # LLM ゲートウェイ・Ollama・RAG
│       ├── security/       # IAM・シークレット・サニタイズ・プロンプト防御
│       ├── policies/       # 承認ゲート・自律実行境界
│       ├── integrations/   # Sentry・MCP・外部スキル・ブラウザアシスト
│       └── tools/          # 外部ツール接続
├── desktop/          # Tauri + React UI
├── edge/             # Cloudflare Workers
└── worker/           # バックグラウンドワーカー
skills/               # ビルトインスキル（7 個）
plugins/              # Plugin マニフェスト（11 Plugin）
extensions/           # Extension マニフェスト（5 Extension）
packages/             # 共有 NPM パッケージ
```

---

## 開発

```bash
# 開発環境セットアップ
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# サーバー起動（ホットリロード）
zero-employee serve --reload

# テスト
pytest apps/api/app/tests/

# リント
ruff check apps/api/app/
ruff format apps/api/app/
```

---

## コントリビューション

1. Fork → Branch → PR の標準フロー
2. セキュリティ問題は [SECURITY.md](SECURITY.md) に従い、非公開で報告
3. コーディング規約: ruff フォーマット・型ヒント必須・async def

---

## ライセンス

[MIT License](LICENSE)

---

<a id="english"></a>
## English

### What is this?

Zero-Employee Orchestrator is a platform for running **AI as an organization** — not just a single chatbot, but a team of AI agents with role-based delegation, human approval gates, and full auditability.

### Key Features

- **Multi-Agent Orchestration**: DAG-based task planning with specialized agents
- **Human-in-the-Loop**: 12 categories of dangerous operations require human approval
- **Skill / Plugin / Extension**: 3-layer extensibility with natural language skill generation
- **Prompt Injection Defense**: 40+ patterns detected across 5 threat categories
- **Browser Assist**: AI analyzes your screen and guides you through web operations
- **Self-Improvement**: AI analyzes and improves its own skills (with approval)
- **Autonomous Operation**: Runs in Docker/Cloudflare Workers even when your PC is off
- **Multi-Model Support**: Dynamic model catalog, auto-fallback for deprecated models

### Installation

```bash
pip install zero-employee-orchestrator

# or from source
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .

# or Docker
docker compose up -d
```

### Quick Start

```bash
# Configure (optional - works without API keys in subscription mode)
zero-employee config set GEMINI_API_KEY

# Start server
zero-employee serve

# Or use local chat mode with Ollama
zero-employee local --model qwen3:8b --lang en
```

### Security

- Prompt injection defense (5 categories, 40+ patterns)
- Approval gates for 12 categories of dangerous operations
- IAM with human/AI account separation
- Secret management with Fernet encryption
- Security headers (CSP, HSTS, X-Frame-Options)
- Audit logging from design stage

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

<a id="中文"></a>
## 中文

### 这是什么？

Zero-Employee Orchestrator 是一个将 **AI 作为组织来运营**的平台——不只是单一聊天机器人，而是一个具有角色分工、人类审批和完整审计能力的 AI 代理团队。

### 主要功能

- **多代理编排**: 基于 DAG 的任务规划与专业代理
- **人机协作**: 12 类危险操作需要人类审批
- **技能/插件/扩展**: 三层可扩展体系，支持自然语言生成技能
- **提示注入防御**: 5 个威胁类别，40+ 检测模式
- **浏览器辅助**: AI 分析你的屏幕，指导网页操作
- **自我改进**: AI 分析和改进自身技能（需审批）
- **自主运行**: 通过 Docker/Cloudflare Workers 即使 PC 关机也能运行

### 安装

```bash
pip install zero-employee-orchestrator
zero-employee serve
```

---

## Star History

如果这个项目对您有用，请给一个 Star！

If you find this project useful, please give it a star!

---

<p align="center">
  <strong>Zero-Employee Orchestrator</strong> — AI を組織として運用する基盤<br>
  Built with security, auditability, and human oversight in mind.
</p>
