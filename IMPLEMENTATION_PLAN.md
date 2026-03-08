# IMPLEMENTATION_PLAN.md

## このファイルの役割

この文書は、CommandWeave の上位思想文書をそのまま実装しようとして暴走しないための、**今回の実装範囲限定ドキュメント**である。  
Claude Code は、まずこの範囲を end-to-end で完成させることを優先する。

---

## 1. 今回のゴール

今回のゴールは、CommandWeave の MVP として、次の一連の流れを最小構成で成立させることである。

1. ユーザーが自然言語で依頼を入力する
2. Design Interview で要件を深掘りする
3. `spec / plan / tasks` を生成・保存する
4. 計画にコスト、権限、危険操作、担当要素を表示する
5. ユーザーが承認または差し戻しできる
6. 承認後に実行へ進む
7. Judge で品質確認する
8. 成果物、実行ログ、承認履歴を保存する

この end-to-end が通れば成功とする。

---

## 2. 今回の対象範囲

### 2.1 対象に含めるもの
- 自然言語入力の受付
- Design Interview の状態管理
- `spec / plan / tasks` の保存モデル
- 案件単位または実行単位のディレクトリ / レコード管理
- 実行計画の表示
- 承認待ち状態
- 実行状態管理
- Judge 判定の最小導線
- 実行ログ / 監査ログ / 成果物保存
- 危険操作フラグ
- 必要権限表示
- Skill / Plugin / Extension の最低限のメタ情報表示

### 2.2 今回は対象外
- 大規模 Registry / Marketplace
- 完全自律の無承認外部実行
- 高度なマルチテナント
- 複雑な組織権限階層の完成版
- 高度な AI 分身機能
- ロボット / IoT / AR / VR 連携
- 全業務領域への対応
- 外部 SaaS の大規模統合
- 企業向け完全監査製品レベルの仕上げ

---

## 3. まず実装すべきユースケース

### 3.1 最優先ユースケース
「自然言語で依頼 → 計画提示 → 承認 → 実行 → Judge → 保存」が一回通ること。

### 3.2 推奨デモシナリオ
業務領域はひとつに絞る。例:
- 調査・分析タスク
- SNS / YouTube 用の下書き生成
- 文書要約と改善提案

最初から複数ドメインを同時にやらない。

---

## 4. 推奨アーキテクチャの切り方

### 4.1 中核ドメイン
最低限、次の責務を分ける。

- `request` : ユーザー依頼の受付
- `interview` : Design Interview の進行
- `spec_plan_tasks` : 中間成果物管理
- `approval` : 承認 / 差し戻し
- `execution` : 実行状態と進捗
- `judge` : 品質確認
- `artifacts` : 成果物保存
- `audit` : 実行ログ / 承認履歴 / イベント記録
- `catalog` : Skill / Plugin / Extension メタ情報

### 4.2 典型状態遷移
最低限、次の状態を管理できるようにする。

- `draft`
- `interviewing`
- `planned`
- `awaiting_approval`
- `approved`
- `running`
- `judge_review`
- `needs_revision`
- `failed`
- `completed`
- `cancelled`

状態名は多少変わってもよいが、意味の欠落は避ける。

---

## 5. 保存構造の初期案

推奨する論理構造は次の通り。

```text
project/
 ├ spec/
 ├ plan/
 ├ tasks/
 ├ outputs/
 ├ review/
 └ logs/
```

アプリ実装上は、ファイル保存でも DB 保存でもよい。  
ただし少なくとも次を追跡できるようにする。

- 実行 ID
- 元の依頼文
- Interview の履歴
- 最新 spec
- 最新 plan
- 最新 tasks
- 承認状態
- 実行状態
- Judge 結果
- 生成成果物
- 使用 Skill / Plugin / Extension
- ログとエラー

---

## 6. データモデルの最小要件

### 6.1 Job / Workflow
- id
- title
- user_request
- domain
- current_state
- risk_level
- estimated_cost
- requires_approval
- created_at
- updated_at

### 6.2 Spec
- job_id
- objective
- constraints
- acceptance_criteria
- assumptions
- inputs

