import { useState, useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import {
  Send,
  Sparkles,
  Ticket,
  ShieldCheck,
  Bot,
  HeartPulse,
  Coins,
  AlertTriangle,
  Lightbulb,
  Target,
} from "lucide-react"
import { api } from "../shared/api/client"

export function DashboardPage() {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [activeTickets, setActiveTickets] = useState(0)
  const [pendingApprovals, setPendingApprovals] = useState(0)
  const [agentStatus, setAgentStatus] = useState("0 / 0")
  const navigate = useNavigate()
  const companyId = localStorage.getItem("company_id") || ""

  const fetchStats = useCallback(async () => {
    if (!companyId) return
    try {
      const [tickets, approvals, agents] = await Promise.all([
        api.get<any[]>(`/companies/${companyId}/tickets?status=in_progress`).catch(() => []),
        api.get<any[]>(`/approvals?status=requested`).catch(() => []),
        api.get<any[]>(`/companies/${companyId}/agents`).catch(() => []),
      ])
      setActiveTickets(tickets.length)
      setPendingApprovals(approvals.length)
      const active = agents.filter((a: any) => a.status === "active").length
      setAgentStatus(`${active} / ${agents.length}`)
    } catch {
      // Stats will remain at defaults
    }
  }, [companyId])

  useEffect(() => { fetchStats() }, [fetchStats])

  const handleSubmit = async () => {
    if (!input.trim() || loading) return
    setLoading(true)
    try {
      if (companyId) {
        const ticket = await api.post<{ id: string }>(`/companies/${companyId}/tickets`, {
          title: input.trim(),
          description: input.trim(),
          priority: "medium",
          source_type: "user",
        })
        navigate(`/tickets/${ticket.id}/interview`)
      } else {
        navigate("/tickets")
      }
    } catch (e) {
      console.error("Failed:", e)
      navigate("/tickets")
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Natural Language Input */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={18} className="text-[#007acc]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              業務を依頼する
            </h2>
          </div>
          <div className="rounded overflow-hidden border border-[#3e3e42] bg-[#252526]">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="例: 新規顧客向けのオンボーディングフローを設計してください"
              className="w-full resize-none px-4 py-3 text-[13px] outline-none bg-transparent text-[#cccccc]"
              style={{ minHeight: "80px" }}
              rows={3}
            />
            <div className="flex items-center justify-end px-4 py-2 border-t border-[#3e3e42]">
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded text-[12px] transition-colors"
                style={{
                  background: input.trim() && !loading ? "#007acc" : "#3e3e42",
                  color: "#ffffff",
                  cursor: input.trim() && !loading ? "pointer" : "not-allowed",
                }}
              >
                <Send size={13} />
                {loading ? "送信中..." : "依頼する"}
              </button>
            </div>
          </div>
        </div>

        {/* Company Mission */}
        <div className="mb-6 rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 mb-1">
            <Target size={14} className="text-[#007acc]" />
            <span className="text-[11px] uppercase tracking-wider text-[#6a6a6a]">
              企業ミッション
            </span>
          </div>
          <p className="text-[13px] text-[#cccccc]">
            まだミッションが設定されていません。設定画面から登録してください。
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <SummaryCard
            icon={Ticket}
            label="アクティブチケット"
            value={String(activeTickets)}
            sub="進行中のタスク"
            onClick={() => navigate("/tickets")}
          />
          <SummaryCard
            icon={ShieldCheck}
            label="承認待ち"
            value={String(pendingApprovals)}
            sub="要対応"
            onClick={() => navigate("/approvals")}
          />
          <SummaryCard
            icon={Bot}
            label="エージェント稼働状況"
            value={agentStatus}
            sub="アクティブ / 全体"
            onClick={() => navigate("/org-chart")}
          />
          <SummaryCard
            icon={HeartPulse}
            label="ハートビート"
            value="正常"
            sub="最終チェック: --"
            onClick={() => navigate("/heartbeats")}
          />
        </div>

        {/* Cost Summary */}
        <div className="mb-6 rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 mb-2">
            <Coins size={14} className="text-[#dcdcaa]" />
            <span className="text-[11px] uppercase tracking-wider text-[#6a6a6a]">
              コストサマリー
            </span>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-[18px] font-semibold text-[#cccccc]">
                $0.00
              </div>
              <div className="text-[11px] text-[#6a6a6a]">今日</div>
            </div>
            <div>
              <div className="text-[18px] font-semibold text-[#cccccc]">
                $0.00
              </div>
              <div className="text-[11px] text-[#6a6a6a]">今週</div>
            </div>
            <div>
              <div className="text-[18px] font-semibold text-[#cccccc]">
                $0.00
              </div>
              <div className="text-[11px] text-[#6a6a6a]">今月</div>
            </div>
          </div>
        </div>

        {/* Errors / Blocks */}
        <div className="mb-6 rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-[#f44747]" />
            <span className="text-[11px] uppercase tracking-wider text-[#6a6a6a]">
              エラー / ブロック
            </span>
          </div>
          <p className="text-[12px] text-[#6a6a6a]">
            現在エラーやブロックされたタスクはありません。
          </p>
        </div>

        {/* Recommended Actions */}
        <div className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb size={14} className="text-[#4ec9b0]" />
            <span className="text-[11px] uppercase tracking-wider text-[#6a6a6a]">
              推奨アクション
            </span>
          </div>
          <ul className="flex flex-col gap-1">
            <li className="text-[12px] text-[#cccccc] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#007acc]" />
              企業ミッションを設定する
            </li>
            <li className="text-[12px] text-[#cccccc] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#007acc]" />
              プロバイダー接続を構成する
            </li>
            <li className="text-[12px] text-[#cccccc] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#007acc]" />
              最初のチケットを作成する
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  sub,
  onClick,
}: {
  icon: React.ComponentType<{ size?: number }>
  label: string
  value: string
  sub: string
  onClick?: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="rounded px-4 py-3 text-left border border-[#3e3e42] bg-[#252526] hover:border-[#007acc] transition-colors"
    >
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} />
        <span className="text-[11px] uppercase tracking-wider text-[#6a6a6a]">
          {label}
        </span>
      </div>
      <div className="text-[20px] font-semibold text-[#cccccc]">{value}</div>
      <div className="text-[11px] text-[#6a6a6a]">{sub}</div>
    </button>
  )
}
