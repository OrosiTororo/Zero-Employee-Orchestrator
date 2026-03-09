import { useState, useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import {
  Send,
  Sparkles,
  Ticket,
  ShieldCheck,
  Bot,
  HeartPulse,
  Coins,
  AlertTriangle,
  Lightbulb,
  Target,
} from "lucide-react"
import { api } from "../shared/api/client"
import { useT } from "@/shared/i18n"

export function DashboardPage() {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [activeTickets, setActiveTickets] = useState(0)
  const [pendingApprovals, setPendingApprovals] = useState(0)
  const [agentStatus, setAgentStatus] = useState("0 / 0")
  const navigate = useNavigate()
  const t = useT()
  const companyId = localStorage.getItem("company_id") || ""

  const fetchStats = useCallback(async () => {
    if (!companyId) return
    try {
      const [tickets, approvals, agents] = await Promise.all([
        api.get<any[]>(`/companies/${companyId}/tickets?status=in_progress`).catch(() => []),
        api.get<any[]>(`/approvals?status=requested`).catch(() => []),
        api.get<any[]>(`/companies/${companyId}/agents`).catch(() => []),
      ])
      setActiveTickets(tickets.length)
      setPendingApprovals(approvals.length)
      const active = agents.filter((a: any) => a.status === "active").length
      setAgentStatus(`${active} / ${agents.length}`)
    } catch {
      // Stats will remain at defaults
    }
  }, [companyId])

  useEffect(() => { fetchStats() }, [fetchStats])

  const handleSubmit = async () => {
    if (!input.trim() || loading) return
    setLoading(true)
    try {
      if (companyId) {
        const ticket = await api.post<{ id: string }>(`/companies/${companyId}/tickets`, {
          title: input.trim(),
          description: input.trim(),
          priority: "medium",
          source_type: "user",
        })
        navigate(`/tickets/${ticket.id}/interview`)
      } else {
        navigate("/tickets")
      }
    } catch (e) {
      console.error("Failed:", e)
      navigate("/tickets")
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Natural Language Input */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.dashboard.requestTask}
            </h2>
          </div>
          <div className="rounded-md overflow-hidden border border-[var(--border)] bg-[var(--bg-surface)] focus-within:border-[var(--accent)] transition-colors">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t.dashboard.inputPlaceholder}
              className="w-full resize-none px-4 py-3 text-[13px] outline-none bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
              style={{ minHeight: "80px" }}
              rows={3}
            />
            <div className="flex items-center justify-end px-4 py-2 border-t border-[var(--border)]">
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-md text-[12px] text-white font-medium"
                style={{
                  background:
                    input.trim() && !loading
                      ? "linear-gradient(135deg, #0078d4, #6d28d9)"
                      : "var(--border)",
                }}
              >
                <Send size={13} />
                {loading ? t.dashboard.submitting : t.dashboard.submit}
              </button>
            </div>
          </div>
        </div>

        {/* Company Mission */}
        <div className="mb-6 rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 mb-1">
            <Target size={14} className="text-[var(--accent)]" />
            <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
              {t.dashboard.companyMission}
            </span>
          </div>
          <p className="text-[13px] text-[var(--text-primary)]">
            {t.dashboard.noMission}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <SummaryCard
            icon={Ticket}
            label={t.dashboard.activeTickets}
            value={String(activeTickets)}
            sub={t.dashboard.activeSub}
            onClick={() => navigate("/tickets")}
          />
          <SummaryCard
            icon={ShieldCheck}
            label={t.dashboard.pendingApprovals}
            value={String(pendingApprovals)}
            sub={t.dashboard.pendingSub}
            onClick={() => navigate("/approvals")}
          />
          <SummaryCard
            icon={Bot}
            label={t.dashboard.agentStatus}
            value={agentStatus}
            sub={t.dashboard.agentSub}
            onClick={() => navigate("/org-chart")}
          />
          <SummaryCard
            icon={HeartPulse}
            label={t.dashboard.heartbeat}
            value={t.dashboard.heartbeatNormal}
            sub={t.dashboard.heartbeatSub}
            onClick={() => navigate("/heartbeats")}
          />
        </div>

        {/* Cost Summary */}
        <div className="mb-6 rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 mb-2">
            <Coins size={14} className="text-[var(--warning)]" />
            <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
              {t.dashboard.costSummary}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-[18px] font-semibold text-[var(--text-primary)]">
                $0.00
              </div>
              <div className="text-[11px] text-[var(--text-muted)]">{t.dashboard.today}</div>
            </div>
            <div>
              <div className="text-[18px] font-semibold text-[var(--text-primary)]">
                $0.00
              </div>
              <div className="text-[11px] text-[var(--text-muted)]">{t.dashboard.thisWeek}</div>
            </div>
            <div>
              <div className="text-[18px] font-semibold text-[var(--text-primary)]">
                $0.00
              </div>
              <div className="text-[11px] text-[var(--text-muted)]">{t.dashboard.thisMonth}</div>
            </div>
          </div>
        </div>

        {/* Errors / Blocks */}
        <div className="mb-6 rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-[var(--error)]" />
            <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
              {t.dashboard.errorsBlocks}
            </span>
          </div>
          <p className="text-[12px] text-[var(--text-muted)]">
            {t.dashboard.noErrors}
          </p>
        </div>

        {/* Recommended Actions */}
        <div className="rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb size={14} className="text-[var(--success-fg)]" />
            <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
              {t.dashboard.recommendedActions}
            </span>
          </div>
          <ul className="flex flex-col gap-1">
            <li className="text-[12px] text-[var(--text-primary)] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
              {t.dashboard.action1}
            </li>
            <li className="text-[12px] text-[var(--text-primary)] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
              {t.dashboard.action2}
            </li>
            <li className="text-[12px] text-[var(--text-primary)] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
              {t.dashboard.action3}
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  sub,
  onClick,
}: {
  icon: React.ComponentType<{ size?: number }>
  label: string
  value: string
  sub: string
  onClick?: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="rounded-md px-4 py-3 text-left border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors"
    >
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} />
        <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
          {label}
        </span>
      </div>
      <div className="text-[20px] font-semibold text-[var(--text-primary)]">
        {value}
      </div>
      <div className="text-[11px] text-[var(--text-muted)]">{sub}</div>
    </button>
  )
}