### 6.3 Plan
- job_id
- steps
- assigned_roles
- required_permissions
- external_connections
- risky_actions
- fallback_routes

### 6.4 Task
- job_id
- task_id
- summary
- owner_type
- depends_on
- status
- verification_rule
- done_condition

### 6.5 Approval
- job_id
- approval_status
- approval_required_reason
- approver_role
- approval_comment
- approved_at

### 6.6 Execution Event / Audit Log
- job_id
- event_type
- timestamp
- actor
- message
- metadata

### 6.7 Artifact
- job_id
- artifact_type
- path_or_blob_ref
- version
- created_at

---

## 7. UI / API で最低限見せるべき情報

### 計画画面
- 目的
- 工程一覧
- 担当 AI / Skill
- 必要権限
- 外部接続の有無
- 危険操作の有無
- コスト概算
- 承認必須ポイント

### 実行画面
- 現在の状態
- 進捗
- 直近イベント
- 生成された成果物
- エラーまたは停止理由

### 履歴画面
- 過去の実行一覧
- 承認履歴
- Judge 判定
- 差し戻し理由

---

## 8. 実装フェーズ

### Phase 0: 土台確認
目的:
- リポジトリ構造を確認する
- 既存の入力、保存、実行、画面の導線を把握する
- 既存コードを壊さずに実装位置を決める

完了条件:
- 主要ディレクトリの責務が説明できる
- 既存の不足点を列挙できる
- どのファイルを編集するか決める

### Phase 1: spec / plan / tasks の中核保存
目的:
- 最低限のデータモデルを定義する
- 入力から `spec / plan / tasks` を保存できるようにする

完了条件:
- 1 件の依頼について中間成果物が永続化される
- 再読込して表示できる

### Phase 2: 承認フロー
目的:
- `awaiting_approval` を中心にした承認 / 差し戻しを追加する

完了条件:
- ユーザーが承認または差し戻しできる
- 危険操作フラグ時は承認なしに進まない

### Phase 3: 実行状態管理
目的:
- 実行の状態遷移とイベント記録を入れる

完了条件:
- `running / failed / completed` の更新が追える
- ログが残る

### Phase 4: Judge 導線
目的:
- 実行後に最低限の品質確認を行う

完了条件:
- Judge の結果が保存される
- `needs_revision` へ戻せる

### Phase 5: 監査と成果物
目的:
- 実行履歴、承認履歴、成果物を一覧で追えるようにする

完了条件:
- ジョブ単位で何が起きたか時系列に追跡できる

---

## 9. テスト方針

最低限、次を確認する。

### 単体
- 状態遷移関数
- 承認判定関数
- リスク判定関数
- 保存 / 読込関数

### 結合
- 入力 → spec / plan / tasks 保存
- 計画 → 承認待ち
- 承認 → 実行
- 実行 → Judge → 完了または差し戻し

### E2E
- 一つの最小ユースケースが画面または CLI 上で最後まで通る

---

## 10. 受け入れ条件

今回の実装は、次を満たしたら完了扱いとする。

- 自然言語入力からジョブを作成できる
- Design Interview またはそれに準ずる要件整理段階がある
- `spec / plan / tasks` が保存される
- 計画に権限・危険操作・コスト概算が表示される
- 承認または差し戻しできる
- 承認なしでは高リスク実行に進まない
- 実行ログが残る
- Judge 結果が残る
- 成果物と履歴を再確認できる

---

## 11. Claude Code への実装上の注意

- 一気に抽象化しすぎないこと
- 型やスキーマがあるなら先に固めること
- UI だけ先に作らず、保存・状態遷移・監査を先に通すこと
- 見た目より end-to-end を優先すること
- 必要ならモックでつないでよいが、どこがモックかを明示すること
- 新しい依存を増やす場合は理由を説明すること

---

## 12. 次に広げる候補

今回が終わった後に拡張してよい候補は次。

- Skill Registry
- Plugin 導入 UX
- 成功体験メモリ
- WebSocket 通知
- コスト分析の高度化
- ローカル / クラウド保存切替
- コーディング系 Plugin 向けの意味的コード理解

これらは**今回の完了条件ではない**。
