import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Blocks,
  MessageSquare,
  Search,
  GitBranch,
  Webhook,
  ChevronRight,
} from "lucide-react";

interface LayoutProps {
  children: React.ReactNode;
}

const activityBarItems = [
  { icon: LayoutDashboard, path: "/", label: "Explorer" },
  { icon: Search, path: "/skills", label: "Skills" },
  { icon: GitBranch, path: "/skills/create", label: "Skill Generator" },
  { icon: Webhook, path: "/webhooks", label: "Webhooks" },
  { icon: Blocks, path: "/settings", label: "Settings" },
];

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden" style={{ background: '#1e1e1e' }}>
      {/* Title Bar */}
      <div
        className="flex items-center h-[30px] shrink-0 select-none"
        style={{ background: '#323233', borderBottom: '1px solid #3e3e42' }}
      >
        <div className="flex items-center gap-2 px-3 text-xs" style={{ color: '#969696' }}>
          <MessageSquare size={14} style={{ color: '#007acc' }} />
          <span>ZPCOS</span>
          <ChevronRight size={12} />
          <span style={{ color: '#cccccc' }}>
            {location.pathname === "/" && "Dashboard"}
            {location.pathname === "/interview" && "Interview"}
            {location.pathname.startsWith("/orchestrate") && "Orchestration"}
            {location.pathname === "/skills" && "Skills"}
            {location.pathname === "/skills/create" && "New Skill"}
            {location.pathname === "/webhooks" && "Webhooks"}
            {location.pathname === "/settings" && "Settings"}
          </span>
        </div>
        <div className="flex-1" />
        <div className="px-3 text-[11px]" style={{ color: '#6a6a6a' }}>
          v0.1.0
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar (VSCode left icon strip) */}
        <div
          className="w-[48px] shrink-0 flex flex-col items-center pt-1"
          style={{ background: '#333333', borderRight: '1px solid #3e3e42' }}
        >
          {activityBarItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => {
                  navigate(item.path);
                  setSidebarOpen(true);
                }}
                className="w-[48px] h-[48px] flex items-center justify-center relative"
                style={{
                  color: isActive ? '#ffffff' : '#858585',
                  borderLeft: isActive ? '2px solid #007acc' : '2px solid transparent',
                }}
                title={item.label}
              >
                <item.icon size={22} />
              </button>
            );
          })}
        </div>

        {/* Sidebar */}
        {sidebarOpen && (
          <div
            className="w-[240px] shrink-0 flex flex-col overflow-hidden"
            style={{ background: '#252526', borderRight: '1px solid #3e3e42' }}
          >
            <div
              className="h-[35px] flex items-center px-4 shrink-0 uppercase text-[11px] tracking-wider"
              style={{ color: '#bbbbbb' }}
            >
              {location.pathname === "/" && "Explorer"}
              {location.pathname === "/interview" && "Interview"}
              {location.pathname.startsWith("/orchestrate") && "Orchestration"}
              {location.pathname === "/skills" && "Skills"}
              {location.pathname === "/skills/create" && "Skill Generator"}
              {location.pathname === "/webhooks" && "Webhooks"}
              {location.pathname === "/settings" && "Settings"}
            </div>
            <SidebarContent />
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab Bar */}
          <div
            className="h-[35px] flex items-end shrink-0"
            style={{ background: '#252526' }}
          >
            <div
              className="h-[35px] flex items-center px-4 text-[13px] cursor-default"
              style={{
                background: '#1e1e1e',
                color: '#cccccc',
                borderTop: '1px solid #007acc',
                borderRight: '1px solid #3e3e42',
                minWidth: '120px',
              }}
            >
              <span className="truncate">
                {location.pathname === "/" && "dashboard.tsx"}
                {location.pathname === "/interview" && "interview.tsx"}
                {location.pathname.startsWith("/orchestrate") && "orchestration.tsx"}
                {location.pathname === "/skills" && "skills.tsx"}
                {location.pathname === "/skills/create" && "new-skill.tsx"}
                {location.pathname === "/webhooks" && "webhooks.json"}
                {location.pathname === "/settings" && "settings.json"}
              </span>
            </div>
          </div>

          {/* Editor Content */}
          <div className="flex-1 overflow-auto" style={{ background: '#1e1e1e' }}>
            {children}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div
        className="h-[22px] flex items-center px-3 shrink-0 text-[12px]"
        style={{ background: '#007acc', color: '#ffffff' }}
      >
        <div className="flex items-center gap-4">
          <span>ZPCOS</span>
          <span>UTF-8</span>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-4">
          <span>Ln 1, Col 1</span>
          <span>TypeScript React</span>
        </div>
      </div>
    </div>
  );
}

