> [日本語](../ja-JP/../CONTRIBUTING.md) | [English](../CONTRIBUTING.md) | 中文

# 为 Zero-Employee Orchestrator 做贡献

我们欢迎对 Zero-Employee Orchestrator 的贡献。无论是错误报告、功能请求还是代码改进，我们都非常感谢您的参与。

## 入门

1. Fork 本仓库
2. 创建分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m "Add your feature"`
4. 推送：`git push origin feature/your-feature`
5. 创建 Pull Request

## 开发环境搭建

```bash
git clone https://github.com/<your-username>/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh
```

**后端：**
```bash
cd apps/api
source .venv/bin/activate
pip install -e ".[dev]"
```

**前端：**
```bash
cd apps/desktop/ui
pnpm install
pnpm dev
```

## 编码规范

**Python：** 使用 ruff 格式化/检查，必须使用类型提示，FastAPI 端点使用 async def，使用 pytest 测试。

**TypeScript：** strict 模式，仅使用函数组件，使用 Tailwind CSS 进行样式设计。

## Pull Request 指南

- 保持 PR 小而专注（每个 PR 一个更改）
- 确保现有测试通过
- 为新功能添加测试
- 使用英文撰写清晰的提交信息
- 遵循 `CLAUDE.md` 中的编码规范

## 错误报告

请通过 [Issues](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/issues) 报告，包含：
- 操作系统和版本
- 重现步骤
- 预期行为与实际行为
- 错误日志（如有）

## Skill / Plugin 贡献

欢迎社区 Skill 和 Plugin：
- Skill：参考 `skills/templates/` 中的模板
- Plugin：参考 `plugins/` 中的现有插件
- 必须通过安全性检查（16 种危险模式检测）
- 请勿包含个人或敏感信息

## 许可证

贡献内容在 [MIT 许可证](LICENSE) 下发布。
