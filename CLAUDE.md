# Zero-Employee Orchestrator — Claude Code 開発ガイド

## プロジェクト概要

Zero-Employee Orchestrator は、自然言語で業務を定義し、複数 AI を役割分担させ、
人間の承認と監査可能性を前提に業務を実行・再計画・改善できる AI オーケストレーション基盤である。

## 参照優先順位

1. `docs/Zero-Employee Orchestrator.md` — 最上位基準文書（思想・要件）
2. `docs/dev/DESIGN.md` — 実装設計書（DB・API・画面・状態遷移）
3. `docs/dev/MASTER_GUIDE.md` — 実装運用ガイド
4. `docs/dev/instructions_section2〜7` — 各領域の実装指示

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
- パッケージ管理: uv

### フロントエンド
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand
- React Router
- パッケージ管理: pnpm

### デスクトップ
- Tauri v2 (Rust)
- Python バックエンドはサイドカー

## ディレクトリ構成

```
apps/
├── api/              # FastAPI バックエンド
│   ├── app/
│   │   ├── core/           # 設定・DB・セキュリティ・i18n
│   │   ├── api/routes/     # REST API エンドポイント
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
│   │   ├── security/       # シークレット管理・サニタイズ・IAM
│   │   ├── integrations/   # Sentry・MCP・外部スキル・AI調査
│   │   ├── audit/          # 監査ログ
│   │   └── tests/          # テスト
│   └── alembic/            # マイグレーション
├── desktop/          # Tauri + React UI
│   ├── src-tauri/
│   └── ui/src/
│       ├── pages/          # 21 画面コンポーネント
│       ├── shared/         # 共通 API・型定義・hooks・UI
│       ├── features/       # 機能別モジュール
│       ├── entities/       # エンティティ
│       ├── widgets/        # ウィジェット
│       └── app/            # ルーティング・エントリ
├── edge/             # Cloudflare Workers (Proxy / Full)
│   ├── proxy/              # 方式A: リバースプロキシ
│   └── full/               # 方式B: Hono + D1 完全移植
└── worker/           # バックグラウンドワーカー
    ├── runners/            # タスク・Heartbeat 実行
    ├── executors/          # LLM・サンドボックス実行
    ├── sandbox/            # クラウドサンドボックス (Local/Docker/Workers)
    └── dispatchers/        # イベント配信
skills/
├── builtin/                # 組み込み Skill（6 個・システム保護）
└── templates/              # Skill テンプレート
plugins/                    # Plugin マニフェスト（9 Plugin）
extensions/                 # Extension マニフェスト（4 Extension）
packages/                   # 共有 NPM パッケージ
docs/                       # 利用者向けドキュメント
└── dev/                    # 開発者向けドキュメント
scripts/                    # 開発・運用スクリプト
examples/                   # サンプル・例
```

## コーディング規約

### Python
- ruff でフォーマット・リント
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

## 重要な設計原則

1. **名称は Zero-Employee Orchestrator で統一** — 旧名称 (CommandWeave / ZPCOS) は使わない
2. **YouTube は代表デモ** — 本体は汎用業務基盤として実装
3. **危険操作は承認前提** — 投稿・送信・削除・課金・権限変更は自律実行しない
4. **本体と拡張を分離** — Skill / Plugin / Extension の境界を明確に
5. **spec / plan / tasks を構造化保存** — 会話ログで済ませない
6. **状態遷移をコードに明示** — 状態機械で管理
7. **監査ログを後付けにしない** — 重要操作は最初から記録
8. **エージェント判断の透明性** — 推論トレースで「なぜその判断をしたか」を記録
9. **マルチエージェント協調の可視化** — 通信ログで委譲・フィードバック・エスカレーションを追跡

## DB スキーマ概要

