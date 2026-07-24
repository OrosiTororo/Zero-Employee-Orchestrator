# refactor-instructions.md — Zero-Employee Orchestrator リファクタリング実装指示書

> 対象リポジトリ: `OrosiTororo/Zero-Employee-Orchestrator`(v0.1.7 系)
> 分析日: 2026-07-24 / 分析対象 commit: `1d896c9`(プロダクトコードは master HEAD `de23344` と同一)
>
> 実装担当モデルへの依頼文:
> **本書の `Required Scope` だけを、`Stop And Ask Conditions` を守りながら実装し、`Definition of Done` を満たすこと。**
> 本書に書かれていない大規模な削除・全面書き換え・「ついでの改善」は禁止。

---

## Objective

既存の外部挙動(API レスポンス、OpenAPI スキーマ、CLI 出力、DB スキーマ、セキュリティ保証)を一切変えずに、根拠を確認済みの技術的負債のうち **小さく・安全で・検証可能な 5 件のみ** を解消する。

1. ORM モデルの置き場の一貫性を回復する(サービス層に置かれた `BrainstormSessionRecord`)。
2. 依存方向の乱れを正す(認証 DI 依存関係がルートモジュール `routes/auth.py` に置かれている問題)。
3. FastAPI 依存性ジェネレータの手動消費(`async for db in get_session()`)を正規のセッション管理に置き換える。
4. `main.py` からの私有属性アクセス(`mcp_server._tools`)を公開アクセサに置き換える。
5. ドキュメント数値主張(432 endpoints)の検証手段をスクリプトとして固定化する。

**目的はコードの見た目を綺麗にすることではない。** 既存仕様を壊さず、検証済みの負債だけを戻しやすい単位で減らすことである。

---

## Repository State

分析開始時点の状態(実装担当は Phase 0 で自分でも取り直すこと):

- リポジトリルート: `git rev-parse --show-toplevel` → リポジトリのクローン先ルート
- デフォルトブランチ: `master`(remote HEAD)
- 作業ブランチ: `claude/refactor-instructions-improvement-28723g`(HEAD `1d896c9`)
- `git status --short` → 出力なし(**未コミット変更なし、クリーン**)
- master(`de23344`)との差分: `refactor-instructions.md` のみ(+383 行、ドキュメントのみ)。**プロダクトコードは master HEAD と完全に同一。**
- 直近の履歴: `de23344` Merge PR #498(repository-overall-improvement)、`fc308f8` fix(desktop)、`03a9e8b` ci: pip-audit 例外、ほか dependabot 系

実装開始時に未コミット変更(本書自身を除く)が存在する場合は、上書き・破棄せず停止して報告すること。

---

## Project Understanding

### プロダクト概要

ZEO(Zero-Employee Orchestrator)は「AI メタオーケストレーター」。CrewAI / AutoGen / LangChain / Dify / n8n などの AI フレームワークと 63 業務アプリを、**人間の承認ゲート・監査ログ・セキュリティ層の下に統合**する。9 層アーキテクチャ(User → Design Interview → Task Orchestrator (DAG) → Skills → Judge → Re-Propose → State & Memory → Provider (LiteLLM) → Skill Registry)。

### コンポーネントとエントリーポイント(検証済み)

| コンポーネント | エントリーポイント | 備考 |
|---|---|---|
| FastAPI バックエンド | `apps/api/app/main.py` | ポート 18234。lifespan で `Base.metadata.create_all` + システムスキル登録 + best-effort 初期化群 |
| CLI | `apps/api/app/cli.py` の `main()` | console_script `zero-employee = "app.cli:main"` が **root `pyproject.toml:79` と `apps/api/pyproject.toml:78` の両方**に定義 |
| デスクトップ UI | `apps/desktop/ui/src/main.tsx` | Tauri v2 + React + Vite。デザインシステム "Clarity" |
| Edge | `apps/edge/proxy`, `apps/edge/full` | Cloudflare Workers (Hono) |
| MCP サーバー | `apps/api/app/integrations/mcp_server.py` | JSON-RPC 2.0 + stdio |

### バックエンドの層構造(すべて 2026-07-24 に grep/読解で検証)

- `apps/api/app/api/routes/`: **53 ルートモジュール + `__init__.py`(計 54 .py)、REST エンドポイント 432 個**(`@router.get|post|put|patch|delete` デコレータ数。websocket デコレータは routes/ 内 0 件)。
- `apps/api/app/services/`: 30 ファイル。**サービス層は `HTTPException` を一切 raise しない**(grep 0 件)。HTTP エラー変換はルート層の責務。この規律は維持すること。
- DB セッションの正規ルートは `apps/api/app/api/deps/database.py` の `get_db`(**成功時 commit / 例外時 rollback**)。ルート 26 ファイルが `app.api.deps` からインポート。
- `apps/api/app/core/database.py:65-68` の `get_session` は FastAPI 依存用 async generator で、**auto-commit しない**(`async with async_session_factory() as session: yield session` のみ)。
- `apps/api/app/api/deps/services.py` は DI シングルトン(`get_sandbox` 等)。docstring に「テストで override 可能にする」設計意図が明記。
- `apps/api/app/repositories/` は `base` / `ticket_repository` / `audit_repository` の 3 つのみ。他のサービスは ORM を直接クエリする(方針未決定 — D9)。
- テスト: `apps/api/app/tests/` に 61 .py(`test_alembic_stamp.py`、ベンチ用 `zeo_bench.py` を含む)。

### DB スキーマ管理(3 系統が意図的に共存 — 壊すな)

1. 起動時 `Base.metadata.create_all`(`main.py` lifespan)— 新規インストール用。
2. Alembic(`apps/api/alembic/versions/` に 4 リビジョン)— 既存インストールの差分適用用。
3. `apps/api/app/core/version_migration.py` — pre-Alembic 期(v0.1.0〜v0.1.2)からの追加専用アップグレードラダー(`test_alembic_stamp.py` でテスト済み)。

この共存は設計判断であり、**リファクタリング対象ではない。**

### セキュリティ機構(CLAUDE.md の非交渉事項)

