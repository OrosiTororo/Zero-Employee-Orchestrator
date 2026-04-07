> [日本語](../ja-JP/OVERVIEW.md) | [English](../OVERVIEW.md) | 中文

# Zero-Employee Orchestrator — 综合指南

> 本文档面向初次接触本项目的读者，全面介绍项目的理念、功能与架构。

---

## 目录

1. [这是什么](#1-这是什么)
2. [为什么需要它](#2-为什么需要它)
3. [基本使用方法](#3-基本使用方法)
4. [9层架构](#4-9层架构)
5. [技术栈](#5-技术栈)
6. [实现状况](#6-实现状况)
7. [离线运行](#7-离线运行)
8. [核心功能与扩展功能的边界](#8-核心功能与扩展功能的边界)
9. [外部工具集成](#9-外部工具集成)
10. [设计注意事项与未来方向](#10-设计注意事项与未来方向)
11. [文档一览](#11-文档一览)

---

## 1. 这是什么

### 一句话概括

**只需用自然语言描述业务需求，多个 AI 便能组建团队进行计划、执行、验证和改进的"AI 业务编排平台"。**

### 更详细的说明

Zero-Employee Orchestrator（ZEO）通过一款软件实现以下功能：

- 只需用自然语言告诉它"想做什么"，AI 就会深入挖掘需求
- AI 将任务分解，并分配给多个 AI Agent 各司其职
- 危险操作（发布、发送、删除、计费）必须经过人类审批
- 所有操作都记录在审计日志中
- 即使失败，AI 也会自动重新规划（Self-Healing）
- 从经验中学习，使用次数越多精度越高

### 与其他 AI Agent 的区别

| | AI Agent（AutoGPT、CrewAI 等） | RPA / n8n / Make | **ZEO** |
|---|---|---|---|
| 输入方式 | 文本 / 代码 | 流程设计 / 节点配置 | **自然语言** |
| AI 团队 | 有限 | 无 / API 调用 | **角色分工的多 AI 团队** |
| 质量保证 | 无或单一模型 | 规则 | **Judge Layer 两阶段验证** |
| 故障恢复 | 停止或简单重试 | 停止 | **Self-Healing DAG 自动重新规划** |
| 审批流程 | 无（全自动） | 手动配置 | **自动检测危险操作并强制阻断** |
| 经验学习 | 无 | 无 | **通过 Experience Memory 积累** |
| 可扩展性 | 修改代码 | 插件（有限） | **Skill / Plugin / Extension 三层** |
| 审计日志 | 无或有限 | 有限 | **全操作记录，可追溯** |

---

## 2. 为什么需要它

当前的 AI 工具存在以下结构性局限：

1. **每次都从零开始** — 反复向 ChatGPT 输入相同的背景信息
2. **手动衔接** — 手动复制 AI 输出并粘贴到下一步
3. **质量未知** — 必须自己验证 AI 的回答是否正确
4. **进度不可见** — 不知道昨天交给 AI 的任务进展到了哪里
5. **担心失控** — 担心 AI 误发邮件或删除重要数据

ZEO 在**架构层面解决**这些问题。

---

## 3. 基本使用方法

### 启动

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # 自动安装依赖
./start.sh   # 启动后端 + 前端
```

在浏览器中打开 **http://localhost:5173**。

### 业务流程

```
1. 用自然语言输入目标
   "制作本月的社交媒体发布日历"

2. Design Interview（AI 深入挖掘需求）
   "目标社交媒体平台是？""发布频率是？""目标受众是？"

3. 自动生成 Spec（要达成什么）

4. 自动生成 Plan（如何实现）
   展示工序、负责 AI、预估成本、所需权限

5. 用户确认计划，进行修改并审批

6. 分解为 Tasks 并行执行
   进度、成果物、失败情况实时可见

7. Judge Layer 进行质量验证
   基于规则的判定 + 不同模型的交叉验证

8. 完成后，确认并审批成果物
   发布、发送等危险操作会显示审批对话框
```

### LLM 配置

| 方式 | 费用 | 配置 |
|------|------|------|
| **Ollama（本地）** | 免费 | `OLLAMA_BASE_URL=http://localhost:11434` |
| **Google Gemini 免费额度** | 免费 | `GEMINI_API_KEY=...` |
| **订阅模式** | 免费 | `DEFAULT_EXECUTION_MODE=subscription` |
| **OpenRouter** | 按量付费 | `OPENROUTER_API_KEY=...` |
| **OpenAI / Anthropic** | 按量付费 | 设置各 API 密钥 |

API 密钥可通过 3 种方式配置：
1. **设置界面**：从应用的"设置"→"LLM API 密钥配置"输入（推荐）
2. **CLI**：`zero-employee config set GEMINI_API_KEY`
3. **.env 文件**：直接编辑 `apps/api/.env`

---

## 4. 9层架构

ZEO 由 9 个层组成，每层拥有独立的职责。

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: User Layer                                  │
│   自然语言输入 → GUI / CLI / TUI / Discord / Slack   │
├─────────────────────────────────────────────────────┤
│ Layer 2: Design Interview                            │
│   需求深挖 → 问题生成 → 答案积累 → Spec 化          │
├─────────────────────────────────────────────────────┤
│ Layer 3: Task Orchestrator                           │
│   Plan 生成 → DAG 化 → Skill 分配 → 成本估算        │
│   Self-Healing DAG → 动态重构                        │
├─────────────────────────────────────────────────────┤
│ Layer 4: Skill Layer                                 │
│   内置 Skill → Plugin 的 Skill → Gap 检测            │
│   Local Context Skill（本地文件安全读取）             │
├─────────────────────────────────────────────────────┤
│ Layer 5: Judge Layer                                 │
│   Stage 1：基于规则的快速检查                         │
│   Stage 2：Cross-Model Verification（不同模型验证）  │
├─────────────────────────────────────────────────────┤
│ Layer 6: Re-Propose Layer                            │
│   退回 → Plan Diff → 部分重新执行 → 再提案           │
├─────────────────────────────────────────────────────┤
│ Layer 7: State & Memory                              │
│   状态机 → Experience Memory → Failure Taxonomy      │
│   Artifact Bridge → Knowledge Refresh               │
├─────────────────────────────────────────────────────┤
│ Layer 8: Provider Interface                          │
│   LiteLLM Gateway → Ollama 直接连接 → g4f            │
│   通过统一 API 在多个 Provider 间切换                │
├─────────────────────────────────────────────────────┤
│ Layer 9: Skill Registry                              │
│   Skill / Plugin / Extension 的搜索、安装与验证      │
└─────────────────────────────────────────────────────┘
```

### 各层说明

| 层 | 功能 | 具体示例 |
|----|------|---------|
| **User Layer** | 接收用户输入 | "制作竞品分析报告" |
| **Design Interview** | 将模糊指令具体化 | "哪些竞品？时间范围？重点指标？" |
| **Task Orchestrator** | 制定执行计划 | 生成 5 阶段 DAG，为每阶段分配 AI |
| **Skill Layer** | 执行实际工作 | 网络搜索、数据整理、报告生成 |
| **Judge Layer** | 验证质量 | 禁止事项检查、不同模型交叉验证 |
| **Re-Propose Layer** | 失败时重新尝试 | 用不同方法重构 DAG |
| **State & Memory** | 记忆状态和经验 | 保存成功模式，下次复用 |
| **Provider Interface** | 连接 AI 模型 | OpenAI / Anthropic / Gemini / Ollama |
| **Skill Registry** | 管理扩展功能 | Skill 搜索、安装、更新 |

---

## 5. 技术栈

### 后端

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 后端语言 |
| FastAPI | REST API 框架 |
| SQLAlchemy 2.x (async) | ORM（数据库访问） |
| Alembic | 数据库迁移 |
| SQLite / PostgreSQL | 数据库 |
| LiteLLM | LLM 网关 |
| httpx | Ollama 直接 HTTP 连接 |

### 前端

| 技术 | 用途 |
|------|------|
| React 19 | UI 框架 |
| TypeScript | 类型安全开发 |
| Vite | 构建工具 |
| Tailwind CSS | 样式 |
| shadcn/ui | UI 组件 |
| Zustand | 状态管理 |
| TanStack Query | 服务器状态管理 |

### 桌面端

| 技术 | 用途 |
|------|------|
| Tauri v2 (Rust) | 桌面应用程序 |

### 边缘部署

| 技术 | 用途 |
|------|------|
| Cloudflare Workers | 边缘执行 |
| Hono | Workers 专用 Web 框架 |
| D1 | 边缘 SQLite |

---

## 6. 实现状况

### 后端（已实现 — 包含实质性代码）

| 组件 | 文件 | 行数 | 状态 |
|------|------|------|------|
| Ollama Provider | `providers/ollama_provider.py` | 656 | 已实现 |
| 本地 RAG | `providers/local_rag.py` | 572 | 已实现 |
| Ollama 集成 | `providers/ollama_integration.py` | 511 | 已实现 |
| LLM Gateway | `providers/gateway.py` | 488 | 已实现 |
| g4f Provider | `providers/g4f_provider.py` | 322 | 已实现 |
| Judge Layer | `orchestration/judge.py` | 250 | 已实现 |
| State Machine | `orchestration/state_machine.py` | 239 | 已实现 |
| Experience Memory | `orchestration/experience_memory.py` | 182 | 已实现 |
| Knowledge Refresh | `orchestration/knowledge_refresh.py` | 169 | 已实现 |
| Failure Taxonomy | `orchestration/failure_taxonomy.py` | 152 | 已实现 |
| Cost Guard | `orchestration/cost_guard.py` | 149 | 已实现 |
| DAG | `orchestration/dag.py` | 147 | 已实现 |
| Artifact Bridge | `orchestration/artifact_bridge.py` | 137 | 已实现 |
| Audit Logger | `audit/logger.py` | 137 | 已实现 |
| Secret Manager | `security/secret_manager.py` | 133 | 已实现 |
| Re-Propose | `orchestration/repropose.py` | 120 | 已实现 |
| Quality SLA | `orchestration/quality_sla.py` | 116 | 已实现 |
| Autonomy Boundary | `policies/autonomy_boundary.py` | 113 | 已实现 |
| Design Interview | `orchestration/interview.py` | 112 | 已实现 |
| Approval Gate | `policies/approval_gate.py` | 109 | 已实现 |
| Sanitizer | `security/sanitizer.py` | 83 | 已实现 |

### API 端点（已实现 — 24 个路由模块）

| 端点组 | 主要功能 |
|--------|---------|
| `/auth` | 登录、注册、匿名会话、OAuth |
| `/companies` | 公司 CRUD、仪表盘 |
| `/tickets` | 工单创建、列表、详情、状态转换、文件附件 |
| `/specs_plans` | Spec / Plan 创建与审批 |
| `/tasks` | 任务创建、执行、完成 |
| `/agents` | Agent 管理、按角色添加、暂停、恢复 |
| `/approvals` | 审批列表、批准、驳回 |
| `/artifacts` | 成果物管理 |
| `/audit` | 审计日志列表与过滤 |
| `/budgets` | 预算策略与成本管理 |
| `/heartbeats` | 定期执行策略与运行历史 |
| `/registry` | Skill / Plugin / Extension 搜索、CRUD、自然语言生成 |
| `/ollama` | 本地 LLM 直接操作、RAG |
| `/settings` | 应用设置、工具连接 |
| `/config` | 运行时配置管理 |
| `/models` | 模型目录、健康检查、废弃管理 |
| `/observability` | 推理追踪、通信日志、执行监控 |
| `/self-improvement` | AI 自我改进（Skill 分析、改进、Judge 调整、A/B 测试） |
| `/multi-model` | 多模型比较、头脑风暴、对话记忆、按角色设置 |
| `/secretary` | 秘书AI（脑暴整理、每日摘要） |
| `/knowledge` | 知识库、变更检测 |
| `/platform` | MCP、Sentry、IAM、假设验证、会话、调查 |
| `/projects` | 项目与目标管理 |
| WebSocket `/ws/events` | 实时事件推送 |

### 前端（23 个页面）

| 页面 | 状态 | 备注 |
|------|------|------|
| LoginPage | 已实现 | 登录、注册、Google OAuth |
| SetupPage | 已实现 | 6 步向导 |
| DashboardPage | 已实现 | 统计、自然语言输入、推荐操作 |
| InterviewPage | 已实现 | 7 个问题的 Design Interview |
| SettingsPage | 已实现 | LLM API 密钥配置、执行模式、Ollama、Provider 连接 |
| ReleasesPage | 已实现 | 版本管理与下载 |
| DownloadPage | 已实现 | 按操作系统分发安装程序 |
| TicketListPage | 有 UI | 数据连接部分完成 |
| TicketDetailPage | 有 UI | 仅有区块结构 |
| SpecPlanPage | 有 UI | DAG 可视化占位符 |
| OrgChartPage | 有 UI | 组织结构骨架 |
| ApprovalsPage | 有 UI | 过滤器与表格结构 |
| AuditPage | 有 UI | 过滤器与表格结构 |
| HeartbeatsPage | 有 UI | 策略与运行历史结构 |
| CostsPage | 有 UI | 预算与支出结构 |
| ArtifactsPage | 有 UI | 成果物列表结构 |
| SkillsPage | 有 UI | 搜索与状态标签 |
| SkillCreatePage | 有 UI | 创建表单 |
| PluginsPage | 有 UI | 浏览器与安装器 |
| PermissionsPage | 有 UI | 权限管理仪表盘 |
| AgentMonitorPage | 有 UI | Agent 监控仪表盘 |
| SecretaryPage | 已实现 | 脑暴整理、每日摘要、优先级建议 |
| BrainstormPage | 已实现 | 头脑风暴、多模型比较、按角色设置、AI 组织管理 |

### ORM 模型（29 张表）

Company, CompanyMember, User, Department, Team, Agent, Project, Goal, Ticket, TicketThread, Spec, Plan, Task, TaskRun, Artifact, Review, ApprovalRequest, HeartbeatPolicy, HeartbeatRun, BudgetPolicy, CostLedger, Skill, Plugin, Extension, ToolConnection, ToolCallTrace, PolicyPack, SecretRef, AuditLog

### 测试

| 测试 | 对象 |
|------|------|
| `test_auth.py` | 认证 |
| `test_companies.py` | 公司管理 |
| `test_tickets.py` | 工单 |
| `test_health.py` | 健康检查 |
| `test_state_machine.py` | 状态转换 |
| `test_cost_guard.py` | 成本管理 |
| `test_failure_taxonomy.py` | 失败分类 |
| `test_audit_logger.py` | 审计日志 |
| `test_registry.py` | 注册表 |
| `test_ollama_provider.py` | Ollama |
| `test_chaos_dag.py` | 混沌测试（Self-Healing DAG） |
| `test_ollama_integration.py` | Ollama 集成 |
| `zeo_bench.py` | ZEO-Bench（Judge Layer 200 题基准测试） |

---

## 7. 离线运行

ZEO 无需云 API 即可运行。

### 完全离线配置

```
Ollama（本地 LLM） + SQLite（本地数据库） + 本地 RAG
```

#### 安装步骤

```bash
# 1. 安装 Ollama
# 从 https://ollama.com/ 下载

# 2. 下载模型
ollama pull qwen3:8b        # 通用（推荐）
ollama pull qwen3-coder:30b # 编程专用

# 3. 配置 .env
echo "OLLAMA_BASE_URL=http://localhost:11434" >> apps/api/.env
echo "DEFAULT_EXECUTION_MODE=free" >> apps/api/.env
```

#### CLI 模式

```bash
zero-employee local                      # 使用默认模型聊天
zero-employee local --model qwen3:8b     # 指定模型
zero-employee local --lang ja            # 日语模式
zero-employee models                     # 列出已安装模型
zero-employee pull qwen3:8b              # 下载模型
```

#### 离线可用功能

| 功能 | 是否可用 | 备注 |
|------|----------|------|
| Design Interview | 可用 | 使用 Ollama 模型推理 |
| Spec / Plan 生成 | 可用 | 使用 Ollama 模型推理 |
| 任务执行（本地 Skill） | 可用 | 文件操作、分析等 |
| Judge Layer（基于规则） | 可用 | 仅 Stage 1 |
| Judge Layer（Cross-Model） | 有条件 | 需要多个 Ollama 模型 |
| 审批流程 | 可用 | 在本地 UI 中完成 |
| 审计日志 | 可用 | 记录在 SQLite 中 |
| 本地 RAG 搜索 | 可用 | 基于 TF-IDF |
| Experience Memory | 可用 | 记录在 SQLite 中 |
| 外部 API 集成 | 不可用 | 需要联网 |

### 支持的本地模型

| 模型 | 用途 |
|------|------|
| `qwen3:8b` / `qwen3:32b` | 高质量通用推理 |
| `qwen3-coder:30b` | 编程专用 |
| `llama3.2` | Meta 通用模型 |
| `mistral` | Mistral 通用模型 |
| `phi3` | Microsoft 轻量模型 |
| `deepseek-coder-v2` | 编程专用 |
| `codellama` | Meta 代码专用 |
| `gemma2` | Google 轻量模型 |

已安装在 Ollama 中的模型会被自动检测。

---

## 8. 核心功能与扩展功能的边界

ZEO 采用了**"不从一开始就全部内置"**的设计理念。

### 核心（平台必需）

认证、权限、审计、状态管理、执行控制、DAG、Judge、审批流程、Experience Memory

-> 没有这些，"AI 业务编排"就无法成立

### Skill（最小能力单元）

文件整理、翻译、脚本生成、竞品分析等

-> `skills/builtin/` 中包含 6 个内置 Skill

### Plugin（业务功能包）

分身 AI、秘书 AI、Discord Bot、Slack Bot、LINE Bot、YouTube 运营、调研、后台管理等

-> `plugins/` 中已定义清单（9 个 Plugin）。业务特定逻辑不放入核心

### Extension（系统基础设施扩展）

OAuth 认证、MCP 连接、通知、Obsidian 集成等

-> `extensions/` 中已定义清单。连接目标的添加不放入核心

**判断标准**："没有它，审批、审计和执行控制是否会无法运作？"

- 是 -> 核心
- 否 -> Skill / Plugin / Extension

详情请参阅 [docs/dev/FEATURE_BOUNDARY.md](../dev/FEATURE_BOUNDARY.md)。

---

## 9. 外部工具集成

### 当前已定义的集成对象

| 集成对象 | 类型 | 状态 | 说明 |
|----------|------|------|------|
| **分身 AI** | Plugin | 已有清单 | 学习用户的决策标准和文风，代理行动 |
| **秘书 AI** | Plugin | 已有清单 | 简报、优先级建议、用户与 AI 组织之间的桥梁 |
| **Discord** | Plugin | 已有清单 (v0.2.0) | 通过 Bot 创建工单、审批、对话、简报 |
| **Slack** | Plugin | 已有清单 (v0.2.0) | 通过 Slash Command 创建工单、审批、对话、简报 |
| **LINE** | Plugin | 已有清单 | 通过 LINE Bot 创建工单、审批、通知 |
| **Obsidian** | Extension | 已有清单 | 将 Vault 作为 Knowledge Source 进行双向集成 |
| **MCP** | Extension | 已有清单 | Model Context Protocol 兼容工具连接 |
| **Google OAuth** | Extension | 已有清单 | Google 账号认证 |
| **通知** | Extension | 已有清单 | Slack / Discord / LINE / 邮件通知 |

### 分身 AI / 秘书 AI

**分身 AI（AI Avatar Plugin）** 学习用户的决策标准和文风，以用户的"分身"身份行动。也可以将用户的价值观反映到 Judge Layer 的判断标准中。

**秘书 AI（AI Secretary Plugin）** 作为连接用户和 AI 组织的"枢纽"，生成晨间简报、下一步行动建议和进度摘要。可以与聊天工具 Plugin 协作，通过 Discord / Slack / LINE 推送简报。

### 从 Discord / Slack / LINE 进行多 Agent 操作

安装 Discord / Slack / LINE Bot Plugin 后，可以直接从聊天应用向 ZEO 的多 Agent 系统发送指令。

```
Discord/Slack/LINE → Bot 接收消息
  → 向 ZEO API 发送工单创建请求
    → Design Interview → Plan → Tasks 执行
      → 结果回复到聊天频道
```

需要审批的操作在聊天工具上也会显示审批对话框。

**命令示例：**
```
/zeo ticket 制作竞品分析报告
/zeo status
/zeo briefing
/zeo ask 这个方案有什么风险？
```

### Obsidian 集成

安装 Obsidian Extension 后，可以将 Vault 中的 Markdown 文件作为 Knowledge Source 使用。

- **导入**：将 Vault 中的笔记导入 RAG
- **导出**：将 Spec / Plan / Tasks / 成果物以 Markdown 格式输出到 Vault
- **链接利用**：将 Obsidian 的 `[[内部链接]]` 结构作为知识图谱引用
- **完全离线**：不需要 Obsidian Sync，只需设置本地 Vault 路径

---

## 10. 设计注意事项与未来方向 (v0.1)

### 避免过度设计的原则

ZEO 的设计文档覆盖范围非常广泛，但实现中遵循以下原则：

1. **MVP 优先** — 首先打通端到端流程是最高优先级
2. **通过 Plugin 添加功能** — 不膨胀核心
3. **9 层是职责分离的指南** — 不需要完全实现所有层
4. **页面逐步充实** — UI 骨架已就位，持续推进数据连接
5. **社区扩展** — 用户分享和发布 Plugin，扩大外部服务集成

### v0.1 功能膨胀审查

以下功能包含在 v0.1 代码库中，但**定位为扩展功能**而非核心功能。
计划在未来版本中作为独立的 Extension / Skill / Plugin 包分离。

| 功能 | 迁移目标 | 原因 |
|------|----------|------|
| Sentry 集成 | Extension | 错误监控对核心的审批、审计、执行控制非必需 |
| AI 调查工具 | Skill | 数据库/日志调查是单一目的任务 |
| 假设验证引擎 | Plugin | 多 Agent 假设验证是高级功能 |
| MCP 服务器 | Extension | 属于连接目标扩展，非核心必需 |
| 外部技能导入 | Extension | Registry 的扩展功能 |

详情请参阅 [docs/dev/FEATURE_BOUNDARY.md](../dev/FEATURE_BOUNDARY.md)。

### 当前课题

| 课题 | 详情 |
|------|------|
| 前端数据连接 | 12 个页面仅有 UI 骨架（后端 API 已存在） |
| features/ 模块 | 11 个模块仅有 `.gitkeep`（逻辑直接写在 pages 中） |
| packages/ 共享库 | 5 个包仅有 `.gitkeep` |
| Worker 核心逻辑 | Runner/Executor 结构存在但逻辑较薄 |
| E2E 测试 | 未实现 |

### 未来优先级

1. **完成前端与后端的连接**
   - 工单列表/详情的数据绑定
   - 审批页面的实时更新
   - 审计日志页面的过滤功能

2. **Design Interview -> Spec -> Plan -> 任务执行的 E2E 流程**
   - 从自然语言输入到成果物生成的全流程贯通

3. **Plugin / Extension 安装机制**
   - 基于清单的加载与执行

4. **Worker 正式运行**
   - 后台任务执行
   - Heartbeat 调度器

---

## 11. 文档一览

> 所有文档的详细说明（目的、目标读者、主要内容）请参阅 **[`docs/MD_FILES_INDEX.md`](../MD_FILES_INDEX.md)**。

**面向用户（`docs/`）：**

| 文件 | 内容 | 目标读者 |
|------|------|---------|
| `README.md` | 快速入门、技术栈 | 所有人 |
| `docs/ABOUT.md` | 为什么需要 ZEO、与传统工具的比较 | 非工程师、管理层 |
| `docs/USER_GUIDE.md` | 从安装到操作方法 | 最终用户 |
| **`docs/OVERVIEW.md`（本文档）** | **理念、功能、架构的综合解说** | **初次访问者** |
| `docs/FEATURES.md` | 已实现功能的完整列表（34 个章节） | 功能确认、评估者 |
| `docs/SECURITY.md` | 安全策略、部署前检查清单 | 运维人员 |
| `docs/CHANGELOG.md` | 变更历史 | 所有人 |
| `docs/Zero-Employee Orchestrator.md` | 最高层级基准文档（理念、需求） | 设计者 |
| `docs/MD_FILES_INDEX.md` | 所有 `.md` 文件的索引 | 所有人 |

**面向开发者（`docs/dev/`）：**

| 文件 | 内容 | 目标读者 |
|------|------|---------|
| `docs/dev/DESIGN.md` | 实现设计文档（数据库、API、状态转换） | 实现者 |
| `docs/dev/MASTER_GUIDE.md` | 实现运维指南 | AI Agent、实现者 |
| `docs/dev/BUILD_GUIDE.md` | 从零开始的构建步骤（附分阶段代码） | 源码构建用户 |
| `docs/dev/FEATURE_BOUNDARY.md` | 核心 vs 扩展的功能边界定义 | 开发者 |
| `docs/dev/PROPOSAL.md` | 项目提案书 | 资助审查员、赞助商 |
| `CLAUDE.md` | Claude Code 开发指南 | AI Agent |

**其他：**

| 文件 | 内容 | 目标读者 |
|------|------|---------|
| `apps/edge/README.md` | Cloudflare Workers 部署方式比较 | 基础设施负责人 |
| `apps/edge/full/README.md` | Full Workers（方式B）安装 | 基础设施负责人 |
| `apps/edge/proxy/README.md` | Proxy（方式A）安装 | 基础设施负责人 |

---

## 目录结构

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                    # FastAPI 后端
│   │   ├── app/
│   │   │   ├── core/           # 配置、数据库、安全、i18n
│   │   │   ├── api/routes/     # REST API（24 个路由）
│   │   │   ├── api/ws/         # WebSocket
│   │   │   ├── models/         # ORM 模型（29 张表 / 18 个文件）
│   │   │   ├── schemas/        # Pydantic DTO
│   │   │   ├── services/       # 业务逻辑
│   │   │   ├── repositories/   # 数据库 I/O 抽象
│   │   │   ├── orchestration/  # DAG、Judge、状态机、Memory（18 个模块）
│   │   │   ├── heartbeat/      # 定期执行调度器
│   │   │   ├── providers/      # LLM Gateway、Ollama、g4f、RAG
│   │   │   ├── tools/          # 外部工具连接（MCP/Webhook/API/CLI）
│   │   │   ├── policies/       # 审批门控、自治边界
│   │   │   ├── security/       # Secret Manager、Sanitizer、IAM
│   │   │   ├── integrations/   # Sentry、MCP Server、外部技能（*扩展功能）
│   │   │   ├── audit/          # 审计日志
│   │   │   └── tests/          # 测试
│   │   └── alembic/            # 数据库迁移
│   ├── desktop/                # Tauri 桌面应用
│   │   └── ui/src/             # React 前端（23 个页面）
│   ├── edge/                   # Cloudflare Workers
│   │   ├── proxy/              # 方式A：反向代理
│   │   └── full/               # 方式B：Hono + D1 完全迁移
│   └── worker/                 # 后台 Worker
├── skills/
│   ├── builtin/                # 内置 Skill（6 个）
│   └── templates/              # Skill 模板
├── plugins/                    # Plugin 清单
│   ├── ai-avatar/              # 分身 AI
│   ├── ai-secretary/           # 秘书 AI
│   ├── discord-bot/            # Discord Bot
│   ├── slack-bot/              # Slack Bot
│   ├── line-bot/               # LINE Bot
│   ├── youtube/                # YouTube 运营
│   ├── research/               # 调研
│   └── backoffice/             # 后台管理
├── extensions/                 # Extension 清单
│   ├── oauth/                  # OAuth 认证
│   ├── mcp/                    # MCP 连接
│   ├── notifications/          # 通知
│   └── obsidian/               # Obsidian 集成
├── packages/                   # 共享包
│   ├── config/                 # 配置
│   ├── sdk/                    # SDK
│   ├── skill-manifest/         # Skill 清单
│   ├── types/                  # 共享类型定义
│   └── ui/                     # 共享 UI
├── docs/                       # 用户文档
│   └── dev/                    # 开发者文档
├── scripts/                    # 开发与部署脚本
│   ├── dev/                    # 开发用
│   ├── lint/                   # 代码检查
│   ├── release/                # 发布
│   └── seed/                   # 种子数据
├── examples/                   # 示例
├── docker/                     # Docker 配置
├── assets/                     # Logo 与图片
├── Dockerfile                  # Rootless 容器
├── docker-compose.yml          # 全服务一键启动
├── setup.sh                    # 安装脚本
└── start.sh                    # 启动脚本
```

---

*Zero-Employee Orchestrator — AI，以组织的形式工作。*
