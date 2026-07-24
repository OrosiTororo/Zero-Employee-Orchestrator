# refactor-instructions.md — Zero-Employee Orchestrator リファクタリング指示書

> 対象リポジトリ: `OrosiTororo/Zero-Employee-Orchestrator`(v0.1.7 時点)
> 本書は分析担当モデルがコードベース全体を読み、証拠を確認した上で作成した実装指示書である。
> 実装担当モデルは本書の範囲内でのみ作業すること。**本書に書かれていない大規模な削除・全面書き換えは禁止。**

---

## 1. Objective

既存の外部挙動(API レスポンス、CLI 出力、DB スキーマ、セキュリティ保証)を一切変えずに、以下を達成する。

1. 依存方向の乱れを正す(認証依存関係がルートモジュールに置かれている問題、ORM モデルがサービス層に置かれている問題)。
2. FastAPI 依存性ジェネレータの誤用(`async for db in get_session()` の手動消費)を正しいセッション管理に置き換える。
3. 肥大化したモジュール(`multi_model.py` ルート、`cli.py`)を、既存のリファクタリング前例(`self_improvement` パッケージ分割 + 後方互換ファサード)に倣って安全に分割する。
4. 変更しないと決めた負債(インメモリストア等)を「提案」として文書化し、勝手に実装しない。

**目的はコードの見た目を綺麗にすることではない。** 既存仕様を壊さず、負債を減らし、今後変更しやすい状態にすることである。

---

## 2. Project Understanding(実装前に必ず読むこと)

### 2.1 プロダクト概要

ZEO(Zero-Employee Orchestrator)は「AI メタオーケストレーター」。CrewAI / AutoGen / LangChain / Dify / n8n などの AI フレームワークと 63+ の業務アプリを、**人間の承認ゲート・監査ログ・セキュリティ層の下に統合**する。9 層アーキテクチャ(User → Design Interview → Task Orchestrator (DAG) → Skills → Judge → Re-Propose → State & Memory → Provider (LiteLLM) → Skill Registry)。

### 2.2 コンポーネントとエントリーポイント

| コンポーネント | エントリーポイント | 備考 |
|---|---|---|
| FastAPI バックエンド | `apps/api/app/main.py` | ポート 18234。lifespan で `Base.metadata.create_all` + システムスキル登録 + 各種 best-effort 初期化 |
| CLI | `apps/api/app/cli.py` (`main()`) | console_script `zero-employee = "app.cli:main"`(root と apps/api の**両方の** `pyproject.toml` に定義) |
| デスクトップ UI | `apps/desktop/ui/src/main.tsx` | Tauri v2 + React + Vite。デザインシステム "Clarity"(`index.css` の CSS カスタムプロパティ) |
| Edge | `apps/edge/proxy`, `apps/edge/full` | Cloudflare Workers (Hono) |
| MCP サーバー | `apps/api/app/integrations/mcp_server.py` | JSON-RPC 2.0 + stdio、14 ツール |

### 2.3 バックエンドの層構造(検証済みの事実)

- `api/routes/`(53 モジュール、REST エンドポイント 432 個 — 検証済み、§8.2 のカウントコマンド参照)→ `services/`(38 ファイル)→ `models/`(ORM)。
- **サービス層は `HTTPException` を一切 raise しない**(grep で 0 件を確認)。HTTP エラー変換はルート層の責務。この規律は維持すること。
- DB セッションの正規ルートは `app/api/deps/database.py` の `get_db`(成功時 commit / 例外時 rollback)。ルート 26 ファイルが使用。
- `app/api/deps/services.py` に DI シングルトンパターン(`Depends(get_sandbox)` 等)が存在。テストで override 可能にする設計意図が docstring に明記されている。
- `repositories/` は `base` / `ticket_repository` / `audit_repository` の 3 つのみ。他のサービスは ORM を直接クエリする。**どちらに寄せるかは未決定(§6 質問 Q4)。**

