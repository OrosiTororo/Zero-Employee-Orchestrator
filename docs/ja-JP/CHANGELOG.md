# Changelog

> [English](../CHANGELOG.md) | 日本語 | [中文](../zh/CHANGELOG.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-03-25

### Added

- **Design Interview 過去失敗パターンフィードバック** — Experience Memory と Failure Taxonomy から類似失敗パターンを自動検索し、Interview 中に警告・追加質問を動的注入。Spec 生成時にリスクノートとして統合。
- **FEATURES.md に 21 件の未記載機能を追加** — RSS/ToS 自動更新、Knowledge Refresh、A2A 双方向通信、Avatar AI 共進化、Longrun Scheduler、Agent Session、Artifact Bridge、メディア生成、AI ツールレジストリ、iPaaS 統合、アーティファクトエクスポート、リパーパスエンジン、Obsidian 統合、クラウドネイティブ統合、スマートデバイス統合、ガバナンス・コンプライアンス、マーケットプレイス、チーム管理、Red-team テスト、ワークスペース隔離

### Security

- **Sandbox シンボリックリンク攻撃対策強化** — resolve() 後のパスが元パスと異なるディレクトリを指す場合を検出・ブロック
- **Data Protection パスワードパターンマッチング修正** — 大文字小文字を区別しないパターンマッチングに修正
- **CI: Dependabot PR でもテスト実行** — 従来スキップされていた lint-and-test ジョブを Dependabot PR でも実行するよう修正

### Changed

- **Dependabot 設定の大幅強化** — メジャーバージョン更新の無視、グループ化、全エコシステム網羅（pip/npm/cargo/github-actions）、Cloudflare Workers 個別管理
- **Dependabot 自動マージワークフロー追加** — patch/minor 更新を CI 通過後に自動承認・squash マージ

## [0.1.0] - 2026-03-12 — Platform v0.1 (Consolidated Release)

### Added — AI Self-Improvement (Level 2: 自己改善の芽)

- **AI Self-Improvement Plugin 実装** (`services/self_improvement_service.py`, `api/routes/self_improvement.py`)
  - 6 Skill の完全実装: skill-analyzer, skill-improver, judge-tuner, failure-to-skill, skill-ab-test, auto-test-generator
  - **Skill Analyzer** — 既存 Skill のコード品質を AI が分析（静的分析 16 パターン + LLM 深層分析）
  - **Skill Improver** — 分析結果に基づく改善版 Skill の自動生成（安全性チェック付き・バージョン管理）
  - **Judge Tuner** — Experience Memory の承認/却下パターンから Judge Layer ルールを自動提案
  - **Failure-to-Skill** — Failure Taxonomy の頻発パターンから予防 Skill を自動生成
  - **Skill A/B Test** — 2つの Skill を同じ入力で実行し品質・速度を定量比較
  - **Auto Test Generator** — Skill コードから正常系・エッジケース・異常系テストを自動生成
  - Self-Improvement API: 10 エンドポイント（`/api/v1/self-improvement/*`）
  - ダッシュボード API: 分析数・改善提案数・適用数・テスト生成数の統計
  - 全操作に承認フロー統合（改善適用・Judge 調整・Skill 登録は承認必須）
  - Skill バージョン管理（manifest_json に version_history を保持・ロールバック可能）
- **Self-Improvement スキーマ** (`schemas/self_improvement.py`)
  - 14 の Pydantic DTO: 分析・改善・Judge調整・失敗学習・A/Bテスト・テスト生成の入出力
- ルーター登録 (`api/routes/__init__.py`): self-improvement ルーター追加

### Security

- **bcrypt を必須依存に昇格** — SHA-256 フォールバックを廃止し、パスワードハッシュに bcrypt を強制
- **レート制限追加** (`slowapi`) — 認証エンドポイントにレート制限を実装（登録: 5/min, ログイン: 10/min）
- **RAG ファイル権限修正** — `index.json` / `idf.json` を `0o600`（所有者のみ）に制限
- **RAG 入力バリデーション** — コンテンツサイズ上限 (10 MB) とメタデータキー数制限を追加
- **認証エンドポイント保護** — 承認 / 設定 / レジストリ API に認証を追加
- **CORS 制限強化** — ワイルドカードを明示的メソッド・ヘッダーリストに変更
- **UUID 入力バリデーション** — 不正 UUID で 400 を返すように修正

### Added

- **ファイル添付による計画作成** — Design Interview にファイルを添付し、仕様書生成のコンテキストに統合
  - `POST /api/v1/tickets/{ticket_id}/interview/attach` — ファイルアップロード
  - `GET /api/v1/tickets/{ticket_id}/interview/attachments` — 添付ファイル一覧
  - テキスト・コード・画像・PDF に対応（テキスト自動抽出 + 複数エンコーディング対応）
  - 抽出テキストを Spec の「参照資料」セクションに自動統合
- **Local Context Skill 画像対応** — 画像ファイル読み取り（Base64 エンコード + PNG/JPEG サイズ検出）
  - `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg` に対応
  - SVG はテキストとしても解析
  - 10 MB サイズ上限
- **ファイルタイプ拡張** — Local Context Skill の対応形式を大幅拡充
  - コード: `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.h`, `.html`, `.xml`, `.css`, `.sql`, `.sh`
  - 複数エンコーディング自動検出（UTF-8, Shift_JIS, EUC-JP, CP932）
- **壁打ち（ブレインストーミング）機能** (`services/multi_model_service.py`, `api/routes/multi_model.py`, `pages/BrainstormPage.tsx`)
  - AI相談役との壁打ちセッション管理（作成・メッセージ追加・検索・アーカイブ）
  - 複数モデル壁打ち対応（GPT / Gemini / Claude を同時に使用可能）
  - セッションタイプ: brainstorm / debate / review / ideation / strategy
  - 壁打ち / Brainstorm / 头脑风暴 — Brainstorm with AI advisors
- **マルチモデル比較機能** (`services/multi_model_service.py`)
  - 同一入力を複数モデルに送信し、回答を並べて比較
  - モデルごとの文字数・トークン数・レイテンシ計測
  - 比較結果の永続保存と一覧表示
  - Multi-Model Compare — Send same input to GPT / Gemini / Claude and compare responses side-by-side
- **会話記憶（Conversation Memory）** (`services/multi_model_service.py`)
  - ユーザーとAI組織の全会話を永続保管
  - 過去の会話をキーワード検索（ユーザーが過去の発言について聞いた場合に対応）
  - 会話統計（総メッセージ数・総文字数・役割別・種類別）
  - Conversation Memory — Permanently store all conversations, search past discussions
- **正確な文字数カウント（TextAnalyzer）** (`services/multi_model_service.py`)
  - Python の len() による Unicode 対応の正確な文字数カウント
  - ひらがな・カタカナ・漢字・ASCII・数字の内訳
  - 文字数バリデーション（最小・最大文字数チェック）
  - ユーザーが文字数を指定した場合に正確に対応
  - Text Analysis API: POST /text/analyze
- **役割別モデル設定** (`services/multi_model_service.py`)
  - エージェントの役割ごとに使用するAIモデルをユーザーが自由に設定
  - エージェント個別設定と全体設定のフォールバック
  - フォールバックモデル・max_tokens・temperature・システムプロンプトの設定
  - Per-Role Model Settings — Users can assign AI models per agent role
- **動的エージェント組織管理** (`services/agent_org_service.py`)
  - プリセット役割（秘書・相談役・PM・リサーチャー・エンジニア等）でのエージェント追加
  - カスタム役割の作成・一覧・削除
  - エージェントの役割更新（名前・説明・モデル・自律度・システムプロンプト）
  - エージェントの削除（廃止状態への遷移）
  - Dynamic Agent Management — Add, remove, modify agents with preset or custom roles
- **秘書・相談役の役割定義** (`services/agent_org_service.py`)
  - 秘書: AI組織とユーザーの繋ぎ役、情報の保管庫、ナレッジ蓄積
  - 相談役: ユーザーの壁打ち相手、多角的アドバイス、秘書とユーザーの橋渡し
  - 各役割にシステムプロンプト定義済み
  - Secretary & Advisor roles with predefined system prompts
- **自然言語組織管理** (`services/agent_org_service.py`)
  - 「相談役を追加して」等の自然言語でAI組織にリクエスト
  - キーワードベースのアクション・役割自動推定
  - 自動実行モード対応（信頼度が高い場合は自動実行）
  - 機能リクエストの永続保存と一覧表示
  - Natural Language Org Management — Manage AI org with natural language
- **フロントエンド BrainstormPage** (`pages/BrainstormPage.tsx`)
  - 壁打ちセッション管理UI（作成・メッセージ送受信・検索）
  - マルチモデル比較UI（モデル選択・入力・結果比較表示）
  - 役割別モデル設定UI（一覧表示・利用可能な役割表示）
  - AI組織管理UI（自然言語リクエスト送信・役割一覧・エージェント追加）
  - リアルタイム文字数カウント表示
- **秘書AI ダッシュボード** (`pages/SecretaryPage.tsx`)
  - ブレインダンプ（思考を整理してカテゴリ分類・アクションアイテム抽出）
  - 日次サマリー生成・閲覧
  - 優先度提案・タスクの整理
- **AI Self-Improvement Plugin** (`plugins/ai-self-improvement/`)
  - 6 Skill のマニフェスト定義: skill-analyzer, skill-improver, judge-tuner, failure-to-skill, skill-ab-test, auto-test-generator
  - Judge Layer / Experience Memory / Failure Taxonomy / Skill Registry / DAG との統合ポイント定義
  - 安全性ポリシー（サンドボックス実行・承認必須・ロールバック・品質閾値・変更量制限・Kill Switch）
- **ZEO-Bench — Judge Layer 定量評価ベンチマーク** (`tests/zeo_bench.py`)
  - 200 問のテストセットで Cross-Model Verification の精度を定量評価
  - 4 カテゴリ: 事実正確性 (50問)・矛盾検出 (70問)・偽陽性 (40問)・修正品質 (40問)
  - 単一モデル自己評価との検出率比較を数値で出力
  - `BenchmarkReport` による per-category 分析とサマリー
- **Cross-Model Verification の改善** (`orchestration/judge.py`)
  - セマンティック類似度検証（トークンレベル Jaccard 類似度）
  - 数値許容範囲比較（5% 以内は一致とみなす）
  - 矛盾検出エンジン: 否定パターン・数値不整合・結論矛盾・時系列不整合を検出
  - 信頼度加重スコアリング（合意モデル数による重み付け）
  - 詳細な矛盾レポート（contradiction_details）の出力
- **汎用ドメイン Skill テンプレート** (`skills/builtin/domain_skills.py`)
  - ContentCreatorSkill — 任意プラットフォーム向けコンテンツ生成（ブログ・SNS・メール・動画台本・プレゼン）
  - CompetitorAnalysisSkill — 任意ドメインの競合分析（市場分析・SWOT・価格比較・機能比較）
  - TrendAnalysisSkill — 任意ドメインのトレンド分析（市場・技術・SNS・業界動向）
  - PerformanceAnalysisSkill — 任意ビジネスのパフォーマンス分析（KPI・ROI・コンバージョン・エンゲージメント）
  - StrategyAdvisorSkill — ドメイン横断の戦略アドバイザー（次アクション・リソース配分・リスク評価）
  - 全 Skill が i18n 対応（ja/en/zh）・Artifact Bridge 互換
- **Artifact Bridge 強化** (`orchestration/artifact_bridge.py`)
  - auto_link_outputs_to_inputs: DAG 内の成果物を自動連携
  - cross-domain 変換: trend_report → market_context 等の自動型変換
  - 互換性マトリクス: 成果物タイプ間の自動変換ルール
  - find_compatible_artifacts: 互換成果物の検索
  - build_artifact_pipeline: Skill チェーンの成果物フロー設計
- **Self-Healing DAG カオステスト** (`tests/test_chaos_dag.py`)
  - 20+ のフォルト注入テストケース
  - 単一ノード障害・カスケード障害・並列ブランチ障害・全ブランチ障害
  - 復旧成功率・復旧時間の計測ベンチマーク
  - 戦略別効果比較（retry / skip / replan）
  - DAG 整合性検証（孤立ノード・依存関係解決・完了ノード保持）

### Fixed (post-release)

- **GUI版ログイン全機能の "Failed to fetch" エラーを修正**
  - Tauri デスクトップアプリのオリジン（`tauri://localhost`, `https://tauri.localhost`）を CORS 許可リストに追加
  - API クライアントにネットワークエラーハンドリングを追加（`NetworkError` / `ApiError` クラス）
  - Vite dev server に API プロキシ設定を追加し、開発時の CORS 問題を解消
  - Tauri 環境と Vite 開発環境で API ベース URL と WebSocket URL を自動切り替え
  - LoginPage の全ボタン（Google認証・メールログイン・アカウント登録・匿名セッション）のエラーハンドリングを改善
  - 接続エラー時にユーザーフレンドリーなメッセージを表示（日本語/英語対応）
  - Google OAuth スタブに対して「準備中」の適切なメッセージを表示
- **CLI/TUI版 pip install の修正**
  - パッケージ名を `zero-employee-orchestrator-api` → `zero-employee-orchestrator` に統一
  - リポジトリルートに `pyproject.toml` を追加し、`pip install .` でインストール可能に
  - README・BUILD_GUIDE のインストール手順をソースインストールに更新
- CI ワークフロー `claude-code-review.yml`: bot PR（Dependabot等）のレビュースキップ処理を修正
- CI ワークフロー `create-release.yml`: CHANGELOG パスを `docs/CHANGELOG.md` に修正
- リリースワークフロー `release.yml`: Tauri v2 ビルドアクション・アセットテーブルを最新化
- フロントエンド `ReleasesPage.tsx`: GitHub Releases 未公開時のフォールバック表示を追加
- ドキュメント整理: md ファイルを `docs/`（利用者向け）と `docs/dev/`（開発者向け）に再構成
- セキュリティ: Dependabot 設定・セキュリティチェックスクリプト・公開前チェックリスト追加

### Added

- **ランタイム設定管理 — .env 不要の API キー設定** (`core/config_manager.py`, `api/routes/config.py`)
  - CLI コマンド `zero-employee config set/get/list/delete/keys` で API キーや実行モードを設定
  - Web API `GET/PUT /api/v1/config` でアプリ内から設定変更
  - 設定画面（SettingsPage）に LLM API キー入力 UI を追加
  - 設定は `~/.zero-employee/config.json` に保存（ファイル権限 600 で保護）
  - 優先順位: 環境変数 > config.json > .env > デフォルト値
  - 機密値のマスク表示、プロバイダー接続状態 API
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
- **レガシーファイル移行 & ロードマップ策定**
  - `ZPCOS_FEATURES_AND_IMPROVEMENTS.md` の有用なアイデアを既存ドキュメントに統合
  - メタスキル概念・セキュリティ自己テスト・iPaaS 連携・AI 共創リパーパス等のアイデアを `ROADMAP.md` に反映
  - レガシーファイル削除
- **コミュニティ文書の追加**
  - `CONTRIBUTING.md` — 3 か国語（日本語・英語・中国語）のコントリビューションガイド
  - `CODE_OF_CONDUCT.md` — 3 か国語の行動規範（Contributor Covenant 2.1 ベース）
  - `ROADMAP.md` — v0.2〜v1.0 のロードマップ（ZPCOS の有用なアイデアを整理・統合）

- 全ドキュメントのバージョン表記を v0.1 に統一
- `CHANGELOG.md`: 全リリースを v0.1 として統合
- `docs/FEATURES.md`: 外部ツール連携・コミュニティプラグインセクション追加、機能肥大化レビュー結果追加
- `docs/FEATURE_BOUNDARY.md`: コミュニティプラグイン共有の方針追加、v0.1 機能境界見直し追加
- `ABOUT.md`: v0.1 表記統一、比較対象を AI エージェントに変更
- `docs/OVERVIEW.md`: v0.1 表記統一、画面数 21 に更新、機能肥大化レビュー追加
- `USER_GUIDE.md`: 方法C（サブスクリプションモード）のプロバイダー情報を正確に修正、比較対象を AI エージェントに変更
- `README.md`: ディレクトリ構成を三か国語（日本語・英語・中国語）で各セクションに追加、最新構造に更新
- `DESIGN.md`: 画面数 21 に更新、ディレクトリ構成に integrations/ と security/IAM を追加
- `CLAUDE.md`: integrations/ モジュールの拡張機能分類を追記

### Changed — v0.1 機能境界レビュー

以下の機能をコア機能から拡張機能に再分類（コードベースには同梱、将来分離予定）:
- `integrations/sentry_integration.py` → Extension
- `integrations/ai_investigator.py` → Skill
- `orchestration/hypothesis_engine.py` → Plugin
- `integrations/mcp_server.py` → Extension
- `integrations/external_skills.py` → Extension

### Initial Implementation (Pre-release — 2026-03-09)

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

## Development History (Pre-release milestones, consolidated into v0.1.0)

## Skills Management

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

[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
