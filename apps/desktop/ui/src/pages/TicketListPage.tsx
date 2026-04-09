import { useState, useEffect, useCallback, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { Ticket, Search, Plus, Circle, ArrowRight } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

const statusFilterIds = ["all", "open", "in_progress", "blocked", "done", "cancelled"] as const

const statusColors: Record<string, string> = {
  open: "var(--accent)",
  in_progress: "var(--warning-fg)",
  blocked: "var(--error)",
  done: "var(--success-fg)",
  cancelled: "var(--text-muted)",
}

interface TicketItem {
  id: string
  title: string
  status: string
  priority: string
  created_at?: string
}

export function TicketListPage() {
  const [filter, setFilter] = useState("all")
  const [search, setSearch] = useState("")
  const [tickets, setTickets] = useState<TicketItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedIdx, setSelectedIdx] = useState(0)
  const navigate = useNavigate()
  const t = useT()
  const companyId = localStorage.getItem("company_id") || ""
  const listRef = useRef<HTMLDivElement>(null)

  const fetchTickets = useCallback(async () => {
    if (!companyId) { setLoading(false); return }
    setLoading(true)
    try {
      const statusParam = filter !== "all" ? `?status=${filter}` : ""
      const data = await api.get<TicketItem[]>(`/companies/${companyId}/tickets${statusParam}`)
      setTickets(data)
    } catch {
      setTickets([])
    } finally {
      setLoading(false)
    }
  }, [companyId, filter])

  useEffect(() => { fetchTickets() }, [fetchTickets])

  // Keyboard navigation: ArrowUp/Down to select, Enter to open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (filtered.length === 0) return
      if ((e.target as HTMLElement).tagName === "INPUT" || (e.target as HTMLElement).tagName === "TEXTAREA") return
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIdx((i) => Math.min(i + 1, filtered.length - 1))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIdx((i) => Math.max(i - 1, 0))
      } else if (e.key === "Enter") {
        const tk = filtered[selectedIdx]
        if (tk) navigate(`/tickets/${tk.id}`)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [filtered, selectedIdx, navigate]) // eslint-disable-line react-hooks/exhaustive-deps

  const statusFilterLabels: Record<string, string> = {
    all: t.ticketList?.filterAll ?? "All",
    open: t.ticketList?.filterOpen ?? "Open",
    in_progress: t.ticketList?.filterInProgress ?? "In Progress",
    blocked: t.ticketList?.filterBlocked ?? "Blocked",
    done: t.ticketList?.filterDone ?? "Done",
    cancelled: t.ticketList?.filterCancelled ?? "Cancelled",
  }

  const filtered = tickets.filter(
    (tk) =>
      tk.title.toLowerCase().includes(search.toLowerCase()) ||
      tk.id.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Ticket size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.ticketList?.title ?? "Tickets"}
            </h2>
          </div>
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white"
          >
            <Plus size={14} />
            {t.ticketList?.newTicket ?? "New Ticket"}
          </button>
        </div>

        <div className="relative mb-4">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.ticketList?.searchPlaceholder ?? "Search tickets..."}
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)]"
          />
        </div>

        <div className="flex gap-1 mb-4">
          {statusFilterIds.map((id) => (
            <button
              key={id}
              onClick={() => setFilter(id)}
              className="px-3 py-1 rounded text-[11px] transition-colors"
              style={{
                background: filter === id ? "var(--accent)" : "transparent",
                color: filter === id ? "var(--bg-base)" : "var(--text-muted)",
                border: filter === id ? "none" : "1px solid var(--border)",
              }}
            >
              {statusFilterLabels[id]}
            </button>
          ))}
        </div>

        {filtered.length > 0 && (
          <div className="flex items-center justify-end mb-1">
            <span className="text-[10px] text-[var(--text-muted)]">↑↓ navigate · <kbd className="font-mono">Enter</kbd> open</span>
          </div>
        )}
        <div className="flex flex-col gap-2" ref={listRef} role="list" aria-label={t.ticketList?.title ?? "Tickets"}>
          {loading ? (
            <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
              {t.common.loading}
            </div>
          ) : filtered.length === 0 ? (
            <div className="rounded px-4 py-8 text-center border border-[var(--border)] text-[var(--text-muted)]">
              <Ticket size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-[12px] mb-2">
                {tickets.length === 0
                  ? (t.ticketList?.emptyState ?? "No tickets yet. Create a ticket by submitting a request from the Dashboard.")
                  : ((t.ticketList as Record<string, string>)?.noMatch ?? "No tickets match your search.")}
              </p>
              {tickets.length === 0 && (
                <button onClick={() => navigate("/")} className="inline-flex items-center gap-1 text-[12px] text-[var(--accent)] hover:underline mt-1">
                  {t.dashboard?.requestTask ?? "Request a task"} <ArrowRight size={12} />
                </button>
              )}
            </div>
          ) : (
            filtered.map((ticket, idx) => (
              <button
                key={ticket.id}
                role="listitem"
                tabIndex={0}
                onClick={() => navigate(`/tickets/${ticket.id}`)}
                onFocus={() => setSelectedIdx(idx)}
                aria-selected={idx === selectedIdx}
                className="rounded px-4 py-3 text-left border bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
                style={{ borderColor: idx === selectedIdx ? "var(--accent)" : "var(--border)" }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Circle
                      size={10}
                      fill={statusColors[ticket.status] ?? "var(--text-muted)"}
                      className="shrink-0"
                      style={{ color: statusColors[ticket.status] ?? "var(--text-muted)" }}
                    />
                    <span className="text-[13px] text-[var(--text-primary)]">{ticket.title}</span>
                  </div>
                  <span className="text-[11px] text-[var(--text-muted)]">{ticket.created_at ?? ""}</span>
                </div>
                <div className="flex items-center gap-3 mt-1 pl-5 text-[11px] text-[var(--text-muted)]">
                  <span>{ticket.id.slice(0, 8)}</span>
                  <span>{ticket.priority}</span>
                  <span>{ticket.status}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