- 外部データ → LLM: `wrap_external_data()`(`security/prompt_guard.py`)必須。
- ユーザー入力 → AI: `pii_guard.py` の PII 検査必須。
- ファイルアクセス: `sandbox.py` 経由必須。危険操作は `approval_gate.py` + `autonomy_boundary.py`。
- `main.py:242` で `InputSanitizationMiddleware` がグローバル適用され、**さらに** 16 のルートファイルが個別に `detect_and_mask_pii` / `scan_prompt_injection` を呼ぶ(多層防御の可能性 — D7、変更禁止)。

### CI が検証していること(`.github/workflows/ci.yml`)

- root と `apps/api/` の 2 つの `pyproject.toml` のメタデータ完全同期(version / dependencies / ruff select 等)。**片方だけの変更は CI で落ちる。**
- ruff check + ruff format --check、pytest(カバレッジ付き)、pip-audit、**Alembic モデル整合チェック(ci.yml:157 で `import app.models` に依存 — D3 に直結)**、Trivy、red-team テスト、フロントエンド tsc / vitest / build。

### バージョン管理

バージョンは 8 ファイルに分散、`./scripts/bump-version.sh` でのみ更新。**本リファクタリングではバージョンを変更しない。**

---

## Scope And Evidence Limits

本書の根拠は以下の範囲の調査に基づく。**「プロジェクト全体を読んだ」とは主張しない。**

**調査した範囲(ファイル読解 + grep + カウント)**:
- `apps/api/app/` の構造全般。特に `main.py`(lifespan / middleware)、`core/database.py`、`api/deps/`、`api/routes/`(カウント + auth.py / multi_model.py / dispatch.py / tickets.py / file_upload.py / themes.py / self_improvement.py の該当行)、`orchestration/executor.py:670-695`、`integrations/mcp_server.py`(該当行)、`services/`(一覧 + multi_model_service.py / ticket_service.py / self_improvement 分割)、`repositories/`、`security/iam.py`(該当行)、`cli.py`(パーサ構造)、`tests/`(一覧 + conftest.py 冒頭)
- root / `apps/api/` の `pyproject.toml`、`.github/workflows/ci.yml`(pyproject 同期・app.models インポート箇所)、`alembic/versions/` の件数
- `README.md:212`、`CLAUDE.md`、`docs/` のディレクトリ構成
- `apps/desktop/ui/src/pages/` は**行数の計測のみ**(ロジック未読)

**調査していない範囲(本書は根拠を主張しない)**:
- `apps/edge/`、`plugins/`、`skills/`、`extensions/`、`packages/` の中身
- 翻訳ドキュメント(docs/ja-JP 等)の内容
- 実行時挙動(本分析環境では Python 依存が未インストールのため、サーバー起動・pytest 実行は不可 — Baseline 参照)
- フロントエンドのロジック・テストカバレッジの詳細
- 秘密情報(`.env` 等)は読んでいない

行番号は commit `1d896c9` 時点のもの。実装時にズレていたら周辺のシンボル名で特定し直すこと。

---

## Behaviors To Preserve(絶対に壊してはいけない挙動)

1. **全 432 REST エンドポイントのパス・メソッド・レスポンス形状**。OpenAPI 出力の差分ゼロ(検証方法は Verification Requirements 参照)。
2. **DB スキーマ**: テーブル名・カラム名・型を一切変更しない。`brainstorm_sessions`(REQ-1)はクラスの移動のみでスキーマ不変。
3. **CLI の全コマンドとフラグ**: `zero-employee serve|db|health|config|local|chat|models|pull|update|upgrade|mcp|security` および chat 内スラッシュコマンド。console_script のインポートパス `app.cli:main` を維持。
4. **セキュリティ層の挙動**: prompt_guard / pii_guard / sandbox / iam / approval_gate / sanitizer / security_headers / input_sanitization の入出力を変更しない。
5. **後方互換ファサード**: `app/services/self_improvement_service.py` は `self_improvement/` パッケージ分割の互換レイヤー。削除禁止(REQ-1, REQ-2 はこの前例に倣う)。
6. **i18n**: 6 言語の HTTP エラー翻訳(`main.py` の exception handler)と `Accept-Language` 処理。
7. **lifespan の best-effort 初期化**: `main.py` の各 try/except(runtime config / Ollama / Sentry / MCP / モデルカタログ等)は「失敗しても起動する」ことが仕様。例外を伝播させる変更をしない。
8. **サービス層が HTTPException を投げない**規律(現状 grep 0 件)。
9. **トランザクション境界**: `get_session` は auto-commit しない。既存呼び出し箇所の commit 有無(例: `mcp_server.py` 自体は `commit()` 0 件で、書き込みは `ticket_service.create_ticket` 等サービス内 commit に依存)を**現状と完全に同一**に保つ。commit の追加・削除は禁止。
10. **既知のインメモリ挙動**: dispatch タスク・面談セッション・アップロードファイル等が再起動で消えるのは既知のトレードオフ(D5)。**永続化を勝手に実装しない。**

---

## Non-Negotiables(作業規律)

1. 最初に `git status --short` を確認し、開始時の未コミット変更を記録する。上書き・破棄・無関係な整形をしない。
2. 既存差分と必要な編集箇所が重なる場合は停止して質問する。
3. 編集前に baseline コマンド・結果・終了コードを記録する(Baseline Commands And Results 参照)。baseline に既存失敗がある場合、新規失敗と区別して報告する。
4. 変更は小さく戻しやすい単位にする。**1 コミット = 1 つの REQ 項目**。フェーズをまたぐコミットをしない。
5. `Required Scope` 外のファイル・挙動を変更しない。無関係な整形・依存更新・ついでのリファクタリングをしない(ruff format は全ファイル適用済みのため、触ったファイル以外に diff を発生させない)。
6. テスト削除・テストの弱体化・広範な ignore 追加で検証を通さない。
7. 公開 API、保存形式、設定キー、エラーの意味を勝手に変えない。
8. 正しさが不明になった時点で実装を止めて質問する。
9. 各フェーズごとに対象を絞った検証を行い、最後に baseline 相当の検証を再実行する。
10. commit や push は、利用者から明示的に依頼された場合だけ行う。
11. ドキュメント上の数値(バージョン・エンドポイント数等)を検証なしに変更しない(CLAUDE.md の Evidence-Based Changes)。2 つの `pyproject.toml` は CI で同期チェックされるため片方だけ変更しない — **本 Required Scope では両方とも変更不要のはず。変更が必要になったら停止。**
12. 翻訳済みドキュメントは触らない(本 Required Scope はユーザー向け機能を変えないため同期不要)。

