import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import {
  LayoutDashboard,
  Network,
  Ticket,
  ShieldCheck,
  FileBox,
  Heartbeat,
  Coins,
  ScrollText,
  Blocks,
  Puzzle,
  Settings,
  ChevronRight,
  Zap,
  LogOut,
} from "lucide-react"
import { useAuthStore } from "@/shared/hooks/use-auth"

interface LayoutProps {
  children: React.ReactNode
}

const navItems = [
  { icon: LayoutDashboard, path: "/", label: "ダッシュボード" },
  { icon: Network, path: "/org-chart", label: "組織図" },
  { icon: Ticket, path: "/tickets", label: "チケット" },
  { icon: ShieldCheck, path: "/approvals", label: "承認" },
  { icon: FileBox, path: "/artifacts", label: "成果物" },
  { icon: Heartbeat, path: "/heartbeats", label: "ハートビート" },
  { icon: Coins, path: "/costs", label: "コスト" },
  { icon: ScrollText, path: "/audit", label: "監査ログ" },
  { icon: Blocks, path: "/skills", label: "スキル" },
  { icon: Puzzle, path: "/plugins", label: "プラグイン" },
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
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#1e1e1e]">
      {/* Title Bar */}
      <div className="flex items-center h-[30px] shrink-0 select-none bg-[#323233] border-b border-[#3e3e42]">
        <div className="flex items-center gap-2 px-3 text-xs text-[#969696]">
          <Zap size={14} className="text-[#007acc]" />
          <span>Zero-Employee Orchestrator</span>
          <ChevronRight size={12} />
          <span className="text-[#cccccc]">{currentTitle}</span>
        </div>
        <div className="flex-1" />
        <div className="px-3 text-[11px] text-[#6a6a6a]">v0.1.0</div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar (icon strip) */}
        <div className="w-[48px] shrink-0 flex flex-col items-center pt-1 bg-[#333333] border-r border-[#3e3e42]">
          {navItems.map((item) => {
            const isActive =
              item.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.path)
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className="w-[48px] h-[48px] flex items-center justify-center relative"
                style={{
                  color: isActive ? "#ffffff" : "#858585",
                  borderLeft: isActive
                    ? "2px solid #007acc"
                    : "2px solid transparent",
                }}
                title={item.label}
              >
                <item.icon size={20} />
              </button>
            )
          })}
          <div className="flex-1" />
          <button
            onClick={() => {
              logout()
              navigate("/login")
            }}
            className="w-[48px] h-[48px] flex items-center justify-center text-[#858585] hover:text-[#ffffff]"
            title="ログアウト"
          >
            <LogOut size={20} />
          </button>
        </div>

        {/* Sidebar */}
        {!sidebarCollapsed && (
          <div className="w-[200px] shrink-0 flex flex-col overflow-hidden bg-[#252526] border-r border-[#3e3e42]">
            <div className="h-[35px] flex items-center justify-between px-4 shrink-0 uppercase text-[11px] tracking-wider text-[#bbbbbb]">
              <span>ナビゲーション</span>
              <button
                onClick={() => setSidebarCollapsed(true)}
                className="text-[#6a6a6a] hover:text-[#cccccc]"
              >
                <ChevronRight size={14} />
              </button>
            </div>
            <nav className="flex-1 overflow-auto">
              {navItems.map((item) => {
                const isActive =
                  item.path === "/"
                    ? location.pathname === "/"
                    : location.pathname.startsWith(item.path)
                return (
                  <button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    className="w-full flex items-center gap-2 px-4 py-[6px] text-[13px] text-left transition-colors"
                    style={{
                      color: isActive ? "#ffffff" : "#cccccc",
                      background: isActive ? "#37373d" : "transparent",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive)
                        e.currentTarget.style.background = "#2a2d2e"
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
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab Bar */}
          <div className="h-[35px] flex items-end shrink-0 bg-[#252526]">
            {sidebarCollapsed && (
              <button
                onClick={() => setSidebarCollapsed(false)}
                className="h-[35px] flex items-center px-2 text-[#6a6a6a] hover:text-[#cccccc]"
              >
                <ChevronRight size={14} className="rotate-180" />
              </button>
            )}
            <div
              className="h-[35px] flex items-center px-4 text-[13px] cursor-default bg-[#1e1e1e] text-[#cccccc] border-t border-t-[#007acc] border-r border-r-[#3e3e42]"
              style={{ minWidth: "120px" }}
            >
              <span className="truncate">{currentTitle}</span>
            </div>
          </div>

          {/* Editor Content */}
          <div className="flex-1 overflow-auto bg-[#1e1e1e]">{children}</div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="h-[22px] flex items-center px-3 shrink-0 text-[12px] bg-[#007acc] text-white">
        <div className="flex items-center gap-4">
          <span>Zero-Employee Orchestrator</span>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-4">
          <span>TypeScript React</span>
        </div>
      </div>
    </div>
  )
}
