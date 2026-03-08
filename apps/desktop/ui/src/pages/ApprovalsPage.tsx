import { ShieldCheck, AlertTriangle, CheckCircle, XCircle } from "lucide-react"

const riskColors: Record<string, string> = {
  low: "#4ec9b0",
  medium: "#dcdcaa",
  high: "#f44747",
  critical: "#ff0000",
}

const riskLabels: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
  critical: "重大",
}

export function ApprovalsPage() {
  // Placeholder data
  const approvals: {
    id: string
    risk: string
    target: string
    reason: string
    requester: string
    created: string
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <ShieldCheck size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">承認待ち</h2>
        </div>

        {approvals.length === 0 ? (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
            承認待ちのリクエストはありません。
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {approvals.map((approval) => (
              <div
                key={approval.id}
                className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle
                      size={14}
                      style={{ color: riskColors[approval.risk] }}
                    />
                    <span
                      className="text-[11px] px-2 py-0.5 rounded"
                      style={{
                        background: riskColors[approval.risk] + "20",
                        color: riskColors[approval.risk],
                      }}
                    >
                      リスク: {riskLabels[approval.risk]}
                    </span>
                    <span className="text-[13px] text-[#cccccc]">
                      {approval.target}
                    </span>
                  </div>
                  <span className="text-[11px] text-[#6a6a6a]">
                    {approval.created}
                  </span>
                </div>
                <p className="text-[12px] text-[#969696] mb-3 pl-6">
                  {approval.reason}
                </p>
                <div className="flex items-center gap-2 pl-6">
                  <button className="flex items-center gap-1 px-3 py-1 rounded text-[11px] bg-[#4ec9b0] text-[#1e1e1e] hover:opacity-80">
                    <CheckCircle size={12} />
                    承認
                  </button>
                  <button className="flex items-center gap-1 px-3 py-1 rounded text-[11px] border border-[#f44747] text-[#f44747] hover:bg-[#f4474720]">
                    <XCircle size={12} />
                    却下
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
