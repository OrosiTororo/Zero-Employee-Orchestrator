import type React from "react"

interface PresetCardProps {
  title: string
  subtitle?: string
  description?: string
  badges?: string[]
  icon?: React.ReactNode
  actionLabel: string
  onAction: () => void
  ariaLabel?: string
  disabled?: boolean
}

/**
 * Shared card primitive used by Templates and Crews pages (and future
 * marketplace surfaces). Matches MarketplacePage tile styling but carries
 * an explicit primary action so the card doubles as a CTA.
 */
export function PresetCard({
  title,
  subtitle,
  description,
  badges,
  icon,
  actionLabel,
  onAction,
  ariaLabel,
  disabled = false,
}: PresetCardProps) {
  return (
    <div className="rounded p-4 border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors flex flex-col">
      <div className="flex items-start justify-between mb-2 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {icon ? <span className="text-[var(--accent)] shrink-0">{icon}</span> : null}
          <span className="text-[13px] font-medium text-[var(--text-primary)] truncate">
            {title}
          </span>
        </div>
        {badges && badges.length > 0 ? (
          <div className="flex gap-1 flex-wrap justify-end">
            {badges.map((b) => (
              <span
                key={b}
                className="text-[10px] px-2 py-0.5 rounded text-[var(--text-secondary)]"
                style={{ background: "color-mix(in srgb, var(--accent) 12%, transparent)" }}
              >
                {b}
              </span>
            ))}
          </div>
        ) : null}
      </div>
      {subtitle ? (
        <div className="text-[11px] text-[var(--text-muted)] mb-1">{subtitle}</div>
      ) : null}
      {description ? (
        <p className="text-[12px] text-[var(--text-secondary)] mb-3 line-clamp-3">{description}</p>
      ) : null}
      <div className="mt-auto flex justify-end">
        <button
          onClick={onAction}
          disabled={disabled}
          aria-label={ariaLabel ?? actionLabel}
          className="px-3 py-1 rounded text-[11px] bg-[var(--accent)] text-[var(--accent-fg)] disabled:opacity-50"
        >
          {actionLabel}
        </button>
      </div>
    </div>
  )
}
