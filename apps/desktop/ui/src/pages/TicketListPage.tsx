import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Ticket, Search, Plus, Circle } from "lucide-react"

const statusFilters = [
  { id: "all", label: "すべて" },
  { id: "open", label: "オープン" },
  { id: "in_progress", label: "進行中" },
  { id: "blocked", label: "ブロック" },
  { id: "done", label: "完了" },
  { id: "cancelled", label: "キャンセル" },
]

const statusColors: Record<string, string> = {
  open: "#007acc",
  in_progress: "#dcdcaa",
  blocked: "#f44747",
  done: "#4ec9b0",
  cancelled: "#6a6a6a",
}

export function TicketListPage() {
  const [filter, setFilter] = useState("all")
  const [search, setSearch] = useState("")
  const navigate = useNavigate()

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
            <Ticket size={18} className="text-[#007acc]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              チケット
            </h2>
          </div>
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white"
          >
            <Plus size={14} />
            新規チケット
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="チケットを検索..."
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42]"
          />
        </div>

        {/* Status Filters */}
        <div className="flex gap-1 mb-4">
          {statusFilters.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className="px-3 py-1 rounded text-[11px] transition-colors"
              style={{
                background: filter === f.id ? "#007acc" : "transparent",
                color: filter === f.id ? "#ffffff" : "#969696",
                border:
                  filter === f.id ? "none" : "1px solid #3e3e42",
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Ticket List */}
        <div className="flex flex-col gap-2">
          {tickets.length === 0 ? (
            <div className="rounded px-4 py-8 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
              チケットはまだありません。ダッシュボードから業務を依頼してチケットを作成してください。
            </div>
          ) : (
            tickets.map((ticket) => (
              <button
                key={ticket.id}
                onClick={() => navigate(`/tickets/${ticket.id}`)}
                className="rounded px-4 py-3 text-left border border-[#3e3e42] bg-[#252526] hover:border-[#007acc] transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Circle
                      size={10}
                      fill={statusColors[ticket.status] ?? "#6a6a6a"}
                      className="shrink-0"
                      style={{
                        color: statusColors[ticket.status] ?? "#6a6a6a",
                      }}
                    />
                    <span className="text-[13px] text-[#cccccc]">
                      {ticket.title}
                    </span>
                  </div>
                  <span className="text-[11px] text-[#6a6a6a]">
                    {ticket.created}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1 pl-5 text-[11px] text-[#6a6a6a]">
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
