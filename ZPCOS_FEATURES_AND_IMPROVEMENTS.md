# ZPCOS 機能一覧・改善案まとめ

> 作成日: 2026-03-03
> 対象バージョン: v11.2
> プロジェクト名: ZPCOS（Zero-Prompt Cross-model Orchestration System）

---

## 1. プロジェクト概要

ZPCOS は「AI を道具から組織に進化させる」ローカル常駐型デスクトップ OS。
YouTube チャンネル運営における、トレンド分析・台本作成・競合調査・パフォーマンス分析などの
「作業」を AI 組織に自律的に任せ、クリエイティブな表現に集中するために生まれた。

**技術スタック:**
- バックエンド: Python 3.12 / FastAPI / uvicorn / LiteLLM
- フロントエンド: React 19 + TypeScript + Vite + shadcn/ui
- デスクトップ: Tauri v2（Rust）+ PyInstaller サイドカー
- LLM プロバイダー: OpenRouter 経由（6モデルグループ: fast, think, quality, free, reason, value）

---

## 2. 現在の機能一覧（9層アーキテクチャ）

### Layer 1: User Layer
- 自然言語で目的を入力するだけで AI 組織が動く

### Layer 2: Design Interview（壁打ち・すり合わせ）
- `POST /api/interview/start` — ユーザー入力から質問リスト自動生成
- `POST /api/interview/respond` — 選択式＋自由記述で深掘り
- `POST /api/interview/finalize` — Spec（要件定義書）自動生成
- ユーザーが言語化していない前提を掘り起こす深い質問

### Layer 3: Task Orchestrator（司令塔）
- **Plan/DAG 提案**: タスク分解→Skill 割当→依存関係 DAG を生成→ユーザー承認後に実行
- **Cost Guard**: API コスト事前見積り、予算超過時に代替 Plan 自動提案
- **Quality SLA**: 3段階（FASTEST / BALANCED / HIGH_QUALITY）の品質モード選択
- **Re-Propose**: 差し戻し時の Change Request ベース再提案、Plan Diff 表示
- **Self-Healing DAG** (v11.2): 失敗時に AI が自律的に DAG を再構築
  - 4戦略: RETRY_SAME / SWAP_SKILL / REPLAN / DECOMPOSE
  - 最大3回リトライ、超過で人間にエスカレーション
  - `POST /api/orchestrate/{id}/self-heal`, `GET /api/orchestrate/{id}/heal-history`

### Layer 4: Skill Layer
- **Skill フレームワーク**: SKILL.json + executor.py の2ファイル構成
- **Skill Gap Negotiation**: 不足 Skill 検出→3案提示（代替 / 自動生成 / スキップ）
- **Skill ROI Explainer**: Skill の代替案・価値・リスクを説明
- **Skill 自動生成エンジン**: 自然言語記述から SKILL.json + executor.py を LLM で生成
- **ビルトイン YouTube Skills（5種）**:
  - `yt-script`: 台本生成（フック→本編→CTA の構成付き）
  - `yt-rival`: 競合チャンネル分析（YouTube Data API 連携）
  - `yt-trend`: トレンド分析（急上昇動画・検索トレンド）
  - `yt-performance`: パフォーマンス分析（YouTube Analytics API）
  - `yt-next-move`: 次の一手提案（全 Skill の成果物を統合分析）
- **Local Context Skill** (v11.2): ローカルファイルをセキュアに読み込み AI 分析
  - 対応: .txt, .md, .csv, .pdf, .docx, .png, .jpg
  - 許可ディレクトリ制限、外部送信時はユーザー承認必須

### Layer 5: Judge Layer
- **Two-stage Detection**:
  - Stage 1（ルールベース・安価）: 入力不足 / 禁止事項 / コスト超過 / 危険操作
  - Stage 2（Cross-Model Judge・高精度）: 論理 / 根拠 / 矛盾検証
- **Policy Pack**: カテゴリ別コンプライアンスルール、提案段階で違反を提示

### Layer 6: Re-Propose Layer
- 再実行粒度: FULL_REGENERATE / FROM_STEP_N / PLAN_MODIFY
- Dynamic DAG Rebuild（v11.2）: Judge 差し戻し時の自動再計画

### Layer 7: State & Memory
- **状態機械**: draft → ai_executing → ai_completed → judging → human_review → approved → committed
- **Experience Memory**: 過去の成功体験を aiosqlite に永続化、Plan 生成時に自動参照
- **Failure Taxonomy**: エラー分類（AUTH_ERROR, RATE_LIMIT, SPEC_CHANGE 等）+ 回復戦略提案
- **Artifact Bridge**: 成果物スロット化（insight / copy / data / analysis）、別業務への自動差し込み
- **Knowledge Refresh**: 外部ソース差分取得→要約・重要度判定（MVP は手動トリガー）

