import { Coins, TrendingUp, ShieldAlert, Receipt } from "lucide-react"
import { useT } from "@/shared/i18n"

export function CostsPage() {
  const t = useT()

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <Coins size={18} className="text-[var(--warning)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.costs.title}</h2>
        </div>

        {/* Budget Policies */}
        <section className="mb-6 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
            <ShieldAlert size={14} className="text-[var(--warning)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.costs.budgetPolicies}</span>
          </div>
          <div className="px-4 py-4">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="rounded p-3 border border-[var(--border)] bg-[var(--bg-base)]">
                <div className="text-[11px] text-[var(--text-muted)] mb-1">{t.costs.dailyLimit}</div>
                <div className="text-[16px] font-semibold text-[var(--text-primary)]">{t.costs.notSet}</div>
              </div>
              <div className="rounded p-3 border border-[var(--border)] bg-[var(--bg-base)]">
                <div className="text-[11px] text-[var(--text-muted)] mb-1">{t.costs.weeklyLimit}</div>
                <div className="text-[16px] font-semibold text-[var(--text-primary)]">{t.costs.notSet}</div>
              </div>
              <div className="rounded p-3 border border-[var(--border)] bg-[var(--bg-base)]">
                <div className="text-[11px] text-[var(--text-muted)] mb-1">{t.costs.monthlyLimit}</div>
                <div className="text-[16px] font-semibold text-[var(--text-primary)]">{t.costs.notSet}</div>
              </div>
            </div>
            <div className="text-[12px] text-[var(--text-muted)]">{t.costs.budgetDesc}</div>
          </div>
        </section>

        {/* Spending Breakdown */}
        <section className="mb-6 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
            <TrendingUp size={14} className="text-[var(--accent)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.costs.spending}</span>
          </div>
          <div className="px-4 py-4">
            <div className="grid grid-cols-4 gap-4 mb-4">
              {[
                { label: t.costs.today, value: "$0.00" },
                { label: t.costs.thisWeek, value: "$0.00" },
                { label: t.costs.thisMonth, value: "$0.00" },
                { label: t.costs.total, value: "$0.00" },
              ].map((item, i) => (
                <div key={i}>
                  <div className="text-[11px] text-[var(--text-muted)]">{item.label}</div>
                  <div className="text-[18px] font-semibold text-[var(--text-primary)]">{item.value}</div>
                </div>
              ))}
            </div>
            <div className="text-center text-[12px] text-[var(--text-muted)] py-4 border-t border-[var(--border)]">
              {t.costs.breakdownHint}
            </div>
          </div>
        </section>

        {/* Cost Ledger */}
        <section className="rounded border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
            <Receipt size={14} className="text-[var(--accent)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.costs.ledger}</span>
          </div>
          <div className="px-4">
            <div className="grid grid-cols-5 gap-2 py-2 text-[11px] text-[var(--text-muted)] border-b border-[var(--border)] font-medium">
              <span>{t.costs.dateTime}</span>
              <span>{t.costs.ticket}</span>
              <span>{t.costs.model}</span>
              <span>{t.costs.tokens}</span>
              <span className="text-right">{t.costs.cost}</span>
            </div>
            <div className="py-6 text-center text-[12px] text-[var(--text-muted)]">
              {t.costs.emptyState}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
