# Changelog

> [English](../CHANGELOG.md) | [日本語](../ja-JP/CHANGELOG.md) | [中文（繁體）](../zh-TW/CHANGELOG.md) | [한국어](../ko-KR/CHANGELOG.md) | [Português](../pt-BR/CHANGELOG.md) | [Türkçe](../tr/CHANGELOG.md) | 简体中文

本项目的所有重要变更将记录在此文件中。

格式：[Keep a Changelog](https://keepachangelog.com/)
版本：[Semantic Versioning](https://semver.org/)

## [0.1.1] - 2026-03-28

### 新增

- **生产环境 Docker Compose** — 资源限制（内存/CPU）、网络隔离、日志轮转、只读文件系统、`no-new-privileges` 安全选项、健康检查 `start_period`
- **CI 添加 Trivy 容器镜像扫描** — 合并前扫描 Docker 镜像的 CRITICAL/HIGH 漏洞
- **CI 添加 Red-team 安全测试** — 运行完整 Red-team 测试套件，发现严重问题时使构建失败
- **65+ i18n 翻译键** — 全 6 种语言从约 30 个扩展到 65+ 个键，涵盖安全消息、设置、导航、常用操作、技能/插件管理、服务器健康、预算/成本、Judge Layer 和浏览器助手
- **补充缺失的 PII 检测模式** — 添加驾驶证（日本/美国）和日语姓名模式，完善全部 13 个 PII 类别
- **6语言 i18n 支持** — 在现有日语、英语、中文基础上，新增韩语（한국어）、葡萄牙语（Português）、土耳其语（Türkçe）的 UI 翻译
- **可扩展 LLM API 密钥设置** — 可在内置四个供应商之外自由添加自定义供应商
- **Design Interview 过去失败模式反馈** — 自动从 Experience Memory 和 Failure Taxonomy 搜索类似失败模式，动态注入警告和追加问题

### 变更

- **默认语言改为英语** — 从 `ja` 改为 `en` 以促进国际化采用（用户可设置 `LANGUAGE=ja` 或 `--lang ja`）
- **模型目录更新至最新** — GPT-5.4 / GPT-5.4 Mini（从 4.1）、Llama 4（从 3.2）、Phi-4（从 3）、Claude Haiku 非日期别名
- **文档准确性修正** — 修正夸大描述：提示防护模式 40+→28+、应用连接器 35+→34+、路由模块 41→40。全语言修正 "GPT-5 Mini"→"GPT-5.4 Mini"
- **Cowork 风格导航栏** — 移除双侧边栏，改用带提示的图标导航栏

### 安全

- **CI 中 pip-audit 改为阻塞模式** — 移除 `continue-on-error`，依赖漏洞将导致构建失败
- **Red-team 测试强化** — 测试处理器使用真实载荷执行安全模块，而非仅配置验证
- **Sandbox 符号链接攻击防护增强** — 检测并阻止解析路径指向与原始路径不同的目录

## [0.1.0] - 2026-03-12 — Platform v0.1（整合版本）

初始实现。详细内容请参阅 [英文 CHANGELOG](../CHANGELOG.md)。

[0.1.1]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.1
[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
