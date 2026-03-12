# Zero-Employee Orchestrator — 総合ガイド

> 日本語 | [English](en/OVERVIEW.md) | [中文](zh/OVERVIEW.md)

> 初めてこのプロジェクトを見る方へ向けた、思想・機能・構造のすべてを解説するドキュメントです。

---

## 目次

1. [これは何か](#1-これは何か)
2. [なぜ必要か](#2-なぜ必要か)
3. [基本的な使い方](#3-基本的な使い方)
4. [9層アーキテクチャ](#4-9層アーキテクチャ)
5. [技術スタック](#5-技術スタック)
6. [実装状況](#6-実装状況)
7. [オフライン動作](#7-オフライン動作)
8. [コア機能と拡張機能の境界](#8-コア機能と拡張機能の境界)
9. [外部ツール連携](#9-外部ツール連携)
10. [設計上の注意点と今後の方向性](#10-設計上の注意点と今後の方向性)
11. [ドキュメント一覧](#11-ドキュメント一覧)

---

## 1. これは何か

### 一言で言うと

**自然言語で業務を指示するだけで、複数の AI がチームを組んで計画・実行・検証・改善を行う「AI 業務オーケストレーション基盤」**です。

### もう少し詳しく

Zero-Employee Orchestrator（ZEO）は、以下を一つのソフトウェアで実現します。

- 自然言語で「やりたいこと」を伝えるだけで AI が要件を深掘りする
- AI がタスクを分解し、複数の AI エージェントに役割分担させる
- 危険な操作（投稿・送信・削除・課金）は必ず人間の承認を要求する
- 全操作が監査ログとして記録される
- 失敗しても AI が自動で再計画する（Self-Healing）
- 経験から学び、繰り返すほど精度が上がる

### 他の AI エージェントとの違い

| | AI エージェント (AutoGPT, CrewAI 等) | RPA / n8n / Make | **ZEO** |
|---|---|---|---|
| 入力方法 | テキスト / コード | フロー設計 / ノード配置 | **自然言語** |
| AI チーム | 限定的 | なし / API 呼出 | **役割分担した複数 AI チーム** |
| 品質保証 | なし or 単一モデル | ルール | **Judge Layer 二段階検証** |
| 障害復旧 | 停止 or 単純リトライ | 停止 | **Self-Healing DAG 自動再計画** |
| 承認フロー | なし（全自動） | 手動設定 | **危険操作を自動検出・強制ブロック** |
| 経験学習 | なし | なし | **Experience Memory で蓄積** |
| 拡張性 | コード変更 | プラグイン（限定的） | **Skill / Plugin / Extension 3層** |
| 監査ログ | なし or 限定的 | 限定的 | **全操作記録・追跡可能** |

---

## 2. なぜ必要か

現在の AI ツールには以下の構造的限界があります。

1. **毎回ゼロから始まる** — ChatGPT に同じ背景情報を何度も入力する
2. **手作業の橋渡し** — AI の出力を手動でコピーして次のステップに貼る
3. **品質が分からない** — AI の回答が正しいか自分で確認しなければならない
4. **進捗が見えない** — 昨日 AI に頼んだタスクがどこまで進んだか分からない
5. **暴走が怖い** — AI がメールを誤送信したり、重要データを消したりしないか不安

ZEO はこれらを**アーキテクチャレベルで解決**します。

---

## 3. 基本的な使い方

### 起動

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # 依存関係の自動インストール
./start.sh   # バックエンド + フロントエンドを起動
```

ブラウザで **http://localhost:5173** を開きます。

### 業務フロー

```
1. 自然言語で目的を入力
   「今月の SNS 投稿カレンダーを作って」

2. Design Interview（AI が要件を深掘り）
   「対象 SNS は？」「投稿頻度は？」「ターゲットは？」

3. Spec（何を達成するか）を自動生成

4. Plan（どう実現するか）を自動生成
   工程・担当 AI・推定コスト・必要権限を提示

5. ユーザーが計画を確認し、修正・承認

6. Tasks に分解して並列実行
   進捗・成果物・失敗がリアルタイムで見える

7. Judge Layer が品質検証
   ルールベース判定 + 別モデルによるクロス検証

8. 完了後、成果物を確認して承認
   投稿・送信等の危険操作は承認ダイアログが表示される
```

### LLM の設定

| 方法 | 費用 | 設定 |
|------|------|------|
| **Ollama（ローカル）** | 無料 | `OLLAMA_BASE_URL=http://localhost:11434` |
| **Google Gemini 無料枠** | 無料 | `GEMINI_API_KEY=...` |
| **サブスクリプションモード** | 無料 | `DEFAULT_EXECUTION_MODE=subscription` |
| **OpenRouter** | 従量制 | `OPENROUTER_API_KEY=...` |
| **OpenAI / Anthropic** | 従量制 | 各 API キーを設定 |

API キーは 3 通りの方法で設定できます:
1. **設定画面**: アプリの「設定」→「LLM API キー設定」から入力（推奨）
2. **CLI**: `zero-employee config set GEMINI_API_KEY`
3. **.env ファイル**: `apps/api/.env` を直接編集

---

## 4. 9層アーキテクチャ

ZEO は 9 つの層で構成されています。各層が独立した責務を持ちます。

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: User Layer                                  │
│   自然言語入力 → GUI / CLI / TUI / Discord / Slack   │
├─────────────────────────────────────────────────────┤
│ Layer 2: Design Interview                            │
│   要件の深掘り → 質問生成 → 回答蓄積 → Spec 化       │
├─────────────────────────────────────────────────────┤
│ Layer 3: Task Orchestrator                           │
│   Plan 生成 → DAG 化 → Skill 割当 → コスト見積り     │
│   Self-Healing DAG → 動的再構築                      │
├─────────────────────────────────────────────────────┤
│ Layer 4: Skill Layer                                 │
│   組み込み Skill → Plugin の Skill → Gap 検出         │
│   Local Context Skill（ローカルファイル安全読込）     │
├─────────────────────────────────────────────────────┤
│ Layer 5: Judge Layer                                 │
│   Stage 1: ルールベース高速チェック                   │
│   Stage 2: Cross-Model Verification（別モデル検証）  │
├─────────────────────────────────────────────────────┤
│ Layer 6: Re-Propose Layer                            │
│   差し戻し → Plan Diff → 部分再実行 → 再提案         │
├─────────────────────────────────────────────────────┤
│ Layer 7: State & Memory                              │
│   状態機械 → Experience Memory → Failure Taxonomy    │
│   Artifact Bridge → Knowledge Refresh               │
├─────────────────────────────────────────────────────┤
│ Layer 8: Provider Interface                          │
│   LiteLLM Gateway → Ollama 直接接続 → g4f            │
│   複数 Provider を統一 API で切替                     │
├─────────────────────────────────────────────────────┤
│ Layer 9: Skill Registry                              │
│   Skill / Plugin / Extension の検索・導入・検証       │
└─────────────────────────────────────────────────────┘
```

### 各層の解説

| 層 | 何をするか | 具体例 |
|----|-----------|--------|
| **User Layer** | ユーザーの入力を受け取る | 「競合分析レポートを作って」 |
| **Design Interview** | 曖昧な指示を具体化する | 「どの競合？期間は？重視する指標は？」 |
| **Task Orchestrator** | 実行計画を立てる | 5 工程の DAG を生成、各工程に AI を割当 |
| **Skill Layer** | 実際の作業を実行する | Web 検索、データ整理、レポート生成 |
| **Judge Layer** | 品質を検証する | 禁止事項チェック、別モデルでクロス検証 |
| **Re-Propose Layer** | 失敗時に再挑戦する | 別アプローチで DAG を再構築 |
| **State & Memory** | 状態と経験を記憶する | 成功パターンを保存、次回に活用 |
| **Provider Interface** | AI モデルに接続する | OpenAI / Anthropic / Gemini / Ollama |
| **Skill Registry** | 拡張機能を管理する | Skill の検索・インストール・更新 |

---

## 5. 技術スタック

### バックエンド

| 技術 | 用途 |
|------|------|
| Python 3.12+ | バックエンド言語 |
| FastAPI | REST API フレームワーク |
| SQLAlchemy 2.x (async) | ORM（データベースアクセス） |
| Alembic | DB マイグレーション |
| SQLite / PostgreSQL | データベース |
| LiteLLM | LLM ゲートウェイ |
| httpx | Ollama 直接 HTTP 接続 |

### フロントエンド

| 技術 | 用途 |
|------|------|
| React 19 | UI フレームワーク |
| TypeScript | 型安全な開発 |
| Vite | ビルドツール |
| Tailwind CSS | スタイリング |
| shadcn/ui | UI コンポーネント |
| Zustand | 状態管理 |
| TanStack Query | サーバー状態管理 |

### デスクトップ

| 技術 | 用途 |
|------|------|
| Tauri v2 (Rust) | デスクトップアプリケーション |

### エッジデプロイ

| 技術 | 用途 |
|------|------|
| Cloudflare Workers | エッジ実行 |
| Hono | Workers 向け Web フレームワーク |
| D1 | エッジ SQLite |

---

## 6. 実装状況

### バックエンド（実装済み・実質的なコードあり）

| コンポーネント | ファイル | 行数 | 状態 |
|---------------|---------|------|------|
| Ollama Provider | `providers/ollama_provider.py` | 656 | 実装済み |
| ローカル RAG | `providers/local_rag.py` | 572 | 実装済み |
| Ollama 統合 | `providers/ollama_integration.py` | 511 | 実装済み |
| LLM Gateway | `providers/gateway.py` | 488 | 実装済み |
| g4f Provider | `providers/g4f_provider.py` | 322 | 実装済み |
| Judge Layer | `orchestration/judge.py` | 250 | 実装済み |
| State Machine | `orchestration/state_machine.py` | 239 | 実装済み |
| Experience Memory | `orchestration/experience_memory.py` | 182 | 実装済み |
| Knowledge Refresh | `orchestration/knowledge_refresh.py` | 169 | 実装済み |
| Failure Taxonomy | `orchestration/failure_taxonomy.py` | 152 | 実装済み |
| Cost Guard | `orchestration/cost_guard.py` | 149 | 実装済み |
| DAG | `orchestration/dag.py` | 147 | 実装済み |
| Artifact Bridge | `orchestration/artifact_bridge.py` | 137 | 実装済み |
| Audit Logger | `audit/logger.py` | 137 | 実装済み |
| Secret Manager | `security/secret_manager.py` | 133 | 実装済み |
| Re-Propose | `orchestration/repropose.py` | 120 | 実装済み |
| Quality SLA | `orchestration/quality_sla.py` | 116 | 実装済み |
| Autonomy Boundary | `policies/autonomy_boundary.py` | 113 | 実装済み |
| Design Interview | `orchestration/interview.py` | 112 | 実装済み |
| Approval Gate | `policies/approval_gate.py` | 109 | 実装済み |
| Sanitizer | `security/sanitizer.py` | 83 | 実装済み |

### API エンドポイント（実装済み）

| エンドポイント群 | 主要機能 |
|-----------------|---------|
| `/auth` | ログイン・登録・セッション管理 |
| `/companies` | 会社 CRUD・ダッシュボード |
| `/tickets` | チケット作成・一覧・詳細・状態遷移 |
| `/specs_plans` | Spec / Plan の作成・承認 |
| `/tasks` | タスク作成・実行・完了 |
| `/agents` | エージェント管理・一時停止・再開 |
| `/approvals` | 承認一覧・承認・却下 |
| `/artifacts` | 成果物管理 |
| `/audit` | 監査ログ一覧・フィルタ |
| `/budgets` | 予算ポリシー・コスト管理 |
| `/heartbeats` | 定期実行ポリシー・実行履歴 |
| `/registry` | Skill / Plugin / Extension 検索 |
| `/ollama` | ローカル LLM 直接操作 |
| `/settings` | アプリ設定 |
| WebSocket `/ws/events` | リアルタイムイベント配信 |

### フロントエンド（23 画面）

| 画面 | 状態 | 備考 |
|------|------|------|
| LoginPage | 実装済み | ログイン・登録・Google OAuth |
| SetupPage | 実装済み | 6 ステップウィザード |
| DashboardPage | 実装済み | 統計・自然言語入力・推奨アクション |
| InterviewPage | 実装済み | 7 質問の Design Interview |
| SettingsPage | 実装済み | LLM API キー設定・実行モード・Ollama・プロバイダー接続 |
| ReleasesPage | 実装済み | バージョン管理・ダウンロード |
| DownloadPage | 実装済み | OS 別インストーラー配布 |
| TicketListPage | UI あり | データ接続は部分的 |
| TicketDetailPage | UI あり | セクション構造のみ |
| SpecPlanPage | UI あり | DAG 可視化プレースホルダー |
| OrgChartPage | UI あり | 組織構造のスケルトン |
| ApprovalsPage | UI あり | フィルター・テーブル構造 |
| AuditPage | UI あり | フィルター・テーブル構造 |
| HeartbeatsPage | UI あり | ポリシー・実行履歴構造 |
| CostsPage | UI あり | 予算・支出構造 |
| ArtifactsPage | UI あり | 成果物一覧構造 |
| SkillsPage | UI あり | 検索・ステータスバッジ |
| SkillCreatePage | UI あり | 作成フォーム |
| PluginsPage | UI あり | ブラウザー・インストーラー |
| PermissionsPage | UI あり | 権限管理ダッシュボード |
| AgentMonitorPage | UI あり | エージェント監視ダッシュボード |

### ORM モデル（21 テーブル）

Company, User, Department, Team, Agent, Project, Ticket, TicketThread, Spec, Plan, Task, TaskRun, Artifact, Review, ApprovalRequest, HeartbeatPolicy, HeartbeatRun, BudgetPolicy, CostLedger, Skill, Plugin, Extension, ToolConnection, ToolCallTrace, PolicyPack, SecretRef, AuditLog

### テスト

| テスト | 対象 |
|--------|------|
| `test_auth.py` | 認証 |
| `test_companies.py` | 会社管理 |
| `test_tickets.py` | チケット |
| `test_health.py` | ヘルスチェック |
| `test_state_machine.py` | 状態遷移 |
| `test_cost_guard.py` | コスト管理 |
| `test_failure_taxonomy.py` | 失敗分類 |
| `test_audit_logger.py` | 監査ログ |
| `test_registry.py` | レジストリ |
| `test_ollama_provider.py` | Ollama |
| `test_ollama_integration.py` | Ollama 統合 |

---

## 7. オフライン動作

ZEO はクラウド API なしでも動作します。

### 完全オフライン構成

```
Ollama（ローカル LLM） + SQLite（ローカル DB） + ローカル RAG
```

#### セットアップ

```bash
# 1. Ollama をインストール
# https://ollama.com/ からダウンロード

# 2. モデルをダウンロード
ollama pull qwen3:8b        # 汎用（推奨）
ollama pull qwen3-coder:30b # コーディング特化

# 3. .env に設定
echo "OLLAMA_BASE_URL=http://localhost:11434" >> apps/api/.env
echo "DEFAULT_EXECUTION_MODE=free" >> apps/api/.env
```

#### CLI モード

```bash
zero-employee local                      # デフォルトモデルでチャット
zero-employee local --model qwen3:8b     # モデル指定
zero-employee local --lang ja            # 日本語モード
zero-employee models                     # インストール済みモデル一覧
zero-employee pull qwen3:8b              # モデルダウンロード
```

#### オフラインで使える機能

| 機能 | 可否 | 備考 |
|------|------|------|
| Design Interview | 可能 | Ollama モデルで推論 |
| Spec / Plan 生成 | 可能 | Ollama モデルで推論 |
| タスク実行（ローカル Skill） | 可能 | ファイル操作、分析等 |
| Judge Layer（ルールベース） | 可能 | Stage 1 のみ |
| Judge Layer（Cross-Model） | 条件付き | 複数 Ollama モデルが必要 |
| 承認フロー | 可能 | ローカル UI で完結 |
| 監査ログ | 可能 | SQLite に記録 |
| ローカル RAG 検索 | 可能 | TF-IDF ベース |
| Experience Memory | 可能 | SQLite に記録 |
| 外部 API 連携 | 不可 | オンライン必須 |

### 対応ローカルモデル

| モデル | 用途 |
|--------|------|
| `qwen3:8b` / `qwen3:32b` | 高品質汎用推論 |
| `qwen3-coder:30b` | コーディング特化 |
| `llama3.2` | Meta 汎用モデル |
| `mistral` | Mistral 汎用モデル |
| `phi3` | Microsoft 軽量モデル |
| `deepseek-coder-v2` | コーディング特化 |
| `codellama` | Meta コード特化 |
| `gemma2` | Google 軽量モデル |

Ollama にインストール済みのモデルは自動検出されます。

---

## 8. コア機能と拡張機能の境界

ZEO は**「最初から全部入りにしない」**設計を採用しています。

### コア（本体に必須）

認証・権限・監査・状態管理・実行制御・DAG・Judge・承認フロー・Experience Memory

→ これらがないと「AI 業務オーケストレーション」が成立しない

### Skill（最小能力単位）

ファイル整理、翻訳、台本生成、競合分析 等

→ `skills/builtin/` に 6 つの組み込み Skill を同梱

### Plugin（業務機能パッケージ）

分身AI、秘書AI、Discord Bot、Slack Bot、LINE Bot、YouTube 運用、リサーチ、バックオフィス 等

→ `plugins/` にマニフェスト定義済み（8 Plugin）。業務特化ロジックは本体に入れない

### Extension（システム基盤拡張）

OAuth 認証、MCP 接続、通知、Obsidian 連携 等

→ `extensions/` にマニフェスト定義済み。接続先の追加は本体に入れない

**判断基準**: 「それがないと承認・監査・実行制御が成立しないか？」

- Yes → コア
- No → Skill / Plugin / Extension

詳細は [docs/dev/FEATURE_BOUNDARY.md](dev/FEATURE_BOUNDARY.md) を参照。

---

## 9. 外部ツール連携

### 現在定義済みの連携先

| 連携先 | 種別 | 状態 | 説明 |
|--------|------|------|------|
| **分身AI** | Plugin | manifest あり | ユーザーの判断基準・文体を学習し代理行動 |
| **秘書AI** | Plugin | manifest あり | ブリーフィング・優先度提案・AI組織との橋渡し |
| **Discord** | Plugin | manifest あり (v0.2.0) | Bot 経由でチケット作成・承認・対話・ブリーフィング |
| **Slack** | Plugin | manifest あり (v0.2.0) | Slash Command でチケット作成・承認・対話・ブリーフィング |
| **LINE** | Plugin | manifest あり | LINE Bot でチケット作成・承認・通知 |
| **Obsidian** | Extension | manifest あり | Vault を Knowledge Source として双方向連携 |
| **MCP** | Extension | manifest あり | Model Context Protocol 対応ツール接続 |
| **Google OAuth** | Extension | manifest あり | Google アカウント認証 |
| **通知全般** | Extension | manifest あり | Slack / Discord / LINE / メール通知 |

### 分身AI / 秘書AI

**分身AI（AI Avatar Plugin）** はユーザーの判断基準・文体を学習し、ユーザーの「分身」として振る舞います。Judge Layer の判断基準にユーザーの価値観を反映させることも可能です。

**秘書AI（AI Secretary Plugin）** はユーザーと AI 組織をつなぐ「ハブ」として機能し、朝のブリーフィング、次のアクション提案、進捗サマリーの生成を行います。チャットツール Plugin と連携して Discord / Slack / LINE 経由でブリーフィングを配信できます。

### Discord / Slack / LINE からのマルチエージェント操作

Discord / Slack / LINE Bot Plugin をインストールすると、チャットアプリから直接 ZEO のマルチエージェントに指示を送れます。

```
Discord/Slack/LINE → Bot がメッセージを受信
  → ZEO API にチケット作成リクエスト
    → Design Interview → Plan → Tasks 実行
      → 結果をチャットチャンネルに返信
```

承認が必要な操作は、チャットツール上でも承認ダイアログが表示されます。

**コマンド例:**
```
/zeo ticket 競合分析レポートを作成して
/zeo status
/zeo briefing
/zeo ask この施策のリスクは？
```

### Obsidian 連携

Obsidian Extension をインストールすると、Vault 内の Markdown ファイルを Knowledge Source として活用できます。

- **インポート**: Vault 内のノートを RAG に取り込み
- **エクスポート**: Spec / Plan / Tasks / 成果物を Vault に Markdown 出力
- **リンク活用**: Obsidian の `[[内部リンク]]` 構造を知識グラフとして参照
- **完全オフライン**: Obsidian Sync は不要、ローカル Vault のパスを設定するだけ

---

## 10. 設計上の注意点と今後の方向性 (v0.1)

### 過剰設計にならないための原則

ZEO の設計文書は非常に広範囲をカバーしていますが、実装では以下を守ります。

1. **MVP ファースト** — まず end-to-end のフローを通すことが最優先
2. **機能は Plugin で追加** — 本体を肥大化させない
3. **9層は責務分離のガイド** — 全層を完全実装する必要はない
4. **画面は段階的に充実** — UI の骨格は整っており、データ接続を進める
5. **コミュニティ拡張** — ユーザーが Plugin を共有・公開し、外部サービス連携を拡大

### v0.1 機能肥大化レビュー

以下の機能は v0.1 コードベースに含まれているが、コア機能ではなく**拡張機能として位置づける**。
将来のバージョンで独立した Extension / Skill / Plugin パッケージとして分離予定。

| 機能 | 移行先 | 理由 |
|------|--------|------|
| Sentry 連携 | Extension | エラー監視はコアの承認・監査・実行制御に不要 |
| AI 調査ツール | Skill | DB/ログ調査は単一目的タスク |
| 仮説検証エンジン | Plugin | マルチエージェント仮説検証は高度機能 |
| MCP サーバー | Extension | 接続先拡張であり、コア必須ではない |
| 外部スキルインポート | Extension | Registry の拡張機能 |

詳細は [docs/dev/FEATURE_BOUNDARY.md](dev/FEATURE_BOUNDARY.md) を参照。

### v0.1 Final 追加機能 (2026-03-11)

| 機能 | 説明 |
|------|------|
| **ZEO-Bench** | Judge Layer の Cross-Model Verification を200問で定量評価するベンチマーク |
| **矛盾検出エンジン** | セマンティック類似度・否定パターン・数値不整合・時系列矛盾を検出 |
| **汎用ドメイン Skill** | 5つの業務汎用スキル（コンテンツ生成・競合分析・トレンド分析・KPI分析・戦略アドバイス） |
| **Artifact Bridge 強化** | DAG内の成果物自動連携・ドメイン横断変換・互換性マトリクス |
| **カオステスト** | Self-Healing DAG の復旧成功率・復旧時間を計測するフォルト注入テスト |

### マルチエージェントの能力と制約

| 能力 | 状態 | 説明 |
|------|------|------|
| **Web操作** | 対応（Tool Connection経由） | MCP / REST API / CLI ツール経由でWebサービスに接続可能。ブラウザ自動操作は Plugin で拡張予定 |
| **ファイル要求** | 対応 | Design Interview でユーザーに必要なファイル・資料を要求。Knowledge Store でファイル権限・フォルダ位置を記憶 |
| **外部ツール連携** | 対応 | REST API / GraphQL / gRPC / Webhook / MCP / CLI ツール（gh, aws, gcloud 等）に対応 |
| **ローカルファイル** | 対応 | Local Context Skill でローカルファイルを安全に読み込み分析。許可ディレクトリ制限付き |
| **リアルタイム監視** | 対応 | WebSocket によるタスク実行状況のリアルタイム配信 |
| **自律実行** | 制限付き | 調査・分析・下書き作成は自律実行可能。投稿・送信・課金・削除は承認必須 |

### 現在の課題

| 課題 | 詳細 |
|------|------|
| フロントエンドのデータ接続 | 12 画面が UI スケルトンのみ（バックエンド API は存在） |
| features/ モジュール | 11 モジュールが `.gitkeep` のみ（ロジックは pages 内に直接記述） |
| packages/ 共有ライブラリ | 5 パッケージが `.gitkeep` のみ |
| Worker のコアロジック | ランナー・エグゼキューター構造はあるがロジックは薄い |
| E2E テスト | 未実装 |

### 今後の優先順位

1. **フロントエンド ←→ バックエンド接続の完成**
   - チケット一覧/詳細のデータバインド
   - 承認画面のリアルタイム更新
   - 監査ログ画面のフィルター動作

2. **Design Interview → Spec → Plan → Task 実行の E2E フロー**
   - 自然言語入力から成果物生成まで一気通貫

3. **Plugin / Extension のインストール機構**
   - マニフェストベースのロード・実行

4. **Worker の本格稼働**
   - バックグラウンドタスク実行
   - Heartbeat スケジューラー

---

## 11. ドキュメント一覧

> 全ドキュメントの詳細な説明（目的・対象読者・主な内容）は **[`docs/MD_FILES_INDEX.md`](MD_FILES_INDEX.md)** を参照してください。

**利用者向け（`docs/`）:**

| ファイル | 内容 | 対象読者 |
|---------|------|---------|
| `README.md` | クイックスタート・技術スタック | 全員 |
| `docs/ABOUT.md` | なぜ ZEO が必要か・従来ツールとの比較 | 非エンジニア・経営者 |
| `docs/USER_GUIDE.md` | セットアップから操作方法まで | エンドユーザー |
| **`docs/OVERVIEW.md`（本書）** | **思想・機能・構造の総合解説** | **初見の方** |
| `docs/FEATURES.md` | 実装済み機能の全体一覧（27セクション） | 機能確認・評価者 |
| `docs/SECURITY.md` | セキュリティポリシー・デプロイ前チェックリスト | 運用者 |
| `docs/CHANGELOG.md` | 変更履歴 | 全員 |
| `docs/AI_SELF_IMPROVEMENT_ROADMAP.md` | AI Self-Improvement ロードマップ | 開発者・研究者 |
| `docs/Zero-Employee Orchestrator.md` | 最上位基準文書（思想・要件） | 設計者 |
| `docs/MD_FILES_INDEX.md` | 全 `.md` ファイルのインデックス | 全員 |

**開発者向け（`docs/dev/`）:**

| ファイル | 内容 | 対象読者 |
|---------|------|---------|
| `docs/dev/DESIGN.md` | 実装設計書（DB・API・状態遷移） | 実装者 |
| `docs/dev/MASTER_GUIDE.md` | 実装運用ガイド | AI エージェント・実装者 |
| `docs/dev/BUILD_GUIDE.md` | ゼロからの構築手順（フェーズ別コード付き） | ソースビルド利用者 |
| `docs/dev/FEATURE_BOUNDARY.md` | コア vs 拡張の機能境界定義 | 開発者 |
| `docs/dev/instructions_section2〜7` | 各領域の実装指示 | 実装者 |
| `CLAUDE.md` | Claude Code 向け開発ガイド | AI エージェント |

**その他:**

| ファイル | 内容 | 対象読者 |
|---------|------|---------|
| `apps/edge/README.md` | Cloudflare Workers デプロイ方式比較 | インフラ担当 |
| `apps/edge/full/README.md` | Full Workers（方式B）セットアップ | インフラ担当 |
| `apps/edge/proxy/README.md` | Proxy（方式A）セットアップ | インフラ担当 |

---

## ディレクトリ構成

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                    # FastAPI バックエンド
│   │   ├── app/
│   │   │   ├── core/           # 設定・DB・セキュリティ・i18n
│   │   │   ├── api/routes/     # REST API (20 ルート)
│   │   │   ├── api/ws/         # WebSocket
│   │   │   ├── models/         # ORM モデル（21 テーブル / 18 ファイル）
│   │   │   ├── schemas/        # Pydantic DTO
│   │   │   ├── services/       # ビジネスロジック
│   │   │   ├── repositories/   # DB 入出力抽象化
│   │   │   ├── orchestration/  # DAG・Judge・状態機械・Memory（18 モジュール）
│   │   │   ├── heartbeat/      # 定期実行スケジューラ
│   │   │   ├── providers/      # LLM Gateway・Ollama・g4f・RAG
│   │   │   ├── tools/          # 外部ツール接続（MCP/Webhook/API/CLI）
│   │   │   ├── policies/       # 承認ゲート・自律実行境界
│   │   │   ├── security/       # Secret Manager・Sanitizer・IAM
│   │   │   ├── integrations/   # Sentry・MCP Server・外部スキル（※拡張機能）
│   │   │   ├── audit/          # 監査ログ
│   │   │   └── tests/          # テスト
│   │   └── alembic/            # DB マイグレーション
│   ├── desktop/                # Tauri デスクトップアプリ
│   │   └── ui/src/             # React フロントエンド (23 画面)
│   ├── edge/                   # Cloudflare Workers
│   │   ├── proxy/              # 方式A: リバースプロキシ
│   │   └── full/               # 方式B: Hono + D1 完全移植
│   └── worker/                 # バックグラウンドワーカー
├── skills/
│   ├── builtin/                # 組み込み Skill (6 個)
│   └── templates/              # Skill テンプレート
├── plugins/                    # Plugin マニフェスト
│   ├── ai-avatar/              # 分身AI
│   ├── ai-secretary/           # 秘書AI
│   ├── discord-bot/            # Discord Bot
│   ├── slack-bot/              # Slack Bot
│   ├── line-bot/               # LINE Bot
│   ├── youtube/                # YouTube 運用
│   ├── research/               # リサーチ
│   ├── backoffice/             # バックオフィス
│   └── ai-self-improvement/    # AI 自己改善
├── extensions/                 # Extension マニフェスト
│   ├── oauth/                  # OAuth 認証
│   ├── mcp/                    # MCP 接続
│   ├── notifications/          # 通知
│   └── obsidian/               # Obsidian 連携
├── packages/                   # 共有パッケージ
│   ├── config/                 # 設定
│   ├── sdk/                    # SDK
│   ├── skill-manifest/         # Skill マニフェスト
│   ├── types/                  # 共有型定義
│   └── ui/                     # 共有 UI
├── docs/                       # 利用者向けドキュメント
│   └── dev/                    # 開発者向けドキュメント
├── scripts/                    # 開発・デプロイスクリプト
│   ├── dev/                    # 開発用
│   ├── lint/                   # リント
│   ├── release/                # リリース
│   └── seed/                   # シードデータ
├── examples/                   # サンプル・例
├── docker/                     # Docker 設定
├── assets/                     # ロゴ・画像
├── Dockerfile                  # Rootless コンテナ
├── docker-compose.yml          # 全サービス一括起動
├── setup.sh                    # セットアップスクリプト
└── start.sh                    # 起動スクリプト
```

---

*Zero-Employee Orchestrator — AI が、組織として働く。*