---

## Stop And Ask Conditions(実装を止めて質問する条件)

以下のいずれかに該当したら、**実装を中断し、状況と選択肢を報告して指示を待つこと**:

1. 変更が **DB スキーマ、保存済みデータ、公開 API の形状、OpenAPI 出力**に影響し得ると気づいたとき。
2. **テストと実装が矛盾**しているとき(どちらが正か勝手に決めない)。
3. 削除候補コードが本当に不要か確信できないとき(re-export ファサードは意図的な互換レイヤー — 削除禁止)。
4. **認証・課金・通知・外部連携**(OAuth、Sentry、app_connector、MCP プロトコル、A2A)の意味を変える必要が生じたとき。
5. REQ-4 の変換対象で「commit されていない書き込みパス」を発見したとき(勝手に commit を足さず、現状のまま変換して報告する。判断に迷えば停止)。
6. REQ-2 で `deps/auth.py` への移動が**循環インポート**を起こし、OAuth 状態やルートハンドラまで動かさないと解決しないとき。
7. いずれかの変更で `pyproject.toml`(root / apps/api)の変更が必要になったとき。
8. baseline で失敗するテストを発見したとき(自分の変更と無関係でも報告。修正はしない)。
9. 本書に列挙されていない負債を発見し、直したくなったとき(提案として報告し、承認なしに着手しない)。
10. 開始時の未コミット変更と編集対象が重なったとき。

---

## Baseline Commands And Results

### 分析セッション(2026-07-24, commit `1d896c9`)で実行済みの結果

| コマンド | 結果 | 終了コード |
|---|---|---|
| `git status --short` | 出力なし(クリーン) | 0 |
| `ruff check app/`(apps/api で実行、ruff 0.15.8) | `All checks passed!` | 0 |
| `ruff format --check app/` | `297 files already formatted` | 0 |
| エンドポイントカウント(下記 8.2 と同じワンライナー) | `REST endpoints: 432`(53 モジュール + `__init__.py`) | 0 |

### 分析セッションで実行できなかった検証(理由付き)

- **pytest フルスイート**: 分析環境に `fastapi` / `pytest` が未インストールで、依存インストールが禁止されていたため未実行。前版の分析記録(コード同一の `de23344` 時点)では **907 passed / 0 failed(約 6 分)、終了時に litellm 由来の "Logging error" ノイズ(無害、`tests/conftest.py:24-27` に説明あり)** とされているが、**本分析セッションでは未検証**。実装担当は必ず自分で取り直すこと。
- **フロントエンド tsc / vite build**: node_modules 未インストールのため未実行。本 Required Scope はフロントエンドに触れないため必須ではない。
- **サーバー起動スモーク / OpenAPI 採取**: 同上の理由で未実行。Phase 0 で採取すること。

### 実装担当が Phase 0 で確立すべき baseline

```bash
git status --short && git log --oneline -3        # 記録する
cd apps/api
python -m venv .venv && .venv/bin/pip install -e ".[dev]" 2>/dev/null \
  || .venv/bin/pip install -e . pytest pytest-asyncio httpx ruff
# ※ pyproject.toml は編集しない。使い捨て .venv への導入のみ
.venv/bin/ruff check app/ && .venv/bin/ruff format --check app/
.venv/bin/python -m pytest app/tests/ -q           # 全結果(passed/failed/所要時間)を記録
```

さらに OpenAPI スナップショットを採取(変更後の diff 用):

```bash
cd apps/api && SECRET_KEY=demo-key .venv/bin/python -c "
import json
from app.main import app
print(json.dumps(app.openapi(), sort_keys=True))" > /tmp/openapi-before.json
```

baseline に失敗があれば **Stop And Ask 条件 8** に従い報告(修正しない)。

---

## Debt Map

各項目のフィールド: Status(Verified/Hypothesis)/ Evidence / Observation / Why It Matters / Impact / Change Risk / Priority / Recommendation / Verification / Disposition / Stop Condition。

### D1 — 認証 DI 依存関係がルートモジュール内にある

- **Status**: Verified
- **Evidence**: `apps/api/app/api/routes/auth.py:72`(`get_current_user`)、`:560`(`get_optional_user`)。`from app.api.routes.auth import` を含むファイル 53 件(grep)。正規の DI 置き場 `apps/api/app/api/deps/`(`database.py` / `services.py` / `validators.py`)が既存。
- **Observation**: ほぼ全ルートがルートモジュール `auth.py` から共有依存関係をインポートしている。`auth.py` はルート定義・OAuth インメモリ状態(`:132`)・共有 DI の 3 責務を持つ。
- **Why It Matters**: ルート → ルートの依存は変更影響が読みにくく、`auth.py` の編集が全ルートのインポートに波及し得る。DI の正規置き場が既にあるのに使われていない。
- **Impact**: インポート 53 ファイル(ただし互換 re-export で既存インポートは無変更にできる)。
- **Change Risk**: Low
- **Priority**: P1
- **Recommendation**: `app/api/deps/auth.py` を新設し定義を移動、`routes/auth.py` で re-export(`self_improvement_service.py` ファサードの前例に倣う)。既存 53 箇所のインポートは書き換えない。
- **Verification**: `pytest app/tests/test_auth.py app/tests/test_auth_service.py` + フルスイート + OpenAPI diff ゼロ。
- **Disposition**: **Required(REQ-2)**
- **Stop Condition**: 循環インポートが発生し、最小限のヘルパー移動で解決できない場合(Stop And Ask 6)。

### D2 — FastAPI 依存性ジェネレータの手動消費

