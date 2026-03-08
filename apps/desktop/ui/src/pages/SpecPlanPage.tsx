import { useParams, useNavigate } from "react-router-dom"
import {
  FileText,
  GitCompare,
  ListTree,
  Coins,
  Link,
  ArrowLeft,
} from "lucide-react"

export function SpecPlanPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate(`/tickets/${id}`)}
            className="text-[#6a6a6a] hover:text-[#cccccc]"
          >
            <ArrowLeft size={18} />
          </button>
          <FileText size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">
            仕様・計画: チケット {id}
          </h2>
        </div>

        {/* Spec Version Comparison */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <GitCompare size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              仕様バージョン比較
            </span>
          </div>
          <div className="px-4 py-4">
            <div className="flex gap-3 mb-3">
              <select className="px-2 py-1 rounded text-[12px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] outline-none">
                <option>v1 (最新)</option>
              </select>
              <span className="text-[#6a6a6a] flex items-center">vs</span>
              <select className="px-2 py-1 rounded text-[12px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] outline-none">
                <option>ベースライン</option>
              </select>
            </div>
            <div className="rounded p-3 text-[12px] text-[#6a6a6a] border border-[#3e3e42] bg-[#1e1e1e] text-center">
              仕様のバージョンがまだありません。
            </div>
          </div>
        </div>

        {/* Plan Summary + Cost */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <Coins size={14} className="text-[#dcdcaa]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              計画サマリー・コスト見積
            </span>
          </div>
          <div className="px-4 py-4">
            <div className="grid grid-cols-3 gap-4 mb-3">
              <div>
                <div className="text-[11px] text-[#6a6a6a]">タスク数</div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  0
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">推定コスト</div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  $0.00
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">推定所要時間</div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  --
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Task DAG */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <ListTree size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              タスク DAG
            </span>
          </div>
          <div className="px-4 py-6 text-center text-[12px] text-[#6a6a6a]">
            タスクの依存関係グラフはまだ生成されていません。
          </div>
        </div>

        {/* Dependencies */}
        <div className="rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <Link size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              依存関係
            </span>
          </div>
          <div className="px-4 py-4 text-center text-[12px] text-[#6a6a6a]">
            外部依存関係はありません。
          </div>
        </div>
      </div>
    </div>
  )
}
