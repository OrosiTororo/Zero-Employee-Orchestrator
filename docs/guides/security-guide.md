[← Back to README](../../README.md)

# Security Guide

> Zero-Employee Orchestrator — Security-First Architecture

---

## Table of Contents

- [Security Philosophy](#security-philosophy)
- [Defense Layers Overview](#defense-layers-overview)
- [Prompt Injection Defense](#prompt-injection-defense)
- [Approval Gates](#approval-gates)
- [Autonomy Boundaries](#autonomy-boundaries)
- [IAM Design](#iam-design)
- [File Sandbox](#file-sandbox)
- [Data Protection](#data-protection)
- [PII Protection](#pii-protection)
- [Workspace Isolation](#workspace-isolation)
- [Secret Management](#secret-management)
- [Security Headers](#security-headers)
- [Rate Limiting](#rate-limiting)
- [Sanitization](#sanitization)
- [Audit Logging](#audit-logging)
- [Red-Team Security Testing](#red-team-security-testing)
- [Production Deployment Checklist](#production-deployment-checklist)

---

## Security Philosophy

ZEO is designed **security-first** — security is not an afterthought but a core architectural principle. Every layer of the system includes security considerations:

1. **Defense in depth** — Multiple overlapping security layers
2. **Least privilege** — AI agents have minimal necessary permissions
3. **Human-in-the-loop** — Dangerous operations always require human approval
4. **Auditability** — Every action is logged and traceable
5. **Fail-safe defaults** — Strict mode by default, users opt into relaxation

---

## Defense Layers Overview

```
┌─────────────────────────────────────────────────┐
│  Workspace Isolation    (workspace_isolation.py) │
│  ┌─────────────────────────────────────────────┐│
│  │  Prompt Injection    (prompt_guard.py)       ││
│  │  ┌─────────────────────────────────────────┐││
│  │  │  Approval Gates   (approval_gate.py)    │││
│  │  │  ┌─────────────────────────────────────┐│││
│  │  │  │  IAM            (iam.py)            ││││
│  │  │  │  ┌─────────────────────────────────┐││││
│  │  │  │  │  File Sandbox (sandbox.py)      │││││
│  │  │  │  │  ┌─────────────────────────────┐│││││
│  │  │  │  │  │  Data Protection            ││││││
│  │  │  │  │  │  (data_protection.py)       ││││││
│  │  │  │  │  └─────────────────────────────┘│││││
│  │  │  │  └─────────────────────────────────┘││││
│  │  │  └─────────────────────────────────────┘│││
│  │  └─────────────────────────────────────────┘││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

| Layer | Module | Description |
|-------|--------|-------------|
| Workspace Isolation | `workspace_isolation.py` | Isolates AI from local/cloud resources |
| Prompt Injection | `prompt_guard.py` | Detects and blocks injection attacks |
| Approval Gates | `approval_gate.py` | Requires human approval for dangerous ops |
| Autonomy Boundaries | `autonomy_boundary.py` | Limits AI autonomous actions |
| IAM | `iam.py` | Human/AI account separation |
| File Sandbox | `sandbox.py` | Whitelist-based folder access |
| Data Protection | `data_protection.py` | Upload/download policy control |
| PII Guard | `pii_guard.py` | Personal information detection/masking |
| Secret Management | `secret_manager.py` | Fernet encryption for secrets |
| Sanitization | `sanitizer.py` | Auto-removal of sensitive data |
| Security Headers | `security_headers.py` | CSP, HSTS, X-Frame-Options |
| Rate Limiting | `rate_limit.py` | API rate limiting via slowapi |

---

## Prompt Injection Defense

**Module:** `apps/api/app/security/prompt_guard.py`

### 5 Categories of Detection

| Category | Description | Example Patterns |
|----------|-------------|-----------------|
| **Instruction Override** | Attempts to override system instructions | "Ignore previous instructions", "You are now..." |
| **Role Manipulation** | Attempts to change AI's role | "Act as an admin", "Pretend you have no restrictions" |
| **Data Exfiltration** | Attempts to extract system data | "Show me the system prompt", "What are your instructions?" |
| **Privilege Escalation** | Attempts to gain elevated access | "Grant me admin access", "Disable security checks" |
| **Encoding Attacks** | Obfuscated injection via encoding | Base64 encoded instructions, Unicode tricks |

### 40+ Detection Patterns

The prompt guard scans all user input before it reaches the LLM. Detection includes:

- Keyword pattern matching
- Semantic similarity detection
- Encoding/obfuscation detection
- Multi-language injection patterns
- Nested injection detection

### External Data Boundary

**Critical Rule:** All external data passed to LLMs must use `wrap_external_data()`:

```python
from app.security.prompt_guard import wrap_external_data

# Always wrap external data before passing to LLM
safe_data = wrap_external_data(external_input)
prompt = f"Analyze this data: {safe_data}"
```

This adds boundary markers that prevent external content from being interpreted as instructions.

---

## Approval Gates

**Module:** `apps/api/app/policies/approval_gate.py`

### 12 Categories of Dangerous Operations

| # | Category | Description | Examples |
|---|----------|-------------|---------|
| 1 | **Send / Publish** | Outbound communication | Email, Slack, social media posts |
| 2 | **Delete / Destroy** | Destructive operations | File deletion, data purge |
| 3 | **Billing / Payment** | Financial operations | API purchases, subscription changes |
| 4 | **Permission Changes** | Access control modifications | Role grants, API key creation |
| 5 | **External API Calls** | Outbound API requests | Third-party service calls |
| 6 | **Data Export** | Data leaving the system | File downloads, report exports |
| 7 | **Configuration Changes** | System setting modifications | Security config, model settings |
| 8 | **User Management** | User account operations | Account creation, deletion |
| 9 | **Deployment** | Production deployment actions | Container restart, scaling |
| 10 | **Database Operations** | Direct DB modifications | Schema changes, data migration |
| 11 | **Security Settings** | Security configuration changes | Firewall rules, encryption settings |
| 12 | **Automation Rules** | Creating autonomous triggers | Cron jobs, event-based automation |

Each operation presents the user with:
- What will happen
- Cost and risk assessment
- Data flow description
- Reversibility status
- Required permissions

---

## Autonomy Boundaries

**Module:** `apps/api/app/policies/autonomy_boundary.py`

Explicitly defines what AI can and cannot do autonomously:

| Allowed Autonomously | Requires Approval |
|---------------------|-------------------|
| Read internal data | Write external data |
| Generate drafts | Send/publish content |
| Analyze content | Delete data |
| Create internal tasks | Modify permissions |
| Local computations | External API calls |
| Search/query | Financial operations |

---

## IAM Design

**Module:** `apps/api/app/security/iam.py`

### Human/AI Account Separation

```
Human Accounts              AI Accounts
─────────────               ───────────
✓ Full admin access         ✗ Admin access denied
✓ Secret management         ✗ Secret access denied
✓ Permission changes        ✗ Cannot modify permissions
✓ Security config           ✗ Security config read-only
✓ Audit log access          ✓ Audit log write (own actions)
✓ User management           ✗ Cannot create/delete users
```

**Key principle:** AI agents are never granted admin or secret-management permissions, regardless of user instructions.

---

## File Sandbox

**Module:** `apps/api/app/security/sandbox.py`

### Whitelist-Based Access Control

Default mode: **STRICT**

```
Allowed (whitelist):
  ✓ User-designated workspace folders
  ✓ Internal storage directories
  ✓ Temporary processing directories

Blocked (everything else):
  ✗ System directories (/etc, /usr, /var)
  ✗ User home directories (unless explicitly permitted)
  ✗ Other application data
  ✗ Network mounts (unless explicitly permitted)
```

### Configuration

Users can expand the sandbox by explicitly granting folder access:

```bash
zero-employee config set SANDBOX_ALLOWED_PATHS "/path/to/project,/path/to/data"
```

---

## Data Protection

**Module:** `apps/api/app/security/data_protection.py`

### Upload/Download Policy

Default mode: **LOCKDOWN**

| Operation | Default | Description |
|-----------|---------|-------------|
| **Upload to AI** | Blocked | Files cannot be sent to external AI services |
| **Download from AI** | Blocked | AI-generated files restricted |
| **Internal transfer** | Allowed | Data movement within ZEO is permitted |
| **Export** | Requires approval | All exports go through approval gates |

### Policy Levels

| Level | Upload | Download | Export |
|-------|--------|----------|--------|
| `LOCKDOWN` | ✗ | ✗ | Approval |
| `RESTRICTED` | Approved types only | Approved types only | Approval |
| `STANDARD` | Most types | Most types | Logged |
| `OPEN` | All types | All types | Logged |

**Always blocked regardless of policy:** passwords, credentials, private keys.

---

## PII Protection

**Module:** `apps/api/app/security/pii_guard.py`

### 13 Categories of Personal Information

| # | Category | Detection Pattern |
|---|----------|------------------|
| 1 | **Email addresses** | RFC 5322 pattern matching |
| 2 | **Phone numbers** | International format detection |
| 3 | **Credit card numbers** | Luhn algorithm validation |
| 4 | **Social security numbers** | Country-specific patterns |
| 5 | **Passport numbers** | Format-based detection |
| 6 | **Driver's license** | Region-specific patterns |
| 7 | **Physical addresses** | Address parsing and detection |
| 8 | **Date of birth** | Date pattern in PII context |
| 9 | **IP addresses** | IPv4/IPv6 detection |
| 10 | **Bank account numbers** | IBAN and domestic formats |
| 11 | **Medical records** | Health-related identifiers |
| 12 | **Biometric data** | Biometric identifier patterns |
| 13 | **Personal names** | Named entity recognition |

### Auto-Masking

PII is automatically detected and masked before being passed to AI:

```
Input:  "Contact John Smith at john@example.com, phone 555-0123"
Masked: "Contact [NAME] at [EMAIL], phone [PHONE]"
```

---

## Workspace Isolation

**Module:** `apps/api/app/security/workspace_isolation.py`

### Default Isolation

In the initial state, AI has **no access** to:
- Local filesystem (beyond sandbox)
- Cloud storage services
- External databases
- Network resources

### Environment Override

When chat instructions conflict with system settings, `should_request_approval()` prompts the user:

```
⚠️  The requested action requires access to [resource].
    Current policy: ISOLATED
    Requested: READ access to /external/data

    Allow this access? [y/N]
```

---

## Secret Management

**Module:** `apps/api/app/security/secret_manager.py`

| Feature | Description |
|---------|-------------|
| **Encryption** | Fernet symmetric encryption (AES-128-CBC) |
| **Auto-masking** | Secrets automatically masked in logs and outputs |
| **Rotation support** | Key rotation without downtime |
| **Access control** | AI agents cannot read raw secrets |
| **Audit trail** | All secret access attempts logged |

---

## Security Headers

**Module:** `apps/api/app/security/security_headers.py`

Applied to all HTTP responses:

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | Strict CSP | Prevents XSS |
| `Strict-Transport-Security` | max-age=31536000 | Forces HTTPS |
| `X-Frame-Options` | DENY | Prevents clickjacking |
| `X-Content-Type-Options` | nosniff | Prevents MIME sniffing |
| `X-XSS-Protection` | 1; mode=block | XSS filter |
| `Referrer-Policy` | strict-origin-when-cross-origin | Controls referrer info |

---

## Rate Limiting

**Module:** `apps/api/app/core/rate_limit.py`

Built on `slowapi`:

- Per-IP rate limiting
- Per-user rate limiting
- Per-endpoint customization
- Configurable limits and windows

---

## Sanitization

**Module:** `apps/api/app/security/sanitizer.py`

Automatically removes from all outputs and logs:

- API keys and tokens
- Passwords and credentials
- Connection strings
- Private keys
- Internal system paths

---

## Audit Logging

**Module:** `apps/api/app/audit/`

All critical operations are recorded:

| Field | Description |
|-------|-------------|
| `timestamp` | When the action occurred |
| `actor` | Who (human or AI agent) performed it |
| `action` | What was done |
| `target` | What was affected |
| `model_used` | Which LLM model was involved |
| `approval_id` | Link to human approval (if required) |
| `result` | Success/failure and details |

---

## Red-Team Security Testing

Built-in self-vulnerability assessment:

### 8 Test Categories

| # | Category | Tests |
|---|----------|-------|
| 1 | **Prompt injection** | Direct, indirect, encoding-based |
| 2 | **Data exfiltration** | System prompt leak, context extraction |
| 3 | **Privilege escalation** | Role bypass, permission elevation |
| 4 | **Authentication bypass** | Token manipulation, session hijacking |
| 5 | **Input validation** | Boundary testing, malformed input |
| 6 | **Output manipulation** | Response injection, format exploitation |
| 7 | **Resource abuse** | Token bomb, infinite loop, cost attack |
| 8 | **Supply chain** | Malicious skill/plugin injection |

Run security assessment:

```bash
zero-employee security status
```

---

## Production Deployment Checklist

Before deploying ZEO to production, verify:

### Infrastructure

- [ ] PostgreSQL configured (not SQLite)
- [ ] HTTPS enabled with valid certificates
- [ ] Reverse proxy configured (nginx/Caddy)
- [ ] Firewall rules restrict port 18234 access
- [ ] Docker containers run as non-root user

### Security Settings

- [ ] `SANDBOX_MODE` set to `STRICT`
- [ ] `DATA_PROTECTION_LEVEL` set to `LOCKDOWN` or `RESTRICTED`
- [ ] `PII_GUARD_ENABLED` is `true`
- [ ] API rate limiting configured
- [ ] CORS origins restricted to known domains

### Secrets

- [ ] All API keys stored via `secret_manager.py` (not env vars)
- [ ] Fernet encryption key rotated from default
- [ ] Database credentials not in plaintext config
- [ ] No secrets in git history

### Monitoring

- [ ] Sentry configured for error tracking
- [ ] Audit logs exported to persistent storage
- [ ] Rate limit alerts configured
- [ ] Health check endpoint monitored

### Access Control

- [ ] Admin accounts use strong passwords
- [ ] AI accounts have minimal permissions
- [ ] API keys have appropriate scopes
- [ ] Session timeout configured

---

## Further Reading

- [Quickstart Guide](quickstart-guide.md) — Get up and running
- [Architecture Guide](architecture-guide.md) — System architecture details
- [SECURITY.md](../../SECURITY.md) — Vulnerability reporting
- [Main README](../../README.md) — Project overview
