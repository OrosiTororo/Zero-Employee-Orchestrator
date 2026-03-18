# Zero-Employee Orchestrator — Claude Code 開発ガイド

> **重要**: 作業開始前に必ず以下のファイルを確認してください。
> このガイドの情報が古い可能性があるため、常に実際のコードとドキュメントを参照してください。
>
> 1. `docs/Zero-Employee Orchestrator.md` — 最上位基準文書
> 2. `docs/dev/DESIGN.md` — 実装設計書
> 3. `docs/dev/MASTER_GUIDE.md` — 実装運用ガイド
> 4. `README.md` — プロジェクト概要・インストール方法
> 5. `SECURITY.md` — セキュリティポリシー
> 6. `pyproject.toml` — パッケージ設定・依存関係

## 作業開始時の必須確認事項

**毎回の作業開始時に以下を実行してください:**

1. **リポジトリの最新状態を確認**: `git log --oneline -10` で最新コミットを確認
2. **ディレクトリ構成を確認**: `ls apps/api/app/` で現在のモジュール構成を確認
3. **README.md を確認**: 最新の機能一覧・API エンドポイント・インストール方法
4. **SECURITY.md を確認**: セキュリティポリシーと脆弱性報告方法
5. **pyproject.toml を確認**: 現在のバージョン・依存関係
6. **既存のテストを確認**: `ls apps/api/app/tests/` でテストファイルを確認

**情報が古い場合は、実際のコードを読んでこのファイルを更新してください。**

## プロジェクト概要

Zero-Employee Orchestrator は、自然言語で業務を定義し、複数 AI を役割分担させ、
人間の承認と監査可能性を前提に業務を実行・再計画・改善できる AI オーケストレーション基盤である。

**PyPI パッケージ**: `zero-employee-orchestrator`
**バージョン**: 0.1.0
**ライセンス**: MIT

## 9層アーキテクチャ

1. **User Layer** — 自然言語で目的を伝える
2. **Design Interview** — 壁打ち・すり合わせで要件を深掘り
3. **Task Orchestrator** — タスク分解・Skill割当・進行管理 + Self-Healing DAG
4. **Skill Layer** — 単一目的の専門Skill + Local Context Skill
5. **Judge Layer** — Two-stage Detection + Cross-Model Verification
6. **Re-Propose Layer** — 差し戻し時の再提案 + 動的DAG再構築
7. **State & Memory** — 永続的な実行環境・Experience Memory・Failure Taxonomy
8. **Provider Interface** — LLM ゲートウェイ（LiteLLM）
9. **Skill Registry** — Skill/Plugin の公開・検索・インストール

## 技術スタック

### バックエンド
- Python 3.12+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- データベース: SQLite (開発) / PostgreSQL (本番推奨)
- LLM ゲートウェイ: LiteLLM Router SDK
- 認証: OAuth PKCE + ローカル暗号化ストア
- パスワードハッシュ: bcrypt（必須）
- レート制限: slowapi
- パッケージ管理: uv
- ビルド: hatchling

### フロントエンド
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand
- React Router
- パッケージ管理: pnpm

### デスクトップ
- Tauri v2 (Rust)
- Python バックエンドはサイドカー

### デプロイ
- Docker + docker-compose（自律運用対応）
- Cloudflare Workers（サーバーレス）

## ディレクトリ構成

> **注意**: 最新の構成は `ls` コマンドで確認してください。以下は参考情報です。