### 2.4 DB スキーマ管理(3 系統が意図的に共存 — 壊すな)

1. 起動時 `Base.metadata.create_all`(`main.py` lifespan)— 新規インストール用。
2. Alembic(`apps/api/alembic/versions/` に 4 リビジョン)— 既存インストールの差分適用用。
3. `app/core/version_migration.py` — pre-Alembic 時代(v0.1.0〜v0.1.2)のインストールを引き上げる手書きの追加専用ラダー。Alembic head の stamp 処理を含み、`test_alembic_stamp.py` でテストされている。

この 3 系統の共存は `version_migration.py` の docstring に設計判断として明記されている。**リファクタリング対象ではない。**

### 2.5 セキュリティ機構(CLAUDE.md の非交渉事項)

- 外部データ → LLM: `wrap_external_data()`(`security/prompt_guard.py`)必須。
- ユーザー入力 → AI: `pii_guard.py` の PII 検査必須。
- ファイルアクセス: `sandbox.py` 経由必須。
- 危険操作: `approval_gate.py` + `autonomy_boundary.py` に登録。
- グローバルに `InputSanitizationMiddleware`(JSON ボディの prompt injection / PII スキャン)が適用され、**さらに** 16 のルートファイルが個別に `detect_and_mask_pii` / `scan_prompt_injection` を呼ぶ。この二重化は多層防御の可能性が高い(§6 質問 Q2)。**どちらも削除禁止。**

### 2.6 CI が検証していること(`.github/workflows/ci.yml`)

- root と `apps/api/` の 2 つの `pyproject.toml` のメタデータ完全同期(version / name / description / requires-python / license / dependencies / dev deps / ruff select)。
- ruff check + ruff format --check(Python 3.11 / 3.12 マトリクス)。
- pytest(カバレッジ付き)、pip-audit、Alembic モデル整合チェック、Trivy イメージスキャン、red-team セキュリティテスト(`app.security.redteam`)、フロントエンド tsc / vitest / build。

### 2.7 バージョン管理

バージョンは **8 ファイル**に分散しており、`./scripts/bump-version.sh` でのみ更新する。**本リファクタリングではバージョンを変更しない。**

---

## 3. Behaviors To Preserve(絶対に壊してはいけない挙動)

1. **全 432 REST エンドポイントのパス・メソッド・レスポンス形状**。ルート分割やスキーマ移動をしても OpenAPI 出力が変わってはならない(検証方法は §8.4)。
2. **DB スキーマ**: テーブル名・カラム名・型を一切変更しない。特に `brainstorm_sessions` テーブル(§5 D3)はクラスの移動のみでスキーマ不変。
3. **CLI の全コマンドとフラグ**: `zero-employee serve|chat|mcp|models|pull|config|local|security|db|upgrade|update` および chat 内スラッシュコマンド(`/read` `/write` `/edit` `/run` `/ls` `/cd` `/pwd` `/find` `/grep` `/ingest` `/query` `/lint` `/ralph` `/plan` ほか)。console_script `app.cli:main` のインポートパスも維持。
4. **セキュリティ層の挙動**: prompt_guard / pii_guard / sandbox / iam / approval_gate / sanitizer / security_headers / input_sanitization の入出力を変更しない。
5. **後方互換ファサード**: `app/services/self_improvement_service.py` は v0.1.7 分割の互換レイヤーとして意図的に残されている。削除禁止。
6. **i18n**: 6 言語(ja/en/zh/ko/pt/tr)の HTTP エラー翻訳(`main.py` の `i18n_http_exception_handler`)と `Accept-Language` 処理。
7. **lifespan の best-effort 初期化**: `main.py` の各 try/except ブロック(Ollama / Sentry / MCP / モデルカタログ / self-improvement スケジューラ)は「失敗しても起動する」ことが仕様。例外を伝播させる変更をしない。
8. **サービス層が HTTPException を投げない**規律。
9. **既知のインメモリ挙動**: dispatch タスク・面談セッション・アップロードファイル等が再起動で消えるのは v0.1.x の既知のトレードオフ(コード内コメントで明示)。**永続化を勝手に実装しない**(§6 質問 Q1)。

