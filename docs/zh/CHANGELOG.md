# Changelog

> [日本語](../CHANGELOG.md) | [English](../en/CHANGELOG.md) | 中文

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-03-12 — 安全加固 & 文件附件支持

### 安全

- **bcrypt 升级为必需依赖** — 移除 SHA-256 回退，强制使用 bcrypt 进行密码哈希
- **添加速率限制** (`slowapi`) — 在认证端点实现速率限制（注册: 5次/分钟, 登录: 10次/分钟）
- **RAG 文件权限修复** — 将 `index.json` / `idf.json` 限制为 `0o600`（仅所有者可读写）
- **RAG 输入验证** — 添加内容大小上限 (10 MB) 和元数据键数限制
- **认证端点保护** (v0.1.0 修复) — 为审批/配置/注册表 API 添加认证
- **CORS 限制加强** (v0.1.0 修复) — 将通配符改为明确的方法和头部列表
- **UUID 输入验证** (v0.1.0 修复) — 修复对无效 UUID 返回 400 的问题

### Added

- **基于文件附件的计划创建** — 在 Design Interview 中附加文件，并集成到规格书生成的上下文中
  - `POST /api/v1/tickets/{ticket_id}/interview/attach` — 文件上传
  - `GET /api/v1/tickets/{ticket_id}/interview/attachments` — 附件列表
  - 支持文本、代码、图片和 PDF（自动文本提取 + 多编码支持）
  - 提取的文本自动集成到规格书的"参考资料"部分
- **Local Context Skill 图片支持** — 图片文件读取（Base64 编码 + PNG/JPEG 尺寸检测）
  - 支持 `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg`
  - SVG 也作为文本解析
  - 10 MB 大小限制
- **扩展文件类型支持** — 大幅扩充 Local Context Skill 的支持格式
  - 代码: `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.h`, `.html`, `.xml`, `.css`, `.sql`, `.sh`
  - 多编码自动检测（UTF-8, Shift_JIS, EUC-JP, CP932）

---

## [0.1.0] - 2026-03-11 — Platform v0.1 (Consolidated Release)

### Added (v0.1 Final — 2026-03-11)

- **头脑风暴（对话伙伴）功能** (`services/multi_model_service.py`, `api/routes/multi_model.py`, `pages/BrainstormPage.tsx`)
  - AI顾问头脑风暴会话管理（创建、发送消息、搜索、归档）
  - 多模型头脑风暴支持（同时使用 GPT / Gemini / Claude）
  - 会话类型：brainstorm / debate / review / ideation / strategy
- **多模型对比功能** (`services/multi_model_service.py`)
  - 将相同输入发送到多个模型，并排比较回答
  - 每个模型的字符数、token 数、延迟测量
  - 比较结果的持久化存储和列表显示
- **对话记忆** (`services/multi_model_service.py`)
  - 永久保存用户与AI组织的所有对话
  - 关键词搜索过去的对话（支持用户询问过去的讨论内容）
  - 对话统计（总消息数、总字符数、按角色、按类型）
- **精确字符计数（TextAnalyzer）** (`services/multi_model_service.py`)
  - 使用 Python len() 的 Unicode 精确字符计数
  - 按平假名、片假名、汉字、ASCII、数字分类
  - 字符数验证（最小/最大字符数检查）
  - 文本分析 API：POST /text/analyze
- **按角色设置模型** (`services/multi_model_service.py`)
  - 用户可自由为每个代理角色分配AI模型
  - 代理个别设置与全局回退
  - 可配置回退模型、max_tokens、temperature、系统提示
- **动态代理组织管理** (`services/agent_org_service.py`)
  - 按预设角色添加代理（秘书、顾问、PM、研究员、工程师等）
  - 创建、列出和删除自定义角色
  - 更新代理角色（名称、描述、模型、自主级别、系统提示）
  - 删除代理（转为退役状态）
- **秘书和顾问角色定义** (`services/agent_org_service.py`)
  - 秘书：AI组织与用户的桥梁、知识库、信息管理
  - 顾问：头脑风暴伙伴、多角度建议、秘书与用户的桥梁
  - 每个角色都有预定义的系统提示