```
apps/
├── api/              # FastAPI バックエンド
│   ├── app/
│   │   ├── core/           # 設定・DB・セキュリティ・i18n
│   │   ├── api/routes/     # 26 REST API エンドポイント
│   │   ├── api/ws/         # WebSocket
│   │   ├── api/deps/       # 依存性注入
│   │   ├── models/         # SQLAlchemy ORM モデル
│   │   ├── schemas/        # Pydantic DTO
│   │   ├── services/       # ビジネスロジック
│   │   ├── repositories/   # DB 入出力抽象化
│   │   ├── orchestration/  # DAG・Judge・状態機械・Knowledge・Artifact Bridge
│   │   ├── heartbeat/      # Heartbeat スケジューラ
│   │   ├── providers/      # LLM ゲートウェイ・Ollama・g4f・RAG
│   │   ├── tools/          # 外部ツール接続 (MCP/Webhook/API/CLI)
│   │   ├── policies/       # 承認ゲート・自律実行境界
│   │   ├── security/       # IAM・シークレット・サニタイズ・プロンプト防御
│   │   ├── integrations/   # Sentry・MCP・外部スキル・ブラウザアシスト・AI調査
│   │   ├── audit/          # 監査ログ
│   │   └── tests/          # テスト
│   └── alembic/            # マイグレーション
├── desktop/          # Tauri + React UI
│   ├── src-tauri/
│   └── ui/src/
├── edge/             # Cloudflare Workers (Proxy / Full)
│   ├── proxy/              # 方式A: リバースプロキシ
│   └── full/               # 方式B: Hono + D1 完全移植
└── worker/           # バックグラウンドワーカー（自律運用）
    ├── runners/            # タスク・Heartbeat 実行
    ├── executors/          # LLM・サンドボックス実行
    ├── sandbox/            # クラウドサンドボックス
    └── dispatchers/        # イベント配信
skills/
├── builtin/                # 組み込み Skill（7 個・browser-assist 含む）
└── templates/              # Skill テンプレート
plugins/                    # Plugin マニフェスト（11 Plugin）
extensions/                 # Extension マニフェスト（5 Extension・browser-assist 含む）
packages/                   # 共有 NPM パッケージ
docs/                       # 利用者向けドキュメント
└── dev/                    # 開発者向けドキュメント
scripts/                    # 開発・運用スクリプト
```

## コーディング規約

### Python
- ruff でフォーマット・リント（line-length=100）
- 型ヒント必須
- docstring は日本語可
- FastAPI エンドポイントは全て async def
- テスト: pytest + pytest-asyncio

### TypeScript
- strict モード
- 関数コンポーネントのみ
- Tailwind CSS でスタイリング

## ポート

- FastAPI: 18234
- Vite dev server: 5173

## セキュリティ（最重要）

### 多層防御アーキテクチャ

1. **プロンプトインジェクション防御** (`security/prompt_guard.py`)
   - 5 カテゴリ・40+ パターンの検出
   - CRITICAL: システムプロンプト書き換え試行
   - HIGH: 権限昇格・データ漏洩試行
   - MEDIUM: 間接的インジェクション・境界操作
   - 外部データの境界マーカー方式による分離
   - ユーザー発信元検証

2. **承認ゲート** (`policies/approval_gate.py`)
   - 12 カテゴリの危険操作検出
   - 外部送信・公開・削除・課金・Git push・権限変更等

3. **自律実行境界** (`policies/autonomy_boundary.py`)
   - 安全操作（調査・分析・下書き）: 自律実行可
   - 危険操作（送信・削除・課金）: 承認必須

4. **IAM** (`security/iam.py`)
   - 人間/AI/サービスアカウント分離
   - AI に対するシークレット・管理権限・承認権限の拒否

5. **セキュリティヘッダー** (`security/security_headers.py`)
   - CSP, HSTS, X-Frame-Options, X-Content-Type-Options
   - Permissions-Policy（カメラ・マイク・位置情報等を制限）
   - 認証済みレスポンスのキャッシュ防止

6. **リクエスト検証** (`security/security_headers.py`)
   - 最大ボディサイズ制限（10MB）
   - Host ヘッダーインジェクション防止

7. **シークレット管理** (`security/secret_manager.py`)
   - Fernet 暗号化（AES-128-CBC + HMAC-SHA256）
   - 自動マスキング・有効期限チェック

8. **サニタイズ** (`security/sanitizer.py`)
   - API キー・Bearer トークン・OAuth トークン・パスワード・メール自動検出
   - [REDACTED:type] マーカーで置換

