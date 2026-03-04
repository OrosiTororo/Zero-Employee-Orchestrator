# ZPCOS 完全構築設計書 v11.2

> 作成日: 2026-03-02
> 基底: v11.1 + 改善4件統合（ローカル特権・Self-Healing・起心動念・Skill Registry）
> 対象環境: Windows 11 / RAM 32 GB / GPU 16 GB VRAM / CPU 16コア

---

注）ZPCOS_FEATURES_AND_IMPROVEMENTS.mdの内容を参考に背景と動機を含む全てを根本から変更してください。

---

## 背景と動機

本プロジェクトは、ある経営者からの「YouTube分析を高度化できないか」という具体的な相談と、「複数のAIを組み合わせれば、単体では到達できない水準に行けるのではないか」という問いから始まりました。
当初は、SNS運用や分析の自動化という実務的な課題への対応が出発点でした。しかし議論を重ねる中で、より根本的な問題に行き当たりました。
多くの企業では、AIを“導入”していると言いながら、実際にはチャット型AIに断片的な質問を投げ、その出力をそのまま採用するという使い方に留まっています。あるいは、AIエージェントに業務を丸投げし、生成物にすべてを委ねる設計思想を採用しようとしています。
しかしそれは本当に正しいのか。
AIにすべてを任せることは、効率化であると同時に思考停止でもあります。
一方で、対話型AIによる壁打ちは、人間の発想を拡張し、アイデアを現実へと引き下ろす力を持っています。
議論の末にたどり着いたのは、「人間の意思決定と思考の主導権は保持しつつ、業務の実行部分は自律化できないか」という問いでした。
私はAIエージェントの自律化そのものには強い未来性を感じています。しかし、それを人間の創造性と切り離した形で設計することには違和感がありました。
そこで考えたのが、
人間のアイデアとの壁打ち構造を保ったまま、業務実行だけを自律化するOS という構想です。
それが ZPCOS です。

---

## 設計思想（Philosophy）

ZPCOS（Zero-Person Campany Orchestration System）は「AI を道具から組織に進化させる」
**ローカル常駐型デスクトップ OS** であり、**人間のアイデアとの壁打ち構造を保ったまま、業務実行だけを自律化するOS**である。


人間の役割は「目的を与える」と「最終承認」の 2 つだけ。AIとの壁打ちやアイデア出し、クリエイティブな作業に集中できる。
それ以外の思考・実行・検証・改善は AI 組織が自律的に遂行する。

### なぜローカル OS なのか？——クラウド AI エージェントとの完全差別化

クラウドベースの AI エージェントプラットフォーム（Dify, GPTs, etc.）が台頭する中、
ZPCOS が「デスクトップ OS」である必然性は以下にある:

1. **ローカル特権アクセス**: ユーザーのファイルシステム・ブラウザ・他アプリに直接アクセス可能。
   機密情報（過去の動画素材・企画書・財務データ）をクラウドに送信せず、ローカルで安全に処理できる。
2. **セキュアなコンテキスト理解**: 機密データを含むローカルファイルを AI 組織がセキュアに操作し、
   ユーザーの業務文脈を深く理解した上でタスクを実行する。
3. **オフライン耐性**: ネットワーク障害時もローカルキャッシュと状態機械が動作を継続。
4. **ローカル推論力 × 外部 API の融合**: ローカル環境の特権的アクセスと OpenRouter 経由の
   最先端モデルの推論力を組み合わせることで、どちらか一方では実現できない価値を生む。

### v11.2 設計原則

1. 実行前に必ず合意形成する（Design Interview → Spec → Plan 承認）
2. AI は勝手に実行しない。提案し、人間が判断する（責任境界の維持）
3. 無駄撃ちを回避する（Cost Guard + Two-stage Detection）
4. 失敗から学ぶ（Failure Taxonomy + Experience Memory）
5. 差し戻しではなく再提案（Re-Propose + Plan Diff）
6. **失敗で終わらない——AI 組織が自律的に計画を練り直す（Self-Healing DAG）** ★v11.2
7. **ローカルファイルは最大の資産——セキュアに読み込み、文脈として活用する** ★v11.2

---

## 9 層アーキテクチャ

