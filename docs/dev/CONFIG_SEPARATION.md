# Configuration Separation Guide: Developer vs User

> Zero-Employee Orchestrator (ZEO) の設定項目を「開発者が設定すべきもの」と「使用ユーザーが設定するもの」に明確に分離するガイド。
>
> Last updated: 2026-03-30

---

## ZEO の設定方針（前提）

ZEO は以下の設計原則に基づいて設定体系を構築している：

1. **API キー不要で開始可能** — g4f（サブスクリプション）、Ollama（ローカル）で即座に利用可能
2. **特定のプロバイダーを推奨しない** — 全選択肢を平等に提示
3. **ZEO 自体は無料** — LLM API コストはユーザーが各プロバイダーに直接支払う
4. **セキュリティファースト** — デフォルトは LOCKDOWN/STRICT、ユーザーが明示的に拡張
5. **オフライン完全動作保証** — Ollama + SQLite で全コア機能が動作
6. **設定ゼロで使える機能が多い** — Design Interview、Judge Layer、承認フロー等は設定不要

### 設定の責任分界点

- **DEVELOPER_SETUP.md** の対象: ZEO コアの開発・品質管理（Sentry、Red-team テスト）
- **USER_SETUP.md** の対象: それ以外すべて（セキュリティ、DB、デプロイ、API キー、ワークスペース等）

---

## 1. 開発者（Developer）が設定する項目

> ZEO のコードベースを開発・保守・リリースする担当者が設定する項目。
> 使用ユーザーは触る必要がない。

### 1.1 CI/CD — GitHub Repository Secrets

| シークレット | 用途 | 使用ワークフロー | 状態 |
|---|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | AI コードレビュー・タスク自動化 | `claude.yml`, `claude-code-review.yml` | 必要 |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Workers デプロイ | `deploy-workers.yml` | Edge 使用時のみ |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers 認証 | `deploy-workers.yml` | Edge 使用時のみ |
| `TAURI_SIGNING_PRIVATE_KEY` | デスクトップアプリ署名 | `release.yml` | リリース時必要 |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | 署名キーパスワード | `release.yml` | リリース時必要 |
| `SENTRY_DSN` | エラー監視（開発チーム用） | `ci.yml`, `deploy-api.yml` | 任意 |
| `SECRET_KEY` | デプロイ時の暗号化キー | `deploy-api.yml` | デプロイ時必要 |

### 1.2 本番デプロイ設定

| 設定項目 | デフォルト | 本番での対応 |
|---|---|---|
| `SECRET_KEY` | 自動生成（揮発性） | 固定の強力なキーに変更必須 |
| `DEBUG` | `true` | `false` に変更必須 |
| `CORS_ORIGINS` | localhost 系 | 本番ドメインに変更必須 |
| `DATABASE_URL` | SQLite | PostgreSQL 推奨 |
| `JWT_SECRET` (Workers) | 未設定 | `wrangler secret put` で設定 |

### 1.3 品質管理

| 設定項目 | 目的 | 対象 |
|---|---|---|
| `SENTRY_DSN` | ZEO 自体のバグ追跡・エラー監視 | 開発チームのみ |
| Red-team テスト | ZEO の脆弱性検証 | リリース前後に実行 |
| `scripts/security-check.sh` | セキュリティチェック | デプロイ前に実行 |

### 1.4 リリース・配布

| 設定項目 | 目的 | 備考 |
|---|---|---|
| Tauri 署名キー | デスクトップアプリのコード署名 | minisign 公開鍵は `tauri.conf.json` に埋め込み済み |
| PyPI 公開 | `pip install zero-employee-orchestrator` | OIDC 認証で自動化済み |
| Cloudflare Workers | Edge デプロイ | 任意（D1/KV は設定済み） |

---

## 2. ユーザー（User）が設定する項目

> ZEO を使用するエンドユーザーが、必要に応じて設定する項目。
> 設定方法: UI（Settings ページ）、CLI（`zero-employee config set`）、REST API

### 2.1 設定不要で使える機能

以下は設定ゼロで動作する（USER_SETUP.md Section 14 参照）：

- Design Interview（ブレインストーミング・要件探索）
- Task Orchestrator（DAG 分解・進捗管理）
- Judge Layer（品質検証）
- Self-Healing DAG（自動リプランニング）
- Experience Memory / Failure Taxonomy
- 承認フロー・監査ログ
- PII 自動検出・マスキング
- プロンプトインジェクション防御
- ファイルサンドボックス

### 2.2 LLM プロバイダー

| 設定項目 | デフォルト | 必須度 |
|---|---|---|
| `DEFAULT_EXECUTION_MODE` | `quality` | 任意（変更可） |
| `USE_G4F` | `true` | 任意（キー不要モード） |
| 各プロバイダー API キー | 空（不要） | 任意（品質向上時） |
| `OLLAMA_BASE_URL` | `localhost:11434` | Ollama 使用時 |
| `OLLAMA_DEFAULT_MODEL` | 自動検出 | 任意 |

### 2.3 言語

