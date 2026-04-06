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
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  BookOpen,
} from "lucide-react"
import { LogoMark } from "@/shared/ui/Logo"
import { UpdateBanner } from "@/shared/ui/UpdateBanner"
import { CommandPalette } from "@/shared/ui/CommandPalette"
import { useT, useI18n } from "@/shared/i18n"

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const t = useT()
  const { locale } = useI18n()
  const [sidebarExpanded, setSidebarExpanded] = useState(false)

  const navGroups = [
    {
      label: t.nav.dashboard,
      items: [
        { icon: LayoutDashboard, path: "/", label: t.nav.dashboard },
        { icon: Network, path: "/org-chart", label: t.nav.orgChart },
      ],
    },
    {
      label: t.nav.tickets,
      items: [
        { icon: Ticket, path: "/tickets", label: t.nav.tickets },
        { icon: ShieldCheck, path: "/approvals", label: t.nav.approvals },
      ],
    },
    {
      label: "AI",
      items: [
        { icon: BrainCircuit, path: "/secretary", label: t.nav.secretary },
        { icon: Sparkles, path: "/brainstorm", label: t.nav.brainstorm },
        { icon: Activity, path: "/monitor", label: t.nav.monitor },
      ],
    },
    {
      label: t.nav.audit,
      items: [
        { icon: FileBox, path: "/artifacts", label: t.nav.artifacts },
        { icon: HeartPulse, path: "/heartbeats", label: t.nav.heartbeats },
        { icon: Coins, path: "/costs", label: t.nav.costs },
        { icon: ScrollText, path: "/audit", label: t.nav.audit },
      ],
    },
    {
      label: t.nav.skills,
      items: [
        { icon: Blocks, path: "/skills", label: t.nav.skills },
        { icon: Puzzle, path: "/plugins", label: t.nav.plugins },
        { icon: Blocks, path: "/extensions", label: t.nav.extensions },
        { icon: Store, path: "/marketplace", label: t.nav.marketplace },
      ],
    },
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
        className="group relative flex items-center gap-3 w-full transition-all duration-150"
        style={{
          height: 36,
          padding: sidebarExpanded ? "0 12px" : "0",
          justifyContent: sidebarExpanded ? "flex-start" : "center",
          color: active ? "var(--text-primary)" : "var(--text-muted)",
          background: active ? "var(--accent-subtle)" : "transparent",
          borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
          borderRadius: active ? "0 var(--radius-sm) var(--radius-sm) 0" : "0",
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
        <item.icon size={18} strokeWidth={active ? 2 : 1.5} className="shrink-0" />
        {sidebarExpanded && (
          <span className="text-[12px] font-medium truncate">{item.label}</span>
        )}
        {!sidebarExpanded && (
          <span
            role="tooltip"
            className="pointer-events-none absolute left-full ml-2 px-2.5 py-1.5 rounded-md text-[11px] font-medium text-[var(--text-primary)] bg-[var(--bg-tooltip)] border border-[var(--border)] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-50"
            style={{ boxShadow: "var(--shadow-md)" }}
          >
            {item.label}
          </span>
        )}
      </button>
    )
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg-base)]">
      {/* Title Bar */}
      <header
        className="flex items-center h-[38px] shrink-0 select-none border-b border-[var(--border)]"
        style={{ background: "var(--bg-titlebar)" }}
      >
        <div className="flex items-center gap-2.5 px-3" style={{ width: sidebarExpanded ? 200 : 48 }}>
          <LogoMark size={16} />
          {sidebarExpanded && (
            <span className="text-[12px] font-semibold text-[var(--text-primary)] truncate">
              ZEO
            </span>
          )}
        </div>

        {/* Breadcrumb / Page Title */}
        <div className="flex items-center gap-2 px-3 flex-1 min-w-0">
          <span className="text-[12px] font-medium text-[var(--text-primary)] truncate">
            {currentTitle}
          </span>
        </div>

        {/* Title bar actions */}
        <div className="flex items-center gap-1 px-3">
          <button
            onClick={() => {
              const event = new KeyboardEvent("keydown", { key: "k", metaKey: true })
              window.dispatchEvent(event)
            }}
            className="flex items-center gap-2 px-3 py-1 rounded-md text-[11px] text-[var(--text-muted)] border border-[var(--border)] bg-[var(--bg-input)] hover:border-[var(--border-elevated)] transition-colors"
          >
            <span>{t.commandPalette?.placeholder ?? "Search..."}</span>
            <kbd className="text-[10px] text-[var(--text-muted)] ml-2">Ctrl+K</kbd>
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar / Sidebar */}
        <nav
          className="shrink-0 flex flex-col border-r border-[var(--border)] transition-all duration-200 overflow-hidden"
          style={{
            width: sidebarExpanded ? 200 : 48,
            background: "var(--bg-activity-bar)",
          }}
          aria-label={t.nav.navigation}
        >
          {/* Sidebar toggle */}
          <div className="flex items-center justify-center h-[8px]" />

          {/* Nav groups */}
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden py-1">
            {navGroups.map((group, gi) => (
              <div key={gi}>
                {gi > 0 && (
                  <div
                    className="mx-3 my-2"
                    style={{ height: 1, background: "var(--activity-bar-divider)" }}
                  />
                )}
                {sidebarExpanded && (
                  <div className="px-3 py-1">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                      {group.label}
                    </span>
                  </div>
                )}
                {group.items.map((item) => renderNavButton(item))}
              </div>
            ))}
          </div>

          {/* Bottom items */}
          <div className="flex flex-col py-1 border-t border-[var(--activity-bar-divider)]">
            {bottomItems.map((item) => renderNavButton(item))}
            <button
              onClick={() => setSidebarExpanded(!sidebarExpanded)}
              className="flex items-center justify-center h-[32px] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              aria-label={sidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
            >
              {sidebarExpanded ? <PanelLeftClose size={16} /> : <PanelLeft size={16} />}
            </button>
          </div>
        </nav>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-auto bg-[var(--bg-base)]">
            {children}
          </main>
        </div>
      </div>

      {/* Status Bar */}
      <footer
        className="h-[24px] flex items-center shrink-0 text-[11px] border-t"
        style={{
          background: "var(--bg-statusbar)",
          borderColor: "transparent",
        }}
      >
        <div className="flex items-center h-full text-[var(--statusbar-fg)]">
          <div className="flex items-center gap-1.5 px-2.5 h-full hover:bg-[rgba(255,255,255,0.1)] transition-colors">
            <Circle size={7} fill="var(--success)" stroke="none" />
            <span>{t.common.connected ?? "OK"}</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 h-full hover:bg-[rgba(255,255,255,0.1)] transition-colors">
            <Briefcase size={11} />
            <span>0 {t.common.jobs ?? "Jobs"}</span>
          </div>
        </div>
        <div className="flex-1" />
        <div className="flex items-center h-full text-[var(--statusbar-fg)]">
          <button
            onClick={() => navigate("/settings")}
            className="flex items-center gap-1.5 px-2.5 h-full hover:bg-[rgba(255,255,255,0.1)] transition-colors"
          >
            <Globe size={11} />
            <span>{locale.toUpperCase()}</span>
          </button>
          <div className="flex items-center gap-1.5 px-2.5 h-full hover:bg-[rgba(255,255,255,0.1)] transition-colors">
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
