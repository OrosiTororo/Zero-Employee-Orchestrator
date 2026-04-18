import { useCallback, useEffect, useState } from "react"
import { BookTemplate, Layers, RefreshCw, Workflow } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api, ApiError } from "@/shared/api/client"
import { useToastStore } from "@/shared/ui/ErrorToast"
import { PresetCard } from "@/shared/ui/PresetCard"
import { Modal } from "@/shared/ui/Modal"

interface TemplateNode {
  id: string
  title: string
  depends_on: string[]
  role: string
  verification: string
}

interface WorkflowTemplate {
  slug: string
  name: string
  description: string
  category: string
  nodes: TemplateNode[]
  tags: string[]
  builtin: boolean
}

interface InstantiateResponse {
  plan_id: string
  ticket_title: string
  template_slug: string
  nodes: { id: string; title: string; depends_on: string[]; role: string; verification_criteria: string }[]
  ready_to_execute: boolean
}

export function TemplatesPage() {
  const t = useT()
  const addToast = useToastStore((s) => s.addToast)
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<WorkflowTemplate | null>(null)
  const [ticketTitle, setTicketTitle] = useState("")
  const [result, setResult] = useState<InstantiateResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const body = await api.get<{ templates: WorkflowTemplate[] }>("/workflow-templates")
      setTemplates(body.templates ?? [])
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : t.templates.loadFailed ?? "Could not load templates."
      addToast(msg)
    } finally {
      setLoading(false)
    }
  }, [addToast, t.templates.loadFailed])

  useEffect(() => {
    load()
  }, [load])

  const openInstantiate = (tpl: WorkflowTemplate) => {
    setSelected(tpl)
    setTicketTitle("")
    setResult(null)
  }

  const submitInstantiate = async () => {
    if (!selected) return
    if (!ticketTitle.trim()) {
      addToast(t.templates.titleRequired ?? "Ticket title is required.")
      return
    }
    setSubmitting(true)
    try {
      const body = await api.post<InstantiateResponse>(
        `/workflow-templates/${selected.slug}/instantiate`,
        { ticket_title: ticketTitle.trim(), variables: {} },
      )
      setResult(body)
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : t.templates.instantiateFailed ?? "Instantiate failed."
      addToast(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <BookTemplate size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.templates.title}
            </h2>
            <span className="text-[11px] text-[var(--text-muted)]">
              {templates.length} {t.templates.countLabel}
            </span>
          </div>
          <button
            onClick={load}
            aria-label={t.templates.refresh}
            className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-[var(--accent)]"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            {t.templates.refresh}
          </button>
        </div>
        <p className="text-[12px] text-[var(--text-muted)] mb-5">{t.templates.subtitle}</p>

        {loading ? (
          <div className="py-16 text-center text-[12px] text-[var(--text-muted)]">
            <RefreshCw size={20} className="mx-auto mb-2 animate-spin text-[var(--accent)]" />
            {t.common.loading ?? "Loading..."}
          </div>
        ) : templates.length === 0 ? (
          <div className="rounded px-4 py-16 text-center border border-[var(--border)]">
            <Workflow size={40} className="mx-auto mb-4 text-[var(--text-muted)] opacity-40" />
            <p className="text-[13px] text-[var(--text-primary)]">{t.templates.empty}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {templates.map((tpl) => (
              <PresetCard
                key={tpl.slug}
                title={tpl.name}
                subtitle={tpl.slug}
                description={tpl.description}
                badges={[
                  tpl.builtin ? t.templates.builtin : t.templates.userSaved,
                  `${tpl.nodes.length} ${t.templates.nodes}`,
                  tpl.category,
                ]}
                icon={<Layers size={14} />}
                actionLabel={t.templates.instantiate}
                ariaLabel={`${t.templates.instantiate}: ${tpl.name}`}
                onAction={() => openInstantiate(tpl)}
              />
            ))}
          </div>
        )}
      </div>

      <Modal
        open={selected !== null}
        onClose={() => setSelected(null)}
        title={selected ? `${t.templates.instantiate}: ${selected.name}` : ""}
        labelledBy="templates-dialog-title"
        footer={
          result ? (
            <button
              onClick={() => setSelected(null)}
              className="px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)]"
            >
              {t.common.done ?? "Done"}
            </button>
          ) : (
            <>
              <button
                onClick={() => setSelected(null)}
                className="px-3 py-1.5 rounded text-[12px] border border-[var(--border)] text-[var(--text-secondary)]"
              >
                {t.common.cancel ?? "Cancel"}
              </button>
              <button
                onClick={submitInstantiate}
                disabled={submitting}
                className="px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)] disabled:opacity-50"
              >
                {submitting ? t.common.working ?? "Working..." : t.templates.instantiate}
              </button>
            </>
          )
        }
      >
        {selected && !result ? (
          <div className="flex flex-col gap-3">
            <p className="text-[12px] text-[var(--text-secondary)]">{selected.description}</p>
            <label className="flex flex-col gap-1">
              <span className="text-[11px] text-[var(--text-muted)]">
                {t.templates.ticketTitle}
              </span>
              <input
                autoFocus
                value={ticketTitle}
                onChange={(e) => setTicketTitle(e.target.value)}
                placeholder={t.templates.ticketTitlePlaceholder}
                className="px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
              />
            </label>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] text-[var(--text-muted)]">{t.templates.preview}</span>
              <ol className="list-decimal list-inside text-[12px] text-[var(--text-secondary)] space-y-0.5">
                {selected.nodes.map((n) => (
                  <li key={n.id}>
                    {n.title}
                    {n.depends_on.length > 0 ? (
                      <span className="text-[var(--text-muted)]"> ← {n.depends_on.join(", ")}</span>
                    ) : null}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        ) : null}
        {result ? (
          <div className="flex flex-col gap-2 text-[12px] text-[var(--text-secondary)]">
            <div>
              <span className="text-[var(--text-muted)]">{t.templates.planId}: </span>
              <span className="text-[var(--text-primary)] font-mono">
                {result.plan_id.slice(0, 8)}…
              </span>
            </div>
            <div>
              <span className="text-[var(--text-muted)]">{t.templates.ticket}: </span>
              <span className="text-[var(--text-primary)]">{result.ticket_title}</span>
            </div>
            <div className="text-[var(--text-muted)]">{t.templates.nodesReady}</div>
            <ol className="list-decimal list-inside space-y-0.5">
              {result.nodes.map((n) => (
                <li key={n.id}>{n.title}</li>
              ))}
            </ol>
          </div>
        ) : null}
      </Modal>
    </div>
  )
}
