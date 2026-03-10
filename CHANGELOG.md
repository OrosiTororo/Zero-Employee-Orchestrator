# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [v0.1] - 2026-03-10 — Platform v0.1 (Consolidated Release)

### Added

- **ナレッジストア — ユーザー設定・ファイル権限の永続記憶** (`orchestration/knowledge_store.py`)
  - ファイル/フォルダの操作権限記憶（計画時に再度聞かない）
  - 業務資料フォルダの場所記憶
  - ユーザー設定・好みの永続化
  - 変更検知（前回の情報との差分検出・通知）
  - Knowledge API（`/knowledge/*`）— 記憶・検索・変更確認
- **ログイン不要の匿名セッション**
  - `POST /auth/anonymous-session` で即座に利用開始
  - 後からアカウント紐付け（`POST /auth/link-account`）
  - ログインすると複数デバイスでの状態共有が可能
  - フロントエンド: 「ログインせずに始める」ボタン追加
- **Webダッシュボード — エージェント監視** (`pages/AgentMonitorPage.tsx`)
  - ブラウザからリアルタイムでエージェント状態を監視
  - 実行中タスク・セッション・仮説検証・エラー監視の4タブ
  - 5秒自動リフレッシュ
  - Sentry連携のエラー統計表示
- **権限管理ダッシュボード** (`pages/PermissionsPage.tsx`)
  - ファイル/フォルダ権限の設定UI
  - 業務フォルダ位置の登録UI
  - 変更検知の確認UI
- **サンドボックス環境** (`worker/app/sandbox/cloud_sandbox.py`)
  - ローカル実行・Docker実行・Cloudflare Workers実行のマルチモード
  - ローカルコードの直接編集（権限チェック付き）
  - Workers上でのJavaScript/TypeScript実行
  - Cloudflare Workersへのワンクリックデプロイ
- **Rootlessコンテナ対応** (`Dockerfile`, `docker-compose.yml`)
  - root権限なしでコンテナ上で動作
  - non-root ユーザー (UID 1000) で実行
  - Docker Compose で全サービス一括起動
- **外部スキルインポート** (`integrations/external_skills.py`)
  - GitHub Agent Skills リポジトリからの検索・インポート
  - skills.sh プラットフォームからの検索・インポート
  - OpenClaw / Claude Code 形式のスキル変換
  - 任意のGitリポジトリからのマニフェスト取得
  - `POST /skills/external/search` / `POST /skills/external/import`
- **MCP サーバー** (`integrations/mcp_server.py`)
  - Model Context Protocol 準拠のサーバー実装
  - 8つの組み込みツール（チケット・タスク・スキル・ナレッジ・監査・監視・仮説検証）
  - 4つのリソース（ダッシュボード・エージェント・スキル・ナレッジ）
  - 2つのプロンプトテンプレート
  - MCP API（`/mcp/*`）
- **Cloudflareデプロイ対応**
  - 既存の `apps/edge/full/` Workers アプリ
  - `deploy_to_workers()` メソッドでワンクリックデプロイ
  - wrangler.toml 自動生成
- **AI調査ツール** (`integrations/ai_investigator.py`)
  - AIがログ・DBを参照して調査を完結
  - 安全なSELECTのみのDB読み取りクエリ
  - 監査ログ検索・エラーパターン分析・タスク実行履歴
  - システムメトリクス取得
  - SQLインジェクション防止（禁止キーワード・SELECT文のみ）
  - Investigation API（`/investigate/*`）
- **Sentry連携** (`integrations/sentry_integration.py`)
  - Sentry SDKとの連携（SDKがない場合はビルトインイベントストア）
  - 例外キャプチャ・メッセージキャプチャ・パフォーマンストランザクション
  - エラー統計・イベント一覧
  - アラートコールバック機能
  - Sentry API（`/sentry/*`）