- **Status**: Verified
- **Evidence**: `apps/api/app/core/database.py:65-68`(`get_session`、auto-commit なし)。消費箇所: `apps/api/app/orchestration/executor.py:678`、`apps/api/app/integrations/mcp_server.py:438, 479, 515, 563, 656, 691`(計 7 箇所、`async for db in get_session(): ... break` パターン)。`mcp_server.py` 内に `commit()` は 0 件(書き込みはサービス層 commit に依存、例: `services/ticket_service.py:85`)。
- **Observation**: DI 用 async generator を通常コードが `async for ... break` で手動消費している。正規手段 `async_session_factory()`(コンテキストマネージャ)が同じモジュールにある。
- **Why It Matters**: generator 消費はクリーンアップのタイミングとエラー時挙動が不明瞭で、`get_session` の実装変更(例: commit 追加)が非 HTTP 経路に予期せず波及する。
- **Impact**: executor の失敗記録パス(best-effort、例外は debug ログで握られる)、MCP ツール 6 個の DB アクセス。
- **Change Risk**: Medium(トランザクション境界を変えないことが条件)
- **Priority**: P1
- **Recommendation**: 各箇所を `async with async_session_factory() as db:` に置き換え。commit の有無は現状と完全同一に保つ(commit を足さない・消さない)。
- **Verification**: `pytest app/tests/test_mcp_server.py` + 関連 DAG/E2E テスト + フルスイート。
- **Disposition**: **Required(REQ-4)**
- **Stop Condition**: 変換対象に commit されていない書き込みパスを発見して判断に迷ったとき(Stop And Ask 5)。

### D3 — ORM モデルがサービス層に定義されている

- **Status**: Verified
- **Evidence**: `apps/api/app/services/multi_model_service.py:128` の `class BrainstormSessionRecord(Base)`(`__tablename__ = "brainstorm_sessions"`)。`apps/api/app/main.py:111` が create_all のため特別インポート(`from app.services.multi_model_service import BrainstormSessionRecord  # noqa: F401`)。CI の Alembic 整合チェックは `import app.models` に依存(`.github/workflows/ci.yml:157`)。
- **Observation**: この 1 クラスだけ `app/models/` の外にあり、`import app.models` では全テーブルが揃わない。
- **Why It Matters**: モデル登録の一貫性が壊れており、create_all・Alembic autogenerate・CI チェックがこの特別インポートの存在を前提にする。忘れると「テーブルが作られない」系の障害になる。
- **Impact**: multi_model サービス/ルート、`main.py`、テストの conftest。
- **Change Risk**: Low(クラス移動 + re-export、スキーマ不変)
- **Priority**: P1
- **Recommendation**: `app/models/brainstorm.py` へ移動し `app/models/__init__.py` に登録、旧位置で re-export、`main.py:110-111` を `import app.models` のみに簡素化。
- **Verification**: create_all 後に `brainstorm_sessions` が存在するテスト + CI 同等の整合チェック + フルスイート。
- **Disposition**: **Required(REQ-1)**
- **Stop Condition**: テーブル名・カラム定義に diff が出たとき(即停止)。

### D4 — 巨大ルートモジュールとインラインスキーマの二重体系

- **Status**: Verified
- **Evidence**: `apps/api/app/api/routes/multi_model.py` は 1,245 行。routes/ 全体でインライン `BaseModel` クラス 449 件(grep)。一方で正規置き場 `apps/api/app/schemas/`(22 ファイル)が存在。
- **Observation**: リクエスト/レスポンス契約の置き場が 2 系統あり、モジュールにより流儀が異なる。
- **Why It Matters**: 契約がどこにあるか探しにくく、1,000 行超モジュールはレビュー・変更が難しい。
- **Impact**: ルート層全体(ただし対処は multi_model.py に限定可能)。
- **Change Risk**: Medium(機械的移動だが diff が大きい)
- **Priority**: P2
- **Recommendation**: `app/schemas/multi_model.py` を新設し Pydantic モデルのみ移動、ハンドラロジック不変、OpenAPI diff ゼロを確認。他ファイルへの水平展開はしない。
- **Verification**: OpenAPI diff ゼロ + フルスイート。
- **Disposition**: **Recommended**(Required 完了後に別途判断。今回は実装しない)
- **Stop Condition**: OpenAPI に差分が出たとき。

### D5 — ルートモジュール内のインメモリ状態

- **Status**: Verified(存在は事実。「直すべきか」はプロダクト判断)
- **Evidence**: `apps/api/app/api/routes/dispatch.py:36`(`_dispatch_tasks`)/ `:549`(`_scheduled_tasks`)、`tickets.py:35`(`_interview_sessions`、コメント「production: persist in DB」)、`file_upload.py:90-91`(`_file_store`、ファイル中身をメモリ保持)、`themes.py:22`(`_custom_themes`)、`auth.py:132`(`_google_oauth_pending`)、`security/iam.py:340`(`_custom_role_policies`)、`self_improvement.py:60`(`_stats`)。
- **Observation**: 再起動で消えるインメモリ dict がルート層に点在。コード内コメントが既知のトレードオフであることを示す。
- **Why It Matters**: 再起動でのデータ消失・マルチワーカー不整合。ただし単一プロセス前提の v0.1.x では設計内。
- **Impact**: 永続化するなら DB スキーマ追加・マイグレーション・API 挙動変化(再起動後の残存)を伴う。
- **Change Risk**: High
- **Priority**: P2
- **Recommendation**: 永続化の要否・対象はプロダクト判断(Open Question Q1)。承認まで現状維持。
- **Verification**: (実装しないため該当なし)
- **Disposition**: **Proposal Only**
- **Stop Condition**: 本項に触れる実装を始めようとした時点で停止(承認なしの実装禁止)。

### D6 — cli.py の 2,268 行モノリス(専用テストなし)

