import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Plus, Package, Search } from "lucide-react"

const statusBadges: Record<string, { label: string; color: string; bg: string }> = {
  verified: { label: "検証済", color: "#4ec9b0", bg: "#4ec9b020" },
  experimental: { label: "実験的", color: "#dcdcaa", bg: "#dcdcaa20" },
  private: { label: "プライベート", color: "#007acc", bg: "#007acc20" },
  deprecated: { label: "非推奨", color: "#f44747", bg: "#f4474720" },
}

export function SkillsPage() {
  const [search, setSearch] = useState("")
  const navigate = useNavigate()

  // Placeholder data
  const skills: {
    name: string
    description: string
    status: string
    version: string
  }[] = []

  const filtered = skills.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.description.toLowerCase().includes(search.toLowerCase()),
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
          </div>
          <button
            onClick={() => navigate("/skills/create")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white"
          >
            <Plus size={14} />
            新規スキル
          </button>
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

        {/* Skill List */}
        <div className="flex flex-col gap-2">
          {filtered.length === 0 ? (
            <div className="rounded px-4 py-8 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
              {skills.length === 0
                ? "スキルはまだ登録されていません。自然言語で新規スキルを作成してください。"
                : "一致するスキルが見つかりませんでした。"}
            </div>
          ) : (
            filtered.map((skill) => {
              const badge = statusBadges[skill.status] ?? statusBadges.private
              return (
                <div
                  key={skill.name}
                  className="rounded px-4 py-3 cursor-pointer border border-[#3e3e42] bg-[#252526] hover:border-[#007acc] transition-colors"
                >
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
                      style={{ background: badge.bg, color: badge.color }}
                    >
                      {badge.label}
                    </span>
                  </div>
                  <p className="mt-1 text-[12px] pl-6 text-[#969696]">
                    {skill.description}
                  </p>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
