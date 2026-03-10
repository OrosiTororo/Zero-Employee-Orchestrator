> [日本語](../SECURITY.md) | English | [中文](../zh/SECURITY.md)

# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do NOT open a public issue**.

Instead, report it via [GitHub Security Advisories](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/security/advisories/new) (private).

We will acknowledge receipt within 48 hours and aim to release a fix within 7 days for critical issues.

---

## Deployment Security Checklist

Before deploying this application to production (or making the repository public), ensure the following:

### 1. Secrets & Keys

| Item | Where to set | How to generate |
| --- | --- | --- |
| `SECRET_KEY` | `apps/api/.env` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_SECRET` | `wrangler secret put JWT_SECRET` | `openssl rand -base64 32` |
| `CLOUDFLARE_API_TOKEN` | GitHub repo Secrets | [Cloudflare Dashboard](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub repo Secrets | Cloudflare Dashboard sidebar |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | `apps/api/.env` (optional) | [Google Cloud Console](https://console.cloud.google.com/) |

> **The application refuses to start** with the default `SECRET_KEY` when `DEBUG=false` (Python backend) and returns `503` with the default `JWT_SECRET` (Cloudflare Workers). This is by design.

### 2. No Secrets in Source Code

This repository contains **no real secrets**. All credentials are managed via:
- Environment variables (`.env` files — excluded by `.gitignore`)
- GitHub Actions Secrets
- Cloudflare Workers Secrets (`wrangler secret put`)

### 3. Deployment Workflow

The `deploy-workers.yml` workflow:
- Triggers **only manually** (`workflow_dispatch`) — no automatic deployments on push
- Requires the `production` environment — configure [environment protection rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment) (optional reviewer approval) in repo Settings
- Validates that required secrets are configured before proceeding

### 4. Placeholder IDs

The following files contain `placeholder-id` values that must be replaced with real resource IDs before deployment:

| File | Field | How to create the resource |
| --- | --- | --- |
| `apps/edge/proxy/wrangler.toml` | KV namespace `id` | `wrangler kv:namespace create RATE_LIMIT` |
| `apps/edge/full/wrangler.toml` | D1 `database_id` | `wrangler d1 create zeo-orchestrator` |

### 5. Tauri Auto-Updater

The desktop app's auto-updater (`apps/desktop/src-tauri/tauri.conf.json`) has an empty `pubkey`. Before publishing production builds:
```bash
npx tauri signer generate -w ~/.tauri/mykey.key
```
Set the public key in `tauri.conf.json` and sign release builds with the private key.

### 6. CORS Configuration

Update `CORS_ORIGINS` in `.env` to match your actual production domain(s). The defaults (`localhost:3000`, `localhost:5173`) are for development only.

### 7. Database

- Development uses SQLite (fine for local use)
- Production should use PostgreSQL: `DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname`

### 8. Authentication & API Security

> **v0.1 Note**: The current API routes do not enforce per-endpoint authentication in development mode. Before deploying to production, add authentication middleware to all endpoints.

- [ ] Add authentication checks to all API endpoints (use FastAPI `Depends` with `get_current_user`)
- [ ] Add WebSocket authentication (verify JWT before accepting connections)
- [ ] Install `bcrypt` for secure password hashing: `pip install bcrypt`
- [ ] Replace `localStorage` token storage with `httpOnly` / `Secure` cookies in production
- [ ] Add rate limiting middleware (e.g., `slowapi`)
- [ ] Restrict CORS `allow_methods` and `allow_headers` to only what's needed

### 9. Secret Storage

The built-in `SecretManager` uses base64 encoding (not encryption) for development convenience. For production:

- [ ] Use `cryptography.Fernet` for local encryption, or
- [ ] Integrate AWS Secrets Manager / HashiCorp Vault / GCP Secret Manager
- [ ] Never store plaintext secrets in the database

### 10. Recommendations

- [ ] Enable [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning) on the repository
- [ ] Enable [Dependabot](https://docs.github.com/en/code-security/dependabot) for dependency vulnerability alerts
- [ ] Set up environment protection rules for the `production` deployment environment
- [ ] Rotate all secrets periodically
