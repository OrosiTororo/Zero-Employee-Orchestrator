> [日本語](../USER_GUIDE.md) | [English](../en/USER_GUIDE.md) | 中文

# 中文用户指南

> **v0.1** | 最后更新: 2026-03-10

## 1. 这个软件是什么？

**Zero-Employee Orchestrator** 是一个 **AI 业务编排平台**。您只需用自然语言描述任务，多个 AI 代理就会自动组建团队进行规划、执行、验证和报告。

### 能做什么

- 输入"调查竞争对手的价格并整理成报告" —— AI 团队自动行动
- **危险操作**（发布、发送、计费）**始终需要人类审批**
- 完整的**审计日志**记录谁用什么模型在何时做了什么
- 失败时自动重新规划和恢复（Self-Healing）

### 与其他 AI 代理的区别

| | 其他 AI 代理（AutoGPT、CrewAI 等） | Zero-Employee Orchestrator |
|---|---|---|
| 任务管理 | 仅在执行期间追踪 | 以工单/规格/计划结构化保存 |
| 质量验证 | 无或单一模型 | Judge Layer（两阶段 + Cross-Model） |
| 审批流程 | 无（完全自主执行） | 危险操作阻断，需人类审批 |
| 故障恢复 | 停止或简单重试 | Self-Healing DAG 自动重新规划 |
| 审计日志 | 无或有限 | 记录所有操作，可追溯 |
| 成本管理 | 无 | 实时追踪 Token 消耗和预算 |
| 经验学习 | 无 | Experience Memory 积累成功/失败模式 |
| 扩展性 | 需要修改代码 | 灵活的 Skill / Plugin / Extension 体系 |

---

## 2. 主要功能

### Design Interview（设计面谈）
接收业务请求后，AI 会提出补充问题以明确需求。

### Spec / Plan / Tasks（规格/计划/任务）
请求内容以"规格书 → 计划 → 任务分解"的形式结构化保存。支持修改和回退。

### Self-Healing DAG
任务依赖关系以有向无环图（DAG）管理。部分任务失败时自动重新规划。

### Judge Layer（质量验证）
AI 输出始终经过两阶段验证：
1. **基于规则的检查**：快速检查禁止操作、凭证泄露等
2. **Cross-Model 验证**：比较多个 LLM 的输出以确认可靠性

### Skill / Plugin / Extension（技能/插件/扩展）
- **Skill**：单一目的处理（如：网页抓取、邮件发送）
- **Plugin**：外部服务集成（如：Slack、Google Drive）—— 可从 GitHub 仓库安装
- **Extension**：UI 和行为自定义

---

## 3. 系统需求

| 项目 | 需求 |
|------|------|
| 操作系统 | Windows 10+、macOS 12+、Ubuntu 22.04+ |
| Python | 3.12 以上 |
| Node.js | 18 以上 |
| 内存 | 4 GB 以上（使用本地 LLM 时推荐 8 GB 以上） |
| 存储空间 | 500 MB 以上（模型文件另需空间） |

---

## 4. LLM（AI）连接方式

| 方式 | 费用 | API 密钥 | 设置 | 推荐用途 |
|------|------|----------|------|---------|
| **Google Gemini 免费 API** | **免费**（有限额） | 需要（免费获取） | 简单 | 最佳起步方式 |
| **Ollama（本地）** | **完全免费** | 不需要 | 需下载模型 | 离线/隐私优先 |
| **订阅模式** | **免费** | **不需要** | **几乎为零** | 测试用 |
| OpenRouter | 按量计费 | 需要 | 普通 | 多模型统一管理 |
| OpenAI / Anthropic / Google | 按量计费 | 需要 | 普通 | 生产环境/高质量 |

---

## 5. 安装

### 桌面应用（GUI 版 —— 简单）

1. 从 [Releases 页面](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) 下载最新版本
2. 运行安装程序
3. 启动应用并按照设置向导操作

### 从源代码启动（面向开发者）

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
chmod +x setup.sh start.sh
./setup.sh
cp apps/api/.env.example apps/api/.env
# 编辑 .env 添加 LLM API 密钥
./start.sh
```

在浏览器中打开 **http://localhost:5173**。

---

## 6. 界面和基本操作

### 仪表板
- **任务请求框**：用自然语言输入任务
- **活跃工单**：当前进行中的任务列表
- **待审批**：需要您确认的操作数量
- **代理状态**：AI 代理的运行状态
- **成本摘要**：今日/本周/本月 API 成本

### 审批界面
当 AI 请求需要审批的操作时：
- **批准**：允许执行
- **拒绝**：取消执行
- **要求修改**：附加评论请 AI 重新考虑

---

## 7. 技能和插件

### 添加技能
1. 打开"技能" → "创建技能"
2. 用自然语言描述技能功能
3. AI 自动生成技能代码
4. 审查后保存

### 从 GitHub 添加插件
可以从 GitHub 仓库安装插件：

```
POST /api/v1/registry/plugins/search-external?query=关键词
POST /api/v1/registry/plugins/import?source_uri=https://github.com/user/plugin-repo
```

用户可以共享和发布插件，无需开发者额外操作。

### 内置插件

| 插件 | 用途 |
|------|------|
| `ai-avatar`（分身AI） | 学习您的判断标准和文风，进行代理审查 |
| `ai-secretary`（秘书AI） | 早间简报、行动建议、连接您和 AI 组织 |
| `discord-bot` | 从 Discord 创建工单、查看进度、审批 |
| `slack-bot` | 从 Slack 创建工单、查看进度、审批 |
| `line-bot` | 从 LINE 创建工单、查看进度、审批 |

---

## 8. 常见问题（FAQ）

### Q: 可以免费使用吗？

**A:** 可以。有三种方式：
1. **Google Gemini 免费 API（推荐）**：从 Google AI Studio 获取免费 API 密钥（无需信用卡）
2. **Ollama（本地 LLM）**：将模型下载到电脑 —— 完全免费、离线、无限制
3. **订阅模式**：无需 API 密钥即可使用（但稳定性较差）

### Q: 数据存储在哪里？

**A:** 默认情况下，数据本地存储在 `apps/api/zero_employee_orchestrator.db`（SQLite 文件）中。不会发送到云端。

### Q: 可以创建自己的分身AI和秘书AI吗？

**A:** 可以。它们可以作为插件添加。分身AI学习您的判断标准和文风。秘书AI生成早间简报，连接您和 AI 组织。

### Q: 可以从 Discord / Slack 操作吗？

**A:** 可以。安装 Discord / Slack / LINE 的 Bot 插件后，您可以直接从聊天应用创建工单、查看进度、审批操作和与 AI 对话。

---

## 相关文档

| 文件 | 内容 |
|------|------|
| `README.md` | 快速入门和技术栈 |
| `docs/SECURITY.md` | 安全配置和生产环境部署 |
| `docs/dev/DESIGN.md` | 实现设计书（DB、API、状态转换） |
| `docs/dev/BUILD_GUIDE.md` | 开发者构建指南 |
