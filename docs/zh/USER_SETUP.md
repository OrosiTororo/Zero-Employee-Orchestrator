# 用户设置指南

> [日本語](../../USER_SETUP.md) | [English](../en/USER_SETUP.md) | 中文

> ZEO 以最小化的初始状态运行，用户可根据需要逐步扩展功能。
> 以下所有设置均为可选，请根据所需功能自行配置。
>
> 有关 ZEO 本体的开发与质量管理设置（Sentry、安全测试等），请参阅 `DEVELOPER_SETUP.md`。
>
> 最后更新: 2026-03-23

---

## 1. 连接 LLM 提供商

ZEO 无需 API 密钥即可开始使用。提供以下 3 种方式:

```bash
# 方法 1: 订阅模式（无需密钥）
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# 方法 2: Ollama 本地 LLM（完全离线・无需密钥）
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# 方法 3: 多 LLM 平台（一个密钥即可使用多个模型）
zero-employee config set OPENROUTER_API_KEY <your-key>
```

> **ZEO 本身不收取任何使用费。** LLM 的 API 费用由用户直接向各提供商支付。
> 不依赖任何特定提供商。当新的平台或服务出现时，只需添加配置即可支持。

### 设置外部 API 密钥（可选）

如需使用更高质量的模型或特定提供商，请设置 API 密钥。所有设置均为可选。

#### LLM 提供商

```bash
# OpenRouter（多 LLM 平台 — 一个密钥即可使用多个模型）
zero-employee config set OPENROUTER_API_KEY <your-key>

# OpenAI (GPT 系列)
zero-employee config set OPENAI_API_KEY <your-key>

# Anthropic (Claude 系列)
zero-employee config set ANTHROPIC_API_KEY <your-key>

# Google (Gemini 系列) — 有免费额度
zero-employee config set GEMINI_API_KEY <your-key>

# Mistral
zero-employee config set MISTRAL_API_KEY <your-key>

# Cohere
zero-employee config set COHERE_API_KEY <your-key>

# DeepSeek
zero-employee config set DEEPSEEK_API_KEY <your-key>
```

### 媒体生成

```bash
# DALL-E (图像生成) — 与 OpenAI API 密钥共用
# Stability AI (Stable Diffusion)
zero-employee config set STABILITY_API_KEY <your-key>

# Replicate (Flux, SVD 等)
zero-employee config set REPLICATE_API_TOKEN <your-key>

# ElevenLabs (语音生成)
zero-employee config set ELEVENLABS_API_KEY <your-key>

# Suno (音乐生成)
zero-employee config set SUNO_API_KEY <your-key>

# Runway ML (视频生成)
zero-employee config set RUNWAY_API_KEY <your-key>
```

### 外部工具集成

```bash
# GitHub
zero-employee config set GITHUB_TOKEN <your-token>

# Slack
zero-employee config set SLACK_BOT_TOKEN <your-token>
zero-employee config set SLACK_SIGNING_SECRET <your-secret>

# Discord
zero-employee config set DISCORD_BOT_TOKEN <your-token>

# Notion
zero-employee config set NOTION_API_KEY <your-key>

# Jira
zero-employee config set JIRA_URL <your-url>
zero-employee config set JIRA_API_TOKEN <your-token>

# Figma (通过 MCP)
zero-employee config set FIGMA_ACCESS_TOKEN <your-token>

# LINE Bot
zero-employee config set LINE_CHANNEL_SECRET <your-secret>
zero-employee config set LINE_CHANNEL_ACCESS_TOKEN <your-token>
```

---

## 2. iPaaS 集成的 Webhook 设置

如需将外部 iPaaS 服务与 ZEO 连接，请进行以下设置。

### n8n

1. 启动 n8n 实例（自托管或 n8n.cloud）
2. 创建 Webhook 节点并复制 URL
3. 在 ZEO 中注册:

```bash
# 通过 API
POST /api/v1/ipaas/workflows
{
  "name": "n8n-workflow-1",
  "provider": "n8n",
  "webhook_url": "https://your-n8n.example.com/webhook/xxx",
  "event_types": ["task_completed", "approval_required"]
}
```

