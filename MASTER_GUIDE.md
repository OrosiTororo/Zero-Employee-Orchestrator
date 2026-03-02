# ZPCOS v11.2 マスター実行ガイド

> 作成日: 2026-03-02
> v11.2: 追加要素22件統合（v11.1の19件 + Self-Healing DAG, Local Context Skill, Skill Registry）

---

## ファイル一覧と役割

| ファイル | 内容 | 渡す先 | 更新 |
|---------|------|--------|------|
| DESIGN_v11.md | 改訂設計書（9層アーキテクチャ） | 参照用 | ★v11.2 |
| instructions_section2_init.md | リポジトリ初期化 | **Claude Code** | ★v11.2 |
| instructions_section3_backend.md | バックエンド全構築（17モジュール） | **Claude Code** | ★v11.2 |
| instructions_section4_frontend.md | フロントエンド全構築（7画面+Self-Healing可視化） | **Antigravity** | ★v11.2 |
| instructions_section5_skills.md | YouTube 5 Skills + Local Context Skill | **Claude Code** | ★v11.2 |
| instructions_section6_tauri.md | Tauri 統合・ビルド | **両方** | 変更なし |
| instructions_section7_test.md | テスト・ベンチマーク | **Claude Code** | ★v11.2 |

---

## v11.0 → v11.1 → v11.2 の変更サマリー

### v11.1 新モジュール（バックエンド +13 ファイル）

- interview/interviewer.py — Design Interview + Spec Writer
- judge/pre_check.py — Two-stage Detection (Stage 1)
- policy/policy_pack.py — Policy Pack
- orchestrator/cost_guard.py — Cost Guard
- orchestrator/quality_sla.py — Quality SLA Selector
- orchestrator/repropose.py — Re-Propose + Plan Diff
- state/experience.py — Experience Memory
- state/failure.py — Failure Taxonomy
- state/artifact_bridge.py — Artifact Bridge
- state/knowledge.py — Knowledge Refresh
- gateway/model_catalog.py — Model Catalog Auto-Update
- skills/gap_detector.py — Skill Gap Negotiation
- skills/roi_explainer.py — Skill ROI Explainer

### v11.2 新モジュール（バックエンド +3 ファイル）

- orchestrator/self_healing.py — Self-Healing DAG（動的DAG再構築エンジン）
- skills/builtins/local_context/ — Local Context Skill（ローカルファイル分析）
- skills/registry.py — Skill Registry（エコシステム基盤）

### 新エンドポイント（v11.1: +7、v11.2: +6、合計33）

- POST /api/interview/start, /respond, /finalize
- POST /api/orchestrate/{id}/approve-plan
- POST /api/orchestrate/{id}/repropose
- GET /api/orchestrate/{id}/cost, /diff
- GET /api/skills/gaps
- POST /api/orchestrate/{id}/self-heal ★v11.2
- GET /api/orchestrate/{id}/heal-history ★v11.2
- GET /api/registry/search, POST /api/registry/publish ★v11.2
- POST /api/registry/install, GET /api/registry/popular ★v11.2

### 新画面（+1、合計7 + Self-Healing可視化パネル）

- /interview — Design Interview
- Orchestration画面にSelf-Healing試行履歴パネル追加 ★v11.2

### 新テスト（v11.1: +7、v11.2: +3）

- test_policy_pack, test_pre_check, test_failure_taxonomy
- test_experience_memory, test_cost_guard, test_quality_sla, test_gap_detector
- test_self_healing, test_local_context, test_skill_registry ★v11.2

---

## 実行順序（厳守）

    Phase 1: Section 2（Claude Code）→ リポジトリ初期化
    Phase 2: Section 3（Claude Code）→ バックエンド14モジュール
    Phase 3: Section 4（Claude Code）→ フロントエンド7画面
    Phase 4: Section 5（Claude Code）→ YouTube 5 Skills
    Phase 5: Section 6（Claude Code）→ Tauri 統合
    Phase 6: Section 7（Claude Code）→ テスト

---

## 未踏 MVP デモシナリオ（v11.2 版）

### 背景ストーリー（起心動念）

「YouTubeチャンネルを伸ばしたい。でもトレンド分析に3時間、台本作成に5時間、
競合調査に2時間…毎週10時間以上が『作業』に消える。本当にやりたい企画会議や
撮影に時間が割けない。この苦しみを、AI組織に全部任せたい。」

### デモフロー

ユーザー: 「YouTubeチャンネルを伸ばして」

