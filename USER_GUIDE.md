# Zero-Employee Orchestrator — ユーザーガイド / User Guide / 用户指南

> **v0.1** | 最終更新: 2026-03-10
>
> 日本語 | [English](#english-user-guide) | [中文](#中文用户指南)
>
> **初めての方へ**: このドキュメントはシステムの概要・セットアップ手順・操作方法を日本語・英語・中国語で解説しています。

---

## 目次

1. [このソフトウェアとは](#1-このソフトウェアとは)
2. [主な機能](#2-主な機能)
3. [動作するために必要なもの](#3-動作するために必要なもの)
4. [LLM（AI）の接続方法](#4-llmai-の接続方法)
5. [インストールとセットアップ](#5-インストールとセットアップ)
6. [画面の説明と基本操作](#6-画面の説明と基本操作)
7. [チケット（業務依頼）の使い方](#7-チケット業務依頼の使い方)
8. [承認フロー](#8-承認フロー)
9. [スキルとプラグインの拡張](#9-スキルとプラグインの拡張)
10. [コスト管理](#10-コスト管理)
11. [トラブルシューティング](#11-トラブルシューティング)
12. [よくある質問（FAQ）](#12-よくある質問faq)

---

## 1. このソフトウェアとは

**Zero-Employee Orchestrator** は、自然言語（普段の言葉）で業務を指示するだけで、複数の AI エージェントがチームを組んで計画・実行・検証・報告を自動的に行う **AI 業務オーケストレーション基盤** です。

### 何ができるのか

- 「競合他社の価格を調べてレポートにまとめて」と入力するだけで AI チームが自動で動く
- 投稿・外部送信・課金などの **危険な操作は必ず人間の承認が必要** なので安心
- 何をどのモデルで実行したかの **監査ログ** が全て残る
- 失敗時は自動的に再計画・復旧（Self-Healing）する

### 他の AI エージェントとの違い

| | 他の AI エージェント（AutoGPT, CrewAI 等） | Zero-Employee Orchestrator |
|---|---|---|
| タスク管理 | 実行中のみ追跡 | チケット・Spec・Plan で構造化保存 |
| 品質検証 | なし or 単一モデル | Judge Layer（二段階検証 + Cross-Model） |
| 承認フロー | なし（全自動実行） | 危険操作を必ずブロック・承認後に実行 |
| 障害復旧 | 停止 or 単純リトライ | Self-Healing DAG で自動再計画 |
| 監査ログ | なし or 限定的 | 全操作を記録・追跡可能 |
| コスト管理 | なし | トークン消費・予算をリアルタイム追跡 |
| 経験学習 | なし | Experience Memory で成功・失敗パターンを蓄積 |
| 拡張性 | コード変更が必要 | Skill / Plugin / Extension で柔軟に拡張 |

---

## 2. 主な機能

### Design Interview（設計面談）
業務依頼を受け取った後、AI が追加質問をして要件を詳細化します。「何を作ればいいか曖昧な状態」を解消してから実行に進みます。

### Spec / Plan / Tasks（仕様・計画・タスク）
依頼内容を「仕様書 → 計画 → タスク分解」の形で構造化して保存します。途中で差し戻しや修正が可能で、再利用・監査にも使えます。

### Self-Healing DAG
タスク間の依存関係を有向非巡回グラフ（DAG）で管理します。一部のタスクが失敗しても自動で再計画し、ブロッカーを回避します。

### Judge Layer（品質検証）
AI の出力は必ず二段階で検証されます:
1. **ルールベース判定**: 禁止操作・資格情報漏洩などを高速チェック
2. **クロスモデル検証**: 複数 LLM の出力を比較して信頼性を確認

### Experience Memory（経験記憶）
過去の成功パターンや失敗事例を記憶し、同様のタスクで自動的に活用します。

### Skill / Plugin / Extension（拡張体系）
- **Skill**: 単一目的の処理（例: Web スクレイピング、メール送信）
- **Plugin**: 外部サービスとの連携（例: Slack、Google Drive）
- **Extension**: UI や動作のカスタマイズ

---

## 3. 動作するために必要なもの

### 最小要件

| 項目 | 要件 |
|------|------|
| OS | Windows 10+、macOS 12+、Ubuntu 22.04+ |
| Python | 3.12 以上 |
| Node.js | 18 以上 |
| メモリ | 4 GB 以上（ローカル LLM 使用時は 8 GB 以上推奨） |
| ストレージ | 500 MB 以上（ローカル LLM のモデルファイルは別途） |

### AI（LLM）の接続

AI タスクを実行するには、LLM プロバイダーへの接続が必要です。**最も手軽なのはサブスクリプションモード**（API キー不要）です。

---

## 4. LLM（AI）の接続方法

### 選択肢の比較

| 方法 | 費用 | API キー | 手間 | 推奨用途 |
|------|------|----------|------|---------|
| **Google Gemini 無料 API** ⭐ | **無料**（上限あり） | 必要（無料取得） | 少ない | 最初の一歩に最適 |
| **Ollama（ローカル）** | **完全無料** | 不要 | モデルDL必要 | オフライン・プライバシー重視 |
| **サブスクリプションモード** | **無料** | **不要** | **設定ほぼゼロ** | 試用・テスト向け |
| OpenRouter | 従量課金 | 必要 | 普通 | 複数モデルを一元管理 |
| OpenAI / Anthropic / Google | 従量課金 | 必要 | 普通 | 本格運用・高品質 |

> **推奨**: 安定した利用には **Google Gemini 無料 API** または **Ollama** を推奨します。
> サブスクリプションモードは手軽ですが、外部 Web サービスの可用性に依存するため安定性は劣ります。

---

### 方法 A: Google Gemini 無料 API ⭐（安定した無料利用に推奨）

Google AI Studio では **クレジットカード不要・無料** で API キーが取得でき、一定のリクエスト上限内で Gemini を利用できます。

**手順:**

1. [Google AI Studio](https://aistudio.google.com/) にアクセスし、Google アカウントでログイン
2. 左上メニューの「**Get API key**」をクリック
3. 「**Create API key**」を押してキーをコピー
4. 以下のいずれかの方法で API キーを設定:

   **方法 1: 設定画面から（推奨）**
   アプリの「設定」画面 → 「LLM API キー設定」で Gemini のキーを入力して保存

   **方法 2: CLI コマンドから**
   ```bash
   zero-employee config set GEMINI_API_KEY
   # プロンプトが表示されるのでキーを入力（エコーなし）
   zero-employee config set DEFAULT_EXECUTION_MODE free
   ```

   **方法 3: .env ファイルを直接編集**
   `apps/api/.env` を開き（なければ `.env.example` をコピーして作成）、以下を追記:
   ```env
   GEMINI_API_KEY=<Google AI Studio で取得したキー>
   DEFAULT_EXECUTION_MODE=free
   ```

5. アプリを再起動すると Gemini が自動的に選択されます

> **注意**: 無料枠は1分あたりのリクエスト数などに制限があります。大量処理には有料プランへのアップグレードが必要です。

---

### 方法 B: Ollama（ローカル LLM・完全無料）

Ollama を使うと PC 上で LLM を実行できます。インターネット接続不要・API キー不要・利用回数制限なしで使えます。

**必要なもの**: RAM 8 GB 以上（モデルによっては 16 GB 推奨）

**手順:**

1. [ollama.com](https://ollama.com/) からインストーラーをダウンロード・インストール
2. ターミナルを開き、モデルをダウンロード:
   ```bash
   ollama pull qwen3:8b        # 高品質汎用・推奨（約 5 GB）
   # または
   ollama pull llama3.2        # Meta 汎用（約 2 GB）
   # または
   ollama pull phi3            # 軽量・高速（約 2 GB）
   # または
   ollama pull mistral         # バランス型（約 4 GB）
   ```
3. 以下のいずれかの方法で設定:

   **方法 1: 設定画面から（推奨）**
   アプリの「設定」画面 → 「実行モード」で「無料」を選択

   **方法 2: CLI コマンドから**
   ```bash
   zero-employee config set DEFAULT_EXECUTION_MODE free
   ```

   **方法 3: .env ファイルを直接編集**
   `apps/api/.env` に追記:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   DEFAULT_EXECUTION_MODE=free
   ```
4. アプリを再起動すると Ollama が自動的に使用されます

---

### 方法 C: サブスクリプションモード（API キー不要・試用向け）

**サブスクリプションモード**は、API キーを一切設定しなくても AI が使えるモードです。g4f（gpt4free）ライブラリを使って、各社の **無料 Web エンドポイントを経由して利用**します。

> **⚠️ 重要な注意事項**
>
> - このモードは外部 Web サービスの**非公式な無料アクセスポイント**を利用します
> - **レート制限・一時的な利用不可が頻繁に発生**します
> - プロバイダーの仕様変更により突然使えなくなる可能性があります
> - **あくまで試用・テスト目的**です。安定した利用には方法 A（Gemini 無料 API）または方法 B（Ollama）を強く推奨します

**設定手順:**

以下のいずれかの方法で設定:

**方法 1: 設定画面から**
アプリの「設定」画面 → 「実行モード」で「サブスク」を選択

**方法 2: CLI コマンドから**
```bash
zero-employee config set DEFAULT_EXECUTION_MODE subscription
zero-employee config set USE_G4F true
```

**方法 3: .env ファイルを直接編集**
`apps/api/.env` に以下を設定:
```env
DEFAULT_EXECUTION_MODE=subscription
USE_G4F=true
```

**利用できるプロバイダー（無料・アカウント不要）:**

| プロバイダー名 | 経由サービス | 利用される AI モデル | 備考 |
|--------------|------------|-------------------|------|
| `g4f/GeminiPro` | Google Gemini 無料枠 | Gemini 2.5 Flash | 比較的安定 |
| `g4f/Copilot` | Microsoft Copilot | GPT-4o 相当（変動あり） | 応答速度にばらつきあり |
| `g4f/OpenaiChat` | ChatGPT Web 無料版 | GPT-4o Mini 相当（変動あり） | 制限が厳しい場合あり |
| `g4f/DeepInfra` | DeepInfra 無料枠 | Llama 3.1 70B | オープンモデル |
| `g4f/AirForce` | マルチモデルリレー | GPT-4o Mini 相当（変動あり） | 複数プロバイダーに自動切替 |

> **ヒント**: エラーが出た場合は別のプロバイダーに切り替えてください。
> 最も安定しているのは `g4f/GeminiPro` です。

**アカウント認証が必要なプロバイダー（より高い制限枠）:**

| プロバイダー名 | 必要なアカウント | 利用される AI モデル |
|--------------|----------------|-------------------|
| `g4f/Gemini` | Google アカウント（Gemini Advanced 推奨） | Gemini 2.5 Flash |
| `g4f/CopilotAccount` | Microsoft アカウント（Copilot Pro 推奨） | GPT-4o 相当（変動あり） |

---

### 方法 D: OpenRouter（複数モデルを一元管理・有料）

OpenRouter は複数の LLM プロバイダーを一つの API キーで利用できるサービスです。

**手順:**

1. [openrouter.ai](https://openrouter.ai/) でアカウント作成
2. クレジットを購入し、API キーを取得
3. 以下のいずれかの方法で API キーを設定:

   **設定画面から:** 「設定」→「LLM API キー設定」→ OpenRouter のキーを入力

   **CLI から:**
   ```bash
   zero-employee config set OPENROUTER_API_KEY
   ```

   **.env を直接編集:**
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
   ```

---

### 方法 E: OpenAI / Anthropic / Google 直接 API（本格運用向け）

各プロバイダーの API キーを設定します。設定方法は3通りから選べます:

**設定画面から（推奨）:** アプリの「設定」画面 → 「LLM API キー設定」で各プロバイダーのキーを入力

**CLI コマンドから:**
```bash
zero-employee config set OPENAI_API_KEY        # プロンプトでキーを入力
zero-employee config set ANTHROPIC_API_KEY
zero-employee config set GEMINI_API_KEY
```

**.env ファイルを直接編集:**
```env
# OpenAI（GPT-5.4, GPT-5 Mini 等）
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# Anthropic（Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 等）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Google Gemini（Gemini 2.5 Pro, Flash, Flash Lite 等）
GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxx
```

> 対応モデルは `apps/api/model_catalog.json` で管理されています。
> モデルの追加・削除・コスト更新はこのファイルを編集するか、Model Registry API 経由で行えます。

---

## 5. インストールとセットアップ

### デスクトップアプリ（GUI 版・簡単）

1. [Releases ページ](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases) から最新版をダウンロード
2. インストーラーを実行（依存関係は含まれています）
3. アプリを起動し、セットアップウィザードに従って設定

### ソースから起動（開発者向け）

```bash
# 1. リポジトリをクローン
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator

# 2. セットアップ（初回のみ）
chmod +x setup.sh start.sh
./setup.sh

# 3. 起動
./start.sh

# 4. LLM API キーを設定（以下のいずれかの方法）
# 方法 1: アプリの「設定」画面から入力（推奨）
# 方法 2: CLI から設定
zero-employee config set GEMINI_API_KEY
# 方法 3: .env ファイルを直接編集
cp apps/api/.env.example apps/api/.env
# .env を編集して LLM API キーを追記（方法 A〜E を参照）
```

ブラウザで **http://localhost:5173** にアクセスします。

### 初回セットアップウィザード

アプリを初めて起動すると、以下の手順でウィザードが表示されます:

| ステップ | 内容 |
|---------|------|
| ① 言語選択 | UI 言語と AI 応答言語を選択（日本語推奨） |
| ② 組織設定 | 組織名とミッションを入力 |
| ③ AI 接続 | LLM プロバイダーを選択（後から変更可能） |
| ④ エージェント | 最初の AI エージェント名を設定 |
| ⑤ 完了 | ダッシュボードへ |

---

## 6. 画面の説明と基本操作

### ダッシュボード

アプリのメイン画面です。

- **業務依頼ボックス**: テキストを入力して AI に業務を依頼
- **アクティブチケット**: 現在進行中の業務一覧
- **承認待ち**: あなたの確認を必要とするアクションの数
- **エージェント稼働状況**: AI エージェントの状態
- **コストサマリー**: 今日・今週・今月の API コスト

**業務依頼の例:**
```
競合他社5社の料金ページをリサーチして、比較表をスプレッドシート形式でまとめてください
```

### チケット一覧

全業務依頼（チケット）の一覧です。状態でフィルタリングできます。

**チケットの状態:**

| 状態 | 説明 |
|------|------|
| draft | 下書き |
| open | 受付済み |
| interviewing | 要件確認中（AI が質問中） |
| planning | 計画策定中 |
| ready | 実行待ち |
| in_progress | 実行中 |
| review | レビュー中 |
| done | 完了 |
| closed | クローズ済み |

### 承認画面

AI が「承認が必要な操作」を依頼してきた場合に表示されます。

承認が必要な操作の例:
- 外部サービスへの投稿・送信
- ファイルの上書き・削除
- 課金を伴う操作
- 権限変更

**承認 / 拒否 / 修正依頼** の三択で応答できます。

### 監査ログ

誰が何をどのモデルでいつ実行したかの完全な履歴です。重要操作は全て記録されます。

### コスト管理

LLM API の利用コストをリアルタイムで追跡します。

- 日次・週次・月次のコスト推移グラフ
- モデル別コスト内訳
- 予算上限の設定と超過アラート

---

## 7. チケット（業務依頼）の使い方

### チケットを作成する

1. ダッシュボードの入力ボックスに業務内容を自然言語で入力
2. 「依頼する」ボタンをクリック
3. AI が要件確認（Design Interview）を開始し、不明な点を質問してきます
4. 質問に答えると自動的に計画が作られ、実行が始まります

### 途中で差し戻す / 修正する

チケット詳細画面から:
- 「**差し戻し**」: 前のステップに戻して修正を依頼
- 「**コメント追加**」: 追加の指示や情報を入力
- 「**キャンセル**」: チケットを中断

### 成果物を確認する

チケットが完了すると「成果物（Artifacts）」タブに成果物が保存されます。
- テキスト、JSON、コードなど様々な形式に対応
- バージョン管理されているため、過去の版にも戻せます

---

## 8. 承認フロー

Zero-Employee Orchestrator は「**危険な操作は必ず人間が承認**」という設計原則に基づいています。

### 承認が必要な操作

- 外部への投稿・送信（SNS、メール、Slack 等）
- ファイルの削除・上書き
- 課金・支払いを伴う操作
- 権限・アクセス設定の変更
- 本番環境へのデプロイ・リリース

### 承認の手順

1. ダッシュボードの「承認待ち」カウントが増えたら通知
2. 「承認」画面を開き、内容を確認
3. **承認**: そのまま実行を許可
4. **拒否**: 実行をキャンセル
5. **修正依頼**: コメントを付けて AI に再考を求める

> 承認した操作の記録は全て監査ログに残ります。

---

## 9. スキルとプラグインの拡張

### スキルの追加

スキルは AI が実行できる「機能モジュール」です。

**スキル作成ページから:**
1. 「スキル」→「スキル作成」を開く
2. スキルの説明を自然言語で入力（例: 「Slack チャンネルにメッセージを送る」）
3. AI が自動的にスキルコードを生成
4. レビューして保存

**組み込みスキル（例）:**
- `spec_writer`: 仕様書の自動生成
- `web_scraper`: Web ページのデータ取得
- `report_generator`: レポートの自動作成

### プラグインの追加

プラグインは外部サービスとの連携や業務機能パッケージを提供します。Skill Registry（スキルレジストリ）からインストールできます。

**主なプラグイン:**

| プラグイン | 用途 |
|-----------|------|
| `ai-avatar`（分身AI） | ユーザーの判断基準・文体を学習し、代理レビューや下書き作成を行う |
| `ai-secretary`（秘書AI） | 朝のブリーフィング、次のアクション提案、AI 組織とユーザーの橋渡し |
| `discord-bot` | Discord からチケット作成・進捗確認・承認操作・AI との対話 |
| `slack-bot` | Slack からチケット作成・進捗確認・承認操作・AI との対話 |
| `line-bot` | LINE からチケット作成・進捗確認・承認操作 |
| `youtube` | YouTube チャンネル運用（トレンド分析・台本作成） |
| `research` | 競合分析・市場調査の自動化 |
| `backoffice` | 経理・事務・書類整理の自動化 |

### 分身AI と秘書AI

**分身AI（AI Avatar）** は、あなたの判断パターンや文体を学習し、あなたの「分身」として振る舞います:
- Judge Layer の判断基準にあなたの価値観を反映
- あなた不在時のタスクレビュー・優先度判断（最終承認権限は常にあなたに残ります）
- あなたの文体・トーンでの下書き作成

**秘書AI（AI Secretary）** は、あなたと AI 組織をつなぐ「ハブ」として機能します:
- 朝のブリーフィング（承認待ち・進行中タスク・今日の予定）
- 次にやるべきことの優先度付き提案
- Discord / Slack / LINE 経由でのブリーフィング配信

### チャットツールからの操作

Discord / Slack / LINE の Bot Plugin をインストールすると、普段使っているチャットツールから AI 組織に指示を送れます。

```
/zeo ticket 競合分析レポートを作成して    → チケット作成
/zeo status                              → 進行中タスクの確認
/zeo approve 12345                       → 承認操作
/zeo briefing                            → 今日のブリーフィング
/zeo ask この施策のリスクは？              → AI に質問
```

承認が必要な操作は、チャットツール上でも承認ダイアログが表示されます。

---

## 10. コスト管理

### 実行モードの設定

`apps/api/.env` で `DEFAULT_EXECUTION_MODE` を設定することでコストを制御できます:

| モード | 説明 | 推奨用途 |
|--------|------|---------|
| `quality` | 最高品質モデル（Claude Opus 4.6, GPT-5.4, Gemini 2.5 Pro） | 重要な成果物 |
| `speed` | 高速モデル（Claude Haiku 4.5, GPT-5 Mini, Gemini 2.5 Flash） | 簡単なタスク |
| `cost` | 低コストモデル（Haiku, Mini, Flash Lite, DeepSeek） | 大量処理 |
| `free` | 無料モデル（Gemini 無料枠 / Ollama ローカル） | テスト・開発 |
| `subscription` | 無料（g4f 経由・API キー不要） | 試用向け |

### 予算の設定

設定画面の「コスト管理」から月次予算の上限を設定できます。超過しそうな場合はアラートが通知されます。

---

## 11. トラブルシューティング

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

### AI が応答しない / エラーになる

1. `.env` ファイルに API キーが正しく設定されているか確認
2. Ollama を使っている場合: `ollama serve` が起動しているか確認
3. **サブスクリプションモードの場合**: 外部サービスが一時的に利用不可の可能性があります（Gemini 無料 API または Ollama への切り替えを推奨）
4. バックエンドログを確認:
   ```bash
   cd apps/api
   source .venv/bin/activate
   uvicorn app.main:app --reload
   ```

### サブスクリプションモードで「g4f error」が出る

サブスクリプションモードは外部 Web サービスに依存しているため、一時的に利用できないことがあります。

- 少し待ってからリトライする
- 別のモデルに切り替える（例: `g4f/Copilot` → `g4f/GeminiPro`）
- より安定した Gemini 無料 API キー（[方法 A](#方法-a-google-gemini-無料-api-安定した無料利用に推奨) 参照）に切り替える

### g4f をインストールしていない

```bash
pip install g4f
```

### Gemini API のエラー

- `RESOURCE_EXHAUSTED`: 無料枠の上限に達した → 1 分待つか、有料プランに切り替え
- `API_KEY_INVALID`: キーが間違っている → Google AI Studio で再確認

### Ollama が接続できない

```bash
# Ollama が起動しているか確認
curl http://localhost:11434/api/tags

# 起動していない場合
ollama serve
```

### データベースをリセットしたい

```bash
# SQLite ファイルを削除して再起動（テーブルは自動作成されます）
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

### Python 仮想環境エラー

```bash
cd apps/api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

---

## 12. よくある質問（FAQ）

### Q: 無料で使えますか？ API キーは必要ですか？

**A:** はい、無料で使えます。3つの方法があります:

1. **Google Gemini 無料 API（推奨）**: Google AI Studio で無料の API キーを取得（クレジットカード不要）
2. **Ollama（ローカル LLM）**: PC にモデルをダウンロードして完全無料・オフラインで利用
3. **サブスクリプションモード**: API キー不要で即利用可能（ただし不安定）

**最もバランスの良い始め方:**
```env
GEMINI_API_KEY=<Google AI Studio で取得したキー>
DEFAULT_EXECUTION_MODE=free
```

> **注意**: ChatGPT Plus・Gemini Advanced・Claude Pro などの Web サブスクリプションでは API は使えません。API アクセスは別途必要です。

---

### Q: データはどこに保存されますか？

**A:** デフォルトでは `apps/api/zero_employee_orchestrator.db`（SQLite ファイル）にローカル保存されます。クラウドには送信されません。本番環境では PostgreSQL への変更を推奨します。

---

### Q: AI が間違った操作をしないか心配です

**A:** 以下の仕組みで安全性を確保しています:
- **Judge Layer**: AI の出力を二段階で検証
- **承認フロー**: 危険な操作は必ずブロックして人間に確認
- **監査ログ**: 全操作を記録・追跡可能

---

### Q: 複数人で使えますか？

**A:** はい。組織（Company）単位でユーザーを管理し、ロールベースアクセス制御（RBAC）で権限を設定できます。

| ロール | 権限 |
|--------|------|
| Owner | 全権限 |
| Admin | 組織設定・承認・監査ログ |
| User | 業務依頼・確認 |
| Auditor | 閲覧のみ |
| Developer | Skill/Plugin 開発 |

---

### Q: オフラインで使えますか？

**A:** Ollama でローカル LLM を使えば、インターネット接続なしで動作します（ただしモデルのダウンロードには最初のみネット接続が必要）。

---

### Q: 自分の分身AIや秘書AIを作れますか？

**A:** はい。Plugin として追加できます。

- **分身AI（AI Avatar Plugin）**: あなたの判断基準や文体を学習し、代理レビューや下書き作成を行います。Judge Layer の品質判定にあなたの価値観を反映させることも可能です。ただし、最終承認権限は常にあなた本人に残ります。
- **秘書AI（AI Secretary Plugin）**: 朝のブリーフィング、次のアクション提案、AI 組織の進捗サマリーなど、あなたと AI 組織をつなぐハブとして機能します。Discord / Slack / LINE 経由での通知も可能です。

---

### Q: Discord や Slack から AI 組織に指示を送れますか？

**A:** はい。Discord Bot Plugin、Slack Bot Plugin、LINE Bot Plugin をインストールすることで、チャットツールから直接チケット作成・進捗確認・承認操作・AI との対話が行えます。コマンド例: `/zeo ticket 競合分析レポートを作成して`

---

### Q: モバイルから操作できますか？

**A:** Web ブラウザ対応のため、スマートフォンのブラウザからもアクセスできます（レスポンシブ対応）。また、Discord / Slack / LINE の Bot Plugin を使えば、モバイルのチャットアプリから操作することもできます。

---

## 関連ドキュメント

| ファイル | 内容 |
|---------|------|
| `README.md` | クイックスタート・技術スタック |
| `DESIGN.md` | 実装設計書（DB・API・状態遷移） |
| `MASTER_GUIDE.md` | 実装運用ガイド |
| `Zero-Employee Orchestrator.md` | 最上位基準文書（思想・要件） |
| `SECURITY.md` | セキュリティ設定・本番環境デプロイ |
| `docs/BUILD_GUIDE.md` | 開発者向けビルドガイド |

---
---

# English User Guide

> **v0.1** | Last updated: 2026-03-10
>
> [日本語](#zero-employee-orchestrator--ユーザーガイド--user-guide--用户指南) | English | [中文](#中文用户指南)

## 1. What is this software?

**Zero-Employee Orchestrator** is an **AI Business Orchestration Platform** where you simply instruct tasks in natural language, and multiple AI agents form teams to automatically plan, execute, verify, and report.

### What it can do

- Enter "Research competitors' pricing and create a report" — the AI team automatically takes action
- **Dangerous operations** (posting, sending, billing) **always require human approval**
- Complete **audit logs** of what was done, by which model, and when
- Automatic re-planning and recovery (Self-Healing) on failure

### Difference from other AI agents

| | Other AI Agents (AutoGPT, CrewAI, etc.) | Zero-Employee Orchestrator |
|---|---|---|
| Task management | Tracked during execution only | Structured as Tickets / Spec / Plan |
| Quality verification | None or single model | Judge Layer (two-stage + Cross-Model) |
| Approval flow | None (fully autonomous) | Dangerous operations blocked, human approval required |
| Failure recovery | Stop or simple retry | Self-Healing DAG with automatic re-planning |
| Audit logs | None or limited | All operations recorded and traceable |
| Cost management | None | Real-time token & budget tracking |
| Experience learning | None | Experience Memory for success/failure patterns |
| Extensibility | Requires code changes | Flexible Skill / Plugin / Extension system |

---

## 2. Key Features

### Design Interview
After receiving a task request, the AI asks additional questions to clarify requirements.

### Spec / Plan / Tasks
Request content is structured as "Specification → Plan → Task breakdown" and saved. Modifications and rollbacks are possible at any stage.

### Self-Healing DAG
Task dependencies are managed as a directed acyclic graph (DAG). If some tasks fail, the system automatically re-plans to avoid blockers.

### Judge Layer (Quality Verification)
AI output is always verified in two stages:
1. **Rule-based check**: Fast check for prohibited operations, credential leaks, etc.
2. **Cross-Model Verification**: Compare outputs from multiple LLMs for reliability

### Skill / Plugin / Extension
- **Skill**: Single-purpose processing (e.g., web scraping, email sending)
- **Plugin**: External service integration (e.g., Slack, Google Drive) — installable from GitHub repos
- **Extension**: UI and behavior customization

---

## 3. System Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10+, macOS 12+, Ubuntu 22.04+ |
| Python | 3.12 or higher |
| Node.js | 18 or higher |
| Memory | 4 GB+ (8 GB+ recommended for local LLM) |
| Storage | 500 MB+ (model files require additional space) |

---

## 4. LLM (AI) Connection Methods

| Method | Cost | API Key | Setup | Recommended For |
|--------|------|---------|-------|-----------------|
| **Google Gemini Free API** | **Free** (with limits) | Required (free) | Easy | Best starting point |
| **Ollama (Local)** | **Completely Free** | Not required | Model DL needed | Offline / Privacy |
| **Subscription Mode** | **Free** | **Not required** | **Almost zero** | Testing |
| OpenRouter | Pay-per-use | Required | Normal | Multi-model management |
| OpenAI / Anthropic / Google | Pay-per-use | Required | Normal | Production / High quality |

---

## 5. Installation

### Desktop App (GUI — Easy)

1. Download the latest version from the [Releases page](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases)
2. Run the installer
3. Launch the app and follow the setup wizard

### From Source (For Developers)

```bash
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
chmod +x setup.sh start.sh
./setup.sh
cp apps/api/.env.example apps/api/.env
# Edit .env to add LLM API keys
./start.sh
```

Open **http://localhost:5173** in your browser.

---

## 6. Screens and Basic Operations

### Dashboard
- **Task request box**: Enter tasks in natural language
- **Active tickets**: List of ongoing tasks
- **Pending approvals**: Actions requiring your confirmation
- **Agent status**: AI agent states
- **Cost summary**: Today / this week / this month API costs

### Approval Screen
When the AI requests an operation requiring approval:
- **Approve**: Allow execution
- **Reject**: Cancel execution
- **Request modification**: Send comments to the AI for reconsideration

---

## 7. Skills and Plugins

### Adding Skills
1. Open "Skills" → "Create Skill"
2. Describe the skill in natural language
3. AI automatically generates the skill code
4. Review and save

### Adding Plugins from GitHub
Plugins can be installed from GitHub repositories:

```
POST /api/v1/registry/plugins/search-external?query=keyword
POST /api/v1/registry/plugins/import?source_uri=https://github.com/user/plugin-repo
```

Users can share and publish plugins without requiring developer intervention.

### Built-in Plugins

| Plugin | Purpose |
|--------|---------|
| `ai-avatar` (Avatar AI) | Learns your judgment criteria and writing style for proxy reviews |
| `ai-secretary` (Secretary AI) | Morning briefings, action proposals, bridges you and AI org |
| `discord-bot` | Create tickets, check progress, approve from Discord |
| `slack-bot` | Create tickets, check progress, approve from Slack |
| `line-bot` | Create tickets, check progress, approve from LINE |

---

## 8. Frequently Asked Questions (FAQ)

### Q: Can I use it for free?

**A:** Yes. Three methods:
1. **Google Gemini Free API (recommended)**: Get a free API key from Google AI Studio (no credit card required)
2. **Ollama (Local LLM)**: Download models to your PC — completely free, offline, unlimited
3. **Subscription Mode**: No API key required (but less stable)

### Q: Where is data stored?

**A:** By default, data is stored locally in `apps/api/zero_employee_orchestrator.db` (SQLite). Nothing is sent to the cloud.

### Q: Can I create my own Avatar AI or Secretary AI?

**A:** Yes. They can be added as Plugins. Avatar AI learns your judgment criteria and writing style. Secretary AI generates morning briefings and connects you with the AI organization.

### Q: Can I operate from Discord / Slack?

**A:** Yes. Install the Bot Plugin for Discord / Slack / LINE to create tickets, check progress, approve operations, and chat with AI directly from your messaging app.

---

## Related Documents

| File | Content |
|------|---------|
| `README.md` | Quick start & tech stack |
| `DESIGN.md` | Implementation design (DB, API, state transitions) |
| `SECURITY.md` | Security configuration & production deployment |
| `docs/BUILD_GUIDE.md` | Developer build guide |

---
---

# 中文用户指南

> **v0.1** | 最后更新: 2026-03-10
>
> [日本語](#zero-employee-orchestrator--ユーザーガイド--user-guide--用户指南) | [English](#english-user-guide) | 中文

## 1. 这个软件是什么？

**Zero-Employee Orchestrator** 是一个 **AI 业务编排平台**。您只需用自然语言描述任务，多个 AI 代理就会自动组建团队进行规划、执行、验证和报告。

### 能做什么

- 输入"调查竞争对手的价格并整理成报告" —— AI 团队自动行动
- **危险操作**（发布、发送、计费）**始终需要人类审批**
- 完整的**审计日志**记录谁用什么模型在何时做了什么
- 失败时自动重新规划和恢复（Self-Healing）

### 与其他 AI 代理的区别

| | 其他 AI 代理（AutoGPT、CrewAI 等） | Zero-Employee Orchestrator |
|---|---|---|
| 任务管理 | 仅在执行期间追踪 | 以工单/规格/计划结构化保存 |
| 质量验证 | 无或单一模型 | Judge Layer（两阶段 + Cross-Model） |
| 审批流程 | 无（完全自主执行） | 危险操作阻断，需人类审批 |
| 故障恢复 | 停止或简单重试 | Self-Healing DAG 自动重新规划 |
| 审计日志 | 无或有限 | 记录所有操作，可追溯 |
| 成本管理 | 无 | 实时追踪 Token 消耗和预算 |
| 经验学习 | 无 | Experience Memory 积累成功/失败模式 |
| 扩展性 | 需要修改代码 | 灵活的 Skill / Plugin / Extension 体系 |

---

## 2. 主要功能

### Design Interview（设计面谈）
接收业务请求后，AI 会提出补充问题以明确需求。

### Spec / Plan / Tasks（规格/计划/任务）
请求内容以"规格书 → 计划 → 任务分解"的形式结构化保存。支持修改和回退。

### Self-Healing DAG
任务依赖关系以有向无环图（DAG）管理。部分任务失败时自动重新规划。

### Judge Layer（质量验证）
AI 输出始终经过两阶段验证：
1. **基于规则的检查**：快速检查禁止操作、凭证泄露等
2. **Cross-Model 验证**：比较多个 LLM 的输出以确认可靠性

### Skill / Plugin / Extension（技能/插件/扩展）
- **Skill**：单一目的处理（如：网页抓取、邮件发送）
- **Plugin**：外部服务集成（如：Slack、Google Drive）—— 可从 GitHub 仓库安装
- **Extension**：UI 和行为自定义

---

## 3. 系统需求

| 项目 | 需求 |
|------|------|
| 操作系统 | Windows 10+、macOS 12+、Ubuntu 22.04+ |
| Python | 3.12 以上 |
| Node.js | 18 以上 |
| 内存 | 4 GB 以上（使用本地 LLM 时推荐 8 GB 以上） |
| 存储空间 | 500 MB 以上（模型文件另需空间） |

---

## 4. LLM（AI）连接方式

| 方式 | 费用 | API 密钥 | 设置 | 推荐用途 |
|------|------|----------|------|---------|
| **Google Gemini 免费 API** | **免费**（有限额） | 需要（免费获取） | 简单 | 最佳起步方式 |
| **Ollama（本地）** | **完全免费** | 不需要 | 需下载模型 | 离线/隐私优先 |
| **订阅模式** | **免费** | **不需要** | **几乎为零** | 测试用 |
| OpenRouter | 按量计费 | 需要 | 普通 | 多模型统一管理 |
| OpenAI / Anthropic / Google | 按量计费 | 需要 | 普通 | 生产环境/高质量 |

---

## 5. 安装

### 桌面应用（GUI 版 —— 简单）

1. 从 [Releases 页面](https://github.com/TroroOrosi/Zero-Employee-Orchestrator/releases) 下载最新版本
2. 运行安装程序
3. 启动应用并按照设置向导操作

### 从源代码启动（面向开发者）

```bash
git clone https://github.com/TroroOrosi/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
chmod +x setup.sh start.sh
./setup.sh
cp apps/api/.env.example apps/api/.env
# 编辑 .env 添加 LLM API 密钥
./start.sh
```

在浏览器中打开 **http://localhost:5173**。

---

## 6. 界面和基本操作

### 仪表板
- **任务请求框**：用自然语言输入任务
- **活跃工单**：当前进行中的任务列表
- **待审批**：需要您确认的操作数量
- **代理状态**：AI 代理的运行状态
- **成本摘要**：今日/本周/本月 API 成本

### 审批界面
当 AI 请求需要审批的操作时：
- **批准**：允许执行
- **拒绝**：取消执行
- **要求修改**：附加评论请 AI 重新考虑

---

## 7. 技能和插件

### 添加技能
1. 打开"技能" → "创建技能"
2. 用自然语言描述技能功能
3. AI 自动生成技能代码
4. 审查后保存

### 从 GitHub 添加插件
可以从 GitHub 仓库安装插件：

```
POST /api/v1/registry/plugins/search-external?query=关键词
POST /api/v1/registry/plugins/import?source_uri=https://github.com/user/plugin-repo
```

用户可以共享和发布插件，无需开发者额外操作。

### 内置插件

| 插件 | 用途 |
|------|------|
| `ai-avatar`（分身AI） | 学习您的判断标准和文风，进行代理审查 |
| `ai-secretary`（秘书AI） | 早间简报、行动建议、连接您和 AI 组织 |
| `discord-bot` | 从 Discord 创建工单、查看进度、审批 |
| `slack-bot` | 从 Slack 创建工单、查看进度、审批 |
| `line-bot` | 从 LINE 创建工单、查看进度、审批 |

---

## 8. 常见问题（FAQ）

### Q: 可以免费使用吗？

**A:** 可以。有三种方式：
1. **Google Gemini 免费 API（推荐）**：从 Google AI Studio 获取免费 API 密钥（无需信用卡）
2. **Ollama（本地 LLM）**：将模型下载到电脑 —— 完全免费、离线、无限制
3. **订阅模式**：无需 API 密钥即可使用（但稳定性较差）

### Q: 数据存储在哪里？

**A:** 默认情况下，数据本地存储在 `apps/api/zero_employee_orchestrator.db`（SQLite 文件）中。不会发送到云端。

### Q: 可以创建自己的分身AI和秘书AI吗？

**A:** 可以。它们可以作为插件添加。分身AI学习您的判断标准和文风。秘书AI生成早间简报，连接您和 AI 组织。

### Q: 可以从 Discord / Slack 操作吗？

**A:** 可以。安装 Discord / Slack / LINE 的 Bot 插件后，您可以直接从聊天应用创建工单、查看进度、审批操作和与 AI 对话。

---

## 相关文档

| 文件 | 内容 |
|------|------|
| `README.md` | 快速入门和技术栈 |
| `DESIGN.md` | 实现设计书（DB、API、状态转换） |
| `SECURITY.md` | 安全配置和生产环境部署 |
| `docs/BUILD_GUIDE.md` | 开发者构建指南 |
