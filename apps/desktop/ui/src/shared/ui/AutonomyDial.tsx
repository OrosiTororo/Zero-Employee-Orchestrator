/**
 * Autonomy Dial — persistent statusbar control for per-company default
 * autonomy and transient per-session overrides.
 *
 * Cowork-style: clicking opens a popover with the four canonical levels,
 * and an "Override for…" radio that flips to a transient row backed by
 * `POST /companies/{cid}/autonomy/override`. While an override is active
 * the bar shows a warning-coloured badge with the remaining time so the
 * operator never forgets they're temporarily off-default.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Gauge, X } from "lucide-react"
import { api } from "@/shared/api/client"
import { useT } from "@/shared/i18n"

type AutonomyLevel = "observe" | "assist" | "semi_auto" | "autonomous"

interface AutonomyStatus {
  company_default: AutonomyLevel
  effective: AutonomyLevel
  override_active: boolean
  override_expires_at: string | null
  override_reason: string | null
}

const LEVEL_ORDER: AutonomyLevel[] = ["observe", "assist", "semi_auto", "autonomous"]

const TTL_OPTIONS: { ttlMinutes: number | null; key: string }[] = [
  { ttlMinutes: 15, key: "override15m" },
  { ttlMinutes: 30, key: "override30m" },
  { ttlMinutes: 60, key: "override1h" },
  { ttlMinutes: null, key: "overrideUntilEnd" },
]

function formatRemaining(expiresAt: string | null): string {
  if (!expiresAt) return ""
  const ms = new Date(expiresAt).getTime() - Date.now()
  if (ms <= 0) return "0m"
  const totalMin = Math.floor(ms / 60000)
  if (totalMin < 60) return `${totalMin}m`
  const hours = Math.floor(totalMin / 60)
  const min = totalMin % 60
  return min ? `${hours}h${min}m` : `${hours}h`
}

export function AutonomyDial() {
  const t = useT()
  const companyId = typeof localStorage !== "undefined" ? localStorage.getItem("company_id") || "" : ""
  const [status, setStatus] = useState<AutonomyStatus | null>(null)
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [, setTick] = useState(0)
  const popoverRef = useRef<HTMLDivElement | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!companyId) return
    try {
      const res = await api.get<AutonomyStatus>(`/companies/${companyId}/autonomy`)
      setStatus(res)
    } catch {
      /* status bar data is non-critical */
    }
  }, [companyId])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(() => {
      fetchStatus()
      setTick((n) => n + 1)
    }, 60_000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  useEffect(() => {
    if (!open) return
    function handle(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handle)
    return () => document.removeEventListener("mousedown", handle)
  }, [open])

  const labelMap = useMemo(
    () => ({
      observe: t.autonomy?.observe ?? "Observe",
      assist: t.autonomy?.assist ?? "Assist",
      semi_auto: t.autonomy?.semiAuto ?? "Semi-Auto",
      autonomous: t.autonomy?.autonomous ?? "Autonomous",
    }),
    [t]
  )

  const setDefault = async (level: AutonomyLevel) => {
    if (!companyId || busy) return
    setBusy(true)
    try {
      await api.patch(`/companies/${companyId}/autonomy`, { level })
      await fetchStatus()
    } finally {
      setBusy(false)
    }
  }

  const setOverride = async (level: AutonomyLevel, ttlMinutes: number | null) => {
    if (!companyId || busy) return
    setBusy(true)
    try {
      await api.post(`/companies/${companyId}/autonomy/override`, {
        level,
        ttl_minutes: ttlMinutes,
        until_session_end: ttlMinutes === null,
      })
      await fetchStatus()
    } finally {
      setBusy(false)
    }
  }

  const clearOverride = async () => {
    if (!companyId || busy) return
    setBusy(true)
    try {
      await api.delete(`/companies/${companyId}/autonomy/override`)
      await fetchStatus()
    } finally {
      setBusy(false)
    }
  }

  if (!companyId || !status) {
    return (
      <button
        className="flex items-center gap-1.5 px-3 h-full"
        title={t.autonomy?.tooltip ?? "Autonomy level"}
        disabled
      >
        <Gauge size={11} />
        <span>--</span>
      </button>
    )
  }

  const overrideRemaining = status.override_active ? formatRemaining(status.override_expires_at) : ""
  const badgeStyle: React.CSSProperties = status.override_active
    ? { background: "color-mix(in srgb, var(--warning) 18%, transparent)", color: "var(--warning-fg)" }
    : {}

  return (
    <div className="relative h-full">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 px-3 h-full transition-colors hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
        style={{ color: "inherit", ...badgeStyle }}
        title={t.autonomy?.tooltip ?? "Click to change autonomy level"}
        aria-haspopup="dialog"
        aria-expanded={open}
      >
        <Gauge size={11} />
        <span>{labelMap[status.effective]}</span>
        {status.override_active && (
          <span
            className="ml-1 text-[10px]"
            aria-label={t.autonomy?.overrideActive ?? "Override active"}
          >
            ({overrideRemaining})
          </span>
        )}
      </button>

      {open && (
        <div
          ref={popoverRef}
          role="dialog"
          aria-label={t.autonomy?.tooltip ?? "Autonomy level"}
          className="menu-surface absolute bottom-full right-0 mb-1.5 w-[288px] text-[var(--text-primary)] z-50 animate-scale-in overflow-hidden"
        >
          <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-[var(--border)]">
            <span className="text-[12px] font-semibold">
              {t.autonomy?.tooltip ?? "Autonomy level"}
            </span>
            <button
              onClick={() => setOpen(false)}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              aria-label="Close"
            >
              <X size={12} />
            </button>
          </div>

          <div className="px-3.5 py-2.5 space-y-2">
            <div className="text-[10px] uppercase tracking-[0.08em] font-semibold text-[var(--text-muted)]">
              {t.autonomy?.companyDefault ?? "Company default"}
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {LEVEL_ORDER.map((level) => {
                const active = status.company_default === level
                return (
                  <button
                    key={level}
                    onClick={() => setDefault(level)}
                    disabled={busy}
                    className={`text-[11.5px] px-2 py-1.5 rounded-md border transition-colors ${
                      active
                        ? "border-transparent bg-[var(--accent-subtle)] text-[var(--accent)] font-semibold"
                        : "border-[var(--border)] hover:bg-[var(--bg-hover)]"
                    }`}
                  >
                    {labelMap[level]}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="px-3.5 py-2.5 border-t border-[var(--border)] space-y-2">
            <div className="text-[10px] uppercase tracking-[0.08em] font-semibold text-[var(--text-muted)]">
              {t.autonomy?.overrideFor ?? "Override for"}
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {TTL_OPTIONS.map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => setOverride(status.company_default, opt.ttlMinutes)}
                  disabled={busy}
                  className="text-[11.5px] px-2 py-1.5 rounded-md border border-[var(--border)] transition-colors hover:bg-[var(--bg-hover)]"
                >
                  {(t.autonomy as Record<string, string> | undefined)?.[opt.key] ?? opt.key}
                </button>
              ))}
            </div>
            {status.override_active && (
              <button
                onClick={clearOverride}
                disabled={busy}
                className="w-full text-[11.5px] px-2 py-1.5 rounded-md transition-colors"
                style={{
                  background: "color-mix(in srgb, var(--warning) 14%, transparent)",
                  color: "var(--warning-fg)",
                }}
              >
                {t.autonomy?.clearOverride ?? "Clear override"} (
                {overrideRemaining} {t.autonomy?.overrideExpiresIn ?? "left"})
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