- **Status**: Verified
- **Evidence**: `apps/api/app/cli.py` = 2,268 行。サブコマンド serve / db / health / config / local / chat / models / pull / update / upgrade / mcp / security を単一ファイルに定義(`add_parser` 呼び出し群 `:2010-2234`)。`app/tests/` に `test_cli*` は 0 件(61 テストファイル確認)。console_script は 2 つの pyproject.toml に定義。
- **Observation**: chat 系ヘルパーとサーバー運用系コマンドが同居し、パーサ受理仕様を固定するテストがない。
- **Why It Matters**: テストなしでの分割は回帰に気づけない。変更影響が読めない。
- **Impact**: CLI 全コマンド、console_script、README / USER_SETUP のコマンド例。
- **Change Risk**: Medium
- **Priority**: P2
- **Recommendation**: 先に `build_parser()` の characterization テストを追加し、green を確認してから `app/cli/` パッケージへ分割(`app.cli:main` パス維持)。テストなしの分割は禁止。
- **Verification**: 新設パーサテスト + `zero-employee --help` / `mcp info` スモーク。
- **Disposition**: **Recommended**(安全網テスト追加が先行条件。今回は実装しない)
- **Stop Condition**: 分割で pyproject.toml の変更が必要になったとき。

### D7 — ミドルウェアとルート個別ガードの二重サニタイズ

- **Status**: 存在は Verified、「負債かどうか」は Hypothesis(意図的な多層防御の可能性が高い)
- **Evidence**: `apps/api/app/main.py:242`(`InputSanitizationMiddleware` グローバル適用)+ ルート 16 ファイルが個別に `detect_and_mask_pii` / `scan_prompt_injection` を呼ぶ(grep)。
- **Observation**: 同種のスキャンが 2 層で走る。
- **Why It Matters**: CPU コストと保守の二重化。ただし CLAUDE.md はセキュリティ層を非交渉事項としており、コードからは意図を確定できない。
- **Impact**: セキュリティ保証全体。
- **Change Risk**: High
- **Priority**: P3
- **Recommendation**: 意図確認(Open Question Q2)まで両方を維持。セキュリティの「簡素化」は本書のスコープ外。
- **Verification**: (実装しないため該当なし)
- **Disposition**: **Proposal Only**(実質 No Action。どちらの層も削除禁止)
- **Stop Condition**: 本項に触れる変更を始めようとした時点で停止。

### D8 — ドキュメント数値主張の検証手段が未定義