9. **レート制限** (`core/rate_limit.py`)
   - slowapi による API レート制限

### セキュリティコード変更時の注意

- **新しい API エンドポイント追加時**: プロンプトインジェクション検査の必要性を検討
- **外部データを LLM に渡す時**: 必ず `wrap_external_data()` で境界マーカーを付与
- **危険操作を追加する時**: `approval_gate.py` と `autonomy_boundary.py` に登録
- **シークレットを扱う時**: `sanitizer.py` でサニタイズ後にログ出力

## API エンドポイント

> **注意**: 最新のエンドポイント一覧は `apps/api/app/api/routes/__init__.py` を確認してください。

バージョンプレフィックス: `/api/v1`

主要グループ:
- `/auth` — 認証・セッション
- `/companies` — 会社・組織
- `/companies/{id}/agents` — エージェント管理
- `/companies/{id}/tickets` — チケット管理
- `/tickets/{id}/specs` — Spec/Plan/Tasks
- `/tasks/{id}` — タスク実行
- `/approvals` — 承認管理
- `/companies/{id}/heartbeat-*` — Heartbeat
- `/companies/{id}/budgets` — 予算・コスト
- `/companies/{id}/audit-logs` — 監査ログ
- `/registry` — Skill/Plugin/Extension
- `/models` — モデルカタログ管理
- `/traces` — 推論トレース
- `/communications` — エージェント間通信ログ
- `/monitor` — リアルタイム実行監視
- `/ws/events` — WebSocket リアルタイム
- `/knowledge` — ナレッジストア・変更検知
- `/ollama` — ローカル LLM
- `/mcp` — MCP サーバー
- `/skills/external` — 外部スキル検索・インポート
- `/iam` — IAM
- `/config` — ランタイム設定管理
- `/self-improvement` — AI Self-Improvement
- `/browser-assist` — ブラウザアシスト（画面分析・操作案内）
- `/companies/{id}/brainstorm` — 壁打ちセッション
- `/companies/{id}/conversation-memory` — 会話記憶
- `/hypotheses` — 仮説の並行検証
- `/sessions` — エージェントセッション管理

## CLI コマンド

```
zero-employee serve              # API サーバーを起動
zero-employee serve --port 8000
zero-employee serve --reload     # ホットリロード
zero-employee db upgrade         # DB マイグレーション
zero-employee health             # ヘルスチェック
zero-employee models             # インストール済みモデル一覧
zero-employee pull qwen3:8b      # モデルダウンロード
zero-employee local              # ローカルチャットモード
zero-employee local --model qwen3:8b --lang ja
zero-employee config list        # 全設定値を表示
zero-employee config set <KEY>   # 設定値を保存
zero-employee config get <KEY>   # 設定値を取得
zero-employee config delete <KEY> # 設定値を削除
zero-employee config keys        # 設定可能なキーの一覧
```

## ランタイム設定管理

### 設定方法（3 通り）
1. **設定画面**: アプリの「設定」→「LLM API キー設定」
2. **CLI**: `zero-employee config set/get/list/delete/keys`
3. **.env ファイル**: `apps/api/.env` を直接編集

### 優先順位
環境変数 > `~/.zero-employee/config.json` > `.env` > デフォルト値

## 対応 LLM モデル（動的管理）

`apps/api/model_catalog.json` で一元管理。コード変更なしにモデルを入れ替え可能。

### 実行モード
- **Quality**: Claude Opus, GPT-5.4, Gemini 2.5 Pro
- **Speed**: Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash
- **Cost**: Haiku, Mini, Flash Lite, DeepSeek
- **Free**: Gemini 無料枠, Ollama ローカル
- **Subscription**: g4f 経由（API キー不要）

## Skill 管理

### 自然言語スキル生成
- `POST /api/v1/registry/skills/generate` で自然言語からスキルを自動生成
- 16 種類の危険パターンを自動検出
- 安全性チェック通過後にのみ登録