- **自然语言组织管理** (`services/agent_org_service.py`)
  - 用自然语言向AI组织提交请求（如"添加一个顾问代理"）
  - 基于关键词的动作和角色自动检测
  - 自动执行模式（置信度高时自动执行）
  - 功能请求的持久化存储和列表显示
- **前端 BrainstormPage** (`pages/BrainstormPage.tsx`)
  - 头脑风暴会话管理UI（创建、收发消息、搜索）
  - 多模型对比UI（模型选择、输入、并排结果显示）
  - 按角色模型设置UI（配置列表、可用角色显示）
  - AI组织管理UI（自然语言请求、角色列表、代理添加）
  - 实时字符计数显示
- **ZEO-Bench — Judge Layer 定量评估基准** (`tests/zeo_bench.py`)
  - 200 道测试题集，定量评估 Cross-Model Verification 的精度
  - 4 个类别：事实准确性 (50题)・矛盾检测 (70题)・假阳性 (40题)・修正质量 (40题)
  - 与单模型自评估的检测率数值比较
  - `BenchmarkReport` 提供各类别分析和摘要
- **Cross-Model Verification 改进** (`orchestration/judge.py`)
  - 语义相似度检验（token 级 Jaccard 相似度）
  - 数值容差比较（5% 以内视为一致）
  - 矛盾检测引擎：否定模式・数值不一致・结论矛盾・时序不一致
  - 置信度加权评分（按同意模型数量加权）
  - 详细矛盾报告（contradiction_details）
- **通用领域 Skill 模板** (`skills/builtin/domain_skills.py`)
  - ContentCreatorSkill — 任意平台的内容生成（博客・社交媒体・邮件・视频脚本・演示文稿）
  - CompetitorAnalysisSkill — 任意领域的竞争分析（市场分析・SWOT・价格比较・功能比较）
  - TrendAnalysisSkill — 任意领域的趋势分析（市场・技术・社交媒体・行业趋势）
  - PerformanceAnalysisSkill — 任意业务的绩效分析（KPI・ROI・转化率・参与度）
  - StrategyAdvisorSkill — 跨领域战略顾问（下一步行动・资源分配・风险评估）
  - 所有 Skill 支持 i18n (ja/en/zh) 和 Artifact Bridge 兼容
- **Artifact Bridge 强化** (`orchestration/artifact_bridge.py`)
  - auto_link_outputs_to_inputs：DAG 内成果物自动连接
  - 跨领域转换：如 trend_report → market_context 的自动类型转换
  - 兼容性矩阵：成果物类型间的自动转换规则
  - find_compatible_artifacts：搜索兼容的成果物
  - build_artifact_pipeline：Skill 链的成果物流程设计
- **Self-Healing DAG 混沌测试** (`tests/test_chaos_dag.py`)
  - 20+ 个故障注入测试用例
  - 单节点故障・级联故障・并行分支故障・全分支故障
  - 恢复成功率和恢复时间基准测试
  - 策略效果比较（retry / skip / replan）
  - DAG 完整性验证（孤立节点・依赖关系解析・已完成节点保留）

### Fixed (post-release)

- CI 工作流 `claude-code-review.yml`: 修复 bot PR（Dependabot 等）的审查跳过处理
- CI 工作流 `create-release.yml`: 修正 CHANGELOG 路径为 `docs/CHANGELOG.md`
- 发布工作流 `release.yml`: 将 Tauri v2 构建 Action 和资产表更新至最新版
- 前端 `ReleasesPage.tsx`: 添加 GitHub Releases 未发布时的回退显示
- 文档整理: 将 md 文件重新组织为 `docs/`（面向用户）和 `docs/dev/`（面向开发者）
- 安全性: 添加 Dependabot 配置、安全检查脚本、发布前检查清单

### Added

