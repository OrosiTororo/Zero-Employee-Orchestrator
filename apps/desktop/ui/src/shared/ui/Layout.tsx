import { useState, useEffect, useCallback } from "react"
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
  Globe,
  Zap,
  ChevronDown,
  ChevronRight,
  Send,
  UserCircle,
  BookTemplate,
  UsersRound,
  Search,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react"
import { LogoMark } from "@/shared/ui/Logo"
import { UpdateBanner } from "@/shared/ui/UpdateBanner"
import { CommandPalette } from "@/shared/ui/CommandPalette"
import { WelcomeTour } from "@/shared/ui/WelcomeTour"
import { AutonomyDial } from "@/shared/ui/AutonomyDial"
import { useCommandPalette } from "@/shared/hooks/use-command-palette"
import { useT, useI18n } from "@/shared/i18n"
import { api } from "@/shared/api/client"

interface LayoutProps {
  children: React.ReactNode
}

/* Shell dimensions — HIG-style chrome: roomy title bar, labeled sidebar
   that collapses to an icon rail, quiet hairline status bar. */
const SIDEBAR_WIDTH = 228
const RAIL_WIDTH = 56
const TITLE_BAR_HEIGHT = 40
const STATUS_BAR_HEIGHT = 26

interface NavItem {
  icon: React.ElementType
  path: string
  label: string
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const t = useT()
  const { locale } = useI18n()
  const openPalette = useCommandPalette((s) => s.setOpen)

