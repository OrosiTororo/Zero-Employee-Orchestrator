# Section 3 — バックエンド構築（Zero-Employee Orchestrator）

> 担当: Claude Code
> 基準文書: `Zero-Employee Orchestrator.md`
> 前提: Section 2 完了
> 目的: 会社・組織・チケット・spec / plan / tasks・実行・承認・監査を扱う FastAPI バックエンドを構築する
> 完了条件: MVP の中核 API と状態遷移が動作し、Section 4 以降が接続できること

---

## 0. 実装対象

MVP では次を優先実装する。

- 認証 / セッション
- company / member / role
- org chart（department, team, agent）
- goals / tickets
- specs / plans / tasks
- task execution / review / artifact
- approval request
- skill registry の最低限
- audit logs
- heartbeat の最小版

未実装でもよいもの:

- Marketplace の完全版
- 高度な課金計算
- 本格的なマルチカンパニー運用 UI
- すべての外部 SaaS 連携

---

## 1. 技術固定

- FastAPI
- SQLModel / SQLAlchemy
- SQLite から開始、後で PostgreSQL へ移行可能にする
- Pydantic v2
- Alembic
- structlog

---

## 2. 実装順序

### 3.1 共通基盤

実装:

- `app/main.py`
- `app/api/router.py`
- `app/core/config.py`
- `app/db/session.py`
- `app/db/base.py`
- `app/db/models.py`
- `app/schemas/common.py`

最低限エンドポイント:

- `GET /api/health`
- `GET /api/version`

### 3.2 認証 / ロール

実装:

- `auth/models.py`
- `auth/service.py`
- `auth/router.py`

必要機能:

- login / logout / me
- company scope の取得
- role: owner / admin / user / auditor / developer

API:

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### 3.3 会社・組織図

実装:

- `companies/*`
- `org/*`

モデル:

- company
- department
- team
- agent
- company_member

API:

- `GET /api/companies/current`
- `GET /api/org/chart`
- `POST /api/org/departments`
- `POST /api/org/teams`
- `POST /api/org/agents`
- `PATCH /api/org/agents/{id}`

### 3.4 goals / tickets

実装:

- `goals/*`
- `tickets/*`

モデル:

- goal
- ticket
- ticket_thread

API:

- `GET /api/goals`
- `POST /api/goals`
- `GET /api/tickets`
- `POST /api/tickets`
- `GET /api/tickets/{id}`
- `POST /api/tickets/{id}/comments`

### 3.5 spec / plan / tasks

実装:

- `specs/*`
- `plans/*`
- `tasks/*`

要件:

- ticket に紐づく spec を保存できる
- spec から plan を派生できる
- plan から tasks を生成できる
- それぞれ版管理と差分の土台を持つ

API:

- `POST /api/tickets/{id}/specs`
- `POST /api/specs/{id}/plans`
- `POST /api/plans/{id}/tasks`
- `GET /api/tickets/{id}/work-graph`

### 3.6 実行 / レビュー / 成果物

実装:

- `execution/*`
- `state/*`

モデル:

- task_run
- artifact
- review

要件:

- task 実行要求を受ける
- 実行ログを保存する
- 生成成果物を結び付ける
- review を記録する

API:

- `POST /api/tasks/{id}/run`
- `GET /api/tasks/{id}/runs`
- `POST /api/runs/{id}/reviews`
- `GET /api/artifacts/{id}`

### 3.7 承認 / Heartbeat / 監査

実装:

- `approvals/*`
- `heartbeat/*`
- `audit/*`

API:

- `POST /api/approvals`
- `POST /api/approvals/{id}/approve`
- `POST /api/approvals/{id}/reject`
- `GET /api/heartbeat/runs`
- `GET /api/audit/logs`

### 3.8 Skills / Plugins / Extensions

実装:

- `skills/*`
- `plugins/*`
- `extensions/*`

要件:

- 用語を混同しない
- registry 一覧を返せる
- verified / draft / blocked などの状態を持てる

API:

- `GET /api/skills`
- `POST /api/skills/register`
- `GET /api/plugins`
- `GET /api/extensions`

---

## 3. 最低限の DB テーブル

初期マイグレーションでは少なくとも以下を作ること。

- companies
- users
- company_members
- departments
- teams
- agents
- goals
- tickets
- ticket_threads
- specs
- plans
- tasks
- task_runs
- artifacts
- reviews
- approval_requests
- heartbeat_runs
- skills
- plugins
- extensions
- audit_logs

---

## 4. 状態遷移の最低要件

### Ticket

`draft -> ready -> in_progress -> waiting_approval -> completed | blocked | cancelled`

### Task

`todo -> ready -> running -> succeeded | failed | needs_review | cancelled`

### ApprovalRequest

`pending -> approved | rejected | expired`

### Agent

`idle -> assigned -> running -> waiting_review | blocked | offline`

---

## 5. 実装ルール

- 破壊的操作前に approval を挟める設計にする
- spec / plan / tasks は必ず永続化する
- 重要操作は audit_logs に残す
- provider 呼び出しは service 層越しに行う
- UI 都合のロジックを backend に混ぜすぎない
- YouTube 固有ロジックをコア層に埋め込まない

---

## 6. 完了確認

以下が通れば Section 3 完了。

1. health / auth / org / tickets / specs / tasks / approvals / skills API が起動する
2. DB マイグレーションが通る
3. ticket から spec / plan / tasks を作れる
4. task 実行ログと artifact が保存される
5. approval と audit の基本機能が動く
6. frontend から接続可能な JSON 形が揃っている
