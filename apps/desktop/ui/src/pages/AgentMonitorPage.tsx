import { useState, useEffect, useCallback } from "react"
import {
  Activity,
  Bot,
  Clock,
  Cpu,
  AlertTriangle,
  MessageSquare,
  Zap,
  RefreshCw,
  Shield,
  Brain,
  PauseCircle,
  PlayCircle,
  GitBranch,
  CheckCircle,
  XCircle,
  Eye,
  OctagonX,
  Play,
} from "lucide-react"
import { api } from "../shared/api/client"
import { useT } from "@/shared/i18n"

interface ActiveExecution {
  task_id: string
  agent_id: string
  company_id: string
  started_at: number
  status: string
  progress_pct: number
  current_step: string
  model_used: string | null
  tokens_used: number
  cost_usd: number
  elapsed_ms: number
}

interface MonitorSummary {
  active_executions: number
  total_events: number
  recent_errors: number
  recent_escalations: number
  active_agents: string[]
}

interface Session {
  session_id: string
  agent_id: string
  role: string
  status: string
  message_count: number
  round_count: number
  started_at: number
  last_active_at: number
  idle_since: number | null
}

interface Hypothesis {
  hypothesis_id: string
  title: string
  status: string
  support_score: number
  review_consensus: string
  evidence_count: number
  review_count: number
  proposer_agent_id: string
}

interface SentryStats {
  total_events: number
  errors_last_hour: number
  errors_last_24h: number
  error_types: Record<string, number>
  sdk_available: boolean
}

interface ReasoningTrace {
  trace_id: string
  task_id: string | null
  agent_id: string | null
  started_at: number
  summary: string
  outcome: string | null
  steps: Array<{
    step_id: string
    step_type: string
    summary: string
    confidence: string
    timestamp: number
    duration_ms: number | null
  }>
}

interface PendingApproval {
  id: string
  operation_type: string
  description: string
  risk_level: string
  requested_by: string
  requested_at: string
  context: Record<string, unknown>
}

