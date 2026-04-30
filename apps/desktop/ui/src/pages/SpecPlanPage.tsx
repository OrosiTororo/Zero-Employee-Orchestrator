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
import { useT } from "@/shared/i18n"

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

interface PlanListItem {
  id: string
  version_no: number
  status: string
  summary: string | null
  goal: string | null
  estimated_cost_usd: number
  estimated_minutes: number
  risk_level: string
  parent_plan_id: string | null
}

interface PlanDiffPayload {
  base_plan_id: string
  against_plan_id: string
  added_tasks: string[]
  removed_tasks: string[]
  modified_tasks: string[]
  added_task_ids: string[]
  removed_task_ids: string[]
  modified_task_ids: string[]
  cost_change_usd: number
  time_change_minutes: number
}

type DiffMark = "added" | "removed" | "modified" | "unchanged"

export function SpecPlanPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const t = useT()
  const [spec, setSpec] = useState<Spec | null>(null)
  const [, setPlan] = useState<Plan | null>(null)
  const [tasks, setTasks] = useState<TaskNode[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState("")
  const [companyPlans, setCompanyPlans] = useState<PlanListItem[]>([])
  const [basePlanId, setBasePlanId] = useState<string>("")
  const [againstPlanId, setAgainstPlanId] = useState<string>("")
  const [diff, setDiff] = useState<PlanDiffPayload | null>(null)
  const [diffLoading, setDiffLoading] = useState(false)

  useEffect(() => {
    loadData()
    loadCompanyPlans()
  }, [id])

  async function loadCompanyPlans() {
    const companyId = localStorage.getItem("company_id") || ""
    if (!companyId) return
    try {
      const list = await api.get<PlanListItem[]>(`/companies/${companyId}/plans?include_attached=true`)
      setCompanyPlans(list)
      if (list.length >= 2) {
        setBasePlanId(list[0].id)
        setAgainstPlanId(list[1].id)
      } else if (list.length === 1) {
        setBasePlanId(list[0].id)
      }
    } catch {
      /* plan list is optional */
    }
  }

  async function loadDiff() {
    if (!basePlanId || !againstPlanId || basePlanId === againstPlanId) {
      setDiff(null)
      return
    }
    const companyId = localStorage.getItem("company_id") || ""
    setDiffLoading(true)
    try {
      const result = await api.get<PlanDiffPayload>(
        `/companies/${companyId}/plans/${basePlanId}/diff?against=${againstPlanId}`
      )
      setDiff(result)
    } catch {
      setDiff(null)
    } finally {
      setDiffLoading(false)
    }
  }

  useEffect(() => {
    loadDiff()
  }, [basePlanId, againstPlanId])

  function diffMarkFor(taskId: string, taskTitle: string): DiffMark {
    if (!diff) return "unchanged"
    if (diff.added_task_ids.includes(taskId) || diff.added_tasks.includes(taskTitle)) return "added"
    if (diff.removed_task_ids.includes(taskId) || diff.removed_tasks.includes(taskTitle))
      return "removed"
    if (diff.modified_task_ids.includes(taskId) || diff.modified_tasks.includes(taskTitle))
      return "modified"
    return "unchanged"
  }

  const diffRowClasses: Record<DiffMark, string> = {
    added: "border-[var(--success-fg)]/40 bg-[var(--success-fg)]/8",
    removed: "border-[var(--error)]/40 bg-[var(--error)]/8 opacity-70",
    modified: "border-[var(--warning)]/40 bg-[var(--warning)]/8",
    unchanged: "border-[var(--border)]",
  }

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
    pending: "text-[var(--text-muted)]",
    ready: "text-[var(--accent)]",
    running: "text-[var(--warning)]",
    succeeded: "text-[var(--success-fg)]",
    failed: "text-[var(--error)]",
    awaiting_approval: "text-[var(--warning)]",
    blocked: "text-[var(--error)]",
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate(`/tickets/${id}`)}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            <ArrowLeft size={18} />
          </button>
          <FileText size={18} className="text-[var(--accent)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
            {t.specPlan?.title ?? "Spec & Plan"}: {t.specPlan?.ticket ?? "Ticket"} {id?.slice(0, 8)}
          </h2>
          {!spec && !loading && (
            <button
              onClick={handleGenerateSpec}
              disabled={generating}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)] hover:opacity-90 disabled:opacity-50"
            >
              {generating ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Play size={14} />
              )}
              {generating ? (t.specPlan?.generating ?? "Generating...") : (t.specPlan?.generateSpec ?? "Generate Spec")}
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 rounded border border-[var(--error)]/30 bg-[var(--error)]/10 px-4 py-2 text-[12px] text-[var(--error)] flex items-center gap-2">
            <AlertTriangle size={14} />
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-12 text-[var(--text-muted)]">
            <Loader2 size={24} className="animate-spin mx-auto mb-2" />
            {t.common?.loading ?? "Loading..."}
          </div>
        )}

        {/* Spec Section */}
        {spec && (
          <div className="mb-6 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
              <FileText size={14} className="text-[var(--accent)]" />
              <span className="text-[12px] font-medium text-[var(--text-primary)]">
                {t.specPlan?.specification ?? "Specification"} (v{spec.version})
              </span>
              <CheckCircle size={12} className="text-[var(--success-fg)] ml-auto" />
            </div>
            <div className="px-4 py-3 space-y-2">
              <div>
                <div className="text-[11px] text-[var(--text-muted)] mb-0.5">{t.specPlan?.objective ?? "Objective"}</div>
                <div className="text-[12px] text-[var(--text-primary)]">{spec.objective}</div>
              </div>
              {spec.risk_notes && (
                <div>
                  <div className="text-[11px] text-[var(--text-muted)] mb-0.5">{t.specPlan?.risk ?? "Risk"}</div>
                  <div className="text-[12px] text-[var(--warning)]">{spec.risk_notes}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Plan Version Comparison */}
        <div className="mb-6 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
            <GitCompare size={14} className="text-[var(--accent)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">
              {t.specPlan?.versionComparison ?? "Plan Version Comparison"}
            </span>
          </div>
          <div className="px-4 py-4">
            {companyPlans.length < 2 ? (
              <div className="rounded p-3 text-[12px] text-[var(--text-muted)] border border-[var(--border)] bg-[var(--bg-base)] text-center">
                {t.specPlan?.noVersions ?? "Not enough plan revisions to compare yet."}
              </div>
            ) : (
              <>
                <div className="flex gap-3 mb-3 items-center flex-wrap">
                  <select
                    aria-label={t.specPlan?.diff?.base ?? "Base plan"}
                    value={basePlanId}
                    onChange={(e) => setBasePlanId(e.target.value)}
                    className="px-2 py-1 rounded text-[12px] bg-[var(--bg-active)] text-[var(--text-primary)] border border-[var(--border)] outline-none"
                  >
                    {companyPlans.map((p) => (
                      <option key={p.id} value={p.id}>
                        v{p.version_no} — {(p.summary || p.goal || p.id).slice(0, 40)}
                      </option>
                    ))}
                  </select>
                  <span className="text-[var(--text-muted)]">vs</span>
                  <select
                    aria-label={t.specPlan?.diff?.against ?? "Compare against"}
                    value={againstPlanId}
                    onChange={(e) => setAgainstPlanId(e.target.value)}
                    className="px-2 py-1 rounded text-[12px] bg-[var(--bg-active)] text-[var(--text-primary)] border border-[var(--border)] outline-none"
                  >
                    {companyPlans.map((p) => (
                      <option key={p.id} value={p.id}>
                        v{p.version_no} — {(p.summary || p.goal || p.id).slice(0, 40)}
                      </option>
                    ))}
                  </select>
                  {diffLoading && <Loader2 size={12} className="animate-spin text-[var(--text-muted)]" />}
                </div>
                {diff && (
                  <div className="grid grid-cols-3 gap-2 text-[11px]">
                    <div className="rounded px-2 py-1.5 border border-[var(--success-fg)]/40 bg-[var(--success-fg)]/8 text-[var(--success-fg)]">
                      <span className="font-semibold">+{diff.added_tasks.length}</span>{" "}
                      {t.specPlan?.diff?.added ?? "added"}
                    </div>
                    <div className="rounded px-2 py-1.5 border border-[var(--warning)]/40 bg-[var(--warning)]/8 text-[var(--warning)]">
                      <span className="font-semibold">~{diff.modified_tasks.length}</span>{" "}
                      {t.specPlan?.diff?.modified ?? "modified"}
                    </div>
                    <div className="rounded px-2 py-1.5 border border-[var(--error)]/40 bg-[var(--error)]/8 text-[var(--error)]">
                      <span className="font-semibold">−{diff.removed_tasks.length}</span>{" "}
                      {t.specPlan?.diff?.removed ?? "removed"}
                    </div>
                    <div className="col-span-3 text-[11px] text-[var(--text-muted)]">
                      {(t.specPlan?.diff?.costDelta ?? "Cost delta").replace(
                        "{n}",
                        `${diff.cost_change_usd >= 0 ? "+" : ""}$${diff.cost_change_usd.toFixed(2)}`
                      )}
                      {" · "}
                      {(t.specPlan?.diff?.timeDelta ?? "Time delta").replace(
                        "{n}",
                        `${diff.time_change_minutes >= 0 ? "+" : ""}${diff.time_change_minutes} ${t.specPlan?.minutes ?? "min"}`
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Plan Summary + Cost */}
        <div className="mb-6 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
            <Coins size={14} className="text-[var(--warning)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">
              {t.specPlan?.planSummary ?? "Plan Summary & Cost Estimate"}
            </span>
          </div>
          <div className="px-4 py-4">
            <div className="grid grid-cols-4 gap-4 mb-3">
              <div>
                <div className="text-[11px] text-[var(--text-muted)]">{t.specPlan?.taskCount ?? "Tasks"}</div>
                <div className="text-[16px] font-semibold text-[var(--text-primary)]">
                  {tasks.length}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[var(--text-muted)]">{t.specPlan?.estimatedCost ?? "Estimated Cost"}</div>
                <div className="text-[16px] font-semibold text-[var(--text-primary)]">
                  ${totalCost.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[var(--text-muted)]">{t.specPlan?.estimatedTime ?? "Estimated Time"}</div>
                <div className="text-[16px] font-semibold text-[var(--text-primary)]">
                  {totalMinutes > 0 ? `${totalMinutes} ${t.specPlan?.minutes ?? "min"}` : "--"}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[var(--text-muted)]">{t.specPlan?.approvalPoints ?? "Approval Points"}</div>
                <div className="text-[16px] font-semibold text-[var(--warning)]">
                  {approvalPoints}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Task DAG */}
        <div className="mb-6 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
            <ListTree size={14} className="text-[var(--accent)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">
              {t.specPlan?.taskDag ?? "Task DAG"} ({tasks.length} {t.specPlan?.tasks ?? "tasks"})
            </span>
          </div>
          {tasks.length > 0 ? (
            <div className="px-4 py-3 space-y-2">
              {tasks.map((task) => {
                const mark = diffMarkFor(task.id, task.title)
                return (
                <div
                  key={task.id}
                  className={`flex items-center gap-3 px-3 py-2 rounded bg-[var(--bg-base)] border ${diffRowClasses[mark]}`}
                >
                  <span
                    className={`text-[11px] font-mono ${statusColors[task.status] || "text-[var(--text-muted)]"}`}
                  >
                    {task.status}
                  </span>
                  <span className="text-[12px] text-[var(--text-primary)] flex-1">
                    {mark !== "unchanged" && (
                      <span
                        className="mr-2 text-[10px] font-mono"
                        aria-label={mark}
                        title={mark}
                      >
                        {mark === "added" ? "+" : mark === "removed" ? "−" : "~"}
                      </span>
                    )}
                    {task.title}
                  </span>
                  {task.requires_approval && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--warning)]/20 text-[var(--warning)]">
                      {t.specPlan?.approvalRequired ?? "Approval Required"}
                    </span>
                  )}
                  {task.depends_on.length > 0 && (
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {t.specPlan?.dependencies ?? "Deps"}: {task.depends_on.length}
                    </span>
                  )}
                  <span className="text-[10px] text-[var(--text-muted)]">
                    ${(task.estimated_cost_usd || 0).toFixed(3)}
                  </span>
                </div>
                )
              })}
            </div>
          ) : (
            <div className="px-4 py-6 text-center text-[12px] text-[var(--text-muted)]">
              {t.specPlan?.noDag ?? "Task dependency graph has not been generated yet."}
            </div>
          )}
        </div>

        {/* Dependencies */}
        <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
            <Link size={14} className="text-[var(--accent)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">
              {t.specPlan?.dependenciesTitle ?? "Dependencies"}
            </span>
          </div>
          <div className="px-4 py-4">
            {tasks.filter((t) => t.depends_on.length > 0).length > 0 ? (
              <div className="space-y-1">
                {tasks
                  .filter((t) => t.depends_on.length > 0)
                  .map((t) => (
                    <div key={t.id} className="text-[12px] text-[var(--text-primary)]">
                      <span className="text-[var(--accent)]">{t.title}</span>
                      <span className="text-[var(--text-muted)]"> → </span>
                      {t.depends_on.map((depId) => {
                        const dep = tasks.find((x) => x.id === depId)
                        return dep?.title || depId.slice(0, 8)
                      }).join(", ")}
                    </div>
                  ))}
              </div>
            ) : (
              <div className="text-center text-[12px] text-[var(--text-muted)]">
                {t.specPlan?.noDependencies ?? "No external dependencies."}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