- **人間/AIアカウント分離（IAM）** (`security/iam.py`)
  - AIエージェント専用サービスアカウント
  - 人間用・AI用で異なるスコープの権限管理
  - AIに禁止された権限（シークレット読取・管理者・承認）の自動除外
  - 認証情報ファイルの保護（owner read only パーミッション）
  - IAM API（`/iam/*`）
- **仮説の並行検証エンジン** (`orchestration/hypothesis_engine.py`)
  - マルチエージェントによる仮説検証とレビューのループ
  - エビデンスの支持/反証スコア計算
  - クロスレビューによるコンセンサス判定
  - 仮説の状態管理（提案→調査→エビデンス→レビュー→確認/反証）
  - Hypothesis API（`/hypotheses/*`）
- **エージェントセッション管理** (`orchestration/agent_session.py`)
  - コンテキストを保持したまま複数ラウンドのやり取り
  - idle状態での待機（コンテキスト保持）と復帰
  - ワーキングメモリ（セッション内の一時記憶）
  - DB永続化とインメモリのハイブリッド
  - Session API（`/sessions/*`）

### Changed

- `core/config.py`: SENTRY_DSN, SANDBOX_MODE, CLOUDFLARE_ACCOUNT_ID, CREDENTIAL_DIR 設定追加
- `main.py`: 新モデル（knowledge_store, agent_session, iam）のインポート追加、Sentry/MCP初期化追加
- `api/routes/__init__.py`: knowledge, platform ルーター追加
- `api/routes/auth.py`: 匿名セッション・アカウント紐付け・オプション認証追加
- `shared/hooks/use-auth.ts`: isAnonymous状態・startAnonymous/linkAccount メソッド追加
- `app/router.tsx`: PermissionsPage, AgentMonitorPage ルート追加
- `shared/ui/Layout.tsx`: サイドバーにエージェント監視・権限管理ナビ追加
- `pages/LoginPage.tsx`: 「ログインせずに始める」ボタン追加

- **外部ツール連携強化** (`tools/connector.py`)
  - CLI ツール接続タイプ追加（gws / gh / aws / gcloud / az 等の CLI ツールに対応）
  - gRPC・GraphQL 接続タイプ追加
  - サービスアカウント認証タイプ追加
- **Plugin の GitHub インポート機能** (`integrations/external_skills.py`)
  - GitHub リポジトリからプラグインを直接検索・インポート（`topic:zeo-plugin`）
  - コミュニティプラグインレジストリからの検索・インポート
  - `POST /api/v1/registry/plugins/search-external` — 外部プラグイン検索
  - `POST /api/v1/registry/plugins/import` — GitHub からプラグインインポート
  - ユーザーがプラグインを共有・公開し、開発者の追加作業なしで外部サービス連携が可能
- **ドキュメント多言語化** (USER_GUIDE.md, README.md)
  - USER_GUIDE.md: 日本語・英語・中国語の3言語対応
  - README.md: Releases セクションを非エンジニア向けに3言語で解説
  - ダウンロードファイルの選び方ガイドを追加
- **レガシーファイル移行**
  - `ZPCOS_FEATURES_AND_IMPROVEMENTS.md` の有用なアイデアを既存ドキュメントに統合
  - メタスキル概念・セキュリティ自己テスト・iPaaS 連携等のアイデアを DESIGN.md / FEATURES.md に反映
  - レガシーファイル削除

### Changed

- 全ドキュメントのバージョン表記を v0.1 に統一
- `CHANGELOG.md`: 全リリースを v0.1 として統合
- `docs/FEATURES.md`: 外部ツール連携・コミュニティプラグインセクション追加
- `docs/FEATURE_BOUNDARY.md`: コミュニティプラグイン共有の方針追加
- `ABOUT.md`: v0.1 表記統一
- `docs/OVERVIEW.md`: v0.1 表記統一

## [0.5.0] - 2026-03-10 — Skills Management v0.1

### Added

