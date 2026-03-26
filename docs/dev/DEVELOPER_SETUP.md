# Developer Setup Guide

> Configuration items for ZEO core development and quality management.
> For developers who develop and maintain the ZEO codebase.
>
> For all settings related to ZEO installation, operation, and feature expansion (security, database, deployment, API keys, workspace, etc.), see `USER_SETUP.md`.
>
> Last updated: 2026-03-26

---

## 1. Error Monitoring (Sentry)

Configuration for bug tracking and error monitoring of ZEO itself. Used by the development team to monitor ZEO quality, not for user environments.

```bash
zero-employee config set SENTRY_DSN <your-dsn>
```

---

## 2. Red-team Security Testing

Tests for verifying ZEO's own vulnerabilities. Recommended to run periodically before and after releases.

```bash
# Security check script
./scripts/security-check.sh

# Run red-team tests via API
POST /api/v1/security/redteam/run
```

---

*Zero-Employee Orchestrator -- Developer Setup Guide*
