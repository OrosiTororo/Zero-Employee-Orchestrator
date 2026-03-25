import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
  FileText,
  GitCompare,
  ListTree,
  Coins,
  Link,
  ArrowLeft,
  Play,
  Loader2,
  CheckCircle,
  AlertTriangle,
} from "lucide-react"
import { api } from "../shared/api/client"

interface Spec {
  id: string
  objective: string
  constraints_json: Record<string, unknown>
  acceptance_criteria_json: string[]
  risk_notes: string
  version: number
}

interface Plan {
  id: string
  title: string
  estimated_cost_usd: number
  estimated_minutes: number
  status: string
}

interface TaskNode {
  id: string
  title: string
  task_type: string
  status: string
  depends_on: string[]
  requires_approval: boolean
  estimated_cost_usd: number
  estimated_minutes: number
}

export function SpecPlanPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [spec, setSpec] = useState<Spec | null>(null)
  const [, setPlan] = useState<Plan | null>(null)
  const [tasks, setTasks] = useState<TaskNode[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    loadData()
  }, [id])

  async function loadData() {
    setLoading(true)
    setError("")
    try {
      const companyId = localStorage.getItem("company_id") || ""
      // Load spec
      try {
        const specData = await api.get<Spec>(
          `/companies/${companyId}/tickets/${id}/spec`
        )
        setSpec(specData)
      } catch {
        // No spec yet
      }
      // Load plan
      try {
        const planData = await api.get<Plan>(
          `/companies/${companyId}/tickets/${id}/plan`
        )
        setPlan(planData)
      } catch {
        // No plan yet
      }
      // Load tasks
      try {
        const taskData = await api.get<{ tasks: TaskNode[] }>(
          `/companies/${companyId}/tickets/${id}/tasks`
        )
        setTasks(taskData.tasks || [])
      } catch {
        // No tasks yet
      }
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerateSpec() {
    setGenerating(true)
    setError("")
    try {
      const companyId = localStorage.getItem("company_id") || ""
      const result = await api.post<Spec>(
        `/companies/${companyId}/tickets/${id}/generate-spec`
      )
      setSpec(result)
      await loadData()
    } catch (e) {
      setError(String(e))
    } finally {
      setGenerating(false)
    }
  }

  const totalCost = tasks.reduce((sum, t) => sum + (t.estimated_cost_usd || 0), 0)
  const totalMinutes = tasks.reduce((sum, t) => sum + (t.estimated_minutes || 0), 0)
  const approvalPoints = tasks.filter((t) => t.requires_approval).length

  const statusColors: Record<string, string> = {
    pending: "text-[#6a6a6a]",
    ready: "text-[#007acc]",
    running: "text-[#dcdcaa]",
    succeeded: "text-[#4ec9b0]",
    failed: "text-[#f44747]",
    awaiting_approval: "text-[#ce9178]",
    blocked: "text-[#f44747]",
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate(`/tickets/${id}`)}
            className="text-[#6a6a6a] hover:text-[#cccccc]"
          >
            <ArrowLeft size={18} />
          </button>
          <FileText size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">
            仕様・計画: チケット {id?.slice(0, 8)}
          </h2>
          {!spec && !loading && (
            <button
              onClick={handleGenerateSpec}
              disabled={generating}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white hover:bg-[#1b8bd4] disabled:opacity-50"
            >
              {generating ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Play size={14} />
              )}
              {generating ? "生成中..." : "仕様を生成"}
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 rounded border border-[#f44747]/30 bg-[#f44747]/10 px-4 py-2 text-[12px] text-[#f44747] flex items-center gap-2">
            <AlertTriangle size={14} />
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-12 text-[#6a6a6a]">
            <Loader2 size={24} className="animate-spin mx-auto mb-2" />
            読み込み中...
          </div>
        )}

        {/* Spec Section */}
        {spec && (
          <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
              <FileText size={14} className="text-[#007acc]" />
              <span className="text-[12px] font-medium text-[#cccccc]">
                仕様書 (v{spec.version})
              </span>
              <CheckCircle size={12} className="text-[#4ec9b0] ml-auto" />
            </div>
            <div className="px-4 py-3 space-y-2">
              <div>
                <div className="text-[11px] text-[#6a6a6a] mb-0.5">目的</div>
                <div className="text-[12px] text-[#cccccc]">{spec.objective}</div>
              </div>
              {spec.risk_notes && (
                <div>
                  <div className="text-[11px] text-[#6a6a6a] mb-0.5">リスク</div>
                  <div className="text-[12px] text-[#ce9178]">{spec.risk_notes}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Spec Version Comparison */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <GitCompare size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              仕様バージョン比較
            </span>
          </div>
          <div className="px-4 py-4">
            <div className="flex gap-3 mb-3">
              <select className="px-2 py-1 rounded text-[12px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] outline-none">
                <option>v{spec?.version || 1} (最新)</option>
              </select>
              <span className="text-[#6a6a6a] flex items-center">vs</span>
              <select className="px-2 py-1 rounded text-[12px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] outline-none">
                <option>ベースライン</option>
              </select>
            </div>
            {!spec && (
              <div className="rounded p-3 text-[12px] text-[#6a6a6a] border border-[#3e3e42] bg-[#1e1e1e] text-center">
                仕様のバージョンがまだありません。
              </div>
            )}
          </div>
        </div>

        {/* Plan Summary + Cost */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <Coins size={14} className="text-[#dcdcaa]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              計画サマリー・コスト見積
            </span>
          </div>
          <div className="px-4 py-4">
            <div className="grid grid-cols-4 gap-4 mb-3">
              <div>
                <div className="text-[11px] text-[#6a6a6a]">タスク数</div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  {tasks.length}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">推定コスト</div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  ${totalCost.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">推定所要時間</div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  {totalMinutes > 0 ? `${totalMinutes}分` : "--"}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">承認ポイント</div>
                <div className="text-[16px] font-semibold text-[#ce9178]">
                  {approvalPoints}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Task DAG */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <ListTree size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              タスク DAG ({tasks.length} タスク)
            </span>
          </div>
          {tasks.length > 0 ? (
            <div className="px-4 py-3 space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center gap-3 px-3 py-2 rounded bg-[#1e1e1e] border border-[#3e3e42]"
                >
                  <span
                    className={`text-[11px] font-mono ${statusColors[task.status] || "text-[#6a6a6a]"}`}
                  >
                    {task.status}
                  </span>
                  <span className="text-[12px] text-[#cccccc] flex-1">
                    {task.title}
                  </span>
                  {task.requires_approval && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#ce9178]/20 text-[#ce9178]">
                      承認必要
                    </span>
                  )}
                  {task.depends_on.length > 0 && (
                    <span className="text-[10px] text-[#6a6a6a]">
                      依存: {task.depends_on.length}
                    </span>
                  )}
                  <span className="text-[10px] text-[#6a6a6a]">
                    ${(task.estimated_cost_usd || 0).toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="px-4 py-6 text-center text-[12px] text-[#6a6a6a]">
              タスクの依存関係グラフはまだ生成されていません。
            </div>
          )}
        </div>

        {/* Dependencies */}
        <div className="rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <Link size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              依存関係
            </span>
          </div>
          <div className="px-4 py-4">
            {tasks.filter((t) => t.depends_on.length > 0).length > 0 ? (
              <div className="space-y-1">
                {tasks
                  .filter((t) => t.depends_on.length > 0)
                  .map((t) => (
                    <div key={t.id} className="text-[12px] text-[#cccccc]">
                      <span className="text-[#007acc]">{t.title}</span>
                      <span className="text-[#6a6a6a]"> → </span>
                      {t.depends_on.map((depId) => {
                        const dep = tasks.find((x) => x.id === depId)
                        return dep?.title || depId.slice(0, 8)
                      }).join(", ")}
                    </div>
                  ))}
              </div>
            ) : (
              <div className="text-center text-[12px] text-[#6a6a6a]">
                外部依存関係はありません。
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
