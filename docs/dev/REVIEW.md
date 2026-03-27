# Zero-Employee Orchestrator — Comprehensive Code Review

> Objective review conducted on 2026-03-27.
> Scope: All files in the repository (64K+ lines of Python, TypeScript frontend, CI/CD, Docker).

---

## Executive Summary

Zero-Employee Orchestrator is an ambitious AI orchestration platform with a well-designed 9-layer
architecture, 350+ API endpoints, and comprehensive security layering. The backend is feature-rich
and the architectural foundations are solid. However, the review identified **critical security
gaps**, **missing error handling**, **incomplete frontend data connections**, and **insufficient
test coverage** that should be addressed before production deployment.

### Severity Breakdown

| Severity | Count | Category |
|----------|-------|----------|
| CRITICAL | 8 | Security bypasses, data loss risks |
| HIGH | 14 | Functional bugs, missing validation |
| MEDIUM | 18 | Performance, code quality, maintainability |
| LOW | 12 | Style, documentation, minor improvements |

---

## 1. CRITICAL Security Issues

### 1.1 Unbounded Base64 Recursion in Prompt Guard
- **File**: `apps/api/app/security/prompt_guard.py:214`
- **Issue**: `scan_prompt_injection()` recursively decodes Base64 with no depth limit
- **Risk**: Stack overflow via deeply nested encoding; DoS vector
- **Fix**: Add `max_depth` parameter (default 3)

### 1.2 Unsafe URL Prefix Matching in Data Protection
- **File**: `apps/api/app/security/data_protection.py:214-216`
- **Issue**: `destination.startswith(d)` allows subdomain spoofing
- **Example**: Allowed `https://example.com` also permits `https://example.com.attacker.com`
- **Fix**: Use `urllib.parse` for proper domain comparison

### 1.3 Weak Boundary Marker Escaping
- **File**: `apps/api/app/security/prompt_guard.py:311`
- **Issue**: Simple `replace("<<<", "\\<<<")` can be bypassed with unicode variants
- **Fix**: Use unique random boundary tokens per invocation

### 1.4 TOCTOU Race in Sandbox Symlink Check
- **File**: `apps/api/app/security/sandbox.py:213`
- **Issue**: Gap between `os.path.islink()` check and actual file access
- **Risk**: Attacker can swap file between check and use
- **Fix**: Resolve path atomically and verify after opening

### 1.5 Silent Sanitization Failures in LLM Gateway
- **File**: `apps/api/app/providers/gateway.py:339-341`
- **Issue**: `_sanitize_messages()` catches all exceptions and returns unsanitized messages
- **Risk**: Prompt injection bypasses security on any sanitization error
- **Fix**: Raise on sanitization failure; never silently skip

### 1.6 No LLM Request Timeout
- **File**: `apps/api/app/providers/gateway.py:362`
- **Issue**: `litellm.acompletion()` called without timeout parameter
- **Risk**: Requests can hang indefinitely, exhausting resources
- **Fix**: Add configurable timeout (default 120s)

### 1.7 Ephemeral Secret Manager Keys
- **File**: `apps/api/app/security/secret_manager.py:104`
- **Issue**: `Fernet.generate_key()` creates new key on every process restart
- **Risk**: All stored secrets become unrecoverable after restart
- **Status**: Already documented as not production-ready; needs external secret store

### 1.8 Legacy Password Hash Support
- **File**: `apps/api/app/core/security.py:35-37`
- **Issue**: SHA-256 and plain-text hashes still accepted for password verification
- **Risk**: Brute-force attacks on legacy-hashed passwords
- **Fix**: Migrate all passwords to bcrypt; remove legacy paths with deprecation warning

---

## 2. HIGH Priority Issues

### 2.1 Missing State Machine History Bounds
- **File**: `apps/api/app/orchestration/state_machine.py:46-47`
- **Issue**: History list grows unbounded — no pruning or size limit
- **Risk**: Memory leak in long-running processes
- **Fix**: Add `max_history` parameter with circular buffer

