/**
 * 共通型定義 — Zero-Employee Orchestrator.md §38 のスキーマに基づく
 *
 * バックエンドの Pydantic スキーマに対応するフロントエンド型定義。
 * すべての主要エンティティの型を定義する。
 */

// ── 基本型 ─────────────────────────────────────────

export interface Timestamps {
  created_at: string
  updated_at: string
}

// ── 会社・組織 ──────────────────────────────────────

export interface Company extends Timestamps {
  id: string
  slug: string
  name: string
  mission?: string
  description?: string
  status: string
  settings_json?: Record<string, unknown>
}

export interface User extends Timestamps {
  id: string
  email: string
  display_name: string
  role: "owner" | "admin" | "user" | "auditor" | "developer"
  status: string
  auth_provider: string
  last_login_at?: string
}

export interface Department extends Timestamps {
  id: string
  company_id: string
  parent_department_id?: string
  name: string
  code: string
  description?: string
}

export interface Team extends Timestamps {
  id: string
  company_id: string
  department_id?: string
  name: string
  purpose?: string
  lead_agent_id?: string
  status: string
  heartbeat_policy_id?: string
  budget_policy_id?: string
}

// ── エージェント ─────────────────────────────────────

export type AgentStatus =
  | "provisioning"
  | "active"
  | "busy"
  | "paused"
  | "budget_blocked"
  | "policy_blocked"
  | "error"
  | "archived"

export type AutonomyLevel = "observe" | "assist" | "semi_auto" | "autonomous"

export interface Agent extends Timestamps {
  id: string
  company_id: string
  team_id?: string
  manager_agent_id?: string
  name: string
  title: string
  description?: string
  agent_type: string
  runtime_type: string
  provider_name: string
  model_name?: string
  status: AgentStatus
  autonomy_level: AutonomyLevel
  can_delegate: boolean
  can_write_external: boolean
  can_spend_budget: boolean
  heartbeat_policy_id?: string
  budget_policy_id?: string
  config_json?: Record<string, unknown>
}

// ── チケット ─────────────────────────────────────────

export type TicketStatus =
  | "draft"
  | "open"
  | "interviewing"
  | "planning"
  | "ready"
  | "in_progress"
  | "review"
  | "done"
  | "closed"
  | "rework"
  | "blocked"
  | "cancelled"
  | "reopened"

export interface Ticket extends Timestamps {
  id: string
  company_id: string
  project_id?: string
  goal_id?: string
  ticket_no: number
  title: string
  description?: string
  priority: "low" | "medium" | "high" | "critical"
  status: TicketStatus
  source_type: string
  requester_user_id?: string
  requester_agent_id?: string
  assignee_user_id?: string
  assignee_agent_id?: string
  parent_ticket_id?: string
  current_spec_id?: string
  current_plan_id?: string
  due_at?: string
  approved_at?: string
  closed_at?: string
}

export interface TicketThread {
  id: string
  company_id: string
  ticket_id: string
  author_type: "user" | "agent" | "system"
  author_user_id?: string
  author_agent_id?: string
  message_type: string
  body_markdown: string
  meta_json?: Record<string, unknown>
  created_at: string
}

// ── Spec / Plan / Task ──────────────────────────────

export interface Spec extends Timestamps {
  id: string
  company_id: string
  ticket_id: string
  version_no: number
  status: string
  objective: string
  constraints_json: { items: string[] }
  acceptance_criteria_json: { items: string[] }
  risk_notes?: string
  created_by_type: string
}

export interface Plan extends Timestamps {
  id: string
  company_id: string
  ticket_id: string
  spec_id: string
  version_no: number
  status: string
  summary: string
  estimated_cost_usd: number
  estimated_minutes: number
  approval_required: boolean
  risk_level: string
  plan_json: Record<string, unknown>
  created_by_agent_id?: string
}

export type TaskStatus =
  | "pending"
  | "ready"
  | "running"
  | "succeeded"
  | "failed"
  | "retrying"
  | "awaiting_approval"
  | "blocked"
  | "verified"
  | "rework_requested"
  | "cancelled"
  | "archived"

export interface Task extends Timestamps {
  id: string
  company_id: string
  ticket_id: string
  plan_id: string
  parent_task_id?: string
  assignee_agent_id?: string
  title: string
  description?: string
  sequence_no: number
  status: TaskStatus
  task_type: string
  requires_approval: boolean
  depends_on_json: Record<string, unknown>
  verification_json: Record<string, unknown>
  started_at?: string
  completed_at?: string
}

// ── 承認 ─────────────────────────────────────────────

export type ApprovalStatus =
  | "requested"
  | "approved"
  | "rejected"
  | "expired"
  | "cancelled"
  | "executed"
  | "superseded"

export interface ApprovalRequest {
  id: string
  company_id: string
  target_type: string
  target_id: string
  requested_by_type: string
  requested_by_user_id?: string
  requested_by_agent_id?: string
  approver_user_id?: string
  status: ApprovalStatus
  reason: string
  risk_level: string
  payload_json: Record<string, unknown>
  requested_at: string
  decided_at?: string
}

// ── 成果物 ───────────────────────────────────────────

export interface Artifact {
  id: string
  company_id: string
  ticket_id?: string
  task_id?: string
  artifact_type: string
  title: string
  storage_type: string
  path_or_uri: string
  mime_type: string
  version_no: number
  summary?: string
  meta_json?: Record<string, unknown>
  created_by_type: string
  created_at: string
}

// ── Heartbeat ────────────────────────────────────────

export interface HeartbeatPolicy extends Timestamps {
  id: string
  company_id: string
  name: string
  cron_expr: string
  timezone: string
  enabled: boolean
  jitter_seconds: number
  max_parallel_runs: number
}

