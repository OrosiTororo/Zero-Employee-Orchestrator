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
  Globe,
  Terminal,
  FileText,
  Zap,
  ArrowRight,
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
    } catch { /* Stats will remain at defaults */ }
  }, [companyId])

  useEffect(() => { fetchStats() }, [fetchStats])

  const [nlResponse, setNlResponse] = useState("")
  const [chatHistory, setChatHistory] = useState<Array<{ role: "user" | "system"; content: string }>>([])
  const [showChat, setShowChat] = useState(false)

  const handleSubmit = async () => {
    if (!input.trim() || loading) return
    setLoading(true)
    setNlResponse("")
    try {
      const nlResult = await api.post<{
        success: boolean; message: string; category: string
        confidence: number; delegate_to_llm: boolean; suggestions: string[]
      }>("/command", { text: input.trim() })

      if (nlResult.confidence >= 0.3 && !nlResult.delegate_to_llm && nlResult.message) {
        setChatHistory(prev => [...prev, { role: "user", content: input.trim() }, { role: "system", content: nlResult.message }])
        setNlResponse(nlResult.message)
        setShowChat(true)
        setInput("")
        fetchStats()
        return
      }

      if (companyId) {
        const ticket = await api.post<{ id: string }>(`/companies/${companyId}/tickets`, {
          title: input.trim(), description: input.trim(), priority: "medium", source_type: "user",
        })
        navigate(`/tickets/${ticket.id}/interview`)
      } else {
        navigate("/tickets")
      }
    } catch {
      navigate("/tickets")
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit() }
  }

  const quickActions = [
    { icon: Globe, label: t.dashboard.qaResearch, example: t.dashboard.qaResearchEx },
    { icon: FileText, label: t.dashboard.qaReport, example: t.dashboard.qaReportEx },
    { icon: Terminal, label: t.dashboard.qaAutomate, example: t.dashboard.qaAutomateEx },
    { icon: Zap, label: t.dashboard.qaAnalyze, example: t.dashboard.qaAnalyzeEx },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[960px] mx-auto px-6 py-6">
        {/* Task Input */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Send size={16} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.dashboard.requestTask}
            </h2>
            <kbd className="ml-auto text-[10px] text-[var(--text-muted)] border border-[var(--border)] rounded px-1.5 py-0.5">
              Ctrl+K
            </kbd>
          </div>
          <div className="rounded-md overflow-hidden border border-[var(--border)] bg-[var(--bg-surface)] focus-within:border-[var(--accent)] transition-colors">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t.dashboard.inputPlaceholder}
              className="w-full resize-none px-4 py-3 text-[13px] outline-none bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
              style={{ minHeight: "72px" }}
              rows={3}
              aria-label={t.dashboard.requestTask}
            />
            <div className="flex items-center justify-between px-4 py-2 border-t border-[var(--border)]">
              <span className="text-[11px] text-[var(--text-muted)]">
                {t.dashboard.inputHint}
              </span>
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-md text-[12px] font-medium disabled:opacity-40"
                style={{
                  background: input.trim() && !loading ? "var(--accent)" : "var(--border)",
                  color: input.trim() && !loading ? "var(--accent-fg)" : "var(--text-muted)",
                }}
              >
                <Send size={13} />
                {loading ? t.dashboard.submitting : t.dashboard.submit}
              </button>
            </div>
          </div>
          {showChat && chatHistory.length > 0 && (
            <div className="mt-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)] max-h-[200px] overflow-auto">
              {chatHistory.map((msg, i) => (
                <div key={i} className={`px-4 py-2 text-[12px] ${i > 0 ? "border-t border-[var(--border)]" : ""}`}>
                  <span className="text-[10px] text-[var(--text-muted)] mr-2">{msg.role === "user" ? ">" : "ZEO"}</span>
                  <span className={msg.role === "user" ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}>
                    {msg.content}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-6">
          {quickActions.map((qa, i) => (
            <button key={i}
              onClick={() => { setInput(qa.example); }}
              className="group rounded-md px-3 py-3 text-left border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors"
            >
              <qa.icon size={16} className="text-[var(--accent)] mb-2" />
              <div className="text-[12px] font-medium text-[var(--text-primary)] mb-0.5">{qa.label}</div>
              <div className="text-[11px] text-[var(--text-muted)] truncate">{qa.example}</div>
            </button>
          ))}
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          <StatusCard icon={Ticket} label={t.dashboard.activeTickets} value={String(activeTickets)}
            accent="var(--accent)" onClick={() => navigate("/tickets")} />
          <StatusCard icon={ShieldCheck} label={t.dashboard.pendingApprovals} value={String(pendingApprovals)}
            accent={pendingApprovals > 0 ? "var(--warning)" : "var(--accent)"} onClick={() => navigate("/approvals")} />
          <StatusCard icon={Bot} label={t.dashboard.agentStatus} value={agentStatus}
            accent="var(--success-fg)" onClick={() => navigate("/org-chart")} />
          <StatusCard icon={HeartPulse} label={t.dashboard.heartbeat} value={t.dashboard.heartbeatNormal}
            accent="var(--success-fg)" onClick={() => navigate("/heartbeats")} />
        </div>

        <div className="grid grid-cols-3 gap-3 mb-6">
          {/* Cost */}
          <div className="rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
            <div className="flex items-center gap-2 mb-2">
              <Coins size={14} className="text-[var(--warning)]" />
              <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
                {t.dashboard.costSummary}
              </span>
            </div>
            <div className="text-[20px] font-semibold text-[var(--text-primary)]">$0.00</div>
            <div className="text-[11px] text-[var(--text-muted)]">{t.dashboard.today}</div>
          </div>

          {/* Mission */}
          <div className="rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
            <div className="flex items-center gap-2 mb-2">
              <Target size={14} className="text-[var(--accent)]" />
              <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
                {t.dashboard.companyMission}
              </span>
            </div>
            <p className="text-[12px] text-[var(--text-muted)] truncate">{t.dashboard.noMission}</p>
          </div>

          {/* Errors */}
          <div className="rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={14} className="text-[var(--success-fg)]" />
              <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
                {t.dashboard.errorsBlocks}
              </span>
            </div>
            <p className="text-[12px] text-[var(--text-muted)]">{t.dashboard.noErrors}</p>
          </div>
        </div>

        {/* Recommended Actions */}
        <div className="rounded-md px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb size={14} className="text-[var(--success-fg)]" />
            <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
              {t.dashboard.recommendedActions}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            {[t.dashboard.action1, t.dashboard.action2, t.dashboard.action3].map((action, i) => (
              <div key={i} className="flex items-center gap-2 text-[12px] text-[var(--text-primary)] group cursor-pointer hover:text-[var(--accent)]">
                <ArrowRight size={12} className="text-[var(--text-muted)] group-hover:text-[var(--accent)]" />
                {action}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusCard({ icon: Icon, label, value, accent, onClick }: {
  icon: React.ComponentType<{ size?: number; className?: string; style?: React.CSSProperties }>
  label: string; value: string; accent: string; onClick?: () => void
}) {
  return (
    <button onClick={onClick}
      className="rounded-md px-3 py-3 text-left border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon size={13} style={{ color: accent }} />
        <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium truncate">{label}</span>
      </div>
      <div className="text-[18px] font-semibold text-[var(--text-primary)]">{value}</div>
    </button>
  )
}