- **运行时配置管理 — 无需 .env 的 API Key 设置** (`core/config_manager.py`, `api/routes/config.py`)
  - 通过 CLI 命令 `zero-employee config set/get/list/delete/keys` 设置 API Key 和执行模式
  - 通过 Web API `GET/PUT /api/v1/config` 在应用内更改设置
  - 在设置页面（SettingsPage）添加 LLM API Key 输入 UI
  - 设置保存至 `~/.zero-employee/config.json`（文件权限 600 保护）
  - 优先级: 环境变量 > config.json > .env > 默认值
  - 敏感值掩码显示、Provider 连接状态 API
- **知识库 — 用户设置和文件权限的持久化存储** (`orchestration/knowledge_store.py`)
  - 记忆文件/文件夹的操作权限（规划时无需再次询问）
  - 记忆业务资料文件夹的位置
  - 用户设置和偏好的持久化
  - 变更检测（检测与上次信息的差异并通知）
  - Knowledge API（`/knowledge/*`）— 存储、搜索、变更确认
- **免登录匿名会话**
  - 通过 `POST /auth/anonymous-session` 即可立即开始使用
  - 之后可绑定账户（`POST /auth/link-account`）
  - 登录后可在多设备间共享状态
  - 前端: 添加"无需登录即可开始"按钮
- **Web 仪表盘 — 代理监控** (`pages/AgentMonitorPage.tsx`)
  - 在浏览器中实时监控代理状态
  - 运行中任务、会话、假设验证、错误监控 4 个标签页
  - 5 秒自动刷新
  - 显示 Sentry 集成的错误统计
- **权限管理仪表盘** (`pages/PermissionsPage.tsx`)
  - 文件/文件夹权限设置 UI
  - 业务文件夹位置注册 UI
  - 变更检测确认 UI
- **沙箱环境** (`worker/app/sandbox/cloud_sandbox.py`)
  - 本地执行、Docker 执行、Cloudflare Workers 执行的多模式支持
  - 本地代码直接编辑（带权限检查）
  - 在 Workers 上执行 JavaScript/TypeScript
  - 一键部署至 Cloudflare Workers
- **Rootless 容器支持** (`Dockerfile`, `docker-compose.yml`)
  - 无需 root 权限即可在容器中运行
  - 以非 root 用户 (UID 1000) 执行
  - 通过 Docker Compose 一键启动所有服务
- **外部技能导入** (`integrations/external_skills.py`)
  - 从 GitHub Agent Skills 仓库搜索和导入
  - 从 skills.sh 平台搜索和导入
  - OpenClaw / Claude Code 格式的技能转换
  - 从任意 Git 仓库获取清单文件
  - `POST /skills/external/search` / `POST /skills/external/import`
- **MCP 服务器** (`integrations/mcp_server.py`)
  - 符合 Model Context Protocol 的服务器实现
  - 8 个内置工具（工单、任务、技能、知识库、审计、监控、假设验证）
  - 4 个资源（仪表盘、代理、技能、知识库）
  - 2 个提示词模板
  - MCP API（`/mcp/*`）
- **Cloudflare 部署支持**
  - 现有的 `apps/edge/full/` Workers 应用
  - 通过 `deploy_to_workers()` 方法一键部署
  - 自动生成 wrangler.toml
- **AI 调查工具** (`integrations/ai_investigator.py`)
  - AI 参考日志和数据库完成调查
  - 安全的只读 SELECT 数据库查询
  - 审计日志搜索、错误模式分析、任务执行历史
  - 获取系统指标
  - SQL 注入防护（禁止关键字、仅允许 SELECT 语句）
  - Investigation API（`/investigate/*`）
- **Sentry 集成** (`integrations/sentry_integration.py`)
  - 与 Sentry SDK 集成（无 SDK 时使用内置事件存储）
  - 异常捕获、消息捕获、性能事务
  - 错误统计、事件列表
  - 告警回调功能
  - Sentry API（`/sentry/*`）
- **人类/AI 账户分离（IAM）** (`security/iam.py`)
  - AI 代理专用服务账户
  - 人类和 AI 使用不同范围的权限管理
  - 自动排除 AI 禁止的权限（密钥读取、管理员、审批）
  - 凭据文件保护（owner read only 权限）
  - IAM API（`/iam/*`）
