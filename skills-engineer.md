# Skills Engineer — Defining Persona-Driven Skills for Zero-Employee Orchestrator

> **Role:** Skills Engineer
> **Scope:** Design, author, and validate `SKILL.md` manifests in ZEO's skill
> registry so every Skill ships with a tightly-bounded persona, not a loose
> instruction list.
> **Counterpart:** [Construction Engineer](construction-engineer.md) — designs
> the orchestration topology that calls these Skills.

---

## 1. Why ZEO Needs Explicit Personas

Zero-Employee Orchestrator delegates work to many AI frameworks at once —
CrewAI, AutoGen, LangChain, Dify, g4f, Ollama, OpenRouter, and the
21+ model families in `model_catalog.json`. Without a persona, each model
falls back to its own defaults, so the *same* Skill produces a different
voice, different risk tolerance, and different output shape every run.

A ZEO Skill is not a single prompt — it is a **persona contract** the
orchestration layer uses to:

1. Lock the tone, vocabulary, and forbidden behaviors of the AI that runs it
2. Make the Judge layer's cross-model verification deterministic
3. Make approval-gate decisions reproducible across model swaps
4. Feed the audit trail with meaningful "who said what" attributions
5. Keep the CLAUDE.md / operator profile small by externalizing role details

Skills live under `skills/builtin/<slug>/SKILL.md` and are registered
through `app/services/skill_service.py`. Every one of them must pass the
checks in this document before being merged.

---

## 2. Anatomy of a ZEO `SKILL.md`

Every `SKILL.md` under `skills/builtin/` or imported from an external
source must include these six sections — in this order:

```markdown
# <Skill Name>

## Persona
One-paragraph, first-person definition of who this Skill acts as.
Example: "You are ZEO's Incident Responder. You triage production
alerts, propose low-risk mitigations, and always escalate destructive
actions to the approval gate."

## Inputs
- `task_id` (string, required)
- `severity` (enum: low | medium | high | critical)
- ...

## Outputs
- Structured JSON matching the Skill's declared schema
- Audit entry (auto-recorded by the orchestrator)

## Tone & Style Rules
- Writing voice, vocabulary floor/ceiling, language locale
- Formatting conventions (markdown, JSON, YAML, prose)

## Forbidden Actions
- Explicit list of things the persona will refuse, e.g.
  "never rm -rf", "never call an external API without an approval token",
  "never generate credentials"

## Escalation Policy
- Exact conditions that trigger `approval_gate.py`
- Exact conditions that trigger `autonomy_boundary.py`
- Exact conditions that trip the kill-switch
```

This is the *only* format the `ensure_system_skills()` bootstrapper
accepts as canonical. Any deviation becomes tech debt that the Skills
Engineer has to clean up before the next release.

---

## 3. Writing Personas That Actually Hold

Personas that "say the right thing" but still drift are worse than no
persona at all, because they give a false sense of safety. A ZEO persona
holds only when it is:

### 3.1 Concrete
Bad: "Write professional content."
Good: "Write for a Japanese mid-size B2B SaaS buyer. Use polite
Japanese (です・ます) by default, allow one casual sentence per ten
paragraphs, never use emoji, never use katakana loanwords when a kanji
equivalent exists."

### 3.2 Negative-biased
List forbidden behaviors before allowed ones. LLMs latch onto
prohibitions more reliably than goals. Every ZEO Skill needs at least
five explicit "do not" clauses.

### 3.3 Source-anchored
Reference the exact file the persona is allowed to touch.
Example: "You may read `docs/dev/DESIGN.md` but must never edit it.
Edits to design docs are reserved for the Construction Engineer."

### 3.4 Model-independent
The persona must produce the same output whether the Judge layer
routes the call to Claude Opus 4.6, GPT-5, Gemini 2.5, Qwen 3, or a
local Ollama model. Write rules that assume the weakest model in the
catalog — it still has to honor them.

### 3.5 Audit-friendly
Every forbidden action must have a machine-parseable tag so that
`audit/logger.py` can count how often the persona refused something.
Example: `<!-- audit:refuse=external_api_unapproved -->`

---

## 4. Skill Separation: One File Per Responsibility

ZEO ships 11 built-in Skills (6 system + 5 domain). The rule is:

