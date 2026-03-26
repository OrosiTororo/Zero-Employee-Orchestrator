> [日本語](../ja-JP/SECURITY.md) | [English](../SECURITY.md) | 中文

# 安全策略

## 支持版本

| 版本 | 支持状态 |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## 报告漏洞

如果您发现安全漏洞，请**不要**创建公开 Issue。

请通过 [GitHub Security Advisories](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/security/advisories/new)（私密）进行报告。

我们将在 48 小时内确认收到报告，并致力于在 7 天内发布关键问题的修复。

---

## 部署安全检查清单

在将此应用部署到生产环境（或将仓库设为公开）之前，请确保以下事项：

### 1. 密钥与凭证

| 项目 | 设置位置 | 生成方式 |
| --- | --- | --- |
| `SECRET_KEY` | `apps/api/.env` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_SECRET` | `wrangler secret put JWT_SECRET` | `openssl rand -base64 32` |
| `CLOUDFLARE_API_TOKEN` | GitHub 仓库 Secrets | [Cloudflare Dashboard](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub 仓库 Secrets | Cloudflare Dashboard 侧边栏 |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | `apps/api/.env`（可选） | [Google Cloud Console](https://console.cloud.google.com/) |

> 当 `DEBUG=false` 时，使用默认 `SECRET_KEY` **应用将拒绝启动**（Python 后端），使用默认 `JWT_SECRET` 将返回 `503`（Cloudflare Workers）。这是设计使然。

### 2. 源代码中不包含密钥

本仓库**不包含任何真实密钥**。所有凭证通过以下方式管理：
- 环境变量（`.env` 文件 — 已通过 `.gitignore` 排除）
- GitHub Actions Secrets
- Cloudflare Workers Secrets（`wrangler secret put`）

### 3. 部署工作流

`deploy-workers.yml` 工作流：
- **仅手动触发**（`workflow_dispatch`）— 推送代码时不会自动部署
- 需要 `production` 环境 — 在仓库 Settings 中配置[环境保护规则](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)（可选的审查者批准）
- 在继续之前验证所需的 Secrets 是否已配置

### 4. 占位符 ID

以下文件包含 `placeholder-id` 值，在部署前必须替换为真实的资源 ID：

| 文件 | 字段 | 创建资源的方式 |
| --- | --- | --- |
| `apps/edge/proxy/wrangler.toml` | KV namespace `id` | `wrangler kv:namespace create RATE_LIMIT` |
| `apps/edge/full/wrangler.toml` | D1 `database_id` | `wrangler d1 create zeo-orchestrator` |

### 5. Tauri 自动更新

桌面应用的自动更新程序（`apps/desktop/src-tauri/tauri.conf.json`）的 `pubkey` 为空。在发布生产构建之前：
```bash
npx tauri signer generate -w ~/.tauri/mykey.key
```
在 `tauri.conf.json` 中设置公钥，并使用私钥对发布构建进行签名。

### 6. CORS 配置

更新 `.env` 中的 `CORS_ORIGINS` 以匹配您的实际生产域名。默认值（`localhost:3000`、`localhost:5173`）仅用于开发环境。

### 7. 数据库

- 开发环境使用 SQLite（适用于本地使用）
- 生产环境应使用 PostgreSQL：`DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname`

### 8. 认证与 API 安全

> **v0.1 说明**：当前 API 路由在开发模式下不强制执行每个端点的认证。在部署到生产环境之前，需要为所有端点添加认证中间件。

- [ ] 为所有 API 端点添加认证检查（使用 FastAPI `Depends` 配合 `get_current_user`）
- [ ] 添加 WebSocket 认证（在接受连接前验证 JWT）
- [ ] 安装 `bcrypt` 进行安全密码哈希：`pip install bcrypt`
- [ ] 在生产环境中将 `localStorage` 令牌存储替换为 `httpOnly` / `Secure` Cookie
- [ ] 添加速率限制中间件（例如 `slowapi`）
- [ ] 将 CORS `allow_methods` 和 `allow_headers` 限制为仅所需项

### 9. 密钥存储

内置的 `SecretManager` 使用 base64 编码（非加密）以方便开发。在生产环境中：

- [ ] 使用 `cryptography.Fernet` 进行本地加密，或
- [ ] 集成 AWS Secrets Manager / HashiCorp Vault / GCP Secret Manager
- [ ] 绝不在数据库中存储明文密钥

### 10. 建议

- [ ] 在仓库上启用 [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [ ] 启用 [Dependabot](https://docs.github.com/en/code-security/dependabot) 以获取依赖漏洞警报
- [ ] 为 `production` 部署环境设置环境保护规则
- [ ] 定期轮换所有密钥
