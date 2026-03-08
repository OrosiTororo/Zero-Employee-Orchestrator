# Section 4 — フロントエンド構築（Zero-Employee Orchestrator）

> 担当: Antigravity
> 基準文書: `Zero-Employee Orchestrator.md`
> 前提: Section 2 完了、Section 3 の API が起動していること
> 目的: 会社運用の中核画面を、承認・監査・中間成果物可視化を含めて構築する
> 完了条件: MVP 画面群が backend と連携し、主要フローを操作できること

---

## 0. UI 原則

- 見た目より運用可能性を優先
- ダッシュボード中心設計
- spec / plan / tasks を隠さない
- 承認待ち・失敗・監査を見える化する
- YouTube デモは追加機能として載せ、本体を侵食させない

---

## 1. 実装する画面

### 4.1 認証系

- Login
- Current Company / Current User 表示

### 4.2 主要業務画面

- Dashboard
- Org Chart
- Goals
- Tickets List
- Ticket Detail
- Work Graph（spec / plan / tasks）
- Approvals Inbox
- Audit Log

### 4.3 レジストリ系

- Skills
- Plugins
- Extensions

### 4.4 設定系

- Providers / Connections
- Policies / Heartbeat
- Developer Settings

---

## 2. ルーティング

```text
/
/login
/dashboard
/org
/goals
/tickets
/tickets/:id
/work/:ticketId
/approvals
/audit
/skills
/plugins
/extensions
/settings
```

---

## 3. API クライアント

`src/lib/api.ts` に最低限以下を実装すること。

- authLogin / authLogout / authMe
- getCurrentCompany
- getOrgChart
- listGoals / createGoal
- listTickets / createTicket / getTicket / addTicketComment
- createSpec / createPlan / createTasks / getWorkGraph
- createApproval / approveApproval / rejectApproval
- listSkills / listPlugins / listExtensions
- listAuditLogs

---

## 4. 状態管理

- 認証状態: zustand
- 一覧取得 / 再取得: React Query
- 入力バリデーション: zod
- 重要フォーム: チケット作成、spec 作成、承認操作

---

## 5. MVP の主要コンポーネント

- OrgChartTree
- GoalTable
- TicketTable
- TicketHeader
- TicketThreadPanel
- SpecPlanTaskBoard
- ApprovalPanel
- AuditLogTable
- RegistryTable
- ProviderConnectionCard

---

## 6. 表示要件

### Dashboard

- 進行中 ticket 数
- 承認待ち件数
- 失敗 task 数
- 最近の audit イベント
- 今日の heartbeat 結果

### Ticket Detail

- ticket 本文
- コメント / スレッド
- 現在状態
- 紐づく spec / plan / tasks
- 直近実行履歴
- 承認要求状況

### Work Graph

- spec
- plan
- tasks
- task status
- artifact 一覧
- review 状態

---

## 7. 実装ルール

- 仮データ前提で終わらせない
- backend の状態名を勝手に変えない
- 承認 UI を省略しない
- 監査ログ UI を後回しにしない
- 基準文書の用語をラベルにも反映する

---

## 8. 完了確認

1. 主要画面に遷移できる
2. tickets 一覧・詳細・work graph が表示できる
3. approval 操作ができる
4. audit logs を見られる
5. skills / plugins / extensions 一覧を見られる
6. dashboard が実運用に必要な情報を持つ
