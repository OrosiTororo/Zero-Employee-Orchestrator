# SKILL.md Authoring Guide

> How to create a "standard operating procedure" that teaches Claude Code specific workflows.
> Written in natural language and composed alongside executable scripts.

## Overview

A `SKILL.md` is a Claude Code skill file consisting of two parts:

1. **Front matter (configuration section)** — Always included in Claude's context
2. **Body (instruction section)** — Loaded only when the skill is invoked

Placement: Under the `.claude/skills/` directory

## 1. Front Matter (Configuration Section)

Written as YAML front matter at the top of the file. This is the configuration that allows Claude to recognize and select the skill.

```yaml
---
name: download-sharepoint
description: Download files from SharePoint and save them locally
disable-model-invocation: true
---
```

| Field | Description |
|-------|-------------|
| `name` | Slash command name, e.g. `/download-sharepoint` |
| `description` | Reference text used by Claude to automatically select the skill based on conversation context |
| `disable-model-invocation` | `true`: The skill is invoked only by an explicit user command. Recommended for operations with side effects |

## 2. Body (Instruction Section)

The concrete instructions loaded when the skill is invoked. Can include interaction design (UX design).

### Elements

**Specific commands and options:**
```markdown
Run the following command:
`pwsh -ExecutionPolicy Bypass -File ./scripts/download-sp.ps1 --site-id $SITE_ID`
```

**STEP-based interaction flow:**
```markdown
## Procedure

STEP 1: Ask the user for the site ID
STEP 2: Confirm which fields to retrieve (Japanese names only / basic info / all fields)
STEP 3: Build and execute the command based on the user's selection
```

**Conditional branching:**
```markdown
Switch arguments based on the user's selection:
- "Japanese names only" → `--id` only
- "Basic info" → `--id --fields basic`
- "All fields" → `--id --fields all`
```

**Result handling:**
```markdown
Check the JSON output of the script:
- `status: "ok"` → Display the results to the user
- `status: "not_found"` → Prompt the user to verify the ID
- `status: "error"` → Relay the contents of the `hint` field to the user
```

**Initial setup (fallback):**
```markdown
## Setup
If Playwright is not installed:
`npm install -g playwright && npx playwright install chromium`
```

## 3. Integration with Scripts

SKILL.md focuses on orchestration (directing), delegating complex logic to scripts.

### Interface Design

Structured JSON is recommended for script output:

```json
{
  "status": "ok",
  "data": { ... },
  "hint": null
}
```

```json
{
  "status": "error",
  "data": null,
  "hint": "Please run pip install playwright"
}
```

- The `status` field allows Claude to accurately branch and interpret results
- The `hint` field suggests remediation steps when errors occur

## 4. Directory Layout

### Pattern A: Self-contained within the skill (portable)

```
.claude/skills/
└── download-sharepoint/
    ├── SKILL.md
    └── scripts/
        └── download-sp.ps1
```

### Pattern B: Placed at the project root (for pipelines and sharing)

```
.claude/skills/
└── download-sharepoint.md
scripts/
└── download-sp.ps1
```

This pattern is suitable when scripts have interdependencies or pipeline-style processing flows.

## 5. Sample: Complete SKILL.md

```markdown
---
name: fetch-user-data
description: Retrieve and format user data from an internal system
disable-model-invocation: true
---

# User Data Retrieval Skill

## Procedure

STEP 1: Ask the user for the target employee ID
STEP 2: Confirm the retrieval scope
  - "Basic info only"
  - "Include department and title"
  - "All fields"
STEP 3: Run the following command

`python scripts/fetch_user.py --employee-id $ID --scope $SCOPE`

## Interpreting Results

Check the `status` field in the JSON output:
- `ok` → Display the data to the user
- `not_found` → Prompt the user to verify the employee ID
- `auth_error` → Guide the user to reconfigure the authentication token

## Setup

If an error occurs on the first run:
`pip install requests && python scripts/setup_auth.py`
```

## 6. Relationship with Zero-Employee Orchestrator

The built-in Skills in this project (`skills/builtin/`) are implemented as Python modules,
which is a separate mechanism from Claude Code skill files (`.claude/skills/`).

| Type | Location | Format | Purpose |
|------|----------|--------|---------|
| Claude Code skill | `.claude/skills/*.md` | SKILL.md (natural language) | Automating developer workflows |
| ZEO built-in Skill | `skills/builtin/*.py` | Python module | Specialized capabilities for AI agents |

By leveraging both, you can simultaneously streamline developer workflows and extend AI agent capabilities.