```
① User Layer
       ↓
② Design Interview（壁打ち・すり合わせ）       ★v11.1
       ↓
③ Task Orchestrator（司令塔）
   ├── Spec Writer        ★v11.1
   ├── Plan/DAG 提案
   ├── Cost Guard         ★v11.1
   ├── Quality SLA        ★v11.1
   └── Self-Healing DAG   ★v11.2  ← 失敗時に自律的にDAGを再構築
       ↓
④ Skill Layer
   ├── Skill Gap Negotiation  ★v11.1
   ├── Skill ROI Explainer    ★v11.1
   └── Local Context Skill    ★v11.2  ← ローカルファイル読み込み・分析
       ↓
⑤ Judge Layer
   ├── Two-stage Detection    ★v11.1
   └── Policy Pack            ★v11.1
       ↓
⑥ Re-Propose Layer            ★v11.1
   └── Dynamic DAG Rebuild    ★v11.2  ← Judge差し戻し時の自動再計画
       ↓
⑦ State & Memory
   ├── Experience Memory       ★v11.1
   ├── Artifact Bridge         ★v11.1
   ├── Failure Taxonomy        ★v11.1
   └── Knowledge Refresh       ★v11.1
       ↓
⑧ Provider Interface
   ├── LiteLLM Gateway
   ├── Recommendation Ladder   ★v11.1
   └── Model Catalog Auto-Update ★v11.1
       ↓
⑨ Skill Registry（エコシステム）  ★v11.2
   ├── Skill パッケージング
   ├── Skill 公開・検索
   └── コミュニティ Skill インストール
```

---

## セクション構成

| Section | 内容 | 担当 |
|---------|------|------|
| 2 | リポジトリ初期化 | Claude Code |
| 3 | バックエンド全構築（17モジュール: 14+3新規） | Claude Code |
| 4 | フロントエンド構築（7画面 + Self-Healing可視化） | Claude Code |
| 5 | YouTube Skills（5 Skills）+ Local Context Skill | Claude Code |
| 6 | Tauri 統合・ビルド | Claude Code |
| 7 | テスト・ベンチマーク | Claude Code |

---

## セクション 3 — バックエンド実装順序

    1. Token Store
    2. OpenRouter OAuth PKCE
    3. LiteLLM Gateway + Model Catalog Auto-Update
    4. Google OAuth + AuthHub
    5. Policy Pack
    6. Cross-Model Judge + Two-stage Detection
    7. 状態機械
    8. Experience Memory + Failure Taxonomy + Artifact Bridge
    9. Skill フレームワーク + Skill Gap Negotiation + ROI
    10. Skill 自動生成エンジン
    11. Design Interview + Spec Writer
    12. Task Orchestrator + Cost Guard + Quality SLA + Re-Propose
    13. Knowledge Refresh
    14. Self-Healing DAG（動的DAG再構築エンジン）                    ★v11.2
    15. Local Context Skill（ローカルファイル読み込み・分析 Skill）    ★v11.2
    16. Skill Registry（パッケージング・公開・検索基盤）              ★v11.2
    17. main.py 全エンドポイント統合

全 API エンドポイント（33個: 27+6新規）:

    # 認証（7）
    POST /api/auth/login, GET /api/auth/status, POST /api/auth/logout
    POST /api/auth/connect/{svc}, GET /api/auth/connections
    DELETE /api/auth/disconnect/{svc}, GET /api/auth/token/{svc}

    # Design Interview（3）★v11.1
    POST /api/interview/start, POST /api/interview/respond
    POST /api/interview/finalize

    # Orchestrate（8: 6+2新規）
    POST /api/orchestrate, GET /api/orchestrate/{id}
    POST /api/orchestrate/{id}/approve-plan   ★v11.1
    POST /api/orchestrate/{id}/repropose      ★v11.1
    GET  /api/orchestrate/{id}/cost           ★v11.1
    GET  /api/orchestrate/{id}/diff           ★v11.1
    POST /api/orchestrate/{id}/self-heal      ★v11.2  ← Self-Healing DAG再構築トリガー
    GET  /api/orchestrate/{id}/heal-history   ★v11.2  ← 自己修復の試行履歴

    # コア（2）
    POST /api/chat, POST /api/judge

    # タスク（3）
    POST /api/tasks, GET /api/tasks/{id}, POST /api/tasks/{id}/transition

    # Skill（4）
    GET /api/skills, POST /api/skills/execute
    POST /api/skills/generate, GET /api/skills/gaps  ★v11.1

    # Skill Registry（4）★v11.2
    GET  /api/registry/search                ← コミュニティSkill検索
    POST /api/registry/publish               ← Skill公開
    POST /api/registry/install               ← Skill インストール
    GET  /api/registry/popular               ← 人気Skill一覧

    # その他（2）
    GET /api/settings, PUT /api/settings, GET /api/health

---

## 追加要素22件の技術仕様（19件 + v11.2 3件）

