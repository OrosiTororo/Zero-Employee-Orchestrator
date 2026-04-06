import { useState } from "react"
import { Store, Search, Package, Puzzle, Blocks, Download, Star } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

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

export function MarketplacePage() {
  const t = useT()
  const [search, setSearch] = useState("")
  const [activeTab, setActiveTab] = useState<TabKey>("all")

  // Placeholder items - will be fetched from API
  const items: MarketplaceItem[] = []

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
        <div className="flex items-center gap-2 mb-1">
          <Store size={18} className="text-[var(--accent)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.marketplace.title}</h2>
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
        {filtered.length === 0 ? (
          <div className="rounded px-4 py-16 text-center border border-[var(--border)]">
            <Store size={40} className="mx-auto mb-4 text-[var(--text-muted)] opacity-40" />
            <p className="text-[13px] text-[var(--text-primary)] mb-2">{t.marketplace.comingSoon}</p>
            <p className="text-[12px] text-[var(--text-muted)] max-w-[400px] mx-auto">{t.marketplace.comingSoonDesc}</p>
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
                  <button
                    onClick={async () => {
                      try {
                        await api.post(`/registry/${item.type}s`, { slug: item.id, name: item.name, description: item.description })
                      } catch { /* marketplace not yet connected */ }
                    }}
                    className="flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-[var(--accent)] text-[var(--accent-fg)]"
                  >
                    <Download size={12} />
                    {t.marketplace.install}
                  </button>
                </div>
                <p className="text-[12px] text-[var(--text-secondary)] mb-2">{item.description}</p>
                <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                  <span>{item.author}</span>
                  <span className="flex items-center gap-0.5"><Star size={10} />{item.rating}</span>
                  <span className="flex items-center gap-0.5"><Download size={10} />{item.downloads}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