- **假设并行验证引擎** (`orchestration/hypothesis_engine.py`)
  - 多代理假设验证和审查循环
  - 证据的支持/反驳评分计算
  - 交叉审查的共识判定
  - 假设状态管理（提议 -> 调查 -> 证据 -> 审查 -> 确认/反驳）
  - Hypothesis API（`/hypotheses/*`）
- **代理会话管理** (`orchestration/agent_session.py`)
  - 保持上下文的多轮交互
  - idle 状态待机（保持上下文）和恢复
  - 工作记忆（会话内临时存储）
  - 数据库持久化与内存的混合方案
  - Session API（`/sessions/*`）

### Changed

- `core/config.py`: 添加 SENTRY_DSN, SANDBOX_MODE, CLOUDFLARE_ACCOUNT_ID, CREDENTIAL_DIR 配置
- `main.py`: 添加新模型（knowledge_store, agent_session, iam）的导入，添加 Sentry/MCP 初始化
- `api/routes/__init__.py`: 添加 knowledge, platform 路由
- `api/routes/auth.py`: 添加匿名会话、账户绑定、可选认证
- `shared/hooks/use-auth.ts`: 添加 isAnonymous 状态、startAnonymous/linkAccount 方法
- `app/router.tsx`: 添加 PermissionsPage, AgentMonitorPage 路由
- `shared/ui/Layout.tsx`: 在侧边栏添加代理监控、权限管理导航
- `pages/LoginPage.tsx`: 添加"无需登录即可开始"按钮

- **外部工具连接增强** (`tools/connector.py`)
  - 添加 CLI 工具连接类型（支持 gws / gh / aws / gcloud / az 等 CLI 工具）
  - 添加 gRPC、GraphQL 连接类型
  - 添加服务账户认证类型
- **Plugin 的 GitHub 导入功能** (`integrations/external_skills.py`)
  - 从 GitHub 仓库直接搜索和导入插件（`topic:zeo-plugin`）
  - 从社区插件注册表搜索和导入
  - `POST /api/v1/registry/plugins/search-external` — 外部插件搜索
  - `POST /api/v1/registry/plugins/import` — 从 GitHub 导入插件
  - 用户可以共享和发布插件，无需开发者额外工作即可集成外部服务
- **文档多语言化** (USER_GUIDE.md, README.md)
  - USER_GUIDE.md: 支持日语、英语、中文 3 种语言
  - README.md: 以 3 种语言面向非工程师解说 Releases 部分
  - 添加下载文件选择指南
- **遗留文件迁移**
  - 将 `ZPCOS_FEATURES_AND_IMPROVEMENTS.md` 中有用的想法整合到现有文档中
  - 将元技能概念、安全自测、iPaaS 集成等想法反映到 DESIGN.md / FEATURES.md
  - 删除遗留文件

- 统一所有文档的版本标记为 v0.1
- `CHANGELOG.md`: 将所有发布合并为 v0.1
- `docs/FEATURES.md`: 添加外部工具连接、社区插件部分，添加功能膨胀审查结果
- `docs/FEATURE_BOUNDARY.md`: 添加社区插件共享方针，添加 v0.1 功能边界修订
- `ABOUT.md`: 统一 v0.1 标记，将对比对象改为 AI 代理
- `docs/OVERVIEW.md`: 统一 v0.1 标记，更新页面数为 21，添加功能膨胀审查
- `USER_GUIDE.md`: 修正方法 C（订阅模式）的 Provider 信息，将对比对象改为 AI 代理
- `README.md`: 在各部分以三国语言（日语、英语、中文）添加目录结构，更新至最新结构
- `DESIGN.md`: 更新页面数为 21，在目录结构中添加 integrations/ 和 security/IAM
- `CLAUDE.md`: 添加 integrations/ 模块的扩展功能分类说明

### Changed — v0.1 功能边界审查

