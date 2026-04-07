import { useState, useEffect, useCallback } from "react"
import {
  Blocks,
  Search,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Shield,
  RefreshCw,
  Plus,
  Star,
} from "lucide-react"
import { useT } from "@/shared/i18n"
import { useToastStore } from "@/shared/ui/ErrorToast"
import { api } from "@/shared/api/client"

interface ExtensionItem {
  id: string
  slug: string
  name: string
  description: string | null
  version: string
  status: string
  is_system_protected: boolean
  enabled: boolean
  category?: string
}

type TabKey = "installed" | "marketplace"

export function ExtensionsPage() {
  const [search, setSearch] = useState("")
  const addToast = useToastStore((s) => s.addToast)
  const [extensions, setExtensions] = useState<ExtensionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabKey>("installed")
  const [showInstall, setShowInstall] = useState(false)
  const [installForm, setInstallForm] = useState({ slug: "", name: "", description: "" })
  const t = useT()

  const fetchExtensions = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<ExtensionItem[]>("/registry/extensions?include_disabled=true")
      setExtensions(data)
    } catch {
      addToast((t as unknown as Record<string, Record<string, string>>).errors?.extensionsFetchFailed ?? "Failed to fetch extensions")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchExtensions()
  }, [fetchExtensions])

  const handleToggle = async (ext: ExtensionItem) => {
    if (ext.is_system_protected) return
    try {
      await api.patch(`/registry/extensions/${ext.id}`, { enabled: !ext.enabled })
      await fetchExtensions()
    } catch (e: unknown) {
      addToast(e instanceof Error ? e.message : String(e) || "Toggle failed")
    }
  }

  const handleDelete = async (ext: ExtensionItem) => {
    if (ext.is_system_protected) {
      alert(t.extensions.cannotDeleteSystem)
      return
    }
    if (!confirm(`${t.extensions.confirmDelete}${ext.name}`)) return
    try {
      await api.delete(`/registry/extensions/${ext.id}`)
      await fetchExtensions()
    } catch (e: unknown) {
      addToast(e instanceof Error ? e.message : String(e) || "Delete failed")
    }
  }

  const handleInstall = async () => {
    if (!installForm.slug.trim() || !installForm.name.trim()) return
    try {
      await api.post("/registry/extensions", installForm)
      setShowInstall(false)
      setInstallForm({ slug: "", name: "", description: "" })
      await fetchExtensions()
    } catch (e: unknown) {
      addToast(e instanceof Error ? e.message : String(e) || "Install failed")
    }
  }

  const filtered = extensions.filter(
    (e) =>
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      (e.description ?? "").toLowerCase().includes(search.toLowerCase()) ||
      e.slug.toLowerCase().includes(search.toLowerCase()),
  )

  const tabs: { key: TabKey; label: string }[] = [
    { key: "installed", label: t.extensions.installed },
    { key: "marketplace", label: t.extensions.marketplace },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Blocks size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.extensions.title}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={fetchExtensions}
              className="flex items-center gap-1 px-2 py-1.5 rounded text-[12px] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border)]">
              <RefreshCw size={12} />
            </button>
            <button onClick={() => setShowInstall(!showInstall)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white">
              <Plus size={14} />
              {t.extensions.add}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 border-b border-[var(--border)]">
          {tabs.map((tab) => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className="px-4 py-2 text-[12px] transition-colors"
              style={{
                color: activeTab === tab.key ? "var(--text-primary)" : "var(--text-muted)",
                borderBottom: activeTab === tab.key ? "2px solid var(--accent)" : "2px solid transparent",
              }}>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Install Form */}
        {showInstall && (
          <div className="rounded p-4 mb-4 border border-[var(--border)] bg-[var(--bg-surface)]">
            <div className="text-[12px] font-medium text-[var(--text-primary)] mb-3">{t.extensions.addNew}</div>
            <div className="flex flex-col gap-2 mb-3">
              <input value={installForm.slug} onChange={(e) => setInstallForm({ ...installForm, slug: e.target.value })}
                placeholder={t.extensions.slugPlaceholder}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]" />
              <input value={installForm.name} onChange={(e) => setInstallForm({ ...installForm, name: e.target.value })}
                placeholder={t.extensions.namePlaceholder}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]" />
              <input value={installForm.description} onChange={(e) => setInstallForm({ ...installForm, description: e.target.value })}
                placeholder={t.extensions.descPlaceholder}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowInstall(false)}
                className="px-3 py-1.5 rounded text-[12px] text-[var(--text-muted)] border border-[var(--border)]">{t.common.cancel}</button>
              <button onClick={handleInstall} disabled={!installForm.slug.trim() || !installForm.name.trim()}
                className="px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white disabled:opacity-40">{t.extensions.add}</button>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-4">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder={t.extensions.searchPlaceholder}
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]" />
        </div>

        {/* Content */}
        {activeTab === "marketplace" ? (
          <div className="rounded px-4 py-12 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            <Star size={32} className="mx-auto mb-3 opacity-40" />
            <p className="mb-1">{t.extensions.marketplaceComingSoon}</p>
            <p className="text-[11px]">{t.extensions.marketplaceDesc}</p>
          </div>
        ) : loading ? (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            {t.common.loading}
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded px-4 py-6 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)]">
            {extensions.length === 0 ? t.extensions.emptyState : t.extensions.noMatch}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filtered.map((ext) => (
              <div key={ext.id} className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)]"
                style={{ opacity: ext.enabled ? 1 : 0.5 }}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Blocks size={14} className="text-[var(--accent)]" />
                      <span className="text-[13px] text-[var(--text-primary)]">{ext.name}</span>
                      {ext.category && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-input)] text-[var(--text-muted)]">{ext.category}</span>
                      )}
                      {ext.is_system_protected && (
                        <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded bg-[#dcdcaa20] text-[var(--warning)]">
                          <Shield size={10} />{t.extensions.systemRequired}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-[var(--text-muted)] mt-0.5 pl-6">{ext.description || t.extensions.noDescription}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleToggle(ext)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                      disabled={ext.is_system_protected}>
                      {ext.enabled ? <ToggleRight size={20} className="text-[var(--success-fg)]" /> : <ToggleLeft size={20} />}
                    </button>
                    <button onClick={() => handleDelete(ext)} className="text-[var(--text-muted)] hover:text-[var(--error)]"
                      disabled={ext.is_system_protected} style={{ opacity: ext.is_system_protected ? 0.3 : 1 }}>
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
