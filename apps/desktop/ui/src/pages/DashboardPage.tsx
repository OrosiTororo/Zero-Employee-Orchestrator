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
  Target,
  Globe,
  Terminal,
  FileText,
  Zap,
  Search,
  HelpCircle,
  ListTodo,
  BookOpen,
  X,
  Settings as SettingsIcon,
} from "lucide-react"
import { api } from "../shared/api/client"
import { useT } from "@/shared/i18n"
import { WhatsNew } from "@/shared/ui/WhatsNew"

export function DashboardPage() {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [activeTickets, setActiveTickets] = useState(0)
  const [pendingApprovals, setPendingApprovals] = useState(0)
  const [agentStatus, setAgentStatus] = useState("0 / 0")
  const [showWelcome, setShowWelcome] = useState(() => !localStorage.getItem("welcome_dismissed"))
  const navigate = useNavigate()
  const t = useT()
  const companyId = localStorage.getItem("company_id") || ""

  const fetchStats = useCallback(async () => {
    if (!companyId) return
    try {
      const [tickets, approvals, agents] = await Promise.all([
        api.get<any[]>(`/companies/${companyId}/tickets?status=in_progress`).catch((e) => { console.warn("Failed to load tickets:", e); return [] }),
        api.get<any[]>(`/companies/${companyId}/approvals?status=requested`).catch((e) => { console.warn("Failed to load approvals:", e); return [] }),
        api.get<any[]>(`/companies/${companyId}/agents`).catch((e) => { console.warn("Failed to load agents:", e); return [] }),
      ])
      setActiveTickets(tickets.length)
      setPendingApprovals(approvals.length)
      const active = agents.filter((a: any) => a.status === "active").length
      setAgentStatus(`${active} / ${agents.length}`)
    } catch { /* Stats will remain at defaults */ }
  }, [companyId])

  useEffect(() => { fetchStats() }, [fetchStats])

  const [chatHistory, setChatHistory] = useState<Array<{ role: "user" | "system"; content: string }>>([])
  const [showChat, setShowChat] = useState(false)

  const handleSubmit = async () => {
    if (!input.trim() || loading) return
    setLoading(true)

    try {
      const nlResult = await api.post<{
        success: boolean; message: string; category: string
        confidence: number; delegate_to_llm: boolean; suggestions: string[]
      }>("/command", { text: input.trim() })

      if (nlResult && nlResult.confidence >= 0.3 && !nlResult.delegate_to_llm && nlResult.message) {
        setChatHistory(prev => [...prev, { role: "user", content: input.trim() }, { role: "system", content: nlResult.message }])
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
        setChatHistory(prev => [...prev, { role: "user", content: input.trim() }, { role: "system", content: "Ticket created. Redirecting to interview..." }])
        setShowChat(true)
        navigate("/tickets")
      }
    } catch (e) {
      console.warn("NL command failed:", e)
      navigate("/tickets")
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit() }
  }

  const dismissWelcome = () => {
    localStorage.setItem("welcome_dismissed", "true")
    setShowWelcome(false)
  }

  const quickActions = [
    { icon: Globe, label: t.dashboard.qaResearch, example: t.dashboard.qaResearchEx, color: "var(--accent)" },
    { icon: FileText, label: t.dashboard.qaReport, example: t.dashboard.qaReportEx, color: "var(--accent-secondary)" },
    { icon: Terminal, label: t.dashboard.qaAutomate, example: t.dashboard.qaAutomateEx, color: "var(--success)" },
    { icon: Zap, label: t.dashboard.qaAnalyze, example: t.dashboard.qaAnalyzeEx, color: "var(--warning)" },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[960px] mx-auto px-6 py-6 space-y-5">

        <WhatsNew />

        {/* Welcome Tour - step-by-step onboarding for first-time users */}
        {showWelcome && (
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-5 animate-slide-in relative">
            <button
              onClick={dismissWelcome}
              className="absolute top-3 right-3 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            >
              <X size={16} />
            </button>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                style={{ background: "var(--accent-subtle)" }}>
                <BookOpen size={20} style={{ color: "var(--accent)" }} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-[14px] font-semibold text-[var(--text-primary)] mb-1">
                  {t.dashboard?.welcomeTitle ?? "Welcome to Zero-Employee Orchestrator"}
                </h3>
                <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed mb-3">
                  {t.dashboard?.welcomeDesc ?? "Describe your business tasks in natural language. Your AI team will plan, execute, verify, and deliver — all under your approval."}
                </p>
                {/* Step-by-step tour */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-3">
                  {[
                    { step: 1, icon: Send, label: "Describe a task", desc: "Type what you need in the box below", action: () => document.querySelector("textarea")?.focus() },
                    { step: 2, icon: Bot, label: "Meet your Secretary", desc: "Your AI assistant organizes and delegates", action: () => navigate("/secretary") },
                    { step: 3, icon: ShieldCheck, label: "Review & approve", desc: "AI works, you approve key decisions", action: () => navigate("/approvals") },
                    { step: 4, icon: SettingsIcon, label: "Customize", desc: "Set LLM provider, language, theme", action: () => navigate("/settings") },
                  ].map((s) => (
                    <button
                      key={s.step}
                      onClick={s.action}
                      className="flex flex-col items-start gap-1 p-2.5 rounded border border-[var(--border)] hover:bg-[var(--bg-hover)] transition-colors text-left"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] w-5 h-5 rounded-full flex items-center justify-center font-bold"
                          style={{ background: "var(--accent)", color: "white" }}>{s.step}</span>
                        <s.icon size={13} className="text-[var(--text-muted)]" />
                        <span className="text-[12px] font-medium text-[var(--text-primary)]">{s.label}</span>
                      </div>
                      <span className="text-[11px] text-[var(--text-muted)] pl-7">{s.desc}</span>
                    </button>
                  ))}
                </div>
                <button
                  onClick={dismissWelcome}
                  className="text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                >
                  {t.dashboard?.dismissGuide ?? "Dismiss guide"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Task Input */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Send size={15} className="text-[var(--accent)]" />
            <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
              {t.dashboard.requestTask}
            </h2>
            <kbd className="ml-auto text-[10px] text-[var(--text-muted)] border border-[var(--border)] rounded px-1.5 py-0.5 bg-[var(--bg-raised)]">
              Ctrl+K
            </kbd>
          </div>
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden focus-within:border-[var(--accent)] transition-colors">
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
            <div className="flex items-center justify-between px-4 py-2.5 border-t border-[var(--border)] bg-[var(--bg-raised)]">
              <span className="text-[11px] text-[var(--text-muted)]">
                {t.dashboard.inputHint}
              </span>
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-md text-[12px] font-medium disabled:opacity-40"
              >
                <Send size={12} />
                {loading ? t.dashboard.submitting : t.dashboard.submit}
              </button>
            </div>
          </div>
          {showChat && chatHistory.length > 0 && (
            <div className="mt-3 rounded border border-[var(--border)] bg-[var(--bg-surface)] max-h-[200px] overflow-auto animate-slide-in">
              {chatHistory.map((msg, i) => (
                <div key={i} className={`px-4 py-2.5 text-[12px] ${i > 0 ? "border-t border-[var(--border)]" : ""}`}>
                  <span className={`text-[10px] font-mono font-medium mr-2 ${msg.role === "user" ? "text-[var(--accent)]" : "text-[var(--success)]"}`}>
                    {msg.role === "user" ? ">" : "ZEO"}
                  </span>
                  <span className={msg.role === "user" ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}>
                    {msg.content}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {quickActions.map((qa, i) => (
            <button key={i}
              onClick={() => { setInput(qa.example); }}
              className="rounded border border-[var(--border)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] transition-colors group rounded-lg px-3.5 py-3.5 text-left"
            >
              <div className="w-8 h-8 rounded-md flex items-center justify-center mb-2.5"
                style={{ background: `color-mix(in srgb, ${qa.color} 12%, transparent)` }}>
                <qa.icon size={16} style={{ color: qa.color }} />
              </div>
              <div className="text-[12px] font-medium text-[var(--text-primary)] mb-0.5">{qa.label}</div>
              <div className="text-[11px] text-[var(--text-muted)] truncate">{qa.example}</div>
            </button>
          ))}
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-4 gap-3">
          <StatusCard icon={Ticket} label={t.dashboard.activeTickets} value={String(activeTickets)}
            accent="var(--accent)" onClick={() => navigate("/tickets")} />
          <StatusCard icon={ShieldCheck} label={t.dashboard.pendingApprovals} value={String(pendingApprovals)}
            accent={pendingApprovals > 0 ? "var(--warning)" : "var(--success)"} onClick={() => navigate("/approvals")} />
          <StatusCard icon={Bot} label={t.dashboard.agentStatus} value={agentStatus}
            accent="var(--success)" onClick={() => navigate("/org-chart")} />
          <StatusCard icon={HeartPulse} label={t.dashboard.heartbeat} value={t.dashboard.heartbeatNormal}
            accent="var(--success)" onClick={() => navigate("/heartbeats")} />
        </div>

        <div className="grid grid-cols-3 gap-3">
          {/* Cost */}
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4">
            <div className="flex items-center gap-2 mb-2">
              <Coins size={14} style={{ color: "var(--warning)" }} />
              <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                {t.dashboard.costSummary}
              </span>
            </div>
            <div className="text-[20px] font-bold text-[var(--text-primary)]">$0.00</div>
            <div className="text-[11px] text-[var(--text-muted)]">{t.dashboard.today}</div>
          </div>

          {/* Mission */}
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target size={14} style={{ color: "var(--accent)" }} />
              <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                {t.dashboard.companyMission}
              </span>
            </div>
            <p className="text-[12px] text-[var(--text-muted)] truncate">{t.dashboard.noMission}</p>
          </div>

          {/* Errors */}
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={14} style={{ color: "var(--success)" }} />
              <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                {t.dashboard.errorsBlocks}
              </span>
            </div>
            <p className="text-[12px] text-[var(--text-muted)]">{t.dashboard.noErrors}</p>
          </div>
        </div>

        {/* Quick Start Templates */}
        <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles size={14} style={{ color: "var(--accent-secondary)" }} />
              <span className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                {t.dashboard?.quickStartTemplates ?? "Quick Start Templates"}
              </span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--bg-raised)] text-[var(--text-muted)]">
              {t.dashboard?.quickStartTemplatesDesc ?? "10 min"}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
            {[
              {
                icon: FileText,
                label: t.dashboard?.templateContentOps ?? "Content Operations",
                desc: t.dashboard?.templateContentOpsDesc ?? "Blog/SNS content pipeline with review and publish approval",
                ticket: "Set up a content operations pipeline: blog and SNS content creation with review workflow and publish approval gate",
              },
              {
                icon: Search,
                label: t.dashboard?.templateSalesResearch ?? "Sales Research",
                desc: t.dashboard?.templateSalesResearchDesc ?? "Competitor analysis, market research, lead scoring",
                ticket: "Run a sales research workflow: competitor analysis, market research, and lead scoring with data verification",
              },
              {
                icon: HelpCircle,
                label: t.dashboard?.templateFaqKb ?? "FAQ / Knowledge Base",
                desc: t.dashboard?.templateFaqKbDesc ?? "Customer support automation with human escalation",
                ticket: "Build an internal FAQ and knowledge base for customer support automation with human escalation for complex cases",
              },
              {
                icon: ListTodo,
                label: t.dashboard?.templateMeetingTasks ?? "Meeting to Tasks",
                desc: t.dashboard?.templateMeetingTasksDesc ?? "Meeting notes to action items to ticket creation",
                ticket: "Extract action items from meeting notes, create tickets, and assign them to the appropriate team members",
              },
              {
                icon: ShieldCheck,
                label: t.dashboard?.templatePrePublishReview ?? "Pre-publish Review",
                desc: t.dashboard?.templatePrePublishReviewDesc ?? "Multi-model cross-check for content, code, or docs",
                ticket: "Set up a pre-publish review process with multi-model cross-checking for content, code, and documents using the Judge Layer",
              },
            ].map((tpl, i) => (
              <button
                key={i}
                onClick={async () => {
                  if (companyId) {
                    try {
                      const ticket = await api.post<{ id: string }>(`/companies/${companyId}/tickets`, {
                        title: tpl.label,
                        description: tpl.ticket,
                        priority: "medium",
                        source_type: "user",
                      })
                      navigate(`/tickets/${ticket.id}/interview`)
                    } catch {
                      navigate("/setup")
                    }
                  } else {
                    navigate("/setup")
                  }
                }}
                className="rounded border border-[var(--border)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] transition-colors group rounded-lg px-3 py-3 text-left"
              >
                <tpl.icon size={16} className="text-[var(--text-muted)] group-hover:text-[var(--accent)] mb-2 transition-colors" />
                <div className="text-[12px] font-medium text-[var(--text-primary)] group-hover:text-[var(--accent)] mb-0.5 transition-colors">
                  {tpl.label}
                </div>
                <div className="text-[11px] text-[var(--text-muted)] line-clamp-2">{tpl.desc}</div>
              </button>
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
      className="rounded border border-[var(--border)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] transition-colors rounded-lg px-3.5 py-3.5 text-left">
      <div className="flex items-center gap-1.5 mb-1.5">
        <Icon size={13} style={{ color: accent }} />
        <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold truncate">{label}</span>
      </div>
      <div className="text-[18px] font-bold text-[var(--text-primary)]">{value}</div>
    </button>
  )
}