以下功能从核心功能重新分类为扩展功能（仍包含在代码库中，未来计划分离）:
- `integrations/sentry_integration.py` → Extension
- `integrations/ai_investigator.py` → Skill
- `orchestration/hypothesis_engine.py` → Plugin
- `integrations/mcp_server.py` → Extension
- `integrations/external_skills.py` → Extension

### Initial Implementation (Pre-release — 2026-03-09)

- 9 层架构的初始实现
  - User Layer / Design Interview / Task Orchestrator / Skill Layer / Judge Layer / Re-Propose Layer / State & Memory / Provider Interface / Skill Registry
- FastAPI 后端 (`apps/api`)
  - 认证 (OAuth PKCE)、公司、代理、工单、任务、审批、Heartbeat、预算管理的各 REST API
  - SQLAlchemy 2.x (async) + Alembic 迁移
  - 通过 LiteLLM Router 实现多 LLM 网关
- React 19 + TypeScript 前端 (`apps/desktop/ui`)
  - 仪表盘、工单、代理、设置页面
  - 基于 shadcn/ui + Tailwind CSS 的设计系统
  - 基于 TanStack Query + Zustand 的状态管理
- Tauri v2 桌面应用 (`apps/desktop`)
  - 支持 Windows (.msi / .exe)、macOS (.dmg)、Linux (.AppImage / .deb)
- 编排引擎
  - 基于 Self-Healing DAG 的动态任务重构
  - Two-stage Detection + Cross-Model Verification (Judge Layer)
  - Experience Memory + Failure Taxonomy
  - 基于状态机的执行管理
- CI/CD 管线
  - 通过 GitHub Actions 实现自动 Lint、测试、构建
  - 多平台 Tauri 构建和发布
  - Cloudflare Workers 部署
- 文档
  - README、DESIGN.md、MASTER_GUIDE.md
  - 各部分实现指南 (instructions_section2~7)

## Development History (Pre-release milestones, consolidated into v0.1.0)

## [0.5.0] - 2026-03-10 — Skills Management

### Added

- **自然语言技能生成引擎** (`services/skill_service.py`)
  - 只需用自然语言描述技能功能，即可自动生成清单文件 (skill.json) 和执行代码 (executor.py)
  - LLM 驱动生成 + 模板回退（LLM 不可用时也能保证正常工作）
  - 生成代码的自动安全检查（检测 16 种危险模式）
  - 安全报告生成（risk_level: low/medium/high、权限要求、外部连接检测）
  - `POST /api/v1/registry/skills/generate` 端点
- **Skill / Plugin / Extension 完整 CRUD API**
  - 所有实体支持 GET（列表/详情）/ POST（创建）/ PATCH（更新）/ DELETE（删除）
  - 基于 slug 的重复检查
  - 启用/禁用切换（`enabled` 标志）
  - 过滤: status, skill_type, include_disabled
- **系统保护技能功能** (`is_system_protected`)
  - 保护系统运行所必需的 6 个内置技能
    - spec-writer, plan-writer, task-breakdown, review-assistant, artifact-summarizer, local-context
  - 在 API 层面拒绝删除受保护技能（HTTP 403）
  - 在 API 层面拒绝禁用受保护技能（HTTP 403）
  - 应用启动时自动注册系统技能并设置保护标志
- **Plugin / Extension 管理服务** (`services/registry_service.py`)
  - Plugin: 完整 CRUD + 系统保护 + 启用/禁用切换
  - Extension: 完整 CRUD + 系统保护 + 启用/禁用切换
  - 拒绝删除和禁用受保护的 Plugin/Extension
- **前端技能管理 UI** (`SkillsPage.tsx`)
  - 通过 API 联动显示技能列表（实时获取）
  - 技能启用/禁用切换开关
  - 技能删除（系统保护技能在 UI 层面也显示锁定状态）
  - 系统保护徽章显示
  - 搜索过滤（名称、描述、slug）
