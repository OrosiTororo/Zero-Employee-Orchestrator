# Zero-Employee Orchestrator 設計書

> 作成日: 2026-03-08  
> 基準文書: `Zero-Employee Orchestrator.md`  
> 本書の役割: 実装判断に必要な構造を、AI コーディングエージェントが着手できる粒度まで整理した設計書

---

## 0. 本書の位置づけ

本書は、`Zero-Employee Orchestrator.md` を実装設計へ落とし込むための中核設計書である。  
思想・背景・改善要望の網羅は基準文書側に持たせ、本書では次を明確化する。

1. 何を本体に含めるか
2. 何を Skill / Plugin / Extension として切り出すか
3. MVP でどこまで作るか
4. どの順序で実装するか
5. AI エージェントがそのままコードに落とせる構造は何か

本書は README ではなく、実装・レビュー・分担・差し戻しの基準として使う。

---

## 1. システム定義

### 1.1 一文定義

Zero-Employee Orchestrator は、自然言語で業務を定義し、複数 AI を役割分担させ、人間の承認と監査可能性を前提に業務を実行・再計画・改善できる AI オーケストレーション基盤である。

### 1.2 目指す状態

- AI を単発チャットではなく、役割を持ったチームとして扱える
- spec / plan / tasks を中間成果物として保存できる
- 人間の最終承認を外さずに、実行部分の大半を自律化できる
- ローカル文脈、外部 API、認証情報、監査ログを一つの基盤で扱える
- 新しいモデルや業務機能を本体更新ではなく拡張で取り込める

### 1.3 利用者層

- 非エンジニアの実務者・経営者
- エンジニア・研究開発者
- 監査、承認、権限管理を必要とする組織利用者

---

## 2. 設計原則

1. **AI を組織として扱う**  
   単一エージェントではなく、計画・実行・検証・改善を役割分担したチーム構造を基本とする。

2. **人間の最終承認を外さない**  
   投稿、送信、課金、削除、権限変更などは必ず承認可能な構造にする。

3. **ブラックボックスを減らす**  
   誰が、何を、なぜ、どのモデル・Skill・権限で実行したかを可視化する。

4. **最新性は拡張で担保する**  
   本体は安定性重視、業務差分は Skill / Plugin / Extension で吸収する。

5. **ローカル文脈を重要資産として扱う**  
   ローカルファイル、業務データ、作業履歴を安全に扱えることを差別化の中心に置く。

6. **失敗時は停止だけでなく再計画できる**  
   Self-Healing、Re-Propose、Plan Diff を前提とする。

7. **汎用業務基盤として設計する**  
   YouTube は代表検証テーマの一つであり、本質は会社業務全体の実行基盤である。

---

## 3. 用語整理

### 3.1 Skill

単一タスクを実行する最小能力単位。  
プロンプト、手順、スクリプト、制約、利用ツールを含む。

例:
- 競合分析
- 台本生成
- ファイル整理
- ローカル文脈読解

### 3.2 Plugin

複数 Skill と補助機能をまとめた業務機能パッケージ。  
特定業務を成立させるためのまとまりとして配布・導入する。

例:
- 分身AI Plugin（ユーザーの判断基準を学習し代理行動）
- 秘書AI Plugin（ブリーフィング・AI組織との橋渡し）
- Discord / Slack / LINE Bot Plugin（チャットからの操作）
- YouTube 運用 Plugin
- リサーチ Plugin

### 3.3 Extension

本体の動作環境、UI、接続先、開発体験を拡張する仕組み。

例:
- MCP 接続
- OAuth 連携
- 通知機能
- VS Code 風 UI

### 3.4 実装境界

- 本体: 認証、権限、監査、実行制御、状態管理、可観測性
- Skill / Plugin: 業務特化ロジック
- Extension: 接続・UI・開発体験の拡張

---

## 4. 想定アーキテクチャ

Zero-Employee Orchestrator は 9 層構造を基本とする。

1. **User Layer**  
   GUI / CLI / TUI / チャット入力 / ダッシュボード

2. **Design Interview Layer**  
   目的整理、制約整理、Spec 化

3. **Task Orchestrator Layer**  
   計画生成、DAG 化、承認待ち、コスト推定、再計画

4. **Skill Layer**  
   Skill 実行、Skill Gap 検出、Skill 生成、業務別プラグイン実行

