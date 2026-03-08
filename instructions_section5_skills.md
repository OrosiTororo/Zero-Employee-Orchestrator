# Section 5 — Skills / Plugins / Extensions 実装

> 担当: Claude Code
> 基準文書: `Zero-Employee Orchestrator.md`
> 前提: Section 3 完了
> 目的: Skill / Plugin / Extension の役割差を保ったまま、MVP の組み込み機能と代表デモを実装する
> 完了条件: Registry に最低限の built-in 項目が登録され、ticket / task 実行から呼べること

---

## 0. 用語を混同しない

### Skill

単一タスクの実行能力。

例:

- 要約
- 競合分析
- 台本生成
- ローカル文書分析

### Plugin

複数 Skill を束ねて業務単位を成立させるパッケージ。

例:

- YouTube Plugin
- Blog Ops Plugin

### Extension

外部接続や UI 拡張、実行補助。

例:

- Google Drive Connector
- Slack Connector

---

## 1. MVP で実装する built-in Skills

### 必須

- `local-context-analyzer`
- `spec-writer`
- `plan-writer`
- `task-breakdown`
- `artifact-summarizer`
- `review-assistant`

### 代表デモ用

- `yt-script`
- `yt-rival-analysis`
- `yt-trend-scan`
- `yt-performance-review`
- `yt-next-move`

---

## 2. 必須 Plugin

### YouTube Plugin

以下の Skill を束ねる。

- yt-script
- yt-rival-analysis
- yt-trend-scan
- yt-performance-review
- yt-next-move

### Core Ops Plugin

以下の Skill を束ねる。

- local-context-analyzer
- spec-writer
- plan-writer
- task-breakdown
- review-assistant

---

## 3. Skill 仕様

各 Skill には最低限以下を持たせること。

- `id`
- `name`
- `description`
- `input_schema`
- `output_schema`
- `required_connections`
- `risk_level`
- `approval_required`
- `version`
- `verified_status`

---

## 4. 実装ルール

- Skill は ticket / task コンテキストを受け取れる
- 重要操作を伴う Skill は `approval_required=true`
- 外部接続が必要なら `required_connections` を明示する
- 実行結果は artifact と review に繋げる
- provider 呼び出しの失敗理由を実行ログに残す

---

## 5. Registry 要件

`GET /api/skills` で以下を返すこと。

- id
- type（skill / plugin / extension）
- title
- description
- version
- verified_status
- approval_required
- required_connections
- tags

---

## 6. Local Context Skill の要件

`local-context-analyzer` は MVP の重要要素。

要件:

- ローカル文書のメタ情報を扱える
- 文書内容から spec / plan に使える要約を作る
- 機密情報を外部送信する前に警告可能
- 解析対象ファイル一覧と結果を artifact 化する

---

## 7. 完了確認

1. built-in skill 一覧が registry に出る
2. plugin 単位の一覧が出る
3. local-context-analyzer が動く
4. YouTube Plugin が代表デモとして動く
5. 実行結果が artifact と review に接続される
