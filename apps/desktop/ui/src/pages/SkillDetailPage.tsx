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

const API_BASE = "/api/v1/registry"

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

const statusBadges: Record<string, { label: string; color: string; bg: string }> = {
  verified: { label: "検証済", color: "#4ec9b0", bg: "#4ec9b020" },
  experimental: { label: "実験的", color: "#dcdcaa", bg: "#dcdcaa20" },
  private: { label: "プライベート", color: "#007acc", bg: "#007acc20" },
  deprecated: { label: "非推奨", color: "#f44747", bg: "#f4474720" },
}

export function SkillDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [skill, setSkill] = useState<SkillDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSkill = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/skills/${id}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSkill(data)
    } catch (e) {
      setError("スキルの取得に失敗しました")
      console.error("Failed to fetch skill:", e)
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
      await fetchSkill()
    } catch (e) {
      console.error("Toggle failed:", e)
    }
  }

  const handleDelete = async () => {
    if (!skill || skill.is_system_protected) return
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
      navigate("/skills")
    } catch (e) {
      console.error("Delete failed:", e)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-[12px] text-[#6a6a6a]">
        読み込み中...
      </div>
    )
  }

  if (error || !skill) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-[900px] mx-auto px-6 py-6">
          <button
            onClick={() => navigate("/skills")}
            className="flex items-center gap-1 text-[12px] text-[#007acc] hover:underline mb-4"
          >
            <ArrowLeft size={14} />
            スキル一覧に戻る
          </button>
          <div className="rounded px-4 py-3 text-[12px] border border-[#f44747] bg-[#4a1a1a] text-[#f44747]">
            {error || "スキルが見つかりません"}
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
          className="flex items-center gap-1 text-[12px] text-[#007acc] hover:underline mb-4"
        >
          <ArrowLeft size={14} />
          スキル一覧に戻る
        </button>

        {/* Header */}
        <div className="rounded border border-[#3e3e42] bg-[#252526] p-4 mb-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded bg-[#007acc20] flex items-center justify-center">
                <Package size={20} className="text-[#007acc]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-[16px] font-medium text-[#cccccc]">
                    {skill.name}
                  </h2>
                  <span className="text-[11px] text-[#6a6a6a]">v{skill.version}</span>
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded"
                    style={{ background: badge.bg, color: badge.color }}
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
                <p className="text-[12px] text-[#969696] mt-1">
                  {skill.slug}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleToggle}
                className="flex items-center gap-1 px-3 py-1.5 rounded text-[12px] border border-[#3e3e42] text-[#cccccc] hover:bg-[#3c3c3c] transition-colors"
                disabled={skill.is_system_protected}
              >
                {skill.enabled ? (
                  <>
                    <ToggleRight size={16} className="text-[#4ec9b0]" />
                    有効
                  </>
                ) : (
                  <>
                    <ToggleLeft size={16} />
                    無効
                  </>
                )}
              </button>
              {!skill.is_system_protected && (
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-1 px-3 py-1.5 rounded text-[12px] border border-[#3e3e42] text-[#f44747] hover:bg-[#4a1a1a] transition-colors"
                >
                  <Trash2 size={14} />
                  削除
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="rounded border border-[#3e3e42] bg-[#252526] p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Info size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">説明</span>
          </div>
          <p className="text-[12px] text-[#969696] leading-relaxed">
            {skill.description || "説明なし"}
          </p>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="rounded border border-[#3e3e42] bg-[#252526] p-4">
            <div className="flex items-center gap-2 mb-3">
              <Tag size={14} className="text-[#007acc]" />
              <span className="text-[12px] font-medium text-[#cccccc]">メタデータ</span>
            </div>
            <div className="flex flex-col gap-2 text-[12px]">
              <div className="flex justify-between">
                <span className="text-[#6a6a6a]">ID</span>
                <span className="text-[#9cdcfe] font-mono text-[11px]">{skill.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6a6a6a]">Slug</span>
                <span className="text-[#cccccc] font-mono text-[11px]">{skill.slug}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6a6a6a]">タイプ</span>
                <span className="text-[#cccccc]">{skill.skill_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6a6a6a]">バージョン</span>
                <span className="text-[#cccccc]">v{skill.version}</span>
              </div>
              {skill.author && (
                <div className="flex justify-between">
                  <span className="text-[#6a6a6a]">作成者</span>
                  <span className="text-[#cccccc]">{skill.author}</span>
                </div>
              )}
            </div>
          </div>
          <div className="rounded border border-[#3e3e42] bg-[#252526] p-4">
            <div className="flex items-center gap-2 mb-3">
              <Clock size={14} className="text-[#007acc]" />
              <span className="text-[12px] font-medium text-[#cccccc]">タイムライン</span>
            </div>
            <div className="flex flex-col gap-2 text-[12px]">
              <div className="flex justify-between">
                <span className="text-[#6a6a6a]">ステータス</span>
                <span
                  className="px-1.5 py-0.5 rounded text-[10px]"
                  style={{ background: badge.bg, color: badge.color }}
                >
                  {badge.label}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6a6a6a]">有効状態</span>
                <span style={{ color: skill.enabled ? "#4ec9b0" : "#f44747" }}>
                  {skill.enabled ? "有効" : "無効"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6a6a6a]">システム保護</span>
                <span className="text-[#cccccc]">
                  {skill.is_system_protected ? "はい" : "いいえ"}
                </span>
              </div>
              {skill.created_at && (
                <div className="flex justify-between">
                  <span className="text-[#6a6a6a]">作成日</span>
                  <span className="text-[#cccccc] text-[11px]">
                    {new Date(skill.created_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tags */}
        {skill.tags && skill.tags.length > 0 && (
          <div className="rounded border border-[#3e3e42] bg-[#252526] p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Tag size={14} className="text-[#007acc]" />
              <span className="text-[12px] font-medium text-[#cccccc]">タグ</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {skill.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded text-[11px] bg-[#3c3c3c] text-[#cccccc]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Schema / Config */}
        {(skill.input_schema || skill.output_schema || skill.config) && (
          <div className="rounded border border-[#3e3e42] bg-[#252526] p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Code2 size={14} className="text-[#007acc]" />
              <span className="text-[12px] font-medium text-[#cccccc]">スキーマ / 設定</span>
            </div>
            <pre className="text-[11px] text-[#d4d4d4] bg-[#1e1e1e] rounded p-3 overflow-auto max-h-[300px] font-mono">
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
