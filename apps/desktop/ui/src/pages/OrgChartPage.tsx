import { Network, Building2, Bot } from "lucide-react"

export function OrgChartPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <Network size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">組織図</h2>
        </div>

        {/* Departments */}
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-3">
            部門
          </div>
          <div className="flex flex-col gap-2">
            <OrgNode
              icon={Building2}
              name="経営企画部"
              description="戦略立案・意思決定"
              agents={0}
            />
            <OrgNode
              icon={Building2}
              name="開発部"
              description="プロダクト開発・技術"
              agents={0}
            />
            <OrgNode
              icon={Building2}
              name="マーケティング部"
              description="集客・ブランド・コンテンツ"
              agents={0}
            />
            <OrgNode
              icon={Building2}
              name="カスタマーサポート部"
              description="顧客対応・問い合わせ管理"
              agents={0}
            />
          </div>
        </div>

        {/* Teams */}
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-3">
            チーム
          </div>
          <div className="rounded px-4 py-6 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
            チームはまだ構成されていません。チケットの作成に応じて自動的に編成されます。
          </div>
        </div>

        {/* Agents */}
        <div>
          <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-3">
            エージェント
          </div>
          <div className="rounded px-4 py-6 text-center text-[12px] border border-[#3e3e42] text-[#6a6a6a]">
            アクティブなエージェントはいません。業務を依頼するとエージェントが自動的に割り当てられます。
          </div>
        </div>
      </div>
    </div>
  )
}

function OrgNode({
  icon: Icon,
  name,
  description,
  agents,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  name: string
  description: string
  agents: number
}) {
  return (
    <div className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526] hover:border-[#007acc] transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Icon size={16} className="text-[#007acc]" />
          <div>
            <div className="text-[13px] text-[#cccccc]">{name}</div>
            <div className="text-[11px] text-[#6a6a6a]">{description}</div>
          </div>
        </div>
        <div className="flex items-center gap-1 text-[11px] text-[#6a6a6a]">
          <Bot size={12} />
          <span>{agents} エージェント</span>
        </div>
      </div>
    </div>
  )
}
