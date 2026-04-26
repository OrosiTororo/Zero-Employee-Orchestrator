# Claude Design Brief — Zero-Employee Orchestrator (ZEO)

> Claude Design (Anthropic Labs, 2026-04-17 公開 / Claude Opus 4.7 搭載) で
> ZEO の全 27 画面を High Fidelity プロトタイプとして段階的に生成するための
> 作業手順・DESIGN.md・プロンプト集。

---

## 0. 前提と目的

- **対象**: Zero-Employee Orchestrator v0.1.7 / Tauri v2 + React + Tailwind
- **ゴール**: VSCode/Zed 系の暗色 UI と Cowork 系ナビを踏襲した
  High Fidelity プロトタイプ (HTML/CSS/React) を Claude Design で 27 画面分生成し、
  最終的に Claude Code に "Send to Claude Code" で連携する。
- **必要なもの**: Claude Pro / Max / Team / Enterprise いずれかの有料プラン
  (Claude Design は Research Preview)。
- **成果物**: `apps/desktop/ui/src/pages/` の 27 画面に対応する
  Claude Design プロジェクト群 + 生成された React コンポーネント zip。

---

## 1. Claude Design で行う操作 (チェックリスト)

下記の順番で操作してください。**各段階の終わりに保存** し、
プロジェクトを使い回せるよう **同じデザインシステム** を共有します。

### Phase A — 初期セットアップ (1 回だけ)

1. **<https://claude.ai/design> にアクセス**しログイン。
2. ダッシュボード左上メニューから **"Connect codebase"** を選択。
3. ZEO の GitHub リポジトリ URL を貼り付け、GitHub 認証を許可。
   - Claude が `apps/desktop/ui/src/index.css` (デザイントークン) と
     `apps/desktop/ui/src/shared/ui/Layout.tsx` (レイアウト骨格) を読み取る。
4. **新規プロジェクトを作成** — 以下のとおり設定:
   - Name: `ZEO Design System Bootstrap`
   - Design system: **None** (この最初のプロジェクトで生成する)
   - Type: **Prototype**
   - Fidelity: **High Fidelity**
5. チャット欄に本ドキュメントの **§3 DESIGN.md** 全文を貼り付けて送信。
   生成された design system を **"Save as design system"** で保存
   (名前は `ZEO Design System` に固定)。

### Phase B — 画面ごとのプロジェクト作成 (×27)

下記を **画面 1 つにつき 1 プロジェクト** 繰り返します。

1. ダッシュボードで **"+ New project"**。
2. 入力:
   - Name: `ZEO — <画面名>` (例 `ZEO — 02 Dashboard`)
   - Design system: **`ZEO Design System`** (ドロップダウンから選択)
   - Type: **Prototype** (タブの中央)
   - Fidelity: **High Fidelity**
3. **メインプロンプト** (チャット欄): 「§5 メインプロンプト テンプレート」を貼る。
4. **"Give the agent more detail on what to implement (optional)"**:
   「§6 各画面の実装詳細プロンプト」から該当画面のブロックを貼る。
5. Send → 45–90 秒で初稿がキャンバスに出現。

### Phase C — イテレーション

- **チャット返信**: 全体的な変更 (例 "make the sidebar denser, 40px wide")
- **インラインコメント**: キャンバス上の要素を選んで局所修正
- **Tweak スライダー**: タイポスケール / spacing / アクセント色の微調整
  (※ DESIGN.md に固定値があるので大きく動かさない)
- 確定したら **"Send to Claude Code"** をクリックし、生成された
  プロンプト + zip を `apps/desktop/ui/src/pages/<画面>/` に取り込む。

### Phase D — レビュー & マージ

- 各画面で生成された React コードを既存の `Layout.tsx` の
  `<Outlet />` 内に組み込む。
- i18n 文字列は `shared/i18n/locales/*.json` の 6 言語キーに置換。
- `npx tsc --noEmit && npx vite build` で破綻が無いことを確認。

---

## 2. 補足: なぜ DESIGN.md を最初に作るか

VoltAgent/awesome-claude-design の標準フォーマットでは DESIGN.md が
**Token (値) / Rule (規約) / Rationale (理由)** を 1 ファイルに集約する単一情報源です。
Claude Design はプロジェクト作成時にこのファイルを design system として読み込み、
以降のすべてのプロンプトに自動適用します。これを最初に固定することで、
27 画面間でフォントサイズ・色・余白・シャドウがブレません。

---

## 3. DESIGN.md (Claude Design に貼り付ける本文)

> 以下を **そのまま** Phase A の最初のチャットに貼り付けてください。
> 値は `apps/desktop/ui/src/index.css` から実測したもの。

````markdown
# ZEO Design System (v0.1.7)

ZEO is the **Zero-Employee Orchestrator** — a meta-orchestrator that wraps
other AI frameworks (CrewAI, AutoGen, LangChain, Dify, n8n, Zapier) under a
unified human-approval, audit, and security layer. The UI must communicate
**control, transparency, and trust** — not playfulness, not editorial warmth.

## 1. Visual Theme & Atmosphere

- IDE-grade desktop tool. Reference: VSCode, Zed, Linear, Raycast.
- Density: **compact** (11–14 px body, 22 px status bar, 30 px title bar).
- Mood: serious, technical, instrument-panel. Quiet by default; status colors
  earn attention only when the system needs the operator.
- Motion: 120–280 ms cubic-bezier(0.4, 0, 0.2, 1). Respect
  `prefers-reduced-motion`.

## 2. Color Palette & Roles (CSS variables)

Dark theme is the default. Light + High-Contrast must be supported.

