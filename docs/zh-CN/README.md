**Language:** [English](../../README.md) | [日本語](../ja-JP/README.md) | **简体中文** | [繁體中文](../zh-TW/README.md) | [한국어](../ko-KR/README.md) | [Português (Brasil)](../pt-BR/README.md) | [Türkçe](../tr/README.md)

# Zero-Employee Orchestrator

[![Stars](https://img.shields.io/github/stars/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/stargazers)
[![Forks](https://img.shields.io/github/forks/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/network/members)
[![Contributors](https://img.shields.io/github/contributors/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Rust](https://img.shields.io/badge/-Rust-000000?logo=rust&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)

> **AI 编排平台 — 设计 · 执行 · 验证 · 改进**

---

**将 AI 作为组织来运营的平台 — 不只是聊天机器人。**

ZEO 不是要取代您的 AI 工具，而是统一它们。将 CrewAI、AutoGen、LangChain、Dify、Claude Cowork、n8n、Zapier 以及 34+ 业务应用连接在单一的审批门控、审计追踪和安全层之下。用自然语言定义业务流程，让多个 AI 代理按角色分工协作，在人类审批门控和完整审计能力的支持下执行任务。基于 Self-Healing DAG、Judge Layer 和 Experience Memory 的 9 层架构构建。

ZEO 本身是免费的开源项目。LLM API 费用由用户直接向各提供商支付。

---

## 开始使用

**选择您的方式：**

| 方式 | 适合人群 | 所需时间 | 是否需要 API 密钥？ |
|------|---------|---------|-------------------|
| **[桌面应用](#️-下载桌面应用)** | 非技术用户 | 2 分钟 | 否（订阅模式） |
| **[CLI (pip install)](#-快速开始-cli)** | 开发者 | 2 分钟 | 否（订阅模式或 Ollama） |
| **[Docker](#-docker)** | 自托管 / 生产环境 | 5 分钟 | 否（订阅模式或 Ollama） |

**系统要求：** Python 3.11+（CLI）、Node.js 22+（前端开发）、内存 4 GB 以上。Ollama 本地模型需要 8 GB 以上内存。

---

## 🖥️ 下载桌面应用

预构建的桌面安装程序可在 [Releases](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) 页面获取。

| 操作系统 | 文件 | 说明 |
|---|---|---|
| **Windows** | `-setup.exe` | Windows 安装程序 (x64) |
| **macOS** | `.dmg` | macOS Universal (Intel + Apple Silicon) |
| **Linux** | `.AppImage` | 便携式（无需安装，amd64） |
| **Linux** | `.deb` / `.rpm` | Debian/Ubuntu / Fedora/RHEL (amd64/x86_64) |

安装后，**设置向导**将引导您完成以下步骤：
1. **语言** — 选择 English、日本語、中文、한국어、Português 或 Türkçe（可在设置中随时更改）
2. **LLM 提供商** — 选择 AI 的运行方式（订阅模式无需 API 密钥）
3. **第一个任务** — 立即开始使用平台

---

## 🚀 快速开始 (CLI)

### 步骤 1：安装

```bash
# PyPI（推荐）
pip install zero-employee-orchestrator

# 从源码安装
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .

# Docker（详见下方 Docker 部分）
docker compose -f docker/docker-compose.yml up -d
```

### 步骤 2：配置

选择以下**一种**方式：

```bash
# 方式 A：无需 API 密钥 — 通过 g4f 使用免费 Web AI 服务
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# 方式 B：完全离线 — 通过 Ollama 使用本地模型（无需互联网）
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# 方式 C：API 密钥 — 最高质量，按使用量向提供商付费
zero-employee config set OPENROUTER_API_KEY <your-key>  # or GEMINI_API_KEY, etc.
```

> **ZEO 本身是免费的。** LLM API 费用（如有）由用户直接向各提供商支付。详见 [USER_SETUP.md](../../USER_SETUP.md)。

### 步骤 3：启动

```bash
# 方式 A：start.sh（自动启动后端 + 前端）
./start.sh
# → 打开 http://localhost:5173

# 方式 B：手动启动
zero-employee serve              # 启动 API 服务器（端口 18234）
cd apps/desktop/ui && pnpm dev   # 在另一个终端启动前端（端口 5173）
# → 打开 http://localhost:5173

# 方式 C：仅聊天模式（无需 Web UI）
zero-employee chat               # 默认设置
zero-employee local --model qwen3:8b  # Ollama
```

> **注意：** `zero-employee serve` 仅启动 API 服务器。Web UI 在端口 5173 上单独运行。最简单的方式是使用 `start.sh`。

### 步骤 4：验证

```bash
zero-employee health              # 检查服务器状态
zero-employee models              # 列出可用模型
zero-employee config list         # 查看设置
```

### 切换语言

默认语言为英语。以下方式可在系统范围内切换（CLI、AI 回复和 Web 界面同时切换）：

```bash
# 启动时指定
zero-employee chat --lang ja      # 日语
zero-employee chat --lang zh      # 中文
zero-employee chat --lang ko      # 韩语
zero-employee chat --lang pt      # 葡萄牙语
zero-employee chat --lang tr      # 土耳其语

# 持久化设置（保存到 ~/.zero-employee/config.json）
zero-employee config set LANGUAGE zh

# 运行时切换（在聊天模式中）
/lang en                          # 切换到英语
/lang ja                          # 切换到日语
/lang zh                          # 切换到中文
/lang ko                          # 切换到韩语
/lang pt                          # 切换到葡萄牙语
/lang tr                          # 切换到土耳其语
```

在桌面应用中，可随时通过**设置**更改语言。

---

## 🐳 Docker

### API + 前端（推荐）

```bash
docker compose -f docker/docker-compose.yml up -d
# → 打开 http://localhost:5173
```

将启动三个服务：API 服务器（端口 18234）、前端（端口 5173）和后台工作进程。

> **注意：** 需要 `SECRET_KEY` 环境变量。生成方式：`python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 仅 API

```bash
docker compose up -d
# → API 可在 http://localhost:18234/api/v1/ 访问
```

仅启动 API 服务器。可与桌面应用或自定义前端配合使用。

---

## 指南

<table>
<tr>
<td width="33%">
<a href="../../docs/guides/quickstart-guide.md">
<img src="../../assets/images/guides/quickstart-guide.svg" alt="快速入门指南" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/architecture-guide.md">
<img src="../../assets/images/guides/architecture-guide.svg" alt="架构深度解析" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/security-guide.md">
<img src="../../assets/images/guides/security-guide.svg" alt="安全指南" />
</a>
</td>
</tr>
<tr>
<td align="center"><b>快速入门指南</b><br/>首次工作流、CLI 基础。</td>
<td align="center"><b>架构深度解析</b><br/>9 层架构、DAG、Judge Layer。</td>
<td align="center"><b>安全指南</b><br/>提示防御、审批门控、沙箱。</td>
</tr>
</table>

---

## 📦 项目结构

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                  # FastAPI 后端
│   │   └── app/
│   │       ├── core/               # 配置、数据库、安全、国际化
│   │       ├── api/routes/         # 47 REST API 路由模块
│   │       ├── api/ws/             # WebSocket
│   │       ├── models/             # SQLAlchemy ORM
│   │       ├── schemas/            # Pydantic DTO
│   │       ├── services/           # 业务逻辑
│   │       ├── repositories/       # 数据库 I/O 抽象
│   │       ├── orchestration/      # DAG、Judge、状态机
│   │       ├── providers/          # LLM 网关、Ollama、RAG
│   │       ├── security/           # IAM、密钥、清理、提示防御
│   │       ├── policies/           # 审批门控、自主执行边界
│   │       ├── integrations/       # Sentry、MCP、外部技能、浏览器辅助
│   │       └── tools/              # 外部工具连接器
│   ├── desktop/              # Tauri v2 + React UI
│   ├── edge/                 # Cloudflare Workers
│   └── worker/               # 后台工作进程
├── skills/                   # 11 个内置技能（6 系统 + 5 领域）
├── plugins/                  # 16 个插件清单
├── extensions/               # 11 个扩展清单
│   └── browser-assist/
│       └── chrome-extension/ # 浏览器辅助 Chrome 扩展程序
├── packages/                 # 共享 NPM 包
├── docs/                     # 多语言文档与指南
│   ├── ja-JP/                # 日本語
│   ├── zh-CN/                # 简体中文
│   ├── zh-TW/                # 繁體中文
│   ├── ko-KR/                # 한국어
│   ├── pt-BR/                # Português (Brasil)
│   ├── tr/                   # Türkçe
│   └── guides/               # 架构、安全、快速入门指南
└── assets/
    └── images/
        ├── guides/           # 指南头图
        └── logo/             # Logo 资源
```

---

## 🏗️ 9 层架构

```
┌─────────────────────────────────────────┐
│  1. User Layer       — 用自然语言传达目的         │
│  2. Design Interview — 需求探索与深挖           │
│  3. Task Orchestrator — DAG 分解与进度管理       │
│  4. Skill Layer      — 专业 Skill + Context     │
│  5. Judge Layer      — Two-stage + Cross-Model QA │
│  6. Re-Propose       — 驳回 → 动态 DAG 重构      │
│  7. State & Memory   — Experience Memory        │
│  8. Provider         — LLM 网关 (LiteLLM)       │
│  9. Skill Registry   — 发布 / 搜索 / Import      │
└─────────────────────────────────────────┘
```

---

## 🎯 主要功能

### 核心编排

| 功能 | 描述 |
|------|------|
| **Design Interview** | 自然语言需求探索与深挖 |
| **Spec / Plan / Tasks** | 结构化中间产物 — 可复用、可审计、可退回 |
| **Task Orchestrator** | 基于 DAG 的计划生成、成本估算、质量模式切换 |
| **Judge Layer** | 基于规则的初判 + 跨模型高精度验证 |
| **Self-Healing / Re-Propose** | 失败时自动重新规划，动态 DAG 重构 |
| **Experience Memory** | 从历史执行中学习，提升未来性能 |

### 可扩展性

| 功能 | 描述 |
|------|------|
| **Skill / Plugin / Extension** | 三层可扩展体系（完整 CRUD 管理） |
| **自然语言技能生成** | 用自然语言描述 → AI 自动生成（含安全性检查） |
| **Skill 市场** | 社区技能的发布、搜索、评审和安装 |
| **外部技能导入** | 从 GitHub 仓库导入技能 |
| **自我改进** | AI 分析和改进自身技能（需审批） |
| **元技能** | AI 学习如何学习（Feeling / Seeing / Dreaming / Making / Learning） |

### AI 能力

| 功能 | 描述 |
|------|------|
| **浏览器辅助** | Chrome 扩展程序叠加 — AI 实时查看您的屏幕 |
| **媒体生成** | 图像、视频、音频、音乐、3D — 支持动态提供商注册 |
| **应用连接器中心** | 34+ 应用（Obsidian、Notion、Google Workspace、Microsoft 365 等） |
| **AI 工具集成** | 21 个类别、55+ 外部工具 |
| **A2A 通信** | 代理间点对点消息、频道和协商 |
| **分身 AI** | 从用户对话中学习判断标准，共同成长 |
| **秘书 AI** | 脑中倾倒 → 结构化任务，作为用户和 AI 组织的桥梁 |
| **操作员档案** | Cowork 风格的个人简介 + 全局指令 — AI 根据您的角色、优先级和工作风格个性化回复 |
| **任务派发** | 受 Cowork Dispatch 启发的后台任务 — 发出即忘，支持状态轮询 |
| **再利用引擎** | 自动将 1 个内容转换为 10 种媒体格式 |

### 安全

| 功能 | 描述 |
|------|------|
| **提示注入防御** | 5 个类别、28+ 检测模式 |
| **审批门控** | 14 类危险操作需要人类审批 |
| **文件沙箱** | AI 仅可访问用户许可的文件夹（默认：STRICT） |
| **数据保护** | 上传/下载策略控制（默认：LOCKDOWN） |
| **PII 保护** | 自动检测和脱敏 13 个类别的个人信息 |
| **IAM** | 人类/AI 账户分离，AI 无法访问密钥和管理权限 |
| **红队安全** | 8 个类别、20+ 测试的自我漏洞评估 |

### 运维

| 功能 | 描述 |
|------|------|
| **多模型支持** | 动态目录、自动回退、按任务指定提供商 |
| **多语言（i18n）** | 6 种语言（EN / JA / ZH / KO / PT / TR）— 界面、AI 回复、CLI |
| **自主运行** | Docker / Cloudflare Workers — 即使 PC 关机也能运行 |
| **24/365 调度器** | 9 种触发类型：cron、工单创建、预算阈值等 |
| **iPaaS 集成** | n8n / Zapier / Make Webhook 集成 |
| **云原生** | AWS / GCP / Azure / Cloudflare 抽象层 |
| **治理与合规** | GDPR / HIPAA / SOC2 / ISO27001 / CCPA / APPI |

---

## 🔒 安全

ZEO 采用**安全优先**设计，具备多层防御：

| 层级 | 描述 |
|------|------|
| **提示注入防御** | 检测并阻止来自外部输入的指令注入（5 个类别、28+ 模式） |
| **审批门控** | 14 类危险操作（发送、删除、计费、权限变更等）需要人类审批 |
| **自主执行边界** | 明确限制 AI 可自主执行的操作 |
| **IAM 与工具权限** | 人类/AI 账户分离；基于角色的工具权限（5 个默认策略：secretary、researcher、reviewer、executor、admin）为每个代理实施最小权限 |
| **紧急停止开关** | 通过 UI 按钮或 API（`/kill-switch/activate`）紧急停止所有活动执行。在恢复之前阻止新的执行 |
| **分级 Judge** | 三级验证：LIGHTWEIGHT（仅规则）→ STANDARD（+策略）→ HEAVY（+跨模型）。降低低风险操作的成本，同时对高风险操作维持完整验证 |
| **记忆信任度** | Experience Memory 条目跟踪来源类型、信任级别（0.0-1.0）、验证状态和过期时间。仅使用可信记忆（≥0.7，未过期） |
| **密钥管理** | Fernet 加密、自动脱敏、轮换支持 |
| **清理** | API 密钥、令牌和个人信息的自动移除 |
| **安全头** | 所有响应添加 CSP、HSTS、X-Frame-Options |
| **速率限制** | 基于 slowapi 的 API 速率限制 |
| **审计日志** | 记录所有关键操作（从设计阶段内置，非事后添加） |

漏洞报告请参阅 [SECURITY.md](../../SECURITY.md)。

---

## 🖥️ CLI 参考

```bash
zero-employee serve              # 启动 API 服务器
zero-employee serve --port 8000  # 指定端口
zero-employee serve --reload     # 热重载

zero-employee chat               # 聊天模式（所有提供商）
zero-employee chat --mode free   # 免费模式（Ollama / g4f）
zero-employee chat --lang zh     # 语言选择

zero-employee local              # 本地聊天（Ollama）
zero-employee local --model qwen3:8b --lang zh

zero-employee models             # 已安装模型列表
zero-employee pull qwen3:8b      # 下载模型

zero-employee config list        # 显示所有设置
zero-employee config set <KEY>   # 设置值
zero-employee config get <KEY>   # 获取值

zero-employee db upgrade         # 数据库迁移
zero-employee health             # 健康检查
zero-employee security status    # 安全状态
zero-employee update             # 更新到最新版本
```

---

## 🤖 支持的 LLM 模型

通过 `model_catalog.json` 统一管理 — 无需修改代码即可切换模型。

| 模式 | 描述 | 示例 |
|------|------|------|
| **Quality** | 最高质量 | Claude Opus, GPT, Gemini Pro |
| **Speed** | 快速响应 | Claude Haiku, GPT Mini, Gemini Flash |
| **Cost** | 低成本 | Haiku, Mini, Flash Lite, DeepSeek |
| **Free** | 免费 | Gemini 免费额度, Ollama 本地 |
| **Subscription** | 无需 API 密钥 | 通过 g4f |

支持按任务指定提供商 — 可为每个任务指定提供商、模型和执行模式。

---

## 🧩 Skill / Plugin / Extension

### 三层可扩展体系

| 类型 | 描述 | 示例 |
|------|------|------|
| **Skill** | 单一用途的专业处理 | spec-writer, review-assistant, browser-assist |
| **Plugin** | 捆绑多个 Skill | ai-secretary, ai-self-improvement, youtube |
| **Extension** | 系统集成与基础设施 | mcp, oauth, notifications, browser-assist |

### 用自然语言生成技能

```bash
POST /api/v1/registry/skills/generate
{
  "description": "将长文档总结为3个要点的技能"
}
```

自动检测 18 种危险模式。仅通过安全性检查的技能才会被注册。

---

## 🌐 浏览器辅助

Chrome 扩展程序叠加聊天 — AI 实时查看您的屏幕并指导操作。

- **叠加聊天**：在任意网站上直接显示聊天 UI
- **实时屏幕共享**：无需手动截图，AI 直接查看您的屏幕
- **错误诊断**：AI 读取屏幕上的错误消息并建议修复方案
- **表单辅助**：逐字段的步骤式指导
- **隐私优先**：截图仅临时处理，PII 自动脱敏，密码字段自动模糊

### 设置

```
1. 在 Chrome 中加载 extensions/browser-assist/chrome-extension/
   → chrome://extensions → 开发者模式 → "加载已解压的扩展程序"
2. 在任意网站上点击聊天图标
3. 输入文字提问，或通过截图按钮将屏幕共享给 AI
```

---

## 🛠️ 技术栈

### 后端
- Python 3.11+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- SQLite（开发）/ PostgreSQL（生产推荐）
- LiteLLM Router SDK
- bcrypt / Fernet 加密
- slowapi 速率限制

### 前端
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand

### 桌面端
- Tauri v2 (Rust) + Python sidecar

### 部署
- Docker + docker-compose
- Cloudflare Workers（无服务器）

---

## ❓ 常见问题

<details>
<summary><b>需要 API 密钥才能开始吗？</b></summary>

不需要。您可以使用订阅模式（无需密钥）或 Ollama（完全离线的本地 AI）。请参阅上方的快速开始部分。
</details>

<details>
<summary><b>费用是多少？</b></summary>

ZEO 本身是免费的。LLM API 费用由您直接向各提供商（OpenAI、Anthropic、Google 等）支付。您也可以使用 Ollama 本地模型完全免费运行。
</details>

<details>
<summary><b>可以同时使用多个 LLM 提供商吗？</b></summary>

可以。ZEO 支持按任务指定提供商 — 您可以在同一工作流中使用 Claude 进行高质量的规格审查，使用 GPT 进行快速任务执行。
</details>

<details>
<summary><b>我的数据安全吗？</b></summary>

ZEO 采用自托管设计。您的数据始终保留在您的基础设施上。文件沙箱默认为 STRICT，数据传输默认为 LOCKDOWN，PII 自动检测默认启用。
</details>

<details>
<summary><b>与 AutoGen / CrewAI / LangGraph 有什么区别？</b></summary>

ZEO 是一个**业务工作流平台**，而非开发者框架。它提供人类审批门控、审计日志、三层可扩展体系、浏览器辅助、媒体生成和完整的 REST API — 所有这些都是为将 AI 作为组织来运营而设计的，而不仅仅是链式提示。
</details>

---

## 🧪 开发

```bash
# 设置
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# 启动（热重载）
zero-employee serve --reload

# 测试
pytest apps/api/app/tests/

# 代码检查
ruff check apps/api/app/
ruff format apps/api/app/
```

---

## 🤝 贡献

欢迎贡献。

1. Fork → Branch → PR（标准流程）
2. 安全问题：请按照 [SECURITY.md](../../SECURITY.md) 进行非公开报告
3. 编码规范：ruff 格式化、类型提示必须、async def

---

## 💜 赞助

本项目免费且开源。赞助有助于项目的持续维护和发展。

[**成为赞助者**](https://github.com/sponsors/OrosiTororo)

---

## 🌟 Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=OrosiTororo/Zero-Employee-Orchestrator&type=Date)](https://star-history.com/#OrosiTororo/Zero-Employee-Orchestrator&Date)

---

## 📄 许可证

MIT — 自由使用和修改，如果可以的话请贡献回来。

---

<p align="center">
  <strong>Zero-Employee Orchestrator</strong> — 将 AI 作为组织来运营。<br>
  以安全性、可审计性和人类监督为核心构建。
</p>
