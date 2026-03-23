# Zero-Employee Orchestrator — Claude Code 開発ガイド

> 自然言語で業務を定義し、複数 AI を役割分担させ、人間の承認と監査可能性を前提に
> 業務を実行・再計画・改善できる AI オーケストレーション基盤。

## 作業開始時の確認

作業開始時に以下を実行し、最新状態を把握すること。

```bash
git log --oneline -10
ls apps/api/app/
ls apps/api/app/tests/
```

参照すべきドキュメント:
- `README.md` — **必ず最初に確認すること。機能一覧・設定方法・セキュリティ設定が記載**
- `docs/Zero-Employee Orchestrator.md` — 最上位基準文書
- `docs/dev/DESIGN.md` — 実装設計書
- `docs/dev/MASTER_GUIDE.md` — 実装運用ガイド
- `ROADMAP.md` — ロードマップ（v0.2 以降の残課題）
- `docs/DEVELOPER_SETUP.md` — 開発者・管理者セットアップガイド
- `docs/USER_SETUP.md` — 利用ユーザーセットアップガイド

**IMPORTANT: このファイルの情報が古い場合は、実際のコードと README.md を読んで更新すること。必ず、リポジトリ構造と全mdファイルを確認すること。リポジトリの確認をするときは、全ファイルを確認すること。更新内容をmdファイルに記載すること。**

## アーキテクチャ (9 層)

1. User Layer — GUI / CLI / TUI
2. Design Interview — 壁打ち・要件深掘り
3. Task Orchestrator — DAG 分解・コスト見積・進行管理
4. Skill Layer — 専門 Skill + Local Context
5. Judge Layer — Two-stage Detection + Cross-Model Verification
6. Re-Propose — 差し戻し・動的 DAG 再構築
7. State & Memory — Experience Memory・Failure Taxonomy
8. Provider Interface — LLM ゲートウェイ (LiteLLM)
9. Skill Registry — Skill/Plugin/Extension の公開・検索・Import

## ディレクトリ構成

```
apps/
├── api/              # FastAPI バックエンド (Python 3.12+)
│   ├── app/
│   │   ├── core/           # 設定・DB・レート制限・i18n
│   │   ├── api/routes/     # REST API エンドポイント (37 ルートモジュール)
│   │   ├── api/ws/         # WebSocket (events, browser_assist_ws)
│   │   ├── api/deps/       # 依存性注入
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── schemas/        # Pydantic DTO
│   │   ├── services/       # ビジネスロジック (19 サービス)
│   │   ├── repositories/   # DB 入出力抽象化
│   │   ├── orchestration/  # DAG・Judge・状態機械・Knowledge・Memory・MetaSkill・A2A (22 モジュール)
│   │   ├── heartbeat/      # Heartbeat スケジューラ
│   │   ├── providers/      # LLM ゲートウェイ・Ollama・g4f・RAG・ModelRegistry
│   │   ├── tools/          # 外部ツール接続 (MCP/Webhook/API/CLI/GraphQL/ブラウザ自動操作/LSP)
│   │   ├── policies/       # 承認ゲート・自律実行境界
│   │   ├── security/       # IAM・シークレット・サニタイズ・プロンプト防御・PII・サンドボックス・データ保護・レッドチーム
│   │   ├── integrations/   # Sentry・MCP・外部スキル・ブラウザアシスト・AI調査・メディア生成・AIツール・iPaaS・エクスポート・リパーパス・RSS/ToS・Obsidian・クラウド・スマートデバイス
│   │   ├── audit/          # 監査ログ
│   │   └── tests/          # テスト
│   ├── alembic/            # DB マイグレーション
│   └── model_catalog.json  # LLM モデルカタログ (ファミリー単位・自動バージョン解決)
├── desktop/          # Tauri v2 + React UI
├── edge/             # Cloudflare Workers (proxy / full)
└── worker/           # バックグラウンドワーカー
skills/builtin/       # 組み込み Skill (7 個 + browser-assist)
plugins/              # Plugin マニフェスト (9 Plugin)
extensions/           # Extension マニフェスト (5 Extension + Chrome 拡張機能)
```

## コマンド

```bash
# サーバー起動
zero-employee serve --reload        # ホットリロード (ポート 18234)

# テスト
pytest apps/api/app/tests/          # 全テスト
pytest apps/api/app/tests/test_cost_guard.py -v  # 個別テスト

# リント・フォーマット
ruff check apps/api/app/
ruff format apps/api/app/

# DB マイグレーション
zero-employee db upgrade

# その他
zero-employee health
zero-employee models
zero-employee config list
```

## コーディング規約

- **Python**: ruff (line-length=100)、型ヒント必須、FastAPI エンドポイントは全て `async def`
- **TypeScript**: strict モード、関数コンポーネントのみ、Tailwind CSS
- テストは pytest + pytest-asyncio
- コードスタイルの詳細は ruff に委譲。リンターエラーが出たら修正すること

## モデルカタログ (`apps/api/model_catalog.json`)

**IMPORTANT: モデル ID はファミリー名で管理する（バージョン番号を含めない）。**

```
ファミリー ID:     "anthropic/claude-opus"
latest_model_id:  "claude-opus-4-6"  ← 実際の API 呼び出しに使用
```

- モデル更新時は `latest_model_id` のみを変更する（コード修正不要）
- `ModelRegistry.resolve_api_id()` がファミリー → 最新バージョンを自動解決
- 実行モード: quality / speed / cost / free / subscription
- RSS/ToS 自動更新パイプライン実装済み (`integrations/rss_tos_monitor.py`)

