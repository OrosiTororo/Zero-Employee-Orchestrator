> [日本語](../MD_FILES_INDEX.md) | [English](../en/MD_FILES_INDEX.md) | 中文

# 仓库内 Markdown 文件索引

> 最后更新: 2026-03-23 (v0.1)
>
> 本文档是 Zero-Employee Orchestrator 仓库中所有 `.md` 文件的概要、用途和目标读者的索引列表。

---

## 目录

1. [根目录文档](#1-根目录文档)
2. [docs/ — 用户文档](#2-docs--用户文档)
3. [docs/dev/ — 开发者文档](#3-docsdev--开发者文档)
4. [apps/edge/ 文档](#4-appsedge-文档)
5. [.github/ 文档](#5-github-文档)
6. [多语言文档](#6-docsen-和-docszh--多语言文档)
7. [文档参考优先级](#7-文档参考优先级)

---

## 1. 根目录文档

### 面向用户

| 文件 | 用途 | 目标读者 | 多语言 |
|------|------|---------|--------|
| `README.md` | 项目第一印象。概述、功能、安装、技术栈 | 所有用户和开发者 | ja/en/zh (内联) |
| `USER_SETUP.md` | ZEO 使用、运维、功能扩展设置指南 | 所有用户 | ja / [en](../en/USER_SETUP.md) / [zh](USER_SETUP.md) |
| `ROADMAP.md` | v0.2 至 v1.0 路线图 | 用户、开发者、贡献者 | ja / [en](../en/ROADMAP.md) / [zh](ROADMAP.md) |
| `CODE_OF_CONDUCT.md` | 社区行为准则 (Contributor Covenant 2.1) | 所有贡献者和用户 | ja / [en](../en/CODE_OF_CONDUCT.md) / [zh](CODE_OF_CONDUCT.md) |
| `CONTRIBUTING.md` | 如何为项目做贡献 | 贡献者、开发者 | ja / [en](../en/CONTRIBUTING.md) / [zh](CONTRIBUTING.md) |
| `SECURITY.md` | 漏洞报告流程 | 安全报告者 | en |

### 面向开发者（根目录）

| 文件 | 用途 | 目标读者 |
|------|------|---------|
| `CLAUDE.md` | Claude Code (AI 代理) 开发指南 | Claude Code |

---

## 2. docs/ — 用户文档

| 文件 | 用途 | 目标读者 | 多语言 |
|------|------|---------|--------|
| `docs/ABOUT.md` | "为什么需要 ZEO" 说明文档 | 非工程师、管理层、评估者 | [en](../en/ABOUT.md) / [zh](ABOUT.md) |
| `docs/USER_GUIDE.md` | 终端用户操作手册 | 终端用户 | ja / [en](../en/USER_GUIDE.md) / [zh](USER_GUIDE.md) |
| `docs/OVERVIEW.md` | 面向初次访问者的综合指南 | 所有人 | [en](../en/OVERVIEW.md) / [zh](OVERVIEW.md) |
| `docs/FEATURES.md` | 已实现功能完整列表（34 个章节） | 功能评审者、评估者、开发者 | [en](../en/FEATURES.md) / [zh](FEATURES.md) |
| `docs/SECURITY.md` | 安全策略和部署前检查清单 | 运维人员、部署工程师 | [en](../en/SECURITY.md) / [zh](SECURITY.md) |
| `docs/CHANGELOG.md` | 版本变更历史 | 所有用户和开发者 | [en](../en/CHANGELOG.md) / [zh](CHANGELOG.md) |
| `docs/SCALING_AND_COSTS.md` | 成本、硬件约束、使用案例 | 潜在用户、运维人员、管理层 | [en](../en/SCALING_AND_COSTS.md) / [zh](SCALING_AND_COSTS.md) |
| `docs/Zero-Employee Orchestrator.md` | **最上层参考文档**。理念、需求、MVP 定义 | 设计者、PO、AI 代理 | ja |
| `docs/MD_FILES_INDEX.md` | **本文档**。所有 `.md` 文件的索引 | 所有用户和开发者 | [en](../en/MD_FILES_INDEX.md) / [zh](MD_FILES_INDEX.md) |

---

## 3. docs/dev/ — 开发者文档

| 文件 | 用途 | 目标读者 |
|------|------|---------|
| `docs/dev/DESIGN.md` | 实现设计（DB、API、状态转换、阶段） | 实现者、AI 代理 |
| `docs/dev/MASTER_GUIDE.md` | AI 实现方法、参考顺序、决策标准 | AI 代理、实现负责人 |
| `docs/dev/BUILD_GUIDE.md` | 从零构建指南（分阶段） | 从源码构建的开发者 |
| `docs/dev/FEATURE_BOUNDARY.md` | 核心功能 vs Skill/Plugin/Extension 边界定义 | 开发者、设计者 |
| `docs/dev/DEVELOPER_SETUP.md` | 开发者设置（Sentry、红队测试等） | ZEO 开发者 |
| `docs/dev/SKILL.md` | SKILL.md 文件创建指南 | Skill 开发者 |
| `docs/dev/Progressive.md` | CLAUDE.md 编写方法论 | 开发者 |
| `docs/dev/PROPOSAL.md` | 项目提案书 | 资助审查员、赞助商 |
| `docs/dev/TITLE_PROPOSALS.md` | 项目标题提案 | 项目相关人员 |
| `docs/dev/AI_SELF_IMPROVEMENT_ROADMAP.md` | AI 自我改进路线图 | 开发者、研究人员 |

### 实现指令文件 (`instructions_section*`)

| 文件 | 内容 |
|------|------|
| `docs/dev/instructions_section2_init.md` | 仓库初始化（目录结构、monorepo、环境） |
| `docs/dev/instructions_section3_backend.md` | FastAPI 后端构建 |
| `docs/dev/instructions_section4_frontend.md` | React 前端构建 |
| `docs/dev/instructions_section5_skills.md` | Skills / Plugins / Extensions 实现 |
| `docs/dev/instructions_section6_tauri.md` | Tauri 集成和桌面应用打包 |
| `docs/dev/instructions_section7_test.md` | 测试和验证 |

---

## 4. apps/edge/ 文档

| 文件 | 用途 | 目标读者 |
|------|------|---------|
| `apps/edge/README.md` | Cloudflare Workers 部署方式比较（Proxy / Full） | 部署工程师 |
| `apps/edge/full/README.md` | Full Workers 设置和部署 | CF Workers 开发者 |
| `apps/edge/proxy/README.md` | Proxy 方式设置和部署 | CF Workers 开发者 |

---

## 5. .github/ 文档

| 文件 | 用途 | 目标读者 |
|------|------|---------|
| `.github/SECURITY_SETUP_CHECKLIST.md` | GitHub Actions 安全设置检查清单 | DevOps、安全工程师 |

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
| `docs/USER_GUIDE.md` | `docs/en/USER_GUIDE.md` | `docs/zh/USER_GUIDE.md` |
| `USER_SETUP.md` | `docs/en/USER_SETUP.md` | `docs/zh/USER_SETUP.md` |
| `ROADMAP.md` | `docs/en/ROADMAP.md` | `docs/zh/ROADMAP.md` |
| `CODE_OF_CONDUCT.md` | `docs/en/CODE_OF_CONDUCT.md` | `docs/zh/CODE_OF_CONDUCT.md` |
| `CONTRIBUTING.md` | `docs/en/CONTRIBUTING.md` | `docs/zh/CONTRIBUTING.md` |

---

## 7. 文档参考优先级

### 开发者和实现者

```
1. docs/Zero-Employee Orchestrator.md  <- 最上层参考（理念、需求、MVP 定义）
2. docs/dev/DESIGN.md                  <- 实现设计（DB、API、状态转换）
3. docs/dev/MASTER_GUIDE.md            <- 运营指南（方法、标准、禁止事项）
4. CLAUDE.md                           <- AI 代理开发指南
5. docs/dev/instructions_section2-7    <- 各领域具体实现指令
```

### 用户

```
初次访问  -> docs/OVERVIEW.md
为什么需要 -> docs/ABOUT.md
设置      -> USER_SETUP.md 或 docs/USER_GUIDE.md
功能确认   -> docs/FEATURES.md
成本和约束 -> docs/SCALING_AND_COSTS.md
部署      -> apps/edge/README.md + docs/SECURITY.md
变更历史   -> docs/CHANGELOG.md
```

---

*本索引与 `docs/OVERVIEW.md` 第 11 节"文档列表"对应。*
