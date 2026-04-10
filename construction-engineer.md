# Construction Engineer — Orchestration Topology for Zero-Employee Orchestrator

> **Role:** Construction Engineer
> **Scope:** Design the DAGs, approval gates, judge topology, and failure
> rollbacks that turn individual Skills into trustworthy ZEO workflows.
> **Counterpart:** [Skills Engineer](skills-engineer.md) — defines the
> persona contracts that the topologies call.

---

## 1. Why the Two Roles Are Separated

Zero-Employee Orchestrator's 9-layer architecture separates *what* an AI
says (a Skill) from *when, how, and under which guarantees it runs*
(a topology). Mixing the two is the single biggest source of drift in
multi-agent systems:

- When a Skill author also controls the DAG, they smuggle orchestration
  rules into the persona ("…and if the budget is low, switch to gpt-4o-mini").
  That rule belongs in `cost_guard.py`, not in a `SKILL.md`.
- When a DAG author also rewrites personas, they smuggle tone changes
  into topology ("…also say sorry if the user is upset"). That rule
  belongs in the Skills Engineer's review.

The Construction Engineer owns everything *outside* the persona: task
decomposition, model selection, approval placement, retry strategy,
cost ceilings, the Judge layer wiring, and the rollback path. The
Skills Engineer owns everything *inside* the persona.

Neither role edits the other's files without a review from the
counterpart.

---

## 2. Artifacts the Construction Engineer Owns

1. **DAG graphs** under `apps/api/app/orchestration/dag.py` and any
   per-workflow descriptor in `skills/builtin/<slug>/workflow.yaml`
2. **Judge topology** — which models verify which Skills, in
   `apps/api/app/orchestration/judge.py`
3. **Approval gate wiring** — which actions must stop at
   `policies/approval_gate.py` before proceeding
4. **Autonomy dial thresholds** — which level in
   `policies/autonomy_boundary.py` unlocks which branch
5. **Budget envelopes** — daily / hourly caps in
   `orchestration/cost_guard.py`
6. **Kill-switch hooks** — fast-halt predicates in
   `orchestration/execution_monitor.py`
7. **Rollback procedures** — structured recovery documented in the
   workflow descriptor (and tested in `tests/test_chaos_dag.py`)

The Construction Engineer never owns the persona text itself. Not
even one sentence.

---

## 3. The Topology Contract

Every ZEO workflow the Construction Engineer publishes must satisfy
this contract before it reaches `main`:

### 3.1 Deterministic decomposition
A workflow is a DAG of at most **7 nodes**. If a business goal needs
more than 7 nodes, it must be expressed as two workflows with an
explicit hand-off. This keeps the audit log readable and the Judge
layer's cross-verification tractable.

### 3.2 Two approval points maximum
Exactly **two** human approval points per workflow — one after
planning, one before irreversible side effects. Three or more
approvals teach users to click-through; zero approvals break the
auditability story. Two is the proven sweet spot.

### 3.3 Model independence
A workflow must execute on any of the families listed in
`providers/model_registry.py` — no hard-coded `anthropic/claude-opus`,
no assumption of a 200k context window. If a node needs a specific
capability (vision, tool calling, long context), declare the
capability in `workflow.yaml`, and let `llm_gateway.py` pick the
cheapest model that meets it.

### 3.4 Always-on Judge layer
Every Skill that writes data the user will trust must be scored by at
least two different model families via `orchestration/judge.py`.
Disagreements feed `orchestration/re_propose.py`. No Judge = no merge.

### 3.5 Chaos-tested rollbacks
Every destructive node must be covered by
`tests/test_chaos_dag.py`, which injects random failures and asserts
the rollback path leaves the system in a consistent state. If the
test does not exist, the PR is blocked.

### 3.6 Budget envelope
Every workflow declares its maximum spend per run in
`workflow.yaml`. `cost_guard.py` enforces it. Anything above the
envelope trips the kill-switch instead of quietly overspending.

---

## 4. The Design Conversation (Mirror of Japanese "Commander AI")

The Construction Engineer runs a scripted design conversation with
the stakeholder *before* touching `dag.py`. The conversation produces
a one-page topology sketch that is reviewed and signed off before any
implementation begins. This mirrors the "think outside, build inside"
split that keeps Claude Code and ZEO focused.

### 4.1 Questions the Construction Engineer always asks

1. *What's the business outcome — measurable, in one sentence?*
2. *What is the worst thing that can happen if this runs unchecked
   for a week?* (drives kill-switch + approval placement)
3. *Which Skills already exist that can be reused as-is?*
   (drives hand-off to Skills Engineer if a new persona is needed)
4. *What is the maximum cost per run we can accept today?*
   (drives `cost_guard` envelope)
5. *Which data sources feed the workflow, and are any of them
   untrusted?* (drives `wrap_external_data` placement)
6. *Who signs off on the first execution, and how are they notified?*
7. *How do we know this worked? What metric do we track?*
   (drives the evaluation entry in `docs/dev/EVALUATION_v*.md`)

### 4.2 The one-page topology sketch

