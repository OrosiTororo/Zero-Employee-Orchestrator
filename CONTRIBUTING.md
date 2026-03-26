# Contributing to Zero-Employee Orchestrator

We welcome contributions to Zero-Employee Orchestrator. Whether it's bug reports, feature requests, or code improvements, all contributions are appreciated.

## Getting Started

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Create a Pull Request

## Development Setup

```bash
git clone https://github.com/<your-username>/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"
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

## Coding Standards

**Python:** ruff for formatting/linting, type hints required, async def for FastAPI endpoints, pytest for testing.

**TypeScript:** strict mode, functional components only, Tailwind CSS for styling.

## Pull Request Guidelines

- Keep PRs small and focused (one change per PR)
- Ensure existing tests pass
- Add tests for new features
- Write clear commit messages in English
- Follow the coding conventions in `CLAUDE.md`

## Bug Reports

Please report via [Issues](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/issues) with:
- OS and version
- Steps to reproduce
- Expected vs. actual behavior
- Error logs (if any)

## Skill / Plugin Contributions

Community Skills and Plugins are welcome:
- Skills: refer to templates in `skills/templates/`
- Plugins: refer to existing plugins in `plugins/`
- Must pass safety checks (16 dangerous pattern detections)
- Do not include personal or sensitive information

## Translations

We welcome translations! Current languages:
- Japanese (`docs/ja-JP/`)
- Simplified Chinese (`docs/zh-CN/`)
- Traditional Chinese (`docs/zh-TW/`)
- Korean (`docs/ko-KR/`)
- Portuguese (`docs/pt-BR/`)
- Turkish (`docs/tr/`)

To add a new language:
1. Create `docs/<lang-code>/README.md`
2. Translate from the English README
3. Update language links in all existing READMEs
4. Submit a PR

## License

Contributions are released under the [MIT License](LICENSE).