5. **Judge Layer**  
   Two-stage Detection、Cross-Model Judge、Policy Pack

6. **Re-Propose Layer**  
   差し戻し、Plan Diff、部分再実行、Self-Healing

7. **State & Memory Layer**  
   状態機械、履歴、成果物、失敗分類、経験知保存

8. **Provider Interface Layer**  
   LiteLLM Gateway、モデルカタログ、外部 API、OAuth、Webhook

9. **Registry Layer**  
   Skill / Plugin / Extension の公開、検索、導入、検証状態表示

---

## 5. 実行フロー

### 5.1 基本フロー

1. ユーザーが自然言語で目的を入力
2. Design Interview が不足情報を補完
3. Spec を生成し、制約・受け入れ条件を確定
4. Plan を生成し、工程・担当 AI・費用・権限を提示
5. ユーザーが承認または差し戻し
6. 承認後のみ Tasks に分解して実行
7. 実行中は進捗、ログ、成果物、失敗、再試行履歴を表示
8. Judge が品質・根拠・禁止事項を検査
9. 必要に応じて Re-Propose / Self-Healing
10. 完了後、成果物・判断理由・履歴を保存

### 5.2 中間成果物

すべての案件は原則として以下の単位で保存する。

```text
project/
├─ spec/
├─ plan/
├─ tasks/
├─ outputs/
├─ review/
└─ logs/
```

### 5.3 イベント駆動実行

Webhook、定期実行、外部イベント起動にも対応する。  
ただし、起動条件・自動実行範囲・承認必須工程・失敗時停止条件は明示する。

---

## 6. MVP スコープ

### 6.1 MVP の目的

Zero-Employee Orchestrator の核である、

- 自然言語入力
- Design Interview
- spec / plan / tasks 保存
- 承認付き実行
- Judge
- 再提案
- ローカル文脈活用
- 監査ログ

を一連で成立させる。

### 6.2 MVP 必須機能

- 認証とローカルセッション管理
- Design Interview
- Spec Writer
- Task Orchestrator
- Cost Guard
- Quality SLA
- Skill 実行基盤
- Judge 基盤
- Re-Propose / Plan Diff
- State Machine
- Experience Memory
- Failure Taxonomy
- Local Context Skill
- 基本ダッシュボード
- 主要 API と監査ログ

### 6.3 MVP で対象外にしてよいもの

- Marketplace のフル機能
- 外部公開向け大規模 Registry 運営機能
- 複雑なマルチテナント課金
- 高度な組織ガバナンスの完全実装
- ロボット連携や大規模外部操作の全面対応

---

## 7. 権限モデル

最低限、以下のロールを持つ。

- **Owner**: 全権限、予算・承認・公開設定
- **Admin**: 運用管理、接続管理、監査閲覧
- **User**: 実行依頼、成果物確認、限定承認
- **Auditor**: 閲覧中心、監査ログ・履歴確認
- **Developer**: Skill / Plugin / Extension 開発と検証

承認が必要な操作はロールと操作種別の組み合わせで定義する。

---

## 8. データとメモリ方針

### 8.1 保存対象

- 会話と意思決定履歴
- spec / plan / tasks
- 成果物メタデータ
- 監査ログ
- 失敗分類と再試行履歴
- 改善知識と成功要因
- 接続設定メタデータ

### 8.2 厳格管理対象

- 生の認証情報
- 機微な個人情報
- 不要な全文保存
- 公開共有に向かない内部文書

### 8.3 方針

- 保存前にサニタイズする
- 共有可能な改善知識と機密情報を分離保存する
- 実行根拠と成果物の対応関係を追跡可能にする

---

## 9. 実行環境

### 9.1 基本方針

- ローカルアプリを中心にする
- 必要に応じてクラウド API を併用する
- 本体は Tauri + フロントエンド + ローカルバックエンド構成を基本候補とする

### 9.2 役割分担

**ローカル側**
- ファイルアクセス
- セッションとキャッシュ
- UI
- 状態管理
- 一部実行制御

**クラウド側 / 外部側**
- LLM API
- 外部 SaaS
- OAuth 接続先
- 通知・配信・投稿対象

### 9.3 技術スタック初期案