---

## 4. Non-Negotiables(作業規律)

1. **最初に `git status` を確認**し、未コミット変更があれば自分の変更と混ぜない(必要なら stash するか、そのまま報告して停止)。
2. 編集前に **baseline の検証結果を記録**する(§7 Phase 0)。baseline で既に失敗しているテストは自分の修正対象ではない — 記録して区別する。
3. 変更は**小さく戻しやすい単位**でコミットする。1 コミット = 1 つの負債項目。フェーズをまたぐコミットをしない。
4. **無関係な整形・ついでのリファクタリングをしない。** ruff format が全ファイル整形済み(検証済み)なので、触ったファイル以外に diff を発生させない。
5. **既存挙動を勝手に変えない。** 「ついでにバグらしきものを直す」場合も、まず報告して指示を仰ぐ。
6. 正しさが不明な場合は**実装を止めて質問する**(§6 の Stop And Ask 条件)。
7. **各フェーズ完了ごとに §8 の検証を実行**し、結果をコミットメッセージまたは作業ログに残す。
8. 最後に**実行したコマンドと結果を報告**する(§9 のフォーマット)。
9. バージョン番号・エンドポイント数などの**ドキュメント上の数値を検証なしに変更しない**(CLAUDE.md の Evidence-Based Changes 規則)。
10. 2 つの `pyproject.toml` は CI で同期チェックされる。片方だけ変更しない。
11. 翻訳済みドキュメント(docs/ja-JP, zh-CN, zh-TW, ko-KR, pt-BR, tr)は、本リファクタリングでは触らない(コード変更がユーザー向け機能を変えないため同期不要)。

---

## 5. Debt Map(負債マップ)

各項目: **根拠 → なぜ負債か → 影響範囲 → リスク → 改善案 → 検証 → 実装可否**。

### D1. 認証依存関係がルートモジュール内にある【実装可 — Phase 2】

- **根拠**: `get_current_user` / `get_optional_user` が `apps/api/app/api/routes/auth.py:72,560` に定義され、**53 ファイル**が `from app.api.routes.auth import get_current_user` でインポート(grep 検証済み)。一方で DI の正規置き場 `app/api/deps/`(database.py / services.py / validators.py)が既に存在する。
- **なぜ負債か**: ルートモジュールが他の全ルートの依存元になっており、依存方向が乱れている。auth.py はルート定義・OAuth インメモリ状態・共有依存関係の 3 責務を抱える。
- **影響範囲**: インポート箇所 53 ファイル(ただし互換再エクスポートで既存インポートは無変更にできる)。
- **リスク**: 低。純粋な定義の移動 + 再エクスポート。
- **改善案**: `app/api/deps/auth.py` を新設し、`get_current_user` / `get_optional_user` と、それらだけが必要とする最小限のヘルパーを移動。`app/api/routes/auth.py` は移動した名前を再インポートして re-export(`self_improvement_service.py` のファサード前例に倣う)。**既存の 53 箇所のインポートは書き換えない**(diff を最小にするため。書き換えは別途承認を得る)。
- **検証**: `pytest app/tests/`(特に `test_auth.py`, `test_auth_service.py`, `test_security_integration.py`)+ §8.4 の OpenAPI 差分ゼロ確認。
- **実装可否**: **実装してよい。**

### D2. FastAPI 依存性ジェネレータの手動消費【実装可 — Phase 3】

