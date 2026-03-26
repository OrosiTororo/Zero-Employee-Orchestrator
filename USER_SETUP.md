# ユーザーセットアップガイド

> 日本語 | [English](docs/en/USER_SETUP.md) | [中文](docs/zh/USER_SETUP.md)

> ZEO はミニマルな初期状態で動作し、ユーザーが必要に応じて機能を拡張していく設計です。
> 以下の設定はすべて任意で、使いたい機能に応じて各自で行ってください。
>
> ZEO 本体の開発・品質管理に関する設定（Sentry・セキュリティテスト等）については `docs/dev/DEVELOPER_SETUP.md` を参照してください。
>
> 最終更新: 2026-03-23

---

## 1. LLM プロバイダーの接続

ZEO は API キー不要で利用を開始できます。以下の 3 通りの方法があります:

```bash
# 方法 1: サブスクリプションモード（キー不要）
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# 方法 2: Ollama ローカル LLM（完全オフライン・キー不要）
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# 方法 3: マルチ LLM プラットフォーム（1 つのキーで複数モデル利用可能）
zero-employee config set OPENROUTER_API_KEY <your-key>
```

> **ZEO 自体は利用料金を徴収しません。** LLM の API 費用はユーザーが各プロバイダーに直接支払います。
> 特定のプロバイダーへの依存はありません。新しいプラットフォームやサービスが登場した場合も、設定の追加だけで対応可能です。

### 外部 API キーの設定（任意）

より高品質なモデルや特定のプロバイダーを使用したい場合、API キーを設定してください。すべて任意です。

#### LLM プロバイダー

```bash
# OpenRouter（マルチ LLM プラットフォーム — 1 つのキーで複数モデル利用可能）
zero-employee config set OPENROUTER_API_KEY <your-key>

# OpenAI (GPT 系)
zero-employee config set OPENAI_API_KEY <your-key>

# Anthropic (Claude 系)
zero-employee config set ANTHROPIC_API_KEY <your-key>

# Google (Gemini 系) — 無料枠あり
zero-employee config set GEMINI_API_KEY <your-key>

# Mistral
zero-employee config set MISTRAL_API_KEY <your-key>

# Cohere
zero-employee config set COHERE_API_KEY <your-key>

# DeepSeek
zero-employee config set DEEPSEEK_API_KEY <your-key>
```

### メディア生成

```bash
# DALL-E (画像生成) — OpenAI API キーと共通
# Stability AI (Stable Diffusion)
zero-employee config set STABILITY_API_KEY <your-key>

# Replicate (Flux, SVD 等)
zero-employee config set REPLICATE_API_TOKEN <your-key>

# ElevenLabs (音声生成)
zero-employee config set ELEVENLABS_API_KEY <your-key>

# Suno (音楽生成)
zero-employee config set SUNO_API_KEY <your-key>

# Runway ML (動画生成)
zero-employee config set RUNWAY_API_KEY <your-key>
```

### カスタムメディアプロバイダーの登録

ビルトインプロバイダー以外の 3D ツールや新しい生成サービスを API から動的に追加できます。

```bash
# 例: 3D モデル生成ツール (Meshy) を登録
curl -X POST http://localhost:18234/api/v1/media/providers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "meshy_3d",
    "media_type": "3d",
    "api_base": "https://api.meshy.ai/v1/generate",
    "env_key": "MESHY_API_KEY",
    "models": ["meshy-v2"],
    "default_model": "meshy-v2",
    "cost_per_generation": 0.30
  }'

# 登録済みプロバイダーの確認
curl http://localhost:18234/api/v1/media/providers

# ユーザー登録プロバイダーの削除
curl -X DELETE http://localhost:18234/api/v1/media/providers/meshy_3d
```

### 外部ツール統合

```bash
# GitHub
zero-employee config set GITHUB_TOKEN <your-token>

# Slack
zero-employee config set SLACK_BOT_TOKEN <your-token>
zero-employee config set SLACK_SIGNING_SECRET <your-secret>

# Discord
zero-employee config set DISCORD_BOT_TOKEN <your-token>

# Notion
zero-employee config set NOTION_API_KEY <your-key>

# Jira
zero-employee config set JIRA_URL <your-url>
zero-employee config set JIRA_API_TOKEN <your-token>

# Figma (MCP 経由)
zero-employee config set FIGMA_ACCESS_TOKEN <your-token>

# LINE Bot
zero-employee config set LINE_CHANNEL_SECRET <your-secret>
zero-employee config set LINE_CHANNEL_ACCESS_TOKEN <your-token>
```