```css
:root, [data-theme="dark"] {
  --bg-base:       #1E1E1E;   /* page */
  --bg-surface:    #252526;   /* cards, sidebar background */
  --bg-raised:     #2D2D2D;   /* modals, popovers */
  --bg-overlay:    #303031;
  --bg-input:      #3C3C3C;
  --bg-hover:      #2A2D2E;
  --bg-active:     #37373D;
  --bg-nav-bar:    #333333;   /* left activity bar */
  --bg-titlebar:   #323233;   /* 30px top bar */
  --bg-statusbar:  #007ACC;   /* 22px bottom bar — accent blue */

  --border:        #3E3E42;
  --border-focus:  #007ACC;

  --text-primary:  #D4D4D4;
  --text-secondary:#BBBBBB;
  --text-muted:    #6E7681;

  --accent:        #007ACC;   /* single accent — VSCode blue */
  --accent-hover:  #1177BB;
  --accent-fg:     #FFFFFF;
  --accent-subtle: rgba(0,122,204,0.08);

  --success: #56BA9F;   /* Zed green */
  --error:   #E5484D;
  --warning: #F3D768;
  --info:    #0090FF;
}
[data-theme="light"]          { --bg-base:#FFFFFF; --bg-surface:#F3F3F3; --text-primary:#1E1E1E; /* …same accent #007ACC */ }
[data-theme="high-contrast"]  { --bg-base:#000000; --border:#00FFFF; /* WCAG AAA */ }
```

**Rules**