function SidebarContent() {
  const location = useLocation();
  const navigate = useNavigate();

  if (location.pathname === "/" || location.pathname === "/interview") {
    return (
      <div className="flex-1 overflow-auto">
        <SidebarSection title="Quick Actions">
          <SidebarItem label="New Task" onClick={() => navigate("/")} />
          <SidebarItem label="View Skills" onClick={() => navigate("/skills")} />
          <SidebarItem label="Create Skill" onClick={() => navigate("/skills/create")} />
        </SidebarSection>
        <SidebarSection title="Recent">
          <div className="px-4 py-2 text-[12px]" style={{ color: '#6a6a6a' }}>
            No recent tasks
          </div>
        </SidebarSection>
      </div>
    );
  }

  if (location.pathname === "/skills") {
    return (
      <div className="flex-1 overflow-auto">
        <SidebarSection title="Built-in Skills">
          <SidebarItem label="local-context" detail="File Analysis" />
        </SidebarSection>
        <SidebarSection title="Generated Skills">
          <div className="px-4 py-2 text-[12px]" style={{ color: '#6a6a6a' }}>
            No generated skills yet
          </div>
        </SidebarSection>
      </div>
    );
  }

  if (location.pathname === "/webhooks") {
    return (
      <div className="flex-1 overflow-auto">
        <SidebarSection title="Webhook Events">
          <SidebarItem label="orchestration.*" detail="3 events" />
          <SidebarItem label="skill.*" detail="2 events" />
          <SidebarItem label="heal.attempt" detail="1 event" />
          <SidebarItem label="judge.completed" detail="1 event" />
          <SidebarItem label="interview.*" detail="1 event" />
          <SidebarItem label="task.transition" detail="1 event" />
        </SidebarSection>
        <SidebarSection title="Integration">
          <SidebarItem label="n8n" detail="Recommended" />
          <SidebarItem label="Zapier" detail="Compatible" />
          <SidebarItem label="Custom" detail="Any HTTP" />
        </SidebarSection>
      </div>
    );
  }

  if (location.pathname === "/settings") {
    return (
      <div className="flex-1 overflow-auto">
        <SidebarSection title="Categories">
          <SidebarItem label="Authentication" />
          <SidebarItem label="Quality Mode" />
          <SidebarItem label="Allowed Directories" />
        </SidebarSection>
      </div>
    );
  }

  return null;
}

function SidebarSection({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div>
      <button
        className="w-full flex items-center gap-1 px-2 py-1 text-[11px] uppercase tracking-wider font-semibold"
        style={{ color: '#bbbbbb', background: '#252526' }}
        onClick={() => setOpen(!open)}
      >
        <ChevronRight size={14} className={`transition-transform ${open ? "rotate-90" : ""}`} />
        {title}
      </button>
      {open && children}
    </div>
  );
}

function SidebarItem({
  label,
  detail,
  onClick,
}: {
  label: string;
  detail?: string;
  onClick?: () => void;
}) {
  return (
    <button
      className="w-full flex items-center justify-between px-6 py-[3px] text-[13px] text-left"
      style={{ color: '#cccccc' }}
      onClick={onClick}
      onMouseEnter={(e) => (e.currentTarget.style.background = '#2a2d2e')}
      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
    >
      <span>{label}</span>
      {detail && <span className="text-[11px]" style={{ color: '#6a6a6a' }}>{detail}</span>}
    </button>
  );
}
