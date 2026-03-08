# ☁️ Cloudflare Workers デプロイオプション

Zero-Employee Orchestrator を Cloudflare Workers 上にデプロイするための2つの方式を提供しています。

## 方式比較

| | 方式 A: Proxy | 方式 B: Full Workers |
| --- | --- | --- |
| **ディレクトリ** | `apps/edge/proxy/` | `apps/edge/full/` |
| **概要** | 既存 FastAPI の前段にリバプロ配置 | 主要 API をエッジ上に完全再実装 |
| **バックエンド** | 既存の FastAPI をそのまま利用 | D1 (SQLite互換) で完全独立 |
| **フレームワーク** | Hono | Hono + jose |
| **データベース** | 不要（既存 DB を利用） | D1 |
| **認証** | バックエンドに委譲 | JWT (jose) |
| **Rate Limiting** | KV ベース | — |
| **キャッシュ** | Cache API (GET のみ) | — |
| **外部サーバー** | 必要（FastAPI） | 不要 |
| **セットアップ難易度** | 低 | 中 |
| **レイテンシ** | バックエンド依存 | 非常に低い |
| **コスト** | Workers 無料枠 + サーバー費用 | Workers + D1 無料枠のみ |

## 選び方ガイド

- **VPS / 自前サーバーがある** → **方式 A (Proxy)** がおすすめ
  - 既存の FastAPI バックエンドをそのまま活かせます
  - Workers は CDN + Rate Limiter + Cache として動作します

- **サーバーレスで完結したい** → **方式 B (Full Workers)** がおすすめ
  - サーバー管理不要、Cloudflare の無料枠だけで運用可能
  - D1 を使ったエッジ上の完全なデータベース

- **両方試せる** → まず **方式 A** で始めて、本格運用時に **方式 B** へ移行

## 共通の前提条件

1. [Cloudflare アカウント](https://dash.cloudflare.com/sign-up)
2. [wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) のインストール

```bash
npm install -g wrangler
wrangler login
```

## 方式 A: Proxy セットアップ

```bash
cd apps/edge/proxy
npm install

# wrangler.toml の BACKEND_ORIGIN を実際のバックエンド URL に変更
# KV Namespace を作成し、id を置き換え
wrangler kv:namespace create RATE_LIMIT

# ローカル開発
npm run dev

# デプロイ
npm run deploy
```

詳細: [apps/edge/proxy/README.md](proxy/README.md)

## 方式 B: Full Workers セットアップ

```bash
cd apps/edge/full
npm install

# D1 データベースを作成
wrangler d1 create zeo-orchestrator
# wrangler.toml の database_id を出力された ID に置き換え

# スキーマ適用
npm run db:init

# wrangler.toml の JWT_SECRET を安全な値に変更

# ローカル開発
npm run dev

# デプロイ
npm run deploy
```

詳細: [apps/edge/full/README.md](full/README.md)

## フロントエンド (Cloudflare Pages)

```bash
cd apps/desktop/ui
npm install
npm run build

# Pages にデプロイ
npx wrangler pages deploy dist --project-name=zeo-ui
```

## GitHub Actions によるデプロイ

`.github/workflows/deploy-workers.yml` で手動デプロイが可能です。

### 必要な Secrets

| Secret | 説明 |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API トークン |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare アカウント ID |

### 使い方

1. GitHub リポジトリの Actions タブを開く
2. "Deploy to Cloudflare Workers" ワークフローを選択
3. "Run workflow" をクリック
4. デプロイモード (`proxy` / `full` / `pages`) を選択して実行
