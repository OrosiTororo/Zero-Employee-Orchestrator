import { useState, useEffect, useRef, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import { Search, ArrowRight } from "lucide-react"
import { useT } from "@/shared/i18n"

interface CommandItem {
  id: string
  label: string
  path?: string
  action?: () => void
  category: string
}

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const t = useT()

  const commands: CommandItem[] = [
    { id: "dashboard", label: t.nav.dashboard, path: "/", category: t.commandPalette.catNavigation },
    { id: "org-chart", label: t.nav.orgChart, path: "/org-chart", category: t.commandPalette.catNavigation },
    { id: "secretary", label: t.nav.secretary, path: "/secretary", category: t.commandPalette.catNavigation },
    { id: "tickets", label: t.nav.tickets, path: "/tickets", category: t.commandPalette.catNavigation },
    { id: "approvals", label: t.nav.approvals, path: "/approvals", category: t.commandPalette.catNavigation },
    { id: "artifacts", label: t.nav.artifacts, path: "/artifacts", category: t.commandPalette.catNavigation },
    { id: "heartbeats", label: t.nav.heartbeats, path: "/heartbeats", category: t.commandPalette.catNavigation },
    { id: "costs", label: t.nav.costs, path: "/costs", category: t.commandPalette.catNavigation },
    { id: "audit", label: t.nav.audit, path: "/audit", category: t.commandPalette.catNavigation },
    { id: "skills", label: t.nav.skills, path: "/skills", category: t.commandPalette.catNavigation },
    { id: "plugins", label: t.nav.plugins, path: "/plugins", category: t.commandPalette.catNavigation },
    { id: "extensions", label: t.nav.extensions, path: "/extensions", category: t.commandPalette.catNavigation },
    { id: "brainstorm", label: t.nav.brainstorm, path: "/brainstorm", category: t.commandPalette.catNavigation },
    { id: "monitor", label: t.nav.monitor, path: "/monitor", category: t.commandPalette.catNavigation },
    { id: "permissions", label: t.nav.permissions, path: "/permissions", category: t.commandPalette.catNavigation },
    { id: "settings", label: t.nav.settings, path: "/settings", category: t.commandPalette.catNavigation },
    { id: "dispatch", label: t.nav.dispatch, path: "/dispatch", category: t.commandPalette.catNavigation },
    { id: "marketplace", label: t.nav.marketplace, path: "/marketplace", category: t.commandPalette.catNavigation },
    { id: "operator-profile", label: t.nav.operatorProfile, path: "/operator-profile", category: t.commandPalette.catNavigation },
    { id: "new-skill", label: t.commandPalette.newSkill, path: "/skills/create", category: t.commandPalette.catActions },
    { id: "new-ticket", label: t.commandPalette.newTicket, path: "/tickets", category: t.commandPalette.catActions },
  ]

  const filtered = query.trim()
    ? commands.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.id.includes(query.toLowerCase())
      )
    : commands

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault()
      setOpen(prev => !prev)
      setQuery("")
      setSelectedIndex(0)
    }
    if (e.key === "Escape" && open) {
      setOpen(false)
    }
  }, [open])

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  const execute = (item: CommandItem) => {
    if (item.path) navigate(item.path)
    if (item.action) item.action()
    setOpen(false)
    setQuery("")
  }

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelectedIndex(i => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelectedIndex(i => Math.max(i - 1, 0))
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      execute(filtered[selectedIndex])
    }
  }

  if (!open) return null

  let lastCategory = ""

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh]"
      onClick={() => setOpen(false)}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" />

      {/* Palette */}
      <div className="relative w-[500px] max-h-[400px] flex flex-col rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden animate-fade-in"
        style={{ boxShadow: "var(--shadow-modal)" }}
        onClick={e => e.stopPropagation()}>
        {/* Search input */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border)]">
          <Search size={16} className="text-[var(--text-muted)] shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0) }}
            onKeyDown={handleInputKeyDown}
            placeholder={t.commandPalette.placeholder}
            className="flex-1 text-[14px] outline-none bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
            aria-label={t.commandPalette.placeholder}
          />
          <kbd className="text-[10px] text-[var(--text-muted)] border border-[var(--border)] rounded px-1.5 py-0.5">ESC</kbd>
        </div>

        {/* Results */}
        <div className="overflow-auto max-h-[320px]">
          {filtered.length === 0 ? (
            <div className="px-4 py-6 text-center text-[12px] text-[var(--text-muted)]">
              {t.commandPalette.noResults}
            </div>
          ) : (
            filtered.map((item, i) => {
              const showCategory = item.category !== lastCategory
              lastCategory = item.category

              return (
                <div key={item.id}>
                  {showCategory && (
                    <div className="px-4 pt-3 pb-1 text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
                      {item.category}
                    </div>
                  )}
                  <button
                    onClick={() => execute(item)}
                    onMouseEnter={() => setSelectedIndex(i)}
                    className="w-full flex items-center justify-between px-4 py-2 text-[13px] text-left transition-colors"
                    style={{
                      background: i === selectedIndex ? "var(--bg-active)" : "transparent",
                      color: "var(--text-primary)",
                    }}
                  >
                    <span>{item.label}</span>
                    {i === selectedIndex && <ArrowRight size={12} className="text-[var(--text-muted)]" />}
                  </button>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
