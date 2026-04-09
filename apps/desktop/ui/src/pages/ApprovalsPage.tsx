import { useState, useEffect, useCallback, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { ShieldCheck, AlertTriangle, CheckCircle, XCircle, ArrowRight, Eye, FileText } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"
import { useToastStore } from "@/shared/ui/ErrorToast"

interface TaskContext {
  task_id?: string | null
  ticket_id?: string | null
  task_name?: string | null
}

interface ApprovalItem {
  id: string
  operation_type: string
  target: string
  target_type?: string
  reason: string
  risk_level: string
  requester: string
  status: string
  preview?: string
  task_context?: TaskContext
  created_at?: string
}

const RISK_BADGE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  low: { bg: "rgba(34,197,94,0.12)", text: "var(--success, #22c55e)", border: "var(--success, #22c55e)" },
  medium: { bg: "rgba(234,179,8,0.12)", text: "var(--warning, #eab308)", border: "var(--warning, #eab308)" },
  high: { bg: "rgba(249,115,22,0.12)", text: "#f97316", border: "#f97316" },
  critical: { bg: "rgba(239,68,68,0.12)", text: "var(--error, #ef4444)", border: "var(--error, #ef4444)" },
}

function RiskBadge({ level, label }: { level: string; label: string }) {
  const colors = RISK_BADGE_COLORS[level] ?? RISK_BADGE_COLORS.medium
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide"
      style={{
        backgroundColor: colors.bg,
        color: colors.text,
        border: `1px solid ${colors.border}`,
      }}
    >
      {label}: {level}
    </span>
  )
}

