import { useState, useEffect } from "react"
import {
  BrainCircuit,
  Send,
  Loader2,
  Archive,
  CheckCircle,
  Search,
  Lightbulb,
  ListTodo,
  Target,
  AlertTriangle,
  MessageSquare,
  Zap,
} from "lucide-react"
import { api } from "@/shared/api/client"
import { useI18n } from "@/shared/i18n"

interface BrainDump {
  id: string
  raw_text: string
  category: string
  priority: string
  title: string | null
  tags: string[]
  action_items: string[]
  is_processed: boolean
  is_archived: boolean
  created_at: string
}

interface ActionItem {
  action: string
  source_dump_id: string
  priority: string
  category: string
  created_at: string | null
}

const CATEGORY_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  idea: Lightbulb,
  todo: ListTodo,
  decision: Target,
  problem: AlertTriangle,
  strategy: Zap,
  memo: MessageSquare,
}

const CATEGORY_COLORS: Record<string, string> = {
  idea: "#f59e0b",
  todo: "#3b82f6",
  decision: "#8b5cf6",
  problem: "#ef4444",
  strategy: "#10b981",
  opportunity: "#06b6d4",
  reflection: "#6366f1",
  memo: "#6b7280",
  daily_log: "#a855f7",
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#6b7280",
}

