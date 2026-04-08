import { useState, useEffect, useCallback } from "react"
import {
  Send, Loader2, CheckCircle, XCircle, Clock, Trash2,
  Eye, Play, ChevronDown, ChevronRight,
  AlertCircle, Navigation,
} from "lucide-react"
import { api } from "@/shared/api/client"
import { useT } from "@/shared/i18n"
import { useToastStore } from "@/shared/ui/ErrorToast"

interface PlanStep {
  id: string
  title: string
  depends_on: string[]
  estimated_minutes: number
  status: string
}

interface DispatchTask {
  task_id: string
  status: string
  instruction: string
  created_at: string
  completed_at: string | null
  result: string | null
  plan_preview: PlanStep[] | null
  needs_input_reason: string | null
}

type TabKey = "active" | "completed" | "all"

export function DispatchPage() {
  const t = useT()
  const addToast = useToastStore((s) => s.addToast)
  const [tasks, setTasks] = useState<DispatchTask[]>([])
  const [instruction, setInstruction] = useState("")
  const [loading, setLoading] = useState(false)
  const [previewMode, setPreviewMode] = useState(false)
  const [activeTab, setActiveTab] = useState<TabKey>("active")
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set())
  const [steerInputs, setSteerInputs] = useState<Record<string, string>>({})
  const [resumeInputs, setResumeInputs] = useState<Record<string, string>>({})
  const companyId = localStorage.getItem("company_id") || ""

  const loadTasks = useCallback(async () => {
    try {
      const data = await api.get<{ tasks: DispatchTask[]; total: number }>("/dispatch")
      setTasks(data.tasks)
    } catch {
      addToast((t as unknown as Record<string, Record<string, string>>).dispatch?.loadFailed ?? "Could not load dispatch tasks.")
    }
  }, [addToast])

  useEffect(() => {
    loadTasks()
    const interval = setInterval(loadTasks, 5_000)
    return () => clearInterval(interval)
  }, [loadTasks])

  const handleDispatch = async () => {
    if (!instruction.trim() || loading) return
    setLoading(true)
    try {
      await api.post("/dispatch", {
        instruction: instruction.trim(),
        priority: "medium",
        context: { company_id: companyId },
        preview_only: previewMode,
      })
      setInstruction("")
      await loadTasks()
    } catch {
      addToast((t as unknown as Record<string, Record<string, string>>).dispatch?.dispatchFailed ?? "Could not dispatch task.")
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async (taskId: string) => {
    try {
      await api.delete(`/dispatch/${taskId}`)
      await loadTasks()
    } catch {
      addToast((t as unknown as Record<string, Record<string, string>>).dispatch?.cancelFailed ?? "Could not cancel task.")
    }
  }

  const handleStartPreview = async (taskId: string) => {
    try {
      await api.post(`/dispatch/${taskId}/start`, {})
      await loadTasks()
    } catch {
      addToast("Could not start task.")
    }
  }

  const handleSteer = async (taskId: string) => {
    const steerText = steerInputs[taskId]?.trim()
    if (!steerText) return
    try {
      await api.post(`/dispatch/${taskId}/steer`, { instruction: steerText })
      setSteerInputs((prev) => ({ ...prev, [taskId]: "" }))
      await loadTasks()
    } catch {
      addToast("Could not steer task.")
    }
  }

  const handleResume = async (taskId: string) => {
    const resumeText = resumeInputs[taskId]?.trim()
    if (!resumeText) return
    try {
      await api.post(`/dispatch/${taskId}/resume`, { user_input: resumeText })
      setResumeInputs((prev) => ({ ...prev, [taskId]: "" }))
      await loadTasks()
    } catch {
      addToast("Could not resume task.")
    }
  }

  const toggleExpand = (taskId: string) => {
    setExpandedTasks((prev) => {
      const next = new Set(prev)
      if (next.has(taskId)) next.delete(taskId)
      else next.add(taskId)
      return next
    })
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle size={14} className="text-[var(--success)]" />
      case "failed": return <XCircle size={14} className="text-[var(--error)]" />
      case "running": return <Loader2 size={14} className="text-[var(--accent)] animate-spin" />
      case "cancelled": return <XCircle size={14} className="text-[var(--text-muted)]" />
      case "needs_input": return <AlertCircle size={14} className="text-[var(--warning)]" />
      case "preview": return <Eye size={14} className="text-[var(--accent)]" />
      default: return <Clock size={14} className="text-[var(--warning)]" />
    }
  }

  const statusLabel = (status: string) => {
    const labels: Record<string, string> = {
      queued: "Queued", running: "Running", completed: "Done",
      failed: "Failed", cancelled: "Cancelled",
      needs_input: "Needs Input", preview: "Plan Preview",
    }
    return labels[status] ?? status
  }

  const statusColor = (status: string) => {
    const colors: Record<string, string> = {
      queued: "var(--text-muted)", running: "var(--accent)",
      completed: "var(--success)", failed: "var(--error)",
      cancelled: "var(--text-muted)", needs_input: "var(--warning)",
      preview: "var(--accent)",
    }
    return colors[status] ?? "var(--text-muted)"
  }

  const filteredTasks = tasks.filter((task) => {
    if (activeTab === "active") return ["queued", "running", "needs_input", "preview"].includes(task.status)
    if (activeTab === "completed") return ["completed", "failed", "cancelled"].includes(task.status)
    return true
  })

  const activeCnt = tasks.filter((t) => ["queued", "running", "needs_input", "preview"].includes(t.status)).length
  const completedCnt = tasks.filter((t) => ["completed", "failed", "cancelled"].includes(t.status)).length

  return (
    <div className="p-6 max-w-[800px] mx-auto space-y-5">
      <div className="flex items-center gap-2">
        <Send size={20} className="text-[var(--accent)]" />
        <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
          {t.nav?.dispatch ?? "Dispatch"}
        </h1>
        <span className="text-[11px] text-[var(--text-muted)] ml-2">
          {(t as unknown as Record<string, Record<string, string>>).dispatch?.subtitle ?? "Background tasks with plan preview & steering"}
        </span>
      </div>

      {/* Input */}
      <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden focus-within:border-[var(--accent)] transition-colors">
        <textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleDispatch() } }}
          placeholder="Describe a background task... (e.g., 'Generate weekly sales report')"
          className="w-full resize-none px-4 py-3 text-[13px] outline-none bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
          rows={2}
        />
        <div className="flex items-center justify-between px-4 py-2 border-t border-[var(--border)] bg-[var(--bg-raised)]">
          <label className="flex items-center gap-1.5 text-[11px] text-[var(--text-muted)] cursor-pointer select-none">
            <input
              type="checkbox"
              checked={previewMode}
              onChange={(e) => setPreviewMode(e.target.checked)}
              className="rounded"
            />
            <Eye size={11} /> Preview plan first
          </label>
          <button
            onClick={handleDispatch}
            disabled={!instruction.trim() || loading}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded text-[12px] font-medium text-white disabled:opacity-40"
            style={{ background: "var(--accent)" }}
          >
            {loading ? <Loader2 size={12} className="animate-spin" /> : previewMode ? <Eye size={12} /> : <Send size={12} />}
            {previewMode ? "Preview" : "Dispatch"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[var(--border)]">
        {([
          ["active", `Active (${activeCnt})`],
          ["completed", `Done (${completedCnt})`],
          ["all", `All (${tasks.length})`],
        ] as [TabKey, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className="px-3 py-1.5 text-[12px] font-medium transition-colors"
            style={{
              color: activeTab === key ? "var(--accent)" : "var(--text-muted)",
              borderBottom: activeTab === key ? "2px solid var(--accent)" : "2px solid transparent",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Task List */}
      <div className="space-y-2">
        {filteredTasks.length === 0 && (
          <div className="text-[12px] text-[var(--text-muted)] py-8 text-center">
            {activeTab === "active" ? "No active tasks. Use the input above to send a background task." : "No tasks in this category."}
          </div>
        )}
        {filteredTasks.map((task) => {
          const expanded = expandedTasks.has(task.task_id)
          return (
            <div key={task.task_id} className="rounded border border-[var(--border)] bg-[var(--bg-surface)]">
              {/* Header */}
              <div
                className="flex items-start justify-between gap-2 p-3 cursor-pointer"
                onClick={() => toggleExpand(task.task_id)}
              >
                <div className="flex items-center gap-2 min-w-0">
                  {expanded ? <ChevronDown size={12} className="text-[var(--text-muted)] shrink-0" /> : <ChevronRight size={12} className="text-[var(--text-muted)] shrink-0" />}
                  {statusIcon(task.status)}
                  <span className="text-[12px] font-medium text-[var(--text-primary)] truncate">
                    {task.instruction}
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                    style={{ color: statusColor(task.status), background: `color-mix(in srgb, ${statusColor(task.status)} 15%, transparent)` }}
                  >
                    {statusLabel(task.status)}
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)]">
                    {new Date(task.created_at).toLocaleTimeString()}
                  </span>
                  {["queued", "running", "needs_input"].includes(task.status) && (
                    <button onClick={(e) => { e.stopPropagation(); handleCancel(task.task_id) }} className="text-[var(--text-muted)] hover:text-[var(--error)]">
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded Content */}
              {expanded && (
                <div className="border-t border-[var(--border)] px-3 py-2 space-y-2">
                  {/* Plan Preview */}
                  {task.plan_preview && task.plan_preview.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                        Execution Plan ({task.plan_preview.length} steps)
                      </div>
                      {task.plan_preview.map((step, i) => (
                        <div key={step.id} className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)] py-0.5">
                          <span className="text-[var(--text-muted)] w-4 text-right">{i + 1}.</span>
                          {step.status === "succeeded" ? <CheckCircle size={10} className="text-[var(--success)]" /> : step.status === "running" ? <Loader2 size={10} className="text-[var(--accent)] animate-spin" /> : <Clock size={10} className="text-[var(--text-muted)]" />}
                          <span>{step.title}</span>
                          {step.estimated_minutes > 0 && <span className="text-[var(--text-muted)]">~{step.estimated_minutes}m</span>}
                        </div>
                      ))}
                      {task.status === "preview" && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleStartPreview(task.task_id) }}
                          className="flex items-center gap-1 mt-1 px-3 py-1 rounded text-[11px] font-medium text-white"
                          style={{ background: "var(--success)" }}
                        >
                          <Play size={10} /> Approve & Execute
                        </button>
                      )}
                    </div>
                  )}

                  {/* Needs Input */}
                  {task.status === "needs_input" && task.needs_input_reason && (
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-1.5 text-[11px] text-[var(--warning)] font-medium">
                        <AlertCircle size={12} /> {task.needs_input_reason}
                      </div>
                      <div className="flex gap-1.5">
                        <input
                          type="text"
                          value={resumeInputs[task.task_id] ?? ""}
                          onChange={(e) => setResumeInputs((prev) => ({ ...prev, [task.task_id]: e.target.value }))}
                          onKeyDown={(e) => { if (e.key === "Enter") handleResume(task.task_id) }}
                          placeholder="Provide input to continue..."
                          className="flex-1 text-[11px] px-2 py-1 rounded border border-[var(--border)] bg-[var(--bg-raised)] outline-none text-[var(--text-primary)]"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <button
                          onClick={(e) => { e.stopPropagation(); handleResume(task.task_id) }}
                          className="px-2 py-1 rounded text-[11px] font-medium text-white"
                          style={{ background: "var(--accent)" }}
                        >
                          Resume
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Steering (for running tasks) */}
                  {task.status === "running" && (
                    <div className="flex gap-1.5">
                      <input
                        type="text"
                        value={steerInputs[task.task_id] ?? ""}
                        onChange={(e) => setSteerInputs((prev) => ({ ...prev, [task.task_id]: e.target.value }))}
                        onKeyDown={(e) => { if (e.key === "Enter") handleSteer(task.task_id) }}
                        placeholder="Add steering instruction..."
                        className="flex-1 text-[11px] px-2 py-1 rounded border border-[var(--border)] bg-[var(--bg-raised)] outline-none text-[var(--text-primary)]"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <button
                        onClick={(e) => { e.stopPropagation(); handleSteer(task.task_id) }}
                        className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium text-white"
                        style={{ background: "var(--accent)" }}
                      >
                        <Navigation size={10} /> Steer
                      </button>
                    </div>
                  )}

                  {/* Result */}
                  {task.result && (
                    <div className="text-[11px] text-[var(--text-secondary)] bg-[var(--bg-raised)] rounded px-2.5 py-1.5 whitespace-pre-wrap">
                      {task.result}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
