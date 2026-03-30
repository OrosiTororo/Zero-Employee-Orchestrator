import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Ticket, Search, Plus, Circle } from "lucide-react"
import { useT } from "@/shared/i18n"

const statusFilterIds = ["all", "open", "in_progress", "blocked", "done", "cancelled"] as const

const statusColors: Record<string, string> = {
  open: "var(--accent)",
  in_progress: "var(--warning-fg)",
  blocked: "var(--error)",
  done: "var(--success-fg)",
  cancelled: "var(--text-muted)",
}

export function TicketListPage() {
  const [filter, setFilter] = useState("all")
  const [search, setSearch] = useState("")
  const navigate = useNavigate()
  const t = useT()

  const statusFilterLabels: Record<string, string> = {
    all: t.ticketList?.filterAll ?? "All",
    open: t.ticketList?.filterOpen ?? "Open",
    in_progress: t.ticketList?.filterInProgress ?? "In Progress",
    blocked: t.ticketList?.filterBlocked ?? "Blocked",
    done: t.ticketList?.filterDone ?? "Done",
    cancelled: t.ticketList?.filterCancelled ?? "Cancelled",
  }

  // Placeholder data
  const tickets: {
    id: string
    title: string
    status: string
    priority: string
    assignee: string
    created: string
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
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

        {/* Search */}
        <div className="relative mb-4">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.ticketList?.searchPlaceholder ?? "Search tickets..."}
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)]"
          />
        </div>

        {/* Status Filters */}
        <div className="flex gap-1 mb-4">
          {statusFilterIds.map((id) => (
            <button
              key={id}
              onClick={() => setFilter(id)}
              className="px-3 py-1 rounded text-[11px] transition-colors"
              style={{
                background: filter === id ? "var(--accent)" : "transparent",
                color: filter === id ? "var(--bg-base)" : "var(--text-muted)",
                border:
                  filter === id ? "none" : "1px solid var(--border)",
              }}
            >
              {statusFilterLabels[id]}
            </button>
          ))}
        </div>

        {/* Ticket List */}
        <div className="flex flex-col gap-2">
          {tickets.length === 0 ? (
            <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
              {t.ticketList?.emptyState ?? "No tickets yet. Create a ticket by submitting a request from the Dashboard."}
            </div>
          ) : (
            tickets.map((ticket) => (
              <button
                key={ticket.id}
                onClick={() => navigate(`/tickets/${ticket.id}`)}
                className="rounded px-4 py-3 text-left border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Circle
                      size={10}
                      fill={statusColors[ticket.status] ?? "var(--text-muted)"}
                      className="shrink-0"
                      style={{
                        color: statusColors[ticket.status] ?? "var(--text-muted)",
                      }}
                    />
                    <span className="text-[13px] text-[var(--text-primary)]">
                      {ticket.title}
                    </span>
                  </div>
                  <span className="text-[11px] text-[var(--text-muted)]">
                    {ticket.created}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1 pl-5 text-[11px] text-[var(--text-muted)]">
                  <span>{ticket.id}</span>
                  <span>{ticket.priority}</span>
                  <span>{ticket.assignee}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
