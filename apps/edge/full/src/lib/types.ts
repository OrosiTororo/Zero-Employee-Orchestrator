/* ------------------------------------------------------------------ */
/*  Shared TypeScript type definitions for ZEO Full Workers            */
/* ------------------------------------------------------------------ */

/** Cloudflare Workers environment bindings */
export type Bindings = {
  DB: D1Database;
  JWT_SECRET: string;
  CORS_ORIGINS?: string;
};

/** Variables attached to the Hono context */
export type Variables = {
  userId: string;
  companyId: string;
};

/** Standard API success response */
export interface ApiResponse<T = unknown> {
  data: T;
}

/** Standard API error response */
export interface ApiError {
  error: string;
  detail?: string;
}

/** Pagination parameters */
export interface PaginationParams {
  limit: number;
  offset: number;
}

/** JWT payload */
export interface JwtPayload {
  sub: string; // user id
  email: string;
  role: string;
  iat: number;
  exp: number;
}

/** User row from D1 */
export interface UserRow {
  id: string;
  email: string | null;
  display_name: string;
  role: string;
  status: string;
  auth_provider: string | null;
  password_hash: string | null;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

/** Company row from D1 */
export interface CompanyRow {
  id: string;
  slug: string;
  name: string;
  mission: string | null;
  description: string | null;
  status: string;
  settings_json: string | null;
  created_at: string;
  updated_at: string;
}

/** Ticket row from D1 */
export interface TicketRow {
  id: string;
  company_id: string;
  project_id: string | null;
  goal_id: string | null;
  ticket_no: number;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  source_type: string;
  requester_user_id: string | null;
  assignee_agent_id: string | null;
  created_at: string;
  updated_at: string;
}

/** Agent row from D1 */
export interface AgentRow {
  id: string;
  company_id: string;
  name: string;
  title: string;
  description: string | null;
  agent_type: string;
  runtime_type: string;
  provider_name: string;
  model_name: string | null;
  status: string;
  autonomy_level: string;
  can_delegate: number;
  can_write_external: number;
  can_spend_budget: number;
  config_json: string | null;
  created_at: string;
  updated_at: string;
}

/** Task row from D1 */
export interface TaskRow {
  id: string;
  company_id: string;
  ticket_id: string;
  plan_id: string;
  title: string;
  description: string | null;
  sequence_no: number;
  status: string;
  task_type: string;
  requires_approval: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

/** Approval request row from D1 */
export interface ApprovalRow {
  id: string;
  company_id: string;
  target_type: string;
  target_id: string;
  requested_by_type: string;
  status: string;
  reason: string | null;
  risk_level: string;
  requested_at: string;
  decided_at: string | null;
}

/** Spec row from D1 */
export interface SpecRow {
  id: string;
  company_id: string;
  ticket_id: string;
  version_no: number;
  status: string;
  objective: string | null;
  constraints_json: string | null;
  acceptance_criteria_json: string | null;
  risk_notes: string | null;
  created_by_type: string;
  created_by_user_id: string | null;
  created_by_agent_id: string | null;
  created_at: string;
  updated_at: string;
}

/** Plan row from D1 */
export interface PlanRow {
  id: string;
  company_id: string;
  ticket_id: string;
  spec_id: string;
  version_no: number;
  status: string;
  summary: string | null;
  estimated_cost_usd: number | null;
  estimated_minutes: number | null;
  approval_required: number;
  risk_level: string;
  plan_json: string | null;
  created_by_agent_id: string | null;
  created_at: string;
  updated_at: string;
}

/** Audit log row from D1 */
export interface AuditLogRow {
  id: string;
  company_id: string;
  actor_type: string;
  actor_user_id: string | null;
  actor_agent_id: string | null;
  event_type: string;
  target_type: string;
  target_id: string | null;
  ticket_id: string | null;
  task_id: string | null;
  details_json: string | null;
  trace_id: string | null;
  created_at: string;
}

/** Project row from D1 */
export interface ProjectRow {
  id: string;
  company_id: string;
  name: string;
  goal: string | null;
  description: string | null;
  priority: string;
  status: string;
  owner_user_id: string | null;
  owner_agent_id: string | null;
  due_at: string | null;
  created_at: string;
  updated_at: string;
}

/** Artifact row from D1 */
export interface ArtifactRow {
  id: string;
  company_id: string;
  ticket_id: string | null;
  task_id: string | null;
  artifact_type: string;
  title: string;
  storage_type: string;
  path_or_uri: string | null;
  mime_type: string | null;
  version_no: number;
  summary: string | null;
  meta_json: string | null;
  created_by_type: string;
  created_by_user_id: string | null;
  created_by_agent_id: string | null;
  created_at: string;
}

/** Skill row from D1 */
export interface SkillRow {
  id: string;
  company_id: string | null;
  slug: string;
  name: string;
  skill_type: string;
  description: string | null;
  version: string;
  status: string;
  source_type: string;
  source_uri: string | null;
  manifest_json: string | null;
  policy_json: string | null;
  created_at: string;
  updated_at: string;
}

/** Plugin row from D1 */
export interface PluginRow {
  id: string;
  company_id: string | null;
  slug: string;
  name: string;
  description: string | null;
  version: string;
  status: string;
  manifest_json: string | null;
  created_at: string;
  updated_at: string;
}

/** Extension row from D1 */
export interface ExtensionRow {
  id: string;
  company_id: string | null;
  slug: string;
  name: string;
  description: string | null;
  version: string;
  status: string;
  manifest_json: string | null;
  created_at: string;
  updated_at: string;
}

/** Budget policy row from D1 */
export interface BudgetPolicyRow {
  id: string;
  company_id: string;
  name: string;
  scope_type: string;
  scope_id: string | null;
  period_type: string;
  limit_usd: number;
  warn_threshold_pct: number;
  stop_threshold_pct: number;
  created_at: string;
  updated_at: string;
}

/** Cost ledger row from D1 */
export interface CostLedgerRow {
  id: string;
  company_id: string;
  scope_type: string;
  scope_id: string;
  provider_name: string;
  model_name: string | null;
  cost_usd: number;
  tokens_input: number | null;
  tokens_output: number | null;
  occurred_at: string;
  run_type: string;
  run_id: string | null;
  created_at: string;
}

/** Heartbeat policy row from D1 */
export interface HeartbeatPolicyRow {
  id: string;
  company_id: string;
  name: string;
  cron_expr: string;
  timezone: string;
  enabled: number;
  jitter_seconds: number;
  max_parallel_runs: number;
  created_at: string;
  updated_at: string;
}

/** Heartbeat run row from D1 */
export interface HeartbeatRunRow {
  id: string;
  company_id: string;
  policy_id: string;
  agent_id: string | null;
  team_id: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  summary: string | null;
  created_at: string;
}

/** Review row from D1 */
export interface ReviewRow {
  id: string;
  company_id: string;
  ticket_id: string | null;
  task_id: string | null;
  reviewer_type: string;
  reviewer_user_id: string | null;
  reviewer_agent_id: string | null;
  status: string;
  score: number | null;
  comments_markdown: string | null;
  created_at: string;
}