主要テーブル: companies, users, departments, teams, agents, projects, goals,
tickets, ticket_threads, specs, plans, tasks, task_runs, artifacts, reviews,
approval_requests, heartbeat_policies, heartbeat_runs, budget_policies,
cost_ledgers, skills, plugins, extensions, tool_connections, tool_call_traces,
policy_packs, secret_refs, audit_logs, knowledge_store, change_detections,
agent_sessions, experience_memory, failure_taxonomy, iam_policies, ai_service_accounts,
multi_model_comparisons, brainstorm_sessions, conversation_memories,
agent_role_model_configs, feature_requests, custom_agent_roles, brain_dumps, daily_summaries

全テーブルに `id`, `company_id`, `created_at`, `updated_at` を基本カラムとして持つ。

## API エンドポイント

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
- `/models` — モデルカタログ管理（動的モデル管理 API）
- `/traces` — 推論トレース（エージェントの判断過程）
- `/communications` — エージェント間通信ログ
- `/monitor` — リアルタイム実行監視
- `/ws/events` — WebSocket リアルタイム
- `/knowledge` — ナレッジストア・変更検知
- `/mcp` — MCP サーバー（ツール・リソース・プロンプト）
- `/skills/external` — 外部スキル検索・インポート
- `/sentry` — Sentry連携（エラー統計・イベント）
- `/iam` — IAM（AIサービスアカウント管理）
- `/investigate` — AI調査（DB/ログ参照）
- `/companies/{id}/multi-model/compare` — マルチモデル比較
- `/companies/{id}/brainstorm` — 壁打ち（ブレインストーミング）セッション
- `/companies/{id}/conversation-memory` — 会話記憶（永続保管・検索）
- `/text/analyze` — テキスト分析（正確な文字数カウント）
- `/companies/{id}/role-models` — 役割別モデル設定
- `/companies/{id}/agents/by-role` — 役割指定エージェント追加
- `/companies/{id}/custom-roles` — カスタム役割管理
- `/companies/{id}/available-roles` — 利用可能な役割一覧
- `/companies/{id}/feature-requests` — 自然言語機能リクエスト
- `/hypotheses` — 仮説の並行検証
- `/sessions` — エージェントセッション管理
- `/config` — ランタイム設定管理（API キー・実行モード）

## ランタイム設定管理

API キーや実行モードを .env ファイルを直接編集せずに設定できる。

### 設定方法（3 通り）
1. **設定画面**: アプリの「設定」→「LLM API キー設定」
2. **CLI**: `zero-employee config set/get/list/delete/keys`
3. **.env ファイル**: 従来通り `apps/api/.env` を直接編集

### 優先順位
環境変数 > `~/.zero-employee/config.json` > `.env` > デフォルト値

### CLI コマンド
```
zero-employee config list              # 全設定値を表示
zero-employee config set <KEY> [VALUE] # 設定値を保存（VALUE省略時はプロンプト入力）
zero-employee config get <KEY>         # 設定値を取得
zero-employee config delete <KEY>      # 設定値を削除（デフォルトに戻す）
zero-employee config keys              # 設定可能なキーの一覧
```

### Config API
- `GET /api/v1/config` — 全設定値（機密値はマスク）
- `GET /api/v1/config/providers` — プロバイダー接続状態
- `PUT /api/v1/config` — 設定値の更新
- `PUT /api/v1/config/batch` — 一括更新
- `DELETE /api/v1/config/{key}` — 設定値の削除
- `GET /api/v1/config/keys` — 設定可能なキーの一覧

## 対応 LLM モデル（動的管理）

対応モデルは `apps/api/model_catalog.json` で一元管理される。
モデルの追加・削除・廃止・後継指定・コスト更新はこのファイルを編集するか、
Model Registry API (`/api/v1/models/*`) 経由で行う。
**コード変更なしにモデルを入れ替え可能。**

### 廃止モデルの自動フォールバック
各モデルに `deprecated` フラグと `successor`（後継モデルID）を設定可能。
廃止されたモデルが指定された場合、自動的に後継モデルに切り替わる。

### 実行モード別の推奨モデル（model_catalog.json で定義）
- **Quality**: 最高品質モデル（例: Claude Opus, GPT-5.4, Gemini 2.5 Pro）
- **Speed**: 高速応答モデル（例: Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash）
- **Cost**: 低コストモデル（例: Haiku, Mini, Flash Lite, DeepSeek）
- **Free**: 無料モデル（Gemini 無料枠, g4f, Ollama ローカル）
- **Subscription**: API キー不要（g4f 経由）