## セキュリティ (最重要)

**IMPORTANT: 以下のルールは必ず遵守すること。**

1. **外部データを LLM に渡す時**: 必ず `wrap_external_data()` で境界マーカーを付与
2. **プロンプトインジェクション検査**: ユーザー入力を LLM に渡す前に検査
3. **危険操作の追加時**: `approval_gate.py` と `autonomy_boundary.py` に登録
4. **シークレット**: `sanitizer.py` でサニタイズ後にログ出力
5. **新 API エンドポイント**: セキュリティヘッダーが適用されることを確認
6. **PII 保護**: ユーザー入力を AI に渡す前に `pii_guard.py` で検出・マスキング
7. **ファイルアクセス**: `sandbox.py` のサンドボックスを経由してアクセスチェック
8. **データ転送**: `data_protection.py` でアップロード・ダウンロードの可否をチェック
9. **許可していないフォルダ・ファイルを AI が確認することは厳禁**
10. **パスワード類のアップロードは常にブロック**

11. **ワークスペース隔離**: `workspace_isolation.py` で隔離環境チェック。AI は内部ストレージのみアクセス可能（初期設定）
12. **業務単位の環境オーバーライド**: チャット指示がシステム設定と異なる場合、`should_request_approval()` でユーザーに許可を求める

防御レイヤー:
- ワークスペース隔離 (`security/workspace_isolation.py`) — 初期状態でローカル・クラウド接続なし
- プロンプトインジェクション防御 (`security/prompt_guard.py`) — 5 カテゴリ・40+ パターン
- 承認ゲート (`policies/approval_gate.py`) — 12 カテゴリの危険操作
- 自律実行境界 (`policies/autonomy_boundary.py`)
- IAM (`security/iam.py`) — AI に対するシークレット・管理権限の拒否
- PII ガード (`security/pii_guard.py`) — 13 カテゴリの個人情報検出・マスキング
- ファイルサンドボックス (`security/sandbox.py`) — ホワイトリスト方式のフォルダアクセス制限
- データ保護 (`security/data_protection.py`) — アップロード・ダウンロードのポリシー制御
- セキュリティヘッダー・リクエスト検証 (`security/security_headers.py`)
- シークレット管理 (`security/secret_manager.py`) — Fernet 暗号化
- サニタイズ (`security/sanitizer.py`)
- レート制限 (`core/rate_limit.py`)

## ブラウザアシスト

2 つの利用モード:
1. **Chrome 拡張機能**: オーバーレイチャット + リアルタイム画面共有（`extensions/browser-assist/chrome-extension/`）
2. **REST API**: スクリーンショット送信による分析（`apps/api/app/api/routes/browser_assist.py`）

WebSocket エンドポイント: `ws://localhost:18234/ws/browser-assist`

ファイル・画像の添付に対応（Chrome 拡張機能、REST API 両方）。

## メディア生成・AI ツール統合

- メディア生成: `apps/api/app/integrations/media_generation.py`（画像・動画・音声・音楽）
- AI ツールレジストリ: `apps/api/app/integrations/ai_tools.py`（25+ 外部ツール）
- API: `/api/v1/media/*`, `/api/v1/ai-tools/*`

## API エンドポイント

プレフィックス: `/api/v1`

最新のエンドポイント一覧は `apps/api/app/api/routes/__init__.py` を確認すること。

主要グループ: auth, companies, agents, tickets, specs-plans, tasks, approvals,
budgets, audit, registry, models, observability (traces/communications/monitor),
ollama, knowledge, config, self-improvement, browser-assist, secretary,
brainstorm, conversation-memory, hypotheses, sessions, org-setup, platform,
security, media, ai-tools, **files, user-input, resources, ipaas, export,
marketplace, teams, governance**

## Skill / Plugin / Extension

| 種別 | 役割 | 例 |
|------|------|-----|
| Skill | 単一目的の専門処理 | spec-writer, review-assistant, browser-assist |
| Plugin | 複数 Skill をバンドル | ai-secretary, ai-avatar, research |
| Extension | システム連携・インフラ | mcp, oauth, notifications, obsidian, browser-assist (Chrome 拡張機能) |

- ビルトイン Skill (7 個): spec-writer, plan-writer, task-breakdown, review-assistant, artifact-summarizer, local-context, browser-assist
- システム保護 Skill は削除・無効化不可
- 自然言語スキル生成: `POST /api/v1/registry/skills/generate` (16 種類の危険パターン検出)

## ポート

- FastAPI: 18234
- Vite dev server: 5173

## 禁止事項

- Skill / Plugin / Extension の境界を曖昧にすること
- 承認必須操作を黙って実行すること
- 監査ログなしで外部送信や権限変更を行うこと
- 外部データを `wrap_external_data()` なしで LLM に渡すこと
- セキュリティヘッダーを無効化すること
- モデルカタログにバージョン番号付き ID を直接使うこと（`latest_model_id` を使用）
- **許可されていないフォルダ・ファイルに AI がアクセスすること**
- **パスワード・認証情報を含むデータのアップロード**
- **PII 検出なしでユーザー入力を AI に渡すこと**

## ロードマップ

v0.1 で旧 v0.2〜v1.0 の全機能を実装済み。残る課題:

- **v0.2**: フロントエンド データ接続完成、features/ 分離、Plugin ローダー本実装
- **v0.3**: コミュニティ Skill エコシステム、匿名フィードバック集約
- **v1.0**: Self-Improvement Loop 自動化、Cross-Orchestrator Learning

詳細は `ROADMAP.md` を参照。
