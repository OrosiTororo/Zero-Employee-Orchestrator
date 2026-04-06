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
import { useT } from "@/shared/i18n"
import { useToastStore } from "@/shared/ui/ErrorToast"
import { api } from "@/shared/api/client"

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
  const addToast = useToastStore((s) => s.addToast)
  const [installForm, setInstallForm] = useState({ slug: "", name: "", description: "" })
  const t = useT()

  const fetchPlugins = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<PluginItem[]>("/registry/plugins?include_disabled=true")
      setPlugins(data)
    } catch {
      addToast("Failed to fetch plugins")
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
      await api.patch(`/registry/plugins/${plugin.id}`, { enabled: !plugin.enabled })
      await fetchPlugins()
    } catch (e: any) {
      addToast(e?.message || "Toggle failed")
    }
  }

  const handleDelete = async (plugin: PluginItem) => {
    if (plugin.is_system_protected) {
      alert(t.plugins.cannotDeleteSystem)
      return
    }
    if (!confirm(`${t.plugins.confirmDelete}${plugin.name}`)) return
    try {
      await api.delete(`/registry/plugins/${plugin.id}`)
      await fetchPlugins()
    } catch (e: any) {
      addToast(e?.message || "Delete failed")
    }
  }

  const handleInstall = async () => {
    if (!installForm.slug.trim() || !installForm.name.trim()) return
    try {
      await api.post("/registry/plugins", installForm)
      setShowInstall(false)
      setInstallForm({ slug: "", name: "", description: "" })
      await fetchPlugins()
    } catch (e: any) {
      addToast(e?.message || "Install failed")
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
            <Puzzle size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.plugins.title}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchPlugins}
              className="flex items-center gap-1 px-2 py-1.5 rounded text-[12px] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border)]"
            >
              <RefreshCw size={12} />
            </button>
            <button
              onClick={() => setShowInstall(!showInstall)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white"
            >
              <Plus size={14} />
              {t.plugins.add}
            </button>
          </div>
        </div>

        {/* Install Form */}
        {showInstall && (
          <div className="rounded p-4 mb-4 border border-[var(--border)] bg-[var(--bg-surface)]">
            <div className="text-[12px] font-medium text-[var(--text-primary)] mb-3">
              {t.plugins.addNew}
            </div>
            <div className="flex flex-col gap-2 mb-3">
              <input
                value={installForm.slug}
                onChange={(e) => setInstallForm({ ...installForm, slug: e.target.value })}
                placeholder={t.plugins.slugPlaceholder}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
              />
              <input
                value={installForm.name}
                onChange={(e) => setInstallForm({ ...installForm, name: e.target.value })}
                placeholder={t.plugins.namePlaceholder}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
              />
              <input
                value={installForm.description}
                onChange={(e) => setInstallForm({ ...installForm, description: e.target.value })}
                placeholder={t.plugins.descPlaceholder}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowInstall(false)}
                className="px-3 py-1.5 rounded text-[12px] text-[var(--text-muted)] border border-[var(--border)]"
              >
                {t.common.cancel}
              </button>
              <button
                onClick={handleInstall}
                disabled={!installForm.slug.trim() || !installForm.name.trim()}
                className="px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white disabled:opacity-40"
              >
                {t.plugins.add}
              </button>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-6">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.plugins.searchPlaceholder}
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
          />
        </div>

        {/* Plugin List */}
        {loading ? (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            {t.common.loading}
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded px-4 py-6 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            {plugins.length === 0
              ? t.plugins.emptyState
              : t.plugins.noMatch}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filtered.map((p) => (
              <div
                key={p.id}
                className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]"
                style={{ opacity: p.enabled ? 1 : 0.5 }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Puzzle size={14} className="text-[var(--accent)]" />
                      <span className="text-[13px] text-[var(--text-primary)]">
                        {p.name}
                      </span>
                      {p.is_system_protected && (
                        <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded bg-[#dcdcaa20] text-[var(--warning)]">
                          <Shield size={10} />
                          {t.plugins.systemRequired}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-[var(--text-muted)] mt-0.5 pl-6">
                      {p.description || t.plugins.noDescription}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggle(p)}
                      className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                      disabled={p.is_system_protected}
                    >
                      {p.enabled ? (
                        <ToggleRight size={20} className="text-[var(--success-fg)]" />
                      ) : (
                        <ToggleLeft size={20} />
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(p)}
                      className="text-[var(--text-muted)] hover:text-[var(--error)]"
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