### Model Registry API
- `GET /api/v1/models` — 全モデル一覧
- `GET /api/v1/models/modes` — 実行モード別カタログ
- `GET /api/v1/models/health` — プロバイダー可用性チェック
- `GET /api/v1/models/deprecated` — 廃止モデル一覧
- `POST /api/v1/models/deprecate` — モデル廃止マーク
- `POST /api/v1/models/update-cost` — コスト情報更新
- `POST /api/v1/models/reload` — カタログ再読み込み

### Ollama ローカルモード
- Ollama にインストール済みのモデルは自動検出される
- 推奨: qwen3:8b, qwen3:32b, qwen3-coder:30b, deepseek-coder-v2, codellama, gemma2

## Ollama 統合 (vibe-local inspired)

[vibe-local](https://github.com/ochyai/vibe-local) のアーキテクチャを参考に、
クラウドAPI不要の完全ローカル動作モードを追加。

### 主要コンポーネント
- **`providers/ollama_provider.py`** — Ollama 直接HTTP接続（LiteLLM不要）
  - モデル自動検出・ヘルスチェック・モデルプル
  - ストリーミング対応・XML形式ツールコール抽出
  - SSRF 防止（プライベートIPバリデーション）
- **`providers/local_rag.py`** — ファイルベースベクトルDB
  - TF-IDF ベクトル化 + コサイン類似度（三角関数）
  - CJK（日本語・中国語）対応トークナイザー
  - JSON ファイルストレージ（外部DB不要）
- **`core/i18n.py`** — 国際化（日本語・英語・中国語）

### CLI コマンド
```
zero-employee serve              # API サーバーを起動
zero-employee config list        # 設定値の一覧表示
zero-employee config set <KEY>   # API キー等の設定（機密値はプロンプト入力）
zero-employee config get <KEY>   # 設定値の取得
zero-employee config delete <KEY> # 設定値の削除
zero-employee config keys        # 設定可能なキーの一覧
zero-employee local              # ローカルチャットモード
zero-employee local --model qwen3:8b --lang ja
zero-employee models             # インストール済みモデル一覧
zero-employee pull qwen3:8b      # モデルダウンロード
zero-employee db upgrade         # DB マイグレーション
zero-employee health             # ヘルスチェック
```

### API エンドポイント
- `/ollama/health` — Ollama ヘルスチェック
- `/ollama/models` — モデル一覧
- `/ollama/pull` — モデルダウンロード
- `/ollama/chat` — ダイレクトチャット
- `/ollama/rag/search` — ローカル RAG 検索
- `/ollama/rag/add` — ドキュメント追加

## Skill 管理 (v0.1)

### 自然言語スキル生成
- `POST /api/v1/registry/skills/generate` で自然言語からスキルを自動生成
- LLM ベース生成 + テンプレートフォールバック
- 自動安全性チェック（16 種類の危険パターン検出）

### システム保護スキル
以下の 6 つのビルトインスキルは `is_system_protected=True` で、削除・無効化不可:
- `spec-writer` — 仕様書生成
- `plan-writer` — 実行計画生成
- `task-breakdown` — タスク DAG 分解
- `review-assistant` — 品質レビュー
- `artifact-summarizer` — 成果物要約
- `local-context` — ローカルコンテキスト

### Skill/Plugin/Extension 管理 API
全エンティティで GET / POST / PATCH / DELETE 対応:
- `/registry/skills` — Skill CRUD + `POST /skills/generate` (自然言語生成)
- `/registry/plugins` — Plugin CRUD
- `/registry/extensions` — Extension CRUD

### サービス層
- **services/skill_service.py**: スキル CRUD・自然言語生成・安全性チェック・システム保護
- **services/registry_service.py**: Plugin/Extension CRUD・システム保護

## バックエンド補足モジュール

- **providers/model_registry.py**: 動的モデルレジストリ（model_catalog.json 読込・廃止自動フォールバック・コスト管理）
- **orchestration/reasoning_trace.py**: 推論トレース（エージェントの思考過程・判断理由の記録）
- **orchestration/agent_communication.py**: エージェント間通信ログ（委譲・フィードバック・エスカレーション）
- **orchestration/execution_monitor.py**: リアルタイム実行監視（WebSocket配信・アクティブタスク追跡）
- **repositories/**: DB 入出力の抽象化（BaseRepository + エンティティ別）
- **heartbeat/**: Heartbeat スケジューラ（9 種類の発火契機に対応）
- **policies/**: 承認ゲート（12 カテゴリの危険操作検出）＋自律実行境界
- **security/**: シークレット管理（マスキング・ローテーション支援）＋サニタイズ
- **tools/**: 外部ツール接続（MCP / Webhook / REST API / OAuth）
- **orchestration/knowledge_refresh.py**: Knowledge Pipeline（7 段階管理）
- **orchestration/artifact_bridge.py**: 工程間の成果物受け渡し

## v0.1 追加モジュール

### ナレッジストア & 変更検知
- **orchestration/knowledge_store.py**: ユーザー設定・ファイル権限・フォルダ位置の永続記憶 + 変更検知

### 仮説検証 & レビュー（※将来 Plugin として分離予定）
- **orchestration/hypothesis_engine.py**: マルチエージェントによる仮説の並行検証・エビデンス・クロスレビュー

### エージェントセッション
- **orchestration/agent_session.py**: コンテキスト永続化・idle/resume・ワーキングメモリ・DB永続化

### 統合モジュール (integrations/) — ※コア機能ではなく拡張機能として分類
以下は v0.1 ではコードベースに同梱されているが、将来 Extension/Skill として分離予定:
- **integrations/sentry_integration.py**: Sentry互換のエラー・パフォーマンス監視 → **Extension 候補**
- **integrations/mcp_server.py**: MCP サーバー → **Extension 候補**
- **integrations/external_skills.py**: 外部スキルインポート → **Extension 候補**
- **integrations/ai_investigator.py**: AI用DB/ログ調査ツール → **Skill 候補**

### IAM
- **security/iam.py**: 人間/AIアカウント分離・権限管理・認証情報保護

### サンドボックス
- **worker/app/sandbox/cloud_sandbox.py**: マルチモードサンドボックス（Local/Docker/Workers）

### コンテナ & デプロイ
- **Dockerfile**: Rootlessコンテナ（non-root UID 1000実行）
- **docker-compose.yml**: 全サービス一括起動
- **apps/edge/full/wrangler.toml**: Cloudflare Workers デプロイ設定

### フロントエンド追加画面
- **pages/PermissionsPage.tsx**: 権限管理ダッシュボード（ファイル権限・フォルダ位置・変更検知）
- **pages/AgentMonitorPage.tsx**: エージェント監視ダッシュボード（実行監視・セッション・仮説・エラー）

## 最新情報取得に関する制約

本システム内の AI エージェントは **Web 検索やリアルタイムインターネットアクセス機能を持たない**。
最新情報の取得が必要な場合は以下の方法で対応する:

1. **MCP / Tool Connection 経由** — 外部 API（ニュース API、検索 API 等）を Tool Connection として
   登録し、Skill から呼び出す（`tools/connector.py`）
2. **ローカル RAG** — 手動でドキュメントを追加し、RAG 検索で参照する
3. **Knowledge Pipeline** — 過去の実行結果から知識を蓄積・再利用する

モデルの可用性・最新性については Model Registry API のヘルスチェック機能で
プロバイダーの稼働状況を確認できる。

## 禁止事項

- Zero-Employee Orchestrator を YouTube 自動化ツールとして実装すること
- Skill / Plugin / Extension の境界を曖昧にすること
- 承認必須操作を黙って実行すること
- 監査ログなしで外部送信や権限変更を行うこと
- ローカル文脈アクセスを無制限権限で実装すること
