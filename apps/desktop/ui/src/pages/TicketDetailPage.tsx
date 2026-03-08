import { useParams, useNavigate } from "react-router-dom"
import {
  Ticket,
  MessageSquare,
  FileText,
  ListTodo,
  Bot,
  ArrowRight,
  ShieldCheck,
  FileBox,
  ChevronRight,
} from "lucide-react"

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Ticket size={18} className="text-[#007acc]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              チケット: {id}
            </h2>
          </div>
          <button
            onClick={() => navigate(`/tickets/${id}/spec-plan`)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#007acc] text-white"
          >
            <FileText size={14} />
            仕様・計画を見る
            <ChevronRight size={14} />
          </button>
        </div>

        {/* Status & Meta */}
        <div className="rounded px-4 py-3 border border-[#3e3e42] bg-[#252526] mb-4">
          <div className="grid grid-cols-4 gap-4 text-[12px]">
            <div>
              <div className="text-[#6a6a6a] text-[11px] mb-1">ステータス</div>
              <span className="px-2 py-0.5 rounded text-[11px] bg-[#007acc20] text-[#007acc]">
                オープン
              </span>
            </div>
            <div>
              <div className="text-[#6a6a6a] text-[11px] mb-1">優先度</div>
              <span className="text-[#cccccc]">--</span>
            </div>
            <div>
              <div className="text-[#6a6a6a] text-[11px] mb-1">作成日</div>
              <span className="text-[#cccccc]">--</span>
            </div>
            <div>
              <div className="text-[#6a6a6a] text-[11px] mb-1">更新日</div>
              <span className="text-[#cccccc]">--</span>
            </div>
          </div>
        </div>

        {/* Thread / Discussion */}
        <Section icon={MessageSquare} title="スレッド">
          <div className="text-[12px] text-[#6a6a6a] py-4 text-center">
            このチケットにはまだメッセージがありません。
          </div>
        </Section>

        {/* Spec / Plan / Tasks */}
        <Section icon={FileText} title="仕様・計画">
          <div className="text-[12px] text-[#6a6a6a] py-4 text-center">
            仕様と計画はまだ作成されていません。
          </div>
        </Section>

        {/* Task List */}
        <Section icon={ListTodo} title="タスク一覧">
          <div className="text-[12px] text-[#6a6a6a] py-4 text-center">
            タスクはまだ割り当てられていません。
          </div>
        </Section>

        {/* Assignments */}
        <Section icon={Bot} title="エージェント割り当て">
          <div className="text-[12px] text-[#6a6a6a] py-4 text-center">
            エージェントはまだ割り当てられていません。
          </div>
        </Section>

        {/* State Transitions */}
        <Section icon={ArrowRight} title="状態遷移履歴">
          <div className="text-[12px] text-[#6a6a6a] py-4 text-center">
            遷移履歴はありません。
          </div>
        </Section>

        {/* Approvals */}
        <Section icon={ShieldCheck} title="承認">
          <div className="text-[12px] text-[#6a6a6a] py-4 text-center">
            承認リクエストはありません。
          </div>
        </Section>

        {/* Artifacts */}
        <Section icon={FileBox} title="成果物">
          <div className="text-[12px] text-[#6a6a6a] py-4 text-center">
            成果物はまだありません。
          </div>
        </Section>
      </div>
    </div>
  )
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-4 rounded border border-[#3e3e42] bg-[#252526]">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
        <Icon size={14} className="text-[#007acc]" />
        <span className="text-[12px] font-medium text-[#cccccc]">{title}</span>
      </div>
      <div className="px-4">{children}</div>
    </div>
  )
}
