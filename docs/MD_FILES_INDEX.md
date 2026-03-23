# リポジトリ内 Markdown ファイル一覧

> 日本語 | [English](en/MD_FILES_INDEX.md) | [中文](zh/MD_FILES_INDEX.md)

> 最終更新: 2026-03-12 (v0.1)
>
> このドキュメントは、Zero-Employee Orchestrator リポジトリに含まれるすべての `.md` ファイルの概要・目的・対象読者を一覧化したインデックスです。

---

## 目次

1. [ルートレベルのドキュメント](#1-ルートレベルのドキュメント)
2. [docs/ — 利用者向けドキュメント](#2-docs--利用者向けドキュメント)
3. [docs/dev/ — 開発者向けドキュメント](#3-docsdev--開発者向けドキュメント)
4. [apps/edge/ のドキュメント](#4-appsedge-のドキュメント)
5. [.github/ のドキュメント](#5-github-のドキュメント)
6. [ドキュメントの参照優先順位](#6-ドキュメントの参照優先順位)

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

### `CLAUDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/CLAUDE.md` |
| **目的** | Claude Code（AI コーディングエージェント）向けの開発ガイド。プロジェクト全体の概要を1ファイルに凝縮 |
| **対象読者** | Claude Code（AI エージェント） |
| **主な内容** | 9層アーキテクチャ定義、技術スタック、ディレクトリ構成、コーディング規約、設計原則、DB スキーマ概要、全 API エンドポイント、ランタイム設定管理、対応 LLM モデル、Ollama 統合、Skill 管理 v0.1、禁止事項 |

---

### `CONTRIBUTING.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/CONTRIBUTING.md` |
| **目的** | コントリビューション（貢献）の方法をまとめたガイド |
| **対象読者** | コントリビューター・開発者 |
| **主な内容** | 3 か国語（日本語・英語・中国語）対応。Issue の報告方法、プルリクエストの作成手順、コーディング規約、開発環境のセットアップ |

---

### `CODE_OF_CONDUCT.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/CODE_OF_CONDUCT.md` |
| **目的** | コミュニティの行動規範 |
| **対象読者** | すべてのコントリビューター・利用者 |
| **主な内容** | 3 か国語（日本語・英語・中国語）対応。Contributor Covenant 2.1 ベースの行動規範 |

---

### `ROADMAP.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/ROADMAP.md` |
| **目的** | v0.2 〜 v1.0 のロードマップ |
| **対象読者** | 利用者・開発者・コントリビューター |
| **主な内容** | 3 か国語（日本語・英語・中国語）対応。各バージョンの計画機能一覧（優先度付き） |

---

## 2. docs/ — 利用者向けドキュメント

利用者（エンドユーザー・評価者・運用者）向け、または利用者と開発者の両方が参照するドキュメントです。

### `docs/ABOUT.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/ABOUT.md` |
| **目的** | "なぜ Zero-Employee Orchestrator が必要か" を訴求するマーケティング・説明文書 |
| **対象読者** | 非エンジニア・経営者・プロダクト評価者 |
| **主な内容** | 他の AI エージェント・RPA・n8n/Make との比較表、9つの優位性、エンタープライズ対応 |

---

### `docs/USER_GUIDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/USER_GUIDE.md` |
| **目的** | エンドユーザー向けのセットアップ〜操作マニュアル |
| **対象読者** | エンドユーザー（エンジニア・非エンジニア問わず） |
| **主な内容** | 日本語・英語・中国語の3言語対応。動作要件、LLM接続方法、インストール手順、全画面の説明と操作方法、チケットの使い方、承認フロー、スキル・プラグイン拡張方法、コスト管理、トラブルシューティング、FAQ |

---

### `docs/OVERVIEW.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/OVERVIEW.md` |
| **目的** | 初めてこのプロジェクトを見る方向けの、思想・機能・構造をすべて解説する総合ガイド |
| **対象読者** | 初見の方（エンジニア・非エンジニア問わず） |
| **主な内容** | ZEO とは何か（他ツールとの比較表）、なぜ必要か、基本的な使い方、9層アーキテクチャ詳細、技術スタック一覧、実装状況、オフライン動作、コア機能と拡張機能の境界、外部ツール連携、設計上の注意点、ドキュメント一覧、ディレクトリ構成 |

---

### `docs/FEATURES.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/FEATURES.md` |
| **目的** | 実装済み機能の全体像を網羅的にまとめた機能一覧 |
| **対象読者** | 機能確認・評価者、開発者 |
| **主な内容** | 全34セクション構成。9層アーキテクチャ機能詳細、Design Interview、Spec/Plan/Tasks、DAG ベース Task Orchestrator、状態機械、Judge Layer、Self-Healing/Re-Propose、承認フロー、監査ログ、Skill/Plugin/Extension 3層拡張、LLM Gateway、フロントエンド UI（23画面）、REST API、WebSocket |

---

### `docs/SECURITY.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/SECURITY.md` |
| **目的** | セキュリティポリシーとデプロイ前チェックリスト |
| **対象読者** | 運用者・デプロイ担当者 |
| **主な内容** | サポートバージョン表、脆弱性報告方法、デプロイセキュリティチェックリスト（SECRET_KEY / JWT_SECRET 生成方法、Cloudflare 認証情報、CORS 設定、DB 本番設定、推奨セキュリティ設定） |

---

### `docs/CHANGELOG.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/CHANGELOG.md` |
| **目的** | バージョン別の変更履歴 |
| **対象読者** | すべての利用者・開発者 |
| **主な内容** | [Keep a Changelog](https://keepachangelog.com/) 形式。v0.1.0（2026-03-12）の全変更一覧 |

---

### `docs/Zero-Employee Orchestrator.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/Zero-Employee Orchestrator.md` |
| **目的** | プロジェクトの**最上位基準文書**。思想・要件・MVP 定義・運用方針・実装判断基準をすべて統合した原典 |
| **対象読者** | 設計者・プロダクトオーナー・AI エージェント |
| **主な内容** | Skill / Plugin / Extension の定義と違い、システムが解決する問題、設計思想、MVP 必須機能と後回し機能の整理、状態遷移設計、承認フロー要件、監査ログ要件、拡張体系、Self-Healing DAG 要件 |
| **備考** | ファイル名にスペースが含まれる |

---

### `docs/SCALING_AND_COSTS.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/SCALING_AND_COSTS.md` |
| **目的** | コスト・ハードウェア制約・大規模プロジェクト活用例をまとめたガイド |
| **対象読者** | 導入検討者・運用者・経営者 |
| **主な内容** | LLM API コスト一覧、無料利用範囲、ハードウェア要件、v0.1 未実装機能、5つの大規模プロジェクト活用例、コスト最適化戦略 |

---

### `docs/AI_SELF_IMPROVEMENT_ROADMAP.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/AI_SELF_IMPROVEMENT_ROADMAP.md` |
| **目的** | AI Self-Improvement（AI が AI を改善・生成する能力）の実現に向けたロードマップ |
| **対象読者** | 開発者・コントリビューター・研究者・ビジョンに共感する方 |
| **主な内容** | AI Self-Improvement のビジョン、ZEO の現在地と目標への距離、個人開発の限界とコミュニティ・資金の必要性、4 フェーズのロードマップ、ai-self-improvement Plugin の設計、コミュニティ拡大戦略、実現する未来のシナリオ、安全性と倫理、費用見積り |

---

### `docs/PROPOSAL.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/PROPOSAL.md` |
| **目的** | プロジェクトの提案書。技術・課題・計画・予算・実績を網羅した提案文書 |
| **対象読者** | 助成金審査員・スポンサー・パートナー候補 |
| **主な内容** | 背景と目的、アーキテクチャ図、既存技術との比較、斬新さの主張、開発線表、予算内訳、提案者の実績、将来のITについての考察 |

---

### `docs/TITLE_PROPOSALS.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/TITLE_PROPOSALS.md` |
| **目的** | プロジェクトタイトル案（30字以内・10案）と申請プロジェクト概要（400〜800字） |
| **対象読者** | 助成金審査員・スポンサー・プロジェクト関係者 |
| **主な内容** | 未踏IT人材発掘・育成事業向けのタイトル候補10案（文字数・強調ポイント付き）、申請用プロジェクト概要文 |

---

### `DEVELOPER_SETUP.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/DEVELOPER_SETUP.md` |
| **目的** | ZEO 本体の開発・品質管理に関するセットアップガイド |
| **対象読者** | ZEO のコードベースを開発・保守する開発者 |
| **主な内容** | Sentry エラー監視、レッドチームセキュリティテスト |

---

### `USER_SETUP.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/USER_SETUP.md` |
| **目的** | ZEO のインストール・運用・機能拡張に関するセットアップガイド |
| **対象読者** | ZEO を利用するすべてのユーザー |
| **主な内容** | API キー設定（LLM・メディア生成・外部ツール）、iPaaS Webhook 設定、Google Workspace OAuth2、セキュリティ設定（秘密鍵・CORS）、DB 設定、デプロイ設定、ワークスペース隔離環境、ローカル・クラウドアクセス許可、業務ごとの環境カスタマイズ、ファイルサンドボックス、データ保護、Ollama セットアップ、Chrome 拡張機能、Obsidian 連携、Heartbeat スケジューラ |

---

### `docs/MD_FILES_INDEX.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/MD_FILES_INDEX.md` |
| **目的** | **本ドキュメント**。リポジトリ内の全 `.md` ファイルを一覧化した索引 |
| **対象読者** | すべての利用者・開発者 |

---

## 3. docs/dev/ — 開発者向けドキュメント

開発者・実装者・AI コーディングエージェント向けのドキュメントです。

### `docs/dev/DESIGN.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/dev/DESIGN.md` |
| **目的** | 実装設計書。AI コーディングエージェントが着手できる粒度まで構造を整理した中核設計書 |
| **対象読者** | 実装者・AI エージェント |
| **主な内容** | システム定義・設計原則・DB テーブル設計（全カラム定義）・API エンドポイント一覧・状態遷移（State Machine）・UI 画面設計・実装フェーズ（Phase 0〜9）・MVP 境界 |

---

### `docs/dev/MASTER_GUIDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/dev/MASTER_GUIDE.md` |
| **目的** | AI コーディングエージェントによる実装の進め方・参照順序・判断基準をまとめた運用ガイド |
| **対象読者** | AI エージェント・実装担当者 |
| **主な内容** | 最重要ルール6条、各ファイルの役割と使い方の対応表、実装フェーズの進め方、禁止事項、判断に迷ったときのフロー |

---

### `docs/dev/BUILD_GUIDE.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/dev/BUILD_GUIDE.md` |
| **目的** | Zero-Employee Orchestrator をゼロから構築する手順をフェーズごとにコード付きで解説するビルドガイド |
| **対象読者** | ソースからビルドする開発者 |
| **主な内容** | 前提条件、クイックセットアップコマンド、Phase 0〜9 の段階的実装手順、デプロイ手順 |

---

### `docs/dev/FEATURE_BOUNDARY.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/docs/dev/FEATURE_BOUNDARY.md` |
| **目的** | コア機能 vs Skill / Plugin / Extension の境界を明文化した境界定義書 |
| **対象読者** | 開発者・設計者 |
| **主な内容** | 境界の判断基準、コア機能の詳細一覧、Skill/Plugin/Extension として切り出す機能一覧 |

---

### 実装指示ファイル（`instructions_section*`）

実装指示ファイルは、AI コーディングエージェントが各フェーズの実装を進める際の具体的な指示書です。

| ファイル | 場所 | 内容 |
|---------|------|------|
| **instructions_section2_init.md** | `/docs/dev/` | リポジトリ初期化（ディレクトリ構成、モノレポ設定、環境構築） |
| **instructions_section3_backend.md** | `/docs/dev/` | FastAPI バックエンド構築（MVP 優先実装項目、SQLAlchemy モデル、状態機械） |
| **instructions_section4_frontend.md** | `/docs/dev/` | React フロントエンド構築（画面一覧、コンポーネント設計方針、API 接続） |
| **instructions_section5_skills.md** | `/docs/dev/` | Skills / Plugins / Extensions 実装（用語定義、組み込み Skill、Registry API） |
| **instructions_section6_tauri.md** | `/docs/dev/` | Tauri 統合・デスクトップアプリ化（サイドカー起動、自動更新） |
| **instructions_section7_test.md** | `/docs/dev/` | テスト・検証（状態遷移テスト、承認バイパス不可テスト、セキュリティテスト） |

---

## 4. apps/edge/ のドキュメント

### `apps/edge/README.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/apps/edge/README.md` |
| **目的** | Cloudflare Workers デプロイの2方式（Proxy / Full Workers）の比較と選択ガイド |
| **対象読者** | デプロイ担当者・インフラエンジニア |

---

### `apps/edge/full/README.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/apps/edge/full/README.md` |
| **目的** | 方式B（Full Workers）のセットアップ・デプロイ手順書 |
| **対象読者** | Cloudflare Workers でフルスタック運用する開発者 |

---

### `apps/edge/proxy/README.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/apps/edge/proxy/README.md` |
| **目的** | 方式A（Proxy）のセットアップ・デプロイ手順書 |
| **対象読者** | 既存 FastAPI バックエンドの前段に Workers を置く開発者 |

---

## 5. .github/ のドキュメント

### `.github/SECURITY_SETUP_CHECKLIST.md`

| 項目 | 内容 |
|------|------|
| **場所** | `/.github/SECURITY_SETUP_CHECKLIST.md` |
| **目的** | GitHub Actions 用のセキュリティセットアップチェックリスト |
| **対象読者** | DevOps・セキュリティ担当者 |
| **主な内容** | 必要な Secrets と設定項目、セキュリティ推奨事項 |

---

## 6. docs/en/ 及び docs/zh/ — 多言語ドキュメント

`docs/en/`（英語）と `docs/zh/`（中国語）には、以下の日本語ドキュメントの翻訳版が含まれています:

| 日本語原本 | 英語版 | 中国語版 |
|-----------|--------|---------|
| `docs/ABOUT.md` | `docs/en/ABOUT.md` | `docs/zh/ABOUT.md` |
| `docs/OVERVIEW.md` | `docs/en/OVERVIEW.md` | `docs/zh/OVERVIEW.md` |
| `docs/FEATURES.md` | `docs/en/FEATURES.md` | `docs/zh/FEATURES.md` |
| `docs/SECURITY.md` | `docs/en/SECURITY.md` | `docs/zh/SECURITY.md` |
| `docs/SCALING_AND_COSTS.md` | `docs/en/SCALING_AND_COSTS.md` | `docs/zh/SCALING_AND_COSTS.md` |
| `docs/CHANGELOG.md` | `docs/en/CHANGELOG.md` | `docs/zh/CHANGELOG.md` |
| `docs/MD_FILES_INDEX.md` | `docs/en/MD_FILES_INDEX.md` | `docs/zh/MD_FILES_INDEX.md` |

---

## 7. ドキュメントの参照優先順位

### 開発者・実装者向け

```
1. docs/Zero-Employee Orchestrator.md  ← 最上位基準（思想・要件・MVP 定義）
2. docs/dev/DESIGN.md                  ← 実装設計（DB・API・状態遷移・実装順）
3. docs/dev/MASTER_GUIDE.md            ← 運用ガイド（進め方・判断基準・禁止事項）
4. CLAUDE.md                           ← AI エージェント向け開発ガイド
5. docs/dev/instructions_section2〜7   ← 各領域の具体的実装指示
```

### 利用者向け

```
初見の方         → docs/OVERVIEW.md
なぜ必要か       → docs/ABOUT.md
セットアップ     → docs/USER_GUIDE.md または docs/dev/BUILD_GUIDE.md
機能確認         → docs/FEATURES.md
コスト・制約     → docs/SCALING_AND_COSTS.md
デプロイ         → apps/edge/README.md + docs/SECURITY.md
変更履歴         → docs/CHANGELOG.md
```

---

*このインデックスは `docs/OVERVIEW.md` セクション 11「ドキュメント一覧」と対応しています。*
