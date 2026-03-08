# Zero-Employee Orchestrator マスターガイド

> 作成日: 2026-03-08  
> 参照優先順位: `Zero-Employee Orchestrator.md` → `DESIGN.md` → instructions 系ファイル

---

## 0. このガイドの役割

このガイドは、Zero-Employee Orchestrator を AI コーディングエージェントで実装する際の、
**参照順序、分担、実装順、判断基準、禁止事項**をまとめた運用ガイドである。

思想や要望の原典は `Zero-Employee Orchestrator.md` にあり、詳細設計は `DESIGN.md` にある。  
本ガイドは「どの文書をどう使って、どう実装を進めるか」を定義する。

---

## 1. 最重要ルール

1. **名称は Zero-Employee Orchestrator で統一する**  
   CommandWeave / ZPCOS など旧名称は、新規実装・新規文書では使わない。

2. **Zero-Employee Orchestrator.md を最上位基準にする**  
   思想、スコープ、境界条件、優先順位が衝突した場合は同ファイルを優先する。

3. **DESIGN.md を実装構造の基準にする**  
   DB、API、画面、状態遷移、実装順序は DESIGN.md を基準にする。

4. **instructions_section2〜7 は既に新方針へ対応済みの前提で扱う**  
   それらを「古い CommandWeave 用指示」とみなして全面修正対象に戻さない。  
   必要なら不足点のみ局所修正する。

5. **YouTube は代表デモであり、本体定義ではない**  
   実装は汎用業務基盤として組み、YouTube 系は Skill / Plugin として扱う。

6. **危険操作は承認前提にする**  
   投稿、送信、削除、課金、権限変更、外部共有は自律実行させない。

---

## 2. ファイルの役割

| ファイル | 役割 | 用途 |
|---|---|---|
| `Zero-Employee Orchestrator.md` | 最上位基準文書 | 思想、境界、要件、改善方針の確認 |
| `DESIGN.md` | 実装設計書 | DB、API、画面、状態遷移、構成の確認 |
| `MASTER_GUIDE.md` | 実装運用ガイド | AI エージェントへの進め方と判断基準 |
| `instructions_section2_init.md` | 初期構築指示 | 開発基盤・初期リポジトリ整備 |
| `instructions_section3_backend.md` | バックエンド指示 | 認証、状態、Orchestrator、Judge など |
| `instructions_section4_frontend.md` | フロントエンド指示 | ダッシュボード、Interview、Plan、Execution UI |
| `instructions_section5_skills.md` | Skill 指示 | YouTube 等の代表 Skill 実装 |
| `instructions_section6_tauri.md` | デスクトップ統合指示 | Tauri 統合、ローカル実行 |
| `instructions_section7_test.md` | テスト指示 | 単体、結合、E2E、セキュリティ |

---

## 3. 参照手順

AI エージェントは、次の順で文書を読む。

1. `Zero-Employee Orchestrator.md`
2. `DESIGN.md`
3. `MASTER_GUIDE.md`
4. 自分が担当する instructions ファイル
5. 必要に応じて関連コード、既存ディレクトリ、既存 API、既存テスト

この順を逆転させない。  
個別 instructions に書いてあっても、上位文書と衝突する場合は上位文書を採用する。

---

## 4. 実装対象の中核

Zero-Employee Orchestrator の本体で先に成立させるべきなのは次である。

- 認証 / 接続管理
- Design Interview
- Spec Writer
- Task Orchestrator
- Cost Guard
- Quality SLA
- Task 状態機械
- Judge
- Re-Propose / Plan Diff
- Self-Healing
- Experience Memory / Failure Taxonomy
- Local Context Skill
- 監査ログ
- 基本 UI

後から拡張するもの:

- Skill Registry の外部公開強化
- Marketplace 的要素の拡張
- Multi-company 高度対応
- Goal Alignment / Heartbeat の高度化
- BYOAgent / MCP の広範対応

---

## 5. 実装順序

### Phase 0: 基盤
- モノレポ整備
- Python / Node / Tauri セットアップ
- CI / Lint / Test / Format
- `.env` / secret 管理

### Phase 1: 認証とスコープ
- auth
- provider connections
- workspace / company スコープ

### Phase 2: Interview と spec
- interview セッション
- Spec Writer
- spec 永続化

### Phase 3: plan と承認
- planner
- cost estimation
- quality mode
- approval
- diff

### Phase 4: tasks と実行
- task decomposition
- task state machine
- execution timeline
- output persistence

### Phase 5: judge と再計画
- policy pack
- pre-check
- cross-model judge
- repropose
- self-healing
- failure taxonomy

