import { useState, useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import { ScrollText, Search, Filter, ArrowRight } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

const EVENT_TYPES = [
  "all",
  "ticket.created", "ticket.updated",
  "approval.requested", "approval.granted", "approval.rejected",
  "agent.assigned", "agent.completed",
  "cost.incurred", "auth.login", "auth.logout", "settings.updated",
]

interface AuditLog {
  id: string
  actor: string
  event_type: string
  target: string
  trace_id?: string
  created_at?: string
  detail?: string
}

export function AuditPage() {
  const t = useT()
  const navigate = useNavigate()
  const companyId = localStorage.getItem("company_id") || ""
  const [search, setSearch] = useState("")
  const [eventFilter, setEventFilter] = useState("all")
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)

  const fetchLogs = useCallback(async () => {
    if (!companyId) { setLoading(false); return }
    setLoading(true)
    try {
      const filter = eventFilter !== "all" ? `&event_type=${eventFilter}` : ""
      const data = await api.get<AuditLog[]>(`/companies/${companyId}/audit-logs?limit=100${filter}`)
      setLogs(data)
    } catch {
      setLogs([])
    } finally {
      setLoading(false)
    }
  }, [companyId, eventFilter])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  const filtered = logs.filter(
    (log) =>
      log.actor?.toLowerCase().includes(search.toLowerCase()) ||
      log.event_type?.toLowerCase().includes(search.toLowerCase()) ||
      log.target?.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1000px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <ScrollText size={18} className="text-[var(--accent)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.audit.title}</h2>
        </div>

        <div className="flex gap-3 mb-4">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder={t.audit.searchPlaceholder}
              className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
              aria-label={t.audit.searchPlaceholder} />
          </div>
          <div className="relative">
            <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <select value={eventFilter} onChange={(e) => setEventFilter(e.target.value)}
              className="pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] appearance-none"
              aria-label={t.audit.filterLabel}>
              {EVENT_TYPES.map((et) => (
                <option key={et} value={et}>{et === "all" ? t.audit.allEvents : et}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden">
          <div className="grid grid-cols-6 gap-2 px-4 py-2 text-[11px] text-[var(--text-muted)] border-b border-[var(--border)] font-medium">
            <span>{t.audit.dateTime}</span>
            <span>{t.audit.actor}</span>
            <span>{t.audit.event}</span>
            <span>{t.audit.target}</span>
            <span>{t.audit.traceId}</span>
            <span>{t.audit.detail}</span>
          </div>
          {loading ? (
            <div className="px-4 py-8 text-center text-[12px] text-[var(--text-muted)]">
              {t.common.loading}
            </div>
          ) : filtered.length === 0 ? (
            <div className="px-4 py-8 text-center text-[var(--text-muted)]">
              <ScrollText size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-[12px] mb-2">{t.audit.emptyState}</p>
              <button onClick={() => navigate("/")} className="inline-flex items-center gap-1 text-[12px] text-[var(--accent)] hover:underline">
                {t.dashboard?.requestTask ?? "Request a task"} <ArrowRight size={12} />
              </button>
            </div>
          ) : (
            filtered.map((log) => (
              <div key={log.id}
                className="grid grid-cols-6 gap-2 px-4 py-2 text-[12px] border-b border-[var(--border)] last:border-b-0 hover:bg-[var(--bg-hover)]">
                <span className="text-[var(--text-muted)] text-[11px]">{log.created_at ?? ""}</span>
                <span className="text-[var(--text-primary)]">{log.actor}</span>
                <span className="text-[var(--info)] font-mono text-[11px]">{log.event_type}</span>
                <span className="text-[var(--text-primary)] truncate">{log.target}</span>
                <span className="text-[var(--text-muted)] font-mono text-[10px] truncate">{log.trace_id ?? ""}</span>
                <span className="text-[var(--text-secondary)] truncate">{log.detail ?? ""}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
