import { useState } from "react"
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
  ChevronDown,
  ChevronRight,
} from "lucide-react"
import { LogoMark } from "@/shared/ui/Logo"
import { UpdateBanner } from "@/shared/ui/UpdateBanner"
import { CommandPalette } from "@/shared/ui/CommandPalette"
import { useT, useI18n } from "@/shared/i18n"

interface LayoutProps {
  children: React.ReactNode
}

/* VSCode dimensions (from source) */
const ACTIVITY_BAR_WIDTH = 48
const TITLE_BAR_HEIGHT = 30
const STATUS_BAR_HEIGHT = 22

function ActivityBarDivider() {
  return (
    <div
      className="mx-auto my-[6px]"
      style={{ width: 28, height: 1, background: "rgba(255,255,255,0.12)" }}
    />
  )
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const t = useT()
  const { locale } = useI18n()

  const [showManage, setShowManage] = useState(false)
  const [showExtend, setShowExtend] = useState(false)

  function isActive(path: string) {
    return path === "/" ? location.pathname === "/" : location.pathname.startsWith(path)
  }

  /* Core items — always visible (progressive disclosure: primary actions) */
  const coreItems = [
    { icon: LayoutDashboard, path: "/", label: t.nav.dashboard },
    { icon: Ticket, path: "/tickets", label: t.nav.tickets },
    { icon: BrainCircuit, path: "/secretary", label: t.nav.secretary },
    { icon: Sparkles, path: "/brainstorm", label: t.nav.brainstorm },
    { icon: Activity, path: "/monitor", label: t.nav.monitor },
  ]

  /* Management items — collapsed by default */
  const manageItems = [
    { icon: Network, path: "/org-chart", label: t.nav.orgChart },
    { icon: ShieldCheck, path: "/approvals", label: t.nav.approvals },
    { icon: FileBox, path: "/artifacts", label: t.nav.artifacts },
    { icon: HeartPulse, path: "/heartbeats", label: t.nav.heartbeats },
    { icon: Coins, path: "/costs", label: t.nav.costs },
    { icon: ScrollText, path: "/audit", label: t.nav.audit },
  ]

  /* Extension items — collapsed by default */
  const extendItems = [
    { icon: Blocks, path: "/skills", label: t.nav.skills },
    { icon: Puzzle, path: "/plugins", label: t.nav.plugins },
    { icon: Blocks, path: "/extensions", label: t.nav.extensions },
    { icon: Store, path: "/marketplace", label: t.nav.marketplace },
  ]

  /* Auto-expand sections when an item in them is active */
  const manageActive = manageItems.some((item) => isActive(item.path))
  const extendActive = extendItems.some((item) => isActive(item.path))
  const isManageOpen = showManage || manageActive
  const isExtendOpen = showExtend || extendActive

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

  /* VSCode Activity Bar button: 48x48px icon area, 24px icon, 2px left border */
  function renderNavButton(item: { icon: React.ElementType; path: string; label: string }) {
    const active = isActive(item.path)
    return (
      <button
        key={item.path}
        onClick={() => navigate(item.path)}
        className="group relative flex items-center justify-center"
        style={{
          width: ACTIVITY_BAR_WIDTH,
          height: ACTIVITY_BAR_WIDTH,
          color: active ? "var(--text-primary)" : "var(--text-muted)",
          borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
          background: active ? "rgba(255,255,255,0.07)" : "transparent",
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
        <item.icon size={24} strokeWidth={active ? 2 : 1.5} />
        {/* Tooltip */}
        <span
          role="tooltip"
          className="pointer-events-none absolute left-[52px] px-2 py-1 rounded text-[11px] text-[var(--text-primary)] bg-[var(--bg-overlay)] border border-[var(--border)] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-50"
          style={{ boxShadow: "var(--shadow-popup)" }}
        >
          {item.label}
        </span>
      </button>
    )
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg-base)]">
      {/* Title Bar — 30px, VSCode style */}
      <header
        className="flex items-center shrink-0 select-none border-b border-[var(--border)]"
        style={{ height: TITLE_BAR_HEIGHT, background: "var(--bg-titlebar)" }}
      >
        <div className="flex items-center gap-2 px-3" style={{ width: ACTIVITY_BAR_WIDTH }}>
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
        {/* Activity Bar — 48px, VSCode style */}
        <nav
          className="shrink-0 flex flex-col items-center border-r border-[var(--border)]"
          style={{ width: ACTIVITY_BAR_WIDTH, background: "var(--bg-activity-bar)" }}
          aria-label={t.nav.navigation}
        >
          <div className="flex flex-col items-center pt-[4px]">
            {/* Core — always visible */}
            {coreItems.map((item) => renderNavButton(item))}

            {/* Manage section — collapsible */}
            <ActivityBarDivider />
            <button
              onClick={() => setShowManage((v) => !v)}
              className="flex items-center justify-center"
              style={{
                width: ACTIVITY_BAR_WIDTH,
                height: 20,
                color: "var(--text-muted)",
                opacity: 0.6,
              }}
              aria-label="Manage"
            >
              {isManageOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            </button>
            {isManageOpen && manageItems.map((item) => renderNavButton(item))}

            {/* Extend section — collapsible */}
            <ActivityBarDivider />
            <button
              onClick={() => setShowExtend((v) => !v)}
              className="flex items-center justify-center"
              style={{
                width: ACTIVITY_BAR_WIDTH,
                height: 20,
                color: "var(--text-muted)",
                opacity: 0.6,
              }}
              aria-label="Extend"
            >
              {isExtendOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            </button>
            {isExtendOpen && extendItems.map((item) => renderNavButton(item))}
          </div>
          <div className="flex-1" />
          <div className="flex flex-col items-center pb-[4px]">
            <ActivityBarDivider />
            {bottomItems.map((item) => renderNavButton(item))}
          </div>
        </nav>

        {/* Main Content — no tab bar (ZEO is not a text editor) */}
        <main className="flex-1 overflow-auto bg-[var(--bg-base)]">
          {children}
        </main>
      </div>

      {/* Status Bar — 22px, VSCode blue bar */}
      <footer
        className="flex items-center shrink-0 text-[12px]"
        style={{ height: STATUS_BAR_HEIGHT, lineHeight: `${STATUS_BAR_HEIGHT}px`, background: "var(--bg-statusbar)" }}
      >
        <div className="flex items-center h-full text-[var(--statusbar-fg)]">
          <div className="flex items-center gap-1 px-2 h-full hover:bg-[rgba(255,255,255,0.12)]">
            <Circle size={7} fill="var(--statusbar-fg)" stroke="none" style={{ opacity: 0.8 }} />
            <span>{t.common.connected ?? "OK"}</span>
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