- **根拠**: `app/core/database.py:65` の `get_session`(FastAPI 依存用 async generator)を、`app/orchestration/executor.py:675-678`(`async for db in get_session(): ... break` パターン)と `app/integrations/mcp_server.py:434,473,511,558,653,687` の計 7 箇所が手動消費している。
- **なぜ負債か**: 依存性注入用ジェネレータの `async for ... break` 消費は、finally 節の実行タイミングが不明瞭でエラーハンドリングも脆い。正規の手段 `async_session_factory()`(コンテキストマネージャ)が同じモジュールにある。
- **影響範囲**: executor の失敗記録パス、MCP ツール 6 個の DB アクセス。
- **リスク**: 中。`get_session` は **auto-commit しない**ため、各呼び出し箇所が明示的に `commit()` しているかを**変換前に 1 箇所ずつ読んで確認**する必要がある。commit していない箇所があれば、それは「commit されないまま動いていた」既存挙動なので、**勝手に commit を追加せず報告する**。
- **改善案**: 各箇所を `async with async_session_factory() as db:` に書き換え。トランザクション境界(commit の有無)は現状と完全に同一に保つ。
- **検証**: `pytest app/tests/test_mcp_server.py app/tests/test_chaos_dag.py app/tests/test_e2e_ticket_execution.py` + フルスイート。
- **実装可否**: **実装してよい**(ただし commit 挙動の同一性を書面で確認してから)。

### D3. ORM モデルがサービス層に定義されている【実装可 — Phase 2】

- **根拠**: `BrainstormSessionRecord`(`__tablename__ = "brainstorm_sessions"`)が `app/services/multi_model_service.py:128` に定義され、`main.py:111` が create_all のために特別インポートしている(`from app.services.multi_model_service import BrainstormSessionRecord  # noqa: F401`)。他の全 ORM モデルは `app/models/` にある。
- **なぜ負債か**: モデル登録の一貫性が壊れており、`import app.models` だけでは全テーブルが揃わない。CI の Alembic 整合チェックも `app.models` インポートに依存している(ci.yml:157)。
- **影響範囲**: multi_model サービス/ルート、main.py、conftest.py。
- **リスク**: 低。クラス移動 + 再エクスポート。**テーブル名・カラムは一切変更しない。**
- **改善案**: `app/models/brainstorm.py` を新設してクラスを移動し、`app/models/__init__.py` に登録。`app/services/multi_model_service.py` で `from app.models.brainstorm import BrainstormSessionRecord` を re-export(既存インポート互換)。その後 `main.py:110-111` の特別インポートを `import app.models` のみに簡素化。
- **検証**: CI と同じ Alembic 整合チェック(§8.3)+ `pytest app/tests/`。SQLite ファイルで `create_all` 後に `brainstorm_sessions` テーブルが存在することを確認。
- **実装可否**: **実装してよい。**

### D4. 巨大ルートモジュール(multi_model.py 1,245 行)【実装可・範囲限定 — Phase 4】

- **根拠**: `app/api/routes/multi_model.py` は 1,245 行で、20+ の Pydantic リクエスト/レスポンスモデルとハンドラが同居。ルート全体ではインライン Pydantic モデルが 449 クラス(grep 検証済み)ある一方、`app/schemas/` ディレクトリ(22 ファイル)という正規置き場が存在する。
- **なぜ負債か**: スキーマの置き場が 2 系統あり、どこを見れば契約が分かるかが不明確。1,245 行のモジュールはレビューと変更が難しい。
- **影響範囲**: multi_model ルートとそのテスト。
- **リスク**: 低〜中(機械的な移動だが diff が大きい)。
- **改善案**: `app/schemas/multi_model.py` を新設し、`multi_model.py` 内の Pydantic モデル(BaseModel 継承クラス)のみを移動。ルート側はインポートに置き換える。**ハンドラのロジックは 1 文字も変えない。** 他のルートファイルへの水平展開は今回はしない(diff 膨張を防ぐ)。
- **検証**: §8.4 の OpenAPI 差分ゼロ確認(スキーマ移動で `openapi.json` が変わらないこと)+ フルスイート。
- **実装可否**: **multi_model.py のみ実装してよい。** 他ファイルへの展開は提案に留める。