export function SecretaryPage() {
  const { locale } = useI18n()
  const isJa = locale === "ja"

  const [dumps, setDumps] = useState<BrainDump[]>([])
  const [actionItems, setActionItems] = useState<ActionItem[]>([])
  const [inputText, setInputText] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [companyId, setCompanyId] = useState<string | null>(null)
  const [dailyStats, setDailyStats] = useState<{ total_dumps: number; ideas_count: number; todos_count: number } | null>(null)

  const categoryLabels: Record<string, string> = isJa
    ? { all: "\u3059\u3079\u3066", idea: "\u30A2\u30A4\u30C7\u30A2", todo: "ToDo", decision: "\u610F\u601D\u6C7A\u5B9A", reflection: "\u632F\u308A\u8FD4\u308A", strategy: "\u6226\u7565", problem: "\u8AB2\u984C", opportunity: "\u6A5F\u4F1A", memo: "\u30E1\u30E2", daily_log: "\u65E5\u8A18" }
    : { all: "All", idea: "Idea", todo: "To-Do", decision: "Decision", reflection: "Reflection", strategy: "Strategy", problem: "Problem", opportunity: "Opportunity", memo: "Memo", daily_log: "Daily Log" }

  const priorityLabels: Record<string, string> = isJa
    ? { high: "\u9AD8", medium: "\u4E2D", low: "\u4F4E" }
    : { high: "High", medium: "Med", low: "Low" }

  useEffect(() => {
    initCompany()
  }, [])

  useEffect(() => {
    if (companyId) {
      loadDumps()
      loadActionItems()
      loadDailyStats()
    }
  }, [companyId, selectedCategory])

  const initCompany = async () => {
    try {
      const companies = await api.get<Array<{ id: string }>>("/companies")
      if (companies.length > 0) {
        setCompanyId(companies[0].id)
      }
    } catch (err) {
      console.error("Failed to load companies:", err)
    }
  }

  const loadDumps = async () => {
    if (!companyId) return
    try {
      const catParam = selectedCategory !== "all" ? `&category=${selectedCategory}` : ""
      const data = await api.get<BrainDump[]>(`/companies/${companyId}/brain-dumps?limit=50${catParam}`)
      setDumps(data)
    } catch (err) {
      console.error("Failed to load brain dumps:", err)
    }
  }

  const loadActionItems = async () => {
    if (!companyId) return
    try {
      const data = await api.get<{ action_items: ActionItem[] }>(`/companies/${companyId}/brain-dumps/action-items`)
      setActionItems(data.action_items)
    } catch (err) {
      console.error("Failed to load action items:", err)
    }
  }

  const loadDailyStats = async () => {
    if (!companyId) return
    try {
      const data = await api.get<{ total_dumps: number; ideas_count: number; todos_count: number }>(
        `/companies/${companyId}/brain-dumps/daily-stats`
      )
      setDailyStats(data)
    } catch (err) {
      console.error("Failed to load daily stats:", err)
    }
  }

  const handleSubmit = async () => {
    if (!inputText.trim() || !companyId) return
    setIsSubmitting(true)
    try {
      await api.post(`/companies/${companyId}/brain-dump`, {
        raw_text: inputText,
      })
      setInputText("")
      await loadDumps()
      await loadActionItems()
      await loadDailyStats()
    } catch (err) {
      console.error("Failed to submit brain dump:", err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleArchive = async (dumpId: string) => {
    try {
      await api.patch(`/brain-dumps/${dumpId}`, { is_archived: true })
      setDumps((prev) => prev.filter((d) => d.id !== dumpId))
    } catch (err) {
      console.error("Failed to archive:", err)
    }
  }

  const handleMarkProcessed = async (dumpId: string) => {
    try {
      await api.patch(`/brain-dumps/${dumpId}`, { is_processed: true })
      setDumps((prev) =>
        prev.map((d) => (d.id === dumpId ? { ...d, is_processed: true } : d))
      )
    } catch (err) {
      console.error("Failed to mark processed:", err)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim() || !companyId) return
    try {
      const data = await api.get<BrainDump[]>(
        `/companies/${companyId}/brain-dumps/search?q=${encodeURIComponent(searchQuery)}`
      )
      setDumps(data)
    } catch (err) {
      console.error("Failed to search:", err)
    }
  }

  const formatDate = (iso: string) => {
    const d = new Date(iso)
    return isJa
      ? `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`
      : d.toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  }

  const CategoryIcon = (cat: string) => CATEGORY_ICONS[cat] || MessageSquare

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <BrainCircuit size={18} className="text-[var(--accent)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
            {isJa ? "\u79D8\u66F8" : "Secretary"}
          </h2>
        </div>
        <p className="text-[12px] text-[var(--text-secondary)] mb-6">
          {isJa
            ? "\u601D\u8003\u30FB\u30A2\u30A4\u30C7\u30A2\u30FBToDo \u3092\u6295\u3052\u8FBC\u3093\u3067\u3001AI \u306B\u6574\u7406\u3057\u3066\u3082\u3089\u3044\u307E\u3057\u3087\u3046"
            : "Dump your thoughts, ideas, and to-dos \u2014 let AI organize them"}
        </p>

        {/* Input area */}
        <div className="mb-6 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-4">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit()
            }}
            placeholder={isJa
              ? "\u8003\u3048\u3066\u3044\u308B\u3053\u3068\u3001\u30A2\u30A4\u30C7\u30A2\u3001\u4ECA\u65E5\u306EToDo\u306A\u3069\u3001\u4F55\u3067\u3082\u6295\u3052\u8FBC\u3093\u3067\u304F\u3060\u3055\u3044..."
              : "Dump your thoughts, ideas, daily to-dos... anything goes"}
            rows={4}
            className="w-full px-3 py-2.5 rounded-md text-[13px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none resize-none mb-3"
          />
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-[var(--text-muted)]">
              {isJa ? "Ctrl+Enter \u3067\u9001\u4FE1" : "Ctrl+Enter to submit"}
            </span>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !inputText.trim()}
              className="flex items-center gap-2 px-4 py-2 rounded-md text-[13px] font-medium text-white disabled:opacity-50"
              style={{ background: "var(--gradient-primary)" }}
            >
              {isSubmitting ? (
                <><Loader2 size={14} className="animate-spin" />{isJa ? "\u6574\u7406\u4E2D..." : "Organizing..."}</>
              ) : (
                <><Send size={14} />{isJa ? "\u6295\u3052\u8FBC\u3080" : "Dump"}</>
              )}
            </button>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Category filter */}
            <div className="flex flex-wrap gap-1 mb-4">
              {Object.entries(categoryLabels).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => { setSelectedCategory(key); setSearchQuery("") }}
                  className="px-2.5 py-1 rounded text-[11px] border transition-colors"
                  style={{
                    background: selectedCategory === key ? "rgba(0, 120, 212, 0.12)" : "transparent",
                    borderColor: selectedCategory === key ? "var(--accent)" : "var(--border)",
                    color: selectedCategory === key ? "var(--accent)" : "var(--text-secondary)",
                  }}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="flex gap-2 mb-4">
              <div className="flex-1 relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSearch() }}
                  placeholder={isJa ? "\u30D6\u30EC\u30A4\u30F3\u30C0\u30F3\u30D7\u3092\u691C\u7D22..." : "Search brain dumps..."}
                  className="w-full pl-8 pr-3 py-2 rounded-md text-[12px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] outline-none"
                />
              </div>
            </div>

            {/* Dumps list */}
            {dumps.length === 0 ? (
              <div className="text-center py-12">
                <BrainCircuit size={48} className="mx-auto mb-4 text-[var(--text-muted)]" />
                <p className="text-[13px] text-[var(--text-secondary)]">
                  {isJa
                    ? "\u307E\u3060\u30D6\u30EC\u30A4\u30F3\u30C0\u30F3\u30D7\u304C\u3042\u308A\u307E\u305B\u3093\u3002\u4E0A\u306E\u5165\u529B\u6B04\u304B\u3089\u601D\u8003\u3092\u6295\u3052\u8FBC\u307F\u307E\u3057\u3087\u3046\u3002"
                    : "No brain dumps yet. Start by dumping your thoughts above."}
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {dumps.map((dump) => {
                  const Icon = CategoryIcon(dump.category)
                  return (
                    <div
                      key={dump.id}
                      className="rounded-md border border-[var(--border)] bg-[var(--bg-surface)] p-4 hover:border-[var(--accent)] transition-colors"
                      style={{ opacity: dump.is_processed ? 0.7 : 1 }}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span style={{ color: CATEGORY_COLORS[dump.category] || "var(--text-muted)" }}><Icon size={14} /></span>
                            <span className="text-[11px] font-medium" style={{ color: CATEGORY_COLORS[dump.category] }}>
                              {categoryLabels[dump.category] || dump.category}
                            </span>
                            <span
                              className="text-[10px] px-1.5 py-0.5 rounded"
                              style={{
                                background: `${PRIORITY_COLORS[dump.priority]}20`,
                                color: PRIORITY_COLORS[dump.priority],
                              }}
                            >
                              {priorityLabels[dump.priority] || dump.priority}
                            </span>
                            <span className="text-[10px] text-[var(--text-muted)]">
                              {formatDate(dump.created_at)}
                            </span>
                          </div>
                          <p className="text-[13px] text-[var(--text-primary)] whitespace-pre-wrap break-words">
                            {dump.raw_text}
                          </p>
                          {dump.action_items.length > 0 && (
                            <div className="mt-2 pl-3 border-l-2 border-[var(--accent)]">
                              {dump.action_items.map((item, i) => (
                                <div key={i} className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
                                  <ListTodo size={12} className="text-[var(--accent)] shrink-0" />
                                  {item}
                                </div>
                              ))}
                            </div>
                          )}
                          {dump.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {dump.tags.map((tag, i) => (
                                <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-hover)] text-[var(--text-muted)]">
                                  #{tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex gap-1 shrink-0">
                          {!dump.is_processed && (
                            <button
                              onClick={() => handleMarkProcessed(dump.id)}
                              className="p-1.5 rounded hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-[var(--success)]"
                              title={isJa ? "\u51E6\u7406\u6E08\u307F" : "Mark processed"}
                            >
                              <CheckCircle size={14} />
                            </button>
                          )}
                          <button
                            onClick={() => handleArchive(dump.id)}
                            className="p-1.5 rounded hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                            title={isJa ? "\u30A2\u30FC\u30AB\u30A4\u30D6" : "Archive"}
                          >
                            <Archive size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="w-[240px] shrink-0">
            {/* Daily Stats */}
            {dailyStats && (
              <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-4 mb-4">
                <h3 className="text-[12px] font-medium text-[var(--text-primary)] mb-3">
                  {isJa ? "\u4ECA\u65E5\u306E\u7D71\u8A08" : "Today's Stats"}
                </h3>
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between text-[12px]">
                    <span className="text-[var(--text-secondary)]">{isJa ? "\u6295\u7A3F\u6570" : "Dumps"}</span>
                    <span className="text-[var(--text-primary)] font-medium">{dailyStats.total_dumps}</span>
                  </div>
                  <div className="flex justify-between text-[12px]">
                    <span className="text-[var(--text-secondary)]">{isJa ? "\u30A2\u30A4\u30C7\u30A2" : "Ideas"}</span>
                    <span className="text-[var(--text-primary)] font-medium">{dailyStats.ideas_count}</span>
                  </div>
                  <div className="flex justify-between text-[12px]">
                    <span className="text-[var(--text-secondary)]">ToDo</span>
                    <span className="text-[var(--text-primary)] font-medium">{dailyStats.todos_count}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Action Items */}
            <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-4">
              <h3 className="text-[12px] font-medium text-[var(--text-primary)] mb-3">
                {isJa ? "\u30A2\u30AF\u30B7\u30E7\u30F3\u30A2\u30A4\u30C6\u30E0" : "Action Items"}
              </h3>
              {actionItems.length === 0 ? (
                <p className="text-[11px] text-[var(--text-muted)]">
                  {isJa ? "\u672A\u51E6\u7406\u306E\u30A2\u30AF\u30B7\u30E7\u30F3\u306F\u3042\u308A\u307E\u305B\u3093" : "No pending actions"}
                </p>
              ) : (
                <div className="flex flex-col gap-2">
                  {actionItems.slice(0, 10).map((item, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <div
                        className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                        style={{ background: PRIORITY_COLORS[item.priority] || "var(--text-muted)" }}
                      />
                      <span className="text-[11px] text-[var(--text-secondary)]">{item.action}</span>
                    </div>
                  ))}
                  {actionItems.length > 10 && (
                    <span className="text-[10px] text-[var(--text-muted)]">
                      +{actionItems.length - 10} {isJa ? "\u4EF6" : "more"}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