### Zapier

1. 在 Zapier 中创建新的 Zap
2. 选择触发器「Webhooks by Zapier → Catch Hook」
3. 将生成的 Webhook URL 注册到 ZEO

### Make (Integromat)

1. 在 Make 中创建场景
2. 添加 Webhook 模块并复制 URL
3. 注册到 ZEO

---

## 3. Google Workspace 集成（OAuth2）

如需与 Google 文档、电子表格等集成:

1. 在 [Google Cloud Console](https://console.cloud.google.com) 中创建项目
2. 前往「API 和服务」→「凭据」→ 创建 OAuth 2.0 客户端 ID
3. 在重定向 URI 中添加 `http://localhost:18234/api/v1/auth/google/callback`
4. 配置:

```bash
zero-employee config set GOOGLE_CLIENT_ID <client-id>
zero-employee config set GOOGLE_CLIENT_SECRET <client-secret>
```

---

## 4. 安全设置（生产环境必需）

在生产环境中运行 ZEO 时，请务必进行以下设置。

### 生成密钥

```bash
# 生成 SECRET_KEY（在生产环境中务必更改）
python -c "import secrets; print(secrets.token_urlsafe(32))"
zero-employee config set SECRET_KEY <generated-key>
```

### CORS 设置

```bash
# 仅允许生产域名
zero-employee config set CORS_ORIGINS '["https://your-domain.com"]'

# 开发环境（默认）
zero-employee config set CORS_ORIGINS '["http://localhost:5173","http://localhost:18234"]'
```

### 认证中间件（重要）

ZEO 实现了基于 JWT 的认证，受保护的端点需要通过 `get_current_user` 依赖函数进行认证。

**在生产环境中请务必确认以下事项:**

1. **SECRET_KEY 已设置为生产环境用** — 使用默认的临时密钥时，服务器重启后所有令牌将失效
2. **所有业务 API 路由均已启用认证** — 运行 `scripts/security-check.sh` 检查是否存在未认证的路由
3. **SecurityHeadersMiddleware 已启用** — 确保附加了 CSP、HSTS、X-Frame-Options 等安全头

```bash
# 部署前的安全检查
./scripts/security-check.sh

# 确认红队测试未检测到认证绕过
curl -X POST http://localhost:18234/api/v1/security/redteam/run \
  -H 'Content-Type: application/json' -d '{}'
```

> **警告**: 未经认证即公开的端点存在非法数据操作和数据泄露的风险。添加新路由时，请务必包含 `Depends(get_current_user)`。

---

## 5. 数据库设置

### 开发与个人使用（SQLite，无需设置）

默认使用 SQLite，无需额外设置。

### 生产与团队使用（推荐 PostgreSQL）

```bash
# PostgreSQL 连接字符串
zero-employee config set DATABASE_URL "postgresql+asyncpg://user:password@localhost:5432/zeo"

# 执行迁移
zero-employee db upgrade
```

---

## 6. 部署设置

### Docker Compose（推荐）

```bash
# 创建环境变量文件
cp .env.example .env
# 编辑 .env 文件设置 API 密钥

# 启动
docker compose up -d
```

### Cloudflare Workers

```bash
cd apps/edge/full
cp wrangler.toml.example wrangler.toml
# 编辑 wrangler.toml

npm install
npm run deploy
```

### 云服务提供商

根据使用的云服务安装相应 CLI:

```bash
# AWS
pip install awscli
aws configure

# Google Cloud
# 安装 gcloud CLI 后:
gcloud auth application-default login

# Azure
# 安装 az CLI 后:
az login
```

---

## 7. 工作区环境（初始设置）

ZEO 以**安全优先**为设计理念。在初始状态下，AI 代理在**完全隔离的工作区**中运行，无法访问本地文件或云存储。

### 初始状态（默认）

```
工作区:             隔离环境（仅内部存储）
本地文件访问:       禁用
云存储连接:         禁用
知识源:             仅用户上传的文件
```

AI 代理使用的知识和文件仅限于用户上传到此隔离环境中的内容。不会访问本地文件夹或云端（Google Drive 等）的数据。

### 工作区机制

```
┌─────────────────────────────────────────┐
│  隔离工作区（内部存储）                     │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  │
│  │ 知识库   │  │ 成果物   │  │ 临时   │  │
│  │ (参考用)  │  │ (输出)   │  │ 文件   │  │
│  └─────────┘  └─────────┘  └────────┘  │
│                                         │
│  ※ 仅限用户上传的文件                      │
│  ※ AI 只能在此处进行读写                   │
└─────────────────────────────────────────┘
          ↑ 上传          ↓ 导出
      ────────────────────────────────
          ↕ 仅在用户许可的情况下
┌─────────────────┐  ┌─────────────────┐
│ 本地文件夹        │  │ 云存储           │
│ (默认: 禁用)      │  │ (默认: 禁用)     │
└─────────────────┘  └─────────────────┘
```

---

## 8. 本地文件夹与云存储的访问授权

用户可根据需要扩展访问范围。

### 通过 GUI 设置

在设置画面 > 安全 > 工作区环境中进行以下设置:

- **添加本地文件夹**: 通过文件选择器选择允许访问的文件夹
- **连接云存储**: 连接 Google Drive / OneDrive / Dropbox 等
- **指定保存位置**: 从「内部存储」「本地」「云端」中选择成果物的保存位置

### 通过 CLI / TUI 设置

```bash
# 允许访问本地文件夹
zero-employee config set WORKSPACE_LOCAL_ACCESS_ENABLED true
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/documents,/home/user/projects"

# 允许访问云存储
zero-employee config set WORKSPACE_CLOUD_ACCESS_ENABLED true
zero-employee config set WORKSPACE_CLOUD_PROVIDERS '["google_drive"]'

# 设置成果物保存位置
zero-employee config set WORKSPACE_STORAGE_LOCATION internal  # internal / local / cloud

# 更改数据传输策略（允许本地・云访问时）
zero-employee config set SECURITY_TRANSFER_POLICY restricted
```

### 通过 API

```bash
# 查看工作区设置
GET /api/v1/security/workspace

# 更新工作区设置
PUT /api/v1/security/workspace
{
  "local_access_enabled": true,
  "cloud_access_enabled": false,
  "allowed_local_paths": ["/home/user/documents"],
  "cloud_providers": [],
  "storage_location": "internal"
}

# 添加沙箱允许路径
POST /api/v1/security/sandbox/allowed-paths
{ "path": "/home/user/documents" }
```

---

## 9. 按业务自定义环境与权限

除系统整体设置外，还可以**按业务（工单）单独指定环境、权限和知识使用范围**。

### 通过聊天指示

可以通过聊天向 AI 指示每项业务的环境:

```
「这个任务请同时参考本地的 /home/user/project-x 文件夹」
「请也使用 Google Drive 共享文件夹中的资料」
「这项业务的成果物请保存到本地的 /home/user/output」
```

**重要**: 当聊天指示与系统设置不同时，AI 会在计划阶段向用户请求许可。

示例:
```
AI: 「此业务需要访问 /home/user/project-x，
     但当前工作区设置中本地访问已禁用。
     是否仅针对此任务允许以下访问？
     - 读取: /home/user/project-x
     - 写入: /home/user/output
     [允许] [拒绝] [永久更改设置]」
```

### 通过 API 设置任务级别的权限

```bash
POST /api/v1/security/workspace/tasks/{task_id}/override
{
  "additional_local_paths": ["/home/user/project-x"],
  "additional_cloud_sources": ["google_drive://shared/project-x"],
  "storage_location": "local",
  "output_path": "/home/user/output"
}
```

---

## 10. 文件沙箱

用于限制 AI 可访问的文件夹的附加设置。

### 级别

| 级别 | 说明 | 初始设置 |
|------|------|---------|
| **STRICT** | 仅可访问允许列表中的文件夹 | **初始设置** |
| MODERATE | 允许列表 + 常见文件扩展名的读取 | - |
| PERMISSIVE | 除禁止列表外均可访问（不推荐） | - |

```bash
# 设置沙箱级别
zero-employee config set SANDBOX_LEVEL strict

# 添加允许的文件夹
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/projects,/tmp/work"
```

---

## 11. 数据保护（上传与下载控制）

| 策略 | 说明 | 初始设置 |
|------|------|---------|
| **LOCKDOWN** | 全面禁止外部传输 | **初始设置** |
| RESTRICTED | 仅允许用户许可的目标 | - |
| PERMISSIVE | 除禁止列表外均可（不推荐） | - |

```bash
# 设置传输策略
zero-employee config set SECURITY_TRANSFER_POLICY lockdown

# 启用上传（仍需审批）
zero-employee config set SECURITY_UPLOAD_ENABLED true
zero-employee config set SECURITY_UPLOAD_REQUIRE_APPROVAL true
```

---

## 12. Ollama 本地 LLM 设置

如需无 API 密钥的完全本地运行:

```bash
# 1. 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. 下载推荐模型
zero-employee pull qwen3:8b        # 轻量级 (推荐)
zero-employee pull qwen3:32b       # 高质量
zero-employee pull deepseek-coder-v2  # 编程专用

# 3. 将执行模式设置为 free
zero-employee config set DEFAULT_EXECUTION_MODE free
```

---

## 13. 安装 Chrome 扩展程序

```
1. 在 Chrome 中打开 chrome://extensions
2. 开启右上角的「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 extensions/browser-assist/chrome-extension/ 文件夹
5. 确认 ZEO 服务器正在运行（http://localhost:18234）
```

---

## 14. Obsidian 集成

```bash
# 注册 Vault 路径（通过 API）
POST /api/v1/knowledge/remember
{
  "category": "obsidian",
  "key": "vault_path",
  "value": "/path/to/your/obsidian/vault"
}
```

建议同时安装 Obsidian 插件「Local REST API」。

---

## 15. Heartbeat 调度器设置

如需设置定期执行的任务:

```bash
# 通过 API 注册调度
POST /api/v1/companies/{company_id}/heartbeat-policies
{
  "name": "daily-report",
  "cron_expr": "0 9 * * *",
  "timezone": "Asia/Tokyo",
  "enabled": true
}

# 策略列表
GET /api/v1/companies/{company_id}/heartbeat-policies

# 执行历史
GET /api/v1/companies/{company_id}/heartbeat-runs
```

---

## 确认设置

确认所有设置是否正确:

```bash
# 显示所有配置值
zero-employee config list

# 健康检查
zero-employee health

# 安全状态
zero-employee security status
```

---

## 无需设置即可使用的功能

以下功能无需额外设置即可使用:

- Design Interview（需求讨论与深入分析）
- Task Orchestrator（DAG 分解与进度管理）
- Judge Layer（质量验证）
- Self-Healing DAG（自动重新规划）
- Experience Memory（经验记忆）
- Skill Registry（技能管理）
- 审批流程与审计日志
- PII 自动检测与脱敏
- 提示注入防御
- 文件沙箱
- 元技能（AI 的学习能力）
- A2A 双向通信
- 市场基础设施
- 团队管理基础设施
- 治理与合规基础设施
- 内容再利用引擎
- 用户输入请求
- 成果物导出（本地）
- E2E 测试框架
- LLM 响应模拟（测试用）

---

## 安全初始设置一览

```
工作区:             隔离环境（仅内部存储）
本地访问:           禁用
云访问:             禁用
沙箱:               STRICT（仅允许列表）
数据传输策略:       LOCKDOWN（禁止外部传输）
AI 上传:            禁用
AI 下载:            禁用
外部 API 调用:      禁用
PII 自动检测:       启用（全部类别）
PII 上传拦截:       启用
密码类传输:         始终拦截
上传审批:           必需
下载审批:           必需
```

---

*Zero-Employee Orchestrator — 用户设置指南*