### Layer 8: Provider Interface
- **LiteLLM Gateway**: OpenRouter 経由で全モデルにアクセス（openrouter/ プレフィックス）
- **Model Catalog Auto-Update**: OpenRouter API からカタログ自動取得→スモークベンチ→適用→失敗時ロールバック
- **Recommendation Ladder**: AI 内部の「今すぐやる / 次にやる / やらないこと」思考フレーム

### Layer 9: Skill Registry（v11.2）
- コミュニティ Skill の公開・検索・インストール
- パッケージ形式: SKILL.json + executor.py + README.md を ZIP 化
- `GET /api/registry/search`, `POST /api/registry/publish`, `POST /api/registry/install`, `GET /api/registry/popular`

### 認証・セキュリティ
- **Token Store**: keyring（AES-256 鍵）+ AES-GCM 暗号化ファイル
- **OpenRouter OAuth PKCE**: ポート 3000 一時サーバー
- **Google OAuth**: InstalledAppFlow + PKCE（YouTube/Gmail/Calendar/Drive）
- **AuthHub**: 統合認証マネージャー
- **Skill セキュリティ**: インポートホワイトリスト / 関数ブラックリスト（eval, exec, subprocess 等禁止）

### フロントエンド（7画面）
- `/login` — ログイン
- `/interview` — Design Interview（壁打ち画面）
- `/` — ダッシュボード
- `/orchestrate/:id` — オーケストレーション詳細 + Self-Healing 履歴パネル
- `/skill/:name` — Skill 実行
- `/skill/create` — Skill 作成
- `/settings` — 設定

### API エンドポイント（合計 33 個）
- 認証: 7 / Interview: 3 / Orchestrate: 8 / コア: 2 / タスク: 3 / Skill: 4 / Registry: 4 / その他: 2

---

## 3. 現状の実装状況

| カテゴリ | 状態 |
|---------|------|
| リポジトリ構造 | 完成（Section 2 完了） |
| バックエンド 17 モジュール | ファイル作成済み（実装レベルは要確認） |
| フロントエンド 7 画面 | 基本構造作成済み |
| YouTube 5 Skills + Local Context | ファイル作成済み |
| テスト 14 ファイル | ファイル作成済み |
| Tauri 統合 | 設定ファイル準備済み |
| Git リモート | **未設定（GitHub リポジトリ未作成）** |
| 初回コミット | **未実行** |

---

## 4. 改善案

### 4.1 インフラ・DevOps

| # | 改善案 | 優先度 | 詳細 |
|---|--------|--------|------|
| 1 | **GitHub リポジトリ作成・初回 push** | 最高 | 現在リモートが未設定。バージョン管理とバックアップのため即座に必要 |
| 2 | **CI/CD パイプライン構築** | 高 | .github/workflows/ ディレクトリは存在するが中身がない。pytest + ruff lint の自動実行を設定 |
| 3 | **Docker 開発環境** | 中 | バックエンド開発のポータビリティ向上。docker-compose で FastAPI + 依存サービスを一発起動 |
| 4 | **環境変数管理の統一** | 高 | .env.example を用意して必要な環境変数を明示化 |

### 4.2 バックエンド

| # | 改善案 | 優先度 | 詳細 |
|---|--------|--------|------|
| 5 | **エラーハンドリングの統一** | 高 | FastAPI の exception_handler でカスタムエラーレスポンス形式を統一 |
| 6 | **ログ基盤の整備** | 高 | structlog 等を導入し、各モジュールで構造化ログを出力。デバッグ効率が大幅に向上 |
| 7 | **レート制限の実装** | 中 | OpenRouter API のレート制限に対するバックプレッシャー制御 |
| 8 | **WebSocket 対応** | 中 | オーケストレーション実行状況のリアルタイム通知。現在はポーリング前提と思われる |
| 9 | **DB マイグレーション機構** | 中 | aiosqlite スキーマ変更時の自動マイグレーション（alembic は重いので軽量な独自実装でも可） |
| 10 | **Webhook 機能の拡充** | 低 | webhook/ ディレクトリにファイルが存在するが、設計書に記載なし。Slack/Discord 通知連携 |

### 4.3 フロントエンド