### Phase 6: skill と文脈
- skill framework
- gap detection
- local context skill
- experience memory

### Phase 7: UI
- dashboard
- interview UI
- plan review UI
- task board
- review / audit UI

### Phase 8: registry
- package model
- install flow
- version metadata
- verification status

### Phase 9: 高度化
- heartbeat
- org chart 中心運用
- board / governance モデル
- multi-company

---

## 6. 各 instructions ファイルの期待役割

### Section 2: 初期化

目的:
- リポジトリ構造を Zero-Employee Orchestrator 前提に整える
- 開発基盤と共通規約を揃える

出力:
- ディレクトリ構成
- 開発スクリプト
- CI の最小構成
- README の最低限更新

### Section 3: バックエンド

目的:
- 本体の中核ロジックを実装する

重点:
- auth
- interview
- orchestrator
- judge
- state / memory
- providers
- registry の土台

### Section 4: フロントエンド

目的:
- 実行の透明性を UI で担保する

重点:
- Interview
- Spec / Plan review
- Task timeline
- Approval UI
- Review / Audit
- Skill / Connection 管理

### Section 5: Skills

目的:
- 本体に依存しない業務スキルとして代表ユースケースを成立させる

重点:
- YouTube 系は代表デモとして実装
- 汎用 Skill framework に乗せる
- Local Context と自然に連携させる

### Section 6: Tauri

目的:
- ローカルアプリとしての価値を成立させる

重点:
- ファイルアクセス
- ローカル起動
- セキュアな接続管理
- 配布しやすいビルド構成

### Section 7: テスト

目的:
- 単に動くことではなく、危険操作・再計画・監査を検証する

重点:
- state machine
- permission boundary
- repropose / self-healing
- audit log consistency
- local context handling

---

## 7. AI エージェントへの実装指示原則

1. **大きな再命名は設計整合性がある場合のみ一括で行う**  
   旧名称が残る箇所は、設定名・ディレクトリ名・DB 名・UI 表示名を見落とさず揃える。

2. **基盤と業務 Skill を混ぜない**  
   汎用の本体ロジックを YouTube 専用コードで汚染しない。

3. **spec / plan / tasks を会話ログで済ませない**  
   構造化データとして保存する。

4. **状態遷移をコードに明示する**  
   暗黙条件で進めず、状態機械または同等の明示構造で管理する。

5. **再計画理由を保存する**  
   Self-Healing や Re-Propose の発火理由、差分、採択結果を追跡可能にする。

6. **監査ログを後付けにしない**  
   重要 API・承認・外部送信・権限変更は最初から記録対象にする。

7. **危険操作は UI と API の両方で防ぐ**  
   フロントだけでなくバックエンドでも承認制約を持つ。

---

## 8. 禁止事項

- Zero-Employee Orchestrator を単なる YouTube 自動化ツールとして実装すること
- Skill / Plugin / Extension の境界を曖昧にすること
- 承認必須操作を黙って実行すること
- 監査ログなしで外部送信や権限変更を行うこと
- instructions_section2〜7 を未対応前提で全面否定すること
- 旧名称を新規 UI や新規コードに残すこと
- ローカル文脈アクセスを無制限権限で実装すること

---

## 9. 最小デモの定義

最小デモは、次を一連で実演できる状態を指す。

1. ユーザーが自然言語で業務依頼
2. Interview で要件整理
3. spec を生成
4. plan と cost を提示
5. ユーザーが承認
6. tasks を実行
7. Local Context Skill がローカル資料を参照
8. Judge が品質を確認
9. 必要時に Re-Propose または Self-Healing
10. 最終成果物、ログ、判断履歴を表示

---

## 10. 現時点の整合方針

- `DESIGN.md` と `MASTER_GUIDE.md` は、`Zero-Employee Orchestrator.md` に整合するよう更新済みとする
- instructions_section2〜7 は、この新方針に対応済みの前提で扱う
- 今後の修正は「全体を作り直す」よりも「不足箇所の局所修正」を優先する
- 実装中に迷った場合は、「本体か拡張か」「承認が必要か」「監査できるか」で判断する

---

## 11. 最終判断の基準

迷った場合は次の順で判断する。

1. その機能は本体の責務か、Skill / Plugin / Extension の責務か
2. その操作は人間承認なしに実行してよいか
3. その処理は監査可能か
4. その実装は汎用業務基盤として再利用可能か
5. その変更は `Zero-Employee Orchestrator.md` の思想に沿っているか

この 5 条件を満たさない変更は採用しない。
