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
      <div className="absolute inset-0 bg-black/55" />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        className="relative flex flex-col rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden outline-none"
        style={{ width: widthPx, maxWidth: "92vw", boxShadow: "var(--shadow-modal)" }}
      >
        <header className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
          <h2 id={labelId} className="text-[13px] font-medium text-[var(--text-primary)]">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            aria-label={t.common.close ?? "Close"}
          >
            <X size={14} />
          </button>
        </header>
        <div className="px-4 py-3 overflow-auto max-h-[60vh]">{children}</div>
        {footer ? (
          <footer className="flex items-center justify-end gap-2 px-4 py-3 border-t border-[var(--border)]">
            {footer}
          </footer>
        ) : null}
      </div>
    </div>
  )
}