```yaml
workflow: competitor-weekly-digest
owner: construction-engineer
version: 1
outcome: "Publish a ranked weekly competitor digest by 09:00 JST"
worst_case: "Publishes incorrect competitor data to all subscribers"

dag:
  - id: plan
    skill: planner
    model_requirements: [long_context, tool_calling]
    judge: [anthropic/claude-opus, openai/gpt-5]
    approval: human
  - id: fetch
    skill: web-harvester
    wrap_external_data: true
  - id: summarize
    skill: knowledge-curator
    judge: [anthropic/claude-opus, google/gemini-pro]
  - id: rank
    skill: data-analyst
  - id: render
    skill: release-writer
  - id: notify
    skill: notifier
    approval: human
    rollback: recall_notification

cost_guard:
  max_usd_per_run: 1.50
  max_tokens_per_run: 400_000

kill_switch:
  halt_if: "weekly_digest_failures_24h > 2"
```

The Construction Engineer commits this sketch to the PR alongside
the actual implementation. Reviewers diff the sketch against the
code and catch topology drift before merge.

---

## 5. Integration with ZEO's Layers

| ZEO layer | Construction Engineer's lever |
|---|---|
| Design Interview | Provides the template prompts for stakeholder questions |
| Task Orchestrator (DAG) | Owns `dag.py`, workflow YAMLs, node wiring |
| Skills | **Does not own** — consumes via registry slug |
| Judge | Owns `judge.py`, declares verifier model pairs |
| Re-Propose | Owns retry policy and max-attempt caps |
| State & Memory | Defines working-memory keys per node, eviction policy |
| Provider (LiteLLM) | Owns capability requirements; model picks auto-route |
| Skill Registry | Read-only consumer |
| Approval/Autonomy/Cost/Kill-Switch | Owns placement and thresholds |

Anything outside this list belongs to another role:

- Skill persona text → Skills Engineer
- New provider integrations → Providers Engineer (separate role)
- UI rendering → Frontend Engineer (separate role)

---

## 6. Why this separation cuts context bloat

ZEO workflows fail catastrophically when the design discussion and
the execution log land in the same agent context. The **planning**
phase needs long back-and-forth; the **execution** phase needs zero
back-and-forth. Putting them in the same window is like doing CAD on
the same desk where the welding happens.

The Construction Engineer builds the topology somewhere "cold" —
typically a design doc, a workflow YAML, or a Claude project — then
ships only the finalized DAG to the running ZEO orchestrator. The
orchestrator never sees the deliberation. The audit log shows the
final plan, not the debate that led to it.

This is exactly why ZEO separates the Design Interview layer (layer 2)
from the Task Orchestrator layer (layer 3). The Construction Engineer
owns the seam between them.

---

## 7. CC Architect Prompt — Drop-in Template

When using Claude Code, Cursor, Continue, or any MCP-aware client to
help design a ZEO workflow, load this persona into a *separate*
session — never the same one running ZEO. The prompt below is the
English / ZEO-specific evolution of the "CC 構築士" template and is
safe to copy into a project knowledge panel.

```markdown
You are "ZEO Construction Architect". Your job is to design
workflows for Zero-Employee Orchestrator (ZEO), not to implement them.
Operate strictly in planning mode.

ZEO artifacts you may produce
1. `workflow.yaml` — DAG, approvals, judge pairs, cost envelope,
   kill-switch predicate
2. `CLAUDE.md` addendum — runtime rules, ≤ 150 lines
3. `docs/dev/EVALUATION_v*.md` stub — how we'll measure success
4. A one-page topology sketch as defined in
   `construction-engineer.md` §4.2

Design principles
- Plan in a design space, execute in a runtime space — never the same.
- Delegate persona design to the Skills Engineer.
- Two approval points, at most 7 DAG nodes, always-on Judge layer.
- Cost envelope mandatory, kill-switch predicate mandatory.
- Every untrusted input goes through `wrap_external_data()`.
- Every user input goes through `pii_guard.py`.

Forbidden
1. Writing new `SKILL.md` persona text (that's the Skills Engineer).
2. Picking a specific model ID — only capability requirements.
3. Allowing more than two approval gates per workflow.
4. Bypassing Cost Guard or Kill Switch.
5. Implementing code — you produce *design artifacts only*, which
   the implementer (Claude Code, a human, or the ZEO self-improvement
   loop) then translates into source.

Design conversation
1. Ask the 7 questions from §4.1 of `construction-engineer.md`.
2. Draft the one-page topology sketch.
3. Score it (100 pts): consistency 20 / reproducibility 20 /
   controllability 25 / simplicity 15 / testability 20.
4. Iterate until ≥ 85.

Output
- Everything copy-pasteable.
- Line counts for every file produced.
- Flag any section where the human must decide before shipping.
```

The Construction Engineer pastes this prompt into their planning
environment, runs the conversation, signs off on the artifacts, and
only then opens a ZEO PR.

---

## 8. Handoff and Review Loop

1. Construction Engineer drafts the topology sketch (offline)
2. Skills Engineer confirms every referenced Skill exists and
   matches the forbidden-action list the workflow assumes
3. Construction Engineer opens the PR with:
   - The one-page sketch
   - The implementation diff
   - A chaos test for every destructive node
   - An `EVALUATION_v*.md` entry with a success metric
4. Two reviewers required (at least one Skills Engineer)
5. `./scripts/bump-version.sh` if the workflow is new
6. Translated READMEs updated if user-visible

That's the whole loop. Run it every time. Short-circuiting it is
how ZEO breaks.

---

**Pinned reminders:**

```
[ ] ≤ 7 DAG nodes
[ ] 2 approval points
[ ] Judge layer on every write
[ ] Chaos test on every destructive node
[ ] Cost envelope + kill-switch predicate
[ ] Capability-based model selection (no hard-coded IDs)
[ ] No persona edits — defer to Skills Engineer
[ ] Planning outside runtime — never the same context
```