### 2.2 Thread-Unsafe Global Singletons
- **File**: `apps/api/app/providers/model_registry.py:635-636`
- **Issue**: `get_model_registry()` has check-then-act race on `_registry`
- **Fix**: Use `threading.Lock` for singleton initialization

### 2.3 Denied Path Pattern Bypass in Sandbox
- **File**: `apps/api/app/security/sandbox.py:252`
- **Issue**: `.env` is denied but `.env.backup` passes filename check
- **Fix**: Match denied patterns against all path segments, not just basename

### 2.4 No Content Preview Requirement for Upload Checks
- **File**: `apps/api/app/security/data_protection.py:176-177`
- **Issue**: Password blocking only applies when `content_preview` is provided
- **Risk**: Omitting preview skips sensitive content detection entirely
- **Fix**: Require preview or block when preview is empty

### 2.5 Incomplete OAuth / Auth Flows
- **File**: `apps/api/app/api/routes/auth.py:85-94`
- **Issue**: Google OAuth and generic OAuth endpoints return 501
- **Missing**: Password reset, email verification, MFA, token invalidation on logout

### 2.6 Frontend Silent API Failures
- **File**: `apps/desktop/ui/src/pages/DashboardPage.tsx:40-42`
- **Issue**: API errors caught silently with no user feedback
- **Impact**: Users see stale/empty data without understanding why

### 2.7 No Frontend Error Boundaries or 404 Route
- **File**: `apps/desktop/ui/src/app/router.tsx`
- **Issue**: No React error boundary; no catch-all route
- **Impact**: Unhandled errors crash the entire app

### 2.8 WebSocket Reconnection Strategy
- **File**: `apps/desktop/ui/src/shared/hooks/use-websocket.ts`
- **Issue**: Only retries once after 3 seconds; no exponential backoff
- **Fix**: Implement exponential backoff with jitter

### 2.9 Stub Implementations in Connectors
- **File**: `apps/api/app/tools/connector.py:462-523`
- **Issue**: WebSocket, Database, and gRPC execution methods return hardcoded stubs
- **Impact**: Features appear available in API but do nothing

### 2.10 Over-Permissive MODERATE Sandbox Extensions
- **File**: `apps/api/app/security/sandbox.py:125-126`
- **Issue**: `.sh` and `.bash` files allowed in MODERATE mode
- **Risk**: Shell scripts may contain embedded secrets or passwords

### 2.11 Missing Exfiltration Protocol Detection
- **File**: `apps/api/app/security/prompt_guard.py:128-141`
- **Issue**: Only detects `http://`, `ftp://`, `wss://` — misses `dns://`, `ldap://`, `gopher://`

### 2.12 No Approval Audit Trail
- **Files**: `apps/api/app/policies/approval_gate.py`, `autonomy_boundary.py`
- **Issue**: Approval decisions are not logged with who/when/what

### 2.13 Operation Name Evasion in Approval Gate
- **File**: `apps/api/app/policies/approval_gate.py:60-78`
- **Issue**: Only exact operation names trigger approvals; synonyms bypass
- **Example**: `send_email` requires approval but `transmit_email` does not

### 2.14 Frontend API Client — No Request Timeout
- **File**: `apps/desktop/ui/src/shared/api/client.ts`
- **Issue**: Fetch calls have no `AbortController` timeout

---

## 3. MEDIUM Priority Issues

### 3.1 Performance

| File | Issue |
|------|-------|
| `gateway.py:259-264` | `_configured_models()` rebuilds list on every call; needs caching |
| `model_registry.py:310-316` | Reverse lookup by `latest_model_id` is O(n); needs index |
| `state_machine.py:56-57` | Available transitions rebuilt from dict every call |
| `cost_guard.py:33-44` | `_load_cost_table()` catches all exceptions silently |
| `judge.py:342-373` | Contradiction detection is O(n²) per key |

### 3.2 Code Duplication