### #1-3: Design Interview + Spec Writer

interview/interviewer.py:

- start_interview(user_input) → InterviewSession（質問リスト生成）
- process_response(session_id, answers) → NextQuestion | SpecDraft
- finalize(session_id) → Spec（不足分をAIが補完）
- 質問形式: 選択式 + 自由記述の両方
- 深い質問: ユーザーが言語化していない前提を掘り起こす

interview/spec_writer.py:

- generate_spec(interview_data) → SpecDocument
- SpecDocument: {requirements, constraints, priorities, acceptance_criteria}

### #4: Plan/DAG 提案（Orchestrator に統合済み）

Plan 生成後に即実行せず、ユーザーに提示して承認を得る。
人間の判断が必要な箇所をハイライト表示。

### #5: Cost Guard

orchestrator/cost_guard.py:

- estimate_cost(plan, quality_mode) → CostEstimate
- CostEstimate: {api_calls, tokens, cost_usd, time_seconds, model_breakdown}
- 予算超過時は代替 Plan を自動提案
- タスク複雑度→モデル自動切替

### #6: Two-stage Detection

judge/pre_check.py:

- Stage 1（ルールベース、安い）: 入力不足/禁止事項/コスト超過/危険操作
- Stage 2（Cross-Model Judge、高い）: 論理/根拠/矛盾検証
- Stage 1 PASS 時のみ Stage 2 実行

### #7: Failure Taxonomy

state/failure.py:

- FailureType: AUTH_ERROR | RATE_LIMIT | SPEC_CHANGE | INPUT_MISSING |
  EVIDENCE_WEAK | CONTRADICTION | TIMEOUT | UNKNOWN
- classify_failure(error) → FailureRecord
- suggest_recovery(failure) → RecoveryStrategy

### #8-10: Re-Propose + Plan Diff

orchestrator/repropose.py:

- 再実行粒度: FULL_REGENERATE | FROM_STEP_N | PLAN_MODIFY
- Change Request ベースの再提案
- Plan Diff: 差分保存→テンプレ + 差分で再利用

### #11: Skill Gap Negotiation

skills/gap_detector.py:

- detect_gaps(plan, registry) → list[SkillGap]
- 3案提示: 代替Skill / 自動生成 / スキップ
- 勝手に生成しない（ユーザー承認必須）

### #12: Skill ROI Explainer

skills/roi_explainer.py:

- explain_roi(skill_name) → {alternatives, value, risks}

### #13: Quality SLA Selector

orchestrator/quality_sla.py:

- FASTEST: fast モデルのみ、Judge スキップ
- BALANCED: fast + quality、Two-stage Judge
- HIGH_QUALITY: quality + reason、Full Judge + 2回実行

### #14: Policy Pack

policy/policy_pack.py:

- PolicyRule: {category, pattern, severity, suggestion}
- check_policy(text) → list[PolicyViolation]
- 提案段階で提示、採用可否はユーザー判断

### #15: Recommendation Ladder

AI内部思考フレーム（エンドポイントなし）。
「今すぐやる / 次にやる / やらないこと」をプロンプトに構造化。

### #16: Experience Memory

state/experience.py:

- ExperienceCard: {task_type, success_factors, model_used, score, context}
- aiosqlite の experiences テーブルに永続化
- Plan 生成時に過去成功体験を自動参照

### #17: Artifact Bridge

state/artifact_bridge.py:

- 成果物スロット化（insight / copy / data / analysis）
- 別業務の入力へ自動差し込み提案

### #18: Knowledge Refresh

state/knowledge.py:

- ソース登録 → 差分取得 → 要約 / 重要度判定
- MVP では手動トリガー

### #19: Model Catalog Auto-Update

gateway/model_catalog.py:

- OpenRouter API からカタログ取得
- 候補抽出 → スモークベンチ → 適用 → ロールバック
- 既定 ON、失敗率上昇で自動ロールバック

### #20: Self-Healing DAG（動的DAG再構築）★v11.2

orchestrator/self_healing.py:

- Judge が品質基準を満たさないと判断（差し戻し）した場合、またはSkill実行エラー時に発動
- Orchestrator が自律的に Plan（DAG）を再構築し、別のアプローチでリトライ
- 再構築戦略:
  - RETRY_SAME: 同じSkillを別モデルで再実行
  - SWAP_SKILL: 代替Skillに切り替え
  - REPLAN: DAG全体を再生成（失敗原因を考慮）
  - DECOMPOSE: 失敗ステップをサブステップに分割
