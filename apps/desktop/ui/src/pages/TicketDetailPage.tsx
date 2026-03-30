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
import { useT } from "@/shared/i18n"

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const t = useT()

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Ticket size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.ticketDetail?.ticketLabel ?? "Ticket"}: {id}
            </h2>
          </div>
          <button
            onClick={() => navigate(`/tickets/${id}/spec-plan`)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white"
          >
            <FileText size={14} />
            {t.ticketDetail?.viewSpecPlan ?? "View Spec & Plan"}
            <ChevronRight size={14} />
          </button>
        </div>

        {/* Status & Meta */}
        <div className="rounded px-4 py-3 border border-[var(--border)] bg-[var(--bg-surface)] mb-4">
          <div className="grid grid-cols-4 gap-4 text-[12px]">
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.status ?? "Status"}</div>
              <span className="px-2 py-0.5 rounded text-[11px] bg-[var(--accent)]/20 text-[var(--accent)]">
                {t.ticketDetail?.open ?? "Open"}
              </span>
            </div>
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.priority ?? "Priority"}</div>
              <span className="text-[var(--text-primary)]">--</span>
            </div>
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.createdAt ?? "Created"}</div>
              <span className="text-[var(--text-primary)]">--</span>
            </div>
            <div>
              <div className="text-[var(--text-muted)] text-[11px] mb-1">{t.ticketDetail?.updatedAt ?? "Updated"}</div>
              <span className="text-[var(--text-primary)]">--</span>
            </div>
          </div>
        </div>

        {/* Thread / Discussion */}
        <Section icon={MessageSquare} title={t.ticketDetail?.thread ?? "Thread"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noMessages ?? "No messages in this ticket yet."}
          </div>
        </Section>

        {/* Spec / Plan / Tasks */}
        <Section icon={FileText} title={t.ticketDetail?.specPlan ?? "Spec & Plan"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noSpecPlan ?? "No spec or plan has been created yet."}
          </div>
        </Section>

        {/* Task List */}
        <Section icon={ListTodo} title={t.ticketDetail?.taskList ?? "Tasks"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noTasks ?? "No tasks have been assigned yet."}
          </div>
        </Section>

        {/* Assignments */}
        <Section icon={Bot} title={t.ticketDetail?.agentAssignment ?? "Agent Assignment"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noAgents ?? "No agents have been assigned yet."}
          </div>
        </Section>

        {/* State Transitions */}
        <Section icon={ArrowRight} title={t.ticketDetail?.stateHistory ?? "State Transition History"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noTransitions ?? "No transition history."}
          </div>
        </Section>

        {/* Approvals */}
        <Section icon={ShieldCheck} title={t.ticketDetail?.approvals ?? "Approvals"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noApprovals ?? "No approval requests."}
          </div>
        </Section>

        {/* Artifacts */}
        <Section icon={FileBox} title={t.ticketDetail?.artifacts ?? "Artifacts"}>
          <div className="text-[12px] text-[var(--text-muted)] py-4 text-center">
            {t.ticketDetail?.noArtifacts ?? "No artifacts yet."}
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
    <div className="mb-4 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
        <Icon size={14} className="text-[var(--accent)]" />
        <span className="text-[12px] font-medium text-[var(--text-primary)]">{title}</span>
      </div>
      <div className="px-4">{children}</div>
    </div>
  )
}