1. **Design Interview**: AI が深い質問（ターゲット層は？予算は？現在の課題は？）
2. ユーザーが回答 → **Spec 生成** → 承認
3. **Local Context Skill** ★v11.2: ローカルにある過去の動画企画書・分析シートを
   セキュアに読み込み、チャンネルの文脈を深く理解（クラウドAIにはできない）
4. **Plan 生成**: 6 Skill の DAG + **コスト見積り** + **品質モード選択**
5. **Skill Gap チェック**: 不足があれば提示（なければスキップ）
   → 不足Skillは **Skill Registry** ★v11.2 からコミュニティSkillを提案
6. ユーザーが **Plan 承認** → 実行開始
7. 各 Skill 実行 → **Two-stage Judge**（Stage1安価チェック → Stage2 Cross-Model）
8. **Self-Healing** ★v11.2: もしSkillが失敗したら、AI組織が自律的にDAGを
   再構築して別のアプローチでリトライ（人間に戻さず自動回復）
9. 統合レポート → **Policy Pack** でコンプラチェック
10. Human Review → 承認 or **Re-Propose**（Change Request ベースの再提案）
11. 完了 → **Experience Memory** に成功要因保存

---

## 追加要素22件のマッピング

| # | 要素 | 実装先 | API |
|---|------|--------|-----|
| 1 | Design Interview | interview/interviewer.py | /api/interview/* |
| 2 | AskUserQuestion + @SPEC.md | interview/interviewer.py | 同上 |
| 3 | Spec Writer | interview/interviewer.py (finalize) | 同上 |
| 4 | Plan/DAG 提案 | orchestrator/planner.py（v11.0既存） | /api/orchestrate |
| 5 | Cost Guard | orchestrator/cost_guard.py | /api/orchestrate/{id}/cost |
| 6 | Two-stage Detection | judge/pre_check.py | Judge内部で自動 |
| 7 | Failure Taxonomy | state/failure.py | 内部使用 |
| 8 | Re-Propose | orchestrator/repropose.py | /api/orchestrate/{id}/repropose |
| 9 | 再実行粒度 | orchestrator/repropose.py (ReExecuteMode) | 同上 |
| 10 | Plan Diff | orchestrator/repropose.py (compute_diff) | /api/orchestrate/{id}/diff |
| 11 | Skill Gap Negotiation | skills/gap_detector.py | /api/skills/gaps |
| 12 | Skill ROI Explainer | skills/roi_explainer.py | 内部使用 |
| 13 | Quality SLA Selector | orchestrator/quality_sla.py | フロント選択→API送信 |
| 14 | Policy Pack | policy/policy_pack.py | Judge内部で自動 |
| 15 | Recommendation Ladder | Orchestrator/Judgeプロンプト内 | 内部 |
| 16 | Experience Memory | state/experience.py | 内部（タスク完了時自動保存） |
| 17 | Artifact Bridge | state/artifact_bridge.py | 内部 |
| 18 | Knowledge Refresh | state/knowledge.py | MVP:手動 |
| 19 | Model Catalog Auto-Update | gateway/model_catalog.py | 内部（起動時自動） |
| **20** | **Self-Healing DAG** ★v11.2 | orchestrator/self_healing.py | /api/orchestrate/{id}/self-heal, heal-history |
| **21** | **Local Context Skill** ★v11.2 | skills/builtins/local_context/ | Skill Layer内部 |
| **22** | **Skill Registry** ★v11.2 | skills/registry.py | /api/registry/* |

---

---

## 未踏提案での差別化ポイント（v11.2）

| ポイント | 対策PM | 訴求内容 |
|---------|--------|---------|
| ローカル特権アクセス | 竹迫PM・落合PM | 機密データを含むローカルファイルをセキュアにAI組織が操作。クラウドAIにはできない |
| Self-Healing DAG | 田中PM | 失敗からAIが自律的にDAGを再構築する自己修復機構。「とてつもなく難しい実装」 |
| 起心動念のストーリー | 稲見PM・曾川PM | 作業に奪われる時間への憎悪から生まれた、泥臭いペインの解決 |
| Skill Registry | 竹迫PM他 | 世界中の開発者がSkillを公開し合うエコシステム。プロジェクト終了後の波及効果 |

---

## 将来的な設計

SkillsだけでなくMCPにも対応し、Work IQにも繋げられるようにしたい。
ユーザーが自然言語だけでSkillsを作成できる点を活かして、Skillを公開し合うエコシステムを構築したい。

---

以上。Phase 1 → 6 を順に実行すれば ZPCOS v11.2 MVP が完成する。
