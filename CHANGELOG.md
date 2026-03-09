# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2025-06-01

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
