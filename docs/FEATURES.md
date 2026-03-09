# Zero-Employee Orchestrator — 機能一覧

> 最終更新: 2026-03-09  
> 対象バージョン: 現在の `main` ブランチ

---

## 概要

Zero-Employee Orchestrator は、自然言語で業務を定義し、複数の AI エージェントを役割分担させ、人間の承認と監査可能性を前提に業務を実行・再計画・改善できる **AI オーケストレーション基盤**です。

本ドキュメントでは、現在実装されている機能と可能なことを網羅的にまとめます。

---

## 目次

1. [9 層アーキテクチャ](#1-9-層アーキテクチャ)
2. [自然言語入力と Design Interview](#2-自然言語入力と-design-interview)
3. [Spec / Plan / Tasks — 構造化された中間成果物](#3-spec--plan--tasks--構造化された中間成果物)
4. [DAG ベース Task Orchestrator](#4-dag-ベース-task-orchestrator)
5. [状態機械による厳密なライフサイクル管理](#5-状態機械による厳密なライフサイクル管理)
6. [Judge Layer — 品質保証と検証](#6-judge-layer--品質保証と検証)
7. [Cost Guard — コスト見積もりと予算制御](#7-cost-guard--コスト見積もりと予算制御)
8. [Quality SLA — 品質モードとモデル選択](#8-quality-sla--品質モードとモデル選択)
9. [Self-Healing / Re-Propose — 障害時の自動復旧と再計画](#9-self-healing--re-propose--障害時の自動復旧と再計画)
10. [Failure Taxonomy — 障害分類と学習](#10-failure-taxonomy--障害分類と学習)
11. [Experience Memory — 経験知の蓄積と再利用](#11-experience-memory--経験知の蓄積と再利用)
12. [承認フロー](#12-承認フロー)
13. [監査ログ](#13-監査ログ)
14. [エージェント管理](#14-エージェント管理)
15. [Skill / Plugin / Extension — 3 層拡張体系](#15-skill--plugin--extension--3-層拡張体系)
16. [LLM Gateway — マルチプロバイダー対応](#16-llm-gateway--マルチプロバイダー対応)
17. [バックグラウンドワーカー](#17-バックグラウンドワーカー)
18. [Heartbeat — 定期実行と死活監視](#18-heartbeat--定期実行と死活監視)
19. [組織管理（会社・部門・チーム）](#19-組織管理会社部門チーム)
20. [権限モデル](#20-権限モデル)
21. [フロントエンド UI](#21-フロントエンド-ui)
22. [REST API](#22-rest-api)
23. [WebSocket リアルタイム通信](#23-websocket-リアルタイム通信)
24. [Cloudflare Workers デプロイ](#24-cloudflare-workers-デプロイ)
25. [デスクトップアプリ (Tauri)](#25-デスクトップアプリ-tauri)
26. [CLI / TUI](#26-cli--tui)

---

## 1. 9 層アーキテクチャ

Zero-Employee Orchestrator は以下の 9 層構造で設計・実装されています。

| レイヤー | 名称 | 役割 |
|---------|------|------|
| Layer 1 | **User Layer** | GUI / CLI / TUI / チャット入力。自然言語で AI 組織を起動 |
| Layer 2 | **Design Interview** | 要件を深掘りする質問生成と回答蓄積。Spec を構造化 |
| Layer 3 | **Task Orchestrator** | Plan/DAG 生成、Skill 割当、コスト見積り、再計画 |
| Layer 4 | **Skill Layer** | 単一目的の専門 Skill 実行 + Local Context Skill |
| Layer 5 | **Judge Layer** | Two-stage Detection + Cross-Model Verification |
| Layer 6 | **Re-Propose Layer** | 差し戻し時の再提案 + 動的 DAG 再構築 |
| Layer 7 | **State & Memory** | 状態機械 + Experience Memory + Failure Taxonomy |
| Layer 8 | **Provider Interface** | LiteLLM Gateway によるマルチ LLM 接続 |
| Layer 9 | **Skill Registry** | Skill / Plugin / Extension の公開・検索・インストール |

---

## 2. 自然言語入力と Design Interview

### 自然言語入力

ダッシュボードから自然言語で業務依頼を入力できます。

```
例: 「競合分析レポートを作成して、来週の会議資料にまとめてほしい」
```

入力された内容は Ticket として登録され、Design Interview が自動的に開始されます。

### Design Interview

7 つの標準質問テンプレートを使い、要件を構造的に深掘りします。

| カテゴリ | 質問例 |
|---------|--------|
| **目的** | この業務の最終的な目的は何ですか？ |
| **制約** | 守るべき制約条件はありますか？（予算、期限、品質基準など） |
| **受け入れ基準** | 完了条件（受け入れ基準）は何ですか？ |
| **リスク** | 想定されるリスクや注意点はありますか？ |
| **優先度** | 優先順位はどの程度ですか？（高/中/低） |
| **外部連携** | 外部サービスへの接続や送信は必要ですか？ |
| **承認工程** | 人間の承認が必要な工程はありますか？ |

回答が完了すると、Interview の回答から Spec（仕様書）を自動生成できます。

---

## 3. Spec / Plan / Tasks — 構造化された中間成果物

すべての業務依頼は「会話ログ」ではなく、構造化された中間成果物として保存されます。

### Spec（仕様書）

- **目的** (`objective`): 業務の最終目標
- **制約条件** (`constraints_json`): 予算、期限、品質基準
- **受け入れ基準** (`acceptance_criteria_json`): 完了の判断基準
- **リスクノート** (`risk_notes`): 想定リスク
- **バージョン管理**: 仕様変更時にバージョンを記録

### Plan（実行計画）

- Spec に基づいて生成される実行計画
- コスト見積もり付き
- 承認フロー付き（承認後のみタスク生成）

### Tasks（個別タスク）

- Plan から分解された個別の実行単位
- DAG（有向非循環グラフ）で依存関係を管理
- 各タスクに担当エージェント、推定コスト、推定時間を割当

---

## 4. DAG ベース Task Orchestrator

タスクの依存関係を DAG（有向非循環グラフ）で管理し、最適な実行順序を自動決定します。

### 主な機能

| 機能 | 説明 |
|------|------|
| **Ready ノード検出** | 依存タスクがすべて完了したタスクを自動的に実行可能状態にする |
| **クリティカルパス計算** | 最長パスの所要時間を計算し、完了予測を提供 |
| **コスト合計見積り** | DAG 全体の推定コストを集計 |
| **承認ポイント検出** | 人間承認が必要なタスクを特定 |
| **Self-Healing DAG** | 障害時に DAG を動的に再構築（retry / skip / replan） |

### Self-Healing 戦略

```
retry   → 失敗ノードを pending に戻してリトライ
skip    → 失敗ノードをスキップし、依存ノードの制約を解除
replace → 代替パスを作成（外部ロジック必要）
replan  → DAG 全体の再計画をトリガー
```

---

## 5. 状態機械による厳密なライフサイクル管理

4 種類の状態機械で、すべてのリソースのライフサイクルを厳密に管理します。

### Ticket 状態遷移

```
draft → open → interviewing → planning → ready → in_progress → review → done → closed
                                                      ↓              ↓         ↓
                                                   blocked        rework    reopened
```

### Task 状態遷移

```
pending → ready → running → succeeded → verified → archived
                    ↓            ↓
               awaiting_approval failed → retrying → running
                    ↓
                  blocked
```

### Approval 状態遷移

```
requested → approved → executed
          → rejected → superseded
          → expired  → requested (再要求)
          → cancelled
```

### Agent 状態遷移

```
provisioning → idle → busy → idle
                 ↓      ↓
              paused   error → idle / paused / decommissioned
                 ↓
          decommissioned
```

すべての状態遷移は履歴として記録され、不正な遷移はエラーとして防止されます。

---

## 6. Judge Layer — 品質保証と検証

3 段階の品質検証メカニズムを実装しています。

### Stage 1: RuleBasedJudge（ルールベース一次判定）

- カスタムルールの動的追加が可能
- 高速な一次フィルタリング
- 重大度別スコアリング（error: -0.2 / warning: -0.05）

### Stage 2: PolicyPackJudge（ポリシー準拠チェック）

**危険操作の検出:**

| 検出対象 |
|---------|
| `external_send` — 外部送信 |
| `publish` / `post` — 公開・投稿 |
| `delete` — 削除 |
| `charge` — 課金 |
| `git_push` / `git_release` — Git 操作 |
| `permission_change` — 権限変更 |
| `credential_update` — 認証情報更新 |

**認証情報漏洩チェック:**

- `sk-`, `Bearer`, `api_key=`, `password=`, `secret=`, `token=`, `AKIA` パターンを検出

### Stage 3: CrossModelJudge（クロスモデル検証）

- 複数 LLM の出力を比較して信頼性を検証
- 構造一致度と値一致度のスコアリング
- HIGH / CRITICAL 品質モードで使用

### 判定結果

| 判定 | 意味 |
|------|------|
| `PASS` | 合格 |
| `WARN` | 警告あり（続行可能） |
| `FAIL` | 不合格（実行停止） |
| `NEEDS_REVIEW` | 人間レビュー必要 |

---

## 7. Cost Guard — コスト見積もりと予算制御

### コスト見積もり

モデルファミリー別のトークン単価テーブルを内蔵し、実行前にコストを見積もります。

| モデル | 入力 ($/1K tokens) | 出力 ($/1K tokens) |
|--------|-------------------|-------------------|
| GPT-4 | 0.03 | 0.06 |
| GPT-4o | 0.005 | 0.015 |
| GPT-4o-mini | 0.00015 | 0.0006 |
| Claude 3 Opus | 0.015 | 0.075 |
| Claude 3.5 Sonnet | 0.003 | 0.015 |
| Claude 3 Haiku | 0.00025 | 0.00125 |

### 予算チェック

| 判定 | 条件 | 動作 |
|------|------|------|
| `ALLOW` | 使用率 < 80% | 実行許可 |
| `WARN` | 80% ≤ 使用率 < 100% | 警告付き許可 |
| `BLOCK` | 使用率 ≥ 100% | 実行ブロック |

### 予算ポリシー管理（UI）

- 日次 / 週次 / 月次の予算上限設定
- 閾値到達時のタスク自動停止
- コスト台帳によるトランザクション単位の追跡

---

## 8. Quality SLA — 品質モードとモデル選択

タスクの重要度に応じて 4 つの品質モードを提供します。

| モード | 推奨モデル | リトライ上限 | Judge 閾値 | 人間レビュー | クロスモデル検証 |
|--------|-----------|-------------|-----------|------------|--------------|
| **DRAFT** | GPT-4o-mini, Claude 3 Haiku | 1 回 | 50% | 不要 | なし |
| **STANDARD** | GPT-4o, Claude 3.5 Sonnet | 2 回 | 70% | 不要 | なし |
| **HIGH** | GPT-4o, Claude 3.5 Sonnet | 3 回 | 85% | 不要 | **あり** |
| **CRITICAL** | Claude 3 Opus, GPT-4 | 5 回 | 95% | **必須** | **あり** |

品質モードに応じてモデル選択、リトライ戦略、検証レベルが自動調整されます。

---

## 9. Self-Healing / Re-Propose — 障害時の自動復旧と再計画

### Re-Propose（再提案）

失敗やリジェクト時に、原因を分類して代替案を生成します。

| 失敗カテゴリ | 説明 |
|-------------|------|
| `quality_insufficient` | 品質基準を満たしていない |
| `scope_mismatch` | 要件との不一致 |
| `cost_exceeded` | 予算超過 |
| `policy_violation` | ポリシー違反 |
| `execution_error` | 実行時エラー |
| `timeout` | タイムアウト |
| `skill_gap` | 必要な Skill が不足 |
| `dependency_broken` | 依存関係の崩壊 |
| `model_incompatible` | モデル特性による不適合 |

### Plan Diff

再提案時には、元の計画との差分（追加・削除・変更されたタスク、コスト変動、時間変動）を構造化して提示します。

---

## 10. Failure Taxonomy — 障害分類と学習

9 カテゴリ × 4 重大度の障害分類体系を実装しています。

### 障害カテゴリ

| カテゴリ | 説明 |
|---------|------|
| `LLM_ERROR` | LLM プロバイダ障害 |
| `TOOL_ERROR` | ツール実行障害 |
| `VALIDATION_ERROR` | 入出力検証障害 |
| `BUDGET_ERROR` | 予算超過 |
| `TIMEOUT_ERROR` | タイムアウト |
| `PERMISSION_ERROR` | 権限不足 |
| `DEPENDENCY_ERROR` | 依存タスク障害 |
| `HUMAN_REJECTION` | 人間による差し戻し |
| `SYSTEM_ERROR` | システム内部エラー |

### 重大度レベル

| 重大度 | 意味 | 対応 |
|--------|------|------|
| `LOW` | 軽微 | 自動リトライで回復可能 |
| `MEDIUM` | 中程度 | 代替手段で回復可能 |
| `HIGH` | 重大 | 人間介入が必要 |
| `CRITICAL` | 致命的 | 即座にエスカレーション |

### 学習機能

- 障害の発生回数を追跡
- 回復成功率を自動計算
- 頻発する障害パターンの検出
- 予防策の有効性追跡

---

## 11. Experience Memory — 経験知の蓄積と再利用

過去の実行履歴から再利用可能な知識を抽出・保存します。

### メモリ種別

| 種別 | 用途 |
|------|------|
| `conversation_log` | 会話ログ |
| `reusable_improvement` | 再利用可能な改善知識 |
| `experimental_knowledge` | 実験的知識 |
| `verified_knowledge` | 検証済み知識 |

### 機能

- 成功パターンの蓄積 (`add_success_pattern`)
- 障害パターンの学習 (`add_failure`)
- キーワード/カテゴリ検索 (`search`)
- 頻発障害の抽出 (`get_frequent_failures`)

---

## 12. 承認フロー

危険な操作は自律実行せず、必ず人間の承認を要求します。

### 承認が必要な操作

| 操作 | 例 |
|------|-----|
| 外部送信 | メール送信、API コール |
| 公開・投稿 | SNS 投稿、ブログ公開 |
| 削除 | データ削除、ファイル削除 |
| 課金 | API 利用料の発生 |
| 権限変更 | ユーザー権限の変更 |
| Git 操作 | push, release |
| 認証情報更新 | API キー変更 |

### 承認 UI

- 承認待ちキューの一覧表示
- リスクレベル表示（Low / Medium / High / Critical）
- 承認・却下ボタンでワンクリック操作
- 承認結果は監査ログに記録

---

## 13. 監査ログ

すべての重要操作を追跡可能な形式で記録します。

### 記録される情報

| フィールド | 説明 |
|-----------|------|
| `actor_type` | user / agent / system |
| `event_type` | 操作種別（例: `task.started`, `approval.requested`） |
| `target_type` | 対象リソース種別 |
| `target_id` | 対象リソース ID |
| `details_json` | 追加詳細情報（JSON） |
| `trace_id` | 分散トレーシング用 ID |

### 主なイベント種別

- `ticket.created` / `ticket.updated`
- `approval.requested` / `approval.granted` / `approval.rejected`
- `agent.assigned` / `agent.completed`
- `task.started` / `task.succeeded` / `task.failed`
- `cost.incurred`
- `auth.login` / `auth.logout`
- `dangerous_operation.*`（危険操作）
- `*.status_changed`（状態遷移）

### 専用ヘルパー関数

- `record_audit_event` — 汎用監査イベント記録
- `record_state_change` — 状態遷移の記録
- `record_dangerous_operation` — 危険操作の記録

---

## 14. エージェント管理

AI エージェントを組織のチームメンバーとして管理します。

### エージェント属性

| 属性 | 説明 |
|------|------|
| `agent_type` | エージェントの役割種別 |
| `autonomy_level` | 自律性レベル |
| `can_delegate` | 他エージェントへの委譲権限 |
| `can_write_external` | 外部書き込み権限 |
| `can_spend_budget` | 予算使用権限 |
| `budget_policy_id` | 紐付く予算ポリシー |
| `heartbeat_policy_id` | 紐付く Heartbeat ポリシー |

### エージェント操作

- プロビジョニング（新規作成）
- アクティベート（有効化）
- 一時停止 / 再開
- 状態遷移の検証

---

## 15. Skill / Plugin / Extension — 3 層拡張体系

本体と業務ロジックを明確に分離する 3 層の拡張体系を提供します。

### Skill（最小能力単位）

単一タスクを実行する最小単位。プロンプト、手順、スクリプト、制約を含む。

```
例: 競合分析、台本生成、ファイル整理、ローカル文脈読解
```

### Plugin（業務機能パッケージ）

複数の Skill と補助機能をまとめた業務機能パッケージ。

```
例: YouTube 運用 Plugin、ブログ運用 Plugin、AI 秘書 Plugin
```

### Extension（環境拡張）

本体の動作環境、UI、接続先を拡張する仕組み。

```
例: MCP 接続、OAuth 連携、通知機能、VS Code 風 UI
```

### レジストリ機能

- Skill / Plugin / Extension の検索
- 公開（publish）と導入（install）
- ステータス管理（Verified / Experimental / Private / Deprecated）
- バージョン管理

---

## 16. LLM Gateway — マルチプロバイダー対応

LiteLLM をベースにした統一 LLM ゲートウェイで、複数のプロバイダーに対応します。

### 対応プロバイダー

| プロバイダー | 対応モデル例 |
|-------------|-------------|
| **OpenRouter** | 複数モデルを単一 API キーで利用（推奨） |
| **OpenAI** | GPT-4, GPT-4o, GPT-4o-mini |
| **Anthropic** | Claude 3 Opus, Sonnet, Haiku |
| **Google** | Gemini 2.0 Flash |
| **Ollama** | Llama 3.2, Mistral（ローカル無料） |

### 実行モード

| モード | 説明 | 推奨モデル |
|--------|------|-----------|
| `QUALITY` | 最高品質 | Claude Opus, GPT-4o |
| `SPEED` | 高速応答 | Claude Haiku, GPT-4o-mini |
| `COST` | 低コスト | Claude Haiku, GPT-4o-mini, DeepSeek |
| `FREE` | 無料（ローカル） | Ollama (Llama, Mistral) |

### 機能

- 自動モデル選択（実行モードに基づく）
- コスト見積もり
- ツール呼び出し（Function Calling）対応
- ビジョン（画像入力）対応フラグ
- フォールバック（LiteLLM 未導入時のモック応答）

---

## 17. バックグラウンドワーカー

メイン API とは別プロセスで動作するバックグラウンドタスク実行エンジンです。

### 構成要素

| コンポーネント | 役割 |
|--------------|------|
| **TaskRunner** | ready 状態のタスクをポーリングして実行 |
| **HeartbeatRunner** | 定期実行ポリシーに基づく定期タスク実行 |
| **EventDispatcher** | WebSocket 経由でリアルタイムイベント配信 |

### TaskRunner の実行パイプライン

1. DB から `status='ready'` のタスクを取得
2. `task_type` に応じてエグゼキューター（LLM / Sandbox）を選択
3. タスクを実行
4. Judge で出力品質を検証
5. 成功 → `succeeded` / 失敗 → リトライ（最大 3 回）
6. 監査ログを記録

### エグゼキューター

| エグゼキューター | 対象タスク |
|----------------|----------|
| **LLMExecutor** | 生成、分析、翻訳など LLM を使うタスク |
| **SandboxExecutor** | Python コードの安全な実行（メモリ・CPU・時間制限付き） |

### SandboxExecutor の制限

| 制限 | デフォルト値 |
|------|------------|
| メモリ上限 | 256 MB |
| CPU 時間上限 | 30 秒 |
| ネットワークアクセス | 無効 |

---

## 18. Heartbeat — 定期実行と死活監視

### Heartbeat ポリシー

- Cron 式で実行スケジュールを定義
- ジッター設定（実行タイミングのばらつき）
- 並列実行の許可設定
- 有効 / 無効の切り替え

### 実行履歴

- 各実行の成功 / 失敗ステータス
- 実行時間の記録
- ダッシュボードでの健全性インジケーター表示

---

## 19. 組織管理（会社・部門・チーム）

### 組織階層

```
Company（会社）
├── Department（部門）
│   ├── 企画・戦略
│   ├── 開発
│   ├── マーケティング
│   └── カスタマーサポート
└── Team（チーム）
    └── タスクごとに動的に編成
```

### 機能

- 会社の作成・管理
- 部門・チームの作成
- エージェントの部門割り当て
- 組織図（Org Chart）の可視化
- ダッシュボードでの組織サマリー表示

---

## 20. 権限モデル

5 つのロールで権限を制御します。

| ロール | 権限 |
|--------|------|
| **Owner** | 全権限（予算・承認・公開設定を含む） |
| **Admin** | 組織設定、一部承認、監査ログ閲覧 |
| **User** | 業務依頼、計画確認、成果物確認 |
| **Auditor** | 実行履歴・監査ログの閲覧のみ |
| **Developer** | Skill / Plugin / Extension の開発 |

### 自律実行の境界

| 自律実行可能 | 承認必須 |
|-------------|---------|
| 調査・分析 | 公開・投稿 |
| 下書き作成 | 課金・削除 |
| 情報整理 | 権限変更・外部送信 |

---

## 21. フロントエンド UI

React 19 + TypeScript + Tailwind CSS で構築された 20 以上の画面を提供します。

### 主要画面

| 画面 | 機能 |
|------|------|
| **ダッシュボード** | 統計表示、自然言語入力、クイックナビ |
| **ログイン** | メール/パスワード認証 |
| **セットアップ** | 初回オンボーディング |
| **チケット一覧** | フィルタリング付きチケット管理 |
| **チケット詳細** | 個別チケットの状態・履歴 |
| **Design Interview** | 構造化インタビュー UI |
| **Spec/Plan** | 仕様書・計画のレビュー・承認 |
| **承認キュー** | リスクレベル付き承認管理 |
| **スキル管理** | Skill のブラウズ・作成 |
| **プラグイン管理** | Plugin のブラウズ・導入 |
| **成果物** | 生成された出力の管理 |
| **監査ログ** | 高度なフィルタリング付きログビューア |
| **コスト管理** | 予算ポリシー・支出追跡 |
| **Heartbeat** | 定期実行ポリシー・履歴 |
| **組織図** | 部門・チーム・エージェントの可視化 |
| **設定** | ユーザー設定・外部接続管理 |
| **リリース** | バージョン履歴 |
| **ダウンロード** | デスクトップアプリのダウンロード |

---

## 22. REST API

`/api/v1` プレフィックスの下に 40 以上のエンドポイントを提供します。

### エンドポイントグループ

| グループ | エンドポイント数 | 主な操作 |
|---------|---------------|---------|
| `/auth` | 6 | 登録、ログイン、OAuth、ログアウト、ユーザー情報 |
| `/companies` | 10+ | 会社 CRUD、ダッシュボード、組織図、部門・チーム |
| `/tickets` | 10+ | チケット CRUD、状態遷移、コメント、スレッド |
| `/tickets/{id}/interview` | 3 | インタビュー取得、回答、Spec 自動生成 |
| `/tickets/{id}/specs` | 2 | Spec 一覧・作成 |
| `/tickets/{id}/plans` | 2 | Plan 一覧・作成 |
| `/plans/{id}` | 3 | 承認、却下、タスク一覧 |
| `/tasks` | 6 | 作成、開始、完了、リトライ、承認要求、実行履歴 |
| `/agents` | 5 | 一覧、作成、詳細、一時停止、再開 |
| `/approvals` | 3 | 一覧、承認、却下 |
| `/artifacts` | 2 | 一覧、作成 |
| `/audit` | 1 | フィルタリング付きログ取得 |
| `/heartbeats` | 3 | ポリシー CRUD、実行履歴 |
| `/budgets` | 3 | ポリシー CRUD、コストサマリー |
| `/registry` | 6 | Skill / Plugin / Extension の検索・導入 |
| `/projects` | 4 | プロジェクト CRUD、ゴール管理 |
| `/settings` | 4 | 会社設定、ツール接続管理 |
| `/health` | 2 | ヘルスチェック（liveness / readiness） |

---

## 23. WebSocket リアルタイム通信

`/ws/events` エンドポイントで、リアルタイムのイベントストリーミングを提供します。

- タスクの進捗更新
- 承認リクエストの通知
- エージェントの状態変化
- エラー・障害の即座通知

---

## 24. Cloudflare Workers デプロイ

ローカル実行に加え、Cloudflare Workers 上でのエッジデプロイに対応しています。

### 方式 A: Proxy

- 既存 FastAPI の前段にリバースプロキシ配置
- フレームワーク: Hono
- 外部サーバーが必要

### 方式 B: Full Workers

- 主要 API を Hono + D1（Cloudflare の SQLite）で完全再実装
- JWT 認証（jose）
- 外部サーバー不要の完全サーバーレス
- 認証、会社管理、チケット、エージェント、タスク、承認、Spec/Plan、監査ログ、予算、プロジェクト、レジストリ、成果物、Heartbeat、レビュー、ヘルスチェックを提供

### フロントエンドデプロイ

```bash
cd apps/desktop/ui && npm run build
npx wrangler pages deploy dist --project-name=zeo-ui
```

---

## 25. デスクトップアプリ (Tauri)

Tauri v2 (Rust) をベースにしたクロスプラットフォームのデスクトップアプリケーションを提供します。

| OS | 形式 |
|----|------|
| Windows | `.msi` / `.exe` |
| macOS | `.dmg` |
| Linux | `.AppImage` / `.deb` |

- Python バックエンドはサイドカーとして同梱
- ローカルファイルアクセス、セッション管理、UI をローカルで実行
- LLM API や外部 SaaS はクラウド経由

---

## 26. CLI / TUI

pip でインストール可能な CLI ツールを提供します。

```bash
pip install zero-employee-orchestrator
# または
uv pip install zero-employee-orchestrator
```

エントリーポイント: `zero-employee` コマンド

---

## データベース

### 主要テーブル（29+）

`companies`, `users`, `company_members`, `agents`, `tickets`, `ticket_threads`, `specs`, `plans`, `tasks`, `task_runs`, `task_dependencies`, `artifacts`, `reviews`, `approvals`, `budget_policies`, `cost_ledgers`, `heartbeat_policies`, `heartbeat_runs`, `skills`, `plugins`, `extensions`, `tool_connections`, `tool_call_traces`, `policy_packs`, `secret_refs`, `audit_logs`, `projects`, `goals`, `departments`, `teams`

### 対応 DB

| 環境 | データベース |
|------|------------|
| 開発 | SQLite (aiosqlite) |
| 本番 | PostgreSQL (asyncpg) 推奨 |
| エッジ | Cloudflare D1 |

---

## 技術スタック一覧

| レイヤー | 技術 |
|---------|------|
| デスクトップ | Tauri v2 (Rust) |
| フロントエンド | React 19, TypeScript 5.9, Vite 7.3 |
| UI ライブラリ | Tailwind CSS 4.2, shadcn/ui, Recharts 3.7, Lucide Icons |
| 状態管理 | TanStack Query 5.62, Zustand 5.0 |
| ルーティング | React Router 7.13 |
| バックエンド | Python 3.12+, FastAPI 0.115+ |
| ORM | SQLAlchemy 2.x (async) |
| マイグレーション | Alembic |
| LLM 接続 | LiteLLM 1.60+ |
| 認証 | OAuth PKCE, python-jose (JWT) |
| バリデーション | Pydantic 2.10+ |
| スケジューラ | APScheduler 3.10+ |
| ログ | structlog 24.0+ |
| エッジ | Cloudflare Workers, Hono 4.12, D1 |
| パッケージ管理 | uv (Python), pnpm (Node.js) |
