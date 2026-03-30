import { useState } from "react"
import { HeartPulse, Plus, Clock, CheckCircle, XCircle } from "lucide-react"
import { useT } from "@/shared/i18n"

export function HeartbeatsPage() {
  const t = useT()

  const [policies] = useState<{
    id: string; name: string; target: string; interval: string; enabled: boolean
  }[]>([])

  const [history] = useState<{
    id: string; policyName: string; status: "success" | "failure"; timestamp: string; duration: string
  }[]>([])

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <HeartPulse size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.heartbeats.title}</h2>
          </div>
          <button
            onClick={() => {
              // TODO: Open add policy form when heartbeat management is implemented
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)]"
            aria-label={t.heartbeats.addPolicy}
          >
            <Plus size={14} />
            {t.heartbeats.addPolicy}
          </button>
        </div>
        <p className="text-[12px] text-[var(--text-muted)] mb-6">{t.heartbeats.description}</p>

        {/* Policies */}
        <section className="mb-6">
          <h3 className="text-[11px] uppercase tracking-wider text-[var(--text-secondary)] font-medium mb-3">
            {t.heartbeats.policies}
          </h3>
          {policies.length === 0 ? (
            <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
              {t.heartbeats.emptyPolicies}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {policies.map((p) => (
                <div key={p.id} className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: p.enabled ? "var(--success-fg)" : "var(--text-muted)" }} />
                      <span className="text-[13px] text-[var(--text-primary)]">{p.name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)]">
                      <Clock size={12} />
                      <span>{p.interval}</span>
                    </div>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] mt-1 pl-4">
                    {t.heartbeats.target}: {p.target}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* History */}
        <section>
          <h3 className="text-[11px] uppercase tracking-wider text-[var(--text-secondary)] font-medium mb-3">
            {t.heartbeats.history}
          </h3>
          {history.length === 0 ? (
            <div className="rounded px-4 py-6 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
              {t.heartbeats.emptyHistory}
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              {history.map((h) => (
                <div key={h.id} className="flex items-center justify-between rounded px-4 py-2 border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center gap-2">
                    {h.status === "success"
                      ? <CheckCircle size={14} className="text-[var(--success-fg)]" />
                      : <XCircle size={14} className="text-[var(--error)]" />}
                    <span className="text-[12px] text-[var(--text-primary)]">{h.policyName}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                    <span>{h.duration}</span>
                    <span>{h.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