---

## 2. iPaaS 連携の Webhook 設定

外部の iPaaS サービスと ZEO を接続する場合に設定してください。

### n8n

1. n8n インスタンスを起動（セルフホスト or n8n.cloud）
2. Webhook ノードを作成し、URL をコピー
3. ZEO に登録:

```bash
# API 経由
POST /api/v1/ipaas/workflows
{
  "name": "n8n-workflow-1",
  "provider": "n8n",
  "webhook_url": "https://your-n8n.example.com/webhook/xxx",
  "event_types": ["task_completed", "approval_required"]
}
```

### Zapier

1. Zapier で新しい Zap を作成
2. Trigger として「Webhooks by Zapier → Catch Hook」を選択
3. 発行された Webhook URL を ZEO に登録

### Make (Integromat)

1. Make でシナリオを作成
2. Webhook モジュールを追加し、URL をコピー
3. ZEO に登録

---

## 3. Google Workspace 連携（OAuth2）

Google ドキュメント・スプレッドシート等と連携する場合:

1. [Google Cloud Console](https://console.cloud.google.com) でプロジェクトを作成
2. 「API とサービス」→「認証情報」→ OAuth 2.0 クライアント ID を作成
3. リダイレクト URI に `http://localhost:18234/api/v1/auth/google/callback` を追加
4. 設定:

```bash
zero-employee config set GOOGLE_CLIENT_ID <client-id>
zero-employee config set GOOGLE_CLIENT_SECRET <client-secret>
```

---

## 4. セキュリティ設定（本番環境必須）

本番環境で ZEO を運用する場合、以下を必ず設定してください。

### 秘密鍵の生成

```bash
# SECRET_KEY を生成（必ず本番環境では変更すること）
python -c "import secrets; print(secrets.token_urlsafe(32))"
zero-employee config set SECRET_KEY <generated-key>
```

### CORS 設定

```bash
# 本番ドメインのみ許可
zero-employee config set CORS_ORIGINS '["https://your-domain.com"]'

# 開発環境（デフォルト）
zero-employee config set CORS_ORIGINS '["http://localhost:5173","http://localhost:18234"]'
```

### 認証ミドルウェア（重要）

ZEO は JWT ベースの認証を実装しており、保護エンドポイントには `get_current_user` 依存関数による認証が必要です。

**本番環境では以下を必ず確認してください:**

1. **SECRET_KEY が本番用に設定されていること** — デフォルトのエフェメラルキーではサーバー再起動時にすべてのトークンが無効化されます
2. **すべての業務 API ルートで認証が有効であること** — `scripts/security-check.sh` を実行して認証なしのルートがないか確認してください
3. **SecurityHeadersMiddleware が有効であること** — CSP、HSTS、X-Frame-Options 等のセキュリティヘッダーが付与されます

```bash
# デプロイ前のセキュリティチェック
./scripts/security-check.sh

# レッドチームテストで認証バイパスが検出されないことを確認
curl -X POST http://localhost:18234/api/v1/security/redteam/run \
  -H 'Content-Type: application/json' -d '{}'
```

> **警告**: 認証なしで公開されたエンドポイントは、不正なデータ操作やデータ漏洩のリスクがあります。新しいルートを追加する際は、必ず `Depends(get_current_user)` を含めてください。

---

## 5. データベース設定

### 開発・個人利用（SQLite、設定不要）

デフォルトで SQLite を使用します。追加設定は不要です。

### 本番・チーム利用（PostgreSQL 推奨）

```bash
# PostgreSQL 接続文字列
zero-employee config set DATABASE_URL "postgresql+asyncpg://user:password@localhost:5432/zeo"

# マイグレーション実行
zero-employee db upgrade
```

---

## 6. デプロイ設定

### Docker Compose（推奨）

```bash
# 環境変数ファイルを作成
cp .env.example .env
# .env ファイルを編集して API キーを設定

# 起動
docker compose up -d
```

### Cloudflare Workers

```bash
cd apps/edge/full
cp wrangler.toml.example wrangler.toml
# wrangler.toml を編集

npm install
npm run deploy
```

### クラウドプロバイダー

利用するクラウドサービスに応じて CLI をインストール:

```bash
# AWS
pip install awscli
aws configure

# Google Cloud
# gcloud CLI をインストール後:
gcloud auth application-default login

# Azure
# az CLI をインストール後:
az login
```

---

## 7. ワークスペース環境（初期設定）

ZEO は**セキュリティファースト**で設計されています。初期状態では、AI エージェントは**完全に隔離されたワークスペース**で動作し、ローカルファイルやクラウドストレージには一切アクセスできません。

### 初期状態（デフォルト）

```
ワークスペース:           隔離環境（内部ストレージのみ）
ローカルファイルアクセス:  無効
クラウドストレージ接続:    無効
ナレッジソース:            ユーザーがアップロードしたファイルのみ
```

AI エージェントが使用するナレッジ・ファイルは、ユーザーがこの隔離環境にアップロードしたものだけです。ローカルのフォルダやクラウド（Google ドライブ等）のデータには触れません。

### ワークスペースの仕組み

```
┌─────────────────────────────────────────┐
│  隔離ワークスペース（内部ストレージ）       │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  │
│  │ ナレッジ  │  │ 成果物   │  │ 一時   │  │
│  │ (参照用)  │  │ (出力)   │  │ ファイル│  │
│  └─────────┘  └─────────┘  └────────┘  │
│                                         │
│  ※ ユーザーがアップロードしたファイルのみ    │
│  ※ AI はここからのみ読み書き可能           │
└─────────────────────────────────────────┘
          ↑ アップロード    ↓ エクスポート
      ────────────────────────────────
          ↕ ユーザーが許可した場合のみ
┌─────────────────┐  ┌─────────────────┐
│ ローカルフォルダ   │  │ クラウドストレージ  │
│ (デフォルト: 無効) │  │ (デフォルト: 無効)  │
└─────────────────┘  └─────────────────┘
```

---

## 8. ローカルフォルダ・クラウドストレージへのアクセス許可

ユーザーが必要に応じてアクセス範囲を拡張できます。

### GUI で設定

設定画面 > セキュリティ > ワークスペース環境 で以下を設定:

- **ローカルフォルダの追加**: ファイルピッカーで許可フォルダを選択
- **クラウドストレージの接続**: Google ドライブ / OneDrive / Dropbox 等を接続
- **保存先の指定**: 成果物の保存先を「内部ストレージ」「ローカル」「クラウド」から選択

### CLI / TUI で設定

```bash
# ローカルフォルダへのアクセスを許可
zero-employee config set WORKSPACE_LOCAL_ACCESS_ENABLED true
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/documents,/home/user/projects"

# クラウドストレージへのアクセスを許可
zero-employee config set WORKSPACE_CLOUD_ACCESS_ENABLED true
zero-employee config set WORKSPACE_CLOUD_PROVIDERS '["google_drive"]'

# 成果物の保存先を設定
zero-employee config set WORKSPACE_STORAGE_LOCATION internal  # internal / local / cloud

# データ転送ポリシーを変更（ローカル・クラウドアクセスを許可する場合）
zero-employee config set SECURITY_TRANSFER_POLICY restricted
```

### API 経由

```bash
# ワークスペース設定の確認
GET /api/v1/security/workspace

# ワークスペース設定の更新
PUT /api/v1/security/workspace
{
  "local_access_enabled": true,
  "cloud_access_enabled": false,
  "allowed_local_paths": ["/home/user/documents"],
  "cloud_providers": [],
  "storage_location": "internal"
}

# サンドボックスの許可パスを追加
POST /api/v1/security/sandbox/allowed-paths
{ "path": "/home/user/documents" }
```

---

## 9. 業務ごとの環境・権限カスタマイズ

システム全体の設定とは別に、**業務（チケット）ごとに環境・権限・ナレッジの使用範囲を個別に指定**できます。

### チャットで指示する場合

AI にチャットで業務ごとの環境を指示できます:

```
「このタスクではローカルの /home/user/project-x フォルダも参照して」
「Google ドライブの共有フォルダにある資料も使ってほしい」
「この業務の成果物はローカルの /home/user/output に保存して」
```

**重要**: チャットでの指示がシステム設定と異なる場合、AI は計画段階でユーザーに許可を求めます。

例:
```
AI: 「この業務では /home/user/project-x へのアクセスが必要ですが、
     現在のワークスペース設定ではローカルアクセスが無効です。
     このタスクに限り、以下のアクセスを許可しますか？
     - 読み取り: /home/user/project-x
     - 書き込み: /home/user/output
     [許可] [拒否] [設定を恒久変更]」
```

### API 経由でタスク単位の権限を設定

```bash
POST /api/v1/security/workspace/tasks/{task_id}/override
{
  "additional_local_paths": ["/home/user/project-x"],
  "additional_cloud_sources": ["google_drive://shared/project-x"],
  "storage_location": "local",
  "output_path": "/home/user/output"
}
```

---

## 10. ファイルサンドボックス

AI がアクセスできるフォルダを制限する追加設定です。

### レベル

| レベル | 説明 | 初期設定 |
|--------|------|---------|
| **STRICT** | 許可リストのフォルダのみアクセス可能 | **初期設定** |
| MODERATE | 許可リスト + 一般的なファイル拡張子の読み取り | - |
| PERMISSIVE | 禁止リスト以外すべて（非推奨） | - |

```bash
# サンドボックスレベルを設定
zero-employee config set SANDBOX_LEVEL strict

# 許可フォルダを追加
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/projects,/tmp/work"
```

---

## 11. データ保護（アップロード・ダウンロード制御）

| ポリシー | 説明 | 初期設定 |
|---------|------|---------|
| **LOCKDOWN** | 外部転送を全面禁止 | **初期設定** |
| RESTRICTED | ユーザーが許可した宛先のみ | - |
| PERMISSIVE | 禁止リスト以外すべて（非推奨） | - |

```bash
# 転送ポリシーを設定
zero-employee config set SECURITY_TRANSFER_POLICY lockdown

# アップロードを有効化（承認必須のまま）
zero-employee config set SECURITY_UPLOAD_ENABLED true
zero-employee config set SECURITY_UPLOAD_REQUIRE_APPROVAL true
```

---

## 12. Ollama ローカル LLM セットアップ

API キー不要で完全ローカル動作させる場合:

```bash
# 1. Ollama をインストール
curl -fsSL https://ollama.com/install.sh | sh

# 2. 推奨モデルをダウンロード
zero-employee pull qwen3:8b        # 軽量 (推奨)
zero-employee pull qwen3:32b       # 高品質
zero-employee pull deepseek-coder-v2  # コーディング特化

# 3. 実行モードを free に設定
zero-employee config set DEFAULT_EXECUTION_MODE free
```

---

## 13. Chrome 拡張機能のインストール

```
1. Chrome で chrome://extensions を開く
2. 右上の「デベロッパーモード」を ON
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. extensions/browser-assist/chrome-extension/ フォルダを選択
5. ZEO サーバーが起動していることを確認（http://localhost:18234）
```

---

## 14. Obsidian 連携

```bash
# Vault パスの登録（API 経由）
POST /api/v1/knowledge/remember
{
  "category": "obsidian",
  "key": "vault_path",
  "value": "/path/to/your/obsidian/vault"
}
```

Obsidian プラグイン「Local REST API」のインストールも推奨します。

---

## 15. 汎用アプリケーション連携 (App Connector Hub)

ZEO は 35 以上の外部アプリケーションとの統合に対応しています。
すべての接続はユーザーが明示的に許可した範囲でのみ動作します。

### 対応アプリケーション一覧の確認

```bash
# 全対応アプリの一覧
GET /api/v1/app-integrations/apps

# カテゴリ別フィルタ
GET /api/v1/app-integrations/apps?category=knowledge_base
GET /api/v1/app-integrations/apps?category=project_management

# カテゴリ一覧
GET /api/v1/app-integrations/categories
```

### ナレッジベースの接続

```bash
# Notion
zero-employee config set NOTION_API_KEY <your-integration-token>
POST /api/v1/app-integrations/connections
{
  "app_id": "notion",
  "permissions": { "read": true, "write": false, "sync": true }
}

# Logseq（ローカルグラフ）
POST /api/v1/app-integrations/connections
{
  "app_id": "logseq",
  "config": { "path": "/path/to/your/logseq/graph" },
  "permissions": { "read": true, "sync": true }
}

# Joplin（REST API 経由）
zero-employee config set JOPLIN_TOKEN <your-token>
POST /api/v1/app-integrations/connections
{
  "app_id": "joplin",
  "permissions": { "read": true, "sync": true }
}
```

### 生産性ツールの接続

```bash
# Google Workspace（OAuth 設定後）
POST /api/v1/app-integrations/connections
{ "app_id": "google_docs", "permissions": { "read": true, "write": true } }

# Microsoft 365
zero-employee config set MICROSOFT_CLIENT_ID <your-client-id>
POST /api/v1/app-integrations/connections
{ "app_id": "microsoft_365", "permissions": { "read": true } }
```

### プロジェクト管理ツールの接続

```bash
# Asana
zero-employee config set ASANA_ACCESS_TOKEN <your-token>
POST /api/v1/app-integrations/connections
{ "app_id": "asana", "permissions": { "read": true, "write": true } }

# ClickUp
zero-employee config set CLICKUP_API_KEY <your-key>
POST /api/v1/app-integrations/connections
{ "app_id": "clickup", "permissions": { "read": true, "write": true } }
```

### CRM の接続

```bash
# HubSpot
zero-employee config set HUBSPOT_API_KEY <your-key>
POST /api/v1/app-integrations/connections
{ "app_id": "hubspot", "permissions": { "read": true } }

# Salesforce
zero-employee config set SALESFORCE_CLIENT_ID <your-client-id>
POST /api/v1/app-integrations/connections
{ "app_id": "salesforce", "permissions": { "read": true } }
```

### カスタムアプリの登録

ZEO が標準対応していないアプリでも登録可能です。

```bash
POST /api/v1/app-integrations/apps/custom
{
  "name": "My Custom App",
  "category": "custom",
  "description": "社内ツールとの連携",
  "auth_method": "api_key",
  "env_key": "CUSTOM_APP_KEY",
  "base_url": "https://api.example.com",
  "capabilities": ["read_data", "write_data"]
}
```

### データ同期・ナレッジインポート

```bash
# 接続先とデータ同期
POST /api/v1/app-integrations/connections/{connection_id}/sync
{ "direction": "read_only" }

# ナレッジストアへのインポート
POST /api/v1/app-integrations/connections/{connection_id}/import-knowledge
{ "query": "プロジェクト計画", "tags": ["planning"], "limit": 50 }

# 同期履歴の確認
GET /api/v1/app-integrations/connections/{connection_id}/sync-history
```

---

## 16. Heartbeat スケジューラ設定

定期実行タスクを設定する場合:

```bash
# API 経由でスケジュール登録
POST /api/v1/companies/{company_id}/heartbeat-policies
{
  "name": "daily-report",
  "cron_expr": "0 9 * * *",
  "timezone": "Asia/Tokyo",
  "enabled": true
}

# ポリシー一覧
GET /api/v1/companies/{company_id}/heartbeat-policies

# 実行履歴
GET /api/v1/companies/{company_id}/heartbeat-runs
```

---

## 設定の確認

すべての設定が正しいか確認:

```bash
# 全設定値を表示
zero-employee config list

# ヘルスチェック
zero-employee health

# セキュリティ状態
zero-employee security status
```

---

## 設定不要で動作する機能

以下の機能は追加設定なしで利用可能です:

- Design Interview（壁打ち・要件深掘り）
- Task Orchestrator（DAG 分解・進行管理）
- Judge Layer（品質検証）
- Self-Healing DAG（自動再計画）
- Experience Memory（経験記憶）
- Skill Registry（スキル管理）
- 承認フロー・監査ログ
- PII 自動検出・マスキング
- プロンプトインジェクション防御
- ファイルサンドボックス
- メタスキル（AI の学習能力）
- A2A 双方向通信
- マーケットプレイス基盤
- チーム管理基盤
- ガバナンス・コンプライアンス基盤
- リパーパスエンジン
- ユーザー入力要求
- 成果物エクスポート（ローカル）
- E2E テストフレームワーク
- LLM レスポンスモック（テスト用）

---

## セキュリティ初期設定一覧

```
ワークスペース:           隔離環境（内部ストレージのみ）
ローカルアクセス:         無効
クラウドアクセス:         無効
サンドボックス:           STRICT（許可リストのみ）
データ転送ポリシー:       LOCKDOWN（外部転送禁止）
AI アップロード:          無効
AI ダウンロード:          無効
外部 API 呼び出し:        無効
PII 自動検出:             有効（全カテゴリ）
PII アップロードブロック: 有効
パスワード類の転送:       常にブロック
アップロード承認:         必須
ダウンロード承認:         必須
```

---

*Zero-Employee Orchestrator — ユーザーセットアップガイド*