- Desktop: Tauri
- Frontend: React / Next.js 系
- Backend: Python FastAPI
- Local DB: SQLite
- Queue / Worker: Python ベース軽量実装から開始
- LLM Gateway: LiteLLM 互換層
- 認証: OAuth + ローカルセッション

### 9.4 Cloudflare Workers デプロイ

ローカル実行に加え、Cloudflare Workers 上での実行にも対応する。  
Workers デプロイは以下の2方式を提供する。

| | 方式 A: Proxy | 方式 B: Full Workers |
|---|---|---|
| ディレクトリ | `apps/edge/proxy/` | `apps/edge/full/` |
| 概要 | 既存 FastAPI の前段にリバースプロキシ配置 | 主要 API を Hono + D1 でエッジ上に完全再実装 |
| データベース | 不要（既存 DB を利用） | D1 (SQLite 互換) |
| 認証 | バックエンドに委譲 | JWT (jose) |
| フレームワーク | Hono | Hono + jose |
| 外部サーバー | 必要 | 不要 |

方式 B (Full Workers) では以下の API をエッジ上で提供する。

- 認証 (register / login / me)
- 会社管理 (CRUD / dashboard)
- チケット管理 (一覧 / 作成 / 詳細)
- エージェント管理 (一覧 / 作成 / 一時停止 / 再開)
- タスク管理 (作成 / 開始 / 完了)
- 承認管理 (一覧 / 承認 / 却下)
- Spec / Plan 管理 (作成 / 詳細 / 承認)
- 監査ログ (一覧 / フィルタ)
- 予算管理 (ポリシー作成 / コスト一覧)
- プロジェクト管理 (CRUD)
- レジストリ (Skills / Plugins / Extensions 検索)
- 成果物管理 (一覧 / 作成 / 詳細)
- Heartbeat (ポリシー作成 / 実行履歴)
- レビュー (作成 / 一覧 / 詳細)
- ヘルスチェック

フロントエンドは Cloudflare Pages にデプロイ可能。  
GitHub Actions による手動デプロイ (`.github/workflows/deploy-workers.yml`) にも対応する。

---

## 10. AI エージェントが着手できる実装前提仕様

### 10.1 DB スキーマ初期案

主要テーブルは以下を起点にする。

- companies
- workspaces
- users
- roles
- agents
- teams
- skills
- plugins
- extensions
- projects
- tickets
- specs
- plans
- tasks
- task_dependencies
- executions
- outputs
- reviews
- approvals
- budgets
- audit_logs
- provider_connections
- credentials_meta
- memories
- failure_records
- heartbeat_runs
- registry_packages
- registry_versions
- installs

### 10.2 API エンドポイント初期群

#### 認証・セッション
- `POST /api/auth/login`
- `GET /api/auth/status`
- `POST /api/auth/logout`
- `POST /api/auth/connect/{service}`
- `GET /api/auth/connections`
- `DELETE /api/auth/disconnect/{service}`

#### 組織・会社
- `GET /api/companies`
- `POST /api/companies`
- `GET /api/org-chart`
- `POST /api/teams`
- `POST /api/agents`

#### spec / plan / tasks
- `POST /api/interview/start`
- `POST /api/interview/respond`
- `POST /api/interview/finalize`
- `POST /api/specs`
- `POST /api/plans`
- `GET /api/plans/{id}`
- `POST /api/plans/{id}/approve`
- `POST /api/plans/{id}/repropose`
- `GET /api/plans/{id}/diff`
- `POST /api/tasks`
- `GET /api/tasks/{id}`
- `POST /api/tasks/{id}/transition`

#### 実行・レビュー
- `POST /api/orchestrate`
- `GET /api/orchestrate/{id}`
- `GET /api/orchestrate/{id}/cost`
- `POST /api/orchestrate/{id}/self-heal`
- `GET /api/orchestrate/{id}/heal-history`
- `POST /api/reviews`
- `POST /api/approvals`

