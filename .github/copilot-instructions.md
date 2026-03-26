# Copilot Instructions

## Required Checks (Before All Responses and Work)

### 1. Check the Latest Repository State
- **Always read** relevant files (`pyproject.toml`, workflows, config files, etc.) before responding or working
- Do not rely on cached knowledge; always refer to the current repository state
- When investigating errors, check logs, workflow files, and dependency files (`pyproject.toml`, `requirements*.txt`, lock files, etc.) before identifying the cause

### 2. Always Verify External Information
- For version numbers, package existence, GitHub Actions versions, and other information dependent on external services, **always verify via web search** before responding
- Only state "does not exist" or "latest is..." after confirming through search
- Do not rely on knowledge cutoff for answers

### 3. Standard Pre-Work Checks

Reference documents (priority order):
- `README.md` -- Feature list, configuration, security settings
- `CLAUDE.md` -- Architecture, directory structure
- `docs/dev/DESIGN.md` -- Implementation design document
- `ROADMAP.md` -- Roadmap

## pyproject.toml Management (Important)

Two `pyproject.toml` files exist (root and `apps/api/`). When changing versions or dependencies, **always sync both**.
- Root: `pyproject.toml`
- API: `apps/api/pyproject.toml`

Sync check script: `./scripts/bump-version.sh`

## Security Notes

- `litellm 1.82.7` / `1.82.8` were removed from PyPI due to a supply chain attack (malware). Do not specify these versions
- Dependency specification example: `litellm>=1.60,!=1.82.7,!=1.82.8`
