import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { FileBox, Grid, List, Download, Eye, ArrowRight } from "lucide-react"
import { useT } from "@/shared/i18n"

export function ArtifactsPage() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const t = useT()
  const navigate = useNavigate()

  const artifacts: {
    id: string
    name: string
    type: string
    size: string
    ticketId: string
    created: string
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <FileBox size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.nav.artifacts}
            </h2>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => setViewMode("grid")}
              className="p-1.5 rounded"
              style={{
                background: viewMode === "grid" ? "var(--bg-active)" : "transparent",
                color: viewMode === "grid" ? "var(--text-primary)" : "var(--text-muted)",
              }}
              aria-label="Grid view"
            >
              <Grid size={16} />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className="p-1.5 rounded"
              style={{
                background: viewMode === "list" ? "var(--bg-active)" : "transparent",
                color: viewMode === "list" ? "var(--text-primary)" : "var(--text-muted)",
              }}
              aria-label="List view"
            >
              <List size={16} />
            </button>
          </div>
        </div>

        {artifacts.length === 0 ? (
          <div className="rounded px-4 py-8 text-center border border-[var(--border)] text-[var(--text-muted)]">
            <FileBox size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-[12px] mb-2">{t.artifacts?.emptyState ?? "No artifacts yet. Results from ticket execution will appear here."}</p>
            <button onClick={() => navigate("/")} className="inline-flex items-center gap-1 text-[12px] text-[var(--accent)] hover:underline mt-1">
              {t.dashboard?.requestTask ?? "Request a task"} <ArrowRight size={12} />
            </button>
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-3 gap-3">
            {artifacts.map((a) => (
              <div
                key={a.id}
                className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors"
              >
                <div className="text-[13px] text-[var(--text-primary)] mb-1 truncate">{a.name}</div>
                <div className="text-[11px] text-[var(--text-muted)] mb-2">{a.type} - {a.size}</div>
                <div className="flex gap-2">
                  <button
                    onClick={() => window.open(`/api/v1/artifacts/${a.id}`, "_blank")}
                    className="flex items-center gap-1 text-[11px] text-[var(--accent)] hover:underline"
                  >
                    <Eye size={12} />
                    {t.common.view ?? "View"}
                  </button>
                  <button
                    onClick={() => window.open(`/api/v1/artifacts/${a.id}/download`, "_blank")}
                    className="flex items-center gap-1 text-[11px] text-[var(--accent)] hover:underline"
                  >
                    <Download size={12} />
                    {t.common.download ?? "Download"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            {artifacts.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between rounded px-4 py-2 border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileBox size={14} className="text-[var(--accent)]" />
                  <span className="text-[13px] text-[var(--text-primary)]">{a.name}</span>
                  <span className="text-[11px] text-[var(--text-muted)]">{a.type}</span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                  <span>{a.size}</span>
                  <span>{a.created}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
