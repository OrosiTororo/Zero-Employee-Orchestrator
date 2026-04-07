import { useState, useEffect, useCallback } from "react"
import { HeartPulse, Plus, Clock, CheckCircle, XCircle } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

interface HeartbeatPolicy {
  id: string
  name: string
  target_agent_id?: string
  cron_expression?: string
  interval_minutes?: number
  enabled: boolean
}

interface HeartbeatRun {
  id: string
  policy_id: string
  status: string
  summary?: string
  created_at?: string
  duration_ms?: number
}

export function HeartbeatsPage() {
  const t = useT()
  const companyId = localStorage.getItem("company_id") || ""
  const [policies, setPolicies] = useState<HeartbeatPolicy[]>([])
  const [history, setHistory] = useState<HeartbeatRun[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    if (!companyId) { setLoading(false); return }
    setLoading(true)
    try {
      const [p, h] = await Promise.all([
        api.get<HeartbeatPolicy[]>(`/companies/${companyId}/heartbeat-policies`).catch((e) => { console.warn("Heartbeat policies:", e); return [] }),
        api.get<HeartbeatRun[]>(`/companies/${companyId}/heartbeat-runs`).catch((e) => { console.warn("Heartbeat runs:", e); return [] }),
      ])
      setPolicies(p)
      setHistory(h)
    } finally {
      setLoading(false)
    }
  }, [companyId])

  useEffect(() => { fetchData() }, [fetchData])

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <HeartPulse size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.heartbeats.title}</h2>
          </div>
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)]"
            aria-label={t.heartbeats.addPolicy}
          >
            <Plus size={14} />
            {t.heartbeats.addPolicy}
          </button>
        </div>
        <p className="text-[12px] text-[var(--text-muted)] mb-6">{t.heartbeats.description}</p>

        <section className="mb-6">
          <h3 className="text-[11px] uppercase tracking-wider text-[var(--text-secondary)] font-medium mb-3">
            {t.heartbeats.policies}
          </h3>
          {loading ? (
            <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
              {t.common.loading}
            </div>
          ) : policies.length === 0 ? (
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
                      <span>{p.cron_expression ?? `${p.interval_minutes ?? 60}min`}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

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
                    <span className="text-[12px] text-[var(--text-primary)]">{h.summary ?? h.policy_id.slice(0, 8)}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                    {h.duration_ms != null && <span>{h.duration_ms}ms</span>}
                    <span>{h.created_at ?? ""}</span>
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
