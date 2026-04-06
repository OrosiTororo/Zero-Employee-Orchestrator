import { useState, useEffect } from "react"
import { Network, Building2, Bot, RefreshCw, ChevronDown, ChevronRight } from "lucide-react"
import { api } from "@/shared/api/client"
import { useT, useI18n } from "@/shared/i18n"
import { useToastStore } from "@/shared/ui/ErrorToast"

interface OrgData {
  departments: Array<{ id: string; name: string; code: string; description?: string }>
  teams: Array<{ id: string; name: string; purpose?: string; status: string }>
  agents: Array<{ id: string; name: string; title: string; status: string }>
}

export function OrgChartPage() {
  const t = useT()
  const { locale } = useI18n()
  const isJa = locale === "ja"
  const addToast = useToastStore((s) => s.addToast)

  const [orgData, setOrgData] = useState<OrgData | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedDepts, setExpandedDepts] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadOrgData()
  }, [])

  const loadOrgData = async () => {
    setLoading(true)
    try {
      const companies = await api.get<Array<{ id: string }>>("/companies")
      if (companies.length > 0) {
        const cid = companies[0].id
        const data = await api.get<OrgData>(`/companies/${cid}/org-chart`)
        setOrgData(data)
        setExpandedDepts(new Set(data.departments.map((d) => d.id)))
      }
    } catch (err) {
      addToast("Failed to load org data")
    } finally {
      setLoading(false)
    }
  }

  const toggleDept = (id: string) => {
    setExpandedDepts((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const statusColor = (status: string) => {
    switch (status) {
      case "idle": return "var(--success)"
      case "busy": return "var(--accent)"
      case "paused": return "#f59e0b"
      default: return "var(--text-muted)"
    }
  }

  const statusLabel = (status: string) => {
    const labels: Record<string, string> = isJa
      ? { idle: "\u5F85\u6A5F\u4E2D", busy: "\u5B9F\u884C\u4E2D", paused: "\u4E00\u6642\u505C\u6B62", provisioning: "\u6E96\u5099\u4E2D", decommissioned: "\u5EC3\u6B62" }
      : { idle: "Idle", busy: "Busy", paused: "Paused", provisioning: "Provisioning", decommissioned: "Decommissioned" }
    return labels[status] || status
  }

  const hasDepts = orgData && orgData.departments.length > 0

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Network size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.nav.orgChart}
            </h2>
          </div>
          <button
            onClick={loadOrgData}
            className="flex items-center gap-1 px-3 py-1.5 rounded-md text-[12px] text-[var(--text-secondary)] border border-[var(--border)] hover:bg-[var(--bg-hover)]"
          >
            <RefreshCw size={12} />
            {isJa ? "\u66F4\u65B0" : "Refresh"}
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-[13px] text-[var(--text-muted)]">
            {t.common.loading}
          </div>
        ) : !hasDepts ? (
          <div className="text-center py-16">
            <Building2 size={48} className="mx-auto mb-4 text-[var(--text-muted)]" />
            <p className="text-[13px] text-[var(--text-secondary)] mb-2">
              {isJa
                ? "\u307E\u3060\u7D44\u7E54\u304C\u69CB\u7BC9\u3055\u308C\u3066\u3044\u307E\u305B\u3093"
                : "No organization structure yet"}
            </p>
            <p className="text-[12px] text-[var(--text-muted)]">
              {isJa
                ? "\u30BB\u30C3\u30C8\u30A2\u30C3\u30D7\u30A6\u30A3\u30B6\u30FC\u30C9\u304B\u3089\u7D44\u7E54\u3092\u69CB\u7BC9\u3057\u3066\u304F\u3060\u3055\u3044"
                : "Build your organization from the Setup Wizard"}
            </p>
          </div>
        ) : (
          <>
            {/* Summary stats */}
            <div className="flex gap-4 mb-6">
              <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-3 text-center">
                <div className="text-xl font-bold text-[var(--accent)]">{orgData!.departments.length}</div>
                <div className="text-[11px] text-[var(--text-secondary)]">{isJa ? "\u90E8\u7F72" : "Departments"}</div>
              </div>
              <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-3 text-center">
                <div className="text-xl font-bold text-[var(--accent)]">{orgData!.teams.length}</div>
                <div className="text-[11px] text-[var(--text-secondary)]">{isJa ? "\u30C1\u30FC\u30E0" : "Teams"}</div>
              </div>
              <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-3 text-center">
                <div className="text-xl font-bold text-[var(--accent)]">{orgData!.agents.length}</div>
                <div className="text-[11px] text-[var(--text-secondary)]">{isJa ? "\u30A8\u30FC\u30B8\u30A7\u30F3\u30C8" : "Agents"}</div>
              </div>
            </div>

            {/* Departments */}
            <div className="mb-6">
              <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] mb-3">
                {isJa ? "\u90E8\u9580" : "DEPARTMENTS"}
              </div>
              <div className="flex flex-col gap-2">
                {orgData!.departments.map((dept) => (
                  <button
                    key={dept.id}
                    onClick={() => toggleDept(dept.id)}
                    className="w-full rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {expandedDepts.has(dept.id) ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        <Building2 size={16} className="text-[var(--accent)]" />
                        <div>
                          <div className="text-[13px] text-[var(--text-primary)]">{dept.name}</div>
                          {dept.description && (
                            <div className="text-[11px] text-[var(--text-muted)]">{dept.description}</div>
                          )}
                        </div>
                      </div>
                      <span className="text-[11px] text-[var(--text-muted)]">{dept.code}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Agents */}
            <div>
              <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] mb-3">
                {isJa ? "\u30A8\u30FC\u30B8\u30A7\u30F3\u30C8" : "AGENTS"}
              </div>
              {orgData!.agents.length === 0 ? (
                <div className="rounded px-4 py-6 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
                  {isJa
                    ? "\u30A2\u30AF\u30C6\u30A3\u30D6\u306A\u30A8\u30FC\u30B8\u30A7\u30F3\u30C8\u306F\u3044\u307E\u305B\u3093\u3002"
                    : "No active agents."}
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {orgData!.agents.map((agent) => (
                    <div
                      key={agent.id}
                      className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Bot size={16} className="text-[var(--accent)]" />
                          <div>
                            <div className="text-[13px] text-[var(--text-primary)]">{agent.name}</div>
                            <div className="text-[11px] text-[var(--text-muted)]">{agent.title}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-2 h-2 rounded-full"
                            style={{ background: statusColor(agent.status) }}
                          />
                          <span className="text-[11px] text-[var(--text-secondary)]">
                            {statusLabel(agent.status)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