export function AgentMonitorPage() {
  const t = useT()
  const [summary, setSummary] = useState<MonitorSummary | null>(null)
  const [active, setActive] = useState<ActiveExecution[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [sentryStats, setSentryStats] = useState<SentryStats | null>(null)
  const [traces, setTraces] = useState<ReasoningTrace[]>([])
  const [approvals, setApprovals] = useState<PendingApproval[]>([])
  const [tab, setTab] = useState<"monitor" | "traces" | "approvals" | "sessions" | "hypotheses" | "errors">("monitor")
  const [killSwitchActive, setKillSwitchActive] = useState(false)

  const fetchKillSwitchStatus = useCallback(async () => {
    try {
      const status = await api.get<{ active: boolean }>("/kill-switch/status")
      setKillSwitchActive(status.active)
    } catch { /* ignore */ }
  }, [])

  const handleKillSwitch = useCallback(async () => {
    if (killSwitchActive) {
      try {
        await api.post("/kill-switch/deactivate", {})
        setKillSwitchActive(false)
      } catch { /* ignore */ }
    } else {
      const confirmed = window.confirm(
        t.agentMonitor?.killSwitchConfirm
          ?? "Are you sure you want to activate the emergency kill switch? This will stop ALL active executions."
      )
      if (!confirmed) return
      try {
        await api.post("/kill-switch/activate", {})
        setKillSwitchActive(true)
        fetchData()
      } catch { /* ignore */ }
    }
  }, [killSwitchActive, t])

  const fetchData = useCallback(async () => {
    try {
      const [dashboard, sessionData, hypoData, sentry, traceData, approvalData] = await Promise.all([
        api.get<{ summary: MonitorSummary; active: ActiveExecution[] }>("/monitor/dashboard").catch(() => null),
        api.get<{ sessions: Session[] }>("/sessions").catch(() => ({ sessions: [] })),
        api.get<{ hypotheses: Hypothesis[] }>("/hypotheses").catch(() => ({ hypotheses: [] })),
        api.get<SentryStats>("/sentry/stats").catch(() => null),
        api.get<{ traces: ReasoningTrace[] }>("/traces?limit=20").catch(() => ({ traces: [] })),
        api.get<PendingApproval[]>("/approvals?status=requested").catch(() => []),
      ])
      if (dashboard) {
        setSummary(dashboard.summary)
        setActive(dashboard.active)
      }
      setSessions(sessionData.sessions)
      setHypotheses(hypoData.hypotheses)
      if (sentry) setSentryStats(sentry)
      setTraces(traceData.traces)
      setApprovals(approvalData)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchData(); fetchKillSwitchStatus() }, [fetchData, fetchKillSwitchStatus])

  // Auto-refresh every 5 seconds
  useEffect(() => {
    const timer = setInterval(fetchData, 5000)
    return () => clearInterval(timer)
  }, [fetchData])

  const tabs = [
    { key: "monitor" as const, label: t.agentMonitor?.executionMonitor ?? "Execution", icon: Activity },
    { key: "traces" as const, label: t.agentMonitor?.reasoningTraces ?? "Reasoning Traces", icon: GitBranch },
    { key: "approvals" as const, label: t.agentMonitor?.approvalQueue ?? "Approvals", icon: Shield, badge: approvals.length },
    { key: "sessions" as const, label: t.agentMonitor?.sessions ?? "Sessions", icon: Brain },
    { key: "hypotheses" as const, label: t.agentMonitor?.hypotheses ?? "Hypotheses", icon: Zap },
    { key: "errors" as const, label: t.agentMonitor?.errorMonitor ?? "Errors", icon: AlertTriangle },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1000px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
              {t.agentMonitor?.title ?? "Agent Monitor Dashboard"}
            </h1>
            <p className="text-[12px] text-[var(--text-muted)] mt-0.5">
              {t.agentMonitor?.subtitle ?? "Monitor agent status in real-time from the browser"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleKillSwitch}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium transition-colors ${
                killSwitchActive
                  ? "bg-[var(--warning)] text-[var(--bg-base)] hover:opacity-90"
                  : "bg-[var(--error)] text-white hover:opacity-90"
              }`}
            >
              {killSwitchActive ? (
                <>
                  <Play size={13} />
                  {t.agentMonitor?.resume ?? "Resume"}
                </>
              ) : (
                <>
                  <OctagonX size={13} />
                  {t.agentMonitor?.killSwitch ?? "Emergency Stop"}
                </>
              )}
            </button>
            <button onClick={fetchData} className="p-2 rounded-md hover:bg-[var(--bg-hover)]">
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-4 gap-3 mb-6">
            <StatCard icon={Cpu} label={t.agentMonitor?.activeTasks ?? "Active Tasks"} value={String(summary.active_executions)} color="var(--accent)" />
            <StatCard icon={Bot} label={t.agentMonitor?.activeAgents ?? "Active Agents"} value={String(summary.active_agents.length)} color="var(--success-fg)" />
            <StatCard icon={AlertTriangle} label={t.agentMonitor?.recentErrors ?? "Recent Errors"} value={String(summary.recent_errors)} color="var(--error)" />
            <StatCard icon={MessageSquare} label={t.agentMonitor?.escalations ?? "Escalations"} value={String(summary.recent_escalations)} color="var(--warning)" />
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-[var(--border)]">
          {tabs.map(({ key, label, icon: Icon, badge }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 px-4 py-2 text-[12px] border-b-2 transition-colors ${
                tab === key
                  ? "border-[var(--accent)] text-[var(--accent)]"
                  : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              <Icon size={13} />
              {label}
              {badge !== undefined && badge > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-[9px] rounded-full bg-[var(--accent)] text-white font-medium">
                  {badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Monitor Tab */}
        {tab === "monitor" && (
          <div className="space-y-3">
            {active.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                {t.agentMonitor?.noActiveTasks ?? "No active tasks"}
              </div>
            ) : (
              active.map(exec => (
                <div key={exec.task_id} className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Cpu size={14} className="text-[var(--accent)]" />
                      <span className="text-[12px] font-medium text-[var(--text-primary)]">
                        {exec.task_id.slice(0, 8)}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent)] text-white">
                        {exec.status}
                      </span>
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
                      <Clock size={10} />
                      {Math.round(exec.elapsed_ms / 1000)}s
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)]">
                    <span>Agent: {exec.agent_id.slice(0, 8)}</span>
                    {exec.model_used && <span>Model: {exec.model_used}</span>}
                    <span>Tokens: {exec.tokens_used}</span>
                    <span>Cost: ${exec.cost_usd.toFixed(4)}</span>
                  </div>
                  {exec.current_step && (
                    <div className="mt-2 text-[11px] text-[var(--text-secondary)]">
                      {exec.current_step}
                    </div>
                  )}
                  <div className="mt-2 w-full bg-[var(--border)] rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-[var(--accent)]"
                      style={{ width: `${exec.progress_pct}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Reasoning Traces Tab */}
        {tab === "traces" && (
          <div className="space-y-3">
            {traces.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                {t.agentMonitor?.noTraces ?? "No reasoning traces yet. Traces appear when agents execute tasks."}
              </div>
            ) : (
              traces.map(trace => (
                <div key={trace.trace_id} className="rounded-md border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)]">
                    <div className="flex items-center gap-2">
                      <GitBranch size={14} className="text-[var(--accent)]" />
                      <span className="text-[12px] font-medium text-[var(--text-primary)]">{trace.summary || trace.trace_id.slice(0, 8)}</span>
                      {trace.outcome && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                          trace.outcome === "success" ? "bg-[rgba(78,201,176,0.15)] text-[var(--success-fg)]" :
                          "bg-[rgba(244,71,71,0.15)] text-[var(--error)]"
                        }`}>{trace.outcome}</span>
                      )}
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)]">{trace.steps.length} steps</span>
                  </div>
                  <div className="px-4 py-2">
                    {trace.steps.map((step, i) => (
                      <div key={step.step_id} className="flex items-start gap-2 py-1.5 text-[11px]">
                        <div className="flex flex-col items-center shrink-0 mt-0.5">
                          <div className={`w-2 h-2 rounded-full ${
                            step.step_type.includes("decision") ? "bg-[var(--accent)]" :
                            step.step_type.includes("error") ? "bg-[var(--error)]" :
                            step.step_type.includes("judge") ? "bg-[var(--warning)]" :
                            "bg-[var(--text-muted)]"
                          }`} />
                          {i < trace.steps.length - 1 && <div className="w-px flex-1 bg-[var(--border)] min-h-[12px]" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[var(--text-primary)]">{step.summary}</span>
                            <span className="text-[9px] px-1 py-0.5 rounded bg-[var(--bg-active)] text-[var(--text-muted)]">{step.step_type}</span>
                            {step.confidence && (
                              <span className="text-[9px] text-[var(--text-muted)]">{step.confidence}</span>
                            )}
                          </div>
                        </div>
                        {step.duration_ms != null && (
                          <span className="text-[10px] text-[var(--text-muted)] shrink-0">{step.duration_ms}ms</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Approvals Tab */}
        {tab === "approvals" && (
          <div className="space-y-3">
            {approvals.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                {t.agentMonitor?.noApprovals ?? "No pending approvals. All operations are running within approved boundaries."}
              </div>
            ) : (
              approvals.map(ap => (
                <div key={ap.id} className="rounded-md border border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Shield size={14} className={
                        ap.risk_level === "high" ? "text-[var(--error)]" :
                        ap.risk_level === "medium" ? "text-[var(--warning)]" :
                        "text-[var(--accent)]"
                      } />
                      <span className="text-[12px] font-medium text-[var(--text-primary)]">{ap.operation_type}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        ap.risk_level === "high" ? "bg-[rgba(244,71,71,0.15)] text-[var(--error)]" :
                        ap.risk_level === "medium" ? "bg-[rgba(220,220,170,0.15)] text-[var(--warning)]" :
                        "bg-[rgba(0,122,204,0.12)] text-[var(--accent)]"
                      }`}>{ap.risk_level}</span>
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)]">{ap.requested_at}</span>
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] mb-3">{ap.description}</p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={async () => {
                        try {
                          await api.post(`/approvals/${ap.id}/approve`, {})
                          fetchData()
                        } catch { /* ignore */ }
                      }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded text-[11px] bg-[var(--success)] text-white hover:opacity-90"
                    >
                      <CheckCircle size={12} />
                      {t.agentMonitor?.approve ?? "Approve"}
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          await api.post(`/approvals/${ap.id}/reject`, {})
                          fetchData()
                        } catch { /* ignore */ }
                      }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded text-[11px] border border-[var(--error)] text-[var(--error)] hover:bg-[rgba(244,71,71,0.1)]"
                    >
                      <XCircle size={12} />
                      {t.agentMonitor?.reject ?? "Reject"}
                    </button>
                    <button className="flex items-center gap-1 px-3 py-1.5 rounded text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                      <Eye size={12} />
                      {t.agentMonitor?.viewDetails ?? "Details"}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Sessions Tab */}
        {tab === "sessions" && (
          <div className="space-y-3">
            {sessions.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                {t.agentMonitor?.noActiveSessions ?? "No active sessions"}
              </div>
            ) : (
              sessions.map(s => (
                <div key={s.session_id} className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {s.status === "idle" ? (
                        <PauseCircle size={14} className="text-[var(--warning)]" />
                      ) : (
                        <PlayCircle size={14} className="text-[var(--success-fg)]" />
                      )}
                      <span className="text-[12px] font-medium text-[var(--text-primary)]">
                        {s.agent_id}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-active)] text-[var(--text-secondary)]">
                        {s.role}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        s.status === "active" ? "bg-green-100 text-green-700" :
                        s.status === "idle" ? "bg-yellow-100 text-yellow-700" :
                        "bg-gray-100 text-gray-700"
                      }`}>{s.status}</span>
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      Round {s.round_count} / {s.message_count} msgs
                    </span>
                  </div>
                  {s.idle_since && (
                    <div className="text-[11px] text-[var(--text-muted)]">
                      {t.agentMonitor?.idleContext ?? "Idle: context held since"} {Math.round((Date.now() / 1000 - s.idle_since) / 60)} {t.agentMonitor?.minutesAgo ?? "min ago"}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Hypotheses Tab */}
        {tab === "hypotheses" && (
          <div className="space-y-3">
            {hypotheses.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                {t.agentMonitor?.noActiveHypotheses ?? "No active hypotheses"}
              </div>
            ) : (
              hypotheses.map(h => (
                <div key={h.hypothesis_id} className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[12px] font-medium text-[var(--text-primary)]">
                      {h.title}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      h.status === "confirmed" ? "bg-green-100 text-green-700" :
                      h.status === "refuted" ? "bg-red-100 text-red-700" :
                      h.status === "investigating" ? "bg-blue-100 text-blue-700" :
                      "bg-yellow-100 text-yellow-700"
                    }`}>{h.status}</span>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)]">
                    <span>{t.agentMonitor?.supportScore ?? "Support"}: {(h.support_score * 100).toFixed(0)}%</span>
                    <span>{t.agentMonitor?.consensus ?? "Consensus"}: {h.review_consensus}</span>
                    <span>{t.agentMonitor?.evidence ?? "Evidence"}: {h.evidence_count}</span>
                    <span>{t.agentMonitor?.reviews ?? "Reviews"}: {h.review_count}</span>
                    <span>{t.agentMonitor?.proposer ?? "Proposer"}: {h.proposer_agent_id.slice(0, 8)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Errors Tab (Sentry) */}
        {tab === "errors" && sentryStats && (
          <div>
            <div className="grid grid-cols-3 gap-3 mb-6">
              <StatCard icon={AlertTriangle} label={t.agentMonitor?.errorsLastHour ?? "Errors (1h)"} value={String(sentryStats.errors_last_hour)} color="var(--error)" />
              <StatCard icon={AlertTriangle} label={t.agentMonitor?.errorsLast24h ?? "Errors (24h)"} value={String(sentryStats.errors_last_24h)} color="var(--warning)" />
              <StatCard icon={Shield} label="Sentry SDK" value={sentryStats.sdk_available ? (t.agentMonitor?.connected ?? "Connected") : (t.agentMonitor?.builtin ?? "Built-in")} color="var(--success-fg)" />
            </div>

            {Object.keys(sentryStats.error_types).length > 0 ? (
              <div className="rounded-md border border-[var(--border)] bg-[var(--bg-surface)] p-4">
                <h3 className="text-[12px] font-medium text-[var(--text-primary)] mb-3">{t.agentMonitor?.errorsByType ?? "Errors by Type"}</h3>
                <div className="space-y-2">
                  {Object.entries(sentryStats.error_types).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-[12px]">
                      <span className="text-[var(--text-primary)] font-mono">{type}</span>
                      <span className="text-[var(--error)] font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                {t.agentMonitor?.noRecentErrors ?? "No recent errors"}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ size?: number }>
  label: string
  value: string
  color: string
}) {
  return (
    <div className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon size={13} />
        <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">{label}</span>
      </div>
      <div className="text-[18px] font-semibold" style={{ color }}>{value}</div>
    </div>
  )
}
