# ZEO Full -- Cloudflare Workers Full Implementation (Method B)

Full re-implementation of major FastAPI backend APIs using Hono + D1 (SQLite-compatible) on the edge.

## Features

- JWT authentication (using jose library)
- All major API endpoints re-implemented
  - Auth: register / login / me
  - Companies: CRUD + dashboard
  - Tickets: list / create / get
  - Agents: list / create / pause / resume
  - Tasks: create / start / complete
  - Approvals: list / approve / reject
  - Specs: list / create / get
  - Plans: create / get / approve
  - Audit Logs: list (with filters)
  - Budgets: list / create / get + cost ledger
  - Projects: list / create / get
  - Registry: skills / plugins / extensions search
  - Artifacts: list / create / get
  - Heartbeats: policies / runs
  - Reviews: list / create / get
- CORS middleware
- Audit log middleware (auto-records mutating requests)
- D1 database (SQLite-compatible)

## Setup

```bash
cd apps/edge/full
npm install
```

## Database Initialization

```bash
npm run db:init
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
| `JWT_SECRET` | JWT signing secret | `change-me-in-production` |

## D1 Database

Replace the `database_id` in `wrangler.toml` with your actual D1 database ID.

```bash
# Create D1 database
wrangler d1 create zeo-orchestrator

# Apply schema
wrangler d1 execute zeo-orchestrator --file=src/db/schema.sql
```
