import { useState, useEffect, useCallback } from "react"
import {
  Activity,
  Bot,
  Clock,
  Cpu,
  AlertTriangle,
  MessageSquare,
  Zap,
  RefreshCw,
  Shield,
  Brain,
  PauseCircle,
  PlayCircle,
} from "lucide-react"
import { api } from "../shared/api/client"

interface ActiveExecution {
  task_id: string
  agent_id: string
  company_id: string
  started_at: number
  status: string
  progress_pct: number
  current_step: string
  model_used: string | null
  tokens_used: number
  cost_usd: number
  elapsed_ms: number
}

interface MonitorSummary {
  active_executions: number
  total_events: number
  recent_errors: number
  recent_escalations: number
  active_agents: string[]
}

interface Session {
  session_id: string
  agent_id: string
  role: string
  status: string
  message_count: number
  round_count: number
  started_at: number
  last_active_at: number
  idle_since: number | null
}

interface Hypothesis {
  hypothesis_id: string
  title: string
  status: string
  support_score: number
  review_consensus: string
  evidence_count: number
  review_count: number
  proposer_agent_id: string
}

interface SentryStats {
  total_events: number
  errors_last_hour: number
  errors_last_24h: number
  error_types: Record<string, number>
  sdk_available: boolean
}

export function AgentMonitorPage() {
  const [summary, setSummary] = useState<MonitorSummary | null>(null)
  const [active, setActive] = useState<ActiveExecution[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [sentryStats, setSentryStats] = useState<SentryStats | null>(null)
  const [tab, setTab] = useState<"monitor" | "sessions" | "hypotheses" | "errors">("monitor")

  const fetchData = useCallback(async () => {
    try {
      const [dashboard, sessionData, hypoData, sentry] = await Promise.all([
        api.get<{ summary: MonitorSummary; active: ActiveExecution[] }>("/monitor/dashboard").catch(() => null),
        api.get<{ sessions: Session[] }>("/sessions").catch(() => ({ sessions: [] })),
        api.get<{ hypotheses: Hypothesis[] }>("/hypotheses").catch(() => ({ hypotheses: [] })),
        api.get<SentryStats>("/sentry/stats").catch(() => null),
      ])
      if (dashboard) {
        setSummary(dashboard.summary)
        setActive(dashboard.active)
      }
      setSessions(sessionData.sessions)
      setHypotheses(hypoData.hypotheses)
      if (sentry) setSentryStats(sentry)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // Auto-refresh every 5 seconds
  useEffect(() => {
    const timer = setInterval(fetchData, 5000)
    return () => clearInterval(timer)
  }, [fetchData])

  const tabs = [
    { key: "monitor" as const, label: "実行監視", icon: Activity },
    { key: "sessions" as const, label: "セッション", icon: Brain },
    { key: "hypotheses" as const, label: "仮説検証", icon: Zap },
    { key: "errors" as const, label: "エラー監視", icon: AlertTriangle },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1000px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
              エージェント監視ダッシュボード
            </h1>
            <p className="text-[12px] text-[var(--text-muted)] mt-0.5">
              ブラウザからリアルタイムでエージェントの状態を監視
            </p>
          </div>
          <button onClick={fetchData} className="p-2 rounded-md hover:bg-[var(--bg-hover)]">
            <RefreshCw size={14} />
          </button>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-4 gap-3 mb-6">
            <StatCard icon={Cpu} label="実行中タスク" value={String(summary.active_executions)} color="var(--accent)" />
            <StatCard icon={Bot} label="アクティブエージェント" value={String(summary.active_agents.length)} color="var(--success-fg)" />
            <StatCard icon={AlertTriangle} label="直近エラー" value={String(summary.recent_errors)} color="var(--error)" />
            <StatCard icon={MessageSquare} label="エスカレーション" value={String(summary.recent_escalations)} color="var(--warning)" />
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-[var(--border)]">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 px-4 py-2 text-[12px] border-b-2 transition-colors ${
                tab === key
                  ? "border-[var(--accent)] text-[var(--accent)]"
                  : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              <Icon size={13} />
              {label}
            </button>
          ))}
        </div>

        {/* Monitor Tab */}
        {tab === "monitor" && (
          <div className="space-y-3">
            {active.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                現在実行中のタスクはありません
              </div>
            ) : (
              active.map(exec => (
                <div key={exec.task_id} className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Cpu size={14} className="text-[var(--accent)]" />
                      <span className="text-[12px] font-medium text-[var(--text-primary)]">
                        {exec.task_id.slice(0, 8)}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent)] text-white">
                        {exec.status}
                      </span>
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
                      <Clock size={10} />
                      {Math.round(exec.elapsed_ms / 1000)}s
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)]">
                    <span>Agent: {exec.agent_id.slice(0, 8)}</span>
                    {exec.model_used && <span>Model: {exec.model_used}</span>}
                    <span>Tokens: {exec.tokens_used}</span>
                    <span>Cost: ${exec.cost_usd.toFixed(4)}</span>
                  </div>
                  {exec.current_step && (
                    <div className="mt-2 text-[11px] text-[var(--text-secondary)]">
                      {exec.current_step}
                    </div>
                  )}
                  <div className="mt-2 w-full bg-[var(--border)] rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-[var(--accent)]"
                      style={{ width: `${exec.progress_pct}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Sessions Tab */}
        {tab === "sessions" && (
          <div className="space-y-3">
            {sessions.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                アクティブなセッションはありません
              </div>
            ) : (
              sessions.map(s => (
                <div key={s.session_id} className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {s.status === "idle" ? (
                        <PauseCircle size={14} className="text-[var(--warning)]" />
                      ) : (
                        <PlayCircle size={14} className="text-[var(--success-fg)]" />
                      )}
                      <span className="text-[12px] font-medium text-[var(--text-primary)]">
                        {s.agent_id}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-active)] text-[var(--text-secondary)]">
                        {s.role}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        s.status === "active" ? "bg-green-100 text-green-700" :
                        s.status === "idle" ? "bg-yellow-100 text-yellow-700" :
                        "bg-gray-100 text-gray-700"
                      }`}>{s.status}</span>
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      Round {s.round_count} / {s.message_count} msgs
                    </span>
                  </div>
                  {s.idle_since && (
                    <div className="text-[11px] text-[var(--text-muted)]">
                      Idle: {Math.round((Date.now() / 1000 - s.idle_since) / 60)}分前からコンテキスト保持中
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Hypotheses Tab */}
        {tab === "hypotheses" && (
          <div className="space-y-3">
            {hypotheses.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                アクティブな仮説はありません
              </div>
            ) : (
              hypotheses.map(h => (
                <div key={h.hypothesis_id} className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[12px] font-medium text-[var(--text-primary)]">
                      {h.title}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      h.status === "confirmed" ? "bg-green-100 text-green-700" :
                      h.status === "refuted" ? "bg-red-100 text-red-700" :
                      h.status === "investigating" ? "bg-blue-100 text-blue-700" :
                      "bg-yellow-100 text-yellow-700"
                    }`}>{h.status}</span>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)]">
                    <span>支持スコア: {(h.support_score * 100).toFixed(0)}%</span>
                    <span>コンセンサス: {h.review_consensus}</span>
                    <span>エビデンス: {h.evidence_count}</span>
                    <span>レビュー: {h.review_count}</span>
                    <span>提案: {h.proposer_agent_id.slice(0, 8)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Errors Tab (Sentry) */}
        {tab === "errors" && sentryStats && (
          <div>
            <div className="grid grid-cols-3 gap-3 mb-6">
              <StatCard icon={AlertTriangle} label="直近1時間のエラー" value={String(sentryStats.errors_last_hour)} color="var(--error)" />
              <StatCard icon={AlertTriangle} label="直近24時間のエラー" value={String(sentryStats.errors_last_24h)} color="var(--warning)" />
              <StatCard icon={Shield} label="Sentry SDK" value={sentryStats.sdk_available ? "接続済" : "ビルトイン"} color="var(--success-fg)" />
            </div>

            {Object.keys(sentryStats.error_types).length > 0 ? (
              <div className="rounded-md border border-[var(--border)] bg-[var(--bg-surface)] p-4">
                <h3 className="text-[12px] font-medium text-[var(--text-primary)] mb-3">エラータイプ別集計</h3>
                <div className="space-y-2">
                  {Object.entries(sentryStats.error_types).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-[12px]">
                      <span className="text-[var(--text-primary)] font-mono">{type}</span>
                      <span className="text-[var(--error)] font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                直近のエラーはありません
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ size?: number }>
  label: string
  value: string
  color: string
}) {
  return (
    <div className="px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon size={13} />
        <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">{label}</span>
      </div>
      <div className="text-[18px] font-semibold" style={{ color }}>{value}</div>
    </div>
  )
}