- 最大リトライ回数: 3回（超過で人間にエスカレーション）
- 各試行の履歴を保存（heal_history テーブル）
- Failure Taxonomy + Experience Memory を参照して最適な回復戦略を選択

```python
class HealStrategy(str, Enum):
    RETRY_SAME = "retry_same"
    SWAP_SKILL = "swap_skill"
    REPLAN = "replan"
    DECOMPOSE = "decompose"

class HealAttempt(BaseModel):
    attempt_number: int
    strategy: HealStrategy
    original_error: str
    new_plan_id: str | None
    result: str  # success | failed | escalated
    timestamp: datetime

async def self_heal(orchestration_id: str, failure: FailureRecord) -> HealAttempt:
    """失敗からの自律回復を試みる。"""
    ...

async def get_heal_history(orchestration_id: str) -> list[HealAttempt]:
    """自己修復の試行履歴を返す。"""
    ...
```

### #21: Local Context Skill（ローカルファイル分析）★v11.2

skills/builtins/local_context/executor.py:

- ローカルファイルシステムからファイルを安全に読み込み、AI組織のコンテキストとして活用
- 対応形式: テキスト(.txt, .md, .csv), ドキュメント(.pdf, .docx), 画像(.png, .jpg)
- セキュリティ:
  - ユーザーが明示的に許可したディレクトリのみアクセス可能
  - 許可ディレクトリは settings で管理（%APPDATA%/zpcos/allowed_dirs.json）
  - ファイル内容はローカルでのみ処理、外部送信時はユーザー承認必須
- Skill入力: ファイルパス or ディレクトリパス + 分析指示
- Skill出力: ファイル内容の要約・分析・構造化データ

```python
class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        """ローカルファイルを読み込み、AIで分析。"""
        path = input_data["path"]
        instruction = input_data.get("instruction", "内容を要約してください")
        # 許可ディレクトリチェック
        # ファイル読み込み
        # LLMで分析
        ...
```

### #22: Skill Registry（エコシステム基盤）★v11.2

skills/registry.py:

- Skillをパッケージマネージャのように共有できるプラットフォーム基盤
- Skill パッケージ形式: SKILL.json + executor.py + README.md を ZIP 化
- MVP では GitHub リポジトリベースのレジストリ（将来的に専用サーバー）
- 機能:
  - search(query) → 条件に合うSkill一覧
  - publish(skill_dir) → Skillをパッケージ化して公開
  - install(skill_id) → コミュニティSkillをローカルにインストール
  - popular() → ダウンロード数・評価順の人気Skill
- セキュリティ: インストール前にセキュリティバリデーション実行（既存のSafe importチェック）

```python
class SkillPackage(BaseModel):
    name: str
    version: str
    author: str
    description: str
    downloads: int = 0
    rating: float = 0.0
    tags: list[str] = []

async def search_registry(query: str) -> list[SkillPackage]:
    """レジストリからSkillを検索。"""
    ...

async def publish_skill(skill_dir: str) -> SkillPackage:
    """Skillをパッケージ化して公開。"""
    ...

async def install_skill(skill_id: str) -> bool:
    """コミュニティSkillをインストール。"""
    ...
```

---

## 技術的制約

ポート: FastAPI 18234, OpenRouter OAuth 3000, Google OAuth 0
モデル ID: openrouter/ プレフィックス必須
非同期: 全て async def

最新モデル ID（2026年3月）:

    fast    → openrouter/google/gemini-3-flash-preview
    think   → openrouter/google/gemini-3.1-pro-preview
    quality → openrouter/anthropic/claude-sonnet-4.6
    free    → openrouter/meta-llama/llama-4-maverick:free
    reason  → openrouter/deepseek/deepseek-r1
    value   → openrouter/deepseek/deepseek-v3.2

---

---

## 未踏提案のハイライト（v11.2 強化ポイント）

1. **「ローカルに常駐するOSだからこそ、機密データを含めたコンテキストをAI組織がセキュアに操作できる」**
   — 他社クラウドエージェントとの完全な差別化

2. **「失敗したら終わりではなく、AI組織が自律的に計画（DAG）を練り直す自己修復機構を持つ」**
   — 圧倒的な技術的挑戦（Self-Healing DAG）

3. **「自分のクリエイティブな時間を奪う『作業』への憎悪（起心動念）から生まれた、超実用的なMVP」**
   — 情熱と熱量

4. **「世界中の開発者が業務自動化Skillを公開し合うプラットフォーム」**
   — Skill Registryによるコミュニティ駆動のエコシステム

---

以上が ZPCOS 完全構築設計書 v11.2 である。
