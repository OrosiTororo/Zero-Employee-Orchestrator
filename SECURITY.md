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

Run the included security check script before deployment:
```bash
./scripts/security-check.sh
```
