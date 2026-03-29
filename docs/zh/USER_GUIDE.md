> [日本語](../ja-JP/USER_GUIDE.md) | [English](../USER_GUIDE.md) | 中文

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

### 分身AI 和秘书AI

**分身AI（AI Avatar）** 学习您的判断模式和文风，作为您的"分身"行动：
- 在 Judge Layer 的质量判定中反映您的价值观
- 在您不在时审查任务和判断优先级（最终审批权限始终保留在您手中）
- 以您的文风和语气起草内容

**秘书AI（AI Secretary）** 作为连接您和 AI 组织的"中枢"运作：
- 早间简报（待审批、进行中任务、今日日程）
- 带优先级的下一步行动建议
- 通过 Discord / Slack / LINE 发送简报

### 从聊天工具操作

安装 Discord / Slack / LINE 的 Bot 插件后，可以从日常使用的聊天工具向 AI 组织发送指令。

```
/zeo ticket 创建竞争分析报告    → 创建工单
/zeo status                    → 查看进行中的任务
/zeo approve 12345             → 审批操作
/zeo briefing                  → 今日简报
/zeo ask 这个方案有什么风险？    → 向 AI 提问
```

需要授权的危险操作也会在聊天工具中显示审批对话框。

---

## 8. 工单（业务请求）的使用方法

### 创建工单

1. 在仪表板的输入框中用自然语言输入业务内容
2. 点击「提交」按钮
3. AI 开始需求确认（Design Interview），对不明确的地方提出问题
4. 回答问题后，系统自动创建计划并开始执行

### 中途回退/修改

在工单详情页面：
- **回退**: 返回上一步并请求修改
- **添加评论**: 输入追加的指示或信息
- **取消**: 中断工单

### 查看成果物

工单完成后，成果物保存在「成果物（Artifacts）」标签页中。
- 支持多种格式：文本、JSON、代码等
- 有版本控制，可以回退到之前的版本

---

## 9. 审批流程

Zero-Employee Orchestrator 基于「**危险操作必须由人类审批**」的设计原则。

### 需要审批的操作

- 向外部服务发布/发送（SNS、邮件、Slack 等）
- 文件的删除或覆盖
- 涉及计费/支付的操作
- 权限或访问设置的变更
- 向生产环境部署/发布

### 审批步骤

1. 仪表板的「待审批」计数增加并发出通知
2. 打开「审批」界面，确认内容
3. **批准**: 允许执行
4. **拒绝**: 取消执行
5. **要求修改**: 附加评论，请 AI 重新考虑

> 所有已审批的操作记录都保存在审计日志中。

---

## 10. 成本管理

### 执行模式设置

通过在 `apps/api/.env` 中设置 `DEFAULT_EXECUTION_MODE` 来控制成本：

| 模式 | 说明 | 推荐用途 |
|------|------|---------|
| `quality` | 最高质量模型（Claude Opus, GPT, Gemini Pro） | 重要成果物 |
| `speed` | 高速模型（Claude Haiku, GPT Mini, Gemini Flash） | 简单任务 |
| `cost` | 低成本模型（Haiku, Mini, Flash Lite, DeepSeek） | 批量处理 |
| `free` | 免费模型（Gemini 免费额度 / Ollama 本地） | 测试/开发 |
| `subscription` | 免费（通过 g4f，无需 API 密钥） | 试用 |

### 预算设置

在设置画面的「成本管理」中设置月度预算上限。接近上限时会发出告警通知。

---

## 11. 故障排除

### `./setup.sh` 无法执行

```bash
chmod +x setup.sh start.sh
./setup.sh
```

### 端口被占用

```bash
# 检查占用的端口
lsof -i :18234   # 后端
lsof -i :5173    # 前端

# 停止进程后重启
kill <PID>
./start.sh
```

### AI 无响应/出错

1. 确认 `.env` 文件中的 API 密钥是否正确设置
2. 如果使用 Ollama：确认 `ollama serve` 是否在运行
3. **订阅模式时**: 外部服务可能暂时不可用（建议切换到 Gemini 免费 API 或 Ollama）
4. 查看后端日志：
   ```bash
   cd apps/api
   source .venv/bin/activate
   uvicorn app.main:app --reload
   ```

### 订阅模式出现「g4f error」

订阅模式依赖外部 Web 服务，可能暂时不可用。

- 等待片刻后重试
- 切换到其他模型（例如：`g4f/Copilot` → `g4f/GeminiPro`）
- 切换到更稳定的 Gemini 免费 API 密钥

### Gemini API 错误

- `RESOURCE_EXHAUSTED`: 已达到免费额度上限 → 等待 1 分钟或升级到付费计划
- `API_KEY_INVALID`: 密钥错误 → 在 Google AI Studio 中重新确认

### Ollama 无法连接

```bash
# 确认 Ollama 是否在运行
curl http://localhost:11434/api/tags

# 如果未运行
ollama serve
```

### 重置数据库

```bash
# 删除 SQLite 文件并重启（表会自动创建）
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

### Python 虚拟环境错误

```bash
cd apps/api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

---

## 12. 常见问题（FAQ）

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

**A:** 可以。安装 Discord / Slack / LINE 的 Bot 插件后，您可以直接从聊天应用创建工单、查看进度、审批操作和与 AI 对话。示例命令：`/zeo ticket 创建竞争分析报告`

---

### Q: AI 会不会做出错误操作？

**A:** 以下机制确保安全性：
- **Judge Layer**: AI 的输出经过两阶段验证
- **审批流程**: 危险操作始终被拦截，需要人类确认
- **审计日志**: 所有操作均有记录，可追溯

---

### Q: 可以多人使用吗？

**A:** 可以。按组织（Company）单位管理用户，通过基于角色的访问控制（RBAC）设置权限。

| 角色 | 权限 |
|------|------|
| Owner | 全部权限 |
| Admin | 组织设置、审批、审计日志 |
| User | 业务请求、查看 |
| Auditor | 仅查看 |
| Developer | Skill/Plugin 开发 |

---

### Q: 可以离线使用吗？

**A:** 可以。使用 Ollama 的本地 LLM 即可在无网络连接的情况下运行（仅首次下载模型时需要网络连接）。

---

### Q: 可以从手机操作吗？

**A:** 由于支持 Web 浏览器，可以从智能手机的浏览器访问（响应式设计）。此外，通过 Discord / Slack / LINE 的 Bot 插件，也可以从手机聊天应用进行操作。

---

## 相关文档

| 文件 | 内容 |
|------|------|
| `README.md` | 快速入门和技术栈 |
| `docs/SECURITY.md` | 安全配置和生产环境部署 |
| `docs/dev/DESIGN.md` | 实现设计书（DB、API、状态转换） |
| `docs/dev/BUILD_GUIDE.md` | 开发者构建指南 |
