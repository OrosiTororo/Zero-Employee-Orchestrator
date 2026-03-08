import { useState } from "react"
import { ScrollText, Search, Filter } from "lucide-react"

const eventTypes = [
  "all",
  "ticket.created",
  "ticket.updated",
  "approval.requested",
  "approval.granted",
  "approval.rejected",
  "agent.assigned",
  "agent.completed",
  "cost.incurred",
  "auth.login",
  "auth.logout",
  "settings.updated",
]

export function AuditPage() {
  const [search, setSearch] = useState("")
  const [eventFilter, setEventFilter] = useState("all")

  // Placeholder data
  const logs: {
    id: string
    actor: string
    eventType: string
    target: string
    traceId: string
    timestamp: string
    detail: string
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1000px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <ScrollText size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">監査ログ</h2>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-4">
          <div className="relative flex-1">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="アクター、対象、トレースIDで検索..."
              className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42]"
            />
          </div>
          <div className="relative">
            <Filter
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
            />
            <select
              value={eventFilter}
              onChange={(e) => setEventFilter(e.target.value)}
              className="pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] appearance-none"
            >
              {eventTypes.map((t) => (
                <option key={t} value={t}>
                  {t === "all" ? "すべてのイベント" : t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Log Table */}
        <div className="rounded border border-[#3e3e42] bg-[#252526]">
          <div className="grid grid-cols-6 gap-2 px-4 py-2 text-[11px] text-[#6a6a6a] border-b border-[#3e3e42]">
            <span>日時</span>
            <span>アクター</span>
            <span>イベント</span>
            <span>対象</span>
            <span>トレースID</span>
            <span>詳細</span>
          </div>
          {logs.length === 0 ? (
            <div className="px-4 py-8 text-center text-[12px] text-[#6a6a6a]">
              監査ログはまだありません。システム操作が記録されるとここに表示されます。
            </div>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className="grid grid-cols-6 gap-2 px-4 py-2 text-[12px] border-b border-[#3e3e42] last:border-b-0 hover:bg-[#2a2d2e]"
              >
                <span className="text-[#6a6a6a] text-[11px]">
                  {log.timestamp}
                </span>
                <span className="text-[#cccccc]">{log.actor}</span>
                <span className="text-[#9cdcfe] font-mono text-[11px]">
                  {log.eventType}
                </span>
                <span className="text-[#cccccc] truncate">{log.target}</span>
                <span className="text-[#6a6a6a] font-mono text-[10px] truncate">
                  {log.traceId}
                </span>
                <span className="text-[#969696] truncate">{log.detail}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