### D5. ルートモジュール内のインメモリ状態【実装禁止 — 提案のみ】

- **根拠**(すべて grep 検証済み):
  - `app/api/routes/dispatch.py:36` `_dispatch_tasks` / `:549` `_scheduled_tasks`(+ `threading.Lock`)
  - `app/api/routes/tickets.py:35` `_interview_sessions`(コメント「production: persist in DB」)
  - `app/api/routes/file_upload.py:91` `_file_store`(アップロードファイルの**中身をメモリ保持**)
  - `app/api/routes/themes.py:22` `_custom_themes`
  - `app/api/routes/auth.py:132` `_google_oauth_pending`
  - `app/security/iam.py:340` `_custom_role_policies`
  - `app/api/routes/self_improvement.py:60` `_stats`
- **なぜ負債か**: 再起動でデータ消失、マルチワーカー構成で不整合。ただしコード内コメントが示す通り**既知の設計トレードオフ**であり、単一プロセス前提の現行 v0.1.x では動作している。
- **影響範囲**: 永続化するなら DB スキーマ追加・マイグレーション・API 挙動変化(再起動後もタスクが残る)を伴う。
- **リスク**: 高(スキーマ・保存データ・互換性に影響)。
- **改善案**: 永続化の要否と対象はプロダクト判断(§6 Q1)。承認が出るまで**現状維持**。
- **実装可否**: **実装禁止。** 質問への回答後に別タスクとして設計する。

### D6. cli.py の 2,268 行モノリス【実装可・安全網必須 — Phase 5】

- **根拠**: `app/cli.py` は serve / db / health / models / pull / mcp / security / config / local / chat(+ 30 以上のスラッシュコマンドハンドラ)/ upgrade / update / パーサ構築のすべてを 1 ファイルに持つ。専用のユニットテストは存在しない(`app/tests/` に test_cli* なし — 検証済み)。
- **なぜ負債か**: 変更の影響範囲が読めず、chat 系ヘルパー(`_cli_*` 30 関数)とサーバー運用系コマンドが同居している。
- **影響範囲**: console_script エントリーポイント(2 つの pyproject.toml)、README / USER_SETUP のコマンド例。
- **リスク**: 中。テストがないため回帰に気づけない。
- **改善案**:
  1. **先に安全網**: `app/tests/test_cli_parser.py` を新設し、`build_parser()` が受理する全サブコマンド・主要フラグの characterization テスト、および `_handle_command` のスラッシュコマンド分岐(ネットワーク不要のもの)のテストを書く。
  2. その後 `app/cli/` パッケージへ分割(例: `app/cli/__init__.py` が `main` と `build_parser` を re-export、`app/cli/chat.py`、`app/cli/serve.py`、`app/cli/mcp.py` 等)。`app.cli:main` というインポートパスは**維持必須**(パッケージ化すれば `app/cli/__init__.py` の `main` で満たせる)。pyproject.toml の変更は不要のはず — 変更が必要になった場合は停止して報告。
  3. 機能互換で足りる(--help の文字列一致までは要求しない)。ただしコマンド名・フラグ名・デフォルト値は不変。
- **検証**: 新設テスト + `zero-employee --help` / `zero-employee mcp info` の手動スモーク(§8.5)。
- **実装可否**: **安全網テストを先に書いた場合のみ実装してよい。** テストなしの分割は禁止。

### D7. ミドルウェアとルート個別のガード呼び出しの二重化【実装禁止 — 現状維持】

- **根拠**: `InputSanitizationMiddleware`(main.py:242 で全 JSON POST に適用)がプロンプトインジェクション/PII をスキャンし、さらに 16 ルートファイルが個別に `detect_and_mask_pii` / `scan_prompt_injection` を呼ぶ。
- **なぜ負債か(かもしれないか)**: 二重スキャンは CPU コストと保守の二重化。ただし**意図的な多層防御である可能性が高く**、コードからは判断できない。
- **実装可否**: **実装禁止。** §6 Q2 の回答があるまでどちらの層も変更しない。セキュリティの「簡素化」は本書のスコープ外。

