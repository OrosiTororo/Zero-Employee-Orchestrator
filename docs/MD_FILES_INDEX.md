# リポジトリ内 Markdown ファイル一覧

> 最終更新: 2026-03-10 (v0.1)
>
> このドキュメントは、Zero-Employee Orchestrator リポジトリに含まれるすべての `.md` ファイルの概要・目的・対象読者を一覧化したインデックスです。

---

## 目次

1. [ルートレベルのドキュメント](#1-ルートレベルのドキュメント)
2. [docs/ フォルダのドキュメント](#2-docs-フォルダのドキュメント)
3. [実装指示ファイル（instructions_section*）](#3-実装指示ファイル)
4. [apps/edge/ のドキュメント](#4-appsedge-のドキュメント)
5. [ドキュメントの参照優先順位](#5-ドキュメントの参照優先順位)

---

## 1. ルートレベルのドキュメント

### `README.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/README.md` |
| **目的** | プロジェクトの第一印象となるドキュメント。概要・主な機能・インストール手順・技術スタックをまとめる |
| **対象読者** | すべての利用者・開発者 |
| **主な内容** | 日本語・英語・中国語の3言語対応。GUI版（デスクトップインストーラー）とCLI版のインストール手順、技術スタック表、クイックスタートコマンド |

---

### `ABOUT.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/ABOUT.md` |
| **目的** | "なぜ Zero-Employee Orchestrator が必要か" を訴求するマーケティング・説明文書 |
| **対象読者** | 非エンジニア・経営者・プロダクト評価者 |
| **主な内容** | 他の AI エージェント（AutoGPT, CrewAI）・RPA・n8n/Make との比較表、9つの優位性（自然言語起動、安全設計、経験学習、Self-Healing、監査可能性、無料利用方法、分身AI/秘書AI、チャットツール連携、3層拡張体系）、エンタープライズ対応 |

---

### `USER_GUIDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/USER_GUIDE.md` |
| **目的** | エンドユーザー向けのセットアップ～操作マニュアル |
| **対象読者** | エンドユーザー（エンジニア・非エンジニア問わず） |
| **主な内容** | 日本語・英語・中国語の3言語対応。動作要件、LLM接続方法（Gemini無料API / Ollama / OpenAI 等）、インストール手順、全画面の説明と操作方法、チケット（業務依頼）の使い方、承認フロー、スキル・プラグイン拡張方法、コスト管理、トラブルシューティング、FAQ |

---

### `DESIGN.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/DESIGN.md` |
| **目的** | 実装設計書。AI コーディングエージェントが着手できる粒度まで構造を整理した中核設計書 |
| **対象読者** | 実装者・AI エージェント |
| **主な内容** | システム定義・設計原則・DB テーブル設計（全カラム定義）・API エンドポイント一覧・状態遷移（State Machine）・UI 画面設計・実装フェーズ（Phase 0〜9）・MVP 境界 |

---

### `MASTER_GUIDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/MASTER_GUIDE.md` |
| **目的** | AI コーディングエージェントによる実装の進め方・参照順序・判断基準をまとめた運用ガイド |
| **対象読者** | AI エージェント・実装担当者 |
| **主な内容** | 最重要ルール6条（名称統一、参照優先順位、YouTube はデモ等）、各ファイルの役割と使い方の対応表、実装フェーズの進め方（Phase 0〜9）、禁止事項、判断に迷ったときのフロー |

---

### `CLAUDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/CLAUDE.md` |
| **目的** | Claude Code（AI コーディングエージェント）向けの開発ガイド。プロジェクト全体の概要を1ファイルに凝縮 |
| **対象読者** | Claude Code（AI エージェント） |
| **主な内容** | 9層アーキテクチャ定義、技術スタック（Python/FastAPI/React/Tauri）、ディレクトリ構成、コーディング規約（Python ruff・TypeScript strict）、ポート番号、設計原則9条、DB スキーマ概要、全 API エンドポイント、ランタイム設定管理、対応 LLM モデル、Ollama 統合、Skill 管理 v0.1、禁止事項 |

---

### `SECURITY.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/SECURITY.md` |
| **目的** | セキュリティポリシーとデプロイ前チェックリスト |
| **対象読者** | 運用者・デプロイ担当者 |
| **主な内容** | サポートバージョン表、脆弱性報告方法（GitHub Security Advisories）、デプロイセキュリティチェックリスト（SECRET_KEY / JWT_SECRET 生成方法、Cloudflare 認証情報、placeholder ID の置き換え、Tauri auto-updater 公開鍵設定、CORS 設定、DB 本番設定、推奨セキュリティ設定） |

---

### `CHANGELOG.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/CHANGELOG.md` |
| **目的** | バージョン別の変更履歴 |
| **対象読者** | すべての利用者・開発者 |
| **主な内容** | [Keep a Changelog](https://keepachangelog.com/) 形式。v0.1.0（2026-03-10）の全追加機能一覧（ランタイム設定管理、ナレッジストア、匿名セッション、エージェント監視、仮説検証エンジン、IAM、Sentry 連携、MCP サーバー、外部スキルインポート、AI 調査ツール、Cloudflare Workers 全移植版、Tauri 自動アップデート、Docker コンテナ等） |

---

### `Zero-Employee Orchestrator.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/Zero-Employee Orchestrator.md` |
| **目的** | プロジェクトの**最上位基準文書**。思想・要件・MVP 定義・運用方針・実装判断基準をすべて統合した原典 |
| **対象読者** | 設計者・プロダクトオーナー・AI エージェント |
| **主な内容** | Skill / Plugin / Extension の定義と違い、システムが解決する問題、設計思想、MVP 必須機能と後回し機能の整理、状態遷移設計、承認フロー要件、監査ログ要件、拡張体系、Self-Healing DAG 要件、Judge Layer 要件、Experience Memory 要件 |
| **備考** | ファイル名にスペースが含まれる（`Zero-Employee Orchestrator.md`）。他のドキュメントより優先順位が最上位 |

---

## 2. docs/ フォルダのドキュメント

### `docs/OVERVIEW.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/OVERVIEW.md` |
| **目的** | 初めてこのプロジェクトを見る方向けの、思想・機能・構造をすべて解説する総合ガイド |
| **対象読者** | 初見の方（エンジニア・非エンジニア問わず） |
| **主な内容** | ZEO とは何か（他ツールとの比較表）、なぜ必要か、基本的な使い方（3ステップ）、9層アーキテクチャ詳細、技術スタック一覧、実装状況（バックエンド・API・フロントエンド・ORM テーブル）、オフライン動作（Ollama/ローカルRAG）、コア機能と拡張機能の境界、外部ツール連携、設計上の注意点、ドキュメント一覧、ディレクトリ構成 |

---

### `docs/FEATURES.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/FEATURES.md` |
| **目的** | 実装済み機能の全体像を網羅的にまとめた機能一覧 |
| **対象読者** | 機能確認・評価者、開発者 |
| **主な内容** | 全27セクション構成。9層アーキテクチャ機能詳細、Design Interview、Spec/Plan/Tasks、DAG ベース Task Orchestrator、状態機械、Judge Layer（二段階検証）、Cost Guard、Quality SLA、Self-Healing/Re-Propose、Failure Taxonomy、Experience Memory、承認フロー、監査ログ、エージェント管理、Skill/Plugin/Extension 3層拡張、LLM Gateway（マルチプロバイダー）、バックグラウンドワーカー、Heartbeat、組織管理、権限モデル、フロントエンド UI（21画面）、REST API、WebSocket、Observability、Cloudflare Workers デプロイ、デスクトップアプリ（Tauri）、CLI/TUI |

---

### `docs/BUILD_GUIDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/BUILD_GUIDE.md` |
| **目的** | Zero-Employee Orchestrator をゼロから構築する手順をフェーズごとにコード付きで解説するビルドガイド |
| **対象読者** | ソースからビルドする開発者・自己ホスティング利用者 |
| **主な内容** | 前提条件（Python 3.12+, Node.js 20+, pnpm 9+, Rust）、クイックセットアップコマンド、Phase 0〜9（開発基盤→認証→Design Interview→Plan/承認→Task実行→Judge/再計画→Skill/LocalContext→UI→Registry→高度化）の段階的実装手順、デプロイ手順 |

---

### `docs/FEATURE_BOUNDARY.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/FEATURE_BOUNDARY.md` |
| **目的** | コア機能（本体に必須）vs Skill / Plugin / Extension（拡張）の境界を明文化した境界定義書 |
| **対象読者** | 開発者・設計者 |
| **主な内容** | 境界の判断基準（「それがないと承認・監査・実行制御が成立しないか？」）、コア機能の詳細一覧（認証・9層アーキテクチャ基盤・承認/監査・データ管理・UI基盤・オフライン動作）、Skill として切り出す機能一覧、Plugin として切り出す機能一覧、Extension として切り出す機能一覧 |

---

### `docs/MD_FILES_INDEX.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/MD_FILES_INDEX.md` |
| **目的** | **本ドキュメント**。リポジトリ内の全 `.md` ファイルを一覧化した索引 |
| **対象読者** | すべての利用者・開発者 |
| **主な内容** | リポジトリ内22ファイルの場所・目的・対象読者・主な内容の一覧 |

---

## 3. 実装指示ファイル

実装指示ファイル（`instructions_section*.md`）は、AI コーディングエージェントが各フェーズの実装を進める際の具体的な指示書です。参照優先順位は `Zero-Employee Orchestrator.md` → `DESIGN.md` → `MASTER_GUIDE.md` → 本ファイル群の順です。

---

### `instructions_section2_init.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/instructions_section2_init.md` |
| **目的** | Section 2: リポジトリ初期化の実装指示 |
| **対象読者** | AI エージェント（実装担当） |
| **主な内容** | ディレクトリ構成の雛形、モノレポ設定（pnpm workspaces）、Python/TypeScript の初期セットアップ、`.env` 雛形の作成、GitHub Actions の基本設定、完了条件（backend/frontend/tauri/docs/tests の骨組みが揃うこと） |

---

### `instructions_section3_backend.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/instructions_section3_backend.md` |
| **目的** | Section 3: FastAPI バックエンド構築の実装指示 |
| **対象読者** | AI エージェント（実装担当） |
| **主な内容** | MVP 優先実装項目（認証/セッション、組織管理、チケット、Spec/Plan/Tasks、実行/レビュー/成果物、承認、Skill Registry 最低限、監査ログ、Heartbeat 最小版）、SQLAlchemy モデル定義、FastAPI ルーター実装、状態機械実装、Judge Layer 実装、完了条件 |

---

### `instructions_section4_frontend.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/instructions_section4_frontend.md` |
| **目的** | Section 4: React フロントエンド構築の実装指示 |
| **対象読者** | AI エージェント（実装担当） |
| **主な内容** | UI 原則（見た目より運用可能性優先）、実装する画面一覧（認証系・主要業務画面・拡張系）、コンポーネント設計方針、API との接続方法、shadcn/ui + Tailwind CSS の使用方針、完了条件 |

---

### `instructions_section5_skills.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/instructions_section5_skills.md` |
| **目的** | Section 5: Skills / Plugins / Extensions 実装の指示 |
| **対象読者** | AI エージェント（実装担当） |
| **主な内容** | Skill / Plugin / Extension の用語定義と違い（混同しないための注意）、MVP での組み込み Skill 一覧（spec-writer, plan-writer, task-breakdown, review-assistant, artifact-summarizer, local-context）、Skill テンプレート構造、Registry API の実装方法、完了条件 |

---

### `instructions_section6_tauri.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/instructions_section6_tauri.md` |
| **目的** | Section 6: Tauri 統合・デスクトップアプリ化の実装指示 |
| **対象読者** | AI エージェント（実装担当） |
| **主な内容** | Python バックエンドをサイドカーとして起動する設定、起動ポート固定、ログ出力先定義、開発時と配布時の設定分離、tauri-plugin-shell / tauri-plugin-updater の設定、ウィンドウ設定、自動更新（GitHub Releases エンドポイント）、完了条件 |

---

### `instructions_section7_test.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/instructions_section7_test.md` |
| **目的** | Section 7: テスト・検証の実装指示 |
| **対象読者** | AI エージェント（実装担当） |
| **主な内容** | テスト方針（CRUD テストだけでなく状態遷移・承認バイパス不可・監査ログ残存・registry 整合性を検証）、Unit Tests の最低限項目、Integration Tests（Spec/Plan/Tasks の完全フロー）、E2E（状態機械遷移）、セキュリティテスト（承認なしに危険操作が通らないこと）、完了条件 |

---

## 4. apps/edge/ のドキュメント

### `apps/edge/README.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/apps/edge/README.md` |
| **目的** | Cloudflare Workers デプロイの2方式（Proxy / Full Workers）の比較と選択ガイド |
| **対象読者** | デプロイ担当者・インフラエンジニア |
| **主な内容** | 方式A（Proxy）と方式B（Full Workers）の比較表（機能・バックエンド・DB・認証・難易度・コスト）、選び方ガイド（VPS あり→方式A、サーバーレス→方式B）、共通前提条件、各方式のセットアップコマンド、GitHub Actions によるデプロイ方法 |

---

### `apps/edge/full/README.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/apps/edge/full/README.md` |
| **目的** | 方式B（Full Workers）のセットアップ・デプロイ手順書 |
| **対象読者** | Cloudflare Workers でフルスタック運用する開発者 |
| **主な内容** | FastAPI バックエンドを Hono + D1（SQLite互換）でエッジ上に再実装した方式の説明、実装済み API エンドポイント一覧（Auth/Companies/Tickets/Agents/Tasks/Approvals/Specs/Plans/Audit/Budgets/Projects/Registry/Artifacts/Heartbeats/Reviews）、セットアップ手順、D1 データベース初期化、環境変数（JWT_SECRET）、ローカル開発・デプロイコマンド |

---

### `apps/edge/proxy/README.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/apps/edge/proxy/README.md` |
| **目的** | 方式A（Proxy）のセットアップ・デプロイ手順書 |
| **対象読者** | 既存 FastAPI バックエンドの前段に Workers を置く開発者 |
| **主な内容** | リバースプロキシ方式の機能説明（CORS/Rate Limiting/キャッシュ/フォールバック/ヘルスチェック）、セットアップ手順、環境変数（BACKEND_ORIGIN）、KV Namespace の設定方法、ローカル開発・デプロイコマンド |

---

## 5. ドキュメントの参照優先順位

実装・設計判断・機能境界の確認を行う際は、以下の順序でドキュメントを参照してください。

```
1. Zero-Employee Orchestrator.md  ← 最上位基準（思想・要件・MVP 定義）
2. DESIGN.md                      ← 実装設計（DB・API・状態遷移・実装順）
3. MASTER_GUIDE.md                ← 運用ガイド（進め方・判断基準・禁止事項）
4. CLAUDE.md                      ← AI エージェント向け開発ガイド
5. instructions_section2〜7       ← 各領域の具体的実装指示
```

利用者向けドキュメントは以下の順序で参照してください：

```
初見の方         → docs/OVERVIEW.md
なぜ必要か       → ABOUT.md
セットアップ     → USER_GUIDE.md または docs/BUILD_GUIDE.md
機能確認         → docs/FEATURES.md
機能境界確認     → docs/FEATURE_BOUNDARY.md
デプロイ         → apps/edge/README.md + SECURITY.md
変更履歴         → CHANGELOG.md
```

---

*このインデックスは `docs/OVERVIEW.md` セクション 11「ドキュメント一覧」と対応しています。*