  const [dispatchCount, setDispatchCount] = useState(0)
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("zeo_sidebar_collapsed") === "1",
  )

  const fetchStatusBar = useCallback(async () => {
    try {
      const dispatches = await api
        .get<{ total: number }>("/dispatch")
        .catch(() => ({ total: 0 }))
      setDispatchCount(dispatches.total)
    } catch {
      /* status bar data is non-critical */
    }
  }, [])

  useEffect(() => {
    fetchStatusBar()
    const interval = setInterval(fetchStatusBar, 30_000)
    return () => clearInterval(interval)
  }, [fetchStatusBar])

  const [showManage, setShowManage] = useState(
    () => localStorage.getItem("zeo_nav_manage") === "1",
  )
  const [showExtend, setShowExtend] = useState(
    () => localStorage.getItem("zeo_nav_extend") === "1",
  )

  const toggleCollapsed = () => {
    setCollapsed((v) => {
      localStorage.setItem("zeo_sidebar_collapsed", v ? "0" : "1")
      return !v
    })
  }

  const toggleManage = () => {
    setShowManage((v) => {
      localStorage.setItem("zeo_nav_manage", v ? "0" : "1")
      return !v
    })
  }

  const toggleExtend = () => {
    setShowExtend((v) => {
      localStorage.setItem("zeo_nav_extend", v ? "0" : "1")
      return !v
    })
  }

  function isActive(path: string) {
    return path === "/" ? location.pathname === "/" : location.pathname.startsWith(path)
  }

  const navStrings = t.nav as Record<string, string>

  /* Core items — always visible (progressive disclosure: primary actions) */
  const coreItems: NavItem[] = [
    { icon: LayoutDashboard, path: "/", label: t.nav.dashboard },
    { icon: Ticket, path: "/tickets", label: t.nav.tickets },
    { icon: BrainCircuit, path: "/secretary", label: t.nav.secretary },
    { icon: Sparkles, path: "/brainstorm", label: t.nav.brainstorm },
    { icon: Send, path: "/dispatch", label: navStrings.dispatch ?? "Dispatch" },
    { icon: Activity, path: "/monitor", label: t.nav.monitor },
  ]

  /* Management items — collapsed by default */
  const manageItems: NavItem[] = [
    { icon: Network, path: "/org-chart", label: t.nav.orgChart },
    { icon: BookTemplate, path: "/templates", label: t.nav.templates },
    { icon: UsersRound, path: "/crews", label: t.nav.crews },
    { icon: ShieldCheck, path: "/approvals", label: t.nav.approvals },
    { icon: FileBox, path: "/artifacts", label: t.nav.artifacts },
    { icon: HeartPulse, path: "/heartbeats", label: t.nav.heartbeats },
    { icon: Coins, path: "/costs", label: t.nav.costs },
    { icon: ScrollText, path: "/audit", label: t.nav.audit },
  ]

  /* Extension items — collapsed by default */
  const extendItems: NavItem[] = [
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

  const bottomItems: NavItem[] = [
    { icon: UserCircle, path: "/operator-profile", label: navStrings.operatorProfile ?? "Operator Profile" },
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
    "/templates": t.nav.templates,
    "/crews": t.nav.crews,
    "/brainstorm": t.nav.brainstorm,
    "/monitor": t.nav.monitor,
    "/permissions": t.nav.permissions,
    "/settings": t.nav.settings,
    "/dispatch": navStrings.dispatch ?? "Dispatch",
    "/operator-profile": navStrings.operatorProfile ?? "Operator Profile",
  }

  const currentTitle =
    pageTitles[location.pathname] ??
    (location.pathname.startsWith("/tickets/") ? t.nav.ticketDetail : "")

  /* Sidebar row: pill selection (macOS sidebar), icon + label when
     expanded; centered icon with hover tooltip when collapsed. */
  function renderNavButton(item: NavItem) {
    const active = isActive(item.path)
    if (collapsed) {
      return (
        <button
          key={item.path}
          onClick={() => navigate(item.path)}
          className="flex items-center justify-center rounded-md transition-colors"
          style={{
            width: 40,
            height: 36,
            color: active ? "var(--accent)" : "var(--text-muted)",
            background: active ? "var(--accent-subtle)" : "transparent",
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
          title={item.label}
          aria-label={item.label}
          aria-current={active ? "page" : undefined}
        >
          <item.icon size={19} strokeWidth={active ? 2 : 1.6} />
        </button>
      )
    }
    return (
      <button
        key={item.path}
        onClick={() => navigate(item.path)}
        className="flex w-full items-center gap-2.5 rounded-md px-2.5 transition-colors text-left"
        style={{
          height: 32,
          color: active ? "var(--accent)" : "var(--text-secondary)",
          background: active ? "var(--accent-subtle)" : "transparent",
          fontWeight: active ? 600 : 450,
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
            e.currentTarget.style.color = "var(--text-secondary)"
          }
        }}
        aria-current={active ? "page" : undefined}
      >
        <item.icon size={17} strokeWidth={active ? 2 : 1.6} className="shrink-0" />
        <span className="truncate text-[13px]">{item.label}</span>
      </button>
    )
  }

  /* Section header — uppercase caption when expanded, hairline when railed. */
  function renderSectionHeader(label: string, open: boolean, onToggle: () => void) {
    if (collapsed) {
      return (
        <button
          onClick={onToggle}
          className="mx-auto my-1 flex items-center justify-center rounded"
          style={{ width: 40, height: 18, color: "var(--text-muted)" }}
          aria-label={label}
          aria-expanded={open}
        >
          {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </button>
      )
    }
    return (
      <button
        onClick={onToggle}
        className="mt-3 mb-1 flex w-full items-center gap-1 rounded px-2.5 py-0.5 text-left transition-colors hover:text-[var(--text-secondary)]"
        style={{ color: "var(--text-muted)" }}
        aria-expanded={open}
      >
        {open ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
        <span className="text-[10.5px] font-semibold uppercase tracking-[0.08em]">{label}</span>
      </button>
    )
  }

  const sidebarWidth = collapsed ? RAIL_WIDTH : SIDEBAR_WIDTH

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg-base)]">
      {/* Skip-link: WCAG 2.4.1 bypass-blocks. Tab reveals it, Enter jumps to <main>. */}
      <a href="#main-content" className="skip-link">
        {t.a11y?.skip_to_main ?? "Skip to main content"}
      </a>

      {/* Title Bar */}
      <header
        className="flex items-center shrink-0 select-none border-b border-[var(--border)] px-2 gap-1"
        style={{ height: TITLE_BAR_HEIGHT, background: "var(--bg-titlebar)" }}
      >
        <div
          className="flex items-center gap-1 shrink-0"
          style={{ width: collapsed ? "auto" : sidebarWidth - 8 }}
        >
          <div className="flex items-center px-2">
            <LogoMark size={16} />
          </div>
          <button
            onClick={toggleCollapsed}
            className="flex items-center justify-center rounded-md text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
            style={{ width: 28, height: 28 }}
            aria-label={
              collapsed
                ? navStrings.expandSidebar ?? "Expand sidebar"
                : navStrings.collapseSidebar ?? "Collapse sidebar"
            }
            aria-expanded={!collapsed}
          >
            {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>
        <div className="flex-1 text-center">
          <span className="text-[13px] font-semibold text-[var(--text-primary)]">
            {currentTitle}
          </span>
        </div>
        {/* Search affordance — summons the Command Palette (Ctrl/Cmd+K) */}
        <button
          onClick={() => openPalette(true)}
          className="flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--bg-hover)] px-2.5 text-[var(--text-muted)] transition-colors hover:border-[var(--border-strong)] hover:text-[var(--text-secondary)]"
          style={{ height: 28 }}
          aria-label={t.common.search}
        >
          <Search size={13} />
          <span className="hidden text-[12px] sm:inline">{t.common.search}</span>
          <kbd className="rounded-[4px] border border-[var(--border)] px-1 py-px text-[10px]">
            ⌘K
          </kbd>
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar — labeled nav that collapses to an icon rail */}
        <nav
          className="shrink-0 flex flex-col overflow-y-auto overflow-x-hidden border-r border-[var(--border)]"
          style={{
            width: sidebarWidth,
            background: "var(--bg-nav-bar)",
            transition: "width var(--motion-med) var(--motion-ease)",
            padding: collapsed ? "8px 8px" : "10px 10px",
          }}
          aria-label={t.nav.navigation}
        >
          <div className={collapsed ? "flex flex-col items-center gap-0.5" : "flex flex-col gap-0.5"}>
            {/* Core — always visible */}
            {coreItems.map((item) => renderNavButton(item))}

            {/* Manage section — collapsible */}
            {renderSectionHeader(
              navStrings.sectionManage ?? "Manage",
              isManageOpen,
              toggleManage,
            )}
            {isManageOpen && manageItems.map((item) => renderNavButton(item))}

            {/* Extend section — collapsible */}
            {renderSectionHeader(
              navStrings.sectionExtend ?? "Extend",
              isExtendOpen,
              toggleExtend,
            )}
            {isExtendOpen && extendItems.map((item) => renderNavButton(item))}
          </div>
          <div className="flex-1" />
          <div
            className={`${collapsed ? "flex flex-col items-center" : "flex flex-col"} gap-0.5 border-t border-[var(--border)] pt-2 mt-2`}
          >
            {bottomItems.map((item) => renderNavButton(item))}
          </div>
        </nav>

        {/* Main Content */}
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-auto bg-[var(--bg-base)] outline-none"
        >
          {children}
        </main>
      </div>

      {/* Status Bar — quiet hairline chrome (autonomy dial + dispatch feed) */}
      <footer
        className="flex items-center shrink-0 border-t border-[var(--border)] text-[11.5px]"
        style={{
          height: STATUS_BAR_HEIGHT,
          background: "var(--bg-statusbar)",
          color: "var(--statusbar-fg)",
        }}
      >
        <div className="flex items-center h-full">
          <div className="flex h-full items-center gap-1.5 px-3 transition-colors hover:bg-[var(--bg-hover)]">
            <span
              aria-hidden="true"
              className="inline-block rounded-full"
              style={{ width: 7, height: 7, background: "var(--success)" }}
            />
            <span>{t.common.connected ?? "OK"}</span>
          </div>
          {/* Dispatch count — background activity feed */}
          <button
            onClick={() => navigate("/monitor")}
            className="flex h-full items-center gap-1.5 px-3 transition-colors hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
            style={{ color: "inherit" }}
          >
            <Send size={11} />
            <span>
              {dispatchCount} {t.common.jobs ?? "Tasks"}
            </span>
          </button>
        </div>
        <div className="flex-1" />
        <div className="flex items-center h-full">
          {/* Autonomy Dial — per-company default + per-session override */}
          <AutonomyDial />
          <button
            onClick={() => navigate("/settings")}
            className="flex h-full items-center gap-1.5 px-3 transition-colors hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
            style={{ color: "inherit" }}
          >
            <Globe size={11} />
            <span>{locale.toUpperCase()}</span>
          </button>
          <div className="flex h-full items-center gap-1.5 px-3">
            <Zap size={11} />
            <span>Quality</span>
          </div>
        </div>
      </footer>

      <CommandPalette />
      <UpdateBanner />
      <WelcomeTour />
    </div>
  )
}
