# Plugin Development Guide

How to create, develop, and publish plugins for Zero-Employee Orchestrator.

## Plugin Types

- **General plugin** — standalone functionality (e.g., `browser-use`, `slack-bot`)
- **Role-based pack** — bundle of skills for a specific business role (e.g., `sales-pack`)

## Directory Structure

```
plugins/
  my-plugin/
    manifest.json      # Required: metadata, skills, permissions
    handler.py         # Optional: runtime logic (async functions)
```

## Manifest Format

Create `plugins/my-plugin/manifest.json`:

```json
{
  "slug": "my-plugin",
  "name": "My Plugin",
  "version": "0.1.0",
  "description": "Short description of what the plugin does",
  "type": "plugin",
  "status": "experimental",
  "skills": ["skill_one", "skill_two"],
  "connectors": [],
  "required_permissions": ["internet_access"],
  "external_connections": [],
  "dangerous_operations": false,
  "approval_required_operations": [],
  "use_cases": [
    "Example use case one",
    "Example use case two"
  ],
  "author": "Your Name"
}
```

### Key Fields

| Field | Required | Description |
|-------|----------|-------------|
| `slug` | Yes | Unique identifier, lowercase with hyphens |
| `name` | Yes | Human-readable name |
| `skills` | Yes | List of skill function names |
| `required_permissions` | Yes | Permissions the plugin needs |
| `dangerous_operations` | Yes | Whether any operation needs approval gate |
| `approval_required_operations` | No | Operations requiring human approval |

## Adding Runtime Logic

Create `plugins/my-plugin/handler.py` alongside the manifest:

```python
"""Runtime handlers for my-plugin."""


async def skill_one(instruction: str) -> dict:
    """Execute skill_one with the given instruction."""
    return {
        "action": "skill_one",
        "instruction": instruction,
        "status": "ready",
    }


async def skill_two(instruction: str) -> dict:
    """Execute skill_two with the given instruction."""
    return {
        "action": "skill_two",
        "instruction": instruction,
        "status": "ready",
    }
```

Each function should:
- Be `async def`
- Accept `instruction: str` as its first argument
- Return a `dict` with at minimum `action`, `instruction`, and `status` keys
- Handle errors gracefully and return `"status": "error"` on failure

## Registering with ToolRegistry

Plugins are auto-discovered by the registry scanner at startup. The registry
reads `manifest.json` from each directory under `plugins/`. To register
manually via the API:

```bash
# List all registered plugins
curl -s localhost:18234/api/v1/registry/plugins

# Register a plugin from a local path
curl -s -X POST localhost:18234/api/v1/registry/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"source": "local", "path": "plugins/my-plugin"}'
```

The registry validates the manifest, runs `analyze_code_safety()` on the
handler module, and blocks HIGH-risk plugins unless `?force=true` is passed.

## Minimal Plugin Template

```bash
mkdir plugins/my-plugin
```

**manifest.json**:
```json
{
  "slug": "my-plugin",
  "name": "My Plugin",
  "version": "0.1.0",
  "description": "A minimal plugin template",
  "type": "plugin",
  "status": "experimental",
  "skills": ["hello"],
  "connectors": [],
  "required_permissions": [],
  "external_connections": [],
  "dangerous_operations": false,
  "approval_required_operations": [],
  "use_cases": ["Greet the user"],
  "author": "You"
}
```

**handler.py**:
```python
"""Minimal plugin handler."""


async def hello(instruction: str) -> dict:
    return {"action": "hello", "instruction": instruction, "status": "ready"}
```

## Publishing to Marketplace

1. Ensure `manifest.json` passes validation (`status` can be `experimental` or `stable`).
2. Add at least one use case in `use_cases`.
3. Test locally: install via registry, invoke each skill.
4. Submit via the marketplace API:

```bash
curl -s -X POST localhost:18234/api/v1/marketplace/plugins/publish \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug": "my-plugin", "version": "0.1.0"}'
```

The marketplace runs a security scan before listing the plugin.

## Role-Based Packs

Role packs follow the same structure but include a `"role"` field in the
manifest. See `plugins/sales-pack/` for an example. Each skill in a role
pack should map to a function in `handler.py`.