- **Single accent**: only `--accent` (#007ACC). No purple gradients,
  no rainbow, no warm cream.
- Status colors are **semantic only** — never decorative.
- Backgrounds escalate `base → surface → raised → overlay → input` for
  z-axis hierarchy. No drop shadow on flat surfaces.

## 3. Typography

```css
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
             "Helvetica Neue", Arial, sans-serif;
--font-mono: "SF Mono", "Fira Code", "Cascadia Code", "JetBrains Mono",
             Menlo, monospace;

--text-xs:   11px;   /* status bar, badges */
--text-sm:   12px;   /* secondary labels */
--text-base: 13px;   /* body */
--text-md:   14px;   /* section heading */
--text-lg:   16px;
--text-xl:   20px;   /* page title */
--text-2xl:  24px;   /* hero numbers */
```

- Do NOT use Inter, Roboto-only, Geist, or any "AI-default" font.
  System font stack is intentional — it matches IDE chrome.
- Numerals in dashboards use `font-variant-numeric: tabular-nums`.
- Headings: `font-weight: 600`, never 700+.

## 4. Component Stylings

### Button
- Solid: `bg:--accent`, `fg:--accent-fg`, hover `--accent-hover`.
  Radius 5 px, padding `6px 12px`, `font-size:13px`.
- Ghost: transparent, border `1px --border`, hover `bg:--bg-hover`.
- Destructive: `bg:--error`, `fg:#fff` — used **only** for irreversible ops.
- Disabled: `opacity:0.5`, no hover.

### Input
- `bg:--bg-input`, border `1px --border`, focus `border:--border-focus`.
- Height 28 px (compact). Radius 3 px.
- Label: 11 px uppercase, `--text-muted`, 4 px below input.

### Card
- `bg:--bg-surface`, border `1px --border`, radius 8 px.
- Inner padding 16 px. No shadow.
- Header: 14 px / `--text-secondary` / uppercase tracker `letter-spacing:0.04em`.

### Nav (left activity bar — 48 px wide)
- `bg:--bg-nav-bar`, items 48×48 px, icon 24 px.
- Active: 2 px left border `--accent`, `bg:--bg-active`, icon at full
  `--text-primary`.
- Tooltip on hover (right side, popup shadow).

### Sidebar (secondary, 240 px, optional per route)
- `bg:--bg-surface`. Section headers 11 px uppercase.
  Progressive disclosure: **Manage** and **Extend** sections collapsed by default.

### Status bar (22 px, full width, accent background)
- `bg:--bg-statusbar` (#007ACC), `fg:--statusbar-fg` (#FFFFFF), 12 px.
- Slots: `[Connection] [Dispatch counter] … [Autonomy Dial] [Lang] [Mode]`.

### Modal / Command Palette
- `bg:--bg-raised`, `box-shadow:--shadow-modal`, radius 12 px.
- Command Palette: 640 px wide, top-anchored 80 px from top, search input
  14 px, results 13 px with right-aligned shortcut hints.

### Badge
- 11 px, padding `2px 6px`, radius 3 px, uppercase tracker.
- Risk levels (used in Approval Gate):
  `LOW=--success`, `MEDIUM=--warning`, `HIGH=--error`, `CRITICAL=#fff on --error`.

## 5. Layout Principles

- **Spacing scale (px)**: `2 / 4 / 8 / 12 / 16 / 24 / 32 / 48`.
  Pick from this scale, never `7px` or `15px`.
- App frame: `[30px Titlebar] / [48px Nav | content] / [22px Statusbar]`.
  Total chrome is ~100 px so content area maximises.
- Page content: max 1200 px wide, 24 px gutters. Multi-column allowed.
- Tables: 32 px row height, sticky header, monospace numerals.

## 6. Depth & Elevation

```css
--shadow-popup: 0 4px 12px rgba(0,0,0,0.3);   /* tooltip, dropdown */
--shadow-modal: 0 8px 24px rgba(0,0,0,0.4);   /* dialog, palette */
```

- Flat by default. Shadow ONLY on popovers and modals.
- For "raised" cards use background step-up, not shadow.

## 7. Do's and Don'ts

**Do**
- Treat the UI as an **instrument panel**: everything has a state, a
  trustworthy label, and a way to drill in.
- Show **risk level** on any operation that could touch real systems.
- Show **cost estimate** before LLM-bound actions.
- Localize every string (en, ja, zh-CN, zh-TW, ko, pt-BR, tr).

**Don't**
- ❌ Warm cream / off-white backgrounds, terracotta accents, serif display.
- ❌ Purple → blue gradients, "AI-glass" glassmorphism, neon glows.
- ❌ Inter/Roboto-only typography, emoji as iconography.
- ❌ Hidden destructive buttons. Always require an explicit confirm step
  for high-risk ops (Approval Gate is mandatory).
- ❌ Decorative illustrations on dashboards. Data first.

## 8. Responsive Behavior

- Primary target: desktop ≥ 1280 × 800 (Tauri window).
- Down to 1024 px: nav stays 48 px, content reflows to single column.
- Below 1024 px: read-only graceful degrade (this is a desktop tool, not mobile).

## 9. Agent Prompt Guide (for every screen prompt)

When generating any screen, the agent must:

1. Use `data-theme="dark"` as default and produce light + high-contrast variants.
2. Pull every color/spacing/font value from the CSS variables above —
   no raw hex outside this file.
3. Render the standard chrome (Titlebar 30 px, Nav 48 px, Statusbar 22 px)
   on every full-page screen unless the prompt says "panel only".
4. Surface **Autonomy Dial** in the status bar with 4 tiers
   `Observe → Assist → Semi-Auto → Autonomous`.
5. Show real loading, empty, error states — not just the happy path.
6. Output **React (TSX) + Tailwind utility classes** that read from these
   CSS variables (e.g. `className="bg-[var(--bg-surface)]"`).
7. Add `aria-label` on every icon-only button. Keyboard shortcuts visible.
````

---

## 4. プロンプト構造の説明

Claude Design の "+ New project" には 2 つのプロンプト入力欄があります:

| 欄 | 役割 | 本ドキュメントで使うもの |
|----|------|--------------------------|
| **メインプロンプト** (チャット欄) | 何を作るかの一文要約 | §5 メインプロンプト テンプレート |
| **Give the agent more detail on what to implement (optional)** | 実装詳細・受け入れ条件・データ構造 | §6 各画面の詳細プロンプト |

メインプロンプトは「画面の目的」を 2–3 行で、詳細欄は「セクション構成・
状態・受け入れ条件」を箇条書きで指示するのがベストです (Anthropic Cookbook
"Prompting for frontend aesthetics" の推奨どおり)。

---

## 5. メインプロンプト テンプレート (チャット欄に貼る)

すべての画面で **共通のヘッダ** を使い、最後の 2 行だけ画面ごとに差し替えます。

```text
You are designing a screen for ZEO (Zero-Employee Orchestrator), an
IDE-grade desktop meta-orchestrator. Apply the active "ZEO Design System"
strictly — pull every value from its CSS variables; do not invent new tokens.

Render the standard app chrome (30px Titlebar, 48px left Nav with active
"<route>" item, 22px Statusbar with Autonomy Dial / Dispatch counter /
Language / Mode) around the screen unless I say "panel only".

Output React (TSX) + Tailwind classes that read CSS variables such as
`bg-[var(--bg-surface)]`. Show loading, empty, and error states.
Localize labels via i18next keys (en + ja shown).

Screen: <SCREEN NAME>
Goal: <ONE SENTENCE — what the user accomplishes here>
```

最後の 2 行 (`Screen:` と `Goal:`) のみ画面ごとに差し替えてください。
詳細は **必ず** "Give the agent more detail on what to implement (optional)" 欄に
入れること (チャット欄に詰め込むと初稿が崩れやすい)。

---

## 6. "Give the agent more detail on what to implement (optional)" 入力内容

> 各画面のブロックを **そのまま** Claude Design の Optional 欄に貼り付け。
> ヘッダの `### Screen 02 — Dashboard` の行は含めず、**本文のみコピー**。

### Screen 01 — App Shell / Layout (最初に作る)

```text
Goal: Establish the persistent chrome reused by every other ZEO screen.

Layout:
- 30px Titlebar
  - Left: workflow icon (Lucide "Workflow") + "ZEO" wordmark in 13px.
  - Center: current document/route breadcrumb in 12px muted.
  - Right: window controls placeholder (Tauri provides real ones).
- 48px Activity Nav (left, vertical):
  - Core (always visible): Dashboard, Tickets, Secretary, Brainstorm,
    Dispatch, Monitor.
  - Manage (collapsible group): Org Chart, Templates, Crews, Approvals,
    Artifacts, Heartbeats, Costs, Audit.
  - Extend (collapsible group): Skills, Plugins, Extensions, Marketplace.
  - Bottom pinned: Operator Profile, Permissions, Settings.
  - Active item: 2px left border in --accent, --bg-active background,
    icon at full --text-primary. Tooltip on hover (right side).
- Main content: --bg-base, scrollable, no padding (page owns its padding).
- 22px Statusbar:
  - Left: Connection dot + "Connected" / "OK".
  - Center: Dispatch icon + count (e.g. "3 running").
  - Right: Autonomy Dial (4 tiers Observe→Assist→Semi-Auto→Autonomous,
    click cycles), Language code (EN/JA/...), Mode chip
    (Quality / Speed / Cost).

States:
- Disconnected: connection dot --error, label "Reconnecting…".
- High-risk autonomy (Autonomous): subtle red ring around dial.
- Reduced-motion: no transitions on nav expand.

Acceptance:
- Works at 1024×768 minimum (nav never collapses below 48px).
- Every icon-only control has aria-label.
- Keyboard: Ctrl+K opens Command Palette overlay (designed separately
  but reserve a focus-trap slot).
```

### Screen 02 — Dashboard (`/`)

```text
Goal: First view after login. Operator sees system pulse and can start a
ticket from natural language in one keystroke.

Sections (top to bottom, single column, max-width 1200px, 24px gutters):
1. Greeting strip — "Good evening, <Operator>. 3 tickets in flight."
   13px, --text-secondary. No avatar.
2. Quick-start chat input (hero, 56px tall):
   - Multiline textarea, placeholder "Describe what you need…
     (Cmd+Enter to dispatch)".
   - Right side: model badge (current default), cost estimate "~$0.04",
     primary button "Dispatch".
3. 4 Quick-action chips below the input: Research / Report / Automate /
   Analyze. Clicking pre-fills the textarea with a templated prompt.
4. Stats row — 4 Cards (16px gap):
   - Active Tickets (number, sparkline last 7d).
   - Pending Approvals (number, --warning if > 0, click → /approvals).
   - Agents Online (number / total, --success dot).
   - Spent today (USD, vs. budget bar).
5. "Recent Activity" feed (full width Card):
   - 32px rows. Columns: time | actor (👤 user / 🤖 agent name) |
     action | resource | status badge. Max 8 rows then "View audit →".

States:
- Empty (new user): replace stats with 1 onboarding Card linking to
  /setup.
- Error fetching stats: skeleton + retry inline.

Acceptance:
- Tab order: textarea → quick-actions → stats → activity.
- Numbers tabular-nums.
- No decorative illustrations.
```

### Screen 03 — Tickets List (`/tickets`)

```text
Goal: Triage queue for all work the operator has dispatched.

Layout: full-width data table inside a Card.
- Toolbar (top, 48px): search input (left, 280px), filters (Status: Open
  / In Progress / Awaiting Approval / Done / Failed; Priority; Assignee),
  right side "+ New Ticket" primary button.
- Table columns (sticky header, 32px rows):
  | Status dot | ID | Title | Skill / Crew | Owner | Updated | Cost | … |
- Status dot colors: open=--info, running=--accent, awaiting=--warning,
  done=--success, failed=--error.
- Row click → /tickets/:id. Right-click → context menu (Cancel, Re-run,
  Open in Monitor).
- Pagination: 50 / page, keyboard j/k navigates rows.

States: empty (illustration-free; CTA "Create your first ticket"),
loading skeleton (8 rows), error banner.
```

### Screen 04 — Ticket Detail (`/tickets/:id`)

```text
Goal: Single source of truth for one unit of work — spec, plan, execution,
artifacts.

Layout: 2-column.
- Left rail (320px): Ticket header (title editable inline, status badge,
  priority, owner, autonomy override). Below it, vertical tab list:
  Overview / Spec / Plan / Tasks / Artifacts / Timeline / Cost.
- Main: tab content.
  - Overview: 1-paragraph summary, 4 KPI tiles (tasks total / done / failed
    / cost), inline approval CTA if pending.
  - Spec: markdown editor (CodeMirror look) with diff toggle.
  - Plan: DAG visualisation — nodes are tasks, edges dependencies. Cost
    chip on each node. "Approve & Run" primary button.
  - Tasks: per-task accordion with logs, retry, skip.
  - Artifacts: file list + preview pane.
  - Timeline: vertical event log (same shape as Audit row).
  - Cost: bar chart by skill, table breakdown.

States: spec drafting, plan awaiting approval (banner --warning across
top), running (live log tail), completed (--success banner), failed
(--error with "Re-propose" button → calls /re-propose route).
```

### Screen 05 — Spec / Plan Review (deep-dive of Plan tab)

```text
Goal: Operator approves the agent's plan before any side-effect runs.
This is THE moment of human-in-the-loop trust.

Layout: 3-pane.
- Left (240px): task tree — collapsible. Each node shows risk badge
  (LOW/MED/HIGH/CRITICAL) and est. cost.
- Center: DAG canvas. Pan/zoom. Selected node highlighted with --accent
  ring. Edge labels show data passed (e.g. "spec.md").
- Right (320px): inspector for selected node — Skill name, Model,
  Prompt preview (truncated), Inputs, Outputs, Cost estimate, Risk
  rationale, Approval requirement.

Footer bar (sticky, 56px, --bg-raised):
- Left: total est. cost + duration ("~$1.20 · 4 min").
- Center: cross-model judge confidence ("Judge: 0.86, 2/3 agree").
- Right: ghost "Re-propose", primary "Approve & Run". Approve is
  disabled until all CRITICAL nodes have been individually acknowledged
  (checkbox in inspector).

States: re-propose loading (skeleton DAG with shimmer), divergent
judges (--warning banner "Models disagree — review before running").
```

### Screen 06 — Secretary (`/secretary`)

```text
Goal: AI assistant briefing — the operator's daily standup.

Layout: full-width chat-like column, max-width 800px centered.
- Header: "Secretary" + last-updated timestamp + refresh icon.
- Briefing Card (top): 4–6 bullet summary of overnight activity, citing
  ticket IDs as inline chips.
- Decision queue: list of "Decisions waiting on you" — each item is a
  question with quick reply buttons (Approve / Defer / Reject).
- Conversation thread below: standard chat bubbles (operator right,
  agent left), 13px, mono code blocks.
- Composer at bottom (sticky), 56px.

No avatars. Bubble background --bg-surface, code in --bg-input.
```

### Screen 07 — Brainstorm (`/brainstorm`)

```text
Goal: Freeform ideation canvas. Less structured than Tickets.

Layout: split.
- Left 60%: infinite canvas with sticky-note style cards (drag to
  reposition). Cards can be linked.
- Right 40%: chat with the brainstorming agent. Operator types a seed
  ("ways to reduce churn"), agent emits 8–12 idea cards onto the
  canvas. Operator promotes selected cards into a Ticket via toolbar
  button.

Toolbar (top, 40px): Mode switcher (Diverge / Converge / Cluster),
Export (md / png), "Promote selected to Ticket".
```

### Screen 08 — Dispatch (`/dispatch`)

```text
Goal: The background queue. Send-and-forget tasks with retries.

Layout: 2-column.
- Left (280px): filter rail (Status, Skill, Owner, Date range).
- Main: virtualised list of dispatched tasks (50 px rows so 1 line of
  context fits). Per row: status dot, task title, skill chip,
  progress bar (if running), elapsed/eta, retry count, cancel button.
- Top toolbar: "+ Quick dispatch" textarea, sort, refresh.

States: a row that's failed shows "Retry" + "View error" inline.
Stuck task (>5 min no heartbeat) gets --warning ring.
```

### Screen 09 — Monitor (`/monitor`)

```text
Goal: Live, low-latency view of agent execution. Operator-as-NOC.

Layout: dashboard-style grid (12-col).
- Top row: 4 KPI tiles (Active agents, Tasks/min, p95 latency, Failures last hour).
- Middle: live log stream (left 70%) — virtualised, monospace,
  color-coded levels (debug muted / info default / warn --warning /
  error --error). Filter chips above (level, skill, ticket).
- Right (30%): "Agents" panel — list of running workers with heartbeat
  pulses (animated dot). Click an agent → filter logs.
- Bottom: small Gantt-like ribbon of in-flight tasks (last 5 min).

States: paused (operator can pause auto-scroll), disconnected (banner +
last-seen), reduced-motion disables heartbeat pulse animation.
```

### Screen 10 — Org Chart (`/org-chart`)

```text
Goal: Visualise the AI workforce — which agents/crews exist, who reports
to whom, how delegation flows.

Layout: SVG tree, top-down.
- Root: "Operator" (the human user) — distinct shape, --accent border.
- Children: Department nodes (e.g. "Research", "Ops", "Finance") that
  expand to specialist agents.
- Leaf nodes: individual skills/agents with model badge underneath.
- Edges labeled with relationship (delegates / reviews / approves).

Side panel (right, 320px, opens on node click): role description, current
load, last 5 tasks, "Open in Crews" button.

Toolbar: zoom, fit, layout switch (Tree / Radial), export PNG.
States: loading skeleton tree, empty (CTA to create first crew).
```

### Screen 11 — Templates (`/templates`)

```text
Goal: Reusable workflow templates the operator can instantiate as a Ticket.

Layout: card grid (3 cols ≥1280px, responsive).
- Each card (240×180): icon, title, 2-line description, tag chips
  (e.g. "research", "weekly"), runs-count, est. cost range, primary
  "Instantiate" button.
- Toolbar: search, category filter, sort by Most-used / Newest, "+ New
  template" button (opens wizard).
- Empty state shows curated starter templates (read-only previews).

Detail (modal on card open): full markdown description, parameter list,
example output, "Instantiate with parameters →" CTA.
```

### Screen 12 — Crews (`/crews`)

```text
Goal: Multi-agent team configuration — define who collaborates on what.

Layout: 2-pane.
- Left (280px): list of crews. Each row: name, member count, last run,
  enabled toggle.
- Main: selected crew editor.
  - Header: name, description, "Run" primary, "Duplicate" ghost.
  - Members table: role | agent (skill+model) | autonomy level |
    actions. "+ Add member" inline.
  - Workflow: ordered list of steps with branching (drag to reorder).
  - Hand-off rules: matrix of who can ask whom.
  - Test panel (bottom): trial input, run dry-run, see traces.

States: unsaved changes banner, validation errors per row.
```

### Screen 13 — Approvals (`/approvals`)

```text
Goal: The Approval Gate inbox — every dangerous operation pauses here.
This screen IS the trust layer.

Layout: tabbed list.
- Tabs: Pending (badge with count, --warning if >0) / Approved / Rejected
  / All. Default Pending.
- Each row is a Card (full width, stacked):
  - Top: risk badge (LOW/MED/HIGH/CRITICAL with semantic color),
    operation name, requesting agent + ticket ID chip, requested-at.
  - Body: 2–3 line summary + "What will happen" expandable diff
    (file changes, API calls, money moved). Show actual values, not
    placeholders.
  - Footer: comment input (optional), ghost "Reject" (with reason
    required), primary "Approve". For CRITICAL: require typing
    "APPROVE" to enable the button.
- Bulk: select multiple LOW items → batch approve.

States: empty pending = "Nothing waiting on you." (--text-muted, no
illustration). Stale items (>1h) get --warning ring.
```

### Screen 14 — Artifacts (`/artifacts`)

```text
Goal: Browse all outputs the agents produced — specs, plans, reports,
generated files.

Layout: 2-pane file browser.
- Left (260px): tree by Ticket / Date. Filter by type (md, json, pdf,
  png, code).
- Main: preview pane.
  - Markdown rendered with monospace code blocks.
  - Images zoomable.
  - Code with syntax highlighting and "Copy / Open in editor".
- Toolbar: search, version dropdown (each artifact is versioned per
  re-run), download, share link.

States: large file (truncate with "Load full" CTA), binary (icon + size
+ download only).
```

### Screen 15 — Heartbeats (`/heartbeats`)

```text
Goal: Scheduled / recurring task management. Cron-with-context.

Layout: table + drawer.
- Toolbar: search, status filter, "+ New schedule" primary.
- Table columns: Enabled toggle | Name | Cron / interval | Skill or
  Crew | Last run (status dot) | Next run (relative + absolute) |
  Owner | actions (run-now, edit, delete).
- Row click → right drawer (480px) with full schedule edit form, last
  10 runs timeline, failure pattern detection.

States: a heartbeat that's failed N times in a row gets --error ring
and a "Disable & investigate" CTA.
```

### Screen 16 — Costs / Cost Guard (`/costs`)

```text
Goal: Budget overview and spending control. Operator must see where
money is going AND set hard caps.

Layout: 12-col grid.
- Top row (4 KPI tiles, 3-col each): Spend today, Spend this month,
  Budget remaining (progress bar inside tile), Avg cost per ticket.
- Middle: 30-day trend line chart (12 col), x=date, y=USD, two series
  (actual vs. budget line). Stacked area below the line breaking down
  by skill.
- Below: "Top spenders" table (skills sorted by cost) + "Top tickets"
  table side-by-side (6 col each).
- Right column floating Card: Budget policy editor — global cap, per-
  skill caps, alert thresholds, kill-switch toggle.

States: budget breached → red banner across the top with "Pause non-
critical agents" CTA. Forecasted breach (≥80% on day 20/30) → --warning
banner.
```

### Screen 17 — Audit (`/audit`)

```text
Goal: Tamper-evident execution log for compliance. Read-only.

Layout: full-width timeline table.
- Toolbar: date range picker (default last 24h), actor filter
  (User / Agent / System), category filter (auth / approval / model /
  file / network / billing), search.
- Table columns: Timestamp (UTC + local) | Actor (icon + name) |
  Action | Resource | Outcome (success/fail/denied) | Hash chip
  (truncated SHA, click to copy full).
- Row expand: full JSON event, prev-hash chain visualisation
  (chain integrity badge).
- Export: CSV / JSONL / signed bundle.

States: chain broken → --error banner "Audit chain integrity failure
at <ts>" (this is critical — must be impossible to dismiss).
```

### Screen 18 — Skills Registry (`/skills`)

```text
Goal: Browse, enable, configure installed Skills. 8 system skills are
non-disableable.

Layout: card grid (3 cols).
- Toolbar: tabs "All / System / Custom", search, "+ Create skill"
  primary, "Import from MCP" ghost.
- Card (240×200): icon, name, version, scope chip (System=locked /
  Domain=toggleable / Custom=user), 2-line description, model badge,
  enable toggle (disabled for System with lock icon + tooltip).
- Click card → /skills/:id.

States: failed manifest validation → card --error border + "View error".
HIGH-risk import warning blocks enable until acknowledged.
```

### Screen 19 — Skill Detail (`/skills/:id`)

```text
Goal: Inspect, test, and edit a single skill.

Layout: tabbed.
- Header: icon, name, version, scope, enable toggle, "Run" primary.
- Tabs: Definition / Prompts / Parameters / Permissions / Test / History.
- Definition: read-only manifest view (yaml/json) with copy.
- Prompts: system prompt + user prompt template (CodeMirror), jinja
  variables highlighted.
- Parameters: form schema editor with type / required / default.
- Permissions: file paths allowed (sandbox), network domains, approval
  requirement matrix.
- Test: input form (built from parameters) + "Run" → output panel with
  cost + duration + token count.
- History: last 50 invocations with status and links to tickets.

States: schema invalid → --error banner; system skill → all editable
fields disabled with lock icon.
```

### Screen 20 — Skill Create (`/skills/create`)

```text
Goal: Natural-language skill creation wizard. Generate manifest from
plain English, then refine.

Layout: 4-step stepper (top, 56px).
1. Describe — large textarea: "What should this skill do?" + examples.
2. Review — generated manifest shown side-by-side with operator's words
   highlighted as evidence.
3. Permissions — confirm sandbox paths, network domains, approval
   requirements. Risk score badge calculated by analyze_code_safety.
4. Test & Save — same Test panel as Skill Detail, then "Save".

CRITICAL UI: step 3 must show HIGH-risk items in --error and require
explicit "I take responsibility" checkbox before continuing.
```

### Screen 21 — Plugins (`/plugins`)

```text
Goal: Manage Plugins (bundles of skills + role packs).

Layout: same shape as Skills Registry but the card emphasises bundle
metadata.
- Card: plugin name, role pack icon (e.g. "AI CEO", "Knowledge Wiki"),
  skills-included count, dependencies list, enable toggle, configure CTA.
- Configure opens a drawer (right, 480px) with the plugin's settings
  schema rendered as a form.

Tabs: All / Role Packs (12 general + 6 role-based) / Custom.
Role Packs displayed first with a slightly larger card and a "ROLE" tag.
```

### Screen 22 — Extensions (`/extensions`)

```text
Goal: System-level integrations (themes, OAuth, MCP transports, IDE
adapters).

Layout: list (not grid — extensions tend to be longer-lived and fewer).
- Toolbar: search, category filter (Theme / Integration / Transport /
  Adapter), "+ Install from URL" ghost.
- Row (72px): icon, name, category chip, status (Active / Disabled /
  Update available with --info dot), last-updated, actions menu.
- Row click → drawer with full description, screenshots, config, logs,
  uninstall.

States: update available → --info pill on the row; failed health check
→ --error ring + auto-disable banner.
```

### Screen 23 — Marketplace (`/marketplace`)

```text
Goal: Discover community / public skills, plugins, extensions.

Layout: grid with rich metadata.
- Hero strip (top, 200px): rotating "Featured" carousel with 3 large
  cards.
- Filters (left rail 240px): Type (Skill/Plugin/Extension), Category,
  Verified-only, License, Cost (free / paid).
- Grid: card with author avatar, name, install count, rating
  (5-star display), price chip, "Install" button (or "Installed").
- Item detail page: README, screenshots carousel, manifest, reviews
  list, security analysis summary (analyze_code_safety result with
  risk score), "Install" / "Install with --force" (gated).

CRITICAL: HIGH-risk items show a red banner before install with the
specific findings, requiring "?force=true" semantics in the UI.
```

### Screen 24 — Operator Profile (`/operator-profile`)

```text
Goal: Cowork-style about-me + global instructions that bias agent behavior.

Layout: 2 tabs in a centered max-720px column.
- Tab "Profile": form fields — Display name, Role, Team, Industry,
  Responsibilities (chip input), Priorities (chip input), Work style
  (radio: collaborative / autonomous / mixed), Language (dropdown of 6),
  Timezone (auto-detected, editable). Save button bottom-right.
- Tab "Instructions": large markdown textarea for global natural-language
  instructions (e.g. "Always cite sources. Default to Japanese for
  internal docs."). Live char count, "Test impact" CTA that runs a
  sample prompt with vs. without the instructions diff.

States: unsaved changes indicator in tab label, save success toast.
```

### Screen 25 — Permissions (`/permissions`)

```text
Goal: Configure approval gates, autonomy boundaries, browser permission
tiers, and policy packs. Power-user surface.

Layout: 3 sections stacked, each a Card.

1. "Autonomy Boundary" — matrix:
   rows = operation categories (file write, network, payment, code
   exec, browser, model call, install package).
   cols = autonomy tiers (Observe / Assist / Semi-Auto / Autonomous).
   each cell = "Auto" / "Approve" / "Block" dropdown.

2. "Browser Permission Tiers" (10 levels):
   visualised as a horizontal ladder: Navigate < Click < Type < Submit
   < Login < Payment < ... Operator selects the highest tier that
   auto-passes; everything above requires approval. Show example
   actions per tier.

3. "Policy Packs": list of installed packs (e.g. "GDPR", "SOC2",
   "Internal-Sec"). Toggle to enable. Conflicts shown as --warning rows.

States: pending policy change requires re-confirmation when leaving
the page.
```

### Screen 26 — Settings (`/settings`)

```text
Goal: All other configuration. Use category-left-rail pattern.

Layout: left rail (200px) with categories, main pane content.
Categories: General / Appearance / Models & Providers / Connections /
Security / Telemetry / Advanced.

- General: language (6), timezone, default workspace dir, kill-switch.
- Appearance: theme (Dark / Light / High-Contrast radio with live
  preview tile), font size, density (Compact / Comfortable),
  reduced-motion toggle.
- Models & Providers: provider tabs (OpenRouter / Anthropic / Ollama /
  g4f / Gemini / OpenAI / etc.). Each tab: API key input (masked,
  test button → green check), default model dropdown (family ID like
  `anthropic/claude-opus`), max-tokens, fallback chain.
- Connections: 63 app integrations as a grid (icon + connect button),
  OAuth status per app.
- Security: PII guard sensitivity, prompt-guard mode (block/warn/off),
  sandbox roots editor, secret scanning toggle.
- Telemetry: usage data sharing toggle (default off, with full
  disclosure of what is sent).
- Advanced: feature flags table, raw config JSON (read-only).

States: connection test failure inline, masked keys reveal on click-and-
hold (for accessibility, a 1-second hold).
```

### Screen 27 — Login (`/login`) & Screen 28 — Setup (`/setup`)

```text
Goal: First-run onboarding. Build trust before any LLM call is made.

Login (centered card, 400px wide):
- Logo + "Zero-Employee Orchestrator" + tagline (1 line).
- Two primary actions: "Continue anonymously (local-only)" and
  "Sign in with provider". Below: provider buttons (GitHub / Google /
  SSO). Footer: privacy note (1 line).

Setup wizard (full-screen, 4 steps with progress bar):
1. Language — choose 1 of 6, preview live.
2. Provider — choose model provider; the page MUST emphasise that ZEO
   is free and that the operator pays the provider directly. Show
   3 zero-cost options first: g4f / Ollama (local) / OpenRouter
   (one key). API key input with test.
3. Operator profile — slim version of /operator-profile (just name,
   role, language).
4. First ticket — pre-filled example prompt the operator can dispatch
   to verify the full chain works. On success: "You're all set →"
   button to /.

States: step validation, skip-for-now ghost on each step, "Need help?"
link bottom-left.
```

### Screen 29 — Command Palette (overlay, Ctrl+K)

```text
Goal: Universal launcher. Designed as an OVERLAY, not a route.

Layout: centered modal, 640px wide, top 80px from window top.
- Search input (56px tall, 16px font, placeholder "Type a command or
  search…", with kbd hint "Ctrl+K" right side).
- Results list grouped by category:
  - Navigation (16 routes): icon + route label + path on the right.
  - Actions: New ticket, New skill, Instantiate template, Spawn crew,
    Toggle theme, Switch language, Approve all LOW.
  - Recent: last 5 used commands.
- Each row 36px, hover --bg-hover, selected --bg-active, right side
  shows shortcut chip if any.
- Empty query → recent + suggested. Type → fuzzy match across labels
  + keywords.
- Keyboard: ↑↓ navigate, Enter execute, Esc close, Tab cycles
  category groups.

This must be panel-only (no app chrome around it) when generated.
```

### Screen 30 — MCP Tools (`/mcp` — power-user view)

```text
Goal: Inspect and test the 14 built-in MCP tools, manage transport.

Layout: 2-pane.
- Left (280px): tool list grouped by category, search, transport
  status indicator (HTTP+JSON-RPC 2.0 / stdio). "+ Connect external
  MCP server" CTA.
- Main: selected tool detail.
  - Header: name, category, annotations (read-only / destructive /
    requires-approval badges).
  - Tabs: Schema (JSON-RPC 2.0 input/output) / Try it (form built
    from schema, "Call" → response panel with status / latency /
    raw JSON) / Logs (last 50 invocations).

States: server disconnected → --error banner with retry. External
server unverified → --warning + acknowledgement.
```

### Screen 31 — Knowledge Wiki (`/wiki`)

```text
Goal: Karpathy-style atomic-page wiki + Ralph pipeline UI for
ingest/query/lint/resync.

Layout: 3-pane.
- Left rail (240px): vault tree (folders → atomic pages). Toolbar at
  top with /ingest, /lint actions.
- Main: page viewer.
  - Markdown rendered, inline citations as chips (click → opens
    source).
  - Top bar: "Edit" / "View links" / "Open in editor".
- Right rail (320px): Query panel.
  - Input: question textarea + "Save answer to vault" toggle.
  - Output: answer with numbered citation chips that scroll-link to
    pages in the tree. Below: "Ralph pipeline" stepper showing the
    last run's stages — Inbox → Reduce → Reflect → Retrieve → Verify
    → Resync, each stage with status dot and elapsed time.

States: lint findings → --warning row in left tree with count
indicator; broken citation → --error chip in citation list.
```

---

## 7. 段階的配信計画 (27 画面の進め方)

一度に全画面を流すと品質がブレるので **5 ウェーブ** に分割します。
各ウェーブの最後に Claude Code 側で取り込み・型チェックまで通してから次へ。

| Wave | 画面 | 目的 | 受け入れ基準 |
|------|------|------|--------------|
| **0 — Foundation** | DESIGN.md + Screen 01 (App Shell) | デザインシステムと共通クロームを確定 | Tokens が CSS variable で出力。Nav/Statusbar が他画面の枠として再利用可能 |
| **1 — Core (5)** | 02 Dashboard / 03 Tickets / 04 Ticket Detail / 09 Monitor / 29 Command Palette | 操作の主動線 | Ctrl+K → Dashboard → Ticket → Monitor の往復が成立 |
| **2 — Trust (4)** | 05 Spec/Plan / 13 Approvals / 17 Audit / 16 Costs | 承認・監査・予算という ZEO の差別化 4 画面 | Risk バッジ・Approval Gate・Audit chain が目に見える |
| **3 — Workforce (6)** | 06 Secretary / 07 Brainstorm / 08 Dispatch / 10 Org Chart / 12 Crews / 11 Templates | 仕事の作り方・任せ方 | Operator → 1 ticket dispatch を Brainstorm から Templates まで通せる |
| **4 — Registry (5)** | 18 Skills / 19 Skill Detail / 20 Skill Create / 21 Plugins / 22 Extensions / 23 Marketplace | 拡張面 | System/Custom 区別、HIGH-risk gate 表現が一貫 |
| **5 — Settings & Onboarding (5)** | 24 Operator Profile / 25 Permissions / 26 Settings / 27 Login / 28 Setup / 14 Artifacts / 15 Heartbeats / 30 MCP / 31 Wiki | 残り全部 | 6 言語切替プレビュー、High-Contrast 確認 |

各ウェーブ着手時のフロー:

1. ダッシュボード "+ New project" → Phase B 手順。
2. 1 画面終わるごとに **"Send to Claude Code"** で zip 取得。
3. ローカルで `apps/desktop/ui/src/pages/<画面>/` に展開
   (既存ファイルがあれば diff レビュー、無ければ新規)。
4. ウェーブ末に `npx tsc --noEmit && npx vite build && pytest apps/api/app/tests/`
   を通し、緑になってから次のウェーブへ。

---

## 8. 共通の禁止事項 (全プロンプトに暗黙適用)

DESIGN.md §7 の Don't と重複しますが、繰り返し効くので Optional 欄の
**末尾** に毎回 1 行貼っても良い:

```text
Avoid: warm cream backgrounds, terracotta/amber accents, serif display
fonts, purple→blue gradients, glassmorphism, neon glows, Inter/Roboto-only
typography, decorative emoji as iconography, hidden destructive buttons.
```

これは Claude Opus 4.7 が dashboard 系で陥りがちな "editorial AI default"
を回避するための既知のテクニックです。

---

## 9. Claude Code への引き継ぎ用 README (各 zip に同梱推奨)

Claude Design が出力する zip を `apps/desktop/ui/src/pages/<screen>/` に
取り込む際、Claude Code 側に下記のメモを渡すと型エラーが減ります:

```text
Integrate the attached Claude Design export into ZEO at
apps/desktop/ui/src/pages/<route>/. Replace literal hex colors with
existing CSS variables from src/index.css. Replace inline strings with
i18next keys; add the new keys to all 6 locale files
(en, ja, zh-CN, zh-TW, ko, pt-BR, tr) — ja is authoritative for new
copy, others machine-translated then human-flagged. Wire the page into
src/app/router.tsx. Add it to the left Nav in src/shared/ui/Layout.tsx
under the correct group (Core / Manage / Extend / Bottom). Run
`npx tsc --noEmit && npx vite build` and fix until green.
```

---

## 10. 検証 (この計画が機能したかの判定)

- [ ] `claude.ai/design` で `ZEO Design System` がデザインシステムとして
      ドロップダウンに保存されている。
- [ ] Wave 0 完了後、Screen 01 の出力に `bg-[var(--bg-base)]` 等の
      CSS variable 参照が含まれている (生 hex でない)。
- [ ] Wave 2 完了後、`/approvals` の HIGH/CRITICAL カードに
      "type APPROVE to enable" UX が再現されている。
- [ ] Wave 5 完了後、`apps/desktop/ui` で
      `npx tsc --noEmit && npx vite build` が緑。
- [ ] 全画面で Dark / Light / High-Contrast の 3 テーマが切替可能。
- [ ] i18next の en/ja キーが揃い、`shared/i18n/locales/ja.json` で
      `npm run check:i18n` (もし存在) が通る。
- [ ] `pytest apps/api/app/tests/` が緑 (UI 変更が API 契約を壊していない)。

---

## 11. 参考リンク

- Anthropic Labs: <https://www.anthropic.com/news/claude-design-anthropic-labs>
- Get started with Claude Design (Help Center):
  <https://support.claude.com/en/articles/14604416-get-started-with-claude-design>
- Set up your design system in Claude Design:
  <https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design>
- Anthropic Cookbook — Prompting for frontend aesthetics:
  <https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics>
- VoltAgent / awesome-claude-design (DESIGN.md format):
  <https://github.com/VoltAgent/awesome-claude-design>
- ZEO 既存資料: `docs/dev/DESIGN.md`, `apps/desktop/ui/src/index.css`,
  `apps/desktop/ui/src/shared/ui/Layout.tsx`.
