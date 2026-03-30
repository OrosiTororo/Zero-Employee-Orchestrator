import { useState, useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import {
  Plus,
  Package,
  Search,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Shield,
  RefreshCw,
} from "lucide-react"
import { useT } from "@/shared/i18n"

const API_BASE = "/api/v1/registry"

interface SkillItem {
  id: string
  slug: string
  name: string
  skill_type: string
  description: string | null
  version?: string
  status: string
  is_system_protected: boolean
  enabled: boolean
}

type TabKey = "my" | "marketplace"

export function SkillsPage() {
  const [search, setSearch] = useState("")
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabKey>("my")
  const navigate = useNavigate()
  const t = useT()

  const fetchSkills = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/skills?include_disabled=true`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSkills(data)
    } catch {
      setError(t.skills.fetchError)
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    fetchSkills()
  }, [fetchSkills])

  const handleToggle = async (skill: SkillItem) => {
    if (skill.is_system_protected) return
    try {
      const res = await fetch(`${API_BASE}/skills/${skill.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !skill.enabled }),
      })
      if (res.status === 403) {
        const data = await res.json()
        alert(data.detail || t.skills.notPermitted)
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchSkills()
    } catch (e) {
      console.error("Toggle failed:", e)
    }
  }

  const handleDelete = async (skill: SkillItem) => {
    if (skill.is_system_protected) {
      alert(t.skills.cannotDeleteSystem)
      return
    }
    if (!confirm(`${t.skills.confirmDelete}${skill.name}`)) return

    try {
      const res = await fetch(`${API_BASE}/skills/${skill.id}`, {
        method: "DELETE",
      })
      if (res.status === 403) {
        const data = await res.json()
        alert(data.detail || t.skills.notPermitted)
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchSkills()
    } catch (e) {
      console.error("Delete failed:", e)
    }
  }

  const mySkills = skills.filter((s) => !s.is_system_protected)
  const systemSkills = skills.filter((s) => s.is_system_protected)

  const displaySkills = activeTab === "my" ? [...systemSkills, ...mySkills] : []

  const filtered = displaySkills.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      (s.description ?? "").toLowerCase().includes(search.toLowerCase()) ||
      s.slug.toLowerCase().includes(search.toLowerCase()),
  )

  const tabs: { key: TabKey; label: string }[] = [
    { key: "my", label: t.skills.mySkills },
    { key: "marketplace", label: t.skills.marketplace },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Package size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.skills.title}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchSkills}
              className="flex items-center gap-1 px-2 py-1.5 rounded text-[12px] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border)]"
            >
              <RefreshCw size={12} />
            </button>
            <button
              onClick={() => navigate("/skills/create")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white"
            >
              <Plus size={14} />
              {t.skills.newSkill}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 border-b border-[var(--border)]">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="px-4 py-2 text-[12px] transition-colors relative"
              style={{
                color: activeTab === tab.key ? "var(--text-primary)" : "var(--text-muted)",
                borderBottom: activeTab === tab.key ? "2px solid var(--accent)" : "2px solid transparent",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.skills.searchPlaceholder}
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded px-4 py-3 mb-4 text-[12px] border border-[var(--error)] bg-[#4a1a1a] text-[var(--error)]">
            {error}
          </div>
        )}

        {/* Content */}
        {activeTab === "marketplace" ? (
          <div className="rounded px-4 py-12 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            <Package size={32} className="mx-auto mb-3 opacity-40" />
            <p>{t.skills.marketplaceComingSoon}</p>
          </div>
        ) : loading ? (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            {t.common.loading}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filtered.length === 0 ? (
              <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
                {skills.length === 0
                  ? t.skills.emptyState
                  : t.skills.noMatch}
              </div>
            ) : (
              <>
              {filtered.some(s => s.is_system_protected) && (
                <div className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-medium px-1 pt-2 pb-1">
                  {t.skills.systemRequired ?? "System"}
                </div>
              )}
              {filtered.filter(s => s.is_system_protected).map((skill) => (
                <SkillListItem key={skill.id} skill={skill} navigate={navigate} handleToggle={handleToggle} handleDelete={handleDelete} t={t} />
              ))}
              {filtered.some(s => !s.is_system_protected) && (
                <div className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-medium px-1 pt-3 pb-1 border-t border-[var(--border)] mt-1">
                  {t.skills.mySkills ?? "My Skills"}
                </div>
              )}
              {filtered.filter(s => !s.is_system_protected).map((skill) => (
                <SkillListItem key={skill.id} skill={skill} navigate={navigate} handleToggle={handleToggle} handleDelete={handleDelete} t={t} />
              ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function SkillListItem({ skill, navigate, handleToggle, handleDelete, t }: {
  skill: SkillItem
  navigate: (path: string) => void
  handleToggle: (skill: SkillItem) => void
  handleDelete: (skill: SkillItem) => void
  t: ReturnType<typeof useT>
}) {
  return (
    <div
      className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors cursor-pointer"
      style={{ opacity: skill.enabled ? 1 : 0.5 }}
      onClick={() => navigate(`/skills/${skill.id}`)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Package size={14} className="text-[var(--accent)]" />
          <span className="text-[13px] font-mono text-[var(--info)]">{skill.name}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-input)] text-[var(--text-muted)]">
            {skill.skill_type}
          </span>
          {skill.is_system_protected && (
            <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded bg-[#dcdcaa20] text-[var(--warning)]">
              <Shield size={10} />
              {t.skills.systemRequired}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => { e.stopPropagation(); handleToggle(skill) }}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            title={skill.is_system_protected ? t.skills.cannotDisableSystem : skill.enabled ? t.skills.disable : t.skills.enable}
            disabled={skill.is_system_protected}
          >
            {skill.enabled ? <ToggleRight size={20} className="text-[var(--success-fg)]" /> : <ToggleLeft size={20} />}
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); handleDelete(skill) }}
            className="text-[var(--text-muted)] hover:text-[var(--error)]"
            title={skill.is_system_protected ? t.skills.cannotDeleteSystem : t.common.delete}
            disabled={skill.is_system_protected}
            style={{ opacity: skill.is_system_protected ? 0.3 : 1 }}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      <p className="mt-1 text-[12px] pl-6 text-[var(--text-secondary)]">
        {skill.description || t.skills.noDescription}
      </p>
    </div>
  )
}
