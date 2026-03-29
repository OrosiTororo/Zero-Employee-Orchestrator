> [日本語](../ja-JP/FEATURES.md) | [English](../FEATURES.md) | 中文

# Zero-Employee Orchestrator — 功能一览

> 最后更新：2026-03-28
> 当前版本：v0.1.1

---

## 概述

Zero-Employee Orchestrator 是一个 **AI 编排平台**，可通过自然语言定义业务，将多个 AI 代理分配不同角色，在人工审批和可审计性的前提下执行、重新规划和改进业务。

本文档全面汇总了当前已实现的功能及其能力。

---

## v0.1.1 新功能 (2026-03-28)

| 领域 | 变更内容 |
|------|---------|
| **生产部署** | Docker Compose 添加资源限制、网络隔离、只读 FS、日志轮转 |
| **CI 安全** | 添加 Trivy 容器扫描、阻塞式 pip-audit、Red-team 测试任务 |
| **Red-team 测试** | 全部 22 个测试现在使用真实载荷执行实际安全模块 |
| **多语言** | 6 种语言 65+ 翻译键（EN/JA/ZH/KO/PT/TR），默认语言改为英语 |
| **模型目录** | 更新至 GPT、Llama、Phi、Claude Haiku 的最新版 |
| **PII 防护** | 全部 13 个类别均有检测模式（添加驾驶证、日语姓名） |
| **文档** | 修正所有夸大数值，7 种语言版本保持一致 |

---

## 目录