#### Skills / Plugins / Extensions (v0.1 実装済み)
- `GET /api/v1/registry/skills` — Skill 一覧（status, skill_type, include_disabled フィルタ）
- `GET /api/v1/registry/skills/{id}` — Skill 個別取得
- `POST /api/v1/registry/skills` — Skill 作成
- `POST /api/v1/registry/skills/install` — Skill インストール
- `PATCH /api/v1/registry/skills/{id}` — Skill 更新（保護スキル無効化拒否）
- `DELETE /api/v1/registry/skills/{id}` — Skill 削除（保護スキル削除拒否）
- `POST /api/v1/registry/skills/generate` — 自然言語スキル生成（安全性チェック付き）
- `POST /api/skills/execute` — Skill 実行
- `GET /api/skills/gaps` — Skill ギャップ検出
- `GET /api/v1/registry/plugins` — Plugin 一覧
- `GET /api/v1/registry/plugins/{id}` — Plugin 個別取得
- `POST /api/v1/registry/plugins` — Plugin 作成
- `PATCH /api/v1/registry/plugins/{id}` — Plugin 更新
- `DELETE /api/v1/registry/plugins/{id}` — Plugin 削除（保護プラグイン削除拒否）
- `GET /api/v1/registry/extensions` — Extension 一覧
- `GET /api/v1/registry/extensions/{id}` — Extension 個別取得
- `POST /api/v1/registry/extensions` — Extension 作成
- `PATCH /api/v1/registry/extensions/{id}` — Extension 更新
- `DELETE /api/v1/registry/extensions/{id}` — Extension 削除（保護拡張削除拒否）

