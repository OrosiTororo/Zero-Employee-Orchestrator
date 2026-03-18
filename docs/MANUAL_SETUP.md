# 手動セットアップガイド

> 開発者が手動で設定・構成する必要がある項目の一覧
>
> 最終更新: 2026-03-18

---

## 1. 外部 API キーの設定

以下の外部サービスを利用する場合、開発者が手動で API キーを設定する必要があります。

### LLM プロバイダー

```bash
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

# Google Workspace (Docs, Sheets 等)
# → OAuth2 設定が必要（下記セクション参照）

# LINE Bot
zero-employee config set LINE_CHANNEL_SECRET <your-secret>
zero-employee config set LINE_CHANNEL_ACCESS_TOKEN <your-token>
```

---

## 2. iPaaS 連携の Webhook 設定

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

## 3. OAuth2 / 認証設定

### Google Workspace 連携

1. [Google Cloud Console](https://console.cloud.google.com) でプロジェクトを作成
2. 「API とサービス」→「認証情報」→ OAuth 2.0 クライアント ID を作成
3. リダイレクト URI に `http://localhost:18234/api/v1/auth/google/callback` を追加
4. 設定:

```bash
zero-employee config set GOOGLE_CLIENT_ID <client-id>
zero-employee config set GOOGLE_CLIENT_SECRET <client-secret>
```

### Sentry (エラー監視)

```bash
zero-employee config set SENTRY_DSN <your-dsn>
```

---

## 4. セキュリティ設定（本番環境必須）

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

### ファイルサンドボックス

```bash
# 許可フォルダの追加
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/projects,/tmp/work"

# レベル変更（推奨: strict のまま）
zero-employee config set SANDBOX_LEVEL strict
```

### データ保護ポリシー

```bash
# デフォルト: lockdown（全転送禁止）
# 必要に応じて変更
zero-employee config set SECURITY_TRANSFER_POLICY restricted

# アップロード・ダウンロード許可先の設定
zero-employee config set SECURITY_ALLOWED_UPLOAD_DESTINATIONS '["internal_storage"]'
zero-employee config set SECURITY_ALLOWED_DOWNLOAD_SOURCES '["internal_storage"]'
```

---

## 5. データベース設定

### 開発環境（SQLite、設定不要）

デフォルトで SQLite を使用します。追加設定は不要です。

### 本番環境（PostgreSQL 推奨）

```bash
# PostgreSQL 接続文字列
zero-employee config set DATABASE_URL "postgresql+asyncpg://user:password@localhost:5432/zeo"

# マイグレーション実行
zero-employee db upgrade
```

---

## 6. Ollama ローカル LLM セットアップ

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

## 7. Chrome 拡張機能のインストール

```
1. Chrome で chrome://extensions を開く
2. 右上の「デベロッパーモード」を ON
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. extensions/browser-assist/chrome-extension/ フォルダを選択
5. ZEO サーバーが起動していることを確認（http://localhost:18234）
```

---

## 8. Obsidian 連携

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

## 9. クラウドプロバイダー設定

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

## 10. Docker / 自律運用設定

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

---

## 11. Heartbeat スケジューラ設定

定期実行タスクを設定する場合:

```bash
# API 経由でスケジュール登録
POST /api/v1/heartbeats
{
  "name": "daily-report",
  "trigger": "schedule",
  "cron": "0 9 * * *",
  "task_template": { "type": "generate_report" }
}
```

---

## 12. レッドチーム セキュリティテスト

定期的にセキュリティテストを実行することを推奨します:

```bash
# セキュリティチェックスクリプト
./scripts/security-check.sh

# API 経由でレッドチームテスト実行
POST /api/v1/security/redteam/run
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

*Zero-Employee Orchestrator — 手動設定ガイド*