- **自然言語スキル生成エンジン** (`services/skill_service.py`)
  - 自然言語でスキルの機能を説明するだけで、マニフェスト (skill.json) と実行コード (executor.py) を自動生成
  - LLM ベース生成 + テンプレートベースフォールバック（LLM 不可時でも動作保証）
  - 生成コードの自動安全性チェック（16 種類の危険パターン検出）
  - 安全性レポート生成（risk_level: low/medium/high、権限要件、外部接続検出）
  - `POST /api/v1/registry/skills/generate` エンドポイント
- **Skill / Plugin / Extension 完全 CRUD API**
  - 全エンティティで GET (一覧・個別) / POST (作成) / PATCH (更新) / DELETE (削除) 対応
  - slug ベースの重複チェック
  - 有効/無効の切り替え（`enabled` フラグ）
  - フィルタリング: status, skill_type, include_disabled
- **システム保護スキル機能** (`is_system_protected`)
  - システム動作に必須な 6 つのビルトインスキルを保護
    - spec-writer, plan-writer, task-breakdown, review-assistant, artifact-summarizer, local-context
  - 保護スキルの削除を API レベルで拒否（HTTP 403）
  - 保護スキルの無効化を API レベルで拒否（HTTP 403）
  - アプリケーション起動時にシステムスキルの自動登録・保護フラグ設定
- **Plugin / Extension 管理サービス** (`services/registry_service.py`)
  - Plugin: 完全 CRUD + システム保護 + 有効/無効切替
  - Extension: 完全 CRUD + システム保護 + 有効/無効切替
  - 保護 Plugin/Extension の削除・無効化拒否
- **フロントエンド スキル管理 UI** (`SkillsPage.tsx`)
  - API 連携によるスキル一覧表示（リアルタイム取得）
  - スキルの有効/無効切替トグル
  - スキルの削除（システム保護スキルは UI レベルでもロック表示）
  - システム保護バッジ表示
  - 検索フィルタ（名前・説明・slug）
- **フロントエンド スキル生成 UI** (`SkillCreatePage.tsx`)
  - 自然言語入力エリア（10-5000 文字、文字数カウンター）
  - 安全性チェック結果の視覚表示（合格/不合格、リスクレベル表示）
  - 生成されたマニフェスト (JSON) とコード (Python) のプレビュー
  - 安全性チェック合格後の「スキル登録」ボタン
  - 安全性レポート詳細表示
- **フロントエンド プラグイン管理 UI** (`PluginsPage.tsx`)
  - API 連携による一覧表示
  - 新規プラグイン追加フォーム
  - 有効/無効切替・削除（保護プラグインはロック表示）
  - 検索フィルタ

### Changed

- **Skill / Plugin / Extension モデル** (`models/skill.py`)
  - `is_system_protected` カラム追加（Boolean, default=False）
  - `enabled` カラム追加（Boolean, default=True）
  - `generated_code` カラム追加（Skill のみ、Text）
  - slug に `unique=True` 制約追加
- **レジストリ API** (`api/routes/registry.py`)
  - 基本的な list/install のみ → 完全 CRUD + 自然言語生成に全面書き換え
  - サービス層経由に変更（直接 SQLAlchemy → services.skill_service / registry_service）
  - 適切な HTTP ステータスコード（201 Created, 403 Forbidden, 404 Not Found, 409 Conflict）
- **レジストリスキーマ** (`schemas/registry.py`)
  - `SkillUpdate`, `PluginUpdate`, `ExtensionUpdate` 追加
  - `SkillGenerateRequest`, `SkillGenerateResponse` 追加
  - `RegistryDeleteResponse` 追加
  - 全 Read スキーマに `is_system_protected`, `enabled` フィールド追加
- **アプリケーション起動** (`main.py`)
  - 起動時にシステム必須スキルの自動登録処理を追加

## [0.4.0] - 2026-03-09

### Added

- **AI Avatar Plugin（分身AI）** (`plugins/ai-avatar/`)
  - ユーザーの判断基準・文体・価値観を学習してプロファイル構築
  - Judge Layer との連携（ユーザーの判断パターンをカスタムルールとして提供）
  - 代理レビュー・文体再現・承認パターン学習
  - ユーザーのプロファイルは暗号化してローカル保存
