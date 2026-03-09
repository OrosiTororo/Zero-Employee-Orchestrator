# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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

[0.1.0]: https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases/tag/v0.1.0
