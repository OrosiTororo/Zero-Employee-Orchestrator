import { useNavigate } from "react-router-dom"
import { ShieldCheck, AlertTriangle, CheckCircle, XCircle, ArrowRight } from "lucide-react"
import { useT } from "@/shared/i18n"

export function ApprovalsPage() {
  const t = useT()
  const navigate = useNavigate()

  const approvals: {
    id: string; risk: string; target: string; reason: string; requester: string; created: string
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <ShieldCheck size={18} className="text-[var(--accent)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.approvals.title}</h2>
        </div>

        {approvals.length === 0 ? (
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
          <div className="flex flex-col gap-3">
            {approvals.map((a) => (
              <div key={a.id} className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={14} className={a.risk === "critical" || a.risk === "high" ? "text-[var(--error)]" : "text-[var(--warning)]"} />
                    <span className="text-[11px] px-2 py-0.5 rounded bg-[var(--bg-active)] text-[var(--text-primary)]">
                      {t.approvals.risk}: {a.risk}
                    </span>
                    <span className="text-[13px] text-[var(--text-primary)]">{a.target}</span>
                  </div>
                  <span className="text-[11px] text-[var(--text-muted)]">{a.created}</span>
                </div>
                <p className="text-[12px] text-[var(--text-secondary)] mb-3 pl-6">{a.reason}</p>
                <div className="flex items-center gap-2 pl-6">
                  <button className="flex items-center gap-1 px-3 py-1 rounded text-[11px] bg-[var(--success)] text-white"
                    aria-label={t.approvals.approve}>
                    <CheckCircle size={12} />{t.approvals.approve}
                  </button>
                  <button className="flex items-center gap-1 px-3 py-1 rounded text-[11px] border border-[var(--error)] text-[var(--error)]"
                    aria-label={t.approvals.reject}>
                    <XCircle size={12} />{t.approvals.reject}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
