# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**DO NOT** open a public issue for security vulnerabilities.

Instead, please use one of the following methods:

1. **GitHub Security Advisories**: Use the [Security tab](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/security/advisories/new) to report privately.
2. **Email**: Contact the maintainer via the email listed on the [GitHub profile](https://github.com/OrosiTororo).

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix or mitigation**: Depending on severity, typically within 2 weeks for critical issues

## Security Architecture

Zero-Employee Orchestrator implements a **defense-in-depth** security model with 9 layers:

### 1. Prompt Injection Defense (`security/prompt_guard.py`)

Detects and blocks instruction injection from external sources (web pages, emails, files, API responses).

- **CRITICAL**: System prompt override attempts ("ignore previous instructions", role reassignment)
- **HIGH**: Privilege escalation, data exfiltration attempts
- **MEDIUM**: Indirect injection, boundary manipulation
- External data is structurally separated using boundary markers (`wrap_external_data()`)
- User origin verification for authenticated sessions

### 2. Approval Gate (`policies/approval_gate.py`)

14 categories of dangerous operations require human approval:
- External send / publish / delete / billing
- Git push / release / file overwrite
- Permission change / credential change
- Agent creation / budget change / policy change / autonomy expansion

### 3. Autonomy Boundary (`policies/autonomy_boundary.py`)

Explicit limits on what AI can do autonomously:
- **Allowed**: research, analyze, draft, summarize, organize, translate, search
- **Approval required**: publish, post, send, delete, charge, permission changes

### 4. IAM (`security/iam.py`)

- Human / AI Agent / Service account separation
- AI-denied permissions: READ_SECRETS, ADMIN, MANAGE_IAM, APPROVE_ACTIONS

### 5. Security Headers (`security/security_headers.py`)

OWASP-recommended headers on all responses:
- Content-Security-Policy (default-src 'self')
- Strict-Transport-Security (HSTS)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy (camera, microphone, geolocation, payment disabled)
- Cache-Control for authenticated responses

### 6. Request Validation (`security/security_headers.py`)

- Maximum body size: 10MB
- Host header injection prevention
- Content-Length validation

### 7. Secret Management (`security/secret_manager.py`)

- Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
- Automatic masking with configurable visibility
- Expiration checking and rotation support

### 8. Sanitization (`security/sanitizer.py`)

Automatic detection and redaction of:
- API keys (sk-*, sk-or-v1-*)
- Bearer tokens
- OAuth tokens (ya29.*)
- Passwords and secrets
- Email addresses

### 9. Rate Limiting (`core/rate_limit.py`)

- slowapi-based API rate limiting
- Per-endpoint configurable limits

## Security Best Practices for Deployment

Before deploying to production, ensure:

1. **SECRET_KEY**: Generate a strong random key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. **DEBUG**: Set `DEBUG=false` in production
3. **CORS_ORIGINS**: Restrict to your actual domain(s)
4. **JWT_SECRET** (Edge): Set via `wrangler secret put JWT_SECRET`
5. **Database**: Use PostgreSQL instead of SQLite for production
6. **HTTPS**: Always use HTTPS in production
7. **API Keys**: Never commit API keys to the repository
8. **Prompt Injection**: Use `wrap_external_data()` when passing external data to LLMs

Run the included security check script before deployment:
```bash
./scripts/security-check.sh
```

## Browser Assist Privacy

The Browser Assist extension follows strict privacy rules:
- Screenshots are processed temporarily only (never stored permanently)
- Password fields are automatically blurred
- Explicit user consent is required before any screen capture
- No autonomous clicking — guidance only
- All captures are audit logged (image hash only, not the image itself)
