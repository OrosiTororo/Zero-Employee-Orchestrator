# Cloudflare Workers Deploy Options

Two deployment methods for running Zero-Employee Orchestrator on Cloudflare Workers.

## Method Comparison

| | Method A: Proxy | Method B: Full Workers |
| --- | --- | --- |
| **Directory** | `apps/edge/proxy/` | `apps/edge/full/` |
| **Overview** | Reverse proxy in front of existing FastAPI | Full re-implementation of major APIs on the edge |
| **Backend** | Uses existing FastAPI as-is | Fully independent with D1 (SQLite-compatible) |
| **Framework** | Hono | Hono + jose |
| **Database** | Not needed (uses existing DB) | D1 |
| **Authentication** | Delegated to backend | JWT (jose) |
| **Rate Limiting** | KV-based | -- |
| **Caching** | Cache API (GET only) | -- |
| **External Server** | Required (FastAPI) | Not required |
| **Setup Difficulty** | Low | Medium |
| **Latency** | Backend-dependent | Very low |
| **Cost** | Workers free tier + server costs | Workers + D1 free tier only |
| **Supported APIs** | All APIs (proxy) | Auth, Companies, Tickets, Agents, Tasks, Approvals, Specs, Plans, Audit, Budgets, Projects, Registry, Artifacts, Heartbeats, Reviews |

## How to Choose

- **Have a VPS or your own server** -> **Method A (Proxy)** recommended
  - Leverages your existing FastAPI backend
  - Workers acts as CDN + Rate Limiter + Cache

- **Want to go fully serverless** -> **Method B (Full Workers)** recommended
  - No server management; runs on Cloudflare's free tier alone
  - Full edge database with D1

- **Want to try both** -> Start with **Method A**, migrate to **Method B** for production

## Prerequisites

1. [Cloudflare account](https://dash.cloudflare.com/sign-up)
2. [wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) installed

```bash
npm install -g wrangler
wrangler login
```

## Method A: Proxy Setup

```bash
cd apps/edge/proxy
npm install

# Change BACKEND_ORIGIN in wrangler.toml to your actual backend URL
# Create a KV Namespace and replace the id
wrangler kv:namespace create RATE_LIMIT

# Local development
npm run dev

# Deploy
npm run deploy
```

Details: [apps/edge/proxy/README.md](proxy/README.md)

## Method B: Full Workers Setup

```bash
cd apps/edge/full
npm install

# Create D1 database
wrangler d1 create zeo-orchestrator
# Replace database_id in wrangler.toml with the output ID

# Apply schema
npm run db:init

# Change JWT_SECRET in wrangler.toml to a secure value

# Local development
npm run dev

# Deploy
npm run deploy
```

Details: [apps/edge/full/README.md](full/README.md)

## Frontend (Cloudflare Pages)

```bash
cd apps/desktop/ui
npm install
npm run build

# Deploy to Pages
npx wrangler pages deploy dist --project-name=zeo-ui
```

## Deployment via GitHub Actions

Manual deployment is available via `.github/workflows/deploy-workers.yml`.

### Required Secrets

| Secret | Description |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID |

### Usage

1. Open the Actions tab in the GitHub repository
2. Select the "Deploy to Cloudflare Workers" workflow
3. Click "Run workflow"
4. Choose a deploy mode (`proxy` / `full` / `pages`) and run
