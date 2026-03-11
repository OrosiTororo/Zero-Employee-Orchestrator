# Contributing to Zero-Employee Orchestrator

> 日本語 | [English](#english) | [中文](#中文)

Zero-Employee Orchestrator へのコントリビューションを歓迎します。
バグ報告、機能リクエスト、コードの改善など、どのような形でも貢献をお待ちしています。

## はじめに

1. リポジトリを Fork する
2. ブランチを作成する: `git checkout -b feature/your-feature`
3. 変更をコミットする: `git commit -m "Add your feature"`
4. プッシュする: `git push origin feature/your-feature`
5. Pull Request を作成する

## 開発環境のセットアップ

```bash
git clone https://github.com/<your-username>/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh
```

### バックエンド

```bash
cd apps/api
source .venv/bin/activate
pip install -e ".[dev]"
```

### フロントエンド

```bash
cd apps/desktop/ui
pnpm install
pnpm dev
```

## コーディング規約

### Python

- **フォーマッター / リンター**: ruff
- 型ヒント必須
- FastAPI エンドポイントは `async def`
- テスト: pytest + pytest-asyncio

### TypeScript

- strict モード
- 関数コンポーネントのみ
- Tailwind CSS でスタイリング

## Pull Request のガイドライン

- PR は小さく保つ（1 つの PR で 1 つの変更）
- 既存のテストが通ることを確認する
- 新機能にはテストを追加する
- コミットメッセージは英語で、変更内容を簡潔に記述する
- `CLAUDE.md` のコーディング規約に従う

## バグ報告

[Issues](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/issues) から報告してください。

以下の情報を含めてください:
- OS とバージョン
- 再現手順
- 期待する動作と実際の動作
- エラーログ（ある場合）

## Skill / Plugin の貢献

コミュニティ Skill や Plugin の作成・共有も大歓迎です。

- Skill: `skills/templates/` のテンプレートを参考にしてください
- Plugin: `plugins/` の既存 Plugin を参考にしてください
- 安全性チェック（16 種類の危険パターン検出）を通過する必要があります
- 個人情報・機密情報を含めないでください

## ライセンス

コントリビューションは [MIT License](LICENSE) の下で公開されます。

---

## English

We welcome contributions to Zero-Employee Orchestrator. Whether it's bug reports, feature requests, or code improvements, all contributions are appreciated.

### Getting Started

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Create a Pull Request

### Development Setup

```bash
git clone https://github.com/<your-username>/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh
```

**Backend:**
```bash
cd apps/api
source .venv/bin/activate
pip install -e ".[dev]"
```

**Frontend:**
```bash
cd apps/desktop/ui
pnpm install
pnpm dev
```

### Coding Standards

**Python:** ruff for formatting/linting, type hints required, async def for FastAPI endpoints, pytest for testing.

**TypeScript:** strict mode, functional components only, Tailwind CSS for styling.

### Pull Request Guidelines

- Keep PRs small and focused (one change per PR)
- Ensure existing tests pass
- Add tests for new features
- Write clear commit messages in English
- Follow the coding conventions in `CLAUDE.md`

### Bug Reports

Please report via [Issues](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/issues) with:
- OS and version
- Steps to reproduce
- Expected vs. actual behavior
- Error logs (if any)

### Skill / Plugin Contributions

Community Skills and Plugins are welcome:
- Skills: refer to templates in `skills/templates/`
- Plugins: refer to existing plugins in `plugins/`
- Must pass safety checks (16 dangerous pattern detections)
- Do not include personal or sensitive information

### License

Contributions are released under the [MIT License](LICENSE).

---

## 中文

我们欢迎对 Zero-Employee Orchestrator 的贡献。无论是错误报告、功能请求还是代码改进，我们都非常感谢您的参与。

### 入门

1. Fork 本仓库
2. 创建分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m "Add your feature"`
4. 推送：`git push origin feature/your-feature`
5. 创建 Pull Request

### 开发环境搭建

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

### 编码规范

**Python：** 使用 ruff 格式化/检查，必须使用类型提示，FastAPI 端点使用 async def，使用 pytest 测试。

**TypeScript：** strict 模式，仅使用函数组件，使用 Tailwind CSS 进行样式设计。

### Pull Request 指南

- 保持 PR 小而专注（每个 PR 一个更改）
- 确保现有测试通过
- 为新功能添加测试
- 使用英文撰写清晰的提交信息
- 遵循 `CLAUDE.md` 中的编码规范

### 错误报告

请通过 [Issues](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/issues) 报告，包含：
- 操作系统和版本
- 重现步骤
- 预期行为与实际行为
- 错误日志（如有）

### Skill / Plugin 贡献

欢迎社区 Skill 和 Plugin：
- Skill：参考 `skills/templates/` 中的模板
- Plugin：参考 `plugins/` 中的现有插件
- 必须通过安全性检查（16 种危险模式检测）
- 请勿包含个人或敏感信息

### 许可证

贡献内容在 [MIT 许可证](LICENSE) 下发布。
