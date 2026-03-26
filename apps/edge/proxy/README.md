# ZEO Proxy -- Workers Reverse Proxy (Method A)

Reverse proxy that places Cloudflare Workers in front of the existing FastAPI backend.

## Features

- `/api/*` -> Proxy to FastAPI backend
- CORS headers
- IP-based Rate Limiting (using KV)
- Cache API caching for GET responses
- Fallback response when backend is unreachable
- `/health` health check endpoint

## Setup

```bash
cd apps/edge/proxy
npm install
```

## Local Development

```bash
npm run dev
```

## Deploy

```bash
npm run deploy
```

## Environment Variables

| Variable | Description | Default |
| --- | --- | --- |
| `BACKEND_ORIGIN` | FastAPI backend URL | `http://localhost:18234` |

## KV Namespace

A `RATE_LIMIT` KV Namespace is required for rate limiting.
Replace the `id` in `wrangler.toml` with your actual KV Namespace ID.
