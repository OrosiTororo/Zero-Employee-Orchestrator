import { useState } from "react"
import {
  Settings,
  Link2,
  Unlink,
  Shield,
  Cpu,
  Building2,
  Save,
} from "lucide-react"

const providers = [
  {
    id: "openrouter",
    name: "OpenRouter",
    description: "LLMゲートウェイ",
    connected: false,
  },
  {
    id: "google",
    name: "Google",
    description: "Google Workspace 連携",
    connected: false,
  },
  {
    id: "github",
    name: "GitHub",
    description: "リポジトリ連携",
    connected: false,
  },
  {
    id: "slack",
    name: "Slack",
    description: "通知・コミュニケーション",
    connected: false,
  },
]

export function SettingsPage() {
  const [companyName, setCompanyName] = useState("")
  const [mission, setMission] = useState("")
  const [qualityMode, setQualityMode] = useState("balanced")
  const [autoApprove, setAutoApprove] = useState(false)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      // TODO: PUT /settings
      await new Promise((r) => setTimeout(r, 500))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <Settings size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">設定</h2>
        </div>

        {/* Company Settings */}
        <SettingsSection icon={Building2} title="企業設定">
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-[11px] text-[#6a6a6a] block mb-1">
                企業名
              </label>
              <input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="株式会社サンプル"
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc]"
              />
            </div>
            <div>
              <label className="text-[11px] text-[#6a6a6a] block mb-1">
                ミッション
              </label>
              <textarea
                value={mission}
                onChange={(e) => setMission(e.target.value)}
                placeholder="テクノロジーで世界をより良くする"
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] resize-none"
                rows={3}
              />
            </div>
          </div>
        </SettingsSection>

        {/* Provider Connections */}
        <SettingsSection icon={Link2} title="プロバイダー接続">
          <div className="flex flex-col gap-2">
            {providers.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between rounded px-3 py-2 border border-[#3e3e42] bg-[#1e1e1e]"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{
                      background: p.connected ? "#4ec9b0" : "#6a6a6a",
                    }}
                  />
                  <div>
                    <div className="text-[13px] text-[#cccccc]">{p.name}</div>
                    <div className="text-[11px] text-[#6a6a6a]">
                      {p.description}
                    </div>
                  </div>
                </div>
                {p.connected ? (
                  <button className="flex items-center gap-1 px-2 py-1 rounded text-[11px] border border-[#3e3e42] text-[#f44747]">
                    <Unlink size={12} />
                    切断
                  </button>
                ) : (
                  <button className="flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-[#007acc] text-white">
                    <Link2 size={12} />
                    接続
                  </button>
                )}
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* Policies */}
        <SettingsSection icon={Shield} title="ポリシー">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[13px] text-[#cccccc]">自動承認</div>
                <div className="text-[11px] text-[#6a6a6a]">
                  低リスクのアクションを自動的に承認する
                </div>
              </div>
              <button
                onClick={() => setAutoApprove(!autoApprove)}
                className="text-[#6a6a6a]"
              >
                {autoApprove ? (
                  <span className="text-[#4ec9b0]">ON</span>
                ) : (
                  <span>OFF</span>
                )}
              </button>
            </div>
          </div>
        </SettingsSection>

        {/* Model Settings */}
        <SettingsSection icon={Cpu} title="モデル設定">
          <div>
            <label className="text-[11px] text-[#6a6a6a] block mb-2">
              品質モード
            </label>
            <div className="flex gap-2">
              {(["fastest", "balanced", "high_quality"] as const).map(
                (mode) => (
                  <button
                    key={mode}
                    onClick={() => setQualityMode(mode)}
                    className="px-3 py-1.5 rounded text-[12px] border transition-colors"
                    style={{
                      background:
                        qualityMode === mode ? "#007acc" : "transparent",
                      color: qualityMode === mode ? "#ffffff" : "#cccccc",
                      borderColor:
                        qualityMode === mode ? "#007acc" : "#3e3e42",
                    }}
                  >
                    {mode === "fastest"
                      ? "高速"
                      : mode === "balanced"
                        ? "バランス"
                        : "高品質"}
                  </button>
                ),
              )}
            </div>
          </div>
        </SettingsSection>

        {/* Save */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded text-[12px] bg-[#007acc] text-white mt-4"
        >
          <Save size={14} />
          {saving ? "保存中..." : "設定を保存"}
        </button>
      </div>
    </div>
  )
}

function SettingsSection({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-6 rounded border border-[#3e3e42] bg-[#252526]">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[#3e3e42]">
        <Icon size={14} className="text-[#007acc]" />
        <span className="text-[12px] font-medium text-[#cccccc]">{title}</span>
      </div>
      <div className="px-4 py-4">{children}</div>
    </div>
  )
}