- **前端技能生成 UI** (`SkillCreatePage.tsx`)
  - 自然语言输入区域（10-5000 字，字数计数器）
  - 安全检查结果的可视化显示（通过/未通过、风险等级显示）
  - 生成的清单文件 (JSON) 和代码 (Python) 预览
  - 安全检查通过后的"注册技能"按钮
  - 安全报告详情显示
- **前端插件管理 UI** (`PluginsPage.tsx`)
  - 通过 API 联动显示列表
  - 新插件添加表单
  - 启用/禁用切换、删除（受保护插件显示锁定状态）
  - 搜索过滤

### Changed

- **Skill / Plugin / Extension 模型** (`models/skill.py`)
  - 添加 `is_system_protected` 列（Boolean, default=False）
  - 添加 `enabled` 列（Boolean, default=True）
  - 添加 `generated_code` 列（仅 Skill，Text 类型）
  - 为 slug 添加 `unique=True` 约束
- **注册表 API** (`api/routes/registry.py`)
  - 从基本的 list/install 全面重写为完整 CRUD + 自然语言生成
  - 改为通过服务层调用（从直接 SQLAlchemy 改为 services.skill_service / registry_service）
  - 使用适当的 HTTP 状态码（201 Created, 403 Forbidden, 404 Not Found, 409 Conflict）
- **注册表 Schema** (`schemas/registry.py`)
  - 添加 `SkillUpdate`, `PluginUpdate`, `ExtensionUpdate`
  - 添加 `SkillGenerateRequest`, `SkillGenerateResponse`
  - 添加 `RegistryDeleteResponse`
  - 在所有 Read Schema 中添加 `is_system_protected`, `enabled` 字段
- **应用启动** (`main.py`)
  - 在启动时添加系统必需技能的自动注册处理

## [0.4.0] - 2026-03-09

### Added

- **AI Avatar Plugin（分身 AI）** (`plugins/ai-avatar/`)
  - 学习用户的判断标准、文风、价值观并构建画像
  - 与 Judge Layer 联动（将用户的判断模式作为自定义规则提供）
  - 代理审查、文风再现、审批模式学习
  - 用户画像加密后本地保存
- **AI Secretary Plugin（秘书 AI）** (`plugins/ai-secretary/`)
  - 早间简报（待审批、进行中任务、今日计划）
  - 下一步行动建议（基于紧急度和重要度的推荐排序）
  - 进度摘要、提醒、委派路由
  - 与 Discord / Slack / LINE Bot Plugin 联动的简报推送
- **LINE Bot Plugin** (`plugins/line-bot/`)
  - 通过 LINE Messaging API 创建工单、查看进度、审批操作
  - 通过 Flex Message 实现审批对话框
  - 通过 Rich Menu 实现快捷操作

### Changed

- **Discord Bot Plugin** 更新至 v0.2.0
  - 添加线程内对话、简报推送、交互按钮
  - 添加与秘书 AI / 分身 AI Plugin 的联动功能
  - 定义 `/zeo` 斜杠命令体系
- **Slack Bot Plugin** 更新至 v0.2.0
  - 添加线程内对话、简报推送、Block Kit 交互
  - 添加与秘书 AI / 分身 AI Plugin 的联动功能
  - 定义 `/zeo` Slash Command 体系
- **文档全面更新**
  - `USER_GUIDE.md`: 修正 LLM 连接方法的推荐优先级（优先推荐 Gemini 免费 API / Ollama），添加分身 AI、秘书 AI、聊天集成说明，更新 FAQ
  - `README.md`: 在日语、英语、中文部分添加新功能（分身 AI、秘书 AI、聊天集成），更新目录结构
  - `ABOUT.md`: 添加分身 AI、秘书 AI、聊天集成部分，更新 LLM 推荐至最新
  - `docs/FEATURES.md`: 将 Plugin / Extension 列表更新为详细表格，新增附加功能部分
  - `docs/OVERVIEW.md`: 更新外部工具连接部分，添加分身 AI、秘书 AI 说明
  - `docs/FEATURE_BOUNDARY.md`: 添加 AI 代理扩展 Plugin、聊天工具集成 Plugin 部分
  - `DESIGN.md`: 在 Plugin 示例中添加分身 AI、秘书 AI、聊天 Bot

