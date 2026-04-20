import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  /** Small graphic / icon to show above the title. */
  icon?: ReactNode
  /** Primary action — rendered as a filled button. */
  action?: {
    label: string
    onClick: () => void
  }
  /** Secondary action — rendered as a subtle link-style button. */
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  /** Compact variant: shorter padding + smaller type. Use inside cards. */
  compact?: boolean
  className?: string
}

/**
 * Consistent empty-state panel for list views that have no data yet.
 *
 * The goal is to always give the user a concrete next action — a page that
 * says "no tickets yet" without a call-to-action is dead weight. Consumers
 * that truly have no next step (offline, gated by permission) should pass
 * `description` to explain the situation instead of leaving the panel blank.
 */
export function EmptyState({
  title,
  description,
  icon,
  action,
  secondaryAction,
  compact = false,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex flex-col items-center justify-center text-center ${
        compact ? 'py-6 px-4' : 'py-12 px-6'
      } ${className}`}
    >
      {icon ? (
        <div
          aria-hidden="true"
          className={`mb-3 text-[var(--text-muted)] ${
            compact ? 'text-[24px]' : 'text-[32px]'
          }`}
        >
          {icon}
        </div>
      ) : null}
      <h3
        className={`font-semibold text-[var(--text-primary)] ${
          compact ? 'text-[13px]' : 'text-[14px]'
        }`}
      >
        {title}
      </h3>
      {description ? (
        <p
          className={`mt-1 max-w-sm text-[var(--text-secondary)] ${
            compact ? 'text-[11px]' : 'text-[12px]'
          }`}
        >
          {description}
        </p>
      ) : null}
      {action || secondaryAction ? (
        <div className="mt-4 flex items-center gap-2">
          {action ? (
            <button
              type="button"
              onClick={action.onClick}
              className="px-3 py-1.5 text-[12px] rounded-md bg-[var(--accent)] text-[var(--accent-fg)] hover:opacity-90"
            >
              {action.label}
            </button>
          ) : null}
          {secondaryAction ? (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className="px-3 py-1.5 text-[12px] rounded-md text-[var(--accent)] hover:bg-[var(--accent-subtle)]"
            >
              {secondaryAction.label}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
