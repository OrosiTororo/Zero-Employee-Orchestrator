# セキュリティポリシー

> 日本語 | [English](en/SECURITY.md) | [中文](zh/SECURITY.md)

## サポートバージョン

| バージョン | サポート状態 |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## 脆弱性の報告

セキュリティの脆弱性を発見した場合、**公開 Issue を作成しないでください**。

代わりに、[GitHub Security Advisories](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/security/advisories/new)（非公開）経由で報告してください。

48 時間以内に受領を確認し、重大な問題については 7 日以内の修正を目指します。

---

## デプロイセキュリティチェックリスト

本番環境にデプロイする（またはリポジトリを公開する）前に、以下を確認してください:

### 1. シークレットと鍵

| 項目 | 設定場所 | 生成方法 |
| --- | --- | --- |
| `SECRET_KEY` | `apps/api/.env` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_SECRET` | `wrangler secret put JWT_SECRET` | `openssl rand -base64 32` |
| `CLOUDFLARE_API_TOKEN` | GitHub リポジトリ Secrets | [Cloudflare Dashboard](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub リポジトリ Secrets | Cloudflare Dashboard サイドバー |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | `apps/api/.env`（任意） | [Google Cloud Console](https://console.cloud.google.com/) |

> `DEBUG=false` の場合、デフォルトの `SECRET_KEY` では**アプリケーションが起動を拒否**します（Python バックエンド）。また、デフォルトの `JWT_SECRET` では `503` を返します（Cloudflare Workers）。これは意図的な設計です。

### 2. ソースコードにシークレットを含めない

このリポジトリには**実際のシークレットは含まれていません**。すべての認証情報は以下で管理されています:
- 環境変数（`.env` ファイル — `.gitignore` で除外済み）
- GitHub Actions Secrets
- Cloudflare Workers Secrets（`wrangler secret put`）

### 3. デプロイワークフロー

`deploy-workers.yml` ワークフロー:
- **手動トリガーのみ**（`workflow_dispatch`）— push 時の自動デプロイなし
- `production` 環境が必要 — リポジトリ Settings で[環境保護ルール](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)（任意のレビュアー承認）を設定
- 続行前に必要な Secrets が設定されているか検証

### 4. プレースホルダー ID

以下のファイルには `placeholder-id` 値が含まれており、デプロイ前に実際のリソース ID に置き換える必要があります:

| ファイル | フィールド | リソースの作成方法 |
| --- | --- | --- |
| `apps/edge/proxy/wrangler.toml` | KV namespace `id` | `wrangler kv:namespace create RATE_LIMIT` |
| `apps/edge/full/wrangler.toml` | D1 `database_id` | `wrangler d1 create zeo-orchestrator` |

### 5. Tauri 自動アップデーター

デスクトップアプリの自動アップデーター（`apps/desktop/src-tauri/tauri.conf.json`）の `pubkey` は空です。本番ビルドを公開する前に:
```bash
npx tauri signer generate -w ~/.tauri/mykey.key
```
`tauri.conf.json` に公開鍵を設定し、秘密鍵でリリースビルドに署名してください。

### 6. CORS 設定

`.env` の `CORS_ORIGINS` を実際の本番ドメインに合わせて更新してください。デフォルト値（`localhost:3000`、`localhost:5173`）は開発用です。

### 7. データベース

- 開発環境は SQLite を使用（ローカル利用には十分）
- 本番環境は PostgreSQL を推奨: `DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname`

### 8. 認証と API セキュリティ

> **v0.1 注記**: 開発モードでは、現在の API ルートはエンドポイントごとの認証を強制していません。本番環境にデプロイする前に、すべてのエンドポイントに認証ミドルウェアを追加してください。

- [ ] すべての API エンドポイントに認証チェックを追加（FastAPI `Depends` で `get_current_user` を使用）
- [ ] WebSocket 認証を追加（接続を受け入れる前に JWT を検証）
- [ ] セキュアなパスワードハッシュのために `bcrypt` をインストール: `pip install bcrypt`
- [ ] 本番環境では `localStorage` のトークン保存を `httpOnly` / `Secure` Cookie に置き換え
- [ ] レート制限ミドルウェアを追加（例: `slowapi`）
- [ ] CORS の `allow_methods` と `allow_headers` を必要なものだけに制限

### 9. シークレットストレージ

内蔵の `SecretManager` は開発の便宜上、base64 エンコーディング（暗号化ではない）を使用しています。本番環境では:

- [ ] ローカル暗号化に `cryptography.Fernet` を使用、または
- [ ] AWS Secrets Manager / HashiCorp Vault / GCP Secret Manager を統合
- [ ] データベースに平文のシークレットを保存しない

### 10. 推奨事項

- [ ] リポジトリで [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning) を有効化
- [ ] 依存関係の脆弱性アラートのために [Dependabot](https://docs.github.com/en/code-security/dependabot) を有効化
- [ ] `production` デプロイ環境に環境保護ルールを設定
- [ ] すべてのシークレットを定期的にローテーション
