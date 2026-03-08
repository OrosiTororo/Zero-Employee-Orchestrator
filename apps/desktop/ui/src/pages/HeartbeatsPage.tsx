import { HeartPulse, Clock, CheckCircle, XCircle, Plus } from "lucide-react"

export function HeartbeatsPage() {
  // Placeholder data
  const policies: {
    id: string
    name: string
    interval: string
    target: string
    enabled: boolean
  }[] = []

  const history: {
    id: string
    policyName: string
    status: "success" | "failure"
    timestamp: string
    duration: string
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <HeartPulse size={18} className="text-[#007acc]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              ハートビート
            </h2>
          </div>
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white">
            <Plus size={14} />
            ポリシー追加
          </button>
        </div>

        {/* Policies */}
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-3">
            ポリシー
          </div>
          {policies.length === 0 ? (
            <div className="rounded px-4 py-6 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
              ハートビートポリシーはまだ設定されていません。定期的な監視チェックを追加してください。
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {policies.map((p) => (
                <div
                  key={p.id}
                  className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{
                          background: p.enabled ? "#4ec9b0" : "#6a6a6a",
                        }}
                      />
                      <span className="text-[13px] text-[#cccccc]">
                        {p.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-[#6a6a6a]">
                      <Clock size={12} />
                      <span>{p.interval}</span>
                    </div>
                  </div>
                  <div className="text-[11px] text-[#6a6a6a] mt-1 pl-4">
                    対象: {p.target}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Run History */}
        <div>
          <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-3">
            実行履歴
          </div>
          {history.length === 0 ? (
            <div className="rounded px-4 py-6 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
              実行履歴はありません。
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              {history.map((h) => (
                <div
                  key={h.id}
                  className="flex items-center justify-between rounded px-4 py-2 border border-[#3e3e42] bg-[#252526]"
                >
                  <div className="flex items-center gap-2">
                    {h.status === "success" ? (
                      <CheckCircle size={14} className="text-[#4ec9b0]" />
                    ) : (
                      <XCircle size={14} className="text-[#f44747]" />
                    )}
                    <span className="text-[13px] text-[#cccccc]">
                      {h.policyName}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-[#6a6a6a]">
                    <span>{h.duration}</span>
                    <span>{h.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