- **AI Secretary Plugin（秘書AI）** (`plugins/ai-secretary/`)
  - 朝のブリーフィング（承認待ち・進行中タスク・今日の予定）
  - 次のアクション提案（緊急度・重要度に基づく推奨順序）
  - 進捗サマリー・リマインド・委任ルーティング
  - Discord / Slack / LINE Bot Plugin と連携したブリーフィング配信
- **LINE Bot Plugin** (`plugins/line-bot/`)
  - LINE Messaging API 経由でチケット作成・進捗確認・承認操作
  - Flex Message による承認ダイアログ
  - リッチメニューによるクイック操作

### Changed

- **Discord Bot Plugin** を v0.2.0 に更新
  - スレッド内対話・ブリーフィング配信・インタラクティブボタン追加
  - 秘書AI / 分身AI Plugin との連携機能追加
  - `/zeo` スラッシュコマンド体系を定義
- **Slack Bot Plugin** を v0.2.0 に更新
  - スレッド内対話・ブリーフィング配信・Block Kit インタラクション追加
  - 秘書AI / 分身AI Plugin との連携機能追加
  - `/zeo` Slash Command 体系を定義
- **ドキュメント全面更新**
  - `USER_GUIDE.md`: LLM 接続方法の推奨順位を修正（Gemini 無料 API / Ollama を優先推奨）、分身AI・秘書AI・チャット連携の説明追加、FAQ 更新
  - `README.md`: 新機能（分身AI・秘書AI・チャット連携）を日本語・英語・中文セクションに追加、ディレクトリ構成更新
  - `ABOUT.md`: 分身AI・秘書AI・チャット連携のセクション追加、LLM 推奨を最新化
  - `docs/FEATURES.md`: Plugin / Extension 一覧を詳細テーブルに更新、追加機能セクション新設
  - `docs/OVERVIEW.md`: 外部ツール連携セクション更新、分身AI・秘書AI の説明追加
  - `docs/FEATURE_BOUNDARY.md`: AI エージェント拡張 Plugin・チャットツール連携 Plugin セクション追加
  - `DESIGN.md`: Plugin 例に分身AI・秘書AI・チャット Bot を追加

## [0.3.0] - 2026-03-09

### Added

- **Dynamic Model Registry** (`providers/model_registry.py`)
  - `model_catalog.json` による LLM モデルの外部設定ファイル管理
  - モデルの追加・削除・廃止・後継指定がコード変更なしで可能
  - 廃止モデルの自動フォールバック（successor 指定で後継モデルに自動切替）
  - プロバイダーヘルスチェック（API 可用性の定期確認）
  - コスト情報の動的更新
- **Model Registry API** (`/api/v1/models/*`)
  - モデル一覧・モード別カタログ・プロバイダーヘルスチェック
  - モデル廃止マーク・コスト更新・カタログ再読み込み
- `model_catalog.json` — モデルカタログ定義ファイル（全モデル・モード・品質SLA）
- **Observability — 推論トレース・通信ログ・実行監視**
  - `orchestration/reasoning_trace.py` — エージェントの推論過程を段階的に記録（19種類のステップ・4段階の確信度）
  - `orchestration/agent_communication.py` — マルチエージェント間の全通信を記録（18種類のメッセージ・スレッド管理）
  - `orchestration/execution_monitor.py` — リアルタイム実行監視・WebSocket配信
  - `api/routes/observability.py` — Observability API（推論トレース・通信ログ・監視ダッシュボード）
  - フロントエンド TypeScript 型定義（ReasoningTrace, AgentMessage, ActiveExecution 等）

### Changed

- `gateway.py`: ハードコードされたモデルカタログを ModelRegistry からの動的読み込みに変更
- `cost_guard.py`: コストテーブルを ModelRegistry から動的生成するように変更
- `quality_sla.py`: 品質モード別モデルリストを ModelRegistry から動的読み込みに変更
- `docs/FEATURES.md`: 旧モデル名修正、動的管理の説明追加、Observabilityセクション追加
- `CLAUDE.md`: ハードコードモデルリスト → 動的管理、設計原則にエージェント透明性を追加

