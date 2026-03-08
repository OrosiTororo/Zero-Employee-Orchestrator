-- ============================================================
-- Zero-Employee Orchestrator — D1 (SQLite) DDL
-- Converted from SQLAlchemy ORM models
-- ============================================================

-- Users & Auth
CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  email         TEXT UNIQUE,
  display_name  TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'user',
  status        TEXT NOT NULL DEFAULT 'active',
  auth_provider TEXT,
  password_hash TEXT,
  last_login_at TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Companies
CREATE TABLE IF NOT EXISTS companies (
  id            TEXT PRIMARY KEY,
  slug          TEXT NOT NULL UNIQUE,
  name          TEXT NOT NULL,
  mission       TEXT,
  description   TEXT,
  status        TEXT NOT NULL DEFAULT 'active',
  settings_json TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug);

-- Company Members
CREATE TABLE IF NOT EXISTS company_members (
  id           TEXT PRIMARY KEY,
  company_id   TEXT NOT NULL REFERENCES companies(id),
  user_id      TEXT NOT NULL REFERENCES users(id),
  company_role TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'active',
  joined_at    TEXT NOT NULL DEFAULT (datetime('now')),
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cm_company ON company_members(company_id);
CREATE INDEX IF NOT EXISTS idx_cm_user    ON company_members(user_id);

-- Departments
CREATE TABLE IF NOT EXISTS departments (
  id                   TEXT PRIMARY KEY,
  company_id           TEXT NOT NULL REFERENCES companies(id),
  parent_department_id TEXT REFERENCES departments(id),
  name                 TEXT NOT NULL,
  code                 TEXT NOT NULL,
  description          TEXT,
  created_at           TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_dept_company ON departments(company_id);

-- Teams
CREATE TABLE IF NOT EXISTS teams (
  id                  TEXT PRIMARY KEY,
  company_id          TEXT NOT NULL REFERENCES companies(id),
  department_id       TEXT REFERENCES departments(id),
  name                TEXT NOT NULL,
  purpose             TEXT,
  lead_agent_id       TEXT,
  status              TEXT NOT NULL DEFAULT 'active',
  heartbeat_policy_id TEXT,
  budget_policy_id    TEXT,
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_teams_company ON teams(company_id);

-- Agents
CREATE TABLE IF NOT EXISTS agents (
  id                  TEXT PRIMARY KEY,
  company_id          TEXT NOT NULL REFERENCES companies(id),
  team_id             TEXT REFERENCES teams(id),
  manager_agent_id    TEXT REFERENCES agents(id),
  name                TEXT NOT NULL,
  title               TEXT NOT NULL,
  description         TEXT,
  agent_type          TEXT NOT NULL,
  runtime_type        TEXT NOT NULL,
  provider_name       TEXT NOT NULL,
  model_name          TEXT,
  status              TEXT NOT NULL DEFAULT 'provisioning',
  autonomy_level      TEXT NOT NULL,
  can_delegate        INTEGER NOT NULL DEFAULT 0,
  can_write_external  INTEGER NOT NULL DEFAULT 0,
  can_spend_budget    INTEGER NOT NULL DEFAULT 0,
  heartbeat_policy_id TEXT,
  budget_policy_id    TEXT,
  config_json         TEXT,
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_agents_company ON agents(company_id);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
  id             TEXT PRIMARY KEY,
  company_id     TEXT NOT NULL REFERENCES companies(id),
  name           TEXT NOT NULL,
  goal           TEXT,
  description    TEXT,
  priority       TEXT NOT NULL,
  status         TEXT NOT NULL,
  owner_user_id  TEXT REFERENCES users(id),
  owner_agent_id TEXT REFERENCES agents(id),
  due_at         TEXT,
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_projects_company ON projects(company_id);

-- Goals
CREATE TABLE IF NOT EXISTS goals (
  id             TEXT PRIMARY KEY,
  company_id     TEXT NOT NULL REFERENCES companies(id),
  parent_goal_id TEXT REFERENCES goals(id),
  project_id     TEXT REFERENCES projects(id),
  title          TEXT NOT NULL,
  description    TEXT,
  goal_level     TEXT NOT NULL,
  status         TEXT NOT NULL,
  metric_name    TEXT,
  metric_target  REAL,
  metric_unit    TEXT,
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_goals_company ON goals(company_id);

-- Tickets
CREATE TABLE IF NOT EXISTS tickets (
  id                 TEXT PRIMARY KEY,
  company_id         TEXT NOT NULL REFERENCES companies(id),
  project_id         TEXT REFERENCES projects(id),
  goal_id            TEXT REFERENCES goals(id),
  ticket_no          INTEGER NOT NULL,
  title              TEXT NOT NULL,
  description        TEXT,
  priority           TEXT NOT NULL DEFAULT 'medium',
  status             TEXT NOT NULL DEFAULT 'draft',
  source_type        TEXT NOT NULL,
  requester_user_id  TEXT REFERENCES users(id),
  requester_agent_id TEXT REFERENCES agents(id),
  assignee_user_id   TEXT REFERENCES users(id),
  assignee_agent_id  TEXT REFERENCES agents(id),
  parent_ticket_id   TEXT REFERENCES tickets(id),
  current_spec_id    TEXT,
  current_plan_id    TEXT,
  due_at             TEXT,
  approved_at        TEXT,
  closed_at          TEXT,
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(company_id, ticket_no)
);
CREATE INDEX IF NOT EXISTS idx_tickets_company ON tickets(company_id);

-- Ticket Threads
CREATE TABLE IF NOT EXISTS ticket_threads (
  id              TEXT PRIMARY KEY,
  company_id      TEXT NOT NULL REFERENCES companies(id),
  ticket_id       TEXT NOT NULL REFERENCES tickets(id),
  author_type     TEXT NOT NULL,
  author_user_id  TEXT REFERENCES users(id),
  author_agent_id TEXT REFERENCES agents(id),
  message_type    TEXT NOT NULL,
  body_markdown   TEXT,
  meta_json       TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tt_company ON ticket_threads(company_id);
CREATE INDEX IF NOT EXISTS idx_tt_ticket  ON ticket_threads(ticket_id);

-- Specs
CREATE TABLE IF NOT EXISTS specs (
  id                       TEXT PRIMARY KEY,
  company_id               TEXT NOT NULL REFERENCES companies(id),
  ticket_id                TEXT NOT NULL REFERENCES tickets(id),
  version_no               INTEGER NOT NULL,
  status                   TEXT NOT NULL,
  objective                TEXT,
  constraints_json         TEXT,
  acceptance_criteria_json TEXT,
  risk_notes               TEXT,
  created_by_type          TEXT NOT NULL,
  created_by_user_id       TEXT REFERENCES users(id),
  created_by_agent_id      TEXT REFERENCES agents(id),
  created_at               TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at               TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_specs_company ON specs(company_id);
CREATE INDEX IF NOT EXISTS idx_specs_ticket  ON specs(ticket_id);

-- Plans
CREATE TABLE IF NOT EXISTS plans (
  id                  TEXT PRIMARY KEY,
  company_id          TEXT NOT NULL REFERENCES companies(id),
  ticket_id           TEXT NOT NULL REFERENCES tickets(id),
  spec_id             TEXT NOT NULL REFERENCES specs(id),
  version_no          INTEGER NOT NULL,
  status              TEXT NOT NULL,
  summary             TEXT,
  estimated_cost_usd  REAL,
  estimated_minutes   INTEGER,
  approval_required   INTEGER NOT NULL DEFAULT 0,
  risk_level          TEXT NOT NULL,
  plan_json           TEXT,
  created_by_agent_id TEXT REFERENCES agents(id),
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_plans_company ON plans(company_id);
CREATE INDEX IF NOT EXISTS idx_plans_ticket  ON plans(ticket_id);
CREATE INDEX IF NOT EXISTS idx_plans_spec    ON plans(spec_id);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
  id                TEXT PRIMARY KEY,
  company_id        TEXT NOT NULL REFERENCES companies(id),
  ticket_id         TEXT NOT NULL REFERENCES tickets(id),
  plan_id           TEXT NOT NULL REFERENCES plans(id),
  parent_task_id    TEXT REFERENCES tasks(id),
  assignee_agent_id TEXT REFERENCES agents(id),
  title             TEXT NOT NULL,
  description       TEXT,
  sequence_no       INTEGER NOT NULL,
  status            TEXT NOT NULL DEFAULT 'pending',
  task_type         TEXT NOT NULL,
  requires_approval INTEGER NOT NULL DEFAULT 0,
  depends_on_json   TEXT,
  verification_json TEXT,
  started_at        TEXT,
  completed_at      TEXT,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tasks_company ON tasks(company_id);
CREATE INDEX IF NOT EXISTS idx_tasks_ticket  ON tasks(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tasks_plan    ON tasks(plan_id);

-- Task Runs
CREATE TABLE IF NOT EXISTS task_runs (
  id                  TEXT PRIMARY KEY,
  company_id          TEXT NOT NULL REFERENCES companies(id),
  task_id             TEXT NOT NULL REFERENCES tasks(id),
  run_no              INTEGER NOT NULL,
  executor_agent_id   TEXT REFERENCES agents(id),
  status              TEXT NOT NULL,
  started_at          TEXT NOT NULL,
  finished_at         TEXT,
  error_code          TEXT,
  error_message       TEXT,
  input_snapshot_json TEXT,
  output_snapshot_json TEXT,
  created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_taskruns_company ON task_runs(company_id);
CREATE INDEX IF NOT EXISTS idx_taskruns_task    ON task_runs(task_id);

-- Artifacts
CREATE TABLE IF NOT EXISTS artifacts (
  id                  TEXT PRIMARY KEY,
  company_id          TEXT NOT NULL REFERENCES companies(id),
  ticket_id           TEXT REFERENCES tickets(id),
  task_id             TEXT REFERENCES tasks(id),
  artifact_type       TEXT NOT NULL,
  title               TEXT NOT NULL,
  storage_type        TEXT NOT NULL,
  path_or_uri         TEXT,
  mime_type           TEXT,
  version_no          INTEGER NOT NULL DEFAULT 1,
  summary             TEXT,
  meta_json           TEXT,
  created_by_type     TEXT NOT NULL,
  created_by_user_id  TEXT REFERENCES users(id),
  created_by_agent_id TEXT REFERENCES agents(id),
  created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_artifacts_company ON artifacts(company_id);

-- Approval Requests
CREATE TABLE IF NOT EXISTS approval_requests (
  id                    TEXT PRIMARY KEY,
  company_id            TEXT NOT NULL REFERENCES companies(id),
  target_type           TEXT NOT NULL,
  target_id             TEXT NOT NULL,
  requested_by_type     TEXT NOT NULL,
  requested_by_user_id  TEXT REFERENCES users(id),
  requested_by_agent_id TEXT REFERENCES agents(id),
  approver_user_id      TEXT REFERENCES users(id),
  status                TEXT NOT NULL DEFAULT 'requested',
  reason                TEXT,
  risk_level            TEXT NOT NULL,
  payload_json          TEXT,
  requested_at          TEXT NOT NULL DEFAULT (datetime('now')),
  decided_at            TEXT
);
CREATE INDEX IF NOT EXISTS idx_approvals_company ON approval_requests(company_id);

-- Reviews
CREATE TABLE IF NOT EXISTS reviews (
  id                TEXT PRIMARY KEY,
  company_id        TEXT NOT NULL REFERENCES companies(id),
  ticket_id         TEXT REFERENCES tickets(id),
  task_id           TEXT REFERENCES tasks(id),
  reviewer_type     TEXT NOT NULL,
  reviewer_user_id  TEXT REFERENCES users(id),
  reviewer_agent_id TEXT REFERENCES agents(id),
  status            TEXT NOT NULL,
  score             REAL,
  comments_markdown TEXT,
  created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_reviews_company ON reviews(company_id);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
  id              TEXT PRIMARY KEY,
  company_id      TEXT NOT NULL REFERENCES companies(id),
  actor_type      TEXT NOT NULL,
  actor_user_id   TEXT REFERENCES users(id),
  actor_agent_id  TEXT REFERENCES agents(id),
  event_type      TEXT NOT NULL,
  target_type     TEXT NOT NULL,
  target_id       TEXT,
  ticket_id       TEXT REFERENCES tickets(id),
  task_id         TEXT REFERENCES tasks(id),
  details_json    TEXT,
  trace_id        TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_audit_company ON audit_logs(company_id);

-- Budget Policies
CREATE TABLE IF NOT EXISTS budget_policies (
  id                 TEXT PRIMARY KEY,
  company_id         TEXT NOT NULL REFERENCES companies(id),
  name               TEXT NOT NULL,
  scope_type         TEXT NOT NULL,
  scope_id           TEXT,
  period_type        TEXT NOT NULL,
  limit_usd          REAL NOT NULL,
  warn_threshold_pct INTEGER NOT NULL DEFAULT 80,
  stop_threshold_pct INTEGER NOT NULL DEFAULT 100,
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_budget_company ON budget_policies(company_id);

-- Cost Ledger
CREATE TABLE IF NOT EXISTS cost_ledger (
  id            TEXT PRIMARY KEY,
  company_id    TEXT NOT NULL REFERENCES companies(id),
  scope_type    TEXT NOT NULL,
  scope_id      TEXT NOT NULL,
  provider_name TEXT NOT NULL,
  model_name    TEXT,
  cost_usd      REAL NOT NULL,
  tokens_input  INTEGER,
  tokens_output INTEGER,
  occurred_at   TEXT NOT NULL,
  run_type      TEXT NOT NULL,
  run_id        TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cost_company ON cost_ledger(company_id);

-- Heartbeat Policies
CREATE TABLE IF NOT EXISTS heartbeat_policies (
  id                TEXT PRIMARY KEY,
  company_id        TEXT NOT NULL REFERENCES companies(id),
  name              TEXT NOT NULL,
  cron_expr         TEXT NOT NULL,
  timezone          TEXT NOT NULL DEFAULT 'UTC',
  enabled           INTEGER NOT NULL DEFAULT 1,
  jitter_seconds    INTEGER NOT NULL DEFAULT 0,
  max_parallel_runs INTEGER NOT NULL DEFAULT 1,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_hbp_company ON heartbeat_policies(company_id);

-- Heartbeat Runs
CREATE TABLE IF NOT EXISTS heartbeat_runs (
  id          TEXT PRIMARY KEY,
  company_id  TEXT NOT NULL REFERENCES companies(id),
  policy_id   TEXT NOT NULL REFERENCES heartbeat_policies(id),
  agent_id    TEXT REFERENCES agents(id),
  team_id     TEXT REFERENCES teams(id),
  status      TEXT NOT NULL,
  started_at  TEXT NOT NULL,
  finished_at TEXT,
  summary     TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_hbr_company ON heartbeat_runs(company_id);
CREATE INDEX IF NOT EXISTS idx_hbr_policy  ON heartbeat_runs(policy_id);

-- Skills
CREATE TABLE IF NOT EXISTS skills (
  id            TEXT PRIMARY KEY,
  company_id    TEXT REFERENCES companies(id),
  slug          TEXT NOT NULL,
  name          TEXT NOT NULL,
  skill_type    TEXT NOT NULL,
  description   TEXT,
  version       TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'experimental',
  source_type   TEXT NOT NULL,
  source_uri    TEXT,
  manifest_json TEXT,
  policy_json   TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_skills_slug ON skills(slug);

-- Plugins
CREATE TABLE IF NOT EXISTS plugins (
  id            TEXT PRIMARY KEY,
  company_id    TEXT REFERENCES companies(id),
  slug          TEXT NOT NULL,
  name          TEXT NOT NULL,
  description   TEXT,
  version       TEXT NOT NULL,
  status        TEXT NOT NULL,
  manifest_json TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_plugins_slug ON plugins(slug);

-- Extensions
CREATE TABLE IF NOT EXISTS extensions (
  id            TEXT PRIMARY KEY,
  company_id    TEXT REFERENCES companies(id),
  slug          TEXT NOT NULL,
  name          TEXT NOT NULL,
  description   TEXT,
  version       TEXT NOT NULL,
  status        TEXT NOT NULL,
  manifest_json TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_extensions_slug ON extensions(slug);

-- Policy Packs
CREATE TABLE IF NOT EXISTS policy_packs (
  id         TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  name       TEXT NOT NULL,
  version    TEXT NOT NULL,
  status     TEXT NOT NULL,
  rules_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pp_company ON policy_packs(company_id);

-- Secret Refs
CREATE TABLE IF NOT EXISTS secret_refs (
  id                   TEXT PRIMARY KEY,
  company_id           TEXT NOT NULL REFERENCES companies(id),
  name                 TEXT NOT NULL,
  secret_type          TEXT NOT NULL,
  provider             TEXT NOT NULL,
  masked_value         TEXT NOT NULL,
  expires_at           TEXT,
  rotation_policy_json TEXT,
  created_at           TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sr_company ON secret_refs(company_id);

-- Tool Connections
CREATE TABLE IF NOT EXISTS tool_connections (
  id              TEXT PRIMARY KEY,
  company_id      TEXT NOT NULL REFERENCES companies(id),
  name            TEXT NOT NULL,
  connection_type TEXT NOT NULL,
  status          TEXT NOT NULL,
  auth_type       TEXT NOT NULL,
  secret_ref      TEXT,
  config_json     TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tc_company ON tool_connections(company_id);

-- Tool Call Traces
CREATE TABLE IF NOT EXISTS tool_call_traces (
  id            TEXT PRIMARY KEY,
  company_id    TEXT NOT NULL REFERENCES companies(id),
  task_run_id   TEXT REFERENCES task_runs(id),
  agent_id      TEXT REFERENCES agents(id),
  tool_name     TEXT NOT NULL,
  request_json  TEXT,
  response_json TEXT,
  status        TEXT NOT NULL,
  latency_ms    INTEGER,
  started_at    TEXT NOT NULL,
  finished_at   TEXT,
  trace_id      TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tct_company ON tool_call_traces(company_id);
