# Deployment Security Setup Checklist

Complete all items below before deploying to production.

## Required (Must)

- [ ] Change `SECRET_KEY` to a secure random value in your `.env` file
  - Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Set `JWT_SECRET` for Cloudflare Workers (`wrangler secret put JWT_SECRET`)
- [ ] Register `CLOUDFLARE_API_TOKEN` in GitHub Secrets (if using Cloudflare deployment)
- [ ] Register `CLOUDFLARE_ACCOUNT_ID` in GitHub Secrets (if using Cloudflare deployment)
- [ ] Replace KV namespace `placeholder-id` with your actual value (`apps/edge/proxy/wrangler.toml`)
- [ ] Replace D1 `database_id` `placeholder-id` with your actual value (`apps/edge/full/wrangler.toml`)
- [ ] Run `scripts/security-check.sh` and pass all checks

## Recommended (Should)

- [ ] Generate and configure Tauri signing keys (`apps/desktop/src-tauri/tauri.conf.json`)
- [ ] Change `CORS_ORIGINS` to your production domain
- [ ] Change `DATABASE_URL` to PostgreSQL for production
- [ ] Enable GitHub Secret Scanning on your repository
- [ ] Enable Dependabot (`.github/dependabot.yml` included)
- [ ] Set up `production` environment protection rules in GitHub

## Optional (Nice to Have)

- [ ] Configure Google OAuth for user authentication
- [ ] Establish a secret rotation schedule
