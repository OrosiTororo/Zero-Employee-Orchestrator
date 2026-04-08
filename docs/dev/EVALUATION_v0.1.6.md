# Zero-Employee Orchestrator — v0.1.6 Evaluation Report

> Evaluation date: 2026-04-07
> Evaluator: Claude Code (Opus 4.6, full automated verification)
> Scope: Full system — backend, frontend, CLI, security, tests, documentation
> Previous: v0.1.5 corrected — 6.3/10

---

## 0. Methodology

This evaluation was conducted through:
1. **4 parallel exploration agents** examining backend, frontend, CLI/plugins, and security modules
2. **Automated execution**: ruff lint, pytest, TypeScript type check, Vite build, server startup
3. **Code-level verification**: endpoint counting via grep, module counting, CSS class validation
4. **Documentation cross-reference**: All claims checked against actual code

---

## 1. Build & Quality Status

| Check | Result | Previous |
|---|---|---|
| `ruff check apps/api/app/` | All checks passed (239 files) | Same |
| `ruff format --check apps/api/app/` | All 239 files formatted | Same |
| `npx tsc --noEmit` (frontend) | Pass — 0 errors | Same |
| `npx vite build` (frontend) | Pass — built in 409ms | Same |
| `pytest apps/api/app/tests/` | **467 passed, 0 failed, 0 errors** | 392 passed, 8 failed, 75 errors |
| Server startup | Successful (port 18234) | Same |
| Python version | 3.11+ | Same |

**Key improvement**: Test suite went from 75 errors + 8 failures → **0 errors, 0 failures** by fixing test DB fixture ordering.

---

## 2. Quantitative Code Audit

### Backend (apps/api/app/)

| Component | Count | Status |
|---|---|---|
| Route modules | 46 | Correct |
| Endpoints (routes 389 + main 3) | **392** | Corrected from 394/396 |
| Service modules | 25 | All implemented |
| Orchestration modules | 23 | All implemented (~8,600 lines) |
| Security modules | 12 | All implemented (~4,000+ lines) |
| Policy modules | 2 | approval_gate + autonomy_boundary |
| Provider modules | 7 | gateway, model_registry, ollama (×2), g4f, local_rag, web_session |
| Test files | 28 | **467 tests, all passing** |
| Bare `pass` in all code | ~15 | All in exception handlers (correct) |
| `NotImplementedError` | 2 | Abstract methods in connector.py (correct) |

### Frontend (apps/desktop/ui/)

| Component | Count | Status |
|---|---|---|
| Page components | 29 | All implemented |
| Dependencies | 12 prod + 17 dev | Reasonable |
| i18n locales | 6 (en/ja/zh/ko/pt/tr) | Full coverage |
| Build output | 18 chunks | Largest: index (296KB / 85KB gzip) |
| TypeScript strict mode | Enabled | `strict: true` |

### Skills / Plugins / Extensions

| Component | Claimed | Actual | Status |
|---|---|---|---|
| Builtin skills | 11 (6 system + 5 domain) | 11 (6 system + 5 domain) | Correct |
| Plugins | 16 (10 general + 6 role-based) | 16 (10 general + 6 role-based) | Correct |
| Extensions | 11 | 11 | Correct |

---

## 3. Issues Found & Fixed

### 3.1 Fixed in This Audit

| # | Issue | Severity | Fix |
|---|---|---|---|
| 1 | **Test suite: 75 errors** — `conftest.py` runs `create_all` before `drop_all`, causing "table already exists" when DB file persists | HIGH | Added `drop_all` before `create_all` in `setup_db` fixture |
| 2 | **DashboardPage.tsx: 6 broken CSS classes** — missing spaces between Tailwind classes (e.g., `bg-[var(--bg-surface)]overflow-hidden`) | MEDIUM | Added missing spaces in all 6 occurrences |
| 3 | **Endpoint count wrong in 5 docs** — CLAUDE.md, ROADMAP.md, architecture-guide.md, FEATURES.md, REVIEW.md all showed 394 or 433 instead of actual 392 | LOW | Corrected to 392 in all files |
| 4 | **ROADMAP.md: "22 orchestration modules"** — actual count is 23 | LOW | Corrected to 23 |

### 3.2 Remaining Issues (Not Fixed — Documented)

| # | Issue | Severity | Recommendation |
|---|---|---|---|
| 1 | **~28 hardcoded English error messages** in frontend toast notifications | MEDIUM | Add i18n keys for error messages in all 6 locale files |
| 2 | **DispatchPage.tsx: 2 hardcoded strings** not using i18n | LOW | Add `dispatch.subtitle` and `dispatch.helpText` to locale files |
| 3 | **`any` type usage** in ~15 locations despite `strict: true` | LOW | Replace `catch (e: any)` with `catch (e: unknown)`, add proper API response types |
| 4 | **`(window as any).__TAURI_INTERNALS__`** — unsafe type assertion | LOW | Add Tauri type declarations |
| 5 | **`TestSeverity` class in redteam.py** triggers pytest collection warning | LOW | Rename to `_TestSeverity` or add `__test__ = False` |
| 6 | **CLI slash commands** (`/read`, `/write`, etc.) delegate to LLM instead of direct execution | INFO | Documented design decision — CLAUDE.md should clarify |
| 7 | **Meta-orchestration** (CrewAI, LangGraph) remains config-level integration | INFO | Deeper runtime integration for future |
| 8 | **Bundle size**: index.js 296KB (85KB gzip) | INFO | Consider code splitting for heavy pages |

