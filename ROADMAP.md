# Roadmap

> 日本語 | [English](#english) | [中文](#中文)

> 最終更新: 2026-03-18
> 現在のバージョン: v0.1

---

## 現在の状態 (v0.1)

v0.1 では、9層アーキテクチャの完全実装に加え、当初 v0.2〜v1.0 で計画していた主要機能をすべて前倒しで実装しました。

### v0.1 実装済み機能一覧

#### 基盤 (旧 v0.1)
- 9層アーキテクチャの完全実装
- ZEO-Bench による Judge Layer の定量評価
- 汎用ドメイン Skill テンプレート
- Self-Healing DAG のカオステスト
- ランタイム設定管理・ナレッジストア
- ai-self-improvement Plugin（6 Skill 全実装）

#### 接続性と実用性 (旧 v0.2)
- **Tool Connector 本実装** — REST API / MCP / GraphQL / CLI / Webhook 対応
- **タスク実行中のユーザー入力要求** — テキスト / ファイル / 選択 / 確認
- **ユーザーリソースインポート** — ファイル / フォルダ / URL からの取り込み
- **iPaaS 連携** — n8n / Zapier / Make との Webhook 連携
- **成果物エクスポート** — PDF / Markdown / HTML / JSON / CSV / DOCX
- **E2E テストフレームワーク** — pytest + httpx ベース
- **LLM レスポンスモック** — テスト用モック基盤
- **ファイルアップロード API** — 単一・複数ファイル対応

#### AI 組織の高度化 (旧 v0.3)
- **メタスキル (Meta-Skills)** — Feeling / Seeing / Dreaming / Making / Learning の 5 要素
- **AI 共創リパーパスエンジン** — 10 種のコンテンツ形式への自動変換
- **RSS / ToS 自動更新パイプライン** — 6 社の AI プロバイダー監視
- **レッドチーム セキュリティ Plugin** — 8 カテゴリ・20+ セキュリティテスト
- **A2A (AI-to-AI) 双方向通信** — エージェント間メッセージ・チャンネル・交渉
- **分身 AI 共進化ループ** — ユーザー嗜好学習・意思決定予測

#### エコシステムとスケーラビリティ (旧 v0.4)
- **Skill マーケットプレイス** — 公開・検索・レビュー・インストール
- **マルチユーザー / チーム対応** — ロール・招待・権限管理
- **Web ブラウザ操作** — Playwright ベースの自動操作（承認フロー付き）
- **Obsidian 連携** — Vault 管理・ノート検索・リンクグラフ・ナレッジ同期
- **LSP (Language Server Protocol) 統合** — 6 言語対応の基盤

#### プロダクション品質 (旧 v1.0)
- **ガバナンスとコンプライアンス** — GDPR / HIPAA / SOC2 / ISO27001 / CCPA / APPI
- **24/365 ロングラン実行** — スケジューラ・ジョブ管理基盤
- **クラウドサービスネイティブ連携** — AWS / GCP / Azure / Cloudflare 抽象化層
- **スマートデバイス / VR / AR 統合** — デバイスハブ・プロトコル抽象化

#### ワークスペース隔離とプライバシー保護
- **隔離ワークスペース** — 初期状態でローカル・クラウドに接続しない独立環境
- **内部ストレージ** — AI エージェントがアクセスできるのはユーザーがアップロードしたファイルのみ
- **段階的アクセス許可** — ユーザーが設定でローカルフォルダ・クラウドストレージへのアクセスを許可可能
- **業務単位の環境カスタマイズ** — チケット・タスクごとに異なる環境・権限・ナレッジ範囲を指定可能
- **チャット指示と設定の整合性チェック** — チャットでの指示がシステム設定と異なる場合、AI が計画段階でユーザーに許可を求める
- **保存先の柔軟な選択** — 成果物の保存先を内部ストレージ・ローカル・クラウドから選択可能

---

## 今後のロードマップ

以下は、コミュニティの成長やリソースの確保が必要な項目です。

### v0.2 — フロントエンド完成とコミュニティ形成

| 優先度 | 機能 | 説明 |
|:------:|------|------|
| 高 | **フロントエンド データ接続完成** | 12画面のバックエンド接続を完成 |
| 高 | **features/ モジュール分離** | pages 内ロジックの features/ への分離 |
| 高 | **packages/ 共有ライブラリ** | 共有コードの抽出・パッケージ化 |
| 高 | **Plugin ローダー本実装** | マニフェストベースの動的ロード・実行機構 |
| 中 | **Design Interview → 成果物 E2E フロー** | 自然言語入力から成果物生成まで一気通貫 |
| 中 | **Playwright フロントエンド E2E テスト** | ブラウザ UI の自動テスト |
| 中 | **Worker コアロジック強化** | TaskRunner / HeartbeatRunner の補強 |

### v0.3 — AI Self-Improvement の加速

| 優先度 | 機能 | 説明 |
|:------:|------|------|
| 高 | **コミュニティ Skill エコシステム** | 大量の Skill・Plugin 共有による進化 |
| 高 | **匿名フィードバック集約** | プライバシー保護つき Experience Memory 共有 |
| 中 | **Cross-Model 大規模検証** | 大量検証データの蓄積と精度向上 |
| 中 | **多言語 Experience Memory** | 日本語・英語・中国語等の多言語知識蓄積 |
| 中 | **コントリビューター向けガイド** | CONTRIBUTING.md・Skill 開発チュートリアル |

### v1.0 — 真の AI Self-Improvement

| 優先度 | 機能 | 説明 |
|:------:|------|------|
| 高 | **Self-Improvement Loop** | 改善提案 → テスト → 検証 → 適用の自動サイクル |
| 高 | **Cross-Orchestrator Learning** | 複数 ZEO インスタンス間の知識共有 |
| 中 | **ファインチューニング基盤** | 特定業務に特化した専門モデルの自動作成 |
| 中 | **AI アーキテクチャ自己改善** | AI がシステム設計レベルの改善を提案 |
| 低 | **メタ学習** | 「どう改善すれば効率的か」自体を学習 |

---

## English

### Current State (v0.1)

v0.1 includes all features originally planned for v0.2 through v1.0, implemented ahead of schedule.

#### Implemented in v0.1

**Foundation:**
- Full 9-layer architecture, ZEO-Bench, Self-Healing DAG, Experience Memory, AI Self-Improvement Plugin

**Connectivity (formerly v0.2):**
- Tool Connector (REST/MCP/GraphQL/CLI/Webhook), iPaaS (n8n/Zapier/Make), Artifact Export, User Input Requests, Resource Import, File Upload API, E2E Test Framework, LLM Response Mocking

**Advanced AI Organization (formerly v0.3):**
- Meta-Skills (Feeling/Seeing/Dreaming/Making/Learning), AI Repurpose Engine, RSS/ToS Monitor, Red-team Security, A2A Communication, Avatar Co-evolution

**Ecosystem (formerly v0.4):**
- Skill Marketplace, Multi-user/Team, Browser Automation, Obsidian Integration, LSP Integration

**Production Quality (formerly v1.0):**
- Governance & Compliance (GDPR/HIPAA/SOC2/ISO27001/CCPA/APPI), 24/365 Scheduler, Cloud Native Integration (AWS/GCP/Azure), Smart Device & VR/AR Hub

**Workspace Isolation & Privacy:**
- Isolated workspace (no local/cloud access by default), internal storage (AI only accesses user-uploaded files), gradual access permission (users can allow local folders/cloud storage via settings), per-task environment customization, chat instruction vs. settings consistency check (AI asks for approval when chat instructions differ from settings), flexible storage location selection

### Future Roadmap

#### v0.2 — Frontend Completion & Community

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Frontend Data Connection** | Complete 12 screens' backend connections |
| High | **features/ Module Separation** | Extract logic from pages to features/ |
| High | **packages/ Shared Libraries** | Extract and package shared code |
| High | **Plugin Loader Implementation** | Manifest-based dynamic loading |
| Medium | **E2E Flow Integration** | Natural language input to artifact generation |
| Medium | **Playwright Frontend E2E Tests** | Browser UI automated testing |
| Medium | **Worker Core Logic Enhancement** | Strengthen TaskRunner / HeartbeatRunner |

#### v0.3 — Accelerating AI Self-Improvement

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Community Skill Ecosystem** | Large-scale Skill/Plugin sharing |
| High | **Anonymous Feedback Aggregation** | Privacy-preserving Experience Memory sharing |
| Medium | **Cross-Model Large-scale Verification** | Massive verification data accumulation |
| Medium | **Multilingual Experience Memory** | Knowledge accumulation in Japanese, English, Chinese, etc. |
| Medium | **Contributor Guide** | CONTRIBUTING.md and Skill development tutorials |

#### v1.0 — True AI Self-Improvement

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Self-Improvement Loop** | Auto-cycle: propose → test → verify → apply |
| High | **Cross-Orchestrator Learning** | Knowledge sharing between ZEO instances |
| Medium | **Fine-tuning Infrastructure** | Auto-create specialized domain models |
| Medium | **AI Architecture Self-Improvement** | AI proposes system-design-level improvements |
| Low | **Meta-Learning** | Learning "how to improve efficiently" itself |

---

## 中文

### 当前状态 (v0.1)

v0.1 包含了原计划在 v0.2 到 v1.0 中实现的所有主要功能。

#### v0.1 已实现功能

**基础：** 9层架构、ZEO-Bench、Self-Healing DAG、经验记忆、AI 自我改进插件

**连接性（原 v0.2）：** Tool Connector、iPaaS（n8n/Zapier/Make）、成果物导出、用户输入请求、资源导入、文件上传、E2E 测试框架、LLM 响应模拟

**AI 组织高度化（原 v0.3）：** 元技能、AI 内容再利用引擎、RSS/ToS 监控、红队安全、A2A 通信、分身 AI 共进化

**生态系统（原 v0.4）：** Skill 市场、多用户/团队、浏览器自动化、Obsidian 集成、LSP 集成

**生产质量（原 v1.0）：** 治理与合规（GDPR/HIPAA/SOC2 等）、24/365 调度器、云服务集成、智能设备/VR/AR

**工作空间隔离与隐私保护：** 隔离工作空间（默认不连接本地/云端）、内部存储（AI 仅访问用户上传的文件）、分级访问许可、按任务自定义环境、聊天指令与设置一致性检查（指令与设置不同时 AI 会请求用户许可）、灵活的存储位置选择

### 未来路线图

#### v0.2 — 前端完成与社区形成

| 优先级 | 功能 | 说明 |
|:------:|------|------|
| 高 | **前端数据连接完成** | 完成 12 个画面的后端连接 |
| 高 | **features/ 模块分离** | 将 pages 内的逻辑分离到 features/ |
| 高 | **packages/ 共享库** | 共享代码的抽取与包化 |
| 高 | **Plugin 加载器** | 基于清单的动态加载机制 |
| 中 | **E2E 流程集成** | 从自然语言输入到成果物生成 |
| 中 | **Playwright 前端 E2E 测试** | 浏览器 UI 自动化测试 |
| 中 | **Worker 核心逻辑强化** | TaskRunner / HeartbeatRunner 的补强 |

#### v0.3 — 加速 AI 自我改进

| 优先级 | 功能 | 说明 |
|:------:|------|------|
| 高 | **社区 Skill 生态系统** | 大规模 Skill/Plugin 共享 |
| 高 | **匿名反馈聚合** | 隐私保护的 Experience Memory 共享 |
| 中 | **Cross-Model 大规模验证** | 大量验证数据的积累与精度提升 |
| 中 | **多语言 Experience Memory** | 日语、英语、中文等多语言知识积累 |
| 中 | **贡献者指南** | CONTRIBUTING.md 和 Skill 开发教程 |

#### v1.0 — 真正的 AI 自我改进

| 优先级 | 功能 | 说明 |
|:------:|------|------|
| 高 | **自我改进循环** | 自动循环：提案→测试→验证→应用 |
| 高 | **跨编排器学习** | ZEO 实例间的知识共享 |
| 中 | **微调基础设施** | 自动创建特定业务的专业模型 |
| 中 | **AI 架构自我改进** | AI 提出系统设计级别的改进方案 |
| 低 | **元学习** | 学习「如何高效改进」本身 |
