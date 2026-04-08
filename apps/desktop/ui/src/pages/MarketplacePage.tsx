import { useState, useEffect, useCallback } from "react"
import { Store, Search, Package, Puzzle, Blocks, Download, Star, RefreshCw } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"
import { useToastStore } from "@/shared/ui/ErrorToast"

type TabKey = "all" | "skills" | "plugins" | "extensions"

interface MarketplaceItem {
  id: string
  name: string
  description: string
  type: "skill" | "plugin" | "extension"
  author: string
  downloads: number
  rating: number
  installed: boolean
}

interface RegistryItem {
  id: string
  slug: string
  name: string
  description: string | null
  version: string
  status: string
  enabled: boolean
  is_system_protected: boolean
}

export function MarketplacePage() {
  const t = useT()
  const addToast = useToastStore((s) => s.addToast)
  const [search, setSearch] = useState("")
  const [activeTab, setActiveTab] = useState<TabKey>("all")
  const [items, setItems] = useState<MarketplaceItem[]>([])
  const [loading, setLoading] = useState(true)

  const loadItems = useCallback(async () => {
    setLoading(true)
    try {
      const [skillsRes, pluginsRes, extensionsRes] = await Promise.all([
        api.get<{ skills: RegistryItem[] }>("/registry/skills").catch(() => ({ skills: [] })),
        api.get<{ plugins: RegistryItem[] }>("/registry/plugins").catch(() => ({ plugins: [] })),
        api.get<{ extensions: RegistryItem[] }>("/registry/extensions").catch(() => ({ extensions: [] })),
      ])

      const mapped: MarketplaceItem[] = [
        ...skillsRes.skills.map((s): MarketplaceItem => ({
          id: s.id, name: s.name, description: s.description ?? "",
          type: "skill", author: "ZEO", downloads: 0, rating: 0,
          installed: s.enabled,
        })),
        ...pluginsRes.plugins.map((p): MarketplaceItem => ({
          id: p.id, name: p.name, description: p.description ?? "",
          type: "plugin", author: "ZEO", downloads: 0, rating: 0,
          installed: p.enabled,
        })),
        ...extensionsRes.extensions.map((e): MarketplaceItem => ({
          id: e.id, name: e.name, description: e.description ?? "",
          type: "extension", author: "ZEO", downloads: 0, rating: 0,
          installed: e.enabled,
        })),
      ]
      setItems(mapped)
    } catch {
      addToast("Could not load marketplace items.")
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => { loadItems() }, [loadItems])

  const tabs: { key: TabKey; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }[] = [
    { key: "all", label: t.common.all, icon: Store },
    { key: "skills", label: t.nav.skills, icon: Package },
    { key: "plugins", label: t.nav.plugins, icon: Puzzle },
    { key: "extensions", label: t.nav.extensions, icon: Blocks },
  ]

  const filtered = items.filter(item => {
    if (activeTab !== "all" && item.type !== activeTab.replace(/s$/, "")) return false
    if (search.trim()) {
      const q = search.toLowerCase()
      return item.name.toLowerCase().includes(q) || item.description.toLowerCase().includes(q)
    }
    return true
  })

  const typeIcon = (type: string) => {
    switch (type) {
      case "skill": return <Package size={14} className="text-[var(--accent)]" />
      case "plugin": return <Puzzle size={14} className="text-[var(--success-fg)]" />
      case "extension": return <Blocks size={14} className="text-[var(--info)]" />
      default: return null
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Store size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.marketplace.title}</h2>
            <span className="text-[11px] text-[var(--text-muted)]">
              {items.length} items
            </span>
          </div>
          <button
            onClick={loadItems}
            className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-[var(--accent)]"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
        <p className="text-[12px] text-[var(--text-muted)] mb-5">{t.marketplace.subtitle}</p>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 border-b border-[var(--border)]">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="flex items-center gap-1.5 px-4 py-2 text-[12px] transition-colors"
              style={{
                color: activeTab === tab.key ? "var(--text-primary)" : "var(--text-muted)",
                borderBottom: activeTab === tab.key ? "2px solid var(--accent)" : "2px solid transparent",
              }}
            >
              <tab.icon size={14} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={t.marketplace.searchPlaceholder}
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
          />
        </div>

        {/* Content */}
        {loading ? (
          <div className="py-16 text-center text-[12px] text-[var(--text-muted)]">
            <RefreshCw size={20} className="mx-auto mb-2 animate-spin text-[var(--accent)]" />
            Loading...
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded px-4 py-16 text-center border border-[var(--border)]">
            <Store size={40} className="mx-auto mb-4 text-[var(--text-muted)] opacity-40" />
            <p className="text-[13px] text-[var(--text-primary)] mb-2">
              {search.trim() ? "No matching items" : t.marketplace.comingSoon}
            </p>
            <p className="text-[12px] text-[var(--text-muted)] max-w-[400px] mx-auto">
              {search.trim() ? "Try a different search term." : t.marketplace.comingSoonDesc}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filtered.map(item => (
              <div key={item.id} className="rounded p-4 border border-[var(--border)] bg-[var(--bg-surface)] hover:border-[var(--accent)] transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {typeIcon(item.type)}
                    <span className="text-[13px] font-medium text-[var(--text-primary)]">{item.name}</span>
                  </div>
                  {item.installed ? (
                    <span className="text-[10px] px-2 py-0.5 rounded text-[var(--success)]" style={{ background: "color-mix(in srgb, var(--success) 15%, transparent)" }}>
                      Installed
                    </span>
                  ) : (
                    <button
                      onClick={async () => {
                        try {
                          await api.post(`/registry/${item.type}s/install`, { slug: item.id, name: item.name, description: item.description })
                          await loadItems()
                        } catch {
                          addToast("Install failed.")
                        }
                      }}
                      className="flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-[var(--accent)] text-[var(--accent-fg)]"
                    >
                      <Download size={12} />
                      {t.marketplace.install}
                    </button>
                  )}
                </div>
                <p className="text-[12px] text-[var(--text-secondary)] mb-2 line-clamp-2">{item.description}</p>
                <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                  <span>{item.author}</span>
                  {item.rating > 0 && <span className="flex items-center gap-0.5"><Star size={10} />{item.rating}</span>}
                  {item.downloads > 0 && <span className="flex items-center gap-0.5"><Download size={10} />{item.downloads}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
