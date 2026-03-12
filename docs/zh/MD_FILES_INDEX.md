> [日本語](../MD_FILES_INDEX.md) | [English](../en/MD_FILES_INDEX.md) | 中文

# 仓库内 Markdown 文件索引

> 最后更新: 2026-03-12 (v0.1.1)
>
> 本文档是 Zero-Employee Orchestrator 仓库中所有 `.md` 文件的概要、用途和目标读者的索引列表。

---

## 目录

1. [根目录文档](#1-根目录文档)
2. [docs/ — 用户文档](#2-docs--用户文档)
3. [docs/dev/ — 开发者文档](#3-docsdev--开发者文档)
4. [apps/edge/ 文档](#4-appsedge-文档)
5. [.github/ 文档](#5-github-文档)
6. [文档参考优先级](#6-文档参考优先级)

---

## 1. 根目录文档

### `README.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/README.md` |
| **用途** | 项目的第一印象文档。汇总概述、主要功能、安装步骤和技术栈 |
| **目标读者** | 所有用户和开发者 |
| **主要内容** | 支持日语、英语、中文三种语言。GUI 版（桌面安装程序）和 CLI 版的安装步骤、技术栈表、快速启动命令 |

---

### `CLAUDE.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/CLAUDE.md` |
| **用途** | 面向 Claude Code（AI 编程代理）的开发指南。将整个项目概述浓缩到一个文件中 |
| **目标读者** | Claude Code（AI 代理） |
| **主要内容** | 9 层架构定义、技术栈、目录结构、编码规范、设计原则、DB Schema 概述、全部 API 端点、运行时配置管理、支持的 LLM 模型、Ollama 集成、Skill 管理 v0.1、禁止事项 |

---

### `CONTRIBUTING.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/CONTRIBUTING.md` |
| **用途** | 项目贡献方法的指南 |
| **目标读者** | 贡献者、开发者 |
| **主要内容** | 支持三种语言（日语、英语、中文）。Issue 报告方法、Pull Request 创建流程、编码规范、开发环境设置 |

---

### `CODE_OF_CONDUCT.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/CODE_OF_CONDUCT.md` |
| **用途** | 社区行为准则 |
| **目标读者** | 所有贡献者和用户 |
| **主要内容** | 支持三种语言（日语、英语、中文）。基于 Contributor Covenant 2.1 的行为准则 |

---

### `ROADMAP.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/ROADMAP.md` |
| **用途** | v0.2 至 v1.0 的路线图 |
| **目标读者** | 用户、开发者、贡献者 |
| **主要内容** | 支持三种语言（日语、英语、中文）。各版本的计划功能列表（带优先级） |

---

## 2. docs/ — 用户文档

面向用户（终端用户、评估者、运维人员）或用户和开发者共同参考的文档。

### `docs/ABOUT.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/ABOUT.md` |
| **用途** | 阐述"为什么需要 Zero-Employee Orchestrator"的营销与说明文档 |
| **目标读者** | 非工程师、管理层、产品评估者 |
| **主要内容** | 与其他 AI 代理、RPA、n8n/Make 的对比表，9 大竞争优势，企业级支持 |

---

### `docs/USER_GUIDE.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/USER_GUIDE.md` |
| **用途** | 从设置到操作的终端用户手册 |
| **目标读者** | 终端用户（工程师和非工程师均适用） |
| **主要内容** | 支持日语、英语、中文三种语言。系统要求、LLM 连接方式、安装步骤、所有画面的说明和操作方法、工单使用方法、审批流程、Skill/Plugin 扩展方法、成本管理、故障排除、FAQ |

---

### `docs/OVERVIEW.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/OVERVIEW.md` |
| **用途** | 面向首次接触本项目的读者，全面解说理念、功能和结构的综合指南 |
| **目标读者** | 首次访问者（工程师和非工程师均适用） |
| **主要内容** | ZEO 是什么（与其他工具的对比表）、为什么需要它、基本用法、9 层架构详解、技术栈一览、实现状态、离线运行、核心功能与扩展功能的边界、外部工具集成、设计注意事项、文档一览、目录结构 |

---

### `docs/FEATURES.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/FEATURES.md` |
| **用途** | 全面覆盖所有已实现功能的功能列表 |
| **目标读者** | 功能确认者、评估者、开发者 |
| **主要内容** | 共 27 个章节。9 层架构功能详情、Design Interview、Spec/Plan/Tasks、基于 DAG 的 Task Orchestrator、状态机、Judge Layer、Self-Healing/Re-Propose、审批流程、审计日志、Skill/Plugin/Extension 三层扩展体系、LLM Gateway、前端 UI（23 个画面）、REST API、WebSocket |

---

### `docs/SECURITY.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/SECURITY.md` |
| **用途** | 安全策略和部署前检查清单 |
| **目标读者** | 运维人员、部署负责人 |
| **主要内容** | 支持版本表、漏洞报告方法、部署安全检查清单（SECRET_KEY / JWT_SECRET 生成方法、Cloudflare 认证信息、CORS 设置、生产环境 DB 设置、推荐安全设置） |

---

### `docs/CHANGELOG.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/CHANGELOG.md` |
| **用途** | 按版本记录的变更历史 |
| **目标读者** | 所有用户和开发者 |
| **主要内容** | [Keep a Changelog](https://keepachangelog.com/) 格式。v0.1.0（2026-03-11）和 v0.1.1（2026-03-12）所有新增功能的完整列表 |

---

### `docs/Zero-Employee Orchestrator.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/Zero-Employee Orchestrator.md` |
| **用途** | 项目的**最高级别基准文档**。整合了理念、需求、MVP 定义、运营方针和实现判断标准的权威原典 |
| **目标读者** | 设计者、产品负责人、AI 代理 |
| **主要内容** | Skill / Plugin / Extension 的定义和区别、系统要解决的问题、设计理念、MVP 必需功能与延后功能的整理、状态转换设计、审批流程要求、审计日志要求、扩展体系、Self-Healing DAG 要求 |
| **备注** | 文件名包含空格 |

---

### `docs/SCALING_AND_COSTS.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/SCALING_AND_COSTS.md` |
| **用途** | 汇总成本、硬件约束和大规模项目应用案例的指南 |
| **目标读者** | 引进评估者、运维人员、管理层 |
| **主要内容** | LLM API 成本列表、免费使用范围、硬件要求、v0.1 未实现功能、5 个大规模项目应用案例、成本优化策略 |

---

### `docs/AI_SELF_IMPROVEMENT_ROADMAP.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/AI_SELF_IMPROVEMENT_ROADMAP.md` |
| **用途** | 面向 AI 自我改进（AI 改进和生成 AI 的能力）实现的路线图 |
| **目标读者** | 开发者、贡献者、研究者、认同愿景的人 |
| **主要内容** | AI 自我改进愿景、ZEO 的当前位置与目标距离、个人开发的局限与社区/资金的必要性、4 阶段路线图、ai-self-improvement Plugin 设计、社区扩大策略、未来场景、安全与伦理、费用估算 |

---

### `docs/MD_FILES_INDEX.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/MD_FILES_INDEX.md` |
| **用途** | **本文档**。列出仓库中所有 `.md` 文件的索引 |
| **目标读者** | 所有用户和开发者 |

---

## 3. docs/dev/ — 开发者文档

面向开发者、实现者和 AI 编程代理的文档。

### `docs/dev/DESIGN.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/dev/DESIGN.md` |
| **用途** | 实现设计文档。将结构整理到 AI 编程代理可以直接开始实现的粒度的核心设计规范 |
| **目标读者** | 实现者、AI 代理 |
| **主要内容** | 系统定义、设计原则、DB 表设计（全部列定义）、API 端点列表、状态转换（State Machine）、UI 画面设计、实现阶段（Phase 0-9）、MVP 边界 |

---

### `docs/dev/MASTER_GUIDE.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/dev/MASTER_GUIDE.md` |
| **用途** | 汇总 AI 编程代理实现方法、参考顺序和判断标准的运营指南 |
| **目标读者** | AI 代理、实现负责人 |
| **主要内容** | 6 条最重要规则、各文件角色与用法的对照表、实现阶段的推进方式、禁止事项、判断犹豫时的决策流程 |

---

### `docs/dev/BUILD_GUIDE.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/dev/BUILD_GUIDE.md` |
| **用途** | 按阶段附带代码示例，从零构建 Zero-Employee Orchestrator 的构建指南 |
| **目标读者** | 从源码构建的开发者 |
| **主要内容** | 前提条件、快速设置命令、Phase 0-9 的逐步实现说明、部署步骤 |

---

### `docs/dev/FEATURE_BOUNDARY.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/docs/dev/FEATURE_BOUNDARY.md` |
| **用途** | 明确划分核心功能与 Skill / Plugin / Extension 边界的边界定义文档 |
| **目标读者** | 开发者、设计者 |
| **主要内容** | 边界判断标准、核心功能详细列表、应提取为 Skill/Plugin/Extension 的功能列表 |

---

### 实现指示文件（`instructions_section*`）

实现指示文件是 AI 编程代理在推进各阶段实现时使用的具体指令文档。

| 文件 | 位置 | 内容 |
|------|------|------|
| **instructions_section2_init.md** | `/docs/dev/` | 仓库初始化（目录结构、monorepo 配置、环境构建） |
| **instructions_section3_backend.md** | `/docs/dev/` | FastAPI 后端构建（MVP 优先实现项目、SQLAlchemy 模型、状态机） |
| **instructions_section4_frontend.md** | `/docs/dev/` | React 前端构建（画面列表、组件设计方针、API 连接） |
| **instructions_section5_skills.md** | `/docs/dev/` | Skills / Plugins / Extensions 实现（术语定义、内置 Skill、Registry API） |
| **instructions_section6_tauri.md** | `/docs/dev/` | Tauri 集成与桌面应用化（Sidecar 启动、自动更新） |
| **instructions_section7_test.md** | `/docs/dev/` | 测试与验证（状态转换测试、审批绕过防止测试、安全测试） |

---

## 4. apps/edge/ 文档

### `apps/edge/README.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/apps/edge/README.md` |
| **用途** | Cloudflare Workers 两种部署方式（Proxy / Full Workers）的比较和选择指南 |
| **目标读者** | 部署负责人、基础设施工程师 |

---

### `apps/edge/full/README.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/apps/edge/full/README.md` |
| **用途** | 方式 B（Full Workers）的设置和部署步骤 |
| **目标读者** | 在 Cloudflare Workers 上进行全栈运维的开发者 |

---

### `apps/edge/proxy/README.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/apps/edge/proxy/README.md` |
| **用途** | 方式 A（Proxy）的设置和部署步骤 |
| **目标读者** | 在现有 FastAPI 后端前端部署 Workers 的开发者 |

---

## 5. .github/ 文档

### `.github/SECURITY_SETUP_CHECKLIST.md`

| 项目 | 内容 |
|------|------|
| **位置** | `/.github/SECURITY_SETUP_CHECKLIST.md` |
| **用途** | GitHub Actions 安全设置检查清单 |
| **目标读者** | DevOps、安全负责人 |
| **主要内容** | 必需的 Secrets 和配置项、安全推荐事项 |

---

## 6. docs/en/ 和 docs/zh/ — 多语言文档

`docs/en/`（英语）和 `docs/zh/`（中文）包含以下日语文档的翻译版本：

| 日语原文 | 英语版 | 中文版 |
|---------|--------|--------|
| `docs/ABOUT.md` | `docs/en/ABOUT.md` | `docs/zh/ABOUT.md` |
| `docs/OVERVIEW.md` | `docs/en/OVERVIEW.md` | `docs/zh/OVERVIEW.md` |
| `docs/FEATURES.md` | `docs/en/FEATURES.md` | `docs/zh/FEATURES.md` |
| `docs/SECURITY.md` | `docs/en/SECURITY.md` | `docs/zh/SECURITY.md` |
| `docs/SCALING_AND_COSTS.md` | `docs/en/SCALING_AND_COSTS.md` | `docs/zh/SCALING_AND_COSTS.md` |
| `docs/CHANGELOG.md` | `docs/en/CHANGELOG.md` | `docs/zh/CHANGELOG.md` |
| `docs/MD_FILES_INDEX.md` | `docs/en/MD_FILES_INDEX.md` | `docs/zh/MD_FILES_INDEX.md` |

---

## 7. 文档参考优先级

### 面向开发者和实现者

```
1. docs/Zero-Employee Orchestrator.md  <- 最高级别基准（理念、需求、MVP 定义）
2. docs/dev/DESIGN.md                  <- 实现设计（DB、API、状态转换、实现顺序）
3. docs/dev/MASTER_GUIDE.md            <- 运营指南（推进方式、判断标准、禁止事项）
4. CLAUDE.md                           <- AI 代理开发指南
5. docs/dev/instructions_section2-7    <- 各领域的具体实现指示
```

### 面向用户

```
首次访问者       -> docs/OVERVIEW.md
为什么需要它     -> docs/ABOUT.md
设置             -> docs/USER_GUIDE.md 或 docs/dev/BUILD_GUIDE.md
功能确认         -> docs/FEATURES.md
成本与约束       -> docs/SCALING_AND_COSTS.md
部署             -> apps/edge/README.md + docs/SECURITY.md
变更历史         -> docs/CHANGELOG.md
```

---

*本索引与 `docs/OVERVIEW.md` 第 11 节"文档一览"相对应。*
