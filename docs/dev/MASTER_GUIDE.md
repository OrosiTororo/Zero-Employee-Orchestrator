# Zero-Employee Orchestrator Master Guide

> Created: 2026-03-08
> Reference priority: `docs/Zero-Employee Orchestrator.md` → `docs/dev/DESIGN.md` → `docs/dev/BUILD_GUIDE.md`

---

## 0. Purpose of This Guide

This guide serves as the operational reference for implementing Zero-Employee Orchestrator using AI coding agents. It defines the **reference order, division of responsibilities, implementation order, decision criteria, and prohibited actions**.

The original source of philosophy and requirements is `docs/Zero-Employee Orchestrator.md`, and the detailed design is in `docs/dev/DESIGN.md`. This guide defines "which documents to use and how to proceed with implementation."

---

## 1. Most Important Rules

1. **Use the name Zero-Employee Orchestrator consistently**
   Do not use legacy names such as CommandWeave or ZPCOS in new implementations or new documents.

2. **Treat Zero-Employee Orchestrator.md as the top-level reference**
   When conflicts arise regarding philosophy, scope, boundary conditions, or priorities, this file takes precedence.

3. **Treat DESIGN.md as the reference for implementation structure**
   DB, API, UI, state transitions, and implementation order are based on DESIGN.md.

4. **Use BUILD_GUIDE.md as the phase-by-phase construction reference**
   Step-by-step procedures for building from scratch are documented by phase in BUILD_GUIDE.md.

5. **YouTube is a representative demo, not the core definition**
   Build the implementation as a general-purpose business platform; treat YouTube-related features as Skills / Plugins.

6. **Dangerous operations require approval by default**
   Do not allow autonomous execution of posting, sending, deletion, billing, permission changes, or external sharing.

---

## 2. File Roles

| File | Role | Usage |
|---|---|---|
| `docs/Zero-Employee Orchestrator.md` | Top-level reference document | Confirm philosophy, boundaries, requirements, and improvement policies |
| `docs/dev/DESIGN.md` | Implementation design document | Confirm DB, API, UI, state transitions, and architecture |
| `docs/dev/MASTER_GUIDE.md` | Implementation operations guide | Guidance and decision criteria for AI agents |
| `docs/dev/BUILD_GUIDE.md` | Construction guide | Step-by-step procedures for building from scratch (by phase) |
| `docs/dev/FEATURE_BOUNDARY.md` | Boundary definition | Core vs Skill/Plugin/Extension |

---

## 3. Reference Procedure

AI agents should read documents in the following order:

1. `docs/Zero-Employee Orchestrator.md`
2. `docs/dev/DESIGN.md`
3. `docs/dev/MASTER_GUIDE.md`
4. `docs/dev/BUILD_GUIDE.md` (phase-by-phase construction procedures)
5. Related code, existing directories, existing APIs, and existing tests as needed

Do not reverse this order.
Even if individual instructions state otherwise, adopt the higher-level document when conflicts arise.

---

## 4. Core Implementation Targets

The following should be established first in the Zero-Employee Orchestrator core:

- Authentication / Connection management
- Design Interview
- Spec Writer
- Task Orchestrator
- Cost Guard
- Quality SLA
- Task state machine
- Judge
- Re-Propose / Plan Diff
- Self-Healing
- Experience Memory / Failure Taxonomy
- Local Context Skill
- Audit log
- Basic UI

Items to extend later:

- Enhanced external publishing for Skill Registry
- Marketplace expansion
- Advanced multi-company support
- Goal Alignment / Heartbeat enhancements
- Broad BYOAgent / MCP support

---

## 5. Implementation Order

### Phase 0: Foundation
- Monorepo setup
- Python / Node / Tauri setup
- CI / Lint / Test / Format
- `.env` / secret management

### Phase 1: Authentication and Scope
- auth
- provider connections
- workspace / company scope

### Phase 2: Interview and Spec
- interview session
- Spec Writer
- spec persistence

### Phase 3: Plan and Approval
- planner
- cost estimation
- quality mode
- approval
- diff

