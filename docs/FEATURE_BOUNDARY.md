# 機能境界定義 — コア機能 vs Skill / Plugin / Extension

> 作成日: 2026-03-09 / 更新: 2026-03-10 (v0.1)
> 目的: 本体に最初から含めるべき機能と、Skill / Plugin / Extension で後から追加する機能の境界を明文化する

---

## 原則

1. **本体（コア）**: 認証・権限・監査・状態管理・実行制御・可観測性 → 安定性を最優先
2. **Skill**: 単一タスクの実行能力 → 業務特化ロジック
3. **Plugin**: 複数 Skill + 補助機能のまとまり → 業務機能パッケージ
4. **Extension**: 接続先・UI・動作環境の拡張 → システム基盤の拡張

**判断基準**: 「それがないと承認・監査・実行制御が成立しないか？」→ Yes ならコア、No なら拡張。

---

## コア機能（本体に必須）

### 認証・セキュリティ
- ローカル認証（ユーザー登録・ログイン・セッション管理）
- ロールベースアクセス制御（Owner / Admin / User / Auditor / Developer）
- Secret Manager（API キー暗号化保存）
- サニタイザー（機密情報のマスキング）

### 9層アーキテクチャ基盤
- **Design Interview** — 要件深掘りの質問生成・回答蓄積
- **Task Orchestrator** — DAG 生成・Skill 割当・コスト見積り・Self-Healing
- **Skill 実行基盤** — Skill のロード・実行・結果取得のフレームワーク
- **Judge Layer** — ルールベース一次判定 + Cross-Model Verification
- **Re-Propose Layer** — 差し戻し・再提案・Plan Diff
- **State Machine** — Ticket / Task / Approval / Agent の状態遷移
- **Experience Memory** — 成功パターン・改善知識の永続記憶
- **Failure Taxonomy** — 失敗分類・再発防止
- **Provider Interface** — LLM Gateway（LiteLLM / Ollama 直接接続）

### 承認・監査
- 承認フロー（危険操作の強制ブロック）
- 承認ゲート（12カテゴリの危険操作検出）
- 自律実行境界の管理
- 監査ログ（全重要操作の記録、削除不可）

### データ管理
- SQLite / PostgreSQL によるデータ永続化
- Spec / Plan / Tasks の構造化保存
- 成果物（Artifact）管理
- コスト計測・予算管理

### UI 基盤
- ダッシュボード
- チケット管理画面
- 承認管理画面
- 監査ログ画面
- 設定画面

### オフライン動作
- Ollama Provider（ローカル LLM 直接接続）
- ローカル RAG（ファイルベースベクトル DB）
- SQLite による完全ローカル DB
- g4f Provider（サブスクリプションモード）

---

## 組み込み Skill（本体に同梱）

| Skill | 用途 | 理由 |
|-------|------|------|
| `local_context` | ローカルファイルの安全な読み込み | コアの Local Context 機能に不可欠 |
| `spec_writer` | Spec 文書の自動生成 | Design Interview フローの必須要素 |
| `plan_writer` | Plan 文書の自動生成 | Task Orchestrator の必須要素 |
| `task_breakdown` | タスク分解 | DAG 生成の必須要素 |
| `review_assistant` | レビュー支援 | Judge Layer の補助 |
| `artifact_summarizer` | 成果物要約 | Artifact Bridge の補助 |

---

## Plugin で追加する機能（本体に含めない）

### 業務特化 Plugin

| Plugin | 用途 | 状態 |
|--------|------|------|
| `youtube` | YouTube チャンネル運用 | manifest あり |
| `research` | 競合分析・市場調査 | manifest あり |
| `backoffice` | 経理・事務・書類整理 | manifest あり |
| `discord-bot` | Discord からのマルチエージェント操作・対話・承認 | manifest あり (v0.2.0) |
| `slack-bot` | Slack からのマルチエージェント操作・対話・承認 | manifest あり (v0.2.0) |

### AI エージェント拡張 Plugin

| Plugin | 用途 | 状態 |
|--------|------|------|
| `ai-avatar` | 分身AI（ユーザーの判断基準・文体を学習し代理行動） | **新規追加** |
| `ai-secretary` | 秘書AI（予定管理・ブリーフィング・AI組織とユーザーの橋渡し） | **新規追加** |

#### 分身AI (ai-avatar) の役割

ユーザーの「分身」として振る舞う AI エージェント。ユーザーの価値観・判断基準・文体を学習し:

