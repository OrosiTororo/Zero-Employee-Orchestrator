# Pre-Release Security Setup Checklist

Complete all items below before making the repository public.

## Required (Must)

- [ ] Change `SECRET_KEY` to a secure random value (`apps/api/.env`)
- [ ] Set `JWT_SECRET` (`wrangler secret put JWT_SECRET`)
- [ ] Register `CLOUDFLARE_API_TOKEN` in GitHub Secrets
- [ ] Register `CLOUDFLARE_ACCOUNT_ID` in GitHub Secrets
- [ ] Replace KV namespace `placeholder-id` with actual value (`apps/edge/proxy/wrangler.toml`)
- [ ] Replace D1 `database_id` `placeholder-id` with actual value (`apps/edge/full/wrangler.toml`)
- [ ] Run `scripts/security-check.sh` and pass all checks

## Recommended (Should)

- [ ] Generate and configure Tauri signing keys (`apps/desktop/src-tauri/tauri.conf.json`)
- [ ] Change CORS_ORIGINS to production domain
- [ ] Change DATABASE_URL to PostgreSQL
- [ ] Enable GitHub Secret Scanning
- [ ] Enable Dependabot (`.github/dependabot.yml` included)
- [ ] Set up `production` environment protection rules

## Optional (Nice to Have)

- [ ] Configure Google OAuth
- [ ] Establish a secret rotation schedule
