import { useState } from "react"
import { Puzzle, Search, Download, Trash2, ToggleLeft, ToggleRight } from "lucide-react"

export function PluginsPage() {
  const [search, setSearch] = useState("")

  // Placeholder data
  const installed: {
    id: string
    name: string
    description: string
    version: string
    enabled: boolean
    author: string
  }[] = []

  const available: {
    id: string
    name: string
    description: string
    version: string
    author: string
    downloads: number
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <Puzzle size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">
            プラグイン管理
          </h2>
        </div>

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

        {/* Installed */}
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-3">
            インストール済み
          </div>
          {installed.length === 0 ? (
            <div className="rounded px-4 py-6 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
              インストール済みのプラグインはありません。
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {installed.map((p) => (
                <div
                  key={p.id}
                  className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] text-[#cccccc]">
                          {p.name}
                        </span>
                        <span className="text-[10px] text-[#6a6a6a]">
                          v{p.version}
                        </span>
                      </div>
                      <div className="text-[11px] text-[#6a6a6a] mt-0.5">
                        {p.description}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="text-[#6a6a6a] hover:text-[#cccccc]">
                        {p.enabled ? (
                          <ToggleRight size={20} className="text-[#4ec9b0]" />
                        ) : (
                          <ToggleLeft size={20} />
                        )}
                      </button>
                      <button className="text-[#6a6a6a] hover:text-[#f44747]">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available */}
        <div>
          <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-3">
            利用可能
          </div>
          {available.length === 0 ? (
            <div className="rounded px-4 py-6 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
              利用可能なプラグインはまだありません。コミュニティプラグインは今後追加予定です。
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {available.map((p) => (
                <div
                  key={p.id}
                  className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526]"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] text-[#cccccc]">
                          {p.name}
                        </span>
                        <span className="text-[10px] text-[#6a6a6a]">
                          v{p.version}
                        </span>
                        <span className="text-[10px] text-[#6a6a6a]">
                          by {p.author}
                        </span>
                      </div>
                      <div className="text-[11px] text-[#6a6a6a] mt-0.5">
                        {p.description}
                      </div>
                    </div>
                    <button className="flex items-center gap-1 px-3 py-1 rounded text-[11px] bg-[#007acc] text-white">
                      <Download size={12} />
                      インストール
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
