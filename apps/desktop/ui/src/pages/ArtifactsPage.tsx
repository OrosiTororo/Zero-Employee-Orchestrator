import { useState } from "react"
import { FileBox, Grid, List, Download, Eye } from "lucide-react"

export function ArtifactsPage() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")

  // Placeholder data
  const artifacts: {
    id: string
    name: string
    type: string
    size: string
    ticketId: string
    created: string
  }[] = []

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <FileBox size={18} className="text-[#007acc]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">成果物</h2>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => setViewMode("grid")}
              className="p-1.5 rounded"
              style={{
                background: viewMode === "grid" ? "#3e3e42" : "transparent",
                color: viewMode === "grid" ? "#cccccc" : "#6a6a6a",
              }}
            >
              <Grid size={16} />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className="p-1.5 rounded"
              style={{
                background: viewMode === "list" ? "#3e3e42" : "transparent",
                color: viewMode === "list" ? "#cccccc" : "#6a6a6a",
              }}
            >
              <List size={16} />
            </button>
          </div>
        </div>

        {artifacts.length === 0 ? (
          <div className="rounded px-4 py-8 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
            成果物はまだありません。チケットの実行結果としてここに表示されます。
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-3 gap-3">
            {artifacts.map((a) => (
              <div
                key={a.id}
                className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526] hover:border-[#007acc] transition-colors"
              >
                <div className="text-[13px] text-[#cccccc] mb-1 truncate">
                  {a.name}
                </div>
                <div className="text-[11px] text-[#6a6a6a] mb-2">
                  {a.type} - {a.size}
                </div>
                <div className="flex gap-2">
                  <button className="flex items-center gap-1 text-[11px] text-[#007acc]">
                    <Eye size={12} />
                    表示
                  </button>
                  <button className="flex items-center gap-1 text-[11px] text-[#007acc]">
                    <Download size={12} />
                    ダウンロード
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            {artifacts.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between rounded px-4 py-2 border border-[#3e3e42] bg-[#252526] hover:border-[#007acc] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileBox size={14} className="text-[#007acc]" />
                  <span className="text-[13px] text-[#cccccc]">{a.name}</span>
                  <span className="text-[11px] text-[#6a6a6a]">{a.type}</span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-[#6a6a6a]">
                  <span>{a.size}</span>
                  <span>{a.created}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
