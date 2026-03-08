import { Coins, TrendingUp, ShieldAlert, Receipt } from "lucide-react"

export function CostsPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <Coins size={18} className="text-[#dcdcaa]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">コスト管理</h2>
        </div>

        {/* Budget Policies */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <ShieldAlert size={14} className="text-[#dcdcaa]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              予算ポリシー
            </span>
          </div>
          <div className="px-4 py-4">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="rounded p-3 border border-[#3e3e42] bg-[#1e1e1e]">
                <div className="text-[11px] text-[#6a6a6a] mb-1">日次上限</div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  未設定
                </div>
              </div>
              <div className="rounded p-3 border border-[#3e3e42] bg-[#1e1e1e]">
                <div className="text-[11px] text-[#6a6a6a] mb-1">
                  週次上限
                </div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  未設定
                </div>
              </div>
              <div className="rounded p-3 border border-[#3e3e42] bg-[#1e1e1e]">
                <div className="text-[11px] text-[#6a6a6a] mb-1">
                  月次上限
                </div>
                <div className="text-[16px] font-semibold text-[#cccccc]">
                  未設定
                </div>
              </div>
            </div>
            <div className="text-[12px] text-[#6a6a6a]">
              予算上限を設定すると、コストが閾値に達した際に自動的にタスクを一時停止します。
            </div>
          </div>
        </div>

        {/* Spending Breakdown */}
        <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <TrendingUp size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              支出内訳
            </span>
          </div>
          <div className="px-4 py-4">
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div>
                <div className="text-[11px] text-[#6a6a6a]">今日</div>
                <div className="text-[18px] font-semibold text-[#cccccc]">
                  $0.00
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">今週</div>
                <div className="text-[18px] font-semibold text-[#cccccc]">
                  $0.00
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">今月</div>
                <div className="text-[18px] font-semibold text-[#cccccc]">
                  $0.00
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#6a6a6a]">累計</div>
                <div className="text-[18px] font-semibold text-[#cccccc]">
                  $0.00
                </div>
              </div>
            </div>
            <div className="text-center text-[12px] text-[#6a6a6a] py-4 border-t border-[#3e3e42]">
              モデル別・チケット別のコスト内訳はタスク実行後に表示されます。
            </div>
          </div>
        </div>

        {/* Cost Ledger */}
        <div className="rounded border border-[#3e3e42] bg-[#252526]">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
            <Receipt size={14} className="text-[#007acc]" />
            <span className="text-[12px] font-medium text-[#cccccc]">
              コスト台帳
            </span>
          </div>
          <div className="px-4">
            {/* Table Header */}
            <div className="grid grid-cols-5 gap-2 py-2 text-[11px] text-[#6a6a6a] border-b border-[#3e3e42]">
              <span>日時</span>
              <span>チケット</span>
              <span>モデル</span>
              <span>トークン</span>
              <span className="text-right">コスト</span>
            </div>
            <div className="py-6 text-center text-[12px] text-[#6a6a6a]">
              コスト記録はまだありません。
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
