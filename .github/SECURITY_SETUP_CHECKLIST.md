# 🔒 公開前セキュリティセットアップチェックリスト

リポジトリを公開する前に、以下の項目をすべて完了してください。

## 必須（Must）

- [ ] `SECRET_KEY` を安全なランダム値に変更（`apps/api/.env`）
- [ ] `JWT_SECRET` を設定（`wrangler secret put JWT_SECRET`）
- [ ] `CLOUDFLARE_API_TOKEN` を GitHub Secrets に登録
- [ ] `CLOUDFLARE_ACCOUNT_ID` を GitHub Secrets に登録
- [ ] KV namespace `placeholder-id` を実際の値に置換（`apps/edge/proxy/wrangler.toml`）
- [ ] D1 `database_id` の `placeholder-id` を実際の値に置換（`apps/edge/full/wrangler.toml`）
- [ ] `scripts/security-check.sh` を実行して全項目パス

## 推奨（Should）

- [ ] Tauri 署名鍵の生成と設定（`apps/desktop/src-tauri/tauri.conf.json`）
- [ ] CORS_ORIGINS を本番ドメインに変更
- [ ] DATABASE_URL を PostgreSQL に変更
- [ ] GitHub Secret Scanning を有効化
- [ ] Dependabot を有効化（`.github/dependabot.yml` は本PRで追加済み）
- [ ] `production` 環境の保護ルールを設定

## 任意（Nice to Have）

- [ ] Google OAuth の設定
- [ ] シークレットローテーションスケジュールの策定