---

## 4. Relative Evaluation (vs Competitors)

### 4.1 vs Claude Cowork

| Dimension | Claude Cowork | ZEO v0.1.6 | Winner |
|---|---|---|---|
| UX polish | Consumer-grade, desktop-native | 29-page functional prototype | Cowork |
| Setup friction | Download → sign in | Python 3.11+ + config | Cowork |
| Task execution | Real (Computer Use) | Real (DAG → LLM → Judge → Re-Propose) | Cowork (deeper) |
| Model support | Claude only | 22+ families (multi-provider) | ZEO |
| Self-hosting | Impossible | Full (Docker, Tauri, Cloudflare) | ZEO |
| Cost | $20-200/mo | Free (users pay providers) | ZEO |
| Meta-orchestration | Own plugins only | CrewAI, AutoGen, LangChain, Dify sub-workers | ZEO |
| Security depth | Enterprise controls | 14-layer defense (12 security modules) | ZEO |
| Offline mode | No | Yes (Ollama) | ZEO |
| Test suite | N/A (closed source) | 467 tests, 100% pass rate | ZEO (transparent) |

### 4.2 vs Developer Frameworks (CrewAI, LangGraph, AutoGen, Dify)

- **Advantage**: ZEO is a meta-orchestrator integrating these as sub-workers, not competing directly
- **Judge layer** (848 lines, cross-model verification) is a genuine differentiator
- **DAG execution** (199 lines) is simpler than LangGraph equivalent but includes parallel node support
- **Security posture** far exceeds any competitor (12 modules vs typically 0-2)

**Relative Score: 6.0/10** (unchanged)

---

## 5. Objective Evaluation (First-Time User)

| Dimension | Score | Notes |
|---|---|---|
| README clarity | 7/10 | Comprehensive, accurate counts now |
| Install experience | 4/10 | Requires Python 3.11+, no PyPI release |
| Time to first value | 5/10 | Execution works E2E; needs LLM provider setup |
| Error handling | 5.5/10 | Backend: good. Frontend: hardcoded English toasts |
| Documentation | 7/10 | 64 md files, 7 languages, architecture guide |
| UI intuitiveness | 7/10 | Autonomy Dial, Command Palette, Welcome Tour |
| Trust & transparency | 6.5/10 | Execution shows cost, tokens, judge scores; 467 passing tests |

**Objective Score: 6.0/10** (up from 5.9 — test reliability + doc accuracy improvements)

---

## 6. Additional Perspectives

| Dimension | Score | Notes |
|---|---|---|
| Architecture quality | 8/10 | Clean 9-layer design, well-separated concerns |
| Implementation reality | 6.0/10 | All 23 orchestration modules implemented, 467 tests pass |
| Security posture | 7.5/10 | 12 security modules, path boundary checks verified correct |
| i18n / Accessibility | 6.5/10 | 6 locales but ~28 hardcoded English error messages remain |
| Cost to operate | 9/10 | Free; users pay LLM providers directly |
| Deployment readiness | 5.5/10 | Docker + Cloudflare Workers ready; no PyPI package yet |

---

## 7. Scoring

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| **Relative (vs competitors)** | 6.0 | 0.35 | 2.10 |
| **Objective (first-time user)** | 6.0 | 0.35 | 2.10 |
| **Architecture quality** | 8.0 | 0.08 | 0.64 |
| **Implementation reality** | 6.0 | 0.07 | 0.42 |
| **Security posture** | 7.5 | 0.05 | 0.38 |
| **i18n / Accessibility** | 6.5 | 0.03 | 0.20 |
| **Cost to operate** | 9.0 | 0.04 | 0.36 |
| **Deployment readiness** | 5.5 | 0.03 | 0.17 |

**Overall: 6.4/10** (up from 6.3 — test suite fully passing, doc accuracy improved, CSS bugs fixed)

---

## 8. Key Changes from v0.1.5 corrected

| Area | v0.1.5 corrected | v0.1.6 |
|---|---|---|
| Test results | 392 passed, 8 failed, 75 errors | **467 passed, 0 failed, 0 errors** |
| Endpoint count (docs) | 394 (wrong) | 392 (verified) |
| DashboardPage CSS | 6 broken class strings | Fixed |
| Orchestration count (ROADMAP) | 22 (wrong) | 23 (verified) |

---

## 9. Recommendations for Score Improvement

### To reach 7.0/10:
1. **i18n error messages** — Replace ~28 hardcoded English toast messages with i18n keys (+0.2)
2. **PyPI package** — Enable `pip install zero-employee-orchestrator` for easy install (+0.2)
3. **Type safety** — Eliminate `any` type usage in frontend (+0.1)
4. **Integration tests** — Add API integration tests with real HTTP requests (+0.1)

### To reach 8.0/10:
5. **Meta-orchestration depth** — Runtime CrewAI/LangGraph integration beyond config (+0.4)
6. **E2E user journey test** — Automated test from setup → task creation → execution → result (+0.2)
7. **Docker Compose one-liner** — `docker compose up` for instant start (+0.2)
8. **CLI slash commands** — Direct execution instead of LLM delegation (+0.2)

**Latest evaluation**: `docs/dev/EVALUATION_v0.1.6.md` — 6.4/10 (2026-04-07)