export interface HeartbeatRun {
  id: string
  company_id: string
  policy_id: string
  agent_id?: string
  team_id?: string
  status: "queued" | "running" | "succeeded" | "partial" | "failed" | "skipped"
  started_at: string
  finished_at?: string
  summary?: string
  created_at: string
}

// ── 予算 ─────────────────────────────────────────────

export interface BudgetPolicy extends Timestamps {
  id: string
  company_id: string
  name: string
  scope_type: string
  scope_id?: string
  period_type: string
  limit_usd: number
  warn_threshold_pct: number
  stop_threshold_pct: number
}

export interface CostLedger {
  id: string
  company_id: string
  scope_type: string
  scope_id: string
  provider_name: string
  model_name?: string
  cost_usd: number
  tokens_input?: number
  tokens_output?: number
  occurred_at: string
  run_type: string
  run_id?: string
  created_at: string
}

// ── Skill / Plugin / Extension ───────────────────────

export type RegistryStatus = "verified" | "experimental" | "private" | "deprecated"

export interface Skill extends Timestamps {
  id: string
  company_id?: string
  slug: string
  name: string
  skill_type: string
  description: string
  version: string
  status: RegistryStatus
  source_type: string
  source_uri?: string
  manifest_json: Record<string, unknown>
  policy_json: Record<string, unknown>
}

export interface Plugin extends Timestamps {
  id: string
  company_id?: string
  slug: string
  name: string
  description: string
  version: string
  status: RegistryStatus
  manifest_json: Record<string, unknown>
}

export interface Extension extends Timestamps {
  id: string
  company_id?: string
  slug: string
  name: string
  description: string
  version: string
  status: RegistryStatus
  manifest_json: Record<string, unknown>
}

// ── 監査ログ ─────────────────────────────────────────

export interface AuditLog {
  id: string
  company_id: string
  actor_type: string
  actor_user_id?: string
  actor_agent_id?: string
  event_type: string
  target_type: string
  target_id?: string
  ticket_id?: string
  task_id?: string
  details_json: Record<string, unknown>
  trace_id?: string
  created_at: string
}

// ── 推論トレース（Observability） ─────────────────────

export type ReasoningStepType =
  | 'context_gathering'
  | 'knowledge_retrieval'
  | 'constraint_check'
  | 'option_enumeration'
  | 'option_evaluation'
  | 'risk_assessment'
  | 'decision'
  | 'delegation'
  | 'approval_request'
  | 'model_selection'
  | 'tool_selection'
  | 'prompt_construction'
  | 'execution'
  | 'quality_check'
  | 'judge_result'
  | 'self_correction'
  | 'error_analysis'
  | 'fallback_decision'
  | 'replan_trigger'

export type ReasoningConfidence = 'high' | 'medium' | 'low' | 'uncertain'

export interface ReasoningStep {
  step_id: string
  step_type: ReasoningStepType
  summary: string
  details: Record<string, unknown>
  confidence: ReasoningConfidence
  timestamp: number
  duration_ms: number
  parent_step_id?: string
}

export interface ReasoningTrace {
  trace_id: string
  task_id?: string
  agent_id?: string
  started_at: number
  finished_at?: number
  outcome?: string
  summary: string
  total_decisions: number
  total_fallbacks: number
  duration_ms?: number
  steps: ReasoningStep[]
}

// ── エージェント間通信 ────────────────────────────────

export type AgentMessageType =
  | 'delegation'
  | 'delegation_accept'
  | 'delegation_reject'
  | 'task_update'
  | 'artifact_handoff'
  | 'artifact_request'
  | 'feedback'
  | 'question'
  | 'answer'
  | 'instruction'
  | 'quality_review'
  | 'approval_request'
  | 'approval_response'
  | 'escalation'
  | 'error_report'
  | 'help_request'
  | 'broadcast'
  | 'heartbeat_ping'

export type MessagePriority = 'low' | 'normal' | 'high' | 'urgent'

export interface AgentMessage {
  message_id: string
  msg_type: AgentMessageType
  sender_agent_id?: string
  receiver_agent_id?: string
  task_id?: string
  content: string
  structured_data: Record<string, unknown>
  priority: MessagePriority
  in_reply_to?: string
  thread_id?: string
  timestamp: number
  acknowledged: boolean
}

export interface ConversationThread {
  thread_id: string
  task_id?: string
  participants: string[]
  subject: string
  message_count: number
  messages: AgentMessage[]
  started_at: number
  closed_at?: number
}

// ── 実行監視 ──────────────────────────────────────────

export interface ActiveExecution {
  task_id: string
  agent_id: string
  company_id: string
  started_at: number
  status: string
  progress_pct: number
  current_step: string
  trace_id?: string
  model_used?: string
  tokens_used: number
  cost_usd: number
  reasoning_steps: number
  elapsed_ms: number
}

export interface MonitorSummary {
  active_executions: number
  total_events: number
  recent_errors: number
  recent_escalations: number
  active_agents: string[]
}

export interface MonitorDashboard {
  summary: MonitorSummary
  active: ActiveExecution[]
  recent_events: Record<string, unknown>[]
}

// ── モデルレジストリ ──────────────────────────────────

export interface ModelEntry {
  id: string
  provider: string
  display_name: string
  cost_per_1k_input: number
  cost_per_1k_output: number
  max_tokens: number
  supports_tools: boolean
  supports_vision: boolean
  deprecated: boolean
  successor?: string
  tags: string[]
}

export interface ProviderHealth {
  provider: string
  available: boolean
  available_models: string[]
  error?: string
}