- **Judge Layer との連携**: ユーザーの判断パターンを Judge Layer のカスタムルールとして提供し、品質判定の基準に反映
- **代理レビュー**: ユーザー不在時のタスクレビュー・優先度判断（最終承認権限は常にユーザー本人に残る）
- **文体再現**: ユーザーの文体・トーンで下書きを作成
- **承認パターン学習**: 過去の承認・却下パターンから自律実行範囲を提案

#### 秘書AI (ai-secretary) の役割

ユーザーと AI 組織をつなぐ「ハブ」として機能する AI エージェント:

- **朝のブリーフィング**: 承認待ち・進行中タスク・今日の予定を要約
- **次のアクション提案**: 優先度に基づいて次にやるべきことを提示
- **進捗サマリー**: AI 組織の活動状況をユーザーに分かりやすく報告
- **委任ルーティング**: ユーザーの指示を適切なエージェントに振り分け
- **チャット連携**: Discord/Slack/LINE Bot Plugin と連携して外部チャットアプリにブリーフィングを配信

### チャットツール連携 Plugin

| Plugin | 用途 | 状態 |
|--------|------|------|
| `line-bot` | LINE からのマルチエージェント操作 | **新規追加** |

### 将来の Plugin 候補

| Plugin | 用途 |
|--------|------|
| `blog-manager` | ブログ記事の企画・下書き・公開管理 |
| `sns-scheduler` | SNS 投稿カレンダーの自動作成 |
| `code-review` | コードレビュー・テスト自動化 |

---

## Extension で追加する機能（本体に含めない）

### 接続・認証系

| Extension | 用途 | 状態 |
|-----------|------|------|
| `oauth` | Google / GitHub 等の OAuth 認証 | manifest あり |
| `mcp` | Model Context Protocol 対応ツール接続 | manifest あり |
| `notifications` | Slack / Discord / LINE / メール通知 | manifest あり |
| `obsidian` | Obsidian Vault との双方向連携 | **新規追加** |

### 将来の Extension 候補

| Extension | 用途 |
|-----------|------|
| `proxy-network` | 社内プロキシ・VPN 対応 |
| `google-drive` | Google Drive 連携 |
| `github-integration` | GitHub Issues / PR 連携 |
| `gws-integration` | Google Workspace CLI (gws) 連携 |
| `vscode-ui` | VS Code 風 UI テーマ |
| `generative-ui` | フォーム・表・グラフによる動的レスポンス |
| `auto-update` | 自動アップデート機構 |
| `ipaas-bridge` | Make / Zapier / n8n 連携ブリッジ |
| `security-audit` | セキュリティ自己テスト（ホワイトハッカー班） |

---

## コミュニティプラグイン共有の方針 (v0.1)

ユーザーが Plugin を共有・公開できる仕組みを提供することで、開発者の追加作業なしに外部サービス連携が拡大します。

### 共有の仕組み

1. ユーザーがプラグインを開発し、GitHub リポジトリに `plugin.json` マニフェスト付きで公開
2. リポジトリに `zeo-plugin` トピックを付与
3. 他のユーザーが `POST /registry/plugins/search-external` で検索
4. `POST /registry/plugins/import` でワンクリックインストール

### 安全性の担保

- インポート時に自動安全性チェック（16 種類の危険パターン検出）
- 外部通信・認証情報アクセス・破壊的操作の検出と警告
- 攻撃的・有害なプラグインの作成・共有・公開は禁止
- インストール前にユーザーへリスクレベルを表示し確認を求める

---

## 判断フローチャート

```
新機能の追加要求
    │
    ├─ 承認・監査・状態管理に不可欠？ → YES → コア機能
    │
    ├─ 単一タスクの実行能力？ → YES → Skill
    │
    ├─ 特定業務の機能パッケージ？ → YES → Plugin
    │
    └─ 接続先・UI・環境の拡張？ → YES → Extension
```

## オフライン動作の保証

コア機能は **Ollama + SQLite** の組み合わせで完全オフライン動作が可能。

| 機能 | オフライン | 備考 |
|------|-----------|------|
| Design Interview | 可能 | Ollama モデルで実行 |
| Spec / Plan 生成 | 可能 | Ollama モデルで実行 |
| Task 実行 | 可能 | ローカル Skill のみ |
| Judge Layer | 可能 | ルールベース判定はオフライン可、Cross-Model は要オンライン |
| 承認フロー | 可能 | ローカル UI で完結 |
| 監査ログ | 可能 | SQLite に記録 |
| ローカル RAG | 可能 | ファイルベース TF-IDF |
| 外部 API 連携 | 不可 | オンライン必須 |
| Registry 検索 | 不可 | ローカルインストール済みは利用可 |
