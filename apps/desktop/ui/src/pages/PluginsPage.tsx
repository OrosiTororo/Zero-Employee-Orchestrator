import { useState, useEffect, useCallback } from "react"
import {
  Puzzle,
  Search,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Shield,
  RefreshCw,
  Plus,
} from "lucide-react"

const API_BASE = "/api/v1/registry"

interface PluginItem {
  id: string
  slug: string
  name: string
  description: string | null
  version: string
  status: string
  is_system_protected: boolean
  enabled: boolean
}

export function PluginsPage() {
  const [search, setSearch] = useState("")
  const [plugins, setPlugins] = useState<PluginItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showInstall, setShowInstall] = useState(false)
  const [installForm, setInstallForm] = useState({ slug: "", name: "", description: "" })

  const fetchPlugins = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/plugins?include_disabled=true`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setPlugins(await res.json())
    } catch (e) {
      console.error("Failed to fetch plugins:", e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPlugins()
  }, [fetchPlugins])

  const handleToggle = async (plugin: PluginItem) => {
    if (plugin.is_system_protected) return
    try {
      const res = await fetch(`${API_BASE}/plugins/${plugin.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !plugin.enabled }),
      })
      if (res.status === 403) {
        const data = await res.json()
        alert(data.detail || "この操作は許可されていません")
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchPlugins()
    } catch (e) {
      console.error("Toggle failed:", e)
    }
  }

  const handleDelete = async (plugin: PluginItem) => {
    if (plugin.is_system_protected) {
      alert("システム必須プラグインは削除できません")
      return
    }
    if (!confirm(`プラグイン「${plugin.name}」を削除しますか?`)) return

    try {
      const res = await fetch(`${API_BASE}/plugins/${plugin.id}`, {
        method: "DELETE",
      })
      if (res.status === 403) {
        const data = await res.json()
        alert(data.detail || "この操作は許可されていません")
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchPlugins()
    } catch (e) {
      console.error("Delete failed:", e)
    }
  }

  const handleInstall = async () => {
    if (!installForm.slug.trim() || !installForm.name.trim()) return
    try {
      const res = await fetch(`${API_BASE}/plugins`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(installForm),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        alert(data.detail || `エラー: HTTP ${res.status}`)
        return
      }
      setShowInstall(false)
      setInstallForm({ slug: "", name: "", description: "" })
      await fetchPlugins()
    } catch (e) {
      console.error("Install failed:", e)
    }
  }

  const filtered = plugins.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.description ?? "").toLowerCase().includes(search.toLowerCase()) ||
      p.slug.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Puzzle size={18} className="text-[#007acc]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              プラグイン管理
            </h2>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#007acc20] text-[#007acc]">
              v0.1
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchPlugins}
              className="flex items-center gap-1 px-2 py-1.5 rounded text-[12px] text-[#6a6a6a] hover:text-[#cccccc] border border-[#3e3e42]"
            >
              <RefreshCw size={12} />
            </button>
            <button
              onClick={() => setShowInstall(!showInstall)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white"
            >
              <Plus size={14} />
              追加
            </button>
          </div>
        </div>

        {/* Install Form */}
        {showInstall && (
          <div className="rounded p-4 mb-4 border border-[#3e3e42] bg-[#252526]">
            <div className="text-[12px] font-medium text-[#cccccc] mb-3">
              新規プラグインの追加
            </div>
            <div className="flex flex-col gap-2 mb-3">
              <input
                value={installForm.slug}
                onChange={(e) => setInstallForm({ ...installForm, slug: e.target.value })}
                placeholder="slug (例: my-plugin)"
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42]"
              />
              <input
                value={installForm.name}
                onChange={(e) => setInstallForm({ ...installForm, name: e.target.value })}
                placeholder="プラグイン名"
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42]"
              />
              <input
                value={installForm.description}
                onChange={(e) => setInstallForm({ ...installForm, description: e.target.value })}
                placeholder="説明 (任意)"
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42]"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowInstall(false)}
                className="px-3 py-1.5 rounded text-[12px] text-[#6a6a6a] border border-[#3e3e42]"
              >
                キャンセル
              </button>
              <button
                onClick={handleInstall}
                disabled={!installForm.slug.trim() || !installForm.name.trim()}
                className="px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white"
              >
                追加
              </button>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-6">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="プラグインを検索..."
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42]"
          />
        </div>

        {/* Plugin List */}
        {loading ? (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
            読み込み中...
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded px-4 py-6 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
            {plugins.length === 0
              ? "インストール済みのプラグインはありません。"
              : "一致するプラグインが見つかりませんでした。"}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filtered.map((p) => (
              <div
                key={p.id}
                className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]"
                style={{ opacity: p.enabled ? 1 : 0.5 }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Puzzle size={14} className="text-[#007acc]" />
                      <span className="text-[13px] text-[#cccccc]">
                        {p.name}
                      </span>
                      <span className="text-[10px] text-[#6a6a6a]">
                        v{p.version}
                      </span>
                      {p.is_system_protected && (
                        <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded bg-[#dcdcaa20] text-[#dcdcaa]">
                          <Shield size={10} />
                          システム必須
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-[#6a6a6a] mt-0.5 pl-6">
                      {p.description || "説明なし"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggle(p)}
                      className="text-[#6a6a6a] hover:text-[#cccccc]"
                      disabled={p.is_system_protected}
                    >
                      {p.enabled ? (
                        <ToggleRight size={20} className="text-[#4ec9b0]" />
                      ) : (
                        <ToggleLeft size={20} />
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(p)}
                      className="text-[#6a6a6a] hover:text-[#f44747]"
                      disabled={p.is_system_protected}
                      style={{ opacity: p.is_system_protected ? 0.3 : 1 }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
