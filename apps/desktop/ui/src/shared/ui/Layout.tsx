import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import {
  LayoutDashboard,
  Network,
  Ticket,
  ShieldCheck,
  FileBox,
  HeartPulse,
  Coins,
  ScrollText,
  Blocks,
  Puzzle,
  Settings,
  Download,
  ChevronRight,
  LogOut,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react"
import { useAuthStore } from "@/shared/hooks/use-auth"
import { LogoMark } from "@/shared/ui/Logo"

interface LayoutProps {
  children: React.ReactNode
}

const navItems = [
  { icon: LayoutDashboard, path: "/", label: "ダッシュボード" },
  { icon: Network, path: "/org-chart", label: "組織図" },
  { icon: Ticket, path: "/tickets", label: "チケット" },
  { icon: ShieldCheck, path: "/approvals", label: "承認" },
  { icon: FileBox, path: "/artifacts", label: "成果物" },
  { icon: HeartPulse, path: "/heartbeats", label: "ハートビート" },
  { icon: Coins, path: "/costs", label: "コスト" },
  { icon: ScrollText, path: "/audit", label: "監査ログ" },
  { icon: Blocks, path: "/skills", label: "スキル" },
  { icon: Puzzle, path: "/plugins", label: "プラグイン" },
  { icon: Download, path: "/releases", label: "ダウンロード" },
  { icon: Settings, path: "/settings", label: "設定" },
]

const pageTitles: Record<string, string> = {
  "/": "ダッシュボード",
  "/org-chart": "組織図",
  "/tickets": "チケット",
  "/approvals": "承認",
  "/artifacts": "成果物",
  "/heartbeats": "ハートビート",
  "/costs": "コスト管理",
  "/audit": "監査ログ",
  "/skills": "スキル",
  "/skills/create": "スキル作成",
  "/plugins": "プラグイン",
  "/download": "ダウンロード",
  "/releases": "ダウンロード",
  "/settings": "設定",
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((s) => s.logout)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const currentTitle =
    pageTitles[location.pathname] ??
    (location.pathname.startsWith("/tickets/") ? "チケット詳細" : "")

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg-base)]">
      {/* Title Bar */}
      <div
        className="flex items-center h-[30px] shrink-0 select-none border-b border-[var(--border)]"
        style={{ background: "var(--bg-titlebar)" }}
      >
        <div className="flex items-center gap-2 px-3">
          <LogoMark size={14} />
          <span className="text-[12px] text-[var(--text-secondary)]">
            Zero-Employee Orchestrator
          </span>
          <ChevronRight size={11} className="text-[var(--text-muted)]" />
          <span className="text-[12px] text-[var(--text-primary)]">
            {currentTitle}
          </span>
        </div>
        <div className="flex-1" />
        <div className="px-3 text-[11px] text-[var(--text-muted)]">v0.1.0</div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar (icon strip) */}
        <div className="w-[48px] shrink-0 flex flex-col items-center pt-1 bg-[var(--bg-activity-bar)] border-r border-[var(--border)]">
          {navItems.map((item) => {
            const isActive =
              item.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.path)
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className="group relative w-[48px] h-[48px] flex items-center justify-center"
                style={{
                  color: isActive ? "#ffffff" : "var(--text-muted)",
                  borderLeft: isActive
                    ? "2px solid var(--accent)"
                    : "2px solid transparent",
                }}
                title={item.label}
              >
                <item.icon
                  size={20}
                  className="group-hover:text-[var(--text-primary)] transition-colors"
                />
                {/* Tooltip */}
                <span className="pointer-events-none absolute left-[52px] px-2 py-1 rounded text-[11px] text-white bg-[#383838] border border-[var(--border)] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-50 shadow-lg">
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
            className="w-[48px] h-[48px] flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            title="ログアウト"
          >
            <LogOut size={20} />
          </button>
        </div>

        {/* Sidebar */}
        <div
          className="shrink-0 flex flex-col overflow-hidden bg-[var(--bg-surface)] border-r border-[var(--border)] transition-all duration-200"
          style={{ width: sidebarCollapsed ? "0px" : "200px" }}
        >
          <div className="h-[35px] flex items-center justify-between px-4 shrink-0">
            <span className="uppercase text-[11px] tracking-wider text-[var(--text-secondary)] font-medium">
              ナビゲーション
            </span>
            <button
              onClick={() => setSidebarCollapsed(true)}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            >
              <PanelLeftClose size={14} />
            </button>
          </div>
          <nav className="flex-1 overflow-auto px-1">
            {navItems.map((item) => {
              const isActive =
                item.path === "/"
                  ? location.pathname === "/"
                  : location.pathname.startsWith(item.path)
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className="w-full flex items-center gap-2.5 px-3 py-[6px] rounded text-[13px] text-left transition-colors"
                  style={{
                    color: isActive
                      ? "var(--text-primary)"
                      : "var(--text-secondary)",
                    background: isActive ? "var(--bg-active)" : "transparent",
                    fontWeight: isActive ? 500 : 400,
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive)
                      e.currentTarget.style.background = "var(--bg-hover)"
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive)
                      e.currentTarget.style.background = "transparent"
                  }}
                >
                  <item.icon size={15} />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab Bar */}
          <div className="h-[35px] flex items-end shrink-0 bg-[var(--bg-surface)]">
            {sidebarCollapsed && (
              <button
                onClick={() => setSidebarCollapsed(false)}
                className="h-[35px] flex items-center px-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                <PanelLeft size={14} />
              </button>
            )}
            <div
              className="h-[35px] flex items-center px-4 text-[13px] cursor-default bg-[var(--bg-base)] text-[var(--text-primary)] border-t-2 border-t-[var(--accent)] border-r border-r-[var(--border)]"
              style={{ minWidth: "120px" }}
            >
              <span className="truncate">{currentTitle}</span>
            </div>
          </div>

          {/* Editor Content */}
          <div className="flex-1 overflow-auto bg-[var(--bg-base)]">
            {children}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div
        className="h-[22px] flex items-center px-3 shrink-0 text-[11px] text-white/90"
        style={{
          background: "linear-gradient(90deg, #0078d4, #6d28d9)",
        }}
      >
        <div className="flex items-center gap-4">
          <span className="font-medium">Zero-Employee Orchestrator</span>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-4 text-white/70">
          <span>TypeScript React</span>
        </div>
      </div>
    </div>
  )
}