#### Registry / Audit / Settings
- `GET /api/registry/search`
- `POST /api/registry/publish`
- `POST /api/registry/install`
- `GET /api/registry/popular`
- `GET /api/audit/logs`
- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/health`

#### ランタイム設定管理 (v0.1 実装済み)
- `GET /api/v1/config` — 全設定値（機密値はマスク済み）
- `GET /api/v1/config/providers` — プロバイダー接続状態
- `PUT /api/v1/config` — 設定値の更新（API キー・実行モード等）
- `PUT /api/v1/config/batch` — 一括更新
- `DELETE /api/v1/config/{key}` — 設定値の削除（デフォルトに戻す）
- `GET /api/v1/config/keys` — 設定可能なキーの一覧

### 10.3 状態遷移（実装済み）

#### Ticket
- draft → open → interviewing → planning → ready → in_progress → review → done → closed
- rework, blocked, cancelled は各状態から遷移可能
- reopened: done / closed / cancelled から再開可能

#### Task
- pending → ready → running → succeeded → verified → archived
- running → failed → retrying → running
- running → awaiting_approval → running
- running → blocked → ready
- rework_requested → ready / running

#### Approval
- requested → approved / rejected / expired / cancelled
- approved → executed
- rejected → superseded

#### Agent
- provisioning → active → busy → paused → archived
- active → budget_blocked / policy_blocked / error
- error → active / paused

### 10.4 画面一覧初期案

- Sign In
- Workspace Selector
- Dashboard
- Interview / Spec Editor
- Plan Review / Diff
- Task Board / Execution Timeline
- Output / Review
- Skill / Plugin / Extension Manager
- Registry / Marketplace
- Audit Log Viewer
- Settings / Connections / Policies

### 10.5 ディレクトリ構成（実装済み）

```text
Zero-Employee-Orchestrator/
├─ apps/
│  ├─ api/                    # FastAPI バックエンド
│  │  ├─ app/
│  │  │  ├─ core/             # 設定・DB・セキュリティ
│  │  │  ├─ api/routes/       # REST API エンドポイント
│  │  │  ├─ api/ws/           # WebSocket
│  │  │  ├─ api/deps/         # 依存性注入
│  │  │  ├─ models/           # SQLAlchemy ORM モデル
│  │  │  ├─ schemas/          # Pydantic DTO
│  │  │  ├─ services/         # ビジネスロジック
│  │  │  ├─ repositories/     # DB 入出力抽象化
│  │  │  ├─ orchestration/    # DAG・Judge・状態機械・Knowledge・Memory
│  │  │  ├─ heartbeat/        # Heartbeat スケジューラ
│  │  │  ├─ providers/        # LLM ゲートウェイ・Ollama・g4f・RAG
│  │  │  ├─ tools/            # 外部ツール接続（MCP/Webhook/API/CLI）
│  │  │  ├─ policies/         # 承認ゲート・自律実行境界
│  │  │  ├─ security/         # シークレット管理・サニタイズ・IAM
│  │  │  ├─ integrations/     # Sentry・MCP Server・外部スキル（※拡張機能）
│  │  │  ├─ audit/            # 監査ログ
│  │  │  └─ tests/            # テスト
│  │  └─ alembic/             # DB マイグレーション
│  ├─ desktop/                # Tauri + React UI
│  │  ├─ src-tauri/           # Rust (Tauri v2)
│  │  └─ ui/src/
│  │     ├─ pages/            # 23 画面コンポーネント
│  │     ├─ features/         # 機能別モジュール
│  │     ├─ shared/           # 共通 API・型・hooks・UI
│  │     └─ app/              # ルーティング・エントリ
│  ├─ edge/                   # Cloudflare Workers
│  └─ worker/                 # バックグラウンドワーカー
│     ├─ runners/             # タスク・Heartbeat 実行
│     ├─ executors/           # LLM・サンドボックス実行
│     ├─ dispatchers/         # イベント配信
│     └─ sandbox/             # 隔離実行環境
├─ skills/builtin/            # 組み込み Skill
├─ plugins/                   # Plugin 定義
├─ extensions/                # Extension 定義
├─ packages/                  # 共有パッケージ
├─ docs/                      # ドキュメント
├─ scripts/                   # 開発・デプロイスクリプト
└─ docker/                    # Docker 設定
```

---

## 11. 実装順序

### Phase 0: 開発基盤
- モノレポ構成
- Python / Node / Tauri 開発基盤
- Lint / Format / Test / CI
- 環境変数とシークレット運用

### Phase 1: 認証と会社スコープ
- ローカル認証
- OAuth 接続基盤
- workspace / company スコープ

### Phase 2: Design Interview と spec
- Interview セッション
- Spec Writer
- Spec 保存と編集

### Phase 3: Plan と承認
- Plan 生成
- Cost Guard
- Quality SLA
- 承認フロー
- Plan Diff

### Phase 4: Task 実行基盤
- Task 分解
- 状態機械
- 実行履歴
- 進捗可視化

### Phase 5: Judge と再計画
- Two-stage Detection
- Cross-Model Judge
- Re-Propose
- Self-Healing
- Failure Taxonomy

### Phase 6: Skill / Local Context
- Skill 実行基盤
- Skill Gap 検出
- Local Context Skill
- Experience Memory

### Phase 7: UI 強化
- ダッシュボード
- 実行タイムライン
- 監査画面
- Registry UI

### Phase 8: Registry / 共有
- パッケージ化
- インストール
- バージョン管理
- 検証状態表示

### Phase 9: 高度化
- Heartbeat
- Goal Alignment
- Ticket / Org Chart 中心運用
- Multi-company 対応
- BYOA/BYOAgent 的な接続性強化

---

## 12. テスト観点

### 12.1 単体テスト
- Interview ロジック
- Spec Writer
- Cost Guard
- Policy Pack
- Failure Taxonomy
- Plan Diff
- Skill Gap 検出

### 12.2 結合テスト
- interview → spec → plan → approval → execute
- Skill 実行 → Judge → Re-Propose
- Local Context 読み込み → 成果物生成

### 12.3 E2E テスト
- GUI から自然言語入力して最終成果物承認まで通す
- 失敗時に Self-Healing が発火するか
- 監査ログが一貫して保存されるか

### 12.4 セキュリティテスト
- 権限逸脱
- 不正接続
- シークレット露出
- 禁止操作の事前検知

### 12.5 LLM 特有テスト
- ハルシネーション抑制
- 根拠の弱い回答の検出
- 差し戻し時の再計画品質
- モデル変更時の劣化検知

---

## 13. 実装上の重要判断

1. YouTube は検証テーマであって本体定義ではない  
2. 本体は業務 OS、個別業務は Skill / Plugin で表現する  
3. 高速開発のために MVP では SQLite 中心でよい  
4. ただし状態機械、監査ログ、承認フローは最初から入れる  
5. 自律実行の境界は厳格にし、危険操作は明示承認を必須にする  
6. Section 2〜7 の実装指示群は、本書の構造に従って再利用できる状態で維持する

---

## 14. 本書と基準文書の関係

- `docs/Zero-Employee Orchestrator.md`: 思想、要望、背景、改善案、全体構想の基準
- `docs/dev/DESIGN.md`: 実装設計の基準
- `docs/dev/MASTER_GUIDE.md`: AI エージェントへの実行順序・参照関係・分担の基準

本書は基準文書を要約するものではなく、実装に必要な構造を明文化した派生設計書である。
