# Privacy Policy — Zero-Employee Orchestrator

**Last updated: 2026-04-08**

## Overview

Zero-Employee Orchestrator ("ZEO") is an open-source AI orchestration platform. This privacy policy covers the ZEO Browser Assist Chrome extension and the ZEO platform.

## Data Collection

### Browser Assist Chrome Extension

The Browser Assist extension:

- **Screenshots**: Temporarily captures screenshots of the active tab for AI analysis when explicitly requested by the user. Screenshots are processed in-memory and **never stored permanently** on any server.
- **Page content**: May read visible text on the current page to provide contextual AI assistance, only when the user initiates a chat interaction.
- **No tracking**: The extension does not track browsing history, collect analytics, or transmit data to third parties.
- **Local communication only**: All data is sent exclusively to the user's local ZEO server instance (`localhost:18234`) and never to external servers.

### ZEO Platform

- **API keys**: Stored locally using Fernet encryption (AES-128-CBC + HMAC-SHA256). Never transmitted to ZEO servers.
- **Task data**: All task data, conversations, and artifacts are stored in the user's local database.
- **No telemetry**: ZEO does not collect usage telemetry, analytics, or crash reports.
- **PII detection**: The platform automatically detects and masks personally identifiable information (PII) before AI processing.

## Data Storage

All data is stored locally on the user's device:
- SQLite database (default) or user-configured PostgreSQL
- Encrypted credential store (`/data/credentials/`)
- No cloud storage unless explicitly configured by the user

## Third-Party Services

ZEO connects to third-party LLM providers (OpenAI, Anthropic, Google, etc.) only when:
1. The user has explicitly configured an API key for that provider
2. The user initiates a task that requires AI processing

Data sent to LLM providers is subject to each provider's own privacy policy.

## Data Sharing

ZEO does **not**:
- Sell, rent, or share user data with any third party
- Collect or transmit data to ZEO developers or any central server
- Include advertising or tracking

## User Rights

Users have full control over their data:
- All data is stored locally and can be deleted at any time
- Database files can be exported or destroyed by the user
- No account registration is required (anonymous sessions available)

## Security

- 14-layer defense-in-depth security architecture
- Sandbox-restricted file access
- Approval gates for dangerous operations
- Automatic PII detection and masking
- Rate limiting on all API endpoints

## Contact

For privacy concerns, please open an issue at:
https://github.com/OrosiTororo/Zero-Employee-Orchestrator/issues

## Changes

This privacy policy may be updated with new releases. Changes will be documented in the CHANGELOG.
