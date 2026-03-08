# ZEO Proxy — Workers Reverse Proxy (方式 A)

既存の FastAPI バックエンドの前段に Cloudflare Workers を配置するリバースプロキシ方式。

## 機能

- `/api/*` → FastAPI バックエンドへプロキシ
- CORS ヘッダー付与
- IP ベースの Rate Limiting（KV 使用）
- GET レスポンスの Cache API キャッシング
- バックエンド接続不可時の fallback レスポンス
- `/health` ヘルスチェックエンドポイント

## セットアップ

```bash
cd apps/edge/proxy
npm install
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
| `BACKEND_ORIGIN` | FastAPI バックエンドの URL | `http://localhost:18234` |

## KV Namespace

Rate Limiting 用に `RATE_LIMIT` KV Namespace が必要です。
`wrangler.toml` の `id` を実際の KV Namespace ID に置き換えてください。