## [0.3.0] - 2026-03-09

### Added

- **Dynamic Model Registry** (`providers/model_registry.py`)
  - 通过 `model_catalog.json` 实现 LLM 模型的外部配置文件管理
  - 无需代码更改即可添加、删除、废弃和指定后继模型
  - 废弃模型自动回退（指定 successor 后自动切换至后继模型）
  - Provider 健康检查（API 可用性的定期确认）
  - 成本信息的动态更新
- **Model Registry API** (`/api/v1/models/*`)
  - 模型列表、按模式分类目录、Provider 健康检查
  - 模型废弃标记、成本更新、目录重新加载
- `model_catalog.json` — 模型目录定义文件（全部模型、模式、质量 SLA）
- **可观测性 — 推理追踪、通信日志、执行监控**
  - `orchestration/reasoning_trace.py` — 分步记录代理的推理过程（19 种步骤、4 个确信度级别）
  - `orchestration/agent_communication.py` — 记录多代理间的全部通信（18 种消息类型、线程管理）
  - `orchestration/execution_monitor.py` — 实时执行监控、WebSocket 推送
  - `api/routes/observability.py` — Observability API（推理追踪、通信日志、监控仪表盘）
  - 前端 TypeScript 类型定义（ReasoningTrace, AgentMessage, ActiveExecution 等）

### Changed

- `gateway.py`: 将硬编码的模型目录改为从 ModelRegistry 动态加载
- `cost_guard.py`: 将成本表改为从 ModelRegistry 动态生成
- `quality_sla.py`: 将质量模式别模型列表改为从 ModelRegistry 动态加载
- `docs/FEATURES.md`: 修正旧模型名称，添加动态管理说明，添加 Observability 部分
- `CLAUDE.md`: 硬编码模型列表改为动态管理，在设计原则中添加代理透明性

## [0.2.0] - 2026-03-09

### Changed

- 将所有旧 LLM 模型引用更新至最新版本
  - g4f_provider.py: gpt-4o → gpt-5.4, gpt-4o-mini → gpt-5-mini, claude-haiku-4-5 → claude-haiku-4-5-20251001
  - cost_guard.py: claude-haiku-4-5 → claude-haiku-4-5-20251001
  - quality_sla.py: claude-haiku-4-5 → claude-haiku-4-5-20251001
  - docs/BUILD_GUIDE.md: 将全部成本表和质量模式设置更新至最新模型
- DESIGN.md: 将状态转换更新为已实现的定义，将目录结构与实际代码库同步

### Added

- 仓库层 (`repositories/`)
  - `base.py` — 通用 CRUD 仓库基础 (BaseRepository)
  - `ticket_repository.py` — 工单和线程 DB 操作
  - `audit_repository.py` — 审计日志专用仓库 (append-only)
- Heartbeat 模块 (`heartbeat/`)
  - `scheduler.py` — Heartbeat 触发条件（9 种）、执行管理、操作记录
- 策略模块 (`policies/`)
  - `approval_gate.py` — 危险操作的自动检测与审批请求（12 个类别）
  - `autonomy_boundary.py` — 自主执行/需审批的边界判定
- 安全模块 (`security/`)
  - `secret_manager.py` — 凭据的安全存储、掩码、轮换支持
  - `sanitizer.py` — 保存/共享时密钥值和个人信息的自动掩码
- 工具连接模块 (`tools/`)
  - `connector.py` — MCP/Webhook/REST API 等外部工具连接管理
- 编排扩展 (`orchestration/`)
  - `knowledge_refresh.py` — Knowledge Pipeline（7 个阶段）、知识的分类存储（5 种）
  - `artifact_bridge.py` — 工序间的成果物传递和版本管理
- 前端类型定义 (`shared/types/index.ts`)
  - 对应后端 Schema §38 的所有实体的 TypeScript 类型

[0.1.1]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.1
[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
[0.2.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.2.0
[0.3.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.3.0
[0.4.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.4.0
[0.5.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.5.0