1. [9 层架构](#1-9-层架构)
2. [自然语言输入与 Design Interview](#2-自然语言输入与-design-interview)
3. [Spec / Plan / Tasks — 结构化中间产物](#3-spec--plan--tasks--结构化中间产物)
4. [基于 DAG 的 Task Orchestrator](#4-基于-dag-的-task-orchestrator)
5. [基于状态机的严格生命周期管理](#5-基于状态机的严格生命周期管理)
6. [Judge Layer — 质量保证与验证](#6-judge-layer--质量保证与验证)
7. [Cost Guard — 成本估算与预算控制](#7-cost-guard--成本估算与预算控制)
8. [Quality SLA — 质量模式与模型选择](#8-quality-sla--质量模式与模型选择)
9. [Self-Healing / Re-Propose — 故障时的自动恢复与重新规划](#9-self-healing--re-propose--故障时的自动恢复与重新规划)
10. [Failure Taxonomy — 故障分类与学习](#10-failure-taxonomy--故障分类与学习)
11. [Experience Memory — 经验知识的积累与复用](#11-experience-memory--经验知识的积累与复用)
12. [审批流程](#12-审批流程)
13. [审计日志](#13-审计日志)
14. [代理管理](#14-代理管理)
15. [Skill / Plugin / Extension — 三层扩展体系](#15-skill--plugin--extension--三层扩展体系)
16. [LLM Gateway — 多供应商支持](#16-llm-gateway--多供应商支持)
17. [后台 Worker](#17-后台-worker)
18. [Heartbeat — 定时执行与健康监控](#18-heartbeat--定时执行与健康监控)
19. [组织管理（公司/部门/团队）](#19-组织管理公司部门团队)
20. [权限模型](#20-权限模型)
21. [前端 UI](#21-前端-ui)
22. [REST API](#22-rest-api)
23. [WebSocket 实时通信](#23-websocket-实时通信)
24. [Observability — 推理追踪、通信日志、执行监控](#24-observability--推理追踪通信日志执行监控)
25. [Cloudflare Workers 部署](#25-cloudflare-workers-部署)
26. [桌面应用 (Tauri)](#26-桌面应用-tauri)
27. [CLI / TUI](#27-cli--tui)
28. [外部工具集成](#28-外部工具集成-v01)
29. [社区插件共享](#29-社区插件共享-v01)
30. [AI 自我改进 — Level 2](#30-ai-self-improvement--level-2-自我改进的萌芽-v01)
31. [v0.1 功能膨胀审查](#31-v01-功能膨胀审查--核心与扩展的边界)
32. [元技能概念](#32-元技能概念-v01)
33. [通过文件附件创建计划](#33-通过文件附件创建计划-v01)
34. [安全增强](#34-安全增强-v01)
35. [RSS/ToS 自动更新管道](#35-rstos-自动更新管道-v01)
36. [Knowledge Refresh — 上下文窗口管理](#36-knowledge-refresh--上下文窗口管理-v01)
37. [A2A 双向通信](#37-a2a-双向通信-v01)
38. [Avatar AI Co-evolution — 与用户共同进化](#38-avatar-ai-co-evolution--与用户共同进化-v01)
39. [Longrun Scheduler — 24/365 持续执行](#39-longrun-scheduler--24365-持续执行-v01)
40. [Agent Session — 上下文持久化](#40-agent-session--上下文持久化-v01)
41. [Artifact Bridge — 跨阶段产物连接](#41-artifact-bridge--跨阶段产物连接-v01)
42. [媒体生成集成](#42-媒体生成集成-v01)
43. [AI 工具注册表](#43-ai-工具注册表-v01)
44. [iPaaS 集成 — 工作流编排](#44-ipaas-集成--工作流编排-v01)
45. [产物导出](#45-产物导出-v01)
46. [AI 共创内容再利用引擎](#46-ai-共创内容再利用引擎-v01)
47. [Obsidian 集成](#47-obsidian-集成-v01)
48. [云原生集成](#48-云原生集成-v01)
49. [智能设备 / VR/AR 集成](#49-智能设备--vrar-集成-v01)
50. [治理与合规](#50-治理与合规-v01)
51. [Skill 市场](#51-skill-市场-v01)
52. [多用户与团队管理](#52-多用户与团队管理-v01)
53. [Red-team 安全测试](#53-red-team-安全测试-v011)
54. [工作区隔离](#54-工作区隔离-v01)
55. [Design Interview 历史失败模式反馈](#55-design-interview-历史失败模式反馈-v01)
56. [前提变化通用监控 — Prerequisite Monitor](#56-前提变化通用监控--prerequisite-monitor-v01)
57. [Spec 间矛盾检测](#57-spec-间矛盾检测--spec-contradiction-detector-v01)
58. [任务执行回放与比较](#58-任务执行回放与比较--task-replay--comparison-v01)
59. [用户判断回顾报告](#59-用户判断回顾报告--judgment-review-v01)
60. [目标→Plan 分解质量验证](#60-目标plan-分解质量验证--plan-quality-verifier-v01)
61. [多模型比较](#61-多模型比较-v01)
62. [头脑风暴会话](#62-头脑风暴会话-v01)
63. [对话记忆 — Conversation Memory](#63-对话记忆--conversation-memory-v01)
64. [文本分析服务](#64-文本分析服务-v01)
65. [基于角色的模型配置](#65-基于角色的模型配置-v01)
66. [AI 组织动态管理](#66-ai-组织动态管理-v01)
67. [自定义代理角色](#67-自定义代理角色-v01)
68. [自然语言功能请求](#68-自然语言功能请求-v01)
69. [脑暴转储 / Secretary AI](#69-脑暴转储--secretary-ai-v01)
70. [文件上传管理](#70-文件上传管理-v01)
71. [任务执行中的用户输入](#71-任务执行中的用户输入-v01)
72. [资源导入](#72-资源导入-v01)
73. [项目与目标管理](#73-项目与目标管理-v01)
74. [假设引擎 — Hypothesis Engine](#74-假设引擎--hypothesis-engine-v01)
75. [AI 调查引擎 — AI Investigator](#75-ai-调查引擎--ai-investigator-v01)
76. [浏览器自动化 — Browser Automation](#76-浏览器自动化--browser-automation-v01)
77. [LSP 集成 — Language Server Protocol](#77-lsp-集成--language-server-protocol-v01)
78. [MCP 集成 — Model Context Protocol](#78-mcp-集成--model-context-protocol-v01)
79. [外部技能搜索与导入](#79-外部技能搜索与导入-v01)
80. [输入安全中间件](#80-输入安全中间件-v01)

---

## 1. 9 层架构

Zero-Employee Orchestrator 采用以下 9 层结构进行设计和实现。

| 层级 | 名称 | 职责 |
|------|------|------|
| Layer 1 | **User Layer** | GUI / CLI / TUI / 聊天输入。通过自然语言启动 AI 组织 |
| Layer 2 | **Design Interview** | 生成深度挖掘需求的问题并积累回答。结构化 Spec |
| Layer 3 | **Task Orchestrator** | Plan/DAG 生成、Skill 分配、成本估算、重新规划 |
| Layer 4 | **Skill Layer** | 单一目的专业 Skill 执行 + Local Context Skill |
| Layer 5 | **Judge Layer** | Two-stage Detection + Cross-Model Verification |
| Layer 6 | **Re-Propose Layer** | 被驳回时的重新提案 + 动态 DAG 重建 |
| Layer 7 | **State & Memory** | 状态机 + Experience Memory + Failure Taxonomy |
| Layer 8 | **Provider Interface** | 通过 LiteLLM Gateway 实现多 LLM 连接 |
| Layer 9 | **Skill Registry** | Skill / Plugin / Extension 的发布、搜索与安装 |

---

## 2. 自然语言输入与 Design Interview

### 自然语言输入

可以从仪表板以自然语言提交业务请求。

```
示例："创建一份竞品分析报告，整理成下周会议的材料"
```

输入内容将注册为 Ticket，并自动启动 Design Interview。

### Design Interview

使用 7 个标准问题模板对需求进行结构化深度挖掘。

| 类别 | 问题示例 |
|------|---------|
| **目标** | 这项业务的最终目标是什么？ |
| **约束** | 是否有需要遵守的约束条件？（预算、期限、质量标准等） |
| **验收标准** | 完成条件（验收标准）是什么？ |
| **风险** | 是否有预期的风险或注意事项？ |
| **优先级** | 优先级如何？（高/中/低） |
| **外部集成** | 是否需要连接或发送到外部服务？ |
| **审批环节** | 是否有需要人工审批的环节？ |

回答完成后，可以从 Interview 的回答中自动生成 Spec（规格文档）。

### 通过文件附件输入上下文

可以在 Design Interview 中附加文件，作为规格文档生成的上下文进行整合。

| 文件类型 | 支持格式 | 处理方法 |
|---------|---------|---------|
| **文本** | `.txt`, `.md`, `.csv`, `.json`, `.yaml`, `.xml`, `.html` | 文本提取（自动检测多种编码） |
| **代码** | `.py`, `.ts`, `.js`, `.java`, `.go`, `.rs`, `.c`, `.cpp` 等 | 作为源代码解析 |
| **图片** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg` | Base64 编码 + 元数据提取 |
| **文档** | `.pdf` | 元信息提取 |

```
POST /api/v1/tickets/{ticket_id}/interview/attach
Content-Type: multipart/form-data

file: (附件)
description: "竞争分析报告的源数据"
```

从附件中提取的文本将自动整合为 Spec 的「参考资料」部分。

---

## 3. Spec / Plan / Tasks — 结构化中间产物

所有业务请求都以结构化中间产物的形式保存，而非"对话日志"。

### Spec（规格文档）

- **目标** (`objective`)：业务的最终目标
- **约束条件** (`constraints_json`)：预算、期限、质量标准
- **验收标准** (`acceptance_criteria_json`)：判断完成的标准
- **风险说明** (`risk_notes`)：预期风险
- **版本管理**：规格变更时记录版本

### Plan（执行计划）

- 基于 Spec 生成的执行计划
- 包含成本估算
- 包含审批流程（仅在审批通过后才生成任务）

### Tasks（个别任务）

- 从 Plan 分解出的各执行单元
- 通过 DAG（有向无环图）管理依赖关系
- 每个任务分配负责代理、预估成本和预估时间

---

## 4. 基于 DAG 的 Task Orchestrator

通过 DAG（有向无环图）管理任务依赖关系，自动确定最优执行顺序。

### 主要功能

| 功能 | 说明 |
|------|------|
| **Ready 节点检测** | 当所有依赖任务完成时，自动将任务标记为可执行状态 |
| **关键路径计算** | 计算最长路径的所需时间，提供完成预测 |
| **总成本估算** | 汇总整个 DAG 的预估成本 |
| **审批点检测** | 识别需要人工审批的任务 |
| **Self-Healing DAG** | 故障时动态重建 DAG（retry / skip / replan） |

### Self-Healing 策略

```
retry   -> 将失败节点重置为 pending 并重试
skip    -> 跳过失败节点，解除依赖节点的约束
replace -> 创建替代路径（需要外部逻辑）
replan  -> 触发整个 DAG 的重新规划
```

---

## 5. 基于状态机的严格生命周期管理

4 种状态机严格管理所有资源的生命周期。

### Ticket 状态转换

```
draft -> open -> interviewing -> planning -> ready -> in_progress -> review -> done -> closed
                                                          |              |         |
                                                       blocked        rework    reopened
```

### Task 状态转换

```
pending -> ready -> running -> succeeded -> verified -> archived
                      |            |
                 awaiting_approval failed -> retrying -> running
                      |
                   blocked
```

### Approval 状态转换

```
requested -> approved -> executed
          -> rejected -> superseded
          -> expired  -> requested（重新请求）
          -> cancelled
```

### Agent 状态转换

```
provisioning -> idle -> busy -> idle
                 |      |
              paused   error -> idle / paused / decommissioned
                 |
          decommissioned
```

所有状态转换都记录为历史，非法转换将作为错误被阻止。

---

## 6. Judge Layer — 质量保证与验证

实现了 3 阶段的质量验证机制。

### Stage 1：RuleBasedJudge（基于规则的一级判定）

- 支持动态添加自定义规则
- 快速一级过滤
- 按严重程度评分（error: -0.2 / warning: -0.05）

### Stage 2：PolicyPackJudge（策略合规检查）

**危险操作检测：**

| 检测对象 |
|---------|
| `external_send` — 外部发送 |
| `publish` / `post` — 发布/发帖 |
| `delete` — 删除 |
| `charge` — 计费 |
| `git_push` / `git_release` — Git 操作 |
| `permission_change` — 权限变更 |
| `credential_update` — 凭证更新 |

**凭证泄露检查：**

- 检测以下模式：`sk-`、`Bearer`、`api_key=`、`password=`、`secret=`、`token=`、`AKIA`

### Stage 3：CrossModelJudge（Cross-Model Verification）

- 比较多个 LLM 的输出以验证可靠性
- 结构一致性和值一致性评分
- 在 HIGH / CRITICAL 质量模式下使用

### 判定结果

| 判定 | 含义 |
|------|------|
| `PASS` | 通过 |
| `WARN` | 有警告（可继续） |
| `FAIL` | 不通过（停止执行） |
| `NEEDS_REVIEW` | 需要人工审查 |

---

## 7. Cost Guard — 成本估算与预算控制

### 成本估算

按模型系列的 Token 单价在 `model_catalog.json` 中管理，并在执行前进行成本估算。
成本信息从模型目录动态加载，因此模型变更时无需修改代码。

> **价格在 `model_catalog.json` 中动态管理，并通过 RSS/ToS 监控管道自动更新。**
> 当前价格可通过 `GET /api/v1/models` 查看，或直接参考 `model_catalog.json`。
> 也可通过 API（`POST /api/v1/models/update-cost`）或直接编辑文件手动更新。

### 预算检查

| 判定 | 条件 | 操作 |
|------|------|------|
| `ALLOW` | 使用率 < 80% | 允许执行 |
| `WARN` | 80% ≤ 使用率 < 100% | 带警告允许 |
| `BLOCK` | 使用率 ≥ 100% | 阻止执行 |

### 预算策略管理（UI）

- 按日/周/月设置预算上限
- 达到阈值时自动停止任务
- 通过成本台账按交易单位跟踪

---

## 8. Quality SLA — 质量模式与模型选择

根据任务重要性提供 4 种质量模式。

| 模式 | 推荐模型 | 最大重试次数 | Judge 阈值 | 人工审查 | Cross-Model Verification |
|------|---------|------------|-----------|---------|------------------------|
| **DRAFT** | GPT Mini, Claude Haiku | 1 次 | 50% | 不需要 | 无 |
| **STANDARD** | GPT, Claude Sonnet | 2 次 | 70% | 不需要 | 无 |
| **HIGH** | GPT, Claude Sonnet | 3 次 | 85% | 不需要 | **有** |
| **CRITICAL** | Claude Opus, GPT | 5 次 | 95% | **必须** | **有** |

模型选择、重试策略和验证级别会根据质量模式自动调整。
推荐模型从 `model_catalog.json` 加载，因此模型更新时只需编辑文件即可。

---

## 9. Self-Healing / Re-Propose — 故障时的自动恢复与重新规划

### Re-Propose（重新提案）

在失败或被驳回时，对原因进行分类并生成替代方案。

| 失败类别 | 说明 |
|---------|------|
| `quality_insufficient` | 未达到质量标准 |
| `scope_mismatch` | 与需求不匹配 |
| `cost_exceeded` | 超出预算 |
| `policy_violation` | 违反策略 |
| `execution_error` | 运行时错误 |
| `timeout` | 超时 |
| `skill_gap` | 缺少所需的 Skill |
| `dependency_broken` | 依赖关系断裂 |
| `model_incompatible` | 因模型特性导致不兼容 |

### Plan Diff

重新提案时，将以结构化方式展示与原始计划的差异（添加、删除、修改的任务，成本变动，时间变动）。

### 混沌测试（v0.1）

实现了混沌测试套件，用于验证 Self-Healing DAG 的可靠性。

| 测试类别 | 测试数 | 验证内容 |
|---------|-------|---------|
| 单节点故障 | 6 | 验证 retry / skip / replan 各策略的行为 |
| 多节点故障 | 4 | 验证级联故障和并行分支故障 |
| 恢复时间 | 3 | 测量恢复成功率和恢复时间 |
| DAG 完整性 | 4 | 验证恢复后 DAG 结构的一致性 |
| 边界情况 | 4 | 空 DAG、单节点 DAG、循环依赖等 |
| 基准测试 | 3 | 100 次随机故障的恢复统计 |

---

## 10. Failure Taxonomy — 故障分类与学习

实现了 9 个类别 x 4 个严重程度的故障分类体系。

### 故障类别

| 类别 | 说明 |
|------|------|
| `LLM_ERROR` | LLM 供应商故障 |
| `TOOL_ERROR` | 工具执行故障 |
| `VALIDATION_ERROR` | 输入/输出验证故障 |
| `BUDGET_ERROR` | 超出预算 |
| `TIMEOUT_ERROR` | 超时 |
| `PERMISSION_ERROR` | 权限不足 |
| `DEPENDENCY_ERROR` | 依赖任务故障 |
| `HUMAN_REJECTION` | 被人工驳回 |
| `SYSTEM_ERROR` | 系统内部错误 |

### 严重程度级别

| 严重程度 | 含义 | 响应 |
|---------|------|------|
| `LOW` | 轻微 | 可通过自动重试恢复 |
| `MEDIUM` | 中等 | 可通过替代手段恢复 |
| `HIGH` | 严重 | 需要人工介入 |
| `CRITICAL` | 致命 | 立即升级 |

### 学习功能

- 跟踪故障发生次数
- 自动计算恢复成功率
- 检测频发的故障模式
- 跟踪预防措施的有效性

---

## 11. Experience Memory — 经验知识的积累与复用

从过去的执行历史中提取和保存可复用的知识。

### 记忆类型

| 类型 | 用途 |
|------|------|
| `conversation_log` | 对话日志 |
| `reusable_improvement` | 可复用的改进知识 |
| `experimental_knowledge` | 实验性知识 |
| `verified_knowledge` | 已验证知识 |

### 功能

- 积累成功模式（`add_success_pattern`）
- 学习故障模式（`add_failure`）
- 关键词/类别搜索（`search`）
- 提取频发故障（`get_frequent_failures`）

---

## 12. 审批流程

危险操作不会自主执行，必须请求人工审批。

### 需要审批的操作

| 操作 | 示例 |
|------|------|
| 外部发送 | 邮件发送、API 调用 |
| 发布/发帖 | SNS 发帖、博客发布 |
| 删除 | 数据删除、文件删除 |
| 计费 | API 使用费产生 |
| 权限变更 | 用户权限变更 |
| Git 操作 | push、release |
| 凭证更新 | API 密钥变更 |

### 审批 UI

- 待审批队列列表显示
- 风险级别显示（Low / Medium / High / Critical）
- 一键审批/驳回按钮
- 审批结果记录到审计日志

---

## 13. 审计日志

以可追溯的格式记录所有重要操作。

### 记录的信息

| 字段 | 说明 |
|------|------|
| `actor_type` | user / agent / system |
| `event_type` | 操作类型（例：`task.started`、`approval.requested`） |
| `target_type` | 目标资源类型 |
| `target_id` | 目标资源 ID |
| `details_json` | 附加详细信息（JSON） |
| `trace_id` | 分布式追踪 ID |

### 主要事件类型

- `ticket.created` / `ticket.updated`
- `approval.requested` / `approval.granted` / `approval.rejected`
- `agent.assigned` / `agent.completed`
- `task.started` / `task.succeeded` / `task.failed`
- `cost.incurred`
- `auth.login` / `auth.logout`
- `dangerous_operation.*`（危险操作）
- `*.status_changed`（状态转换）

### 专用辅助函数

- `record_audit_event` — 通用审计事件记录
- `record_state_change` — 状态转换记录
- `record_dangerous_operation` — 危险操作记录

---

## 14. 代理管理

将 AI 代理作为组织的团队成员进行管理。

### 代理属性

| 属性 | 说明 |
|------|------|
| `agent_type` | 代理角色类型 |
| `autonomy_level` | 自主性级别 |
| `can_delegate` | 向其他代理委派的权限 |
| `can_write_external` | 外部写入权限 |
| `can_spend_budget` | 预算使用权限 |
| `budget_policy_id` | 关联的预算策略 |
| `heartbeat_policy_id` | 关联的 Heartbeat 策略 |

### 代理操作

- 预配置（新建）
- 激活（启用）
- 暂停/恢复
- 状态转换验证

---

## 15. Skill / Plugin / Extension — 三层扩展体系

提供将核心与业务逻辑明确分离的三层扩展体系。

### Skill（最小能力单元）

执行单一任务的最小单元。包含提示词、流程、脚本和约束。

```
示例：竞品分析、脚本生成、文件整理、本地上下文理解
```

### Plugin（业务功能包）

将多个 Skill 和辅助功能打包的业务功能包。

| Plugin | 用途 | 状态 |
|--------|------|------|
| `ai-avatar`（分身 AI） | 学习用户的判断标准和文体，代理行动 | 已有 manifest |
| `ai-secretary`（AI 秘书） | 简报、优先级建议、与 AI 组织的桥梁 | 已有 manifest |
| `discord-bot` | 从 Discord 进行多代理操作和对话 | 已有 manifest (v0.2.0) |
| `slack-bot` | 从 Slack 进行多代理操作和对话 | 已有 manifest (v0.2.0) |
| `line-bot` | 从 LINE 进行多代理操作 | 已有 manifest |
| `youtube` | YouTube 频道运营 | 已有 manifest |
| `research` | 竞品分析、市场调研 | 已有 manifest |
| `backoffice` | 财务、行政、文档管理 | 已有 manifest |
| `ai-self-improvement` | AI 自我改进（Skill 分析、改进建议、A/B 测试） | **v0.1 已实现**（6 技能 + API） |

### Extension（环境扩展）

扩展核心运行环境、UI 和连接目标的机制。

| Extension | 用途 | 状态 |
|-----------|------|------|
| `oauth` | Google / GitHub 等 OAuth 认证 | 已有 manifest |
| `mcp` | Model Context Protocol 兼容工具连接 | 已有 manifest |
| `notifications` | Slack / Discord / LINE / 邮件通知 | 已有 manifest |
| `obsidian` | 与 Obsidian Vault 双向集成 | 已有 manifest |

### 注册中心功能

- Skill / Plugin / Extension 搜索
- 发布（publish）和安装（install）
- 状态管理（Verified / Experimental / Private / Deprecated）
- 版本管理

---

## 16. LLM Gateway — 多供应商支持

基于 LiteLLM 的统一 LLM 网关，支持多个供应商。

### 支持的供应商

| 供应商 | 支持模型示例 |
|--------|------------|
| **OpenRouter** | 通过单一 API 密钥使用多个模型 |
| **OpenAI** | GPT、GPT Mini |
| **Anthropic** | Claude Opus、Sonnet、Haiku |
| **Google** | Gemini Pro、Flash、Flash Lite |
| **DeepSeek** | DeepSeek Chat |
| **Ollama** | Llama、Mistral、Phi、Qwen 等（本地免费） |
| **g4f** | 通过免费供应商（无需 API 密钥） |

> **支持的模型在 `model_catalog.json` 中管理。**
> 模型的添加、删除、废弃和后继指定可以通过编辑此文件或
> 通过 Model Registry API（`/api/v1/models/*`）来完成。

### 执行模式

| 模式 | 说明 | 推荐模型 |
|------|------|---------|
| `QUALITY` | 最高质量 | Claude Opus、GPT |
| `SPEED` | 快速响应 | Claude Haiku、GPT Mini |
| `COST` | 低成本 | Claude Haiku、GPT Mini、DeepSeek |
| `FREE` | 免费（本地 + 免费 API） | Ollama、Gemini 免费额度、g4f |
| `SUBSCRIPTION` | 免费（无需 API 密钥） | 通过 g4f 的各种模型 |

### 功能

- **动态模型目录**（`model_catalog.json`）— 添加、废弃或更新模型成本无需修改代码
- **自定义模型注册** — 通过 `POST /api/v1/models/add` 添加默认目录中没有的任何 LLM 模型（支持 LiteLLM、OpenRouter、Ollama、vLLM、自定义端点）
- **旧版模型支持** — 已废弃但仍在运行的模型（如 GPT-4o、Gemini 2.5）可通过 `?tag=legacy&include_deprecated=true` 使用
- **模型废弃时的自动回退** — 通过 deprecated 标志 + successor 自动切换到后继模型
- **供应商健康检查** — 定期确认 API 可用性，避免使用不可用的模型
- 自动模型选择（基于执行模式）
- 成本估算（与目录联动）
- 工具调用（Function Calling）支持
- 视觉（图像输入）支持标志
- 回退（LiteLLM 未部署时的模拟响应）
- Ollama 模型自动检测
- 模型删除：`DELETE /api/v1/models/{model_id}`

---

## 17. 后台 Worker

独立于主 API 进程运行的后台任务执行引擎。

### 组件

| 组件 | 职责 |
|------|------|
| **TaskRunner** | 轮询并执行 ready 状态的任务 |
| **HeartbeatRunner** | 基于定时策略执行定期任务 |
| **EventDispatcher** | 通过 WebSocket 实时分发事件 |

### TaskRunner 执行管线

1. 从数据库获取 `status='ready'` 的任务
2. 根据 `task_type` 选择执行器（LLM / Sandbox）
3. 执行任务
4. 通过 Judge 验证输出质量
5. 成功 -> `succeeded` / 失败 -> 重试（最多 3 次）
6. 记录审计日志

### 执行器

| 执行器 | 目标任务 |
|--------|---------|
| **LLMExecutor** | 使用 LLM 的任务，如生成、分析、翻译等 |
| **SandboxExecutor** | Python 代码的安全执行（带内存、CPU 和时间限制） |

### SandboxExecutor 限制

| 限制 | 默认值 |
|------|--------|
| 内存上限 | 256 MB |
| CPU 时间上限 | 30 秒 |
| 网络访问 | 禁用 |

---

## 18. Heartbeat — 定时执行与健康监控

### Heartbeat 策略

- 通过 Cron 表达式定义执行计划
- 抖动设置（执行时间的偏差）
- 并行执行许可设置
- 启用/禁用切换

### 执行历史

- 每次执行的成功/失败状态
- 执行时间记录
- 仪表板上的健康指标显示

---

## 19. 组织管理（公司/部门/团队）

### 组织层级

```
Company（公司）
├── Department（部门）
│   ├── 企划与战略
│   ├── 开发
│   ├── 市场营销
│   └── 客户支持
└── Team（团队）
    └── 按任务动态编组
```

### 功能

- 公司创建与管理
- 部门与团队创建
- 代理分配到部门
- 组织架构图（Org Chart）可视化
- 仪表板上的组织摘要显示

---

## 20. 权限模型

通过 5 个角色控制权限。

| 角色 | 权限 |
|------|------|
| **Owner** | 全部权限（包括预算、审批和发布设置） |
| **Admin** | 组织设置、部分审批、审计日志查看 |
| **User** | 业务请求、计划查看、产物查看 |
| **Auditor** | 仅执行历史和审计日志查看 |
| **Developer** | Skill / Plugin / Extension 开发 |

### 自主执行边界

| 可自主执行 | 需要审批 |
|-----------|---------|
| 调研/分析 | 发布/发帖 |
| 草稿创建 | 计费/删除 |
| 信息整理 | 权限变更/外部发送 |

---

## 21. 前端 UI

使用 React 19 + TypeScript + Tailwind CSS 构建的 20 多个页面。

### 主要页面

| 页面 | 功能 |
|------|------|
| **仪表板** | 统计显示、自然语言输入、快速导航 |
| **登录** | 邮箱/密码认证 |
| **初始设置** | 首次引导 |
| **工单列表** | 带筛选的工单管理 |
| **工单详情** | 单个工单的状态与历史 |
| **Design Interview** | 结构化访谈 UI |
| **Spec/Plan** | 规格与计划的审查/审批 |
| **审批队列** | 带风险级别的审批管理 |
| **Skill 管理** | Skill 浏览与创建 |
| **Plugin 管理** | Plugin 浏览与安装 |
| **产物** | 生成输出的管理 |
| **审计日志** | 带高级筛选的日志查看器 |
| **成本管理** | 预算策略与支出跟踪 |
| **Heartbeat** | 定时执行策略与历史 |
| **组织架构图** | 部门、团队和代理的可视化 |
| **设置** | 用户设置与外部连接管理 |
| **版本发布** | 版本历史 |
| **下载** | 桌面应用下载 |

---

## 22. REST API

在 `/api/v1` 前缀下提供 41 个路由模块、350 个以上的端点。

### 端点分组

| 分组 | 端点数量 | 主要操作 |
|------|---------|---------|
| `/auth` | 6 | 注册、登录、OAuth、登出、用户信息 |
| `/companies` | 10+ | 公司 CRUD、仪表板、组织架构图、部门/团队 |
| `/tickets` | 10+ | 工单 CRUD、状态转换、评论、线程 |
| `/tickets/{id}/interview` | 3 | 访谈获取、回答、Spec 自动生成 |
| `/tickets/{id}/specs` | 2 | Spec 列表与创建 |
| `/tickets/{id}/plans` | 2 | Plan 列表与创建 |
| `/plans/{id}` | 3 | 审批、驳回、任务列表 |
| `/tasks` | 6 | 创建、开始、完成、重试、审批请求、执行历史 |
| `/agents` | 5 | 列表、创建、详情、暂停、恢复 |
| `/approvals` | 3 | 列表、审批、驳回 |
| `/artifacts` | 2 | 列表、创建 |
| `/audit` | 1 | 带筛选的日志获取 |
| `/heartbeats` | 3 | 策略 CRUD、执行历史 |
| `/budgets` | 3 | 策略 CRUD、成本摘要 |
| `/registry` | 6 | Skill / Plugin / Extension 搜索与安装 |
| `/projects` | 4 | 项目 CRUD、目标管理 |
| `/settings` | 6 | LLM API 密钥设置、执行模式、公司设置、工具连接管理 |
| `/health` | 2 | 健康检查（liveness / readiness） |
| `/models` | 7 | 模型目录管理、健康检查、废弃管理 |
| `/traces` | 4 | 推理追踪列表、详情、决策提取 |
| `/communications` | 5 | 代理间通信、升级、线程 |
| `/monitor` | 4 | 执行监控仪表板、活跃任务、事件 |

---

## 23. WebSocket 实时通信

`/ws/events` 端点提供实时事件流。

- 任务进度更新
- 审批请求通知
- 代理状态变更
- 错误和故障即时通知
- **推理追踪的实时推送** — 逐步推送代理的思考过程
- **代理间通信推送** — 实时显示委派、反馈和升级
- **执行监控事件** — 实时显示任务进度、模型选择和 Judge 判定

---

## 24. Observability — 推理追踪、通信日志、执行监控

消除多代理业务黑盒化的可观测性功能群。

### 24.1 推理追踪 (Reasoning Trace)

逐步记录代理**为何做出该决策**。

| 步骤类型 | 说明 |
|---------|------|
| `context_gathering` | 从信息源收集上下文 |
| `knowledge_retrieval` | 从 Experience Memory / RAG 检索知识 |
| `option_enumeration` | 列举选项 |
| `option_evaluation` | 评估和评分各选项 |
| `decision` | 最终决策（包含选择的选项、理由和置信度） |
| `model_selection` | LLM 模型选择理由 |
| `judge_result` | Judge Layer 判定结果 |
| `error_analysis` | 错误原因分析 |
| `fallback_decision` | 回退策略选择 |

每个步骤都带有**置信度**（high / medium / low / uncertain），
可定量评估决策的可靠性。

### 24.2 代理间通信日志 (Agent Communication)

记录多代理协作时的**全部消息交换**。

| 消息类型 | 说明 |
|---------|------|
| `delegation` / `delegation_accept` / `delegation_reject` | 任务委派 |
| `artifact_handoff` | 产物交接 |
| `feedback` / `question` / `answer` | 沟通 |
| `quality_review` | 质量审查结果 |
| `escalation` | 升级（委派给人工） |
| `error_report` / `help_request` | 异常报告 |

对话按**线程**分组，可按任务跟踪对话。

### 24.3 执行监控 (Execution Monitor)

实时监控**正在执行的任务**，并通过 WebSocket 推送到前端。

- 执行中任务的进度率、当前步骤、使用的 Token 数、成本
- 实时推送推理追踪的各步骤
- 错误和升级的即时通知
- 按代理汇总的活动摘要

### API 端点

| 端点 | 说明 |
|------|------|
| `GET /traces` | 推理追踪列表（按任务/代理筛选） |
| `GET /traces/{id}` | 推理追踪详情（包含全部步骤） |
| `GET /traces/{id}/decisions` | 仅提取决策步骤 |
| `GET /communications` | 代理间通信日志 |
| `GET /communications/escalations` | 升级列表 |
| `GET /communications/agent/{id}/interactions` | 按通信对象汇总 |
| `GET /monitor/dashboard` | 监控仪表板（摘要 + 活跃 + 事件） |
| `GET /monitor/active` | 执行中任务列表 |
| `GET /monitor/agent/{id}` | 代理活动 |

---

## 25. Cloudflare Workers 部署

除本地执行外，还支持在 Cloudflare Workers 上进行边缘部署。

### 方式 A：Proxy

- 在现有 FastAPI 前端放置反向代理
- 框架：Hono
- 需要外部服务器

### 方式 B：Full Workers

- 使用 Hono + D1（Cloudflare 的 SQLite）完全重新实现主要 API
- JWT 认证（jose）
- 无需外部服务器的完全无服务器架构
- 提供认证、公司管理、工单、代理、任务、审批、Spec/Plan、审计日志、预算、项目、注册中心、产物、Heartbeat、审查和健康检查

### 前端部署

```bash
cd apps/desktop/ui && npm run build
npx wrangler pages deploy dist --project-name=zeo-ui
```

---

## 26. 桌面应用 (Tauri)

提供基于 Tauri v2 (Rust) 的跨平台桌面应用程序。

| 操作系统 | 格式 |
|---------|------|
| Windows | `.exe` |
| macOS | `.dmg` |
| Linux | `.AppImage` / `.deb` / `.rpm` |

- Python 后端作为 Sidecar 捆绑
- 本地文件访问、会话管理和 UI 在本地运行
- LLM API 和外部 SaaS 通过云端访问

---

## 27. CLI / TUI

提供可通过 pip 安装的 CLI 工具。

```bash
pip install zero-employee-orchestrator
# 或
uv pip install zero-employee-orchestrator
```

入口点：`zero-employee` 命令

### CLI 命令列表

| 命令 | 说明 |
|------|------|
| `zero-employee serve` | 启动 API 服务器 |
| `zero-employee config list` | 显示所有配置值 |
| `zero-employee config set <KEY> [VALUE]` | 保存配置值（省略 VALUE 时提示输入；敏感值不回显） |
| `zero-employee config get <KEY>` | 获取配置值 |
| `zero-employee config delete <KEY>` | 删除配置值（恢复默认） |
| `zero-employee config keys` | 列出可配置的键 |
| `zero-employee local` | 本地聊天模式（Ollama） |
| `zero-employee models` | 列出已安装的 Ollama 模型 |
| `zero-employee pull <model>` | 下载 Ollama 模型 |
| `zero-employee db upgrade` | 运行数据库迁移 |
| `zero-employee health` | 健康检查 |

### 运行时配置管理

无需直接编辑 `.env` 文件即可配置 API 密钥和执行模式。

**3 种配置方式：**
1. **设置界面**：在应用的"设置" -> "LLM API 密钥设置"中输入
2. **CLI**：`zero-employee config set GEMINI_API_KEY`（敏感值通过提示安全输入）
3. **.env 文件**：按传统方式直接编辑 `apps/api/.env`

配置优先级：环境变量 > `~/.zero-employee/config.json` > `.env` > 默认值

---

## 数据库

### 主要表（29+）

`companies`、`users`、`company_members`、`agents`、`tickets`、`ticket_threads`、`specs`、`plans`、`tasks`、`task_runs`、`task_dependencies`、`artifacts`、`reviews`、`approvals`、`budget_policies`、`cost_ledgers`、`heartbeat_policies`、`heartbeat_runs`、`skills`、`plugins`、`extensions`、`tool_connections`、`tool_call_traces`、`policy_packs`、`secret_refs`、`audit_logs`、`projects`、`goals`、`departments`、`teams`

### 支持的数据库

| 环境 | 数据库 |
|------|--------|
| 开发 | SQLite (aiosqlite) |
| 生产 | PostgreSQL (asyncpg) 推荐 |
| 边缘 | Cloudflare D1 |

---

## 技术栈一览

| 层级 | 技术 |
|------|------|
| 桌面 | Tauri v2 (Rust) |
| 前端 | React 19、TypeScript 5.9、Vite 7.3 |
| UI 库 | Tailwind CSS 4.2、shadcn/ui、Recharts 3.7、Lucide Icons |
| 状态管理 | TanStack Query 5.62、Zustand 5.0 |
| 路由 | React Router 7.13 |
| 后端 | Python 3.12+、FastAPI 0.115+ |
| ORM | SQLAlchemy 2.x (async) |
| 迁移 | Alembic |
| LLM 连接 | LiteLLM 1.60+ |
| 认证 | OAuth PKCE、python-jose (JWT) |
| 验证 | Pydantic 2.10+ |
| 调度器 | APScheduler 3.10+ |
| 日志 | structlog 24.0+ |
| 边缘 | Cloudflare Workers、Hono 4.12、D1 |
| 包管理 | uv (Python)、pnpm (Node.js) |

---

## 附加功能（通过 Plugin / Extension 提供）

以下功能不包含在核心中，通过 Plugin / Extension 附加引入。

### 分身 AI（AI Avatar Plugin）

作为用户"分身"行动的 AI 代理。将用户的判断标准、文体和专业知识作为画像进行学习。

| 功能 | 说明 |
|------|------|
| **画像学习** | 通过分析过去的审批/驳回模式、评论历史和文体构建画像 |
| **Judge Layer 集成** | 将用户的判断标准作为 Judge Layer 的自定义规则提供 |
| **代理审查** | 用户不在时的任务审查和优先级判断（最终审批权始终归用户本人） |
| **文体再现** | 以用户的文体和语调创建草稿 |
| **审批模式建议** | 基于过去的审批模式建议自主执行范围 |

### AI 秘书（AI Secretary Plugin）

作为连接用户与 AI 组织的"枢纽"运作的 AI 代理。

| 功能 | 说明 |
|------|------|
| **晨间简报** | 汇总待审批、进行中的任务和今日日程 |
| **下一步行动建议** | 判定任务的紧急度和重要度，推荐排序 |
| **进展摘要** | 以易懂的方式向用户报告 AI 组织的活动状况 |
| **提醒** | 临近截止日期的任务和待审批通知 |
| **委派路由** | 将用户指令路由到合适的代理 |
| **聊天集成** | 与 Discord / Slack / LINE Bot Plugin 集成推送简报 |

### 聊天工具集成（Discord / Slack / LINE Bot Plugin）

从外部聊天工具向 AI 组织发送指令并接收结果。

| 命令 | 动作 |
|------|------|
| `/zeo ticket <描述>` | 创建新工单 |
| `/zeo status [ticket_id]` | 查看工单/任务状态 |
| `/zeo approve <approval_id>` | 审批操作 |
| `/zeo reject <approval_id>` | 驳回操作 |
| `/zeo briefing` | 获取当前业务摘要 |
| `/zeo ask <问题>` | 向 AI 组织提问 |

需要审批的操作也会在聊天工具中显示审批对话框。可与 AI 秘书 Plugin 联动，作为定期简报的推送目标使用。

---

## 28. 外部工具集成 (v0.1)

### CLI 工具连接

`tools/connector.py` 支持以下连接类型：

| 连接类型 | 说明 | 示例 |
|---------|------|------|
| `rest_api` | REST API 调用 | SaaS API、内部 API |
| `webhook` | Webhook 接收/发送 | Slack / Discord 通知 |
| `mcp` | Model Context Protocol | Claude Desktop、VS Code 集成 |
| `oauth` | OAuth 2.0 认证流程 | Google / GitHub 认证 |
| `websocket` | WebSocket 双向通信 | 实时数据流 |
| `file_system` | 文件系统连接 | 本地 / NFS / S3 |
| `database` | 数据库连接 | PostgreSQL、MySQL |
| `cli_tool` | CLI 工具连接 | gws、gh、aws CLI 等 |
| `grpc` | gRPC 服务连接 | 微服务间通信 |
| `graphql` | GraphQL API 连接 | GitHub GraphQL API 等 |

### 支持的 CLI 工具示例

| 工具 | 说明 | 仓库 |
|------|------|------|
| **gws** | Google Workspace CLI（从终端统一操作所有 Google Workspace API） | `googleworkspace/cli` |
| **gh** | GitHub CLI（仓库、Issue、PR 操作） | `cli/cli` |
| **aws** | AWS CLI（所有 AWS 服务操作） | `aws/aws-cli` |
| **gcloud** | Google Cloud CLI（GCP 服务操作） | Google Cloud SDK |
| **az** | Azure CLI（Azure 服务操作） | `Azure/azure-cli` |

这些 CLI 工具注册到 `ToolConnector` 后，即可从 Skill 中调用。也可以将 CLI 工具集成包作为 Plugin 提供。

---

## 29. 社区插件共享 (v0.1)

### 插件的共享与发布

用户可以将自制插件作为 GitHub 仓库发布，其他用户可以轻松安装。无需开发者将其添加到核心。

### 插件共享机制

```
用户 A：开发插件
  -> 推送到 GitHub 仓库（topic：zeo-plugin）
  -> 包含 plugin.json manifest

用户 B：搜索并安装插件
  -> POST /api/v1/registry/plugins/search-external?query=关键词
  -> POST /api/v1/registry/plugins/import?source_uri=https://github.com/user/plugin
  -> 插件自动安装并可使用
```

### 插件 Manifest 格式（`plugin.json`）

```json
{
  "name": "my-awesome-plugin",
  "slug": "my-awesome-plugin",
  "description": "插件描述",
  "version": "0.1.0",
  "author": "作者名",
  "license": "MIT",
  "tags": ["productivity", "automation"],
  "skills": ["skill-a", "skill-b"],
  "config_schema": {}
}
```

### 社区插件 API

| 端点 | 说明 |
|------|------|
| `POST /api/v1/registry/plugins/search-external` | 从 GitHub 等搜索外部插件 |
| `POST /api/v1/registry/plugins/import` | 从 GitHub 仓库导入并安装插件 |
| `POST /api/v1/registry/plugins` | 在本地创建插件 |
| `POST /api/v1/registry/plugins/install` | 安装插件 |

### 安全性检查

安装共享插件时会执行以下安全性检查：

- 检测危险代码模式（16 种）
- 检测并警告外部通信
- 检测凭证访问
- 检测破坏性操作
- 风险级别评估（low / medium / high）

---

## 30. AI Self-Improvement — Level 2: 自我改进的萌芽 (v0.1)

AI 分析、改进和验证 AI 的自我改进功能集。作为 `ai-self-improvement` 插件实现。

### 6 个自我改进 Skill

| Skill | 功能 | API 端点 |
|-------|------|---------|
| **skill-analyzer** | 现有 Skill 的代码质量分析（静态分析 + LLM 深度分析） | `POST /self-improvement/analyze` |
| **skill-improver** | 基于分析结果自动生成改进版 Skill | `POST /self-improvement/improve` |
| **judge-tuner** | 从 Experience Memory 自动调整 Judge 判定标准 | `POST /self-improvement/judge/tune` |
| **failure-to-skill** | 从失败模式自动生成预防 Skill | `POST /self-improvement/failure-to-skill` |
| **skill-ab-test** | 两个 Skill 的 A/B 测试比较（质量和速度） | `POST /self-improvement/ab-test` |
| **auto-test-generator** | 自动生成 Skill 测试代码（正常、边界、异常情况） | `POST /self-improvement/generate-tests` |

### 分析类别

| 类别 | 评估内容 |
|------|---------|
| `code_quality` | 代码结构、可读性、命名规范、DRY 原则 |
| `performance` | 不必要的处理、内存使用、N+1 查询 |
| `error_handling` | 异常处理、回退机制、输入验证 |
| `security` | 注入、凭证暴露、危险操作 |
| `test_coverage` | 可测试性、边界情况考虑 |
| `documentation` | 文档字符串、类型提示、注释 |

### 安全机制

- 所有改进应用**必须用户审批**
- 改进前代码作为 **version_history** 保留（可回滚）
- 改进代码的**安全性检查**（16 种危险代码模式检测）
- Judge 规则仅应用**置信度 0.5 以上**的规则

### 仪表板 API

`GET /api/v1/self-improvement/status` 返回以下统计：
- Skill 分析数、改进提案数、改进应用数
- Judge 规则提案数、应用数
- 故障预防 Skill 提案数、A/B 测试完成数、测试生成数

---

## 31. v0.1 功能膨胀审查 — 核心与扩展的边界

在 v0.1 中，以下功能包含在代码库中，但根据**核心功能判断标准**（"没有它，审批、审计和执行控制是否无法成立？"），被归类为**扩展功能**。计划在未来版本中作为独立包分离。

| 功能 | 当前位置 | 分类 | 状态 |
|------|---------|------|------|
| **Sentry 集成** | `integrations/sentry_integration.py` | Extension | v0.1 捆绑，将来分离 |
| **AI 调查工具** | `integrations/ai_investigator.py` | Skill | v0.1 捆绑，将来分离 |
| **假设验证引擎** | `orchestration/hypothesis_engine.py` | Plugin | v0.1 捆绑，将来分离 |
| **MCP 服务器** | `integrations/mcp_server.py` | Extension | v0.1 捆绑，将来分离 |
| **外部 Skill 导入** | `integrations/external_skills.py` | Extension | v0.1 捆绑，将来分离 |

> **注意**：以上功能在 v0.1 中可用，但为维护核心稳定性，
> 计划在未来版本中作为 Extension / Skill / Plugin 独立出来。
> 详情请参阅 [FEATURE_BOUNDARY.md](../dev/FEATURE_BOUNDARY.md)。

---

## 32. 元技能概念 (v0.1)

赋予 AI 代理"学习如何学习"能力的设计概念。

### 元技能的 5 个要素

| 要素 | AI 代理中的实现 |
|------|---------------|
| **Feeling（感知力）** | 推察用户意图和情感、理解上下文 |
| **Seeing（洞察力）** | 系统思维、把握业务整体依赖关系 |
| **Dreaming（想象力）** | 创造性替代方案提案、Re-Propose Layer |
| **Making（实现力）** | 从规划到实施的一贯执行、DAG 构建 |
| **Learning（学习力）** | 通过 Experience Memory 和 Failure Taxonomy 进行学习 |

传统 AI 代理具备硬技能（特定任务的执行）和软技能（沟通），但缺乏元技能（支撑技能运用和学习的能力）。Zero-Employee Orchestrator 通过 Experience Memory 和 Failure Taxonomy 提供元技能的基础。

---

## 33. 基于文件附件的计划创建 (v0.1)

在 Design Interview 中附加文件，作为规格书（Spec）生成的上下文进行整合。

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /api/v1/tickets/{ticket_id}/interview/attach` | 文件上传 |
| `GET /api/v1/tickets/{ticket_id}/interview/attachments` | 附件列表 |

### 支持的文件格式

| 类别 | 格式 |
|------|------|
| 文本 | `.txt`, `.md`, `.csv`, `.json`, `.yaml` |
| 代码 | `.py`, `.ts`, `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.h`, `.html`, `.xml`, `.css`, `.sql`, `.sh` |
| 图片 | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg` |
| 文档 | `.pdf` |

- 自动文本提取 + 多编码支持（UTF-8, Shift_JIS, EUC-JP, CP932）
- 提取的文本自动集成到 Spec 的"参考资料"部分
- 图片使用 Base64 编码 + PNG/JPEG 尺寸检测
- SVG 也作为文本解析
- 10 MB 大小限制

---

## 34. 安全加固 (v0.1)

| 项目 | 说明 |
|------|------|
| **bcrypt 强制化** | 强制使用 bcrypt 进行密码哈希。移除 SHA-256 回退 |
| **速率限制** | 通过 `slowapi` 实现认证端点的速率限制（注册: 5次/分钟, 登录: 10次/分钟） |
| **RAG 文件权限** | 将 `index.json` / `idf.json` 限制为 `0o600`（仅所有者可读写） |
| **RAG 输入验证** | 内容大小上限 (10 MB) 和元数据键数限制 |
| **CORS 限制加强** | 将通配符改为明确的方法和头部列表 |
| **UUID 输入验证** | 修复对无效 UUID 返回 400 的问题 |

---

## 35. RSS/ToS 自动更新管道 (v0.1)

定期监控 AI 服务商的 RSS 订阅源、使用条款和定价页面，自动检测变更。

### 监控对象

| 供应商 | RSS | ToS | 定价 | 检查间隔 |
|--------|-----|-----|------|----------|
| **OpenAI** | 是 | 是 | 是 | 12 小时 |
| **Anthropic** | 是 | 是 | 是 | 12 小时 |
| **Google AI** | 是 | 是 | 是 | 12 小时 |
| **Mistral AI** | 是 | 是 | 是 | 24 小时 |
| **Cohere** | 是 | 是 | 是 | 24 小时 |
| **Meta AI** | 是 | 是 | — | 24 小时 |

### 检测到的变更类型

| 变更类型 | 影响等级 | 说明 |
|---------|---------|------|
| `MODEL_UPDATE` | MEDIUM | 新模型发布 / 版本更新 |
| `PRICING_CHANGE` | MEDIUM | 定价变更 |
| `TOS_UPDATE` | HIGH | 使用条款修订 |
| `NEW_FEATURE` | LOW | 新功能添加 |
| `DEPRECATION` | HIGH | 模型 / API 弃用通知 |
| `API_CHANGE` | HIGH | 破坏性 API 变更 |
| `SECURITY_ADVISORY` | CRITICAL | 安全公告 |

### 自动更新流程

1. 定期获取 RSS 源、ToS 页面和定价页面
2. 通过哈希比较检测变更
3. 使用关键词匹配对变更类型进行分类
4. 自动评估影响等级（紧急关键词触发 CRITICAL 升级）
5. 检测到 `MODEL_UPDATE` 时自动触发 `ModelRegistry.refresh_catalog()`
6. 支持添加自定义监控服务

---

## 36. Knowledge Refresh — 上下文窗口管理 (v0.1)

动态选择和注入与任务相关的知识，以应对 LLM 上下文窗口限制。

### 知识管道

```
获取 → 提取 → 分割 → 索引 → 搜索 → 引用/摘要 → 晋升为已验证知识 / 拒绝
```

### 知识类型

| 类型 | 说明 |
|------|------|
| `conversation_log` | 对话历史 |
| `reusable_improvement` | 可复用的改进知识 |
| `experimental_knowledge` | 实验性知识 |
| `verified_knowledge` | 已验证知识 |
| `experience_memory` | 成功模式 |
| `failure_taxonomy` | 失败分类 |
| `policy_memory` | 审批条件 / 禁止事项 |
| `skill_improvement` | Skill 改进知识 |
| `plugin_operation` | 插件运营知识 |

### 知识生命周期

```
RAW → EXTRACTED → INDEXED → VERIFIED（已批准）
                           → EXPERIMENTAL（实验性）
                           → REJECTED（已拒绝）
```

---

## 37. A2A 双向通信 (v0.1)

代理间点对点通信枢纽。不仅支持父→子的子代理指令，还支持对等通信、协商和基于频道的广播。

### 功能

| 功能 | 说明 |
|------|------|
| **直接消息** | 代理间 1:1 消息收发 |
| **频道通信** | 命名频道的群组通信/广播 |
| **线程追踪** | 消息线程自动分组 |
| **协商协议** | 代理间共识达成协议 |
| **优先级控制** | LOW / NORMAL / HIGH / URGENT 消息优先级 |

---

## 38. Avatar AI 共进化 — 与用户共同成长 (v0.1)

从用户交互模式中学习决策标准的共进化引擎，让 AI 与用户共同成长。

### 功能

| 功能 | 说明 |
|------|------|
| **交互记录** | 记录用户的批准/拒绝/编辑操作 |
| **偏好提取** | 从操作模式中自动提取用户偏好 |
| **决策标准学习** | 积累批准/拒绝的判断标准 |
| **选项排序** | 基于用户偏好进行建议优先排序 |
| **用户模型管理** | 支持导出/导入 |

---

## 39. Longrun Scheduler — 24/365 持续运行 (v0.1)

支持 AI 组织全天候持续运行的调度器。

### 调度类型

| 类型 | 说明 |
|------|------|
| `INTERVAL` | 按固定间隔重复执行 |
| `CRON` | 基于 cron 表达式的调度 |
| `EVENT_DRIVEN` | 由外部事件触发执行 |
| `CONTINUOUS` | 持续执行（直到停止指令） |

---

## 40. Agent Session — 上下文持久化 (v0.1)

让 AI 代理在多轮交互中保持上下文的会话管理功能。

### 功能

- 会话状态管理：ACTIVE / IDLE / EXPIRED / TERMINATED
- 上下文 DB 持久化（SQLAlchemy async）
- 空闲状态等待并保持上下文
- 会话自动过期

---

## 41. Artifact Bridge — 工序间成果物交接 (v0.1)

实现工序间成果物交接，支持版本管理和复用。

### 功能

| 功能 | 说明 |
|------|------|
| **自动链接** | DAG 输出→输入自动连接 |
| **跨域转换** | 跨领域的成果物类型转换 |
| **兼容性矩阵** | 成果物类型间的兼容性映射 |
| **成果物搜索** | 搜索兼容的成果物 |
| **管道支持** | 技能链成果物流构建 |

---

## 42. 媒体生成集成 (v0.1)

使用外部 API 集成图像、视频、音频和音乐生成。

### 支持的服务

| 类别 | 服务 |
|------|------|
| **图像生成** | OpenAI DALL-E, Stability AI (Stable Diffusion), Replicate |
| **视频生成** | Runway ML, Replicate (SVD/AnimateDiff), Pika |
| **语音生成** | OpenAI TTS, ElevenLabs |
| **音乐生成** | Suno, Udio |

安全性：提示注入检查、审批门控、数据保护策略执行、审计日志。

API: `/api/v1/media/*`

---

## 43. AI 工具注册表 (v0.1)

统一管理 AI 代理可操作的 25+ 外部工具。

### 支持的工具类别

| 类别 | 示例 |
|------|------|
| 代码相关 | GitHub, GitLab, Bitbucket, 代码审查 |
| 文档 | Google Docs, Notion, Confluence, Obsidian |
| 通信 | Slack, Discord, LINE, Email |
| 项目管理 | Jira, Linear, Asana, Trello |
| 设计 | Figma (通过 MCP) |
| 数据分析 | Google Sheets, Airtable |
| 云服务 | AWS, GCP, Azure (通过 CLI) |
| 搜索 | Web Search, RAG, Knowledge Base |
| 媒体生成 | 图像/视频/音频 (media_generation.py) |
| 浏览器操作 | Browser Assist, Playwright |

所有工具操作均通过审批门控、审计日志和数据保护策略。

API: `/api/v1/ai-tools/*`

---

## 44. iPaaS 集成 — 工作流连接 (v0.1)

通过 Webhook 触发器与外部 iPaaS 平台连接。

### 支持的平台

| 平台 | 说明 |
|------|------|
| **n8n** | 支持自托管的开源自动化 |
| **Zapier** | 云端 iPaaS（Webhook 触发器） |
| **Make (Integromat)** | 可视化自动化 |

API: `/api/v1/ipaas/*`

---

## 45. 成果物导出 (v0.1)

将任务成果物以各种格式导出，用于本地保存或外部服务发送。

### 支持的格式

PDF / Markdown / HTML / JSON / CSV / DOCX

### 发送目标

- 本地文件系统（沙箱白名单文件夹）
- Google Docs
- Notion
- n8n Webhook

API: `/api/v1/export/*`

---

## 46. AI 共创内容再利用引擎 (v0.1)

自动将单一内容转换为多种媒体格式，根据品牌声音和风格指南调整语调。

### 目标格式

博客文章 / 社交媒体帖子 / 推文线程 / 邮件新闻通讯 / 幻灯片 / 信息图表 / 新闻稿 / FAQ / 视频脚本 / 播客文字稿

安全性：提示注入检查、PII 防护、审计日志。

---

## 47. Obsidian 集成 (v0.1)

提供与 Obsidian Vault 的双向同步。

### 功能

| 功能 | 说明 |
|------|------|
| **笔记读写** | 在 Vault 中创建、更新、删除笔记 |
| **链接图构建** | 自动解析 `[[wikilink]]` 并生成图谱 |
| **全文搜索** | 搜索 Vault 中的所有笔记 |
| **反向链接分析** | 从引用目标到引用源的反向查找 |
| **知识库集成** | 与 ZEO Knowledge Store 双向同步 |

文件访问通过沙箱限制在允许的目录内。

---

## 48. 云服务原生集成 (v0.1)

通过统一接口提供多云资源管理、存储、无服务器执行和成本估算。

### 支持的供应商

| 供应商 | 支持的资源 |
|--------|-----------|
| **AWS** | S3, Lambda, EC2, RDS 等 |
| **GCP** | Cloud Storage, Cloud Functions, GKE 等 |
| **Azure** | Blob Storage, Functions, AKS 等 |
| **Cloudflare** | Workers, R2, D1 等 |

所有操作通过审批门控、审计日志，凭证通过 secret_manager 管理。

---

## 49. 智能设备 / VR/AR 集成 (v0.1)

统一管理 IoT 传感器、智能显示器、VR/AR 头显、机器人和无人机。

### 支持的协议

| 协议 | 用途 |
|------|------|
| **MQTT** | IoT 传感器/执行器 |
| **HTTP** | REST API 兼容设备 |
| **WebSocket** | 实时流 |
| **Bluetooth** | 近距离通信设备 |
| **Zigbee** | 智能家居设备 |
| **Matter** | 下一代智能家居标准 |

所有设备操作通过审批门控、审计日志和数据保护策略。

---

## 50. 治理与合规 (v0.1)

提供企业级审计、权限管理和数据策略。

### 支持的框架

| 框架 | 说明 |
|------|------|
| **GDPR** | 欧盟通用数据保护条例 |
| **HIPAA** | 美国健康保险可携性和责任法案 |
| **SOC2** | 服务组织控制 2 |
| **ISO27001** | 信息安全管理 |
| **CCPA** | 加州消费者隐私法 |
| **APPI** | 日本个人信息保护法 |

### 策略类型

| 类型 | 说明 |
|------|------|
| `DATA_RETENTION` | 数据保留期限/自动删除 |
| `ACCESS_CONTROL` | 访问控制规则 |
| `AUDIT_REQUIREMENT` | 审计要求 |
| `EXPORT_RESTRICTION` | 数据导出限制 |
| `AI_USAGE_LIMIT` | AI 使用限制 |
| `PII_HANDLING` | 个人信息处理 |
| `ENCRYPTION_REQUIREMENT` | 加密要求 |

API: `/api/v1/governance/*`

---

## 51. Skill 市场 (v0.1)

用于发布、搜索、评审和安装社区 Skills / Plugins / Extensions 的市场。

### 发布流程

```
DRAFT → PENDING_REVIEW → PUBLISHED
                        → REJECTED
```

### 类别

生产力 / 通信 / 数据分析 / 开发 / 营销 / 设计 / 安全 / DevOps / 财务 / 教育

### 功能

- 类别和标签搜索
- 用户评价（1-5 星评分 + 评论）
- 安装数量追踪
- 基于审批的发布流程

API: `/api/v1/marketplace/*`

---

## 52. 多用户/团队管理 (v0.1)

提供基于团队的认证和权限管理。

### 团队角色

| 角色 | 权限 |
|------|------|
| **Owner** | 全部权限（包括团队设置、成员管理） |
| **Admin** | 成员管理、AI 设置 |
| **Member** | 创建工单、执行任务 |
| **Viewer** | 只读 |
| **AI Operator** | 仅限 AI 相关资源 |

### 功能

- 团队创建和邀请（邮件/链接）
- 邀请有效期和使用限制
- 资源类型 × 操作的权限矩阵

API: `/api/v1/teams/*`

---

## 53. 红队安全测试 (v0.1.1)

自动测试系统的安全防御，早期检测和报告漏洞。
所有测试均使用真实载荷执行实际安全模块，而非仅验证配置。

### 测试类别（8 个类别，22 个测试）

| 类别 | 测试数 | 验证方法 |
|------|--------|---------|
| **提示注入** | 4 | 通过 `prompt_guard` 扫描载荷并验证检测 |
| **数据泄露** | 3 | 通过 `sanitizer` 和 `pii_guard` 执行载荷 |
| **权限提升** | 3 | 验证 IAM 拒绝范围 + 提示防护升级检测 |
| **PII 泄露** | 3 | 通过 `pii_guard` 执行载荷并验证脱敏 |
| **未授权访问** | 2 | 验证安全头中间件 + 认证依赖 |
| **沙箱逃逸** | 3 | 测试 8+ 个危险路径（含路径遍历变体） |
| **速率限制绕过** | 2 | 验证限流配置 + 429 处理器 + 实时端点测试 |
| **认证绕过** | 2 | 测试 algorithm=none、过期和篡改的 JWT 令牌 |

### CI 集成 (v0.1.1)

- Red-team 测试在每个 PR 上通过 GitHub Actions 自动运行
- 发现 **critical** 级别问题时构建失败
- 失败率超过 20% 时发出警告

---

## 54. 工作空间隔离 (v0.1)

严格限制 AI 代理文件访问和网络访问的隔离层。

### 功能

- 默认无本地或云连接（最小权限原则）
- 仅可访问内部存储
- 当聊天指令与系统设置不同时，`should_request_approval()` 请求用户许可
- 环境覆盖审计日志

---

## 55. Design Interview 历史失败模式反馈 (v0.1)

在 Design Interview 执行过程中，自动搜索 Experience Memory 和 Failure Taxonomy 中的类似过去失败模式，提供"此类目标设定过去因 XX 原因失败"的反馈。

### 功能

| 功能 | 说明 |
|------|------|
| **基于目标的失败搜索** | 搜索与用户输入目标相似的过去失败模式 |
| **频繁失败自动警告** | 自动显示发生 2 次以上的失败模式警告 |
| **预防策略展示** | 以结构化格式展示过去失败的预防策略 |
| **恢复成功率展示** | 以数字展示每个失败模式的恢复成功率 |
| **Interview 问题动态注入** | 基于过去失败模式自动生成额外问题 |

### 流程

```
1. 用户输入目标
2. 使用目标文本搜索 Experience Memory
3. 从 Failure Taxonomy 获取频繁失败模式
4. 将匹配的失败模式格式化为反馈
5. 将警告和额外问题注入 Interview 会话
6. 在 Spec 生成时作为风险说明集成
```

---

## 56. 前提变化通用监控 — Prerequisite Monitor (v0.1)

扩展 RSS/ToS 管道，允许用户注册与业务相关的外部信息源（竞争对手网站、法规页面、依赖 API 变更日志等）并定期检查。通过 Heartbeat + Web fetch 组合实现。

### 监控类别

| 类别 | 说明 | 示例 |
|------|------|------|
| `competitor` | 竞争对手网站 | 定价页面、功能列表 |
| `regulation` | 法规页面 | GDPR 指南、数据保护法 |
| `dependency_api` | 依赖 API | Stripe API changelog、AWS 服务更新 |
| `pricing` | 定价页面 | SaaS 定价变更 |
| `tos` | 服务条款 | 服务条款变更 |
| `documentation` | 文档 | API 文档、SDK 发布说明 |
| `security` | 安全 | CVE、安全公告 |
| `custom` | 自定义 | 任意网页 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /quality-insights/prerequisites/sources` | 注册监控源 |
| `GET /quality-insights/prerequisites/sources` | 监控源列表 |
| `POST /quality-insights/prerequisites/check` | 手动检查 |
| `GET /quality-insights/prerequisites/changes` | 变更历史 |
| `GET /quality-insights/prerequisites/summary` | 摘要仪表板 |

---

## 57. Spec 间矛盾检测 — Spec Contradiction Detector (v0.1)

验证多个工单的 Spec 之间是否存在矛盾，利用 CrossModelJudge 的否定模式检测、数值不一致检测和语义比较。

### 检测的矛盾类型

| 类型 | 说明 | 严重程度 |
|------|------|---------|
| `objective_conflict` | 目标矛盾 | ERROR |
| `constraint_conflict` | 约束条件矛盾 | ERROR |
| `acceptance_criteria_conflict` | 验收标准矛盾 | ERROR |
| `resource_conflict` | 资源分配冲突 | WARNING |
| `priority_conflict` | 类似目标的优先级不一致 | INFO |
| `negation_conflict` | 否定模式矛盾 | ERROR |
| `numeric_discrepancy` | 数值不一致 | WARNING |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /quality-insights/spec-contradictions/check` | 执行矛盾检测 |

---

## 58. 任务执行重放与比较 — Task Replay & Comparison (v0.1)

使用不同模型或参数重新执行同一任务并比较结果。将 A/B 测试从 Skill 级别扩展到任务级别的比较。

### 比较维度

| 维度 | 说明 | 权重 |
|------|------|------|
| **品质** | 与原始输出的相似度 | 50% |
| **速度** | 执行时间 | 20% |
| **成本** | API 成本 | 20% |
| **一致性** | 各次执行间的相似度 | 10% |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /quality-insights/task-replay/jobs` | 创建重放任务 |
| `GET /quality-insights/task-replay/jobs` | 任务列表 |
| `GET /quality-insights/task-replay/jobs/{id}` | 任务详情 |
| `POST /quality-insights/task-replay/jobs/{id}/execute` | 记录执行结果 |

---

## 59. 用户判断回顾报告 — Judgment Review (v0.1)

从审批/拒绝历史中可视化判断趋势："在此期间，您有这些判断倾向"。支持用户自身决策意识的提升。

### 检测的模式

| 模式 | 说明 | 建议 |
|------|------|------|
| `high_rejection_rate` | 拒绝率 > 50% | 检查 AI 提案质量 |
| `category_concentration` | 判断集中于特定类别 | 扩大自主执行范围 |
| `high_risk_auto_approve` | 高风险操作审批率高 | 审查审批标准 |
| `slow_response` | 平均响应 > 1 小时 | 检查通知设置 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /quality-insights/judgment-review/record` | 记录判断 |
| `GET /quality-insights/judgment-review/report` | 生成报告 |

---

## 60. 目标→Plan 分解品质验证 — Plan Quality Verifier (v0.1)

验证 Spec 到 Plan 的分解是否"不遗漏、不重复（MECE）"，使用 Judge Layer 进行验证。

### 品质等级

| 等级 | 分数范围 | 说明 |
|------|---------|------|
| **EXCELLENT** | 0.9 以上 | 无遗漏、无重复 |
| **GOOD** | 0.7–0.9 | 整体良好，可轻微改进 |
| **FAIR** | 0.5–0.7 | 需要改进 |
| **POOR** | 0.5 以下 | 需要大幅修改 |

### 检测的问题

| 问题类型 | 说明 |
|---------|------|
| `missing_coverage` | Spec 要素未被任务覆盖 |
| `duplicate_task` | 存在类似任务 |
| `constraint_not_reflected` | 约束未反映在任务中 |
| `acceptance_not_mapped` | 验收标准无对应任务 |
| `dependency_issue` | 缺失或循环依赖 |
| `scope_creep` | Spec 范围外的任务 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /quality-insights/plan-quality/verify` | 验证 Plan 品质 |

---

## 61. 多模型比较 (v0.1)

将相同的输入同时发送到多个 LLM 模型，比较响应质量、延迟和令牌使用量。

### 功能概述

| 项目 | 说明 |
|------|------|
| **同时比较** | 将相同的提示发送到多个模型并行获取结果 |
| **指标记录** | 自动记录每个模型的延迟、令牌数和成本 |
| **会话管理** | 保存和搜索比较会话历史 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /companies/{id}/multi-model/compare` | 执行多模型比较 |

---

## 62. 头脑风暴会话 (v0.1)

使用多个 AI 代理运行辩论、评审和策略会话。

### 会话类型

| 类型 | 说明 |
|------|------|
| **debate** | 不同模型之间的辩论形式 |
| **review** | 评审和批评会话 |
| **strategy** | 策略规划会话 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /companies/{id}/brainstorm` | 创建会话 |
| `POST /brainstorm/{session_id}/message` | 添加消息 |
| `GET /brainstorm/{session_id}` | 获取会话（含对话历史和洞察） |
| `GET /companies/{id}/brainstorm/sessions` | 会话列表 |
| `POST /brainstorm/{session_id}/status` | 更新状态 |
| `GET /companies/{id}/brainstorm/search` | 搜索会话 |

---

## 63. 对话记忆 — Conversation Memory (v0.1)

持久化存储所有用户与代理之间的对话，支持搜索和统计查询。

### 内容类型

| 类型 | 说明 |
|------|------|
| `text` | 文本消息 |
| `brainstorm` | 头脑风暴 |
| `comparison` | 模型比较 |
| `task` | 任务相关 |
| `secretary` | Secretary AI |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /companies/{id}/conversation-memory` | 存储消息 |
| `GET /companies/{id}/conversation-memory` | 获取历史（支持筛选） |
| `GET /companies/{id}/conversation-memory/search` | 全文搜索 |
| `GET /companies/{id}/conversation-memory/stats` | 对话统计 |

---

## 64. 文本分析服务 (v0.1)

提供精确的 Unicode 字符计数和详细分类。

### 分析类别

| 类别 | 说明 |
|------|------|
| **平假名** | 平假名字符数 |
| **片假名** | 片假名字符数 |
| **汉字** | 汉字（CJK统一表意文字）字符数 |
| **ASCII** | 英文数字和符号 |
| **数字** | 数字字符数 |
| **空格** | 空白字符数 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /text/analyze` | 执行文本分析 |

---

## 65. 基于角色的模型配置 (v0.1)

为代理角色指定特定的 LLM 模型，支持回退模型设置。

### API 端点

| 端点 | 说明 |
|------|------|
| `PUT /companies/{id}/role-models` | 设置角色模型配置 |
| `GET /companies/{id}/role-models` | 获取所有角色配置 |
| `GET /companies/{id}/role-models/{role}` | 获取特定角色配置 |
| `DELETE /role-models/{config_id}` | 删除配置 |

---

## 66. AI 组织动态管理 (v0.1)

在运行时按角色添加、删除和更新代理，支持自定义系统提示。

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /companies/{id}/agents/by-role` | 按角色添加代理 |
| `DELETE /agents/{id}/remove` | 删除代理 |
| `PATCH /agents/{id}/role` | 更新代理角色 |

---

## 67. 自定义代理角色 (v0.1)

除预设角色外，用户可定义自定义角色。

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /companies/{id}/custom-roles` | 创建自定义角色 |
| `GET /companies/{id}/custom-roles` | 自定义角色列表 |
| `DELETE /custom-roles/{role_id}` | 删除自定义角色 |
| `GET /companies/{id}/available-roles` | 获取所有可用角色（预设+自定义） |

---

## 68. 自然语言功能请求 (v0.1)

用自然语言向 AI 组织提交请求，系统自动解释意图并可自动执行。

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /companies/{id}/feature-requests` | 提交功能请求 |
| `GET /companies/{id}/feature-requests` | 请求列表 |

---

## 69. 脑暴转储 / Secretary AI (v0.1)

CEO/用户可自由记录想法、创意和待办事项，系统自动分类、标签和追踪。

### 类别

| 类别 | 说明 |
|------|------|
| `idea` | 创意 |
| `todo` | 待办事项 |
| `decision` | 决策 |
| `reflection` | 反思 |
| `strategy` | 策略 |
| `problem` | 问题 |
| `opportunity` | 机会 |
| `memo` | 备忘录 |
| `daily_log` | 日志 |

### 功能

- 自动标签
- 行动项提取
- 优先级追踪
- 日统计

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /companies/{id}/brain-dump` | 创建脑暴转储 |
| `GET /companies/{id}/brain-dumps` | 列表（支持筛选） |
| `GET /brain-dumps/{id}` | 获取详情 |
| `PATCH /brain-dumps/{id}` | 更新 |
| `GET /companies/{id}/brain-dumps/search` | 搜索 |
| `GET /companies/{id}/brain-dumps/action-items` | 提取所有行动项 |
| `GET /companies/{id}/brain-dumps/daily-stats` | 日统计 |

---

## 70. 文件上传管理 (v0.1)

支持最大 50MB 的文件上传，通过扩展名白名单安全管理。

### 支持的格式

| 类别 | 扩展名 |
|------|--------|
| **文档** | txt, md, csv, json, yaml, xml, html, pdf, docx, xlsx, pptx |
| **图片** | png, jpg, jpeg, gif, svg, webp |
| **代码** | py, js, ts, tsx, jsx, rb, go, rs, java, c, cpp, h |
| **压缩包** | zip, tar, gz |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /files/upload` | 单文件上传 |
| `POST /files/upload-multiple` | 多文件上传 |
| `GET /files/{id}` | 获取文件信息 |
| `GET /files/{id}/download` | 下载文件 |
| `DELETE /files/{id}` | 删除文件 |
| `GET /files` | 文件列表（分页） |

---

## 71. 任务执行中的用户输入 (v0.1)

AI 可在任务执行过程中向用户请求额外信息，支持超时机制。

### 输入类型

| 类型 | 说明 |
|------|------|
| `text` | 文本输入 |
| `file` | 文件附件 |
| `choice` | 从选项中选择 |
| `confirmation` | 确认（是/否） |
| `multi_file` | 多文件附件 |

### 状态

| 状态 | 说明 |
|------|------|
| `pending` | 等待回复 |
| `answered` | 已回复 |
| `expired` | 已超时 |
| `cancelled` | 已取消 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /user-input/request` | 创建输入请求 |
| `GET /user-input/pending` | 获取所有待处理请求 |
| `GET /user-input/pending/{task_id}` | 获取任务相关待处理请求 |
| `POST /user-input/{id}/answer` | 提交回复 |
| `DELETE /user-input/{id}` | 取消请求 |

---

## 72. 资源导入 (v0.1)

从文件、文件夹或 URL 导入业务手册、规定和文档，作为 AI 上下文使用。

### 资源类型

| 类型 | 说明 |
|------|------|
| `manual` | 业务手册 |
| `rule` | 规定和规则 |
| `documentation` | 文档 |
| `template` | 模板 |
| `code_example` | 代码示例 |
| `config` | 配置文件 |
| `data_reference` | 数据参考 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /resources/import/file` | 导入文件 |
| `POST /resources/import/folder` | 导入文件夹（递归） |
| `POST /resources/import/url` | 从 URL 导入 |
| `GET /resources` | 资源列表（支持筛选） |
| `GET /resources/search` | 全文搜索 |
| `GET /resources/{id}` | 获取资源详情 |
| `DELETE /resources/{id}` | 删除资源 |

---

## 73. 项目与目标管理 (v0.1)

创建项目并定义层级目标。

### API 端点

| 端点 | 说明 |
|------|------|
| `GET /companies/{id}/projects` | 项目列表 |
| `POST /companies/{id}/projects` | 创建项目 |
| `GET /projects/{id}/goals` | 目标列表 |
| `POST /projects/{id}/goals` | 创建目标 |

---

## 74. 假设引擎 — Hypothesis Engine (v0.1)

多代理并行假设验证与交叉评审。

### 假设状态

| 状态 | 说明 |
|------|------|
| `proposed` | 已提出 |
| `investigating` | 调查中 |
| `evidence_found` | 发现证据 |
| `refuted` | 已反驳 |
| `confirmed` | 已确认 |
| `needs_review` | 需要评审 |
| `reviewed` | 已评审 |

### 功能

- 假设提出与调查员分配
- 支持/反驳证据收集
- 交叉评审提交
- 支持度评分计算（-1.0 至 1.0）
- 评审共识追踪

---

## 75. AI 调查引擎 — AI Investigator (v0.1)

AI 安全的只读数据库查询接口，用于故障排查和分析。

### 安全性

| 约束 | 说明 |
|------|------|
| **只读** | 仅允许 SELECT 查询 |
| **表白名单** | tickets, tasks, agents, audit_logs, knowledge_store 等 |
| **SQL 注入防御** | 禁止关键词检测 |
| **行数限制** | 每次查询最多 500 行 |

### 功能

- 安全的 SELECT 查询执行
- 审计日志筛选搜索
- 错误模式分析
- 任务执行历史获取
- 知识库搜索
- 系统指标收集

---

## 76. 浏览器自动化 — Browser Automation (v0.1)

基于 Playwright 的网页浏览器自动化，配备审批门和审计日志。

### 支持的操作

| 操作 | 说明 |
|------|------|
| `navigate` | 导航到 URL |
| `click` | 点击元素 |
| `type` | 输入文本 |
| `screenshot` | 截图 |
| `extract` | 提取数据 |
| `fill_form` | 填写表单 |
| `wait` | 等待元素 |
| `scroll` | 滚动页面 |
| `select` | 选择下拉选项 |

### 安全性

- 通过 `approval_gate.py` 进行执行前审批
- 所有操作的完整审计日志
- 数据保护策略执行

---

## 77. LSP 集成 — Language Server Protocol (v0.1)

通过 LSP 提供代码补全、悬停信息、跳转定义、引用搜索和诊断。

### 支持的语言

| 语言 | 服务器 |
|------|--------|
| Python | pyright / pylsp |
| TypeScript | tsserver |
| JavaScript | tsserver |
| Rust | rust-analyzer |
| Go | gopls |
| Java | jdtls |

### 功能

| 功能 | 说明 |
|------|------|
| `completion` | 代码补全 |
| `hover` | 悬停信息 |
| `definition` | 跳转定义 |
| `references` | 查找引用 |
| `diagnostics` | 诊断（错误和警告） |
| `formatting` | 代码格式化 |
| `rename` | 重命名 |

---

## 78. MCP 集成 — Model Context Protocol (v0.1)

通过模型上下文协议（MCP）集成外部工具、资源和提示。

### API 端点

| 端点 | 说明 |
|------|------|
| `GET /mcp/capabilities` | 获取 MCP 服务器能力 |
| `GET /mcp/tools` | 可用工具列表 |
| `POST /mcp/tools/call` | 调用工具 |
| `GET /mcp/resources` | 资源列表 |
| `GET /mcp/prompts` | 提示列表 |

---

## 79. 外部技能搜索与导入 (v0.1)

从 GitHub 和各种注册表搜索技能，一键安装。

### 支持的来源

| 来源 | 说明 |
|------|------|
| `github_agent_skills` | GitHub Agent Skills 仓库 |
| `skills_sh` | skills.sh 注册表 |
| `openclaw` | OpenClaw 注册表 |
| `claude_code` | Claude Code 技能 |
| `git_repo` | 任意 Git 仓库 |
| `url` | 直接 URL 指定 |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /skills/external/search` | 搜索外部技能 |
| `POST /skills/external/import` | 导入并安装技能 |

---

## 80. 输入安全中间件 (v0.1)

自动对所有 API 端点输入应用提示注入扫描和 PII 检测的中间件。

### 检查内容

| 检查 | 说明 |
|------|------|
| **提示注入** | 28+ 模式的 5 级威胁检测 |
| **PII 检测** | 13 类个人信息检测和掩码 |
| **外部数据包装** | 对发送到 LLM 的外部数据添加边界标记 |

### 实现

- `InputSanitizationMiddleware` — 请求体扫描
- 检测到 CRITICAL/HIGH 威胁时拒绝请求（HTTP 422）
- PII 检测仅记录日志（掩码在服务层执行）
