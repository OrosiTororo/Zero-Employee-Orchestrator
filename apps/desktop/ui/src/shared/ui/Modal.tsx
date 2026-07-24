import { useEffect, useRef } from "react"
import { X } from "lucide-react"
import { useT } from "@/shared/i18n"

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  footer?: React.ReactNode
  labelledBy?: string
  widthPx?: number
}

/**
 * Lightweight accessible dialog.
 *
 * - `role="dialog"` + `aria-modal="true"` + focus trap on mount
 * - Esc closes, backdrop click closes
 * - Tab stays inside the dialog
 * - Restores focus to the previously-focused element on close
 */
export function Modal({ open, onClose, title, children, footer, labelledBy, widthPx = 480 }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)
  const t = useT()

  useEffect(() => {
    if (!open) return
    previouslyFocused.current = document.activeElement as HTMLElement | null
    const el = dialogRef.current
    el?.focus()
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault()
        onClose()
      }
      if (e.key === "Tab" && el) {
        const focusables = el.querySelectorAll<HTMLElement>(
          'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])',
        )
        if (focusables.length === 0) return
        const first = focusables[0]
        const last = focusables[focusables.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    window.addEventListener("keydown", onKey)
    return () => {
      window.removeEventListener("keydown", onKey)
      previouslyFocused.current?.focus?.()
    }
  }, [open, onClose])

  if (!open) return null
  const labelId = labelledBy ?? "modal-title"

  return (
    <div
      className="fixed inset-0 z-[120] flex items-start justify-center pt-[12vh]"
      onClick={onClose}
    >
      <div className="absolute inset-0" style={{ background: "var(--scrim)" }} />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        className="relative flex flex-col rounded-xl border border-[var(--border)] bg-[var(--bg-overlay)] overflow-hidden outline-none animate-scale-in"
        style={{ width: widthPx, maxWidth: "92vw", boxShadow: "var(--shadow-modal)" }}
      >
        <header className="flex items-center justify-between px-5 pt-4 pb-3">
          <h2 id={labelId} className="text-[15px] font-semibold text-[var(--text-primary)]">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-6 h-6 rounded-full text-[var(--text-muted)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
            aria-label={t.common.close ?? "Close"}
          >
            <X size={14} />
          </button>
        </header>
        <div className="px-5 pb-4 overflow-auto max-h-[60vh]">{children}</div>
        {footer ? (
          <footer className="flex items-center justify-end gap-2 px-5 py-3.5 border-t border-[var(--border)] bg-[var(--bg-raised)]">
            {footer}
          </footer>
        ) : null}
      </div>
    </div>
  )
}