| # | 改善案 | 優先度 | 詳細 |
|---|--------|--------|------|
| 11 | **状態管理の導入** | 高 | 認証状態やオーケストレーション進行状況をグローバルに管理（Zustand or TanStack Query） |
| 12 | **エラー境界（Error Boundary）** | 高 | API エラーや予期しないクラッシュ時の UX 改善 |
| 13 | **ダークモード対応** | 低 | Tailwind の dark: プレフィックスで比較的容易に実装可能 |
| 14 | **アクセシビリティ改善** | 中 | キーボードナビゲーション、スクリーンリーダー対応 |
| 15 | **レスポンシブデザイン** | 低 | デスクトップアプリだが、ウィンドウリサイズ時の表示崩れ防止 |

### 4.4 機能拡張

| # | 改善案 | 優先度 | 詳細 |
|---|--------|--------|------|
| 16 | **MCP（Model Context Protocol）対応** | 高 | 設計書の将来構想に記載あり。外部ツール連携の標準化 |
| 17 | **マルチプラットフォーム Skill** | 中 | YouTube 以外の SNS（TikTok, Instagram, X/Twitter）向け Skill |
| 18 | **スケジューラ機能** | 中 | 定期実行（毎週のトレンド分析、月次パフォーマンスレポート等） |
| 19 | **通知システム** | 中 | タスク完了・Self-Healing 発動・エスカレーション時のデスクトップ通知 |
| 20 | **マルチユーザー対応** | 低 | 将来的にチームでの運用を想定した認証・権限管理 |
| 21 | **Skill テンプレート** | 中 | 頻出パターン（API 呼び出し型、LLM 分析型、データ集計型）のテンプレート提供 |
| 22 | **成果物のエクスポート** | 中 | 台本・分析レポートを PDF/Google Docs/Notion にエクスポート |

### 4.5 品質・テスト

| # | 改善案 | 優先度 | 詳細 |
|---|--------|--------|------|
| 23 | **テストカバレッジの計測** | 高 | pytest-cov を導入し、カバレッジ率を可視化 |
| 24 | **E2E テスト** | 中 | Playwright でフロントエンド〜バックエンド一気通貫のテスト |
| 25 | **LLM レスポンスのモック** | 高 | テスト時に OpenRouter API を呼ばずに済むモック基盤 |
| 26 | **負荷テスト** | 低 | 複数オーケストレーション同時実行時のパフォーマンス検証 |

### 4.6 セキュリティ

| # | 改善案 | 優先度 | 詳細 |
|---|--------|--------|------|
| 27 | **Skill サンドボックス強化** | 高 | 現在はインポートホワイトリスト方式。プロセス分離やリソース制限の追加 |
| 28 | **監査ログ** | 中 | 全 API 呼び出し・Skill 実行・トークン操作のログ記録 |
| 29 | **自動セキュリティスキャン** | 中 | bandit（Python）や npm audit の CI 統合 |

### 4.7 ドキュメント・DX

| # | 改善案 | 優先度 | 詳細 |
|---|--------|--------|------|
| 30 | **API ドキュメント自動生成** | 中 | FastAPI の OpenAPI スキーマを活用した Swagger UI の公開 |
| 31 | **Skill 開発者向けガイド** | 中 | コミュニティ Skill 開発のチュートリアル（Skill Registry 活用のため必須） |
| 32 | **README.md 整備** | 高 | プロジェクトルートに概要・セットアップ手順・アーキテクチャ図を記載 |

---

## 5. 優先実施ロードマップ（提案）

### Phase A: 基盤整備（最優先）
1. GitHub リポジトリ作成＋初回コミット＋push
2. CI/CD（pytest + ruff）の設定
3. .env.example 作成
4. README.md 整備

### Phase B: 品質向上
5. ログ基盤（structlog）導入
6. エラーハンドリング統一
7. LLM モック基盤でテスト安定化
8. テストカバレッジ計測

### Phase C: 機能完成
9. 全 33 API エンドポイントの実装完了と動作確認
10. WebSocket リアルタイム通知
11. 通知システム（デスクトップ通知）
12. 成果物エクスポート

### Phase D: エコシステム
13. MCP 対応
14. Skill テンプレート整備
15. Skill 開発者向けガイド
16. マルチプラットフォーム Skill（TikTok, Instagram 等）

---

## 6. GitHub リポジトリ状況

**現状: GitHub リポジトリは未作成**

- `zpcos/` 内に `.git` ディレクトリは存在する（`git init` 済み）
- リモートリポジトリは設定されていない
- コミット履歴は 0 件（初回コミット未実行）

### 推奨アクション
```bash
cd zpcos
git add -A
git commit -m "feat: initialize ZPCOS v11.2 repository structure"
gh repo create zpcos --private --source=. --push
```
