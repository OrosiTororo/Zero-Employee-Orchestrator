import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
  Ticket,
  MessageSquare,
  FileText,
  ListTodo,
  Bot,
  ArrowRight,
  ShieldCheck,
  FileBox,
  ChevronRight,
  Play,
  Loader2,
  CheckCircle,
  XCircle,
} from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

interface TicketData {
  id: string
  title: string
  description: string
  status: string
  priority: string
  created_at: string
  updated_at: string
}

interface ExecutionResult {
  status: string
  output: string
  metrics: {
    total_cost_usd: number
    total_tokens: number
    nodes_executed: number
    nodes_succeeded: number
  }
  failure_reason: string | null
}

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const t = useT()

  const [ticket, setTicket] = useState<TicketData | null>(null)
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState<ExecutionResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    api.get(`/tickets/${id}`).then(d => setTicket(d as TicketData)).catch(() => setError("Failed to load ticket"))
  }, [id])

  const handleExecute = async () => {
    if (!id) return
    setExecuting(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.post(`/tickets/${id}/execute`) as ExecutionResult
      setResult(res)
      // Reload ticket to get updated status
      const updated = await api.get(`/tickets/${id}`) as TicketData
      setTicket(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Execution failed")
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Ticket size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {ticket?.title || `${t.ticketDetail?.ticketLabel ?? "Ticket"}: ${id}`}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExecute}
              disabled={executing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] font-medium text-white transition-colors"
              style={{ background: executing ? "var(--text-muted)" : "var(--success-fg, #22c55e)" }}
            >
              {executing ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Play size={14} />
              )}
              {executing ? "Executing..." : "Execute"}
            </button>
            <button
              onClick={() => navigate(`/tickets/${id}/spec-plan`)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white"
            >
              <FileText size={14} />
              {t.ticketDetail?.viewSpecPlan ?? "View Spec & Plan"}
              <ChevronRight size={14} />
            </button>
          </div>
        </div>

        {/* Execution Result */}
        {result && (
          <div
            className="rounded px-4 py-3 border mb-4"
            style={{
              borderColor: result.status === "succeeded" ? "var(--success-fg, #22c55e)" : "var(--error-fg, #ef4444)",
              background: result.status === "succeeded"
                ? "rgba(34,197,94,0.08)"
                : "rgba(239,68,68,0.08)",
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              {result.status === "succeeded" ? (
                <CheckCircle size={16} className="text-green-500" />
              ) : (
                <XCircle size={16} className="text-red-500" />
              )}
              <span className="text-[13px] font-medium text-[var(--text-primary)]">
                Execution {result.status}
              </span>
              <span className="text-[11px] text-[var(--text-muted)] ml-auto">
                {result.metrics.nodes_succeeded}/{result.metrics.nodes_executed} nodes
                {result.metrics.total_cost_usd > 0 && ` · $${result.metrics.total_cost_usd.toFixed(4)}`}
                {result.metrics.total_tokens > 0 && ` · ${result.metrics.total_tokens} tokens`}
              </span>
            </div>
            {result.output && (
              <div className="text-[12px] text-[var(--text-secondary)] whitespace-pre-wrap max-h-[300px] overflow-auto">
                {result.output}
              </div>
            )}
            {result.failure_reason && (
              <div className="text-[12px] text-red-400 mt-2">{result.failure_reason}</div>
            )}
          </div>
        )}

        {error && (
          <div className="rounded px-4 py-3 border border-red-500/30 bg-red-500/10 mb-4 text-[12px] text-red-400">
            {error}
          </div>
        )}

        {/* Status & Meta */}
        <div className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)] mb-4">
          <div className="grid grid-cols-4 gap-4 text-[12px]">
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.status ?? "Status"}</div>
              <span className="px-2 py-0.5 rounded text-[11px] bg-[var(--accent)]/20 text-[var(--accent)]">
                {ticket?.status ?? "--"}
              </span>
            </div>
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.priority ?? "Priority"}</div>
              <span className="text-[var(--text-primary)]">{ticket?.priority ?? "--"}</span>
            </div>
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.createdAt ?? "Created"}</div>
              <span className="text-[var(--text-primary)]">{ticket?.created_at?.slice(0, 10) ?? "--"}</span>
            </div>
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.updatedAt ?? "Updated"}</div>
              <span className="text-[var(--text-primary)]">{ticket?.updated_at?.slice(0, 10) ?? "--"}</span>
            </div>
          </div>
        </div>

        {/* Description */}
        {ticket?.description && (
          <Section icon={FileText} title="Description">
            <div className="text-[12px] text-[var(--text-secondary)] py-3 whitespace-pre-wrap">
              {ticket.description}
            </div>
          </Section>
        )}

        {/* Thread / Discussion */}
        <Section icon={MessageSquare} title={t.ticketDetail?.thread ?? "Thread"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noMessages ?? "No messages in this ticket yet."}
          </div>
        </Section>

        {/* Spec / Plan / Tasks */}
        <Section icon={FileText} title={t.ticketDetail?.specPlan ?? "Spec & Plan"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noSpecPlan ?? "No spec or plan has been created yet."}
          </div>
        </Section>

        {/* Task List */}
        <Section icon={ListTodo} title={t.ticketDetail?.taskList ?? "Tasks"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noTasks ?? "No tasks have been assigned yet."}
          </div>
        </Section>

        {/* Assignments */}
        <Section icon={Bot} title={t.ticketDetail?.agentAssignment ?? "Agent Assignment"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noAgents ?? "No agents have been assigned yet."}
          </div>
        </Section>

        {/* State Transitions */}
        <Section icon={ArrowRight} title={t.ticketDetail?.stateHistory ?? "State Transition History"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noTransitions ?? "No transition history."}
          </div>
        </Section>

        {/* Approvals */}
        <Section icon={ShieldCheck} title={t.ticketDetail?.approvals ?? "Approvals"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noApprovals ?? "No approval requests."}
          </div>
        </Section>

        {/* Artifacts */}
        <Section icon={FileBox} title={t.ticketDetail?.artifacts ?? "Artifacts"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noArtifacts ?? "No artifacts yet."}
          </div>
        </Section>
      </div>
    </div>
  )
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-4 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
        <Icon size={14} className="text-[var(--accent)]" />
        <span className="text-[12px] font-medium text-[var(--text-primary)]">{title}</span>
      </div>
      <div className="px-4">{children}</div>
    </div>
  )
}