### D8. ドキュメント数値主張の手動メンテナンス【実装可・軽量 — Phase 6】

- **根拠**: README.md:212 等が「53 route modules / 432 endpoints」を主張。分析時点でこの数値は**正確**(routes/*.py の `@router.<method>` デコレータ数 = 432、モジュール数 = 53 を検証済み)。ただし数え方はどこにも文書化されていない。
- **なぜ負債か**: CLAUDE.md が「数値主張は検証必須」と定める一方、検証コマンドが定義されておらず、毎回アドホックに数えることになる。
- **改善案**: `scripts/count-endpoints.py`(または .sh)を追加し、§8.2 のカウント方法を固定化する。ドキュメントの数値自体は現時点で正しいため**変更しない**。
- **リスク**: 極小(新規スクリプト追加のみ)。
- **実装可否**: **実装してよい。** ただし WS・health をどう数えるかの正準定義は §6 Q3 で確認し、回答が来るまでは「routes/*.py の @router REST デコレータ数」という現行実測と一致する定義でスクリプトを書き、docstring にその定義を明記する。

### D9. repositories/ 層の中途半端な抽象化【実装禁止 — 提案のみ】

- **根拠**: `app/repositories/` は base / ticket / audit の 3 ファイル 193 行のみ。他 30+ サービスは ORM 直接クエリ。
- **なぜ負債か**: データアクセスパターンが 2 系統あり、新規コードがどちらに従うべきか不明。
- **実装可否**: **実装禁止。** 拡大(全サービスをリポジトリ経由に)か凍結(レガシーと明記して新規はサービス直クエリ)かは設計判断(§6 Q4)。回答後も、まずは CONTRIBUTING などへの方針記載のみを行うこと。

### D10. その他の軽微な項目

| 項目 | 根拠 | 対応 |
|---|---|---|
| `main.py:166` が `mcp_server._tools` という私有属性にアクセス | 読取のみ | Phase 2 で `mcp_server` に公開プロパティ(例 `tool_count`)を追加し main.py を置換。**実装可** |
| `threading.Lock` が async コード内で使用(dispatch.py, file_upload.py, model_registry.py) | クリティカルセクション内に await がなければ実害なし | **現状維持。** D5 の永続化判断と一緒に扱う |
| `app/tests/zeo_bench.py` はテストでなくベンチ | tests/ 配下の命名慣習の乱れ | **現状維持**(pytest の収集対象になっていないか Phase 0 で確認のみ) |
| フロントエンドの巨大ページ(ReleasesPage 918 行、SettingsPage 840 行、SetupPage 824 行) | `apps/desktop/ui/src/pages/` | **提案のみ。** 本リファクタリングは backend 優先。vitest カバレッジが薄いため安全網なしで触らない |
| `docs/zh/`(深掘り docs)と `docs/zh-CN/`(README+CHANGELOG)の分担 | MD_FILES_INDEX.md:115 | **現状維持**(§6 Q5) |
| i18n 翻訳テーブル 861 行がコード内インライン辞書 | `app/core/i18n.py` | **提案のみ**(データファイル化は CLI 起動経路に影響するため今回は触らない) |

---

## 6. Stop And Ask Conditions(実装を止めて質問する条件)

以下のいずれかに該当したら、**実装を中断し、状況と選択肢を報告して指示を待つこと**:

1. 変更が **DB スキーマ、保存済みデータ、公開 API の形状**に影響し得ると気づいたとき。
2. **テストと実装が矛盾**しているとき(どちらが正か勝手に決めない)。
3. 削除候補コードが本当に不要か確信できないとき(re-export ファサードは意図的な互換レイヤーである — 削除禁止)。
4. **認証・課金・通知・外部連携**(OAuth、SSO、Sentry、app_connector、MCP、A2A)に触れる必要が生じたとき。
5. D2 の変換で「commit されていない書き込みパス」を発見したとき(勝手に commit を足さない)。
6. cli.py 分割で `pyproject.toml` の変更が必要になったとき。
7. baseline で失敗するテストを発見したとき(自分の変更と無関係でも報告)。
8. 本書に列挙されていない大きな負債を発見し、直したくなったとき(提案として報告し、承認なしに着手しない)。

### 実装前に人間へ確認済みであるべき質問(未回答なら該当フェーズをスキップ)

- **Q1**: インメモリストア(D5)の永続化は v0.2 でやるのか? 対象はどれか?(→ 回答まで D5 は現状維持)
- **Q2**: ミドルウェア + ルート個別ガードの二重スキャン(D7)は意図した多層防御か?(→ 回答まで両方維持)
- **Q3**: 「432 endpoints」の正準的な数え方に WS / health / A2A を含めるか?(→ 回答まで現行実測と一致する定義で D8 を実装)
- **Q4**: repositories/ 層(D9)は拡大か凍結か?(→ 回答まで何もしない)
- **Q5**: `docs/zh/` と `docs/zh-CN/` の分担は意図通りか?(→ 回答まで何もしない)

---

## 7. Implementation Phases(この順番で実施)

### Phase 0 — 現状確認と baseline 記録(コード変更なし)

```bash
git status                     # 未コミット変更がないことを確認。あれば停止して報告
git log --oneline -5
cd apps/api
python -m venv .venv && .venv/bin/pip install -e . pytest pytest-asyncio httpx ruff
.venv/bin/ruff check app/ && .venv/bin/ruff format --check app/
.venv/bin/python -m pytest app/tests/ -q          # 全結果を記録(所要 数分)
```

- 分析時点(2026-07-24, commit `de23344`)の baseline: `ruff check` クリーン、`ruff format --check` 297 files formatted、フルスイート **907 passed / 0 failed(約 6 分)**。テスト終了時に litellm のクリーンアップ由来の "Logging error" ノイズが出るが無害(conftest.py に説明あり)。フルスイートの結果は必ず自分でも取り直して記録すること。
- `pytest --collect-only -q app/tests/zeo_bench.py` で bench が収集されないことも確認。

### Phase 1 — 安全網の追加(挙動変更なし、テスト追加のみ)

1. `app/tests/test_cli_parser.py` 新設: `build_parser()` の全サブコマンド受理と主要フラグの characterization テスト(D6 の前提)。
2. `brainstorm_sessions` テーブルが create_all で生成されることのテスト(D3 の移動前に現行挙動を固定)。既存の Alembic 整合チェック(§8.3)相当を pytest 化してもよい。

### Phase 2 — 明らかに安全な整理(各項目 1 コミット)

1. **D3**: `BrainstormSessionRecord` を `app/models/brainstorm.py` へ移動、旧位置で re-export、`main.py:110-111` 簡素化。
2. **D1**: `get_current_user` / `get_optional_user` を `app/api/deps/auth.py` へ移動、`routes/auth.py` で re-export。既存インポート 53 箇所は書き換えない。
3. **D10-1**: `mcp_server` に公開アクセサを追加し、`main.py:166` の `_tools` 直接参照を置換。

### Phase 3 — セッション取得の正常化(D2)

7 箇所を 1 箇所ずつ: 変換前に commit 有無を確認 → `async with async_session_factory() as db:` へ書き換え → 対応テスト実行。commit 挙動は現状維持。

### Phase 4 — スキーマ抽出(D4、multi_model.py のみ)

Pydantic モデルを `app/schemas/multi_model.py` へ移動。ハンドラロジック不変。OpenAPI 差分ゼロを確認(§8.4)。

### Phase 5 — CLI 分割(D6、Phase 1 の安全網が green の場合のみ)

`app/cli.py` → `app/cli/` パッケージ。`app.cli:main` 維持。1 サブコマンド群ずつコミット。

### Phase 6 — カウントスクリプト追加(D8)

`scripts/count-endpoints.py` 新設。ドキュメントの数値は(実測と一致しているため)変更しない。

### Phase 7 — 提案書の作成(実装しない)

D5 / D7 / D9 / フロントエンド分割 / i18n データ化について、選択肢・影響・推奨を `docs/dev/REFACTOR_PROPOSALS.md` にまとめる(新規ファイル、コード変更なし)。

> **大きな設計変更(D5, D7, D9)は承認なしに実装しない。** これは本書の最重要制約である。

---

## 8. Verification Requirements(各フェーズ後に実行)

### 8.1 毎フェーズ必須

```bash
cd apps/api
.venv/bin/ruff check app/ && .venv/bin/ruff format --check app/
.venv/bin/python -m pytest app/tests/ -q
```

### 8.2 エンドポイント数の不変確認(ルートを触ったフェーズ)

```bash
python - <<'EOF'
import re, glob
n = sum(len(re.findall(r'@router\.(get|post|put|patch|delete)\(', open(f).read()))
        for f in glob.glob('apps/api/app/api/routes/*.py'))
print('REST endpoints:', n)   # 432 のままであること
EOF
```

### 8.3 モデル/スキーマ整合(モデルを触ったフェーズ — CI と同一)

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

### 8.4 OpenAPI 差分ゼロ確認(ルート/スキーマを触ったフェーズ)

変更前後で `openapi.json` を取得して diff する:

```bash
cd apps/api && SECRET_KEY=demo-key DEBUG=true .venv/bin/python -c "
import json
from app.main import app
print(json.dumps(app.openapi(), sort_keys=True))" > /tmp/openapi-after.json
# Phase 0 で同じコマンドで /tmp/openapi-before.json を採取しておき、diff が空であること
```

### 8.5 CLI スモーク(Phase 5 のみ)

```bash
cd apps/api && .venv/bin/pip install -e . && .venv/bin/zero-employee --help && .venv/bin/zero-employee mcp info
```

### 8.6 サーバー起動スモーク(Phase 2, 3 の後)

```bash
cd apps/api && PYTHONPATH=. SECRET_KEY=demo-key DATABASE_URL=sqlite+aiosqlite:///./demo.db \
  timeout 15 .venv/bin/python -m uvicorn app.main:app --port 18234 &
sleep 8 && curl -sf localhost:18234/healthz && curl -s -X POST localhost:18234/api/v1/auth/anonymous-session | head -c 200
```

---

## 9. Reporting Format(最終報告)

作業完了時(または中断時)に以下を報告すること:

```
## 実施フェーズ
- Phase N: <内容> — <コミットハッシュ> — 検証: <実行コマンドと結果(passed/failed 数)>

## Baseline との差分
- テスト: before <X passed / Y failed> → after <X' passed / Y' failed>
- ruff: before/after
- OpenAPI diff: <空 or 差分内容>
- エンドポイント数: 432 → <数>

## スキップ・中断した項目と理由
- <項目>: <理由(未回答の質問 / Stop And Ask 条件のどれに該当したか)>

## 発見した問題(修正していないもの)
- <ファイル:行> <内容>

## 最後に実行したコマンドと出力(要約)
```

---

## 10. Out-of-scope Items(今回やらないこと)

- D5(インメモリストアの永続化)、D7(ガード二重化の整理)、D9(repositories 方針)の**実装**。
- フロントエンド(apps/desktop)・Edge(apps/edge)・plugins/・skills/・extensions/ の変更。
- バージョン番号の変更、依存パッケージの追加・更新(テスト用 dev 依存を除き、それも pyproject には追加しない)。
- 翻訳済みドキュメントの更新。
- セキュリティモジュール(`app/security/`)の挙動変更。
- パフォーマンス最適化(計測なしの最適化は禁止)。
- 「全部きれいにする」類の網羅的リライト。本書に列挙された項目のみが対象である。
