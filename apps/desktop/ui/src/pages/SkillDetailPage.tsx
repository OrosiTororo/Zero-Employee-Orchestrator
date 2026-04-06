import { useState, useEffect, useCallback } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
  Package,
  ArrowLeft,
  Shield,
  ToggleLeft,
  ToggleRight,
  Trash2,
  Code2,
  Info,
  Tag,
  Clock,
} from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

interface SkillDetail {
  id: string
  slug: string
  name: string
  skill_type: string
  description: string | null
  version: string
  status: string
  is_system_protected: boolean
  enabled: boolean
  created_at?: string
  updated_at?: string
  author?: string
  tags?: string[]
  input_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
  code?: string
  config?: Record<string, unknown>
}

export function SkillDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const t = useT()
  const [skill, setSkill] = useState<SkillDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const statusBadges: Record<string, { label: string; color: string; bg: string }> = {
    verified: { label: t.skillDetail?.verified ?? "Verified", color: "var(--success-fg)", bg: "color-mix(in srgb, var(--success-fg) 12%, transparent)" },
    experimental: { label: t.skillDetail?.experimental ?? "Experimental", color: "var(--warning)", bg: "color-mix(in srgb, var(--warning) 12%, transparent)" },
    private: { label: t.skillDetail?.private ?? "Private", color: "var(--accent)", bg: "color-mix(in srgb, var(--accent) 12%, transparent)" },
    deprecated: { label: t.skillDetail?.deprecated ?? "Deprecated", color: "var(--error)", bg: "color-mix(in srgb, var(--error) 12%, transparent)" },
  }

  const fetchSkill = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<SkillDetail>(`/registry/skills/${id}`)
      setSkill(data)
    } catch {
      setError(t.skillDetail?.fetchError ?? "Failed to fetch skill")
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchSkill()
  }, [fetchSkill])

  const handleToggle = async () => {
    if (!skill || skill.is_system_protected) return
    try {
      await api.patch(`/registry/skills/${skill.id}`, { enabled: !skill.enabled })
      await fetchSkill()
    } catch (e: any) {
      alert(e?.message || (t.skillDetail?.notAllowed ?? "This operation is not allowed"))
    }
  }

  const handleDelete = async () => {
    if (!skill || skill.is_system_protected) return
    if (!confirm(`${t.skillDetail?.confirmDelete ?? "Delete skill"} "${skill.name}"?`)) return
    try {
      await api.delete(`/registry/skills/${skill.id}`)
      navigate("/skills")
    } catch (e: any) {
      alert(e?.message || (t.skillDetail?.notAllowed ?? "This operation is not allowed"))
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-[12px] text-[var(--text-muted)]">
        {t.common?.loading ?? "Loading..."}
      </div>
    )
  }

  if (error || !skill) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-[900px] mx-auto px-6 py-6">
          <button
            onClick={() => navigate("/skills")}
            className="flex items-center gap-1 text-[12px] text-[var(--accent)] hover:underline mb-4"
          >
            <ArrowLeft size={14} />
            {t.skillDetail?.backToList ?? "Back to Skills"}
          </button>
          <div className="rounded px-4 py-3 text-[12px] border border-[var(--error)] bg-[color-mix(in_srgb,var(--error)_12%,transparent)] text-[var(--error)]">
            {error || (t.skillDetail?.notFound ?? "Skill not found")}
          </div>
        </div>
      </div>
    )
  }

  const badge = statusBadges[skill.status] ?? statusBadges.private

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Back button */}
        <button
          onClick={() => navigate("/skills")}
          className="flex items-center gap-1 text-[12px] text-[var(--accent)] hover:underline mb-4"
        >
          <ArrowLeft size={14} />
          {t.skillDetail?.backToList ?? "Back to Skills"}
        </button>

        {/* Header */}
        <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4 mb-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded bg-[color-mix(in_srgb,var(--accent)_12%,transparent)] flex items-center justify-center">
                <Package size={20} className="text-[var(--accent)]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-[16px] font-medium text-[var(--text-primary)]">
                    {skill.name}
                  </h2>
                  <span className="text-[11px] text-[var(--text-muted)]">v{skill.version}</span>
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded"
                    style={{ background: badge.bg, color: badge.color }}
                  >
                    {badge.label}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-active)] text-[var(--text-muted)]">
                    {skill.skill_type}
                  </span>
                  {skill.is_system_protected && (
                    <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded bg-[color-mix(in_srgb,var(--warning)_12%,transparent)] text-[var(--warning)]">
                      <Shield size={10} />
                      {t.skillDetail?.systemRequired ?? "System Required"}
                    </span>
                  )}
                </div>
                <p className="text-[12px] text-[var(--text-muted)] mt-1">
                  {skill.slug}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleToggle}
                className="flex items-center gap-1 px-3 py-1.5 rounded text-[12px] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-active)] transition-colors"
                disabled={skill.is_system_protected}
              >
                {skill.enabled ? (
                  <>
                    <ToggleRight size={16} className="text-[var(--success-fg)]" />
                    {t.skillDetail?.enabled ?? "Enabled"}
                  </>
                ) : (
                  <>
                    <ToggleLeft size={16} />
                    {t.skillDetail?.disabled ?? "Disabled"}
                  </>
                )}
              </button>
              {!skill.is_system_protected && (
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-1 px-3 py-1.5 rounded text-[12px] border border-[var(--border)] text-[var(--error)] hover:bg-[color-mix(in_srgb,var(--error)_12%,transparent)] transition-colors"
                >
                  <Trash2 size={14} />
                  {t.common?.delete ?? "Delete"}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Info size={14} className="text-[var(--accent)]" />
            <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.skillDetail?.description ?? "Description"}</span>
          </div>
          <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
            {skill.description || (t.skillDetail?.noDescription ?? "No description")}
          </p>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4">
            <div className="flex items-center gap-2 mb-3">
              <Tag size={14} className="text-[var(--accent)]" />
              <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.skillDetail?.metadata ?? "Metadata"}</span>
            </div>
            <div className="flex flex-col gap-2 text-[12px]">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">ID</span>
                <span className="text-[var(--accent)] font-mono text-[11px]">{skill.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Slug</span>
                <span className="text-[var(--text-primary)] font-mono text-[11px]">{skill.slug}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t.skillDetail?.type ?? "Type"}</span>
                <span className="text-[var(--text-primary)]">{skill.skill_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t.skillDetail?.version ?? "Version"}</span>
                <span className="text-[var(--text-primary)]">v{skill.version}</span>
              </div>
              {skill.author && (
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t.skillDetail?.author ?? "Author"}</span>
                  <span className="text-[var(--text-primary)]">{skill.author}</span>
                </div>
              )}
            </div>
          </div>
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4">
            <div className="flex items-center gap-2 mb-3">
              <Clock size={14} className="text-[var(--accent)]" />
              <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.skillDetail?.timeline ?? "Timeline"}</span>
            </div>
            <div className="flex flex-col gap-2 text-[12px]">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t.skillDetail?.status ?? "Status"}</span>
                <span
                  className="px-1.5 py-0.5 rounded text-[10px]"
                  style={{ background: badge.bg, color: badge.color }}
                >
                  {badge.label}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t.skillDetail?.enabledState ?? "Enabled State"}</span>
                <span style={{ color: skill.enabled ? "var(--success-fg)" : "var(--error)" }}>
                  {skill.enabled ? (t.skillDetail?.enabled ?? "Enabled") : (t.skillDetail?.disabled ?? "Disabled")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t.skillDetail?.systemProtection ?? "System Protection"}</span>
                <span className="text-[var(--text-primary)]">
                  {skill.is_system_protected ? (t.common?.yes ?? "Yes") : (t.common?.no ?? "No")}
                </span>
              </div>
              {skill.created_at && (
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t.skillDetail?.createdAt ?? "Created"}</span>
                  <span className="text-[var(--text-primary)] text-[11px]">
                    {new Date(skill.created_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tags */}
        {skill.tags && skill.tags.length > 0 && (
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Tag size={14} className="text-[var(--accent)]" />
              <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.skillDetail?.tags ?? "Tags"}</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {skill.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded text-[11px] bg-[var(--bg-active)] text-[var(--text-primary)]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Schema / Config */}
        {(skill.input_schema || skill.output_schema || skill.config) && (
          <div className="rounded border border-[var(--border)] bg-[var(--bg-surface)] p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Code2 size={14} className="text-[var(--accent)]" />
              <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.skillDetail?.schemaConfig ?? "Schema / Config"}</span>
            </div>
            <pre className="text-[11px] text-[var(--text-primary)] bg-[var(--bg-base)] rounded p-3 overflow-auto max-h-[300px] font-mono">
              {JSON.stringify(
                {
                  ...(skill.input_schema && { input_schema: skill.input_schema }),
                  ...(skill.output_schema && { output_schema: skill.output_schema }),
                  ...(skill.config && { config: skill.config }),
                },
                null,
                2,
              )}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