| 設定項目 | デフォルト | 備考 |
|---|---|---|
| `LANGUAGE` | `en` | UI + AI エージェント出力言語 |

### 2.4 セキュリティ（ユーザー制御）

| 設定項目 | デフォルト | 備考 |
|---|---|---|
| サンドボックスレベル | STRICT | ユーザーが緩和可能 |
| データ転送ポリシー | LOCKDOWN | ユーザーが緩和可能 |
| PII 自動検出 | 有効 | 無効化可能 |
| ワークスペースアクセス | 内部ストレージのみ | ローカル/クラウド有効化可能 |

### 2.5 エージェント動作

| 設定項目 | デフォルト | 備考 |
|---|---|---|
| 自律レベル | semi_auto | observe/assist/semi_auto/autonomous |
| 予算上限 | なし | 日次/週次/月次で設定可能 |
| 承認ポリシー | 危険操作は承認必須 | カスタマイズ可能 |

### 2.6 外部連携（すべて任意）

| カテゴリ | 例 | 備考 |
|---|---|---|
| コミュニケーション | Slack, Discord, LINE | ユーザーが接続設定 |
| プロジェクト管理 | Jira, Linear, Asana | ユーザーが接続設定 |
| ナレッジ | Notion, Obsidian | ユーザーが接続設定 |
| メディア生成 | Stability AI, ElevenLabs | API キーをユーザーが設定 |
| クラウドストレージ | Google Drive, OneDrive | OAuth 認証 |

### 2.7 テーマ・UI

| 設定項目 | デフォルト | 備考 |
|---|---|---|
| テーマ | ダーク | ダーク/ライト/ハイコントラスト |
| 会社名・ミッション | 空 | 任意 |

---

## 3. 現状の Repository Secrets 監査

スクリーンショット（2026-03-30 確認）に基づく現在のシークレット一覧：

| シークレット | 状態 | 判定 |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | `claude.yml`, `claude-code-review.yml` で使用 | **適切** |
| `CLOUDFLARE_ACCOUNT_ID` | `deploy-workers.yml` で使用 | **適切** |
| `CLOUDFLARE_API_TOKEN` | `deploy-workers.yml` で使用 | **適切** |
| `PYPI_API_TOKEN` | **どのワークフローでも未使用** | **削除推奨** |
| `SENTRY_DSN` | `ci.yml`, `deploy-api.yml` で使用 | **適切**（開発チーム用） |
| `TAURI_SIGNING_PRIVATE_KEY` | `release.yml` で使用 | **適切** |

---

## 4. 注意点・改善提案

### 4.1 PYPI_API_TOKEN — ワークフロー未使用だが手動バックアップとして保持可

**現状**: `PYPI_API_TOKEN` が Repository Secrets に登録されているが、`publish-pypi.yml` は
OIDC (Trusted Publisher) 認証を使用しており、このトークンはワークフロー内で参照されていない。

```yaml
# publish-pypi.yml — OIDC 認証を使用
permissions:
  id-token: write  # ← OIDC トークン自動生成
steps:
  - uses: pypa/gh-action-pypi-publish@release/v1  # ← トークン不要
```

ZEO は PyPI に公開済み（`pip install zero-employee-orchestrator`）であり、
OIDC Trusted Publisher が正常に機能している限りトークンは不要。

**対応（選択肢）**:
- **削除**: 不要なシークレットの放置はセキュリティリスク（攻撃面拡大）
- **保持**: `twine upload` による手動アップロードのバックアップとして残す

---

### 4.2 TAURI_SIGNING_PRIVATE_KEY_PASSWORD — パスワードなしで登録済み、対応不要

**現状**: `release.yml` で `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` を参照しているが、
署名キーはパスワードなしで登録されている。

```yaml
# release.yml line 76
TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY_PASSWORD }}
```

**判定**: Tauri のアクションはパスワードが空でもエラーにならない。
パスワードなしの署名キーであるため、現状で問題なし。

**任意対応**: `release.yml` から該当行を削除して意図を明確化することも可能だが、
将来パスワード付きキーに変更する可能性を考慮し、残しておいてもよい。

---

### 4.3 SECURITY_SETUP_CHECKLIST.md に不整合

**現状**: チェックリストに以下の記載がある：

```markdown
- [ ] Replace KV namespace `placeholder-id` with your actual value
- [ ] Replace D1 `database_id` `placeholder-id` with your actual value
```

しかし実際の `wrangler.toml` では：
- D1 database_id: `04e8c22d-10c5-442f-bc43-5b2f2ac0ae99`（実 ID 設定済み）
- KV namespace_id: `21e5ccb52e034b4ead2781a3f0445783`（実 ID 設定済み）

**対応**: `SECURITY_SETUP_CHECKLIST.md` のチェック項目を更新し、
実 ID が設定済みであることを反映する（チェック済みにするか、項目を修正）。

---

### 4.4 Google OAuth — ユーザー設定（現在は未実装）

**現状**: `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` は `config_manager.py` で
ユーザー設定可能（CONFIGURABLE_KEYS）として定義されている。
`USER_SETUP.md` にはユーザー自身が Google Cloud Console で OAuth アプリを作成し、
CLI で設定する手順が記載されている：

