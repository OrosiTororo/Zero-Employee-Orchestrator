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
  Settings as SettingsIcon,
  LogOut,
  Activity,
  Shield,
  Sparkles,
} from "lucide-react"
import { useAuthStore } from "@/shared/hooks/use-auth"
import { LogoMark } from "@/shared/ui/Logo"
import { UpdateBanner } from "@/shared/ui/UpdateBanner"
import { useT } from "@/shared/i18n"

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((s) => s.logout)
  const t = useT()

  const navItems = [
    { icon: LayoutDashboard, path: "/", label: t.nav.dashboard },
    { icon: Network, path: "/org-chart", label: t.nav.orgChart },
    { icon: BrainCircuit, path: "/secretary", label: t.nav.secretary },
    { icon: Ticket, path: "/tickets", label: t.nav.tickets },
    { icon: ShieldCheck, path: "/approvals", label: t.nav.approvals },
    { icon: FileBox, path: "/artifacts", label: t.nav.artifacts },
    { icon: HeartPulse, path: "/heartbeats", label: t.nav.heartbeats },
    { icon: Coins, path: "/costs", label: t.nav.costs },
    { icon: ScrollText, path: "/audit", label: t.nav.audit },
    { icon: Blocks, path: "/skills", label: t.nav.skills },
    { icon: Puzzle, path: "/plugins", label: t.nav.plugins },
    { icon: Blocks, path: "/extensions", label: t.nav.extensions },
    { icon: Sparkles, path: "/brainstorm", label: t.nav.brainstorm },
    { icon: Activity, path: "/monitor", label: t.nav.monitor },
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
    "/brainstorm": t.nav.brainstorm,
    "/monitor": t.nav.monitor,
    "/permissions": t.nav.permissions,
    "/settings": t.nav.settings,
  }

  const currentTitle =
    pageTitles[location.pathname] ??
    (location.pathname.startsWith("/tickets/") ? t.nav.ticketDetail : "")

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg-base)]">
      {/* Title Bar */}
      <header
        className="flex items-center h-[30px] shrink-0 select-none border-b border-[var(--border)] bg-[var(--bg-titlebar)]"
      >
        <div className="flex items-center gap-2 px-3">
          <LogoMark size={14} />
          <span className="text-[12px] text-[var(--text-muted)]">
            {currentTitle} — {t.common.appName}
          </span>
        </div>
        <div className="flex-1" />
        <div className="px-3 text-[11px] text-[var(--text-muted)]">{t.common.version}</div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar */}
        <nav
          className="w-[48px] shrink-0 flex flex-col items-center pt-1 bg-[var(--bg-activity-bar)] border-r border-[var(--border)]"
          aria-label={t.nav.navigation}
        >
          {navItems.map((item) => {
            const isActive =
              item.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.path)
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className="group relative w-[48px] h-[40px] flex items-center justify-center transition-colors"
                style={{
                  color: isActive ? "var(--text-primary)" : "var(--text-muted)",
                  borderLeft: isActive
                    ? "2px solid var(--accent)"
                    : "2px solid transparent",
                }}
                aria-label={item.label}
                aria-current={isActive ? "page" : undefined}
              >
                <item.icon
                  size={20}
                  className="group-hover:text-[var(--text-primary)] transition-colors"
                />
                <span
                  role="tooltip"
                  className="pointer-events-none absolute left-[52px] px-2 py-1 rounded text-[11px] text-[var(--text-primary)] bg-[var(--bg-tooltip)] border border-[var(--border)] whitespace-nowrap opacity-0 group-hover:opacity-100 group-focus-visible:opacity-100 transition-opacity z-50 shadow-lg"
                >
                  {item.label}
                </span>
              </button>
            )
          })}
          <div className="flex-1" />
          <button
            onClick={() => {
              logout()
              navigate("/login")
            }}
            className="w-[48px] h-[40px] flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            aria-label={t.auth.logout}
          >
            <LogOut size={20} />
          </button>
        </nav>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab Bar */}
          <div className="h-[35px] flex items-end shrink-0 bg-[var(--bg-surface)]" role="tablist">
            <div
              className="h-[35px] flex items-center px-4 text-[13px] cursor-default bg-[var(--bg-base)] text-[var(--text-primary)] border-t-2 border-t-[var(--accent)] border-r border-r-[var(--border)]"
              style={{ minWidth: "120px" }}
              role="tab"
              aria-selected="true"
            >
              <span className="truncate">{currentTitle}</span>
            </div>
          </div>

          {/* Editor Content */}
          <main className="flex-1 overflow-auto bg-[var(--bg-base)]">
            {children}
          </main>
        </div>
      </div>

      {/* Status Bar */}
      <footer className="h-[22px] flex items-center px-3 shrink-0 text-[11px] text-[var(--text-secondary)] bg-[var(--bg-activity-bar)] border-t border-[var(--border)]">
        <span className="font-medium">{t.common.appName}</span>
        <div className="flex-1" />
        <span className="text-[var(--text-muted)]">{t.common.typescriptReact}</span>
      </footer>

      <UpdateBanner />
    </div>
  )
}
