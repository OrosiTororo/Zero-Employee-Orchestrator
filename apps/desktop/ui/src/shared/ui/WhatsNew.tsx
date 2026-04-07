/**
 * "What's New" banner — shown once per version on Dashboard.
 *
 * Inspired by Claude Code's release notes pattern.
 * Dismissible, stored in localStorage by version.
 */
import { useState } from "react"
import { Sparkles, X } from "lucide-react"

const CURRENT_VERSION = "0.1.5"
const STORAGE_KEY = `zeo_whats_new_dismissed_${CURRENT_VERSION}`

const HIGHLIGHTS = [
  "Task execution engine — tickets can now be executed end-to-end via AI",
  "Desktop auto-update fixed — automatic download & install on launch",
  "Execute button on ticket detail page with real-time result display",
  "Dispatch runs tasks through the execution engine (not just ticket creation)",
]

export function WhatsNew() {
  const [visible, setVisible] = useState(() => {
    return !localStorage.getItem(STORAGE_KEY)
  })

  if (!visible) return null

  const dismiss = () => {
    localStorage.setItem(STORAGE_KEY, "1")
    setVisible(false)
  }

  return (
    <div className="rounded border border-[var(--accent)] bg-[var(--accent-subtle)] px-4 py-3 mb-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 min-w-0">
          <Sparkles size={14} className="text-[var(--accent)] mt-0.5 shrink-0" />
          <div>
            <div className="text-[12px] font-semibold text-[var(--text-primary)] mb-1">
              What's new in v{CURRENT_VERSION}
            </div>
            <ul className="space-y-0.5">
              {HIGHLIGHTS.map((h, i) => (
                <li key={i} className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                  &bull; {h}
                </li>
              ))}
            </ul>
          </div>
        </div>
        <button
          onClick={dismiss}
          className="text-[var(--text-muted)] hover:text-[var(--text-primary)] shrink-0"
          aria-label="Dismiss"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  )
}
