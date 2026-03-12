# Roadmap

> 日本語 | [English](#english) | [中文](#中文)

> 最終更新: 2026-03-12
> 現在のバージョン: v0.1

---

## 現在の状態 (v0.1)

v0.1 では、9層アーキテクチャの完全実装、ZEO-Bench による Judge Layer の定量評価、汎用ドメイン Skill テンプレート、Self-Healing DAG のカオステスト、ランタイム設定管理、ナレッジストア等の基盤機能が完成しています。

## v0.2 — 接続性と実用性の強化

| 優先度 | 機能 | 説明 |
|:------:|------|------|
| 高 | **Tool Connector 実装完成** | REST API / MCP / GraphQL / CLI ツールの実行を stub から本実装に移行 |
| 高 | **タスク実行中のユーザー入力要求** | 実行中に追加情報やファイルをユーザーに求めるメカニズム |
| 高 | **ユーザーリソースインポート** | 業務マニュアル・ルール・資料フォルダの指定と AI 学習への活用 |
| 高 | **iPaaS 連携 (n8n / Zapier / Make)** | 既存のワークフロー自動化ツールとのシームレスな接続 |
| 中 | **成果物エクスポート** | PDF / Google Docs / Notion / n8n へのエクスポート機能 |
| 中 | **E2E テスト** | Playwright によるフロントエンド〜バックエンド一気通貫テスト |
| 中 | **LLM レスポンスモック** | テスト時に実 API を呼ばないモック基盤 |

## v0.3 — AI 組織の高度化

| 優先度 | 機能 | 説明 |
|:------:|------|------|
| 高 | **メタスキル (Meta-Skills)** | AI エージェントに「学び方を学ぶ能力」を付与。Feeling / Seeing / Dreaming / Making / Learning の 5 要素 |
| 高 | **AI 共創リパーパスエンジン** | 1 つのコンテンツ（音声・ブログ・動画）を複数メディア形式に自動変換 |
| 高 | **RSS / ToS 自動更新パイプライン** | AI サービスの利用規約変更・モデル更新・料金変更を公式 RSS から自動検知 |
| 中 | **レッドチーム セキュリティ Plugin** | AI 組織内のホワイトハッカー班による定期的な自己脆弱性テスト |
| 中 | **A2A (AI-to-AI) 双方向通信** | サブエージェント → エージェントチーム方式への進化。メンバー間双方向通信 |
| 中 | **分身 AI の共進化ループ** | ユーザーとの対話から判断基準を学習し、ユーザーと共に成長する AI |

## v0.4 — エコシステムとスケーラビリティ

| 優先度 | 機能 | 説明 |
|:------:|------|------|
| 高 | **Skill マーケットプレイス** | コミュニティ Skill / Plugin の公開・検索・レビュー・インストールのプラットフォーム |
| 高 | **マルチユーザー / チーム対応** | チームでの運用を想定した認証・権限管理の強化 |
| 中 | **Web ブラウザ操作 Plugin** | Playwright / Puppeteer ベースの Web 自動操作（承認フロー付き） |
| 中 | **ファイルアップロード API** | タスク実行中のファイル受け渡しエンドポイント |
| 中 | **Obsidian 連携** | Markdown ベースのナレッジ管理ツールとのシームレスな連携 |
| 低 | **LSP (Language Server Protocol) 統合** | コーディングアシスタントとしての高度なコンテキスト理解 |

## v1.0 — プロダクション品質

| 優先度 | 機能 | 説明 |
|:------:|------|------|
| 高 | **ガバナンスとコンプライアンス** | 企業向けの監査・権限管理・データポリシーの完全実装 |
| 高 | **24/365 ロングラン実行** | ユーザー非アクティブ時も継続稼働する AI 組織 |
| 中 | **スマートデバイス連携** | IoT / スマートグラス / AI ロボットの開発環境としての拡張 |
| 中 | **VR / AR 統合** | 遠隔操作・文化保存などの次世代インターフェース |
| 低 | **クラウドサービスネイティブ連携** | Google Cloud / AWS / Azure との直接接続 |

---

## English

### Current State (v0.1)

v0.1 includes full implementation of the 9-layer architecture, ZEO-Bench quantitative evaluation of the Judge Layer, generic domain Skill templates, Self-Healing DAG chaos testing, runtime configuration management, knowledge store, and other foundational features.

### v0.2 — Connectivity & Practicality

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Tool Connector Full Implementation** | Move REST API / MCP / GraphQL / CLI tool execution from stub to real implementation |
| High | **Mid-task User Input Requests** | Mechanism to request additional info or files from users during execution |
| High | **User Resource Import** | Specify business manuals/rules/document folders for AI learning |
| High | **iPaaS Integration (n8n / Zapier / Make)** | Seamless connection with existing workflow automation tools |
| Medium | **Artifact Export** | Export to PDF / Google Docs / Notion / n8n |
| Medium | **E2E Testing** | End-to-end testing with Playwright |
| Medium | **LLM Response Mocking** | Mock framework to avoid real API calls during testing |

### v0.3 — Advanced AI Organization

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Meta-Skills** | Give AI agents "the ability to learn how to learn" — Feeling / Seeing / Dreaming / Making / Learning |
| High | **AI Co-creation Repurpose Engine** | Auto-convert one piece of content (audio/blog/video) into multiple media formats |
| High | **RSS / ToS Auto-update Pipeline** | Auto-detect AI service ToS changes, model updates, pricing changes from official RSS |
| Medium | **Red-team Security Plugin** | Periodic self-vulnerability testing by an internal white-hacker AI team |
| Medium | **A2A (AI-to-AI) Bidirectional Communication** | Evolution from sub-agents to agent teams with peer-to-peer communication |
| Medium | **Avatar AI Co-evolution Loop** | AI that learns decision criteria from user interactions and grows together |

### v0.4 — Ecosystem & Scalability

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Skill Marketplace** | Platform for publishing, searching, reviewing, and installing community Skills/Plugins |
| High | **Multi-user / Team Support** | Enhanced auth and permission management for team operations |
| Medium | **Web Browser Automation Plugin** | Playwright/Puppeteer-based web automation (with approval flows) |
| Medium | **File Upload API** | File exchange endpoints during task execution |
| Medium | **Obsidian Integration** | Seamless integration with Markdown-based knowledge management tools |
| Low | **LSP Integration** | Advanced context understanding as a coding assistant |

### v1.0 — Production Quality

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Governance & Compliance** | Full enterprise audit, permission management, data policy implementation |
| High | **24/365 Long-running Execution** | AI organization that continues operating when user is inactive |
| Medium | **Smart Device Integration** | Extension as a dev environment for IoT / smart glasses / AI robots |
| Medium | **VR / AR Integration** | Next-gen interfaces for remote operation and cultural preservation |
| Low | **Cloud Service Native Integration** | Direct connection with Google Cloud / AWS / Azure |

---

## 中文

### 当前状态 (v0.1)

v0.1 包含 9 层架构的完整实现、ZEO-Bench 对 Judge Layer 的定量评估、通用领域 Skill 模板、Self-Healing DAG 混沌测试、运行时配置管理、知识库等基础功能。

### v0.2 — 连接性与实用性强化

| 优先级 | 功能 | 说明 |
|:------:|------|------|
| 高 | **Tool Connector 完整实现** | 将 REST API / MCP / GraphQL / CLI 工具执行从 stub 迁移到真正实现 |
| 高 | **任务执行中的用户输入请求** | 在执行过程中向用户请求额外信息或文件的机制 |
| 高 | **用户资源导入** | 指定业务手册/规则/文档文件夹供 AI 学习 |
| 高 | **iPaaS 集成 (n8n / Zapier / Make)** | 与现有工作流自动化工具的无缝连接 |
| 中 | **成果物导出** | 导出到 PDF / Google Docs / Notion / n8n |
| 中 | **E2E 测试** | 使用 Playwright 的前后端一体化测试 |
| 中 | **LLM 响应模拟** | 测试时避免调用实际 API 的模拟框架 |

### v0.3 — AI 组织高度化

| 优先级 | 功能 | 说明 |
|:------:|------|------|
| 高 | **元技能 (Meta-Skills)** | 赋予 AI 代理"学习如何学习"的能力——感知/洞察/想象/实现/学习 |
| 高 | **AI 共创内容再利用引擎** | 将一个内容（音频/博客/视频）自动转换为多种媒体格式 |
| 高 | **RSS / 服务条款自动更新管道** | 从官方 RSS 自动检测 AI 服务条款变更、模型更新、定价变更 |
| 中 | **红队安全插件** | AI 组织内部白帽黑客团队定期进行自我漏洞测试 |
| 中 | **A2A (AI-to-AI) 双向通信** | 从子代理到代理团队的演进，支持成员间双向通信 |
| 中 | **分身 AI 共进化循环** | 从用户交互中学习判断标准，与用户共同成长的 AI |

### v0.4 — 生态系统与可扩展性

| 优先级 | 功能 | 说明 |
|:------:|------|------|
| 高 | **Skill 市场** | 社区 Skill/Plugin 的发布、搜索、评价、安装平台 |
| 高 | **多用户/团队支持** | 面向团队运营的增强认证和权限管理 |
| 中 | **Web 浏览器自动化插件** | 基于 Playwright/Puppeteer 的网页自动操作（带审批流程） |
| 中 | **文件上传 API** | 任务执行中的文件交换端点 |
| 中 | **Obsidian 集成** | 与基于 Markdown 的知识管理工具的无缝集成 |
| 低 | **LSP 集成** | 作为编码助手的高级上下文理解 |

### v1.0 — 生产质量

| 优先级 | 功能 | 说明 |
|:------:|------|------|
| 高 | **治理与合规** | 企业级审计、权限管理、数据策略的完整实现 |
| 高 | **24/365 长期运行执行** | 用户不活跃时仍继续运行的 AI 组织 |
| 中 | **智能设备集成** | 作为 IoT / 智能眼镜 / AI 机器人的开发环境扩展 |
| 中 | **VR / AR 集成** | 远程操作和文化保存等下一代界面 |
| 低 | **云服务原生集成** | 与 Google Cloud / AWS / Azure 的直接连接 |