## [0.2.0] - 2026-03-09

### Changed

- 古い LLM モデル参照をすべて最新版に更新
  - g4f_provider.py: gpt-4o → gpt-5.4, gpt-4o-mini → gpt-5-mini, claude-haiku-4-5 → claude-haiku-4-5-20251001
  - cost_guard.py: claude-haiku-4-5 → claude-haiku-4-5-20251001
  - quality_sla.py: claude-haiku-4-5 → claude-haiku-4-5-20251001
  - docs/BUILD_GUIDE.md: 全コスト表・品質モード設定を最新モデルに更新
- DESIGN.md: 状態遷移を実装済みの定義に更新、ディレクトリ構成を実際のコードベースに同期

### Added

- リポジトリ層 (`repositories/`)
  - `base.py` — 汎用 CRUD リポジトリ基盤 (BaseRepository)
  - `ticket_repository.py` — チケット・スレッド DB 操作
  - `audit_repository.py` — 監査ログ専用リポジトリ (append-only)
- Heartbeat モジュール (`heartbeat/`)
  - `scheduler.py` — Heartbeat 発火契機 (9 種類)・実行管理・アクション記録
- ポリシーモジュール (`policies/`)
  - `approval_gate.py` — 危険操作の自動検出と承認要求 (12 カテゴリ)
  - `autonomy_boundary.py` — 自律実行可能/承認必須の境界判定
- セキュリティモジュール (`security/`)
  - `secret_manager.py` — 認証情報の安全な保管・マスキング・ローテーション支援
  - `sanitizer.py` — 保存/共有時のシークレット値・個人情報の自動マスキング
- ツール接続モジュール (`tools/`)
  - `connector.py` — MCP/Webhook/REST API 等の外部ツール接続管理
- オーケストレーション拡張 (`orchestration/`)
  - `knowledge_refresh.py` — Knowledge Pipeline (7 段階)・知識の分離保存 (5 種類)
  - `artifact_bridge.py` — 工程間の成果物受け渡し・バージョン管理
- フロントエンド型定義 (`shared/types/index.ts`)
  - バックエンドスキーマ §38 に対応する全エンティティの TypeScript 型

## [0.1.0] - 2026-03-09

### Added

- 9 層アーキテクチャの初期実装
  - User Layer / Design Interview / Task Orchestrator / Skill Layer / Judge Layer / Re-Propose Layer / State & Memory / Provider Interface / Skill Registry
- FastAPI バックエンド (`apps/api`)
  - 認証 (OAuth PKCE)・会社・エージェント・チケット・タスク・承認・Heartbeat・予算管理の各 REST API
  - SQLAlchemy 2.x (async) + Alembic マイグレーション
  - LiteLLM Router によるマルチ LLM ゲートウェイ
- React 19 + TypeScript フロントエンド (`apps/desktop/ui`)
  - ダッシュボード・チケット・エージェント・設定画面
  - shadcn/ui + Tailwind CSS によるデザインシステム
  - TanStack Query + Zustand による状態管理
- Tauri v2 デスクトップアプリ (`apps/desktop`)
  - Windows (.msi / .exe)・macOS (.dmg)・Linux (.AppImage / .deb) 対応
- オーケストレーションエンジン
  - Self-Healing DAG による動的タスク再構築
  - Two-stage Detection + Cross-Model Verification (Judge Layer)
  - Experience Memory + Failure Taxonomy
  - 状態機械ベースの実行管理
- CI/CD パイプライン
  - GitHub Actions による自動リント・テスト・ビルド
  - マルチプラットフォーム Tauri ビルド & リリース
  - Cloudflare Workers デプロイ
- ドキュメント
  - README・DESIGN.md・MASTER_GUIDE.md
  - 各セクション実装ガイド (instructions_section2〜7)

[v0.1]: https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/tag/v0.1
[0.1.0]: https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/tag/v0.1.0