- **Status**: Verified
- **Evidence**: `README.md:212` と `CLAUDE.md:27` が「53 route modules / 432 endpoints」を主張。実測(2026-07-24): ルートモジュール 53 + `__init__.py`、`@router.<method>` REST デコレータ 432 — **主張は正確**。ただし数え方はどこにも文書化・スクリプト化されていない。
- **Observation**: CLAUDE.md が「数値主張は検証必須」と定める一方、検証コマンドが定義されておらず毎回アドホックに数えることになる。
- **Why It Matters**: 数え方が揺れると、ルート追加時にドキュメント数値の検証・更新を誤る。
- **Impact**: ドキュメント整合性のみ(実行時挙動への影響なし)。
- **Change Risk**: Low(新規スクリプト追加のみ)
- **Priority**: P2
- **Recommendation**: `scripts/count-endpoints.py` を新設し、「routes/*.py の `@router.get|post|put|patch|delete` デコレータ数」という現行実測と一致する定義を docstring に明記して固定化。ドキュメントの数値自体は正確なため変更しない。WS/health/A2A を含める正準定義の変更は Open Question Q3(回答不要で本実装は可能)。
- **Verification**: スクリプト実行結果が 432 / 53 と一致すること。tracked file への変更がスクリプト追加のみであること。
- **Disposition**: **Required(REQ-5)**
- **Stop Condition**: スクリプト実装のためにドキュメント数値の変更が必要になったとき(数値が実測とズレていたら報告して停止)。

### D9 — repositories/ 層の中途半端な抽象化

- **Status**: Verified(存在は事実。方針は未決定)
- **Evidence**: `apps/api/app/repositories/` は base / ticket / audit の 3 モジュールのみ。services/ 30 ファイルの大半は ORM 直接クエリ。
- **Observation**: データアクセスパターンが 2 系統あり、新規コードがどちらに従うべきか不明。
- **Why It Matters**: 一貫性のなさが新規実装の迷いと分散を生む。
- **Impact**: データアクセス層全体。
- **Change Risk**: High(拡大方向)/ Low(方針文書化のみ)
- **Priority**: P3
- **Recommendation**: 拡大か凍結かは設計判断(Open Question Q4)。回答後も、まずは CONTRIBUTING 等への方針記載のみ。
- **Verification**: (実装しないため該当なし)
- **Disposition**: **Proposal Only**
- **Stop Condition**: 本項に触れる実装を始めようとした時点で停止。

### D10 — main.py が MCP サーバーの私有属性にアクセス

- **Status**: Verified
- **Evidence**: `apps/api/app/main.py:166` の `len(mcp_server._tools)`。`_tools` は `apps/api/app/integrations/mcp_server.py:168` で定義される私有 dict。
- **Observation**: 起動ログのツール数表示のためだけに私有属性を読んでいる(読み取りのみ)。
- **Why It Matters**: `mcp_server` 内部表現の変更が `main.py` を壊す。カプセル化違反の前例になる。
- **Impact**: 起動ログ 1 行。
- **Change Risk**: Low
- **Priority**: P2
- **Recommendation**: `mcp_server` に公開アクセサ(例: `tool_count` プロパティ)を追加し、`main.py:166` を置換。
- **Verification**: 起動スモークで同じツール数がログに出ること + `pytest app/tests/test_mcp_server.py`。
- **Disposition**: **Required(REQ-3)**
- **Stop Condition**: MCP プロトコル応答(tools/list 等)の形状を変えないと実装できないと気づいたとき。

### D11 — async コード内の threading.Lock

- **Status**: 存在は Verified、実害は Hypothesis
- **Evidence**: `apps/api/app/api/routes/file_upload.py:90`(`_file_store_lock = threading.Lock()`)、`dispatch.py` 等。
- **Observation**: async ハンドラから threading.Lock を使用。クリティカルセクション内に await がなければ実害はない(未検証)。
- **Recommendation / Verification**: 現状維持。D5 の永続化判断と一緒に扱う。
- **Change Risk**: Low(触らない限り) / **Priority**: P3 / **Impact**: 該当ルートのみ
- **Disposition**: **No Action**
- **Stop Condition**: (作業対象外)

### D12 — tests/ 配下のベンチファイル

- **Status**: Verified
- **Evidence**: `apps/api/app/tests/zeo_bench.py`。pytest のデフォルト収集規則(`test_*.py`)に一致しないため収集されない(pyproject に `python_files` 上書きなし — grep 確認)。
- **Recommendation**: 現状維持。Phase 0 で非収集を確認するのみ。
- **Change Risk**: Low / **Priority**: P3 / **Impact**: なし
- **Disposition**: **No Action**
- **Stop Condition**: (作業対象外)

### D13 — フロントエンドの巨大ページ

- **Status**: Verified(行数のみ。ロジック未読)
- **Evidence**: `apps/desktop/ui/src/pages/ReleasesPage.tsx` 918 行、`SettingsPage.tsx` 840 行、`SetupPage.tsx` 824 行。
- **Observation**: バックエンドと異なり分割の前例・テスト安全網が薄い。
- **Recommendation**: 提案のみ。安全網なしで触らない。
- **Change Risk**: Medium / **Priority**: P3 / **Impact**: デスクトップ UI
- **Disposition**: **Proposal Only**
- **Stop Condition**: 本項に触れる実装を始めようとした時点で停止。

### D14 — i18n 翻訳テーブルのインライン辞書

- **Status**: Verified(サイズのみ)
- **Evidence**: `apps/api/app/core/i18n.py` = 861 行(コード内インライン辞書)。
- **Observation**: データファイル化は CLI/サーバー起動経路のファイル解決に影響し得る。
- **Recommendation**: 提案のみ。
- **Change Risk**: Medium / **Priority**: P3 / **Impact**: 全エラーメッセージ翻訳
- **Disposition**: **Proposal Only**
- **Stop Condition**: 本項に触れる実装を始めようとした時点で停止。

### D15 — docs/zh と docs/zh-CN の分担

- **Status**: 存在は Verified、意図は Hypothesis
- **Evidence**: `docs/zh/`、`docs/zh-CN/`、`docs/zh-TW/` が並存(ディレクトリ一覧で確認)。
- **Recommendation**: 意図確認(Open Question Q5)まで何もしない。
- **Change Risk**: Low / **Priority**: P3 / **Impact**: ドキュメントのみ
- **Disposition**: **Proposal Only**
- **Stop Condition**: (作業対象外)

---

## Required Scope

**この 5 件だけを実装する。** 各項目は 1 コミット。順序は Implementation Phases に従う。

### REQ-1: BrainstormSessionRecord を app/models/ へ移動(D3)

- **目的 / 解消する問題**: `import app.models` で全 ORM テーブルが揃わない不整合を解消し、`main.py` の特別インポートを不要にする。
- **変更してよいファイル**: `apps/api/app/models/brainstorm.py`(新規)、`apps/api/app/models/__init__.py`、`apps/api/app/services/multi_model_service.py`(クラス定義削除 + re-export)、`apps/api/app/main.py`(110-111 行付近のみ)、`apps/api/app/tests/` への安全網テスト追加。
- **変更してはいけない境界**: `__tablename__` / カラム定義 / 型は 1 文字も変えない。multi_model サービスのロジック・ルート・スキーマは触らない。
- **実装手順**:
  1. (Phase 1)create_all 後に `brainstorm_sessions` テーブルが存在することを固定するテストを追加し、green を確認。
  2. `app/models/brainstorm.py` を新設しクラスを移動、`app/models/__init__.py` に登録。
  3. `multi_model_service.py` で `from app.models.brainstorm import BrainstormSessionRecord` を re-export(既存インポート互換)。
  4. `main.py:110-111` を `import app.models  # noqa: F401` のみに簡素化。
- **挙動を固定するテスト**: 手順 1 のテスト(移動の前後で green であること)。
- **受け入れ条件**: 手順 1 のテストが移動後も green / `from app.services.multi_model_service import BrainstormSessionRecord` が引き続き成功 / CI 同等の create_all チェック成功 / フルスイートに新規失敗なし / OpenAPI diff ゼロ。
- **検証コマンド**: 8.1 + 8.3 + 8.4(Verification Requirements 参照)。
- **停止条件**: スキーマ diff の発生、Alembic 整合チェックの失敗。

### REQ-2: 認証 DI を app/api/deps/auth.py へ移動(D1)

- **目的 / 解消する問題**: ルート → ルート依存を解消し、DI を正規置き場に集約する。
- **変更してよいファイル**: `apps/api/app/api/deps/auth.py`(新規)、`apps/api/app/api/routes/auth.py`(定義の移動 + re-import)。
- **変更してはいけない境界**: 既存 53 ファイルのインポート文は書き換えない。`get_current_user` / `get_optional_user` のシグネチャ・例外・戻り値を変えない。OAuth 状態(`_google_oauth_pending`)とルートハンドラは `routes/auth.py` に残す。
- **実装手順**:
  1. `get_current_user` / `get_optional_user` と、それらだけが必要とする最小限のヘルパーを `deps/auth.py` へ移動。
  2. `routes/auth.py` の先頭で re-import し、既存のインポートパスを維持。
- **挙動を固定するテスト**: 既存の `test_auth.py` / `test_auth_service.py` / `test_security_integration.py`(存在確認済みは前者 2 つ。3 つ目がなければ既存の認証系テストで代替)。
- **受け入れ条件**: `from app.api.routes.auth import get_current_user` が引き続き成功 / 認証系テストとフルスイートに新規失敗なし / OpenAPI diff ゼロ(security scheme 含む)。
- **検証コマンド**: 8.1 + 8.4。
- **停止条件**: 循環インポートが最小限の移動で解決できない場合(Stop And Ask 6)。

### REQ-3: mcp_server の私有属性アクセスを公開アクセサに置換(D10)

- **目的 / 解消する問題**: `main.py` からのカプセル化違反(`_tools` 直接参照)を解消。
- **変更してよいファイル**: `apps/api/app/integrations/mcp_server.py`(読み取り専用アクセサ追加のみ)、`apps/api/app/main.py:166`。
- **変更してはいけない境界**: MCP プロトコル応答(tools/list 等)・ツール登録ロジック・CLI `mcp` サブコマンドの出力を変えない。
- **実装手順**: `mcp_server` に `tool_count`(または同等の読み取り専用プロパティ)を追加 → `main.py:166` を置換。
- **挙動を固定するテスト**: 既存 `test_mcp_server.py`。
- **受け入れ条件**: 起動ログに従来と同じツール数が出る / `pytest app/tests/test_mcp_server.py` とフルスイートに新規失敗なし。
- **検証コマンド**: 8.1 + 8.6(起動スモーク)。
- **停止条件**: プロトコル応答の形状変更が必要になったとき。

### REQ-4: get_session の手動消費 7 箇所を async_session_factory に置換(D2)

- **目的 / 解消する問題**: DI 用 generator の `async for ... break` 消費を正規のコンテキストマネージャに置き換え、セッション寿命を明確にする。
- **変更してよいファイル**: `apps/api/app/orchestration/executor.py`(`:678` 周辺の 1 箇所)、`apps/api/app/integrations/mcp_server.py`(`:438, 479, 515, 563, 656, 691` の 6 箇所)。
- **変更してはいけない境界**: `core/database.py` の `get_session` 自体は変更しない(FastAPI 依存として現役)。commit を追加・削除しない。例外処理・ログ・戻り値を変えない。
- **実装手順**: 1 箇所ずつ: (a) 変換前にそのブロックの commit 有無と例外処理を読んで記録 → (b) `async for db in get_session(): ... break` を `async with async_session_factory() as db:` に書き換え(インデント調整以外のロジック変更なし)→ (c) 対応テストを実行。7 箇所すべて完了後に 1 コミット(または 2 ファイルで 2 コミット)。
- **挙動を固定するテスト**: 既存 `test_mcp_server.py` ほか MCP/オーケストレーション系テスト。
- **受け入れ条件**: 7 箇所すべて変換済み / `grep -rn "async for db in get_session" app/ | grep -v tests` が 0 件 / 対象テストとフルスイートに新規失敗なし。
- **検証コマンド**: 8.1 + `pytest app/tests/test_mcp_server.py -q`。
- **停止条件**: commit されていない書き込みパスの扱いに迷ったとき(Stop And Ask 5 — 現状維持のまま変換し、報告する)。

### REQ-5: エンドポイントカウントスクリプトの追加(D8)

- **目的 / 解消する問題**: ドキュメント数値主張(432 endpoints / 53 modules)の検証手段を固定化し、アドホックな数え直しをなくす。
- **変更してよいファイル**: `scripts/count-endpoints.py`(新規のみ)。
- **変更してはいけない境界**: README / CLAUDE.md 等の数値は変更しない(現在の実測と一致しているため)。既存スクリプトを変更しない。
- **実装手順**: 8.2 のカウント方法(routes/*.py の `@router.get|post|put|patch|delete` デコレータ数、`__init__.py` を除いたモジュール数)を実装し、docstring に定義を明記。依存は標準ライブラリのみ。
- **挙動を固定するテスト**: スクリプト実行で `432` / `53` が出力されること(現 HEAD 時点)。
- **受け入れ条件**: 出力が README:212 の主張と一致 / tracked file への変更が本スクリプト追加のみ / ruff クリーン。
- **検証コマンド**: `python3 scripts/count-endpoints.py` + 8.1。
- **停止条件**: 実測がドキュメントとズレていた場合(数値を書き換えず報告して停止)。

---

## Recommended Follow-ups

Required 完了後に**別途判断**する(今回は実装しない)。

1. **D4**: `multi_model.py` の Pydantic モデルを `app/schemas/multi_model.py` へ抽出(OpenAPI diff ゼロ必須。他ルートへの水平展開はさらに別判断)。
2. **D6**: `cli.py` の分割。**先に** `build_parser()` の characterization テスト(`app/tests/test_cli_parser.py`)を追加し green を確認してから、`app/cli/` パッケージへ段階分割(`app.cli:main` パス維持、pyproject 変更が必要になったら停止)。

---

## Proposal-only Items

承認・仕様判断・追加調査が必要。**勝手に実装してはいけない。**

| 項目 | 内容 | 必要な判断(Open Question) |
|---|---|---|
| D5 | インメモリストア群の永続化 | Q1: v0.2 で永続化するか? 対象はどれか? |
| D7 | ミドルウェア + ルート個別ガードの二重サニタイズ整理 | Q2: 意図した多層防御か?(回答まで両方維持) |
| D9 | repositories/ 層の拡大 or 凍結 | Q4: どちらの方針か?(回答後も、まず方針文書化のみ) |
| D13 | フロントエンド巨大ページの分割 | vitest 安全網の整備方針 |
| D14 | i18n 辞書のデータファイル化 | 起動経路への影響評価 |
| D15 | docs/zh と docs/zh-CN の分担整理 | Q5: 現状の分担は意図通りか? |
| (D8 関連) | エンドポイント数の正準定義に WS/health/A2A を含めるか | Q3(REQ-5 は現行実測と一致する定義で実装可能なため、回答を待たない) |

これらの Open Question は **Required Scope の内容・受け入れ条件を変えない**(質問対象の作業をすべて Proposal Only に隔離済み)。そのため実装開始をブロックしない。

---

## Implementation Phases

該当しないフェーズは省略済み。**大きな設計変更(D5/D7/D9 等)はどのフェーズにも含まれない。**

- **Phase 0 — 状態確認と baseline**(コード変更なし): `git status --short` 記録 → 使い捨て .venv 構築 → ruff / pytest フルスイート / OpenAPI スナップショット / エンドポイントカウントを記録(Baseline Commands And Results 参照)。`pytest --collect-only -q app/tests/zeo_bench.py` で bench が非収集であることも確認。baseline 失敗があれば停止・報告。
- **Phase 1 — 安全網の追加**(挙動変更なし): REQ-1 の前提となる `brainstorm_sessions` create_all テストを追加し、green を確認。
- **Phase 2 — 明らかに安全な整理**(各 1 コミット): REQ-1 → REQ-2 → REQ-3。各コミット後に 8.1、ルート/モデルに応じて 8.3 / 8.4。
- **Phase 3 — セッション取得の正常化**: REQ-4 を 1 箇所ずつ(手順は REQ-4 参照)。完了後 8.1 + 対象テスト。
- **Phase 4 — カウントスクリプト追加**: REQ-5。実行結果がドキュメント数値と一致することを確認。
- **Phase 5 — 全体検証**: baseline 相当(ruff + フルスイート + OpenAPI diff + エンドポイント数)を再実行し、Reporting Format で報告。

---

## Verification Requirements

各検証が**何を保証するか**を含めて実施する。存在しないコマンドを追加発明しない。

### 8.1 毎フェーズ必須 — 静的検証 + 回帰検知

```bash
cd apps/api
.venv/bin/ruff check app/ && .venv/bin/ruff format --check app/   # lint/format 回帰なし
.venv/bin/python -m pytest app/tests/ -q                          # フルスイート(baseline 比較)
```

保証: 変更が既存テストで検知可能な回帰を起こしていない。baseline との passed/failed 差分を必ず記録。

### 8.2 エンドポイント数の不変確認(ルートを触ったフェーズ + 最終)

```bash
python3 - <<'EOF'
import re, glob
files = glob.glob('apps/api/app/api/routes/*.py')
n = sum(len(re.findall(r'@router\.(get|post|put|patch|delete)\(', open(f).read())) for f in files)
print('REST endpoints:', n)   # 432 のままであること
EOF
```

保証: ルートの追加・削除が起きていない。

### 8.3 モデル/スキーマ整合(REQ-1 後 — CI と同一の保証)

```bash
cd apps/api && .venv/bin/python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
import app.models
async def check():
    engine = create_async_engine('sqlite+aiosqlite://')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('OK')
asyncio.run(check())"
```

保証: `import app.models` だけで全テーブル(`brainstorm_sessions` 含む)が create_all できる。REQ-1 の目的そのもの。

### 8.4 OpenAPI 差分ゼロ確認(REQ-1 / REQ-2 後 + 最終)

```bash
cd apps/api && SECRET_KEY=demo-key .venv/bin/python -c "
import json
from app.main import app
print(json.dumps(app.openapi(), sort_keys=True))" > /tmp/openapi-after.json
diff /tmp/openapi-before.json /tmp/openapi-after.json   # 空であること
```

保証: 公開 API 契約(パス・メソッド・スキーマ・security scheme)が不変。

### 8.5 変換完了の確認(REQ-4 後)

```bash
grep -rn "async for db in get_session" apps/api/app/ | grep -v tests   # 0 件であること
```

### 8.6 サーバー起動スモーク(Phase 2 / 3 の後 — 実行環境がある場合)

```bash
cd apps/api && PYTHONPATH=. SECRET_KEY=demo-key DATABASE_URL=sqlite+aiosqlite:///./smoke.db \
  timeout 15 .venv/bin/python -m uvicorn app.main:app --port 18234 &
sleep 8 && curl -sf localhost:18234/healthz && \
  curl -s -X POST localhost:18234/api/v1/auth/anonymous-session | head -c 200
# 終了後: smoke.db を削除(untracked の一時ファイル)
```

保証: lifespan(create_all + MCP 初期化ログ含む)が正常に完走する。REQ-3 のログ出力もここで目視確認。実行できない場合は「未実行 + 理由」を報告に含める。

---

## Definition of Done

以下すべてを満たしたときのみ完了とする:

1. REQ-1〜REQ-5 がすべて各自の受け入れ条件を満たしている。
2. Behaviors To Preserve に回帰がない(特に OpenAPI diff ゼロ、`grep` による変換完了確認、create_all 整合)。
3. 新しいテスト失敗・型エラー・lint エラー・build 失敗を導入していない(8.1 が baseline と同等以上)。
4. baseline に既存失敗があった場合、その差分を説明できる(既存失敗を「直した」ことにしない)。
5. Required Scope 外の変更がない(`git diff --stat` が REQ の許可ファイル + 新規テスト/スクリプトのみ)。
6. 未解決事項と残存リスクが報告されている。
7. 実行したすべての検証コマンドと結果が報告されている(未実行のものは理由付き)。

---

## Reporting Format

作業完了時(または中断時)に以下の 8 項目を報告すること:

1. **実装した Debt ID と要約**(REQ-1〜5 それぞれの実施結果)
2. **変更したファイルと理由**
3. **保持した重要挙動**(Behaviors To Preserve のうち検証で確認したもの)
4. **実行したコマンド・終了結果・baseline との差**(テスト: before X passed / after X' passed、ruff、OpenAPI diff、エンドポイント数 432 → N)
5. **実行できなかった検証と理由**(例: 起動スモーク不可の環境)
6. **Required から除外・中断した項目**(該当した Stop And Ask 条件)
7. **残存リスクと追加質問**(発見したが直していない問題は `ファイル:行` で列挙)
8. **作業終了時の `git status --short`**

---

## Out-of-scope Items

- D5(インメモリ永続化)、D7(二重サニタイズ整理)、D9(repositories 方針)、D13(フロントエンド分割)、D14(i18n データ化)、D15(docs/zh 整理)の**実装**。
- D4(multi_model スキーマ抽出)、D6(cli.py 分割)— Recommended であり今回は実装しない。
- `apps/desktop` / `apps/edge` / `plugins/` / `skills/` / `extensions/` / `packages/` の変更。
- バージョン番号の変更、`pyproject.toml`(root / apps/api)の変更、依存パッケージの追加・更新(検証用の使い捨て .venv への導入を除く)。
- 翻訳済みドキュメントの更新、README 等の数値変更。
- セキュリティモジュール(`app/security/`)の挙動変更。
- 計測なしのパフォーマンス最適化。
- 「全部きれいにする」類の網羅的リライト。**本書に列挙された Required 5 件のみが実装対象である。**
