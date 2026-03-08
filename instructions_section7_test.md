# Section 7 — テスト・検証

> 担当: Claude Code
> 基準文書: `Zero-Employee Orchestrator.md`
> 前提: Section 3〜6 の主要実装が完了していること
> 目的: 中間成果物保持、承認、監査、自律実行境界を含めて MVP の信頼性を検証する
> 完了条件: unit / integration / e2e / state machine / security の最低限テストが通ること

---

## 0. テスト方針

通常の CRUD テストだけでは不足。  
このプロジェクトでは次も検証すること。

- spec / plan / tasks が欠落せず保存されるか
- approval を経ずに危険操作が進まないか
- audit logs が残るか
- task 失敗時に状態が壊れないか
- registry 情報が UI と矛盾しないか

---

## 1. Unit Tests

最低限作るもの:

- auth service
- role guard
- ticket service
- spec / plan / task builders
- approval service
- audit logger
- skill registry
- local context analyzer

---

## 2. Integration Tests

主要フロー:

1. login
2. ticket 作成
3. spec 作成
4. plan 作成
5. tasks 生成
6. task 実行
7. review 登録
8. approval 発行 / 承認
9. audit 確認

---

## 3. State Machine Tests

### Ticket

- draft -> ready
- ready -> in_progress
- in_progress -> waiting_approval
- waiting_approval -> completed
- invalid transition を拒否

### Task

- todo -> ready -> running -> succeeded
- running -> failed
- failed -> ready の再実行可否

### Approval

- pending -> approved
- pending -> rejected
- approved 後の再 reject を拒否

---

## 4. Security Tests

- role ごとの API 制限
- company scope をまたぐ参照拒否
- approval_required skill の直実行拒否
- audit 改ざん防止の土台確認
- secrets を API レスポンスに漏らさない

---

## 5. E2E Tests

最低限:

- Login
- Dashboard 表示
- Ticket 作成
- Work Graph 表示
- Approval 操作
- Skills Registry 表示

---

## 6. 受け入れ基準

1. 主要 API が失敗せず通る
2. 中間成果物が保存される
3. 監査ログが追跡できる
4. 承認境界が守られる
5. Local Context と YouTube デモの両方が成立する
6. desktop 起動フローで最低限の運用ができる
