# Zero-Employee Orchestrator

自然言語で業務を定義し、複数 AI を役割分担させ、人間の承認と監査可能性を前提に業務を実行・再計画・改善できる AI オーケストレーション基盤。

---

## クイックスタート（3ステップで起動）

### 1. ダウンロード

```bash
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
```

### 2. セットアップ（初回のみ）

```bash
./setup.sh
```

このスクリプトが自動で以下を実行します:

- 前提条件（Python, Node.js, pnpm）の確認
- Python 仮想環境の作成と依存関係のインストール
- フロントエンド依存関係のインストール
- 環境変数ファイル（`.env`）の自動生成
- SQLite データベースの初期化

### 3. 起動

```bash
./start.sh
```

起動後、ブラウザで **http://localhost:5173** にアクセスしてください。

> 停止するには `Ctrl+C` を押します。

---

## 前提条件

| ツール | バージョン | 確認コマンド | インストール方法 |
|--------|-----------|-------------|----------------|
| Python | 3.12 以上 | `python3 --version` | [python.org](https://www.python.org/downloads/) |
| Node.js | 20 以上 | `node -v` | [nodejs.org](https://nodejs.org/) |
| pnpm | 9 以上 | `pnpm -v` | `npm install -g pnpm` |
| Git | 任意 | `git --version` | [git-scm.com](https://git-scm.com/) |

> **Rust** はデスクトップアプリ（Tauri）をビルドする場合のみ必要です。Web ブラウザでの利用には不要です。

### OS 別インストールガイド

<details>
<summary><strong>macOS</strong></summary>

```bash
# Homebrew で一括インストール
brew install python@3.12 node pnpm git

# バージョン確認
python3 --version   # 3.12 以上
node -v             # v20 以上
pnpm -v             # 9 以上
```

</details>

<details>
<summary><strong>Windows</strong></summary>

1. **Python 3.12+**: [python.org](https://www.python.org/downloads/) からインストーラーをダウンロード
   - インストール時に「Add Python to PATH」にチェック
2. **Node.js 20+**: [nodejs.org](https://nodejs.org/) から LTS 版をインストール
3. **pnpm**: PowerShell で `npm install -g pnpm`
4. **Git**: [git-scm.com](https://git-scm.com/download/win) からインストール

> Windows では Git Bash または WSL2 でスクリプトを実行してください。

```bash
# Git Bash / WSL2 で実行
./setup.sh
./start.sh
```

**PowerShell で実行する場合（スクリプトを使わない方法）:**

```powershell
# バックエンド
cd apps\api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e "."
uvicorn app.main:app --reload --host 0.0.0.0 --port 18234

# 別ターミナルでフロントエンド
cd apps\desktop\ui
pnpm install
pnpm dev
```

</details>

<details>
<summary><strong>Linux (Ubuntu / Debian)</strong></summary>

```bash
# システムパッケージの更新
sudo apt update && sudo apt upgrade -y

# Python 3.12+
sudo apt install -y python3 python3-venv python3-pip

# Node.js 20+ (NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# pnpm
npm install -g pnpm

# Git
sudo apt install -y git
```

</details>

---

## 手動セットアップ（スクリプトを使わない場合）

### 1. リポジトリのクローン

```bash
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
```

### 2. 環境変数の設定

```bash
cp .env.example apps/api/.env
```

`apps/api/.env` を開き、必要に応じて値を編集します:

```env
# データベース (デフォルトは SQLite)
DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db

# セキュリティ（本番では必ず変更してください）
SECRET_KEY=your-random-secret-key

# デバッグモード
DEBUG=true

# LLM API キー（AI 機能を使う場合は設定してください）
OPENROUTER_API_KEY=your-api-key
```

### 3. バックエンドのセットアップ

```bash
cd apps/api

# 仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\Activate.ps1     # Windows PowerShell

# 依存関係をインストール
pip install -e "."

# API サーバーを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 18234
```

起動すると自動的にデータベーステーブルが作成されます。

### 4. フロントエンドのセットアップ

```bash
# 別のターミナルを開いて実行
cd apps/desktop/ui

# 依存関係をインストール
pnpm install

# 開発サーバーを起動
pnpm dev
```

### 5. 動作確認

| サービス | URL |
|---------|-----|
| フロントエンド | http://localhost:5173 |
| バックエンド API | http://localhost:18234 |
| ヘルスチェック | http://localhost:18234/healthz |
| API ドキュメント (JSON) | http://localhost:18234/api/v1/openapi.json |

---

## LLM API キーの設定

AI によるタスク実行機能を使うには、LLM プロバイダーの API キーが必要です。

`apps/api/.env` に以下のいずれかを設定してください:

```env
# OpenRouter（複数モデル対応 — 推奨）
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

> API キーは各プロバイダーの公式サイトで取得できます:
> - [OpenRouter](https://openrouter.ai/)
> - [OpenAI](https://platform.openai.com/)

---

## ディレクトリ構成

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                # FastAPI バックエンド
│   │   ├── app/
│   │   │   ├── core/       # 設定・DB・セキュリティ
│   │   │   ├── api/        # ルーティング
│   │   │   ├── models/     # SQLAlchemy ORM モデル
│   │   │   ├── schemas/    # Pydantic DTO
│   │   │   ├── services/   # ビジネスロジック
│   │   │   └── ...
│   │   ├── alembic/        # DBマイグレーション
│   │   └── pyproject.toml
│   ├── desktop/            # Tauri デスクトップアプリ
│   │   └── ui/             # React フロントエンド
│   │       └── src/
│   │           ├── pages/  # 画面コンポーネント
│   │           ├── shared/ # 共通ユーティリティ
│   │           └── ...
│   └── worker/             # バックグラウンドワーカー
├── scripts/                # 開発・運用スクリプト
├── setup.sh                # セットアップスクリプト（初回のみ）
├── start.sh                # 起動スクリプト
└── README.md
```

---

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

---

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| デスクトップ | Tauri v2 (Rust) |
| フロントエンド | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| バックエンド | Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic |
| LLM接続 | LiteLLM Gateway (OpenRouter, 複数Provider対応) |
| 認証 | OAuth PKCE, ローカル暗号化ストア |
| データベース | SQLite (開発), PostgreSQL (本番推奨) |

---

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

---

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

---

## トラブルシューティング

### `./setup.sh` が実行できない

```bash
chmod +x setup.sh start.sh
./setup.sh
```

### ポートが使用中

```bash
# 使用中のポートを確認
lsof -i :18234   # バックエンド
lsof -i :5173    # フロントエンド

# プロセスを停止してから再起動
kill <PID>
./start.sh
```

### Python の仮想環境エラー

```bash
# 仮想環境を再作成
cd apps/api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

### pnpm install が失敗する

```bash
# キャッシュをクリアして再インストール
cd apps/desktop/ui
rm -rf node_modules
pnpm install
```

### データベースをリセットしたい

```bash
# SQLite ファイルを削除して再起動（テーブルは自動作成されます）
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

---

## 本番環境での運用

本番環境では以下の設定を推奨します:

### PostgreSQL の使用

```env
# apps/api/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zero_employee_orchestrator
```

> `asyncpg` パッケージの追加インストールが必要です:
> ```bash
> cd apps/api && source .venv/bin/activate
> pip install asyncpg
> ```

### セキュリティ設定

```env
SECRET_KEY=<ランダムな文字列を生成して設定>
DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

---

## ライセンス

プライベートプロジェクト

## 関連文書

- `Zero-Employee Orchestrator.md` — 最上位基準文書（思想・要件・改善方針）
- `DESIGN.md` — 実装設計書（DB・API・画面・状態遷移）
- `MASTER_GUIDE.md` — 実装運用ガイド（進め方と判断基準）
