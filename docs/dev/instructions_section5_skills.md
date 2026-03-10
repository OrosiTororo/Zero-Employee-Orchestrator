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

## 7. 自然言語スキル生成 (v0.1 実装済み)

### 概要
ユーザーが自然言語でスキルの機能を説明するだけで、マニフェスト (skill.json) と
実行コード (executor.py) を自動生成する。

### エンドポイント
- `POST /api/v1/registry/skills/generate`

### 生成フロー
1. ユーザーが自然言語で説明を入力
2. LLM がマニフェスト + 実行コードを生成（LLM 不可時はテンプレートフォールバック）
3. 生成コードの安全性チェック（16 種類の危険パターン）
4. 安全性レポート生成（risk_level, 権限要件, 外部接続検出）
5. 安全性チェック通過後、オプションで自動登録

### 安全性チェック対象
- 危険コードパターン: os.system, subprocess, eval, exec, compile
- 外部通信: requests.post/put/delete, httpx, aiohttp, smtplib, socket
- 認証情報: api_key, secret, password, token, os.environ
- 破壊操作: shutil.rmtree, os.remove, DROP TABLE, DELETE FROM

---

## 8. システム保護スキル (v0.1 実装済み)

### 保護対象の built-in スキル
以下のスキルは `is_system_protected=True` でマークされ、削除・無効化不可:
- `spec-writer` — 仕様書生成
- `plan-writer` — 実行計画生成
- `task-breakdown` — タスク DAG 分解
- `review-assistant` — 品質レビュー
- `artifact-summarizer` — 成果物要約
- `local-context` — ローカルコンテキスト

### 保護メカニズム
- API レベル: DELETE / PATCH (enabled=false) で HTTP 403 を返す
- サービス層: ValueError で拒否
- 起動時: `ensure_system_skills()` で自動登録・保護フラグ設定

---

## 9. Skill / Plugin / Extension 管理 API (v0.1 実装済み)

### Skill API
| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/registry/skills` | 一覧（status, skill_type, include_disabled でフィルタ） |
| GET | `/registry/skills/{id}` | 個別取得 |
| POST | `/registry/skills` | 新規作成 |
| POST | `/registry/skills/install` | インストール（create のエイリアス） |
| PATCH | `/registry/skills/{id}` | 更新（保護スキルの無効化は拒否） |
| DELETE | `/registry/skills/{id}` | 削除（保護スキルは拒否） |
| POST | `/registry/skills/generate` | 自然言語生成 |

### Plugin / Extension API
同様の CRUD 構成（GET, POST, PATCH, DELETE）

---

## 10. 完了確認

1. built-in skill 一覧が registry に出る
2. plugin 単位の一覧が出る
3. local-context-analyzer が動く
4. YouTube Plugin が代表デモとして動く
5. 実行結果が artifact と review に接続される
6. 自然言語でスキルを生成できる (v0.1)
7. 生成されたスキルの安全性チェックが行われる (v0.1)
8. システム必須スキルが削除できない (v0.1)
9. Skill / Plugin / Extension の CRUD 管理ができる (v0.1)