> **One Skill = one responsibility = one persona.**

Never bundle two responsibilities. Instead, compose. If a business
workflow needs planning plus writing plus review, the Construction
Engineer wires three Skills together in a DAG — the Skills Engineer
does not merge them into a super-skill.

```
skills/builtin/
├── system/
│   ├── approval-gate/SKILL.md         # mandatory, cannot be disabled
│   ├── audit-logger/SKILL.md          # mandatory
│   ├── security-review/SKILL.md       # mandatory
│   ├── kill-switch/SKILL.md           # mandatory
│   ├── autonomy-dial/SKILL.md         # mandatory
│   └── cost-guard/SKILL.md            # mandatory
└── domain/
    ├── incident-responder/SKILL.md    # toggleable
    ├── knowledge-curator/SKILL.md     # toggleable
    ├── release-writer/SKILL.md        # toggleable
    ├── marketing-copy/SKILL.md        # toggleable
    └── data-analyst/SKILL.md          # toggleable
```

System Skills are immutable at runtime. Only the Skills Engineer can
open a PR to change them, and every such PR must include a diff of the
rendered persona *and* an updated `docs/dev/EVALUATION_v*.md` section.

---

## 5. Shared Policy Layer

Domain Skills must not duplicate security rules. They reference the
shared policy Skills instead:

```markdown
## Forbidden Actions
- Any action listed in `skills/builtin/system/security-review/SKILL.md`
- Any spend above the current Cost Guard budget
  (defer to `skills/builtin/system/cost-guard/SKILL.md`)
```

This keeps CLAUDE.md under 200 lines and makes security audits
surgical: one PR, one file, one review.

---

## 6. Validation Checklist Before Merge

A `SKILL.md` is ready to ship only if all the boxes below are checked:

- [ ] All six canonical sections present, in order
- [ ] Persona paragraph ≤ 4 sentences
- [ ] At least 5 items in "Forbidden Actions"
- [ ] Escalation policy cites `approval_gate.py` / `autonomy_boundary.py`
      /`kill_switch` by name
- [ ] Audit tags (`audit:*`) present for every refusal branch
- [ ] No direct model IDs (only family IDs like `anthropic/claude-opus`)
- [ ] `wrap_external_data()` is referenced anywhere external text is
      consumed
- [ ] PII Guard check is referenced anywhere user input is consumed
- [ ] Unit test exists in `apps/api/app/tests/test_registry.py`
- [ ] `./scripts/bump-version.sh` was run if the Skill is new
- [ ] `docs/dev/EVALUATION_v*.md` updated
- [ ] All translated READMEs (`docs/ja-JP/`, `docs/zh-CN/`, …) mention
      the Skill if it changes the surface area

A Skills Engineer who skips any checkbox is, by definition, shipping
tech debt. Don't.

---

## 7. Why This Model Works

ZEO's Judge layer (`apps/api/app/orchestration/judge.py`, ~848 lines)
runs cross-model verification: two different models score the same
output and disagree only when the persona is ambiguous. A tight
`SKILL.md` cuts Judge disagreement rates by 30-60% in internal
measurements, which:

1. Reduces LLM spend (fewer re-runs)
2. Shortens the DAG critical path
3. Makes the audit log useful in incident reviews
4. Lets the Autonomy Dial push beyond level 3 without losing trust

The Skills Engineer is the person who makes all four of those true.

---

## 8. Handoff to the Construction Engineer

Once a `SKILL.md` is merged, the Skills Engineer's job ends and the
[Construction Engineer](construction-engineer.md) picks it up:

- The Skills Engineer guarantees *what the Skill says and refuses*
- The Construction Engineer guarantees *when the Skill runs, on which
  model, behind which approval gate, and how failures are rolled back*

Neither role reaches into the other. That separation is what lets ZEO
ship dozens of Skills without a CLAUDE.md explosion.

---

**Checklist summary (print and pin):**

```
[ ] Persona ≤ 4 sentences
[ ] ≥ 5 forbidden actions
[ ] Escalation → approval_gate.py / autonomy_boundary.py / kill_switch
[ ] Audit tags
[ ] Family model IDs only
[ ] wrap_external_data + PII check
[ ] Tests + bump-version.sh + EVALUATION.md + translated READMEs
```
