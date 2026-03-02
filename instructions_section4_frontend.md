# Section 4 — フロントエンド構築（Antigravity 用）v11.2

> 担当: Antigravity（全ステップ）
> 前提: Section 2 完了、Section 3 バックエンド動作中
> バックエンド API: http://localhost:18234
> 完了条件: 全 7 画面 + Self-Healing可視化が動作し、バックエンドと正常に連携できること
> v11.2 追加: Self-Healing試行履歴パネル、Skill Registry UI、ローカルファイル選択

---

## ステップ 4.1 — 初期セットアップ

    pnpm add tailwindcss @tailwindcss/vite
    pnpm dlx shadcn@latest init -d
    pnpm dlx shadcn@latest add button card input textarea dialog tabs toast badge scroll-area separator alert progress select radio-group
    pnpm add @tauri-apps/api @tauri-apps/plugin-shell recharts lucide-react react-router-dom

---

## ステップ 4.2 — API クライアント（src/lib/api.ts）

バックエンド API 全 27 エンドポイントに対応する TypeScript クライアント:

    const API_BASE = "http://localhost:18234";

    // 認証（7）
    POST /api/auth/login       → authLogin()
    GET  /api/auth/status      → authStatus()
    POST /api/auth/logout      → authLogout()
    POST /api/auth/connect/:s  → authConnect(service)
    GET  /api/auth/connections  → authConnections()
    DELETE /api/auth/disconnect/:s → authDisconnect(service)

    // Design Interview（3）★v11.1
    POST /api/interview/start     → interviewStart(input)
    POST /api/interview/respond   → interviewRespond(session_id, answers)
    POST /api/interview/finalize  → interviewFinalize(session_id)

    // Orchestrate（6）
    POST /api/orchestrate                → orchestrate(input, quality_mode?)
    GET  /api/orchestrate/:id            → getOrchestration(id)
    POST /api/orchestrate/:id/approve-plan → approvePlan(id) ★v11.1
    POST /api/orchestrate/:id/repropose    → repropose(id, feedback, mode) ★v11.1
    GET  /api/orchestrate/:id/cost         → getCost(id) ★v11.1
    GET  /api/orchestrate/:id/diff         → getDiff(id) ★v11.1

    // コア（2）
    POST /api/chat    → chat(messages, model_group?)
    POST /api/judge   → judge(text, context?)

    // タスク（3）
    POST /api/tasks               → createTask(skill_name, input_data)
    GET  /api/tasks/:id           → getTask(id)
    POST /api/tasks/:id/transition → transitionTask(id, trigger)

    // Skill（4）
    GET  /api/skills         → listSkills()
    POST /api/skills/execute → executeSkill(skill_name, input)
    POST /api/skills/generate → generateSkill(description)
    GET  /api/skills/gaps    → getSkillGaps() ★v11.1

    // Self-Healing（2）★v11.2
    POST /api/orchestrate/:id/self-heal  → selfHeal(id)
    GET  /api/orchestrate/:id/heal-history → getHealHistory(id)

    // Skill Registry（4）★v11.2
    GET  /api/registry/search?q=query  → registrySearch(query)
    POST /api/registry/publish         → registryPublish(skillDir, author)
    POST /api/registry/install         → registryInstall(skillName)
    GET  /api/registry/popular         → registryPopular()

    // その他
    GET /api/health, GET /api/settings, PUT /api/settings

---

## ステップ 4.3 — ルーティング（src/App.tsx）

7 画面:

    /login              → LoginPage
    /interview          → InterviewPage          ★v11.1
    /                   → DashboardPage
    /orchestrate/:id    → OrchestrationPage
    /skill/:name        → SkillExecutePage
    /skill/create       → SkillCreatePage
    /settings           → SettingsPage

未認証時は /login にリダイレクト。

---

## ステップ 4.4 — Hooks

### use-auth.ts（変更なし）

### use-interview.ts ★v11.1 新規
- startInterview(input) → InterviewSession
- respondToQuestion(session_id, answers) → updated session
- finalizeInterview(session_id) → SpecDocument
- 状態管理: currentSession, currentQuestions, spec

### use-orchestrate.ts（v11.0 の use-chat.ts を拡張）
- orchestrate(input, qualityMode) → Plan 生成（実行前に表示）
- approvePlan(id) → 実行開始
- repropose(id, feedback) → 再提案
- getCost(id) → CostEstimate

### use-skills.ts（変更なし）

---

## ステップ 4.5 — ログイン画面（変更なし）

---

## ステップ 4.6 — Design Interview 画面（/interview）★v11.1

