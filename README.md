# Zero-Employee Orchestrator

自然言語で業務を定義し、複数 AI を役割分担させ、人間の承認と監査可能性を前提に業務を実行・再計画・改善できる AI オーケストレーション基盤。

## 概要

Zero-Employee Orchestrator は、単なる AI チャットや単発自動化ツールではなく、AI を「組織」として運用するための基盤です。

### 中核思想

- **AI を組織として扱う** — 単一エージェントではなく、計画・実行・検証・改善を役割分担したチーム構造
- **人間の最終承認を外さない** — 投稿・送信・課金・削除・権限変更は必ず承認可能
- **ブラックボックスを減らす** — 誰が何をなぜどのモデルで実行したかを可視化
- **最新性は拡張で担保** — 本体は安定性重視、業務差分は Skill / Plugin / Extension で吸収
- **汎用業務基盤** — YouTube は代表検証テーマ。本質は会社業務全体の実行基盤

### 主な機能

- **Design Interview** — 自然言語で業務依頼を受け、要件を深掘り
- **Spec / Plan / Tasks** — 中間成果物として構造化保存、再利用・監査・差し戻し可能
- **Task Orchestrator** — DAG ベースの計画生成、コスト見積り、品質モード切替
- **Judge Layer** — ルールベース一次判定 + Cross-Model 高精度判定
- **Self-Healing / Re-Propose** — 障害時の自動再計画・再提案
- **Skill / Plugin / Extension** — 3層の拡張体系で業務機能を追加
- **承認フロー** — 危険操作は必ず人間承認を要求
- **監査ログ** — 全重要操作を追跡可能

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| デスクトップ | Tauri v2 (Rust) |
| フロントエンド | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| バックエンド | Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic |
| LLM接続 | LiteLLM Gateway (OpenRouter, 複数Provider対応) |
| 認証 | OAuth PKCE, ローカル暗号化ストア |
| データベース | SQLite (開発), PostgreSQL (本番推奨) |

## ディレクトリ構成

```
zero-employee-orchestrator/
├── apps/
│   ├── desktop/        # Tauri デスクトップアプリ + React UI
│   ├── api/            # FastAPI バックエンド
│   └── worker/         # バックグラウンドワーカー
├── packages/           # 共有パッケージ
├── skills/             # ビルトインスキル
├── plugins/            # プラグイン
├── extensions/         # エクステンション
├── docs/               # ドキュメント
└── scripts/            # 開発・運用スクリプト
```

## セットアップ

### 前提条件

- Python 3.12+
- Node.js 20+
- pnpm 9+
- Rust (Tauri ビルド用)

### バックエンド

```bash
cd apps/api
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 18234
```

### フロントエンド

```bash
cd apps/desktop/ui
pnpm install
pnpm dev
```

### デスクトップアプリ

```bash
cd apps/desktop
pnpm tauri dev
```

## 9層アーキテクチャ

1. **User Layer** — 自然言語入力から AI 組織を起動
2. **Design Interview** — 要件を深掘りする質問生成と回答蓄積
3. **Task Orchestrator** — Plan/DAG 生成、Skill 割当、コスト見積り
4. **Skill Layer** — 単一目的の専門 Skill + Local Context Skill
5. **Judge Layer** — Two-stage Detection + Cross-Model Verification
6. **Re-Propose Layer** — 差し戻し時の再提案 + 動的 DAG 再構築
7. **State & Memory** — 永続的な実行環境・Experience Memory・Failure Taxonomy
8. **Provider Interface** — LLM ゲートウェイ (LiteLLM)
9. **Skill Registry** — Skill/Plugin の公開・検索・インストール

## 権限モデル

| ロール | 権限 |
|--------|------|
| Owner | 全権限 |
| Admin | 組織設定、一部承認、監査ログ |
| User | 業務依頼、計画確認、成果物確認 |
| Auditor | 実行履歴・監査ログの閲覧のみ |
| Developer | Skill/Plugin/Extension の開発 |

## 自律実行の境界

| 自律実行可能 | 承認必須 |
|-------------|---------|
| 調査・分析 | 公開・投稿 |
| 下書き作成 | 課金・削除 |
| 情報整理 | 権限変更・外部送信 |

## ライセンス

プライベートプロジェクト

## 関連文書

- `Zero-Employee Orchestrator.md` — 最上位基準文書（思想・要件・改善方針）
- `DESIGN.md` — 実装設計書（DB・API・画面・状態遷移）
- `MASTER_GUIDE.md` — 実装運用ガイド（進め方と判断基準）
