import { useNavigate, useLocation } from "react-router-dom"
import {
  LayoutDashboard,
  Network,
  BrainCircuit,
  Ticket,
  ShieldCheck,
  FileBox,
  HeartPulse,
  Coins,
  ScrollText,
  Blocks,
  Puzzle,
  Store,
  Settings as SettingsIcon,
  Activity,
  Shield,
  Sparkles,
  Circle,
  Globe,
  Zap,
  Briefcase,
} from "lucide-react"
import { LogoMark } from "@/shared/ui/Logo"
import { UpdateBanner } from "@/shared/ui/UpdateBanner"
import { CommandPalette } from "@/shared/ui/CommandPalette"
import { useT, useI18n } from "@/shared/i18n"

interface LayoutProps {
  children: React.ReactNode
}

function ActivityBarDivider() {
  return (
    <div
      className="mx-auto my-[6px]"
      style={{ width: 28, height: 1, background: "var(--activity-bar-divider)" }}
    />
  )
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const t = useT()
  const { locale } = useI18n()

  const navGroups = [
    [
      { icon: LayoutDashboard, path: "/", label: t.nav.dashboard },
      { icon: Network, path: "/org-chart", label: t.nav.orgChart },
    ],
    [
      { icon: Ticket, path: "/tickets", label: t.nav.tickets },
      { icon: ShieldCheck, path: "/approvals", label: t.nav.approvals },
    ],
    [
      { icon: BrainCircuit, path: "/secretary", label: t.nav.secretary },
      { icon: Sparkles, path: "/brainstorm", label: t.nav.brainstorm },
      { icon: Activity, path: "/monitor", label: t.nav.monitor },
    ],
    [
      { icon: FileBox, path: "/artifacts", label: t.nav.artifacts },
      { icon: HeartPulse, path: "/heartbeats", label: t.nav.heartbeats },
      { icon: Coins, path: "/costs", label: t.nav.costs },
      { icon: ScrollText, path: "/audit", label: t.nav.audit },
    ],
    [
      { icon: Blocks, path: "/skills", label: t.nav.skills },
      { icon: Puzzle, path: "/plugins", label: t.nav.plugins },
      { icon: Blocks, path: "/extensions", label: t.nav.extensions },
      { icon: Store, path: "/marketplace", label: t.nav.marketplace },
    ],
  ]

  const bottomItems = [
    { icon: Shield, path: "/permissions", label: t.nav.permissions },
    { icon: SettingsIcon, path: "/settings", label: t.nav.settings },
  ]

  const pageTitles: Record<string, string> = {
    "/": t.nav.dashboard,
    "/org-chart": t.nav.orgChart,
    "/secretary": t.nav.secretary,
    "/tickets": t.nav.tickets,
    "/approvals": t.nav.approvals,
    "/artifacts": t.nav.artifacts,
    "/heartbeats": t.nav.heartbeats,
    "/costs": t.nav.costManagement,
    "/audit": t.nav.audit,
    "/skills": t.nav.skills,
    "/skills/create": t.nav.skillCreate,
    "/plugins": t.nav.plugins,
    "/extensions": t.nav.extensions,
    "/marketplace": t.nav.marketplace,
    "/brainstorm": t.nav.brainstorm,
    "/monitor": t.nav.monitor,
    "/permissions": t.nav.permissions,
    "/settings": t.nav.settings,
  }

  const currentTitle =
    pageTitles[location.pathname] ??
    (location.pathname.startsWith("/tickets/") ? t.nav.ticketDetail : "")

  function isActive(path: string) {
    return path === "/" ? location.pathname === "/" : location.pathname.startsWith(path)
  }

  function renderNavButton(item: { icon: React.ElementType; path: string; label: string }) {
    const active = isActive(item.path)
    return (
      <button
        key={item.path}
        onClick={() => navigate(item.path)}
        className="group relative w-[48px] h-[40px] flex items-center justify-center"
        style={{
          color: active ? "var(--text-primary)" : "var(--text-muted)",
          borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
          background: active ? "var(--bg-active-indicator)" : "transparent",
        }}
        onMouseEnter={(e) => {
          if (!active) {
            e.currentTarget.style.background = "var(--bg-hover)"
            e.currentTarget.style.color = "var(--text-primary)"
          }
        }}
        onMouseLeave={(e) => {
          if (!active) {
            e.currentTarget.style.background = "transparent"
            e.currentTarget.style.color = "var(--text-muted)"
          }
        }}
        aria-label={item.label}
        aria-current={active ? "page" : undefined}
      >
        <item.icon size={20} strokeWidth={active ? 2 : 1.5} />
        <span
          role="tooltip"
          className="pointer-events-none absolute left-[52px] px-2 py-1 rounded text-[11px] text-[var(--text-primary)] bg-[var(--bg-tooltip)] border border-[var(--border)] whitespace-nowrap opacity-0 group-hover:opacity-100 group-focus-visible:opacity-100 transition-opacity z-50 shadow-lg"
        >
          {item.label}
        </span>
      </button>
    )
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg-base)]">
      {/* Title Bar */}
      <header className="flex items-center h-[30px] shrink-0 select-none border-b border-[var(--border)] bg-[var(--bg-titlebar)]">
        <div className="flex items-center gap-2 px-3">
          <LogoMark size={14} />
        </div>
        <div className="flex-1 text-center">
          <span className="text-[11px] font-medium text-[var(--text-secondary)] tracking-wide">
            {currentTitle}
          </span>
        </div>
        <div className="w-[60px]" />
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar */}
        <nav
          className="w-[48px] shrink-0 flex flex-col items-center bg-[var(--bg-activity-bar)] border-r border-[var(--border)]"
          aria-label={t.nav.navigation}
        >
          <div className="flex flex-col items-center pt-[4px]">
            {navGroups.map((group, gi) => (
              <div key={gi}>
                {gi > 0 && <ActivityBarDivider />}
                {group.map((item) => renderNavButton(item))}
              </div>
            ))}
          </div>
          <div className="flex-1" />
          <div className="flex flex-col items-center pb-[4px]">
            <ActivityBarDivider />
            {bottomItems.map((item) => renderNavButton(item))}
          </div>
        </nav>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab Bar */}
          <div className="h-[35px] flex items-end shrink-0 bg-[var(--bg-tab-bar)]" role="tablist">
            <div
              className="h-[35px] flex items-center px-4 text-[12px] cursor-default"
              style={{
                minWidth: 120,
                background: "var(--bg-base)",
                color: "var(--text-primary)",
                borderTop: "2px solid var(--accent)",
                borderRight: "1px solid var(--border)",
              }}
              role="tab"
              aria-selected="true"
            >
              <span className="truncate">{currentTitle}</span>
            </div>
            <div className="flex-1 h-full" style={{ borderBottom: "1px solid var(--border)" }} />
          </div>

          <main className="flex-1 overflow-auto bg-[var(--bg-base)]">
            {children}
          </main>
        </div>
      </div>

      {/* Status Bar — VSCode-style blue bar */}
      <footer className="h-[22px] flex items-center shrink-0 text-[11px] bg-[var(--bg-statusbar)]">
        <div className="flex items-center h-full text-[var(--statusbar-fg)]">
          <div className="flex items-center gap-1 px-2 h-full hover:bg-[rgba(255,255,255,0.12)]">
            <Circle size={7} fill="var(--statusbar-fg)" stroke="none" style={{ opacity: 0.8 }} />
            <span>{t.common.connected ?? "Connected"}</span>
          </div>
          <div className="flex items-center gap-1 px-2 h-full hover:bg-[rgba(255,255,255,0.12)]">
            <Briefcase size={11} />
            <span>0 {t.common.jobs ?? "Jobs"}</span>
          </div>
        </div>
        <div className="flex-1" />
        <div className="flex items-center h-full text-[var(--statusbar-fg)]">
          <button
            onClick={() => navigate("/settings")}
            className="flex items-center gap-1 px-2 h-full hover:bg-[rgba(255,255,255,0.12)]"
          >
            <Globe size={11} />
            <span>{locale.toUpperCase()}</span>
          </button>
          <div className="flex items-center gap-1 px-2 h-full hover:bg-[rgba(255,255,255,0.12)]">
            <Zap size={11} />
            <span>Quality</span>
          </div>
        </div>
      </footer>

      <CommandPalette />
      <UpdateBanner />
    </div>
  )
}