### システム保護スキル（7 個）
- `spec-writer` — 仕様書生成
- `plan-writer` — 実行計画生成
- `task-breakdown` — タスク DAG 分解
- `review-assistant` — 品質レビュー
- `artifact-summarizer` — 成果物要約
- `local-context` — ローカルコンテキスト
- `browser-assist` — ブラウザアシスト（画面分析・操作案内）

### 外部スキルのインポート
- GitHub (`topic:agent-skills`)
- skills.sh, OpenClaw, Claude Code 形式
- 任意の Git リポジトリ / URL

## ブラウザアシスト（Extension）

ユーザーがブラウザやアプリを使用中に画面を共有し、AI が操作方法を案内する拡張機能。

### エンドポイント
- `POST /api/v1/browser-assist/consent` — 画面共有同意
- `POST /api/v1/browser-assist/analyze` — スクリーンショット分析
- `GET /api/v1/browser-assist/status` — ステータス確認

### アクション種別
- `analyze_screen` — 画面分析
- `guide_navigation` — 操作案内
- `diagnose_error` — エラー診断
- `fill_form_guide` — フォーム入力支援
- `explain_ui` — UI 説明

### 安全性
- ユーザーの明示的な同意が必須
- スクリーンショットは一時的にのみ処理（永続保存しない）
- 自律的なクリック操作は行わない（案内のみ）
- 全キャプチャは監査ログに記録

## 自律運用

### バックグラウンドワーカー (`apps/worker/`)
- TaskRunner: タスクキューの自動処理（5 秒間隔ポーリング）
- HeartbeatRunner: スケジュール実行（30 秒間隔チェック）
- EventDispatcher: イベント駆動タスク配信

### Docker Compose
```bash
docker compose up -d
# restart: unless-stopped で自動再起動
```

### Cloudflare Workers
```bash
cd apps/edge/full
npm run deploy
# サーバー不要・D1 データベースで永続化
```

## AI Self-Improvement API (Level 2)

### エンドポイント
- `POST /api/v1/self-improvement/analyze` — Skill 品質分析
- `POST /api/v1/self-improvement/improve` — 改善版生成（承認必須）
- `POST /api/v1/self-improvement/judge/tune` — Judge ルール自動提案
- `POST /api/v1/self-improvement/failure-to-skill` — 失敗から予防 Skill 生成
- `POST /api/v1/self-improvement/ab-test` — A/B テスト
- `POST /api/v1/self-improvement/generate-tests` — テスト自動生成

## DB スキーマ概要

> **注意**: 最新のスキーマは `apps/api/app/models/` を確認してください。

全テーブルに `id`, `company_id`, `created_at`, `updated_at` を基本カラムとして持つ。

## 重要な設計原則

1. **名称は Zero-Employee Orchestrator で統一** — 旧名称は使わない
2. **危険操作は承認前提** — 投稿・送信・削除・課金・権限変更は自律実行しない
3. **本体と拡張を分離** — Skill / Plugin / Extension の境界を明確に
4. **状態遷移をコードに明示** — 状態機械で管理
5. **監査ログを後付けにしない** — 重要操作は最初から記録
6. **プロンプトインジェクション防御** — 外部データは境界マーカーで分離
7. **セキュリティファースト** — 新機能追加時はセキュリティ影響を必ず検討
8. **マルチエージェント協調の可視化** — 通信ログで追跡

## PyPI パッケージ

```bash
# インストール
pip install zero-employee-orchestrator

# 開発用インストール
pip install -e ".[dev]"

# ビルド
python -m build

# アップロード
twine upload dist/*
```

## 禁止事項

- Zero-Employee Orchestrator を YouTube 自動化ツールとして実装すること
- Skill / Plugin / Extension の境界を曖昧にすること
- 承認必須操作を黙って実行すること
- 監査ログなしで外部送信や権限変更を行うこと
- ローカル文脈アクセスを無制限権限で実装すること
- **外部データを LLM に渡す際に `wrap_external_data()` を使わないこと**
- **プロンプトインジェクション検査なしでユーザー入力を LLM に渡すこと**
- **セキュリティヘッダーを無効化すること**