| Location | Duplicated Pattern |
|----------|-------------------|
| `gateway.py:166-222` | Provider configuration repeated 4 times |
| `cli.py:296-510` | Two chat functions share identical conversation management |
| `judge.py:337-511` | Repeated section headers and docstring patterns |
| `ticket_service.py` + `task_service.py` | Identical transition validation and audit logging |
| `connector.py:296-535` | Auth header building duplicated across handlers |

### 3.3 Missing Type Hints
- `judge.py:33-38` — `rules: list[dict]` should use `TypedDict`
- `gateway.py:49-53` — `messages: list[dict]` untyped
- `state_machine.py:150` — `conditions: dict` untyped
- `dag.py:33` — `provider_override: dict | None` untyped

### 3.4 Architectural Concerns

- **Global mutable state**: `llm_gateway` (gateway.py:558), judge instances (judge.py:633),
  `experience_memory` (state_machine.py:244) — all created at module level
- **Circular imports**: DAG and Judge both import from `policies.autonomy_boundary`
- **No dependency injection**: Gateway, sandbox, and data protection guards are global singletons
- **Transaction safety**: Multiple `db.commit()` calls without wrapping transactions

### 3.5 CI/CD Gaps
- No frontend unit tests in CI
- No end-to-end tests
- No database migration validation
- No dependency security audit (pip-audit, snyk)
- No pytest coverage reporting

### 3.6 Docker Issues
- `docker-compose.yml`: SECRET_KEY defaults to empty string
- No database volume persistence for SQLite
- No resource limits (CPU/memory) on containers
- Worker service has no graceful shutdown handling

---

## 4. LOW Priority Issues

### 4.1 Documentation
- Some functions lack docstrings for exceptions, side effects, and examples
- Japanese comments in frontend code reduce international accessibility
- ROADMAP.md is transparent and honest about feature status (good)

### 4.2 Frontend UX
- No loading spinners for async operations
- No form validation feedback
- No empty states for pages with no data
- Settings page uses 10+ `useState` — should use `useReducer` or form library
- Hardcoded cost display (`$0.00`) in Dashboard

### 4.3 Configuration
- `config.py:56-61` — CORS origins include development-only Tauri URLs in production
- `config.py:73` — Hardcoded `OLLAMA_TIMEOUT` (300s)
- `.env.example` — SECRET_KEY advice shows `change-this` instead of generation command

---

## 5. What's Done Well

- **Security-first defaults**: LOCKDOWN transfer policy, STRICT sandbox, comprehensive denied paths
- **9-layer architecture**: Clean separation of concerns with well-defined boundaries
- **Multi-provider LLM support**: Ollama, g4f, LiteLLM with auto-discovery
- **Family-based model IDs**: `model_catalog.json` allows version updates without code changes
- **Comprehensive approval gates**: 12 categories of dangerous operations
- **Prompt injection defense**: 5 categories, 40+ patterns including Japanese
- **PII detection**: 13 categories with masking
- **Extensive API surface**: 350+ endpoints covering the full domain
- **Version management**: 8-file version sync with bump script and CI check
- **Plugin/Skill/Extension model**: VS Code-inspired extensibility architecture

---

## 6. Recommended Priority Actions

### Immediate (This Sprint)
1. Fix Base64 recursion depth limit in prompt_guard
2. Fix URL prefix matching in data_protection (use proper URL parsing)
3. Add LLM request timeout to gateway
4. Add state machine history bounds
5. Add thread lock to model_registry singleton
6. Expand test coverage for security modules
7. Improve sandbox denied path matching

### Short-term (Next 2 Sprints)
1. Complete OAuth / password reset flows
2. Add frontend error boundaries and 404 route
3. Implement WebSocket reconnection with exponential backoff
4. Add CSRF protection to state-changing endpoints
5. Add dependency security scanning to CI
6. Wire up Sentry integration

### Medium-term (Next Quarter)
1. Migrate from SQLite to PostgreSQL for production
2. Add distributed tracing (OpenTelemetry)
3. Implement proper dependency injection
4. Complete frontend data connections (currently many stubs)
5. Add end-to-end test suite