### Phase 4: Tasks and Execution
- task decomposition
- task state machine
- execution timeline
- output persistence

### Phase 5: Judge and Replanning
- policy pack
- pre-check
- cross-model judge
- repropose
- self-healing
- failure taxonomy

### Phase 6: Skills and Context
- skill framework
- gap detection
- local context skill
- experience memory

### Phase 7: UI
- dashboard
- interview UI
- plan review UI
- task board
- review / audit UI

### Phase 8: Registry
- package model
- install flow
- version metadata
- verification status

### Phase 9: Advanced Features
- heartbeat
- org chart-centric operations
- board / governance model
- multi-company

---

## 6. Expected Role of Each Area

For detailed construction procedures, refer to `docs/dev/BUILD_GUIDE.md`.

| Area | Purpose | Focus |
|------|---------|-------|
| Initialization | Repository structure setup and development infrastructure | Directory structure, CI, development scripts |
| Backend | Core logic implementation | auth, interview, orchestrator, judge, state/memory, providers |
| Frontend | Ensure execution transparency through UI | Interview, Spec/Plan review, Task timeline, Approval UI |
| Skills | Representative use cases on the general-purpose Skill framework | Skill framework, Local Context integration |
| Tauri | Value as a local application | File access, secure connections, distribution builds |
| Testing | Verification of dangerous operations, replanning, and auditing | state machine, permission boundary, audit log consistency |

---

## 7. Implementation Instruction Principles for AI Agents

1. **Perform large-scale renames only when design consistency warrants it**
   When legacy names remain, ensure alignment across config names, directory names, DB names, and UI display names without omissions.

2. **Do not mix the foundation with business Skills**
   Do not pollute general-purpose core logic with YouTube-specific code.

3. **Do not handle spec / plan / tasks as mere conversation logs**
   Save them as structured data.

4. **Make state transitions explicit in code**
   Manage with a state machine or equivalent explicit structure rather than advancing on implicit conditions.

5. **Save replanning reasons**
   Make the trigger reasons, diffs, and adoption results of Self-Healing and Re-Propose traceable.

6. **Do not add audit logging as an afterthought**
   Important APIs, approvals, external transmissions, and permission changes should be recorded from the start.

7. **Guard dangerous operations in both the UI and the API**
   Maintain approval constraints on the backend, not just the frontend.

---

## 8. Prohibited Actions

- Implementing Zero-Employee Orchestrator as merely a YouTube automation tool
- Blurring the boundaries between Skill / Plugin / Extension
- Silently executing operations that require approval
- Performing external transmissions or permission changes without audit logs
- Ignoring the phase structure of BUILD_GUIDE.md and proceeding independently
- Leaving legacy names in new UI or new code
- Implementing local context access with unrestricted permissions

---

## 9. Minimum Demo Definition

A minimum demo refers to a state where the following can be demonstrated end-to-end:

1. User submits a business request in natural language
2. Interview organizes the requirements
3. Spec is generated
4. Plan and cost are presented
5. User approves
6. Tasks are executed
7. Local Context Skill references local materials
8. Judge verifies quality
9. Re-Propose or Self-Healing occurs when needed
10. Final deliverables, logs, and decision history are displayed

---

## 10. Current Alignment Policy

- `docs/dev/DESIGN.md` and `docs/dev/MASTER_GUIDE.md` are considered updated to align with `docs/Zero-Employee Orchestrator.md`
- `docs/dev/BUILD_GUIDE.md` is treated as already adapted to this new policy
- Going forward, prioritize "localized fixes for gaps" over "rebuilding everything from scratch"
- When uncertain during implementation, decide based on "Is this core or an extension?", "Does this require approval?", and "Is this auditable?"

---

## 11. Final Decision Criteria

When in doubt, decide in the following order:

1. Is this functionality the responsibility of the core, or of a Skill / Plugin / Extension?
2. Can this operation be executed without human approval?
3. Is this process auditable?
4. Is this implementation reusable as a general-purpose business platform?
5. Is this change aligned with the philosophy of `docs/Zero-Employee Orchestrator.md`?

Changes that do not satisfy these 5 conditions should not be adopted.