```bash
zero-employee config set GOOGLE_CLIENT_ID <client-id>
zero-employee config set GOOGLE_CLIENT_SECRET <client-secret>
```

**ただし**: `auth.py` の Google OAuth エンドポイントは現在 501 (Not Implemented) を返す。

```python
@router.get("/google/authorize")
async def google_authorize():
    raise HTTPException(status_code=501, detail="Google OAuth is not yet available.")
```

**判定**: 設計上はユーザー設定の方針であり、ZEO の「特定プロバイダーを推奨しない」原則に合致する。
OAuth の実装完了時に、ユーザーが各自の Google Cloud プロジェクトで OAuth アプリを作成する
フローを `USER_SETUP.md` に沿って案内すればよい。

---

### 4.5 デプロイ用シークレット — デプロイ方式に応じて追加

**現状**: `deploy-api.yml` は3つのデプロイターゲットをサポートしており、
選択した方式に応じて必要なシークレットが異なる：

| デプロイ方式 | 必要なシークレット | 備考 |
|---|---|---|
| **Docker (Self-Hosted VPS)** | `SECRET_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY` | 最も柔軟 |
| **Fly.io** | `SECRET_KEY`, `FLY_API_TOKEN` | マネージド PaaS |
| **Railway** | `SECRET_KEY`, `RAILWAY_TOKEN` | マネージド PaaS |
| **共通（任意）** | `DATABASE_URL`, `CORS_ORIGINS`, `SENTRY_DSN` | 環境に応じて |

**ローカル Docker Compose**: `SECRET_KEY` のみで起動可能（最もシンプル）：

```bash
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export SECRET_KEY
docker compose up -d  # → http://localhost:18234
```

**判定**: デプロイ方式を選択してから必要なシークレットを追加する設計。
現時点で未登録は適切。

---

### 4.6 Sentry — ユーザー任意が最もコスト効率的

**現状**: Sentry は以下の3箇所で異なる扱いを受けている：

| ドキュメント | 位置づけ |
|---|---|
| `DEVELOPER_SETUP.md` | 開発チーム用（ユーザー環境ではない） |
| `FEATURE_BOUNDARY.md` | Extension に移行すべき（コアではない） |
| `config_manager.py` | ユーザー設定可能（CONFIGURABLE_KEYS に含まれる） |

**コスト面**: Sentry は無料枠があるが、本番利用では有料（$26+/月）になりうる。
`SENTRY_DSN` が空（デフォルト）の場合、ローカルイベントストア（5,000件上限、メモリ内）に
フォールバックするため、**設定しなければコストゼロ**。

**ZEO 方針との照合**: `FEATURE_BOUNDARY.md` は「承認・監査・実行制御がなくても壊れないもの
→ コアではない」と定義しており、Sentry は Extension に分類されている。
ユーザーが任意で設定する現在の設計が最もコスト効率的。

**判定**:
- `config_manager.py` の `SENTRY_DSN` は残す（開発者・ユーザー双方がランタイムで設定可能）
- Repository Secret の `SENTRY_DSN` は CI/CD での開発品質管理用として適切
- ユーザー環境では未設定（デフォルト）で運用し、必要な場合のみ有効化

---

## 5. 設定の優先順位

```
1. 環境変数              （最高優先）
   ↓
2. ランタイム設定ファイル   (~/.zero-employee/config.json)
   ↓
3. .env ファイル           (プロジェクトルート)
   ↓
4. Settings クラスデフォルト (config.py)
   ↓
5. ハードコードフォールバック （最低優先）
```

---

## 6. 設定アクセス方法

| 方法 | 対象 | 備考 |
|---|---|---|
| UI Settings ページ | ユーザー | デスクトップ/Web |
| `zero-employee config set KEY VALUE` | ユーザー/開発者 | CLI |
| `PUT /api/v1/config` | ユーザー/開発者 | REST API |
| `.env` ファイル | 開発者 | 環境変数 |
| GitHub Repository Secrets | 開発者 | CI/CD |
| `wrangler secret put` | 開発者 | Cloudflare Workers |

---

## 7. まとめ: 対応アクション一覧

| # | アクション | 重要度 | 状態 |
|---|---|---|---|
| 1 | `PYPI_API_TOKEN` — OIDC で不要。削除 or バックアップ保持を判断 | 中 | 開発者判断 |
| 2 | `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` — パスワードなし、対応不要 | — | **解決済み** |
| 3 | `SECURITY_SETUP_CHECKLIST.md` の Cloudflare ID 項目を更新 | 中 | **修正済み** |
| 4 | Google OAuth — ユーザー設定の設計で方針合致、実装完了時に案内 | 低 | 実装待ち (501) |
| 5 | Sentry — ユーザー任意（デフォルト無効）が最もコスト効率的 | — | **現状適切** |
| 6 | デプロイ用シークレット — 方式選択後に追加 | — | デプロイ時 |

---

*Zero-Employee Orchestrator -- Configuration Separation Guide*