---

## 7. Comparison with Industry Best Practices (2026)

### 7.1 OWASP LLM Top 10 (2025) Compliance

Prompt injection remains the #1 vulnerability (LLM01:2025). The current system addresses this
with 5-category, 40+ pattern detection, but industry standards now recommend:

| OWASP Recommendation | ZEO Status | Gap |
|---------------------|------------|-----|
| Multi-layer input validation (pattern + fuzzy) | Partial — pattern-based only | Add fuzzy/typoglycemia detection |
| System prompt isolation from user data | Done — boundary markers | Improved with unique random tokens |
| Privilege separation / least privilege | Done — IAM + sandbox | Good |
| Output validation and sandboxing | Partial — Judge layer | Add LLM output sanitization before execution |
| Human-in-the-loop for high-risk actions | Done — 12-category approval gates | Good |
| External enforcement layer | Partial — policy layer | Consider decoupling enforcement from LLM process |
| Continuous red-team testing | Stubbed — `redteam.py` exists | Implement automated red-team pipeline |
| RAG poisoning defense | Not addressed | Add document integrity verification for knowledge store |
| Multi-turn jailbreak detection | Not addressed | Add conversation-level pattern analysis |
| Multimodal injection detection | Not addressed | Add image/file content scanning for hidden instructions |

Sources:
- [OWASP LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [Prompt Injection: Risks and Defenses in 2026](https://witness.ai/blog/prompt-injection/)

### 7.2 A2A Protocol Compatibility

Google's Agent-to-Agent (A2A) protocol, now under the Linux Foundation, is emerging as the
standard for multi-agent interoperability. ZEO already has `a2a_communication.py` in the
orchestration layer, but should align with the official A2A specification:

| A2A Feature | ZEO Status | Recommendation |
|-------------|------------|----------------|
| Agent Cards (JSON metadata) | Not implemented | Add agent card generation/discovery |
| HTTPS/TLS + JWT authentication | JWT exists | Align with A2A auth spec |
| gRPC support (A2A v0.3) | Not implemented | Consider for performance-critical agent comms |
| Task lifecycle (submitted/working/done) | Done — state machine | Already aligned |
| Streaming via SSE | WebSocket exists | Add SSE as alternative |
| Push notifications | Not implemented | Add webhook-based push for async results |

The A2A protocol is complementary to MCP (which ZEO already supports) — MCP handles agent-to-tool
communication while A2A handles agent-to-agent communication.

Sources:
- [A2A Protocol Official](https://a2a-protocol.org/latest/)
- [A2A Protocol Explained (OneReach)](https://onereach.ai/blog/what-is-a2a-agent-to-agent-protocol/)
- [Building Secure AI Applications with A2A (arXiv)](https://arxiv.org/abs/2504.16902)
- [Linux Foundation A2A Project Launch](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)

### 7.3 MAESTRO Threat Modeling Framework

The MAESTRO (Multi-Agent Environment, Security, Threat, Risk, and Outcome) framework is
specifically designed for multi-agent AI risk assessment. ZEO should adopt its methodology
for ongoing threat modeling:

- **Agent Card management**: Validate and sign agent metadata
- **Task execution integrity**: Verify task results haven't been tampered with
- **Authentication methodologies**: Per-agent credential scoping
- **Inter-agent trust boundaries**: Define explicit trust levels between agents

### 7.4 Key Industry Trends (2026)

1. **40% of enterprise apps will feature AI agents by 2026** (Gartner) — ZEO is well-positioned
2. **Defense-in-depth is mandatory** — Single-layer defenses proven insufficient against persistent attackers
3. **LLM output must be treated as untrusted** — Judge layer is a good start, add output sanitization
4. **RAG poisoning** is a growing attack vector — 5 crafted documents can manipulate AI responses 90% of the time
5. **Vendor-neutral agent protocols** (A2A, MCP) are consolidating — alignment reduces integration friction
