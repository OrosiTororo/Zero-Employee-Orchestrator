/* ------------------------------------------------------------------ */
/*  Shared TypeScript type definitions for ZEO Full Workers            */
/* ------------------------------------------------------------------ */

/** Cloudflare Workers environment bindings */
export type Bindings = {
  DB: D1Database;
  JWT_SECRET: string;
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
