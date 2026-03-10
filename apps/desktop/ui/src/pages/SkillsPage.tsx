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

const API_BASE = "/api/v1/registry"

const statusBadges: Record<string, { label: string; color: string; bg: string }> = {
  verified: { label: "検証済", color: "#4ec9b0", bg: "#4ec9b020" },
  experimental: { label: "実験的", color: "#dcdcaa", bg: "#dcdcaa20" },
  private: { label: "プライベート", color: "#007acc", bg: "#007acc20" },
  deprecated: { label: "非推奨", color: "#f44747", bg: "#f4474720" },
}

interface SkillItem {
  id: string
  slug: string
  name: string
  skill_type: string
  description: string | null
  version: string
  status: string
  is_system_protected: boolean
  enabled: boolean
}

export function SkillsPage() {
  const [search, setSearch] = useState("")
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const fetchSkills = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/skills?include_disabled=true`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSkills(data)
    } catch (e) {
      setError("スキルの取得に失敗しました")
      console.error("Failed to fetch skills:", e)
    } finally {
      setLoading(false)
    }
  }, [])

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
        alert(data.detail || "この操作は許可されていません")
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
      alert("システム必須スキルは削除できません")
      return
    }
    if (!confirm(`スキル「${skill.name}」を削除しますか?`)) return

    try {
      const res = await fetch(`${API_BASE}/skills/${skill.id}`, {
        method: "DELETE",
      })
      if (res.status === 403) {
        const data = await res.json()
        alert(data.detail || "この操作は許可されていません")
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchSkills()
    } catch (e) {
      console.error("Delete failed:", e)
    }
  }

  const filtered = skills.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      (s.description ?? "").toLowerCase().includes(search.toLowerCase()) ||
      s.slug.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Package size={18} className="text-[#007acc]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              スキルレジストリ
            </h2>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#007acc20] text-[#007acc]">
              v0.1
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchSkills}
              className="flex items-center gap-1 px-2 py-1.5 rounded text-[12px] text-[#6a6a6a] hover:text-[#cccccc] border border-[#3e3e42]"
            >
              <RefreshCw size={12} />
            </button>
            <button
              onClick={() => navigate("/skills/create")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white"
            >
              <Plus size={14} />
              新規スキル
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="スキルを検索..."
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42]"
          />
        </div>

        {/* Status Filter */}
        <div className="flex gap-1 mb-4">
          {Object.entries(statusBadges).map(([key, badge]) => (
            <span
              key={key}
              className="px-2 py-0.5 rounded text-[11px]"
              style={{ background: badge.bg, color: badge.color }}
            >
              {badge.label}
            </span>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="rounded px-4 py-3 mb-4 text-[12px] border border-[#f44747] bg-[#4a1a1a] text-[#f44747]">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
            読み込み中...
          </div>
        )}

        {/* Skill List */}
        {!loading && (
          <div className="flex flex-col gap-2">
            {filtered.length === 0 ? (
              <div className="rounded px-4 py-8 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
                {skills.length === 0
                  ? "スキルはまだ登録されていません。自然言語で新規スキルを作成してください。"
                  : "一致するスキルが見つかりませんでした。"}
              </div>
            ) : (
              filtered.map((skill) => {
                const badge =
                  statusBadges[skill.status] ?? statusBadges.private
                return (
                  <div
                    key={skill.id}
                    className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526] hover:border-[#007acc] transition-colors"
                    style={{ opacity: skill.enabled ? 1 : 0.5 }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Package size={14} className="text-[#007acc]" />
                        <span className="text-[13px] font-mono text-[#9cdcfe]">
                          {skill.name}
                        </span>
                        <span className="text-[10px] text-[#6a6a6a]">
                          v{skill.version}
                        </span>
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded"
                          style={{
                            background: badge.bg,
                            color: badge.color,
                          }}
                        >
                          {badge.label}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#3c3c3c] text-[#6a6a6a]">
                          {skill.skill_type}
                        </span>
                        {skill.is_system_protected && (
                          <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded bg-[#dcdcaa20] text-[#dcdcaa]">
                            <Shield size={10} />
                            システム必須
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggle(skill)}
                          className="text-[#6a6a6a] hover:text-[#cccccc]"
                          title={
                            skill.is_system_protected
                              ? "システム必須スキルは無効化できません"
                              : skill.enabled
                                ? "無効化"
                                : "有効化"
                          }
                          disabled={skill.is_system_protected}
                        >
                          {skill.enabled ? (
                            <ToggleRight
                              size={20}
                              className="text-[#4ec9b0]"
                            />
                          ) : (
                            <ToggleLeft size={20} />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(skill)}
                          className="text-[#6a6a6a] hover:text-[#f44747]"
                          title={
                            skill.is_system_protected
                              ? "システム必須スキルは削除できません"
                              : "削除"
                          }
                          disabled={skill.is_system_protected}
                          style={{
                            opacity: skill.is_system_protected ? 0.3 : 1,
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    <p className="mt-1 text-[12px] pl-6 text-[#969696]">
                      {skill.description || "説明なし"}
                    </p>
                  </div>
                )
              })
            )}
          </div>
        )}
      </div>
    </div>
  )
}
