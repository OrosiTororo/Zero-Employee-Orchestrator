# Zero-Employee Orchestrator — 機能一覧

> 日本語 | [English](en/FEATURES.md) | [中文](zh/FEATURES.md)

> 最終更新: 2026-03-12
> 対象バージョン: v0.1

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
24. [Observability — 推論トレース・通信ログ・実行監視](#24-observability--推論トレース通信ログ実行監視)
25. [Cloudflare Workers デプロイ](#25-cloudflare-workers-デプロイ)
26. [デスクトップアプリ (Tauri)](#26-デスクトップアプリ-tauri)
27. [CLI / TUI](#27-cli--tui)

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

### ファイル添付によるコンテキスト入力

Design Interview にファイルを添付し、仕様書生成のコンテキストとして統合できます。

| ファイル種別 | 対応形式 | 処理方法 |
|------------|---------|---------|
| **テキスト** | `.txt`, `.md`, `.csv`, `.json`, `.yaml`, `.xml`, `.html` | テキスト抽出（複数エンコーディング自動検出） |
| **コード** | `.py`, `.ts`, `.js`, `.java`, `.go`, `.rs`, `.c`, `.cpp` 等 | ソースコードとして解析 |
| **画像** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg` | Base64 エンコード + メタデータ抽出 |
| **ドキュメント** | `.pdf` | メタ情報抽出 |

```
POST /api/v1/tickets/{ticket_id}/interview/attach
Content-Type: multipart/form-data

file: (添付ファイル)
description: "競合分析レポートの元データ"
```

添付ファイルから抽出されたテキストは、Spec の「参照資料」セクションとして自動統合されます。

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
- **v0.1 改善**: セマンティック類似度検証、矛盾検出エンジン、信頼度加重スコアリング

**矛盾検出エンジン (v0.1):**

| 検出タイプ | 説明 |
|-----------|------|
| 否定パターン | "is" vs "is not"、"true" vs "false" の矛盾を検出 |
| 数値不整合 | 5% を超える数値差異を検出 |
| 結論矛盾 | 対立する感情・方向性の結論を検出 |
| 時系列不整合 | 矛盾する日付・順序関係を検出 |

**ZEO-Bench（定量評価ベンチマーク）:**

200 問のテストセットで Cross-Model Verification の精度を定量評価するベンチマーク。

| カテゴリ | テスト数 | 評価内容 |
|---------|---------|---------|
| 事実正確性 | 50 | 事実誤りの検出精度 |
| 矛盾検出 | 70 | モデル間矛盾の検出率 |
| 偽陽性 | 40 | 正当な出力を誤検出しないか |
| 修正品質 | 40 | 矛盾時に正しい出力を特定できるか |

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

モデルファミリー別のトークン単価テーブルを `model_catalog.json` で管理し、実行前にコストを見積もります。
コスト情報はモデルカタログから動的に読み込まれるため、モデル変更時もコード修正は不要です。

| モデル | 入力 ($/1K tokens) | 出力 ($/1K tokens) |
|--------|-------------------|-------------------|
| Claude Opus 4.6 | 0.015 | 0.075 |
| Claude Sonnet 4.6 | 0.003 | 0.015 |
| Claude Haiku 4.5 | 0.001 | 0.005 |
| GPT-5.4 | 0.005 | 0.015 |
| GPT-5 Mini | 0.00015 | 0.0006 |
| Gemini 2.5 Pro | 0.00125 | 0.005 |
| Gemini 2.5 Flash | 0.0001 | 0.0004 |
| Gemini 2.5 Flash Lite | 0.00005 | 0.0002 |
| DeepSeek Chat | 0.00014 | 0.00028 |
| Ollama (ローカル) | 0.0 | 0.0 |
| g4f (無料プロバイダー) | 0.0 | 0.0 |

> **注意**: 上記は `model_catalog.json` のデフォルト値です。プロバイダーの料金改定に合わせて
> API (`POST /api/v1/models/update-cost`) またはファイル直接編集で更新できます。

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
| **DRAFT** | GPT-5 Mini, Claude Haiku 4.5 | 1 回 | 50% | 不要 | なし |
| **STANDARD** | GPT-5.4, Claude Sonnet 4.6 | 2 回 | 70% | 不要 | なし |
| **HIGH** | GPT-5.4, Claude Sonnet 4.6 | 3 回 | 85% | 不要 | **あり** |
| **CRITICAL** | Claude Opus 4.6, GPT-5.4 | 5 回 | 95% | **必須** | **あり** |

品質モードに応じてモデル選択、リトライ戦略、検証レベルが自動調整されます。
推奨モデルは `model_catalog.json` から読み込まれるため、モデル更新時はファイル編集のみで対応できます。

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

### カオステスト（v0.1）

Self-Healing DAG の信頼性を検証するためのカオステストスイートを実装しています。

| テストカテゴリ | テスト数 | 検証内容 |
|--------------|---------|---------|
| 単一ノード障害 | 6 | retry / skip / replan 各戦略の動作検証 |
| 複数ノード障害 | 4 | カスケード障害・並列ブランチ障害の検証 |
| 復旧時間 | 3 | 復旧成功率と復旧時間の計測 |
| DAG 整合性 | 4 | 復旧後の DAG 構造の一貫性検証 |
| エッジケース | 4 | 空 DAG・単一ノード DAG・循環依存等 |
| ベンチマーク | 3 | 100 回ランダム障害での復旧統計 |

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

**汎用ドメイン Skill テンプレート（v0.1）:**

| Skill | 対応ドメイン | 説明 |
|-------|------------|------|
| `ContentCreatorSkill` | マーケティング・SNS・メール | 任意プラットフォーム向けコンテンツ生成 |
| `CompetitorAnalysisSkill` | 市場分析・営業 | SWOT・価格比較・機能比較等の競合分析 |
| `TrendAnalysisSkill` | リサーチ・企画 | 市場・技術・SNS のトレンド分析 |
| `PerformanceAnalysisSkill` | 経営・データ分析 | KPI・ROI・コンバージョン分析 |
| `StrategyAdvisorSkill` | 経営・戦略 | ドメイン横断の戦略アドバイス |

全 Skill が Artifact Bridge と互換性を持ち、成果物を自動的に次の Skill の入力として活用できます。

### Plugin（業務機能パッケージ）

複数の Skill と補助機能をまとめた業務機能パッケージ。

| Plugin | 用途 | 状態 |
|--------|------|------|
| `ai-avatar`（分身AI） | ユーザーの判断基準・文体を学習し代理行動 | manifest あり |
| `ai-secretary`（秘書AI） | ブリーフィング・優先度提案・AI組織との橋渡し | manifest あり |
| `discord-bot` | Discord からのマルチエージェント操作・対話 | manifest あり (v0.2.0) |
| `slack-bot` | Slack からのマルチエージェント操作・対話 | manifest あり (v0.2.0) |
| `line-bot` | LINE からのマルチエージェント操作 | manifest あり |
| `youtube` | YouTube チャンネル運用 | manifest あり |
| `research` | 競合分析・市場調査 | manifest あり |
| `backoffice` | 経理・事務・書類整理 | manifest あり |
| `ai-self-improvement` | AI 自己改善（Skill 分析・改善提案・A/B テスト） | **v0.1 実装済み**（6 Skill + API） |

### Extension（環境拡張）

本体の動作環境、UI、接続先を拡張する仕組み。

| Extension | 用途 | 状態 |
|-----------|------|------|
| `oauth` | Google / GitHub 等の OAuth 認証 | manifest あり |
| `mcp` | Model Context Protocol 対応ツール接続 | manifest あり |
| `notifications` | Slack / Discord / LINE / メール通知 | manifest あり |
| `obsidian` | Obsidian Vault との双方向連携 | manifest あり |

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
| **OpenAI** | GPT-5.4, GPT-5 Mini |
| **Anthropic** | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 |
| **Google** | Gemini 2.5 Pro, Flash, Flash Lite |
| **DeepSeek** | DeepSeek Chat |
| **Ollama** | Llama 3.2, Mistral, Phi-3, Qwen3 等（ローカル無料） |
| **g4f** | 無料プロバイダー経由（API キー不要） |

> **対応モデルは `model_catalog.json` で管理されます。**
> モデルの追加・削除・廃止・後継指定はこのファイルを編集するか、
> Model Registry API (`/api/v1/models/*`) 経由で行えます。

### 実行モード

| モード | 説明 | 推奨モデル |
|--------|------|-----------|
| `QUALITY` | 最高品質 | Claude Opus 4.6, GPT-5.4 |
| `SPEED` | 高速応答 | Claude Haiku 4.5, GPT-5 Mini |
| `COST` | 低コスト | Claude Haiku 4.5, GPT-5 Mini, DeepSeek |
| `FREE` | 無料（ローカル + 無料 API） | Ollama, Gemini 無料枠, g4f |
| `SUBSCRIPTION` | 無料（API キー不要） | g4f 経由の各種モデル |

### 機能

- **動的モデルカタログ** (`model_catalog.json`) — モデルの追加・廃止・コスト更新にコード変更不要
- **モデル廃止時の自動フォールバック** — deprecated フラグ + successor で後継モデルに自動切替
- **プロバイダーヘルスチェック** — API 可用性を定期確認し、利用不可モデルを回避
- 自動モデル選択（実行モードに基づく）
- コスト見積もり（カタログ連動）
- ツール呼び出し（Function Calling）対応
- ビジョン（画像入力）対応フラグ
- フォールバック（LiteLLM 未導入時のモック応答）
- Ollama モデル自動検出

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

React 19 + TypeScript + Tailwind CSS で構築された 23 の画面を提供します。

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
| **秘書AI** | ブレインダンプ・日次サマリー・優先度提案 |
| **壁打ち** | マルチモデル比較・役割別設定・AI組織管理 |

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
| `/settings` | 6 | LLM API キー設定、実行モード、会社設定、ツール接続管理 |
| `/health` | 2 | ヘルスチェック（liveness / readiness） |
| `/models` | 7 | モデルカタログ管理、ヘルスチェック、廃止管理 |
| `/traces` | 4 | 推論トレース一覧、詳細、判断抽出 |
| `/communications` | 5 | エージェント間通信、エスカレーション、スレッド |
| `/monitor` | 4 | 実行監視ダッシュボード、アクティブタスク、イベント |

---

## 23. WebSocket リアルタイム通信

`/ws/events` エンドポイントで、リアルタイムのイベントストリーミングを提供します。

- タスクの進捗更新
- 承認リクエストの通知
- エージェントの状態変化
- エラー・障害の即座通知
- **推論トレースのリアルタイム配信** — エージェントの思考過程をステップ単位で配信
- **エージェント間通信の配信** — 委譲・フィードバック・エスカレーションをリアルタイム表示
- **実行監視イベント** — タスク進捗・モデル選択・Judge判定をリアルタイム表示

---

## 24. Observability — 推論トレース・通信ログ・実行監視

マルチエージェント業務のブラックボックス化を解消するための可観測性機能群です。

### 24.1 推論トレース (Reasoning Trace)

エージェントが**なぜその判断をしたか**を段階的に記録します。

| ステップ種別 | 説明 |
|-------------|------|
| `context_gathering` | 情報源からのコンテキスト収集 |
| `knowledge_retrieval` | Experience Memory / RAG からの知識検索 |
| `option_enumeration` | 選択肢の列挙 |
| `option_evaluation` | 各選択肢の評価・スコアリング |
| `decision` | 最終的な意思決定（選択肢・理由・確信度を含む） |
| `model_selection` | LLM モデルの選択理由 |
| `judge_result` | Judge Layer の判定結果 |
| `error_analysis` | エラー原因の分析 |
| `fallback_decision` | フォールバック戦略の選択 |

各ステップには**確信度** (high / medium / low / uncertain) が付き、
判断の信頼性を定量的に評価できます。

### 24.2 エージェント間通信ログ (Agent Communication)

マルチエージェント協調時の**全メッセージ交換**を記録します。

| メッセージ種別 | 説明 |
|--------------|------|
| `delegation` / `delegation_accept` / `delegation_reject` | タスク委譲 |
| `artifact_handoff` | 成果物の受け渡し |
| `feedback` / `question` / `answer` | コミュニケーション |
| `quality_review` | 品質レビュー結果 |
| `escalation` | エスカレーション（人間への委譲） |
| `error_report` / `help_request` | 異常報告 |

会話は**スレッド**でグループ化され、タスク単位での会話追跡が可能です。

### 24.3 実行監視 (Execution Monitor)

リアルタイムで**実行中のタスク**を監視し、WebSocket 経由でフロントエンドに配信します。

- 実行中タスクの進捗率・現在のステップ・使用トークン数・コスト
- 推論トレースの各ステップをリアルタイム配信
- エラー・エスカレーションの即座通知
- エージェントごとのアクティビティサマリー

### API エンドポイント

| エンドポイント | 説明 |
|-------------|------|
| `GET /traces` | 推論トレース一覧（タスク別・エージェント別フィルタ） |
| `GET /traces/{id}` | 推論トレース詳細（全ステップ含む） |
| `GET /traces/{id}/decisions` | 意思決定ステップのみ抽出 |
| `GET /communications` | エージェント間通信ログ |
| `GET /communications/escalations` | エスカレーション一覧 |
| `GET /communications/agent/{id}/interactions` | 通信相手別の集計 |
| `GET /monitor/dashboard` | 監視ダッシュボード（サマリー+アクティブ+イベント） |
| `GET /monitor/active` | 実行中タスク一覧 |
| `GET /monitor/agent/{id}` | エージェントアクティビティ |

---

## 25. Cloudflare Workers デプロイ

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

## 26. デスクトップアプリ (Tauri)

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

## 27. CLI / TUI

pip でインストール可能な CLI ツールを提供します。

```bash
pip install zero-employee-orchestrator
# または
uv pip install zero-employee-orchestrator
```

エントリーポイント: `zero-employee` コマンド

### CLI コマンド一覧

| コマンド | 説明 |
|---------|------|
| `zero-employee serve` | API サーバーを起動 |
| `zero-employee config list` | 全設定値の一覧表示 |
| `zero-employee config set <KEY> [VALUE]` | 設定値を保存（VALUE 省略時はプロンプト入力、機密値はエコーなし） |
| `zero-employee config get <KEY>` | 設定値を取得 |
| `zero-employee config delete <KEY>` | 設定値を削除（デフォルトに戻す） |
| `zero-employee config keys` | 設定可能なキーの一覧 |
| `zero-employee local` | ローカルチャットモード（Ollama） |
| `zero-employee models` | インストール済み Ollama モデル一覧 |
| `zero-employee pull <model>` | Ollama モデルをダウンロード |
| `zero-employee db upgrade` | DB マイグレーション実行 |
| `zero-employee health` | ヘルスチェック |

### ランタイム設定管理

API キーや実行モードを `.env` ファイルを直接編集せずに設定できます。

**3 通りの設定方法:**
1. **設定画面**: アプリの「設定」→「LLM API キー設定」から入力
2. **CLI**: `zero-employee config set GEMINI_API_KEY`（機密値はプロンプトで安全に入力）
3. **.env ファイル**: 従来通り `apps/api/.env` を直接編集

設定の優先順位: 環境変数 > `~/.zero-employee/config.json` > `.env` > デフォルト値

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

---

## 追加機能（Plugin / Extension で提供）

以下の機能は本体に含まれず、Plugin / Extension として追加導入します。

### 分身AI（AI Avatar Plugin）

ユーザーの「分身」として振る舞う AI エージェント。ユーザーの判断基準・文体・専門知識をプロファイルとして学習します。

| 機能 | 説明 |
|------|------|
| **プロファイル学習** | 過去の承認・却下パターン、コメント履歴、文体を分析してプロファイル構築 |
| **Judge Layer 連携** | ユーザーの判断基準を Judge Layer のカスタムルールとして提供 |
| **代理レビュー** | ユーザー不在時のタスクレビュー・優先度判断（最終承認権限は常にユーザー本人） |
| **文体再現** | ユーザーの文体・トーンでの下書き作成 |
| **承認パターン提案** | 過去の承認パターンから自律実行範囲を提案 |

### 秘書AI（AI Secretary Plugin）

ユーザーと AI 組織をつなぐ「ハブ」として機能する AI エージェント。

| 機能 | 説明 |
|------|------|
| **朝のブリーフィング** | 承認待ち・進行中タスク・今日の予定を要約 |
| **次のアクション提案** | タスクの緊急度・重要度を判定し推奨順序を提示 |
| **進捗サマリー** | AI 組織の活動状況をユーザーに分かりやすく報告 |
| **リマインド** | 期限が近いタスク・承認待ちの通知 |
| **委任ルーティング** | ユーザーの指示を適切なエージェントに振り分け |
| **チャット連携** | Discord / Slack / LINE Bot Plugin と連携してブリーフィング配信 |

### チャットツール連携（Discord / Slack / LINE Bot Plugin）

外部チャットツールから AI 組織に指示を送り、結果を受け取ります。

| コマンド | 動作 |
|---------|------|
| `/zeo ticket <説明>` | 新しいチケットを作成 |
| `/zeo status [ticket_id]` | チケット・タスクの状態確認 |
| `/zeo approve <approval_id>` | 承認操作 |
| `/zeo reject <approval_id>` | 却下操作 |
| `/zeo briefing` | 現在の業務サマリーを取得 |
| `/zeo ask <質問>` | AI 組織に質問 |

承認が必要な操作はチャットツール上でも承認ダイアログが表示されます。秘書AI Plugin と連携して、定期ブリーフィングの配信先としても利用可能です。

---

## 28. 外部ツール連携 (v0.1)

### CLI ツール接続

`tools/connector.py` は以下の接続タイプをサポートします:

| 接続タイプ | 説明 | 例 |
|-----------|------|-----|
| `rest_api` | REST API 呼び出し | SaaS API、社内 API |
| `webhook` | Webhook 受信・送信 | Slack / Discord 通知 |
| `mcp` | Model Context Protocol | Claude Desktop、VS Code 連携 |
| `oauth` | OAuth 2.0 認証フロー | Google / GitHub 認証 |
| `websocket` | WebSocket 双方向通信 | リアルタイムデータストリーム |
| `file_system` | ファイルシステム接続 | ローカル/NFS/S3 |
| `database` | データベース接続 | PostgreSQL、MySQL |
| `cli_tool` | CLI ツール接続 | gws、gh、aws CLI 等 |
| `grpc` | gRPC サービス接続 | マイクロサービス間通信 |
| `graphql` | GraphQL API 接続 | GitHub GraphQL API 等 |

### 対応可能な CLI ツール例

| ツール | 説明 | リポジトリ |
|--------|------|-----------|
| **gws** | Google Workspace CLI（Google Workspace API 全操作をターミナルから統一操作） | `googleworkspace/cli` |
| **gh** | GitHub CLI（リポジトリ・Issue・PR 操作） | `cli/cli` |
| **aws** | AWS CLI（AWS サービス全般操作） | `aws/aws-cli` |
| **gcloud** | Google Cloud CLI（GCP サービス操作） | Google Cloud SDK |
| **az** | Azure CLI（Azure サービス操作） | `Azure/azure-cli` |

これらの CLI ツールは `ToolConnector` に登録することで、Skill から呼び出し可能になります。Plugin として CLI ツール連携パッケージを提供することも可能です。

---

## 29. コミュニティプラグイン共有 (v0.1)

### プラグインの共有・公開

ユーザーは自作のプラグインを GitHub リポジトリとして公開し、他のユーザーが簡単にインストールできます。開発者による本体への追加作業は不要です。

### プラグイン共有の仕組み

```
ユーザー A: プラグインを開発
  → GitHub リポジトリに push（topic: zeo-plugin）
  → plugin.json マニフェストを含める

ユーザー B: プラグインを検索・インストール
  → POST /api/v1/registry/plugins/search-external?query=キーワード
  → POST /api/v1/registry/plugins/import?source_uri=https://github.com/user/plugin
  → プラグインが自動的にインストールされ利用可能に
```

### プラグインマニフェスト形式 (`plugin.json`)

```json
{
  "name": "my-awesome-plugin",
  "slug": "my-awesome-plugin",
  "description": "プラグインの説明",
  "version": "0.1.0",
  "author": "作成者名",
  "license": "MIT",
  "tags": ["productivity", "automation"],
  "skills": ["skill-a", "skill-b"],
  "config_schema": {}
}
```

### コミュニティプラグイン API

| エンドポイント | 説明 |
|-------------|------|
| `POST /api/v1/registry/plugins/search-external` | GitHub 等から外部プラグインを検索 |
| `POST /api/v1/registry/plugins/import` | GitHub リポジトリからプラグインをインポート・インストール |
| `POST /api/v1/registry/plugins` | ローカルでプラグインを作成 |
| `POST /api/v1/registry/plugins/install` | プラグインをインストール |

### 安全性チェック

共有プラグインのインストール時には以下の安全性チェックが実行されます:

- 危険なコードパターンの検出（16 種類）
- 外部通信の検出と警告
- 認証情報アクセスの検出
- 破壊的操作の検出
- リスクレベルの評価（low / medium / high）

---

## 30. AI Self-Improvement — Level 2: 自己改善の芽 (v0.1)

AI が AI を分析・改善・検証する自己改善機能群です。`ai-self-improvement` Plugin として実装されています。

### 6 つの自己改善 Skill

| Skill | 機能 | API エンドポイント |
|-------|------|-------------------|
| **skill-analyzer** | 既存 Skill のコード品質分析（静的分析 + LLM 深層分析） | `POST /self-improvement/analyze` |
| **skill-improver** | 分析結果に基づく改善版 Skill の自動生成 | `POST /self-improvement/improve` |
| **judge-tuner** | Experience Memory から Judge 判定基準の自動調整 | `POST /self-improvement/judge/tune` |
| **failure-to-skill** | 失敗パターンから予防 Skill の自動生成 | `POST /self-improvement/failure-to-skill` |
| **skill-ab-test** | 2つの Skill の A/B テスト比較（品質・速度） | `POST /self-improvement/ab-test` |
| **auto-test-generator** | Skill テストコードの自動生成（正常系・エッジ・異常系） | `POST /self-improvement/generate-tests` |

### 分析カテゴリ

| カテゴリ | 評価内容 |
|---------|---------|
| `code_quality` | コード構造、可読性、命名規則、DRY原則 |
| `performance` | 不要な処理、メモリ使用、N+1クエリ |
| `error_handling` | 例外処理、フォールバック、入力検証 |
| `security` | インジェクション、認証情報露出、危険な操作 |
| `test_coverage` | テスト可能性、エッジケースの考慮 |
| `documentation` | docstring、型ヒント、コメント |

### 安全機構

- 全ての改善適用に**ユーザー承認が必須**
- 改善前のコードを **version_history** として保持（ロールバック可能）
- 改善版コードの**安全性チェック**（16パターンの危険コード検出）
- Judge ルール適用は**信頼度 0.5 以上**のルールのみ

### ダッシュボード API

`GET /api/v1/self-improvement/status` で以下の統計を取得:
- スキル分析数、改善提案数、改善適用数
- Judge ルール提案数、適用数
- 失敗防止スキル提案数、A/B テスト完了数、テスト生成数

---

## 31. v0.1 機能肥大化レビュー — コアと拡張の境界

v0.1 では以下の機能がコードベースに同梱されているが、**コア機能の判断基準**（「それがないと承認・監査・実行制御が成立しないか？」）に照らして、**拡張機能**として分類される。将来のバージョンで独立パッケージとして分離予定。

| 機能 | 現在の場所 | 分類先 | 状態 |
|------|-----------|--------|------|
| **Sentry 連携** | `integrations/sentry_integration.py` | Extension | v0.1 同梱・将来分離 |
| **AI 調査ツール** | `integrations/ai_investigator.py` | Skill | v0.1 同梱・将来分離 |
| **仮説検証エンジン** | `orchestration/hypothesis_engine.py` | Plugin | v0.1 同梱・将来分離 |
| **MCP サーバー** | `integrations/mcp_server.py` | Extension | v0.1 同梱・将来分離 |
| **外部スキルインポート** | `integrations/external_skills.py` | Extension | v0.1 同梱・将来分離 |

> **注意**: 上記の機能は v0.1 では利用可能ですが、コアの安定性を維持するために
> 将来のバージョンで Extension / Skill / Plugin として独立させる計画です。
> 詳細は [FEATURE_BOUNDARY.md](FEATURE_BOUNDARY.md) を参照。

---

## 32. メタスキル概念 (v0.1)

AI エージェントに「学び方を学ぶ能力」を持たせる設計概念です。

### メタスキルの5要素

| 要素 | AI エージェントでの実装 |
|------|----------------------|
| **Feeling（感じ取る力）** | ユーザーの意図・感情の推察、コンテキスト理解 |
| **Seeing（見通す力）** | システム思考、業務全体の依存関係把握 |
| **Dreaming（夢見る力）** | 創造的な代替案の提案、Re-Propose Layer |
| **Making（実現する力）** | 計画から実装までの一貫した実行、DAG 構築 |
| **Learning（学ぶ力）** | Experience Memory、Failure Taxonomy による学習 |

従来の AI エージェントはハードスキル（特定タスクの実行）とソフトスキル（コミュニケーション）を持ちますが、メタスキル（スキルの運用・学習を支える力）は不足しています。Zero-Employee Orchestrator は Experience Memory と Failure Taxonomy によりメタスキルの基盤を提供します。

---

## 33. ファイル添付による計画作成 (v0.1)

Design Interview にファイルを添付し、仕様書（Spec）生成のコンテキストとして統合する機能です。

### API エンドポイント

| エンドポイント | 説明 |
|-------------|------|
| `POST /api/v1/tickets/{ticket_id}/interview/attach` | ファイルアップロード |
| `GET /api/v1/tickets/{ticket_id}/interview/attachments` | 添付ファイル一覧 |

### 対応ファイル形式

| カテゴリ | 形式 |
|---------|------|
| テキスト | `.txt`, `.md`, `.csv`, `.json`, `.yaml` |
| コード | `.py`, `.ts`, `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.h`, `.html`, `.xml`, `.css`, `.sql`, `.sh` |
| 画像 | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg` |
| ドキュメント | `.pdf` |

- テキスト自動抽出 + 複数エンコーディング対応（UTF-8, Shift_JIS, EUC-JP, CP932）
- 抽出テキストを Spec の「参照資料」セクションに自動統合
- 画像は Base64 エンコード + PNG/JPEG サイズ検出
- SVG はテキストとしても解析
- 10 MB サイズ上限

---

## 34. セキュリティ強化 (v0.1)

| 項目 | 説明 |
|------|------|
| **bcrypt 必須化** | パスワードハッシュに bcrypt を強制。SHA-256 フォールバックを廃止 |
| **レート制限** | `slowapi` による認証エンドポイントのレート制限（登録: 5/min, ログイン: 10/min） |
| **RAG ファイル権限** | `index.json` / `idf.json` を `0o600`（所有者のみ）に制限 |
| **RAG 入力バリデーション** | コンテンツサイズ上限 (10 MB) とメタデータキー数制限 |
| **CORS 制限強化** | ワイルドカードを明示的メソッド・ヘッダーリストに変更 |
| **UUID 入力バリデーション** | 不正 UUID で 400 を返すように修正 |
