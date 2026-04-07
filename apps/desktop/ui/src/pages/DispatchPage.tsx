import { useState, useEffect, useCallback } from "react"
import { Send, Loader2, CheckCircle, XCircle, Clock, Trash2 } from "lucide-react"
import { api } from "@/shared/api/client"
import { useT } from "@/shared/i18n"
import { useToastStore } from "@/shared/ui/ErrorToast"

interface DispatchTask {
  task_id: string
  status: string
  instruction: string
  created_at: string
  completed_at: string | null
  result: string | null
}

export function DispatchPage() {
  const t = useT()
  const addToast = useToastStore((s) => s.addToast)
  const [tasks, setTasks] = useState<DispatchTask[]>([])
  const [instruction, setInstruction] = useState("")
  const [loading, setLoading] = useState(false)
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
    const interval = setInterval(loadTasks, 10_000)
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

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle size={14} className="text-[var(--success)]" />
      case "failed": return <XCircle size={14} className="text-[var(--error)]" />
      case "running": return <Loader2 size={14} className="text-[var(--accent)] animate-spin" />
      case "cancelled": return <XCircle size={14} className="text-[var(--text-muted)]" />
      default: return <Clock size={14} className="text-[var(--warning)]" />
    }
  }

  return (
    <div className="p-6 max-w-[800px] mx-auto space-y-5">
      <div className="flex items-center gap-2">
        <Send size={20} className="text-[var(--accent)]" />
        <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
          {t.nav?.dispatch ?? "Dispatch"}
        </h1>
        <span className="text-[11px] text-[var(--text-muted)] ml-2">
          {(t as unknown as Record<string, Record<string, string>>).dispatch?.subtitle ?? "Background tasks — fire and forget"}
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
          <span className="text-[11px] text-[var(--text-muted)]">
            {(t as unknown as Record<string, Record<string, string>>).dispatch?.helpText ?? "Tasks run in the background. A ticket is auto-created."}
          </span>
          <button
            onClick={handleDispatch}
            disabled={!instruction.trim() || loading}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded text-[12px] font-medium text-white disabled:opacity-40"
            style={{ background: "var(--accent)" }}
          >
            {loading ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
            Dispatch
          </button>
        </div>
      </div>

      {/* Task List */}
      <div className="space-y-2">
        <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
          {tasks.length} task{tasks.length !== 1 ? "s" : ""}
        </div>
        {tasks.length === 0 && (
          <div className="text-[12px] text-[var(--text-muted)] py-8 text-center">
            No dispatched tasks yet. Use the input above to send a background task.
          </div>
        )}
        {tasks.map((task) => (
          <div key={task.task_id} className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                {statusIcon(task.status)}
                <span className="text-[12px] font-medium text-[var(--text-primary)] truncate">
                  {task.instruction}
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[10px] text-[var(--text-muted)]">
                  {new Date(task.created_at).toLocaleTimeString()}
                </span>
                {(task.status === "queued" || task.status === "running") && (
                  <button onClick={() => handleCancel(task.task_id)} className="text-[var(--text-muted)] hover:text-[var(--error)]">
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            </div>
            {task.result && (
              <div className="mt-2 text-[11px] text-[var(--text-secondary)] bg-[var(--bg-raised)] rounded px-2.5 py-1.5">
                {task.result}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
