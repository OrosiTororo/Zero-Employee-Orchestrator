# リポジトリ内 Markdown ファイル一覧

> 日本語 | [English](en/MD_FILES_INDEX.md) | [中文](zh/MD_FILES_INDEX.md)

> 最終更新: 2026-03-23 (v0.1)
>
> このドキュメントは、Zero-Employee Orchestrator リポジトリに含まれるすべての `.md` ファイルの概要・目的・対象読者を一覧化したインデックスです。

---

## 目次

1. [ルートレベルのドキュメント](#1-ルートレベルのドキュメント)
2. [docs/ — 利用者向けドキュメント](#2-docs--利用者向けドキュメント)
3. [docs/dev/ — 開発者向けドキュメント](#3-docsdev--開発者向けドキュメント)
4. [apps/edge/ のドキュメント](#4-appsedge-のドキュメント)
5. [.github/ のドキュメント](#5-github-のドキュメント)
6. [多言語ドキュメント](#6-docsen-及び-docszh--多言語ドキュメント)
7. [ドキュメントの参照優先順位](#7-ドキュメントの参照優先順位)

---

## 1. ルートレベルのドキュメント

### ユーザー向け

| ファイル | 目的 | 対象読者 | 多言語 |
|---------|------|---------|--------|
| `README.md` | プロジェクトの第一印象。概要・主な機能・インストール手順・技術スタック | すべての利用者・開発者 | ja/en/zh (インライン) |
| `USER_SETUP.md` | ZEO の利用・運用・機能拡張に関するセットアップガイド | すべてのユーザー | ja / [en](en/USER_SETUP.md) / [zh](zh/USER_SETUP.md) |
| `ROADMAP.md` | v0.2〜v1.0 のロードマップ | 利用者・開発者・コントリビューター | ja / [en](en/ROADMAP.md) / [zh](zh/ROADMAP.md) |
| `CODE_OF_CONDUCT.md` | コミュニティの行動規範（Contributor Covenant 2.1） | すべてのコントリビューター・利用者 | ja / [en](en/CODE_OF_CONDUCT.md) / [zh](zh/CODE_OF_CONDUCT.md) |
| `CONTRIBUTING.md` | コントリビューション（貢献）の方法 | コントリビューター・開発者 | ja / [en](en/CONTRIBUTING.md) / [zh](zh/CONTRIBUTING.md) |
| `SECURITY.md` | 脆弱性報告手順 | セキュリティ報告者 | en |

### 開発者向け（ルート）

| ファイル | 目的 | 対象読者 |
|---------|------|---------|
| `CLAUDE.md` | Claude Code（AI エージェント）向けの開発ガイド | Claude Code |

---

## 2. docs/ — 利用者向けドキュメント

利用者（エンドユーザー・評価者・運用者）向け、または利用者と開発者の両方が参照するドキュメントです。

| ファイル | 目的 | 対象読者 | 多言語 |
|---------|------|---------|--------|
| `docs/ABOUT.md` | "なぜ ZEO が必要か" を訴求する説明文書 | 非エンジニア・経営者・評価者 | [en](en/ABOUT.md) / [zh](zh/ABOUT.md) |
| `docs/USER_GUIDE.md` | エンドユーザー向けの操作マニュアル | エンドユーザー | ja / [en](en/USER_GUIDE.md) / [zh](zh/USER_GUIDE.md) |
| `docs/OVERVIEW.md` | 初見の方向け総合ガイド | すべての方 | [en](en/OVERVIEW.md) / [zh](zh/OVERVIEW.md) |
| `docs/FEATURES.md` | 実装済み機能の全体像（全80セクション） | 機能確認・評価者、開発者 | [en](en/FEATURES.md) / [zh](zh/FEATURES.md) |
| `docs/SECURITY.md` | セキュリティポリシーとデプロイ前チェックリスト | 運用者・デプロイ担当者 | [en](en/SECURITY.md) / [zh](zh/SECURITY.md) |
| `docs/CHANGELOG.md` | バージョン別の変更履歴 | すべての利用者・開発者 | [en](en/CHANGELOG.md) / [zh](zh/CHANGELOG.md) |
| `docs/SCALING_AND_COSTS.md` | コスト・ハードウェア制約・活用例 | 導入検討者・運用者・経営者 | [en](en/SCALING_AND_COSTS.md) / [zh](zh/SCALING_AND_COSTS.md) |
| `docs/Zero-Employee Orchestrator.md` | **最上位基準文書**。思想・要件・MVP 定義 | 設計者・PO・AI エージェント | ja |
| `docs/MD_FILES_INDEX.md` | **本ドキュメント**。全 `.md` ファイルの索引 | すべての利用者・開発者 | [en](en/MD_FILES_INDEX.md) / [zh](zh/MD_FILES_INDEX.md) |

---

## 3. docs/dev/ — 開発者向けドキュメント

開発者・実装者・AI コーディングエージェント向けのドキュメントです。

| ファイル | 目的 | 対象読者 |
|---------|------|---------|
| `docs/dev/DESIGN.md` | 実装設計書（DB・API・状態遷移・実装順） | 実装者・AI エージェント |
| `docs/dev/MASTER_GUIDE.md` | AI 実装の進め方・参照順序・判断基準 | AI エージェント・実装担当者 |
| `docs/dev/BUILD_GUIDE.md` | ゼロから構築する手順（フェーズ別） | ソースからビルドする開発者 |
| `docs/dev/FEATURE_BOUNDARY.md` | コア機能 vs Skill/Plugin/Extension 境界定義 | 開発者・設計者 |
| `docs/dev/DEVELOPER_SETUP.md` | 開発者向けセットアップ（Sentry・レッドチーム等） | ZEO 開発者 |
| `docs/dev/SKILL.md` | SKILL.md ファイル作成ガイド | Skill 開発者 |
| `docs/dev/Progressive.md` | CLAUDE.md 作成方法論 | 開発者 |
| `docs/dev/PROPOSAL.md` | プロジェクト提案書 | 助成金審査員・スポンサー |
| `docs/dev/TITLE_PROPOSALS.md` | プロジェクトタイトル案 | プロジェクト関係者 |
| `docs/dev/AI_SELF_IMPROVEMENT_ROADMAP.md` | AI 自己改善ロードマップ | 開発者・研究者 |

### 実装指示ファイル（`instructions_section*`）

AI コーディングエージェントが各フェーズの実装を進める際の具体的な指示書です。

| ファイル | 内容 |
|---------|------|
| `docs/dev/instructions_section2_init.md` | リポジトリ初期化（ディレクトリ構成、モノレポ設定、環境構築） |
| `docs/dev/instructions_section3_backend.md` | FastAPI バックエンド構築 |
| `docs/dev/instructions_section4_frontend.md` | React フロントエンド構築 |
| `docs/dev/instructions_section5_skills.md` | Skills / Plugins / Extensions 実装 |
| `docs/dev/instructions_section6_tauri.md` | Tauri 統合・デスクトップアプリ化 |
| `docs/dev/instructions_section7_test.md` | テスト・検証 |

---

## 4. apps/edge/ のドキュメント

| ファイル | 目的 | 対象読者 |
|---------|------|---------|
| `apps/edge/README.md` | Cloudflare Workers デプロイの2方式比較 | デプロイ担当者 |
| `apps/edge/full/README.md` | Full Workers セットアップ手順 | CF Workers 開発者 |
| `apps/edge/proxy/README.md` | Proxy 方式セットアップ手順 | CF Workers 開発者 |

---

## 5. .github/ のドキュメント

| ファイル | 目的 | 対象読者 |
|---------|------|---------|
| `.github/SECURITY_SETUP_CHECKLIST.md` | GitHub Actions 用セキュリティセットアップチェックリスト | DevOps・セキュリティ担当者 |

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
| `docs/USER_GUIDE.md` | `docs/en/USER_GUIDE.md` | `docs/zh/USER_GUIDE.md` |
| `USER_SETUP.md` | `docs/en/USER_SETUP.md` | `docs/zh/USER_SETUP.md` |
| `ROADMAP.md` | `docs/en/ROADMAP.md` | `docs/zh/ROADMAP.md` |
| `CODE_OF_CONDUCT.md` | `docs/en/CODE_OF_CONDUCT.md` | `docs/zh/CODE_OF_CONDUCT.md` |
| `CONTRIBUTING.md` | `docs/en/CONTRIBUTING.md` | `docs/zh/CONTRIBUTING.md` |

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
セットアップ     → USER_SETUP.md または docs/USER_GUIDE.md
機能確認         → docs/FEATURES.md
コスト・制約     → docs/SCALING_AND_COSTS.md
デプロイ         → apps/edge/README.md + docs/SECURITY.md
変更履歴         → docs/CHANGELOG.md
```

---

*このインデックスは `docs/OVERVIEW.md` セクション 11「ドキュメント一覧」と対応しています。*
