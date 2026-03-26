**Language:** [English](../../README.md) | **日本語** | [简体中文](../zh-CN/README.md) | [繁體中文](../zh-TW/README.md) | [한국어](../ko-KR/README.md) | [Português (Brasil)](../pt-BR/README.md) | [Türkçe](../tr/README.md)

# Zero-Employee Orchestrator

[![Stars](https://img.shields.io/github/stars/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/stargazers)
[![Forks](https://img.shields.io/github/forks/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/network/members)
[![Contributors](https://img.shields.io/github/contributors/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Rust](https://img.shields.io/badge/-Rust-000000?logo=rust&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)

> **AI オーケストレーション基盤 — 設計 · 実行 · 検証 · 改善**

---

<div align="center">

**🌐 Language / 言語 / 语言**

[English](../../README.md) | [**日本語**](README.md) | [简体中文](../zh-CN/README.md) | [繁體中文](../zh-TW/README.md) | [한국어](../ko-KR/README.md) | [Português (Brasil)](../pt-BR/README.md) | [Türkçe](../tr/README.md)

</div>

---

**AI を「組織」として運用するための基盤 — 単なるチャットボットではありません。**

自然言語で業務ワークフローを定義し、複数の AI エージェントを役割分担させ、人間の承認ゲートと完全な監査可能性を備えた状態でタスクを実行します。Self-Healing DAG・Judge Layer・Experience Memory を備えた 9 層アーキテクチャで構築されています。

ZEO 自体は無料かつオープンソースです。LLM の API 費用はユーザーが各プロバイダーに直接支払います。

---

## ガイド

このリポジトリはプラットフォーム本体です。ガイドでアーキテクチャと設計思想を解説しています。

<table>
<tr>
<td width="33%">
<a href="../../docs/guides/quickstart-guide.md">
<img src="../../assets/images/guides/quickstart-guide.svg" alt="クイックスタートガイド" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/architecture-guide.md">
<img src="../../assets/images/guides/architecture-guide.svg" alt="アーキテクチャ詳解" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/security-guide.md">
<img src="../../assets/images/guides/security-guide.svg" alt="セキュリティガイド" />
</a>
</td>
</tr>
<tr>
<td align="center"><b>クイックスタートガイド</b><br/>インストール、初回ワークフロー、CLI の基本。<b>最初にお読みください。</b></td>
<td align="center"><b>アーキテクチャ詳解</b><br/>9 層アーキテクチャ、DAG オーケストレーション、Judge Layer、Experience Memory。</td>
<td align="center"><b>セキュリティガイド</b><br/>プロンプトインジェクション防御、承認ゲート、IAM、サンドボックス、PII 保護。</td>
</tr>
</table>

| トピック | 学べること |
|---------|-----------|
| 9 層アーキテクチャ | User → Design Interview → Task Orchestrator → Skill → Judge → Re-Propose → Memory → Provider → Registry |
| Self-Healing DAG | タスク失敗時の自動再計画・再提案 |
| Judge Layer | ルールベース一次判定 + Cross-Model 高精度検証 |
| Skill / Plugin / Extension | 自然言語スキル生成を備えた 3 層拡張体系 |
| Human-in-the-Loop | 12 カテゴリの危険操作に人間の承認を必須化 |
| セキュリティファースト設計 | プロンプトインジェクション防御（40+ パターン）、PII マスキング、ファイルサンドボックス |

---

## 最新情報

### v0.1.0 — 初回リリース（2026年3月）

- **9 層アーキテクチャ** — User Layer → Design Interview → Task Orchestrator → Skill Layer → Judge Layer → Re-Propose → State & Memory → Provider → Skill Registry
- **Self-Healing DAG** — タスク失敗時に動的 DAG 再構築による自動再計画
- **Judge Layer** — ルールベース一次判定 + Cross-Model 高精度検証
- **Experience Memory** — 過去の実行から学習し、将来のパフォーマンスを改善
- **Skill / Plugin / Extension** — 3 層拡張体系: ビルトインスキル 8 個、プラグイン 10 個、エクステンション 5 個
- **自然言語スキル生成** — スキルを自然言語で説明するだけで AI が自動生成（安全性チェック付き）
- **ブラウザアシスト** — Chrome 拡張機能によるオーバーレイチャット、リアルタイム画面共有、エラー診断
- **メディア生成** — 画像（DALL-E, SD）、動画（Runway ML, Pika）、音声（TTS, ElevenLabs）、音楽（Suno）、3D（動的プロバイダー登録）
- **AI ツール統合** — 25+ の外部ツール（GitHub, Slack, Jira, Figma 等）を AI が操作可能
- **セキュリティファースト** — プロンプトインジェクション防御（5 カテゴリ、40+ パターン）、承認ゲート、IAM、PII 保護、ファイルサンドボックス
- **マルチモデル対応** — `model_catalog.json` による動的モデルカタログ、非推奨モデルの自動フォールバック
- **多言語対応（i18n）** — 日本語 / English / 中文 — UI・AI 応答・CLI すべてシームレスに切替
- **自律運用** — Docker / Cloudflare Workers による 24/365 バックグラウンド実行
- **Self-Improvement** — AI が自身のスキルを分析・改善（承認必須）
- **A2A 通信** — エージェント間のピアツーピア通信・チャンネル・交渉

---

## 🖥️ デスクトップアプリのダウンロード

ビルド済みのデスクトップインストーラーは [Releases](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) ページで入手できます。

| OS | ファイル | 説明 |
|---|---|---|
| **Windows** | `.msi` / `-setup.exe` | Windows インストーラー |
| **macOS** | `.dmg` | macOS (Intel / Apple Silicon) |
| **Linux** | `.AppImage` | ポータブル（インストール不要） |
| **Linux** | `.deb` / `.rpm` | Debian/Ubuntu / Fedora/RHEL |

すべてのインストーラーには**セットアップウィザード**が含まれており、言語（English / 日本語 / 中文 / 한국어 / Português / Türkçe）を選択できます。言語は**設定**からいつでも変更可能です。

---

## 🚀 クイックスタート

2 分以内で起動できます:

### ステップ 1: インストール

```bash
# PyPI
pip install zero-employee-orchestrator

# ソースからインストール
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .

# Docker
docker compose up -d
```

### ステップ 2: 設定（API キー不要で開始可能）

```bash
# 方法 A: サブスクリプションモード（キー不要）
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# 方法 B: Ollama ローカル LLM（完全オフライン）
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# 方法 C: マルチ LLM プラットフォーム（1 つのキーで複数モデル利用可能）
zero-employee config set OPENROUTER_API_KEY <your-key>

# 方法 D: 各プロバイダーの API キーを個別設定
zero-employee config set GEMINI_API_KEY <your-key>
```

> **ZEO 自体は無料です。** LLM の API 費用はユーザーが各プロバイダーに直接支払います。詳しくは [USER_SETUP.md](../../USER_SETUP.md) を参照してください。

### ステップ 3: 起動

```bash
# Web UI
zero-employee serve
# → http://localhost:18234

# ローカルチャット（Ollama）
zero-employee local --model qwen3:8b --lang ja
```

✨ **以上です！** 人間の承認ゲートと監査機能を備えた AI オーケストレーション基盤が利用可能になりました。

### 言語の切り替え (CLI)

デフォルト言語は英語です。以下の方法で変更できます:

```bash
# 起動時に指定
zero-employee chat --lang ja    # 日本語
zero-employee chat --lang zh    # 中国語
zero-employee chat --lang ko    # 韓国語
zero-employee chat --lang pt    # ポルトガル語
zero-employee chat --lang tr    # トルコ語

# 永続的に変更（~/.zero-employee/config.json に保存）
zero-employee config set LANGUAGE ja

# 実行中に変更（チャットモード内）
/lang en                         # 英語に切り替え
/lang ja                         # 日本語に切り替え
/lang zh                         # 中国語に切り替え
/lang ko                         # 韓国語に切り替え
/lang pt                         # ポルトガル語に切り替え
/lang tr                         # トルコ語に切り替え

# API 経由
curl -X PUT http://localhost:18234/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"key": "LANGUAGE", "value": "ja"}'
```

言語設定はシステム全体に適用されます: CLI 出力、AI の応答、Web UI がすべて一括で切り替わります。

---

## 📦 構成内容

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                  # FastAPI バックエンド
│   │   └── app/
│   │       ├── core/               # 設定・DB・セキュリティ・i18n
│   │       ├── api/routes/         # 39 REST API ルートモジュール
│   │       ├── api/ws/             # WebSocket
│   │       ├── models/             # SQLAlchemy ORM
│   │       ├── schemas/            # Pydantic DTO
│   │       ├── services/           # ビジネスロジック
│   │       ├── repositories/       # DB 入出力抽象化
│   │       ├── orchestration/      # DAG・Judge・状態機械
│   │       ├── providers/          # LLM ゲートウェイ・Ollama・RAG
│   │       ├── security/           # IAM・シークレット・サニタイズ・プロンプト防御
│   │       ├── policies/           # 承認ゲート・自律実行境界
│   │       ├── integrations/       # Sentry・MCP・外部スキル・ブラウザアシスト
│   │       └── tools/              # 外部ツール接続
│   ├── desktop/              # Tauri v2 + React UI
│   ├── edge/                 # Cloudflare Workers
│   └── worker/               # バックグラウンドワーカー
├── skills/                   # ビルトインスキル（8 個）
├── plugins/                  # プラグインマニフェスト（10 個）
├── extensions/               # エクステンションマニフェスト（5 個）
│   └── browser-assist/
│       └── chrome-extension/ # ブラウザアシスト用 Chrome 拡張機能
├── packages/                 # 共有 NPM パッケージ
├── docs/                     # 多言語ドキュメント & ガイド
│   ├── ja-JP/                # 日本語
│   ├── zh-CN/                # 简体中文
│   ├── zh-TW/                # 繁體中文
│   ├── ko-KR/                # 한국어
│   ├── pt-BR/                # Português (Brasil)
│   ├── tr/                   # Türkçe
│   └── guides/               # アーキテクチャ・セキュリティ・クイックスタートガイド
└── assets/
    └── images/
        ├── guides/           # ガイドヘッダー画像
        └── logo/             # ロゴ素材
```

---

## 🏗️ 9 層アーキテクチャ

```
┌─────────────────────────────────────────┐
│  1. User Layer       — 自然言語で目的を伝える        │
│  2. Design Interview — 壁打ち・要件深掘り          │
│  3. Task Orchestrator — DAG 分解・進行管理         │
│  4. Skill Layer      — 専門 Skill + Context       │
│  5. Judge Layer      — Two-stage + Cross-Model QA  │
│  6. Re-Propose       — 差し戻し → 動的 DAG 再構築   │
│  7. State & Memory   — Experience Memory          │
│  8. Provider         — LLM ゲートウェイ (LiteLLM)   │
│  9. Skill Registry   — 公開 / 検索 / Import        │
└─────────────────────────────────────────┘
```

---

## 🎯 主な機能

### コアオーケストレーション

| 機能 | 説明 |
|------|------|
| **Design Interview** | 自然言語による要件探索・深掘り |
| **Spec / Plan / Tasks** | 構造化された中間成果物 — 再利用・監査・差し戻し可能 |
| **Task Orchestrator** | DAG ベースの計画生成、コスト見積り、品質モード切替 |
| **Judge Layer** | ルールベース一次判定 + Cross-Model 高精度検証 |
| **Self-Healing / Re-Propose** | 障害時の自動再計画・動的 DAG 再構築 |
| **Experience Memory** | 過去の実行から学習し、将来のパフォーマンスを改善 |

### 拡張性

| 機能 | 説明 |
|------|------|
| **Skill / Plugin / Extension** | 3 層拡張体系（完全 CRUD 管理対応） |
| **自然言語スキル生成** | 自然言語で説明 → AI が自動生成（安全性チェック付き） |
| **Skill マーケットプレイス** | コミュニティ Skill の公開・検索・レビュー・インストール |
| **外部スキルインポート** | GitHub リポジトリからスキルをインポート |
| **Self-Improvement** | AI が自身のスキルを分析・改善（承認必須） |
| **メタスキル** | AI に「学び方を学ぶ能力」を付与（Feeling / Seeing / Dreaming / Making / Learning） |

### AI 機能

| 機能 | 説明 |
|------|------|
| **ブラウザアシスト** | Chrome 拡張機能オーバーレイ — AI がリアルタイムで画面を確認 |
| **メディア生成** | 画像・動画・音声・音楽・3D — 動的プロバイダー登録対応 |
| **AI ツール統合** | 25+ の外部ツール（GitHub, Slack, Jira, Figma 等） |
| **A2A 通信** | エージェント間のピアツーピア通信・チャンネル・交渉 |
| **分身 AI** | ユーザーの判断基準を学習し共に成長 |
| **秘書 AI** | ブレインダンプ → 構造化タスク、AI 組織との橋渡し |
| **リパーパスエンジン** | 1 つのコンテンツを 10 種のメディア形式に自動変換 |

### セキュリティ

| 機能 | 説明 |
|------|------|
| **プロンプトインジェクション防御** | 5 カテゴリ、40+ 検出パターン |
| **承認ゲート** | 12 カテゴリの危険操作に人間の承認を必須化 |
| **ファイルサンドボックス** | AI がアクセスできるフォルダをユーザー許可制で制限（初期設定: STRICT） |
| **データ保護** | AI のアップロード・ダウンロードをポリシーで制御（初期設定: LOCKDOWN） |
| **PII 保護** | 個人情報の自動検出・マスキング（13 カテゴリ） |
| **IAM** | 人間/AI アカウント分離、AI に対するシークレット・管理権限の拒否 |
| **レッドチーム セキュリティ** | 8 カテゴリ・20+ テストで自己脆弱性を定期検査 |

### 運用

| 機能 | 説明 |
|------|------|
| **マルチモデル対応** | 動的カタログ、自動フォールバック、タスク単位のプロバイダー指定 |
| **多言語対応（i18n）** | 日本語 / English / 中文 — UI・AI 応答・CLI |
| **自律運用** | Docker / Cloudflare Workers — PC がオフでも稼働 |
| **24/365 スケジューラ** | 9 種類の発火契機: cron、チケット作成、予算閾値等 |
| **iPaaS 連携** | n8n / Zapier / Make Webhook 連携 |
| **クラウドネイティブ** | AWS / GCP / Azure / Cloudflare 抽象化層 |
| **ガバナンス・コンプライアンス** | GDPR / HIPAA / SOC2 / ISO27001 / CCPA / APPI |

---

## 🔒 セキュリティ

ZEO は**セキュリティファースト**で設計された多層防御を備えています:

| レイヤー | 説明 |
|---------|------|
| **プロンプトインジェクション防御** | 外部入力からの指示注入を検出・遮断（5 カテゴリ、40+ パターン） |
| **承認ゲート** | 12 カテゴリの危険操作（送信・削除・課金・権限変更等）に人間の承認を必須化 |
| **自律実行境界** | AI が自律実行できる操作を明示的に制限 |
| **IAM** | 人間/AI アカウント分離、AI に対するシークレット・管理権限の拒否 |
| **シークレット管理** | Fernet 暗号化・自動マスキング・ローテーション支援 |
| **サニタイズ** | API キー・トークン・個人情報の自動除去 |
| **セキュリティヘッダー** | CSP・HSTS・X-Frame-Options 等を全レスポンスに付与 |
| **レート制限** | slowapi による API レート制限 |
| **監査ログ** | 全重要操作を記録（後付けではなく設計段階から組込み） |

脆弱性の報告は [SECURITY.md](../../SECURITY.md) を参照してください。

---

## 🖥️ CLI リファレンス

```bash
zero-employee serve              # API サーバーを起動
zero-employee serve --port 8000  # ポート指定
zero-employee serve --reload     # ホットリロード

zero-employee chat               # チャットモード（全プロバイダー対応）
zero-employee chat --mode free   # 無料モード（Ollama / g4f）
zero-employee chat --lang ja     # 言語選択

zero-employee local              # ローカルチャット（Ollama）
zero-employee local --model qwen3:8b --lang ja

zero-employee models             # インストール済みモデル一覧
zero-employee pull qwen3:8b      # モデルダウンロード

zero-employee config list        # 全設定値を表示
zero-employee config set <KEY>   # 設定値を保存
zero-employee config get <KEY>   # 設定値を取得

zero-employee db upgrade         # DB マイグレーション
zero-employee health             # ヘルスチェック
zero-employee security status    # セキュリティ状態
zero-employee update             # 最新版にアップデート
```

---

## 🤖 対応 LLM モデル

`model_catalog.json` で一元管理 — コード変更なしにモデルを入れ替え可能。

| モード | 説明 | 例 |
|-------|------|-----|
| **Quality** | 最高品質 | Claude Opus, GPT-5.4, Gemini 2.5 Pro |
| **Speed** | 高速応答 | Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash |
| **Cost** | 低コスト | Haiku, Mini, Flash Lite, DeepSeek |
| **Free** | 無料 | Gemini 無料枠, Ollama ローカル |
| **Subscription** | API キー不要 | g4f 経由 |

タスク単位のプロバイダー指定に対応 — タスクごとにプロバイダー・モデル・実行モードを指定可能。

---

## 🧩 Skill / Plugin / Extension

### 3 層の拡張体系

| 種別 | 説明 | 例 |
|------|------|-----|
| **Skill** | 単一目的の専門処理 | spec-writer, review-assistant, browser-assist |
| **Plugin** | 複数 Skill をバンドル | ai-secretary, ai-self-improvement, youtube |
| **Extension** | システム連携・インフラ | mcp, oauth, notifications, browser-assist |

### 自然言語でスキル生成

```bash
POST /api/v1/registry/skills/generate
{
  "description": "長文ドキュメントを3つの要点にまとめるスキル"
}
```

16 種類の危険パターンを自動検出。安全性チェック通過後にのみ登録。

---

## 🌐 ブラウザアシスト

Chrome 拡張機能によるオーバーレイチャット — AI がリアルタイムで画面を確認し操作を案内します。

- **オーバーレイチャット**: ウェブサイト上に直接チャット UI を表示
- **リアルタイム画面共有**: スクショを貼らずに AI が画面を確認
- **エラー診断**: 画面上のエラーメッセージを読み取り、解決策を提案
- **フォーム入力支援**: 各フィールドの入力方法をステップバイステップで案内
- **プライバシーファースト**: スクリーンショットは一時処理のみ、PII 自動マスキング、パスワードフィールド自動ぼかし

### セットアップ

```
1. extensions/browser-assist/chrome-extension/ を Chrome にロード
   → chrome://extensions → デベロッパーモード → 「パッケージ化されていない拡張機能を読み込む」
2. 任意のウェブサイトで右下のチャットアイコンをクリック
3. テキストで質問、またはスクリーンショットボタンで画面を AI に共有
```

---

## 🛠️ 技術スタック

### バックエンド
- Python 3.12+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- SQLite（開発）/ PostgreSQL（本番推奨）
- LiteLLM Router SDK
- bcrypt / Fernet 暗号化
- slowapi レート制限

### フロントエンド
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand

### デスクトップ
- Tauri v2 (Rust) + Python サイドカー

### デプロイ
- Docker + docker-compose
- Cloudflare Workers（サーバーレス）

---

## ❓ FAQ

<details>
<summary><b>API キーなしで始められますか？</b></summary>

はい。サブスクリプションモード（キー不要）または Ollama（完全オフラインのローカル AI）で利用できます。上記のクイックスタートセクションを参照してください。
</details>

<details>
<summary><b>費用はどのくらいですか？</b></summary>

ZEO 自体は無料です。LLM の API 費用は各プロバイダー（OpenAI, Anthropic, Google 等）に直接支払います。Ollama ローカルモデルを使えば完全無料で運用することも可能です。
</details>

<details>
<summary><b>複数の LLM プロバイダーを同時に使えますか？</b></summary>

はい。ZEO はタスク単位のプロバイダー指定に対応しています。同じワークフロー内で、高品質な仕様書レビューには Claude、高速なタスク実行には GPT を使うといった使い分けが可能です。
</details>

<details>
<summary><b>データは安全ですか？</b></summary>

ZEO はセルフホスト前提で設計されています。データはすべてユーザーのインフラ上に保持されます。ファイルサンドボックスは STRICT、データ転送は LOCKDOWN、PII 自動検出は有効がデフォルトです。
</details>

<details>
<summary><b>AutoGen / CrewAI / LangGraph との違いは？</b></summary>

ZEO は**業務ワークフロー基盤**であり、開発者向けフレームワークではありません。人間の承認ゲート、監査ログ、3 層拡張体系、ブラウザアシスト、メディア生成、完全な REST API を提供し、AI を「組織」として運用するために設計されています。
</details>

---

## 🧪 開発

```bash
# セットアップ
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# 起動（ホットリロード）
zero-employee serve --reload

# テスト
pytest apps/api/app/tests/

# リント
ruff check apps/api/app/
ruff format apps/api/app/
```

---

## 🤝 コントリビューション

コントリビューションを歓迎します。

1. Fork → Branch → PR（標準フロー）
2. セキュリティ問題: [SECURITY.md](../../SECURITY.md) に従い非公開で報告
3. コーディング規約: ruff フォーマット・型ヒント必須・async def

---

## 💜 スポンサー

このプロジェクトは無料かつオープンソースです。スポンサーシップが開発の継続と成長を支えます。

[**スポンサーになる**](https://github.com/sponsors/OrosiTororo)

---

## 🌟 Star 履歴

[![Star History Chart](https://api.star-history.com/svg?repos=OrosiTororo/Zero-Employee-Orchestrator&type=Date)](https://star-history.com/#OrosiTororo/Zero-Employee-Orchestrator&Date)

---

## 📄 ライセンス

MIT — 自由に使用・改変できます。可能であればコントリビューションをお願いします。

---

<p align="center">
  <strong>Zero-Employee Orchestrator</strong> — AI を組織として運用する基盤。<br>
  セキュリティ・監査可能性・人間の監督を前提に構築されています。
</p>