export function ApprovalsPage() {
  const t = useT()
  const navigate = useNavigate()
  const companyId = localStorage.getItem("company_id") || ""
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedIdx, setSelectedIdx] = useState(0)
  const listRef = useRef<HTMLDivElement>(null)
  const addToast = useToastStore((s) => s.addToast)

  const fetchApprovals = useCallback(async () => {
    if (!companyId) { setLoading(false); return }
    setLoading(true)
    try {
      const data = await api.get<ApprovalItem[]>(`/companies/${companyId}/approvals?status=requested`)
      setApprovals(data)
    } catch {
      setApprovals([])
      addToast((t.approvals as Record<string, string>).loadFailed ?? "Could not load approvals.")
    } finally {
      setLoading(false)
    }
  }, [companyId, addToast])

  useEffect(() => { fetchApprovals() }, [fetchApprovals])

  // Keyboard navigation: ArrowUp/Down to select, A to approve, R to reject
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (approvals.length === 0) return
      if ((e.target as HTMLElement).tagName === "INPUT" || (e.target as HTMLElement).tagName === "TEXTAREA") return
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIdx((i) => Math.min(i + 1, approvals.length - 1))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIdx((i) => Math.max(i - 1, 0))
      } else if (e.key === "a" || e.key === "A") {
        const a = approvals[selectedIdx]
        if (a && a.status === "requested") handleApprove(a.id)
      } else if (e.key === "r" || e.key === "R") {
        const a = approvals[selectedIdx]
        if (a && a.status === "requested") handleReject(a.id)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [approvals, selectedIdx]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleApprove = async (id: string) => {
    try {
      await api.post(`/approvals/${id}/approve`, {})
      await fetchApprovals()
    } catch {
      addToast((t.approvals as Record<string, string>).approveFailed ?? "Could not approve.")
    }
  }

  const handleReject = async (id: string) => {
    const reason = prompt((t.approvals as Record<string, string>)?.rejectReason ?? "Reason for rejection:")
    if (!reason) return
    try {
      await api.post(`/approvals/${id}/reject`, { reason })
      await fetchApprovals()
    } catch {
      addToast((t.approvals as Record<string, string>).rejectFailed ?? "Could not reject.")
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.approvals.title}</h2>
          </div>
          {approvals.length > 0 && (
            <span className="text-[10px] text-[var(--text-muted)]">
              ↑↓ navigate · <kbd className="font-mono">A</kbd> approve · <kbd className="font-mono">R</kbd> reject
            </span>
          )}
        </div>

        {loading ? (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            {t.common.loading}
          </div>
        ) : approvals.length === 0 ? (
          <div className="rounded px-4 py-8 text-center border border-[var(--border)] text-[var(--text-muted)]">
            <ShieldCheck size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-[12px] mb-2">{t.approvals.emptyState}</p>
            <button
              onClick={() => navigate("/")}
              className="inline-flex items-center gap-1 text-[12px] text-[var(--accent)] hover:underline mt-1"
            >
              {t.dashboard?.requestTask ?? "Request a task"} <ArrowRight size={12} />
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-3" ref={listRef} role="list" aria-label={t.approvals.title}>
            {approvals.map((a, idx) => {
              const hasTaskContext = a.task_context && (a.task_context.task_name || a.task_context.ticket_id)
              const isSelected = idx === selectedIdx
              return (
                <div
                  key={a.id}
                  role="listitem"
                  tabIndex={0}
                  onClick={() => setSelectedIdx(idx)}
                  onFocus={() => setSelectedIdx(idx)}
                  aria-selected={isSelected}
                  className="rounded px-4 py-3 border bg-[var(--bg-surface)] cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
                  style={{ borderColor: isSelected ? "var(--accent)" : "var(--border)" }}
                >
                  {/* Header row: risk badge + operation name + timestamp */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <AlertTriangle size={14} className={a.risk_level === "critical" || a.risk_level === "high" ? "text-[var(--error)]" : "text-[var(--warning)]"} />
                      <RiskBadge level={a.risk_level} label={t.approvals.risk} />
                      <span className="text-[13px] text-[var(--text-primary)]">{a.target || a.target_type || a.operation_type}</span>
                    </div>
                    <span className="text-[11px] text-[var(--text-muted)]">{a.created_at ?? ""}</span>
                  </div>

                  {/* Action preview section */}
                  {a.preview && (
                    <div
                      className="flex items-start gap-2 rounded px-3 py-2 mb-2 ml-6 text-[12px]"
                      style={{
                        backgroundColor: "var(--bg-active, rgba(0,0,0,0.04))",
                        border: "1px solid var(--border)",
                      }}
                    >
                      <Eye size={13} className="mt-px shrink-0 text-[var(--accent)]" />
                      <div>
                        <span className="font-medium text-[var(--text-primary)]">
                          {(t.approvals as Record<string, string>).previewLabel ?? "Action Preview"}
                        </span>
                        <p className="text-[var(--text-secondary)] mt-0.5">{a.preview}</p>
                      </div>
                    </div>
                  )}

                  {/* Task context */}
                  {hasTaskContext && (
                    <div className="flex items-center gap-2 ml-6 mb-2 text-[11px] text-[var(--text-muted)]">
                      <FileText size={12} className="shrink-0" />
                      {a.task_context!.task_name && (
                        <span>
                          {(t.approvals as Record<string, string>).taskLabel ?? "Task"}: {a.task_context!.task_name}
                        </span>
                      )}
                      {a.task_context!.ticket_id && (
                        <span className="px-1.5 py-0.5 rounded bg-[var(--bg-active)] font-mono">
                          #{a.task_context!.ticket_id.slice(0, 8)}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Reason */}
                  <p className="text-[12px] text-[var(--text-secondary)] mb-3 pl-6">{a.reason}</p>

                  {/* Action buttons */}
                  <div className="flex items-center gap-2 pl-6">
                    <button
                      onClick={() => handleApprove(a.id)}
                      className="flex items-center gap-1 px-3 py-1 rounded text-[11px] bg-[var(--success)] text-white"
                      aria-label={t.approvals.approve}
                    >
                      <CheckCircle size={12} />{t.approvals.approve}
                    </button>
                    <button
                      onClick={() => handleReject(a.id)}
                      className="flex items-center gap-1 px-3 py-1 rounded text-[11px] border border-[var(--error)] text-[var(--error)]"
                      aria-label={t.approvals.reject}
                    >
                      <XCircle size={12} />{t.approvals.reject}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