ZPCOS の最重要 UX。タスク実行前に必ずここを通る。

フロー:
1. ダッシュボードで入力 →「まず確認させてください」→ /interview に遷移
2. AI が生成した質問をカード形式で表示
3. 各質問: 選択式ボタン + 自由記述テキストエリアの両方
4. 回答を送信 → 追加質問があれば表示
5. 「これで十分です」ボタン → Spec 生成
6. Spec プレビュー表示 → 「修正」or「この仕様で実行」
7. 承認 → /orchestrate/:id に遷移

UI要素:
- 質問カード: アイコン + 質問文 + 「なぜこの質問？」折りたたみ説明
- 選択肢: Radio/Checkbox ボタン（shadcn Radio Group）
- 自由記述: Textarea
- 進捗バー: 回答済み / 全質問数
- Spec プレビュー: 要件・制約・優先順位・受入基準をセクション表示
- AI 補完部分: 黄色ハイライトで「AI が推定した前提」を明示

---

## ステップ 4.7 — ダッシュボード（/）

v11.0 からの変更:
- チャット入力の送信先を変更:
  入力 → POST /api/interview/start → /interview に遷移
  （直接 orchestrate しない。必ず Interview を経由する）
- 右サイドバーに品質モードセレクター追加（★v11.1）:
  「最速 / バランス / 高品質」の 3 択ラジオボタン

それ以外は v11.0 と同じ（Skill 一覧、タスク状況表示）。

---

## ステップ 4.8 — Orchestration 画面（/orchestrate/:id）

v11.0 からの変更:

上部に追加（★v11.1）:
- コスト見積り表示: GET /api/orchestrate/:id/cost
  「API呼び出し: N回 / 推定コスト: $X.XX / 推定時間: Ns」
  予算超過時は黄色警告バッジ
- 品質モード表示: 「高品質モード」等のバッジ
- Skill Gap 警告: 不足 Skill があれば赤カードで表示
  3案（代替/生成/スキップ）をボタンで選択

Plan 承認フロー（★v11.1、v11.0 では即実行だったのを変更）:
1. Plan を表示（DAG ビジュアライゼーション）
2. 「この Plan で実行する」ボタン → POST /approve-plan → 実行開始
3. 「修正したい」ボタン → フィードバック入力 → POST /repropose → 新 Plan 表示
4. Plan Diff 表示: 変更箇所をハイライト

実行中・完了後は v11.0 と同じ（ステップ進行、Judge スコア、承認/差し戻し）。
差し戻し時は「reject」ではなく「Change Request」として扱い、フィードバック入力欄を表示。

Self-Healing 可視化パネル（★v11.2）:
- Skill実行エラーやJudge差し戻し時に自動表示
- 試行履歴をタイムライン形式で表示:
  - 各試行: 戦略（RETRY_SAME/SWAP_SKILL/REPLAN/DECOMPOSE）+ 結果 + 理由
  - 成功: 緑バッジ、失敗: 赤バッジ、エスカレーション: 黄バッジ
- 「AIが自律的に回復を試みています…」アニメーション
- 最大3回の自動リトライ後に「人間の判断が必要です」メッセージ
- GET /api/orchestrate/:id/heal-history でポーリング更新

---

## ステップ 4.9 — Skill 実行画面（変更なし）

---

## ステップ 4.10 — Skill 作成画面

v11.0 からの変更:
- 生成前に ROI 表示（★v11.1）:
  「この Skill を作る価値: 再利用可能性 / 時間短縮 / リスク」
- Gap Negotiation 統合:
  Plan から呼び出された場合、代替案も表示
- Skill Registry 連携（★v11.2）:
  - 「コミュニティから探す」ボタン → レジストリ検索モーダル
  - 人気Skill一覧表示
  - ワンクリックインストール
  - 作成したSkillを「公開する」ボタンで共有

---

## ステップ 4.11 — 設定画面（変更なし）

---

## ステップ 4.12 — 確認

    cd zpcos/frontend
    pnpm dev
    # http://localhost:5173

    確認項目:
    1. ログイン画面が表示される
    2. チャット入力 → Interview 画面に遷移する
    3. Interview 質問が表示され、回答できる
    4. Spec が生成され、承認できる
    5. Plan が表示され、コスト見積りが見える
    6. Plan 承認後に実行が始まる
    7. 設定画面が表示される
    8. Self-Healing 試行履歴パネルが表示される（★v11.2）
    9. Skill Registry 検索・インストールが動作する（★v11.2）

    git add -A
    git commit -m "feat: implement complete frontend (Section 4 v11.2)"

セクション 4 完了。
