# Zero-Employee Orchestrator — Claude Code 開発ガイド

## プロジェクト概要

Zero-Employee Orchestrator は、自然言語で業務を定義し、複数 AI を役割分担させ、
人間の承認と監査可能性を前提に業務を実行・再計画・改善できる AI オーケストレーション基盤である。

## 参照優先順位

1. `Zero-Employee Orchestrator.md` — 最上位基準文書（思想・要件）
2. `DESIGN.md` — 実装設計書（DB・API・画面・状態遷移）
3. `MASTER_GUIDE.md` — 実装運用ガイド
4. `instructions_section2〜7` — 各領域の実装指示

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
│   │   ├── core/           # 設定・DB・セキュリティ
│   │   ├── api/routes/     # REST API エンドポイント
│   │   ├── api/ws/         # WebSocket
│   │   ├── api/deps/       # 依存性注入
│   │   ├── models/         # SQLAlchemy ORM モデル
│   │   ├── schemas/        # Pydantic DTO
│   │   ├── services/       # ビジネスロジック
│   │   ├── repositories/   # DB 入出力抽象化
│   │   ├── orchestration/  # DAG・Judge・状態機械・Knowledge・Artifact Bridge
│   │   ├── heartbeat/      # Heartbeat スケジューラ
│   │   ├── providers/      # LLM ゲートウェイ・g4f Provider
│   │   ├── tools/          # 外部ツール接続 (MCP/Webhook/API)
│   │   ├── policies/       # 承認ゲート・自律実行境界
│   │   ├── security/       # シークレット管理・サニタイズ
│   │   ├── audit/          # 監査ログ
│   │   └── tests/          # テスト
│   └── alembic/            # マイグレーション
├── desktop/          # Tauri + React UI
│   ├── src-tauri/
│   └── ui/src/
│       ├── pages/    # 19 画面コンポーネント
│       ├── shared/   # 共通 API・型定義・hooks・UI
│       ├── features/ # 機能別モジュール
│       └── app/      # ルーティング・エントリ
├── edge/             # Cloudflare Workers (Proxy / Full)
└── worker/           # バックグラウンドワーカー
    ├── runners/      # タスク・Heartbeat 実行
    ├── executors/    # LLM・サンドボックス実行
    └── dispatchers/  # イベント配信
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

## DB スキーマ概要

主要テーブル: companies, users, departments, teams, agents, projects, goals,
tickets, ticket_threads, specs, plans, tasks, task_runs, artifacts, reviews,
approval_requests, heartbeat_policies, heartbeat_runs, budget_policies,
cost_ledgers, skills, plugins, extensions, tool_connections, tool_call_traces,
policy_packs, secret_refs, audit_logs

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
- `/ws/events` — WebSocket リアルタイム

## 対応 LLM モデル（2026-03 時点）

### Quality モード
- anthropic/claude-opus-4-6
- openai/gpt-5.4
- gemini/gemini-2.5-pro

### Speed モード
- anthropic/claude-haiku-4-5-20251001
- openai/gpt-5-mini
- gemini/gemini-2.5-flash

### Cost モード
- anthropic/claude-haiku-4-5-20251001
- openai/gpt-5-mini
- gemini/gemini-2.5-flash-lite
- deepseek/deepseek-chat

### Free モード
- gemini/gemini-2.5-flash (Google AI Studio 無料枠)
- g4f/GeminiPro, g4f/Copilot, g4f/OpenaiChat, g4f/Claude, g4f/DeepInfra
- ollama/llama3.2, ollama/mistral, ollama/phi3

### Ollama ローカルモード（追加対応モデル）
- ollama/qwen3:8b, ollama/qwen3:32b — Qwen3（高品質推論）
- ollama/qwen3-coder:30b — Qwen3 Coder（コーディング特化）
- ollama/deepseek-coder-v2 — DeepSeek Coder V2
- ollama/codellama — Code Llama（Meta コード特化）
- ollama/gemma2 — Gemma 2（Google 軽量モデル）
- ※ Ollama にインストール済みのモデルは自動検出される

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
zero-employee local              # ローカルチャットモード
zero-employee local --model qwen3:8b --lang ja
zero-employee models             # インストール済みモデル一覧
zero-employee pull qwen3:8b      # モデルダウンロード
```

### API エンドポイント
- `/ollama/health` — Ollama ヘルスチェック
- `/ollama/models` — モデル一覧
- `/ollama/pull` — モデルダウンロード
- `/ollama/chat` — ダイレクトチャット
- `/ollama/rag/search` — ローカル RAG 検索
- `/ollama/rag/add` — ドキュメント追加

## バックエンド補足モジュール

- **repositories/**: DB 入出力の抽象化（BaseRepository + エンティティ別）
- **heartbeat/**: Heartbeat スケジューラ（9 種類の発火契機に対応）
- **policies/**: 承認ゲート（12 カテゴリの危険操作検出）＋自律実行境界
- **security/**: シークレット管理（マスキング・ローテーション支援）＋サニタイズ
- **tools/**: 外部ツール接続（MCP / Webhook / REST API / OAuth）
- **orchestration/knowledge_refresh.py**: Knowledge Pipeline（7 段階管理）
- **orchestration/artifact_bridge.py**: 工程間の成果物受け渡し

## 禁止事項

- Zero-Employee Orchestrator を YouTube 自動化ツールとして実装すること
- Skill / Plugin / Extension の境界を曖昧にすること
- 承認必須操作を黙って実行すること
- 監査ログなしで外部送信や権限変更を行うこと
- ローカル文脈アクセスを無制限権限で実装すること
