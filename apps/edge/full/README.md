# ZEO Full — Cloudflare Workers 完全移植 (方式 B)

FastAPI バックエンドの主要 API を Hono + D1 (SQLite 互換) でエッジ上に再実装した方式。

## 機能

- JWT 認証（jose ライブラリ使用）
- 全主要 API エンドポイントの再実装
  - Auth: register / login / me
  - Companies: CRUD + dashboard
  - Tickets: list / create / get
  - Agents: list / create / pause / resume
  - Tasks: create / start / complete
  - Approvals: list / approve / reject
  - Specs: list / create / get
  - Plans: create / get / approve
  - Audit Logs: list (フィルタ対応)
  - Budgets: list / create / get + cost ledger
  - Projects: list / create / get
  - Registry: skills / plugins / extensions 検索
  - Artifacts: list / create / get
  - Heartbeats: policies / runs
  - Reviews: list / create / get
- CORS ミドルウェア
- 監査ログミドルウェア（mutating リクエストを自動記録）
- D1 データベース（SQLite 互換）

## セットアップ

```bash
cd apps/edge/full
npm install
```

## データベース初期化

```bash
npm run db:init
```

## ローカル開発

```bash
npm run dev
```

## デプロイ

```bash
npm run deploy
```

## 環境変数

| 変数 | 説明 | デフォルト |
| --- | --- | --- |
| `JWT_SECRET` | JWT 署名用シークレット | `change-me-in-production` |

## D1 データベース

`wrangler.toml` の `database_id` を実際の D1 データベース ID に置き換えてください。

```bash
# D1 データベース作成
wrangler d1 create zeo-orchestrator

# スキーマ適用
wrangler d1 execute zeo-orchestrator --file=src/db/schema.sql
```
