import { useState, useEffect, useCallback } from "react"
import {
  Settings,
  Link2,
  Unlink,
  Shield,
  Cpu,
  Building2,
  Save,
  Key,
  Eye,
  EyeOff,
  Check,
} from "lucide-react"
import { api } from "../shared/api/client"

interface ProviderInfo {
  name: string
  description: string
  configured: boolean
}

const PROVIDER_KEYS = [
  {
    key: "OPENROUTER_API_KEY",
    name: "OpenRouter",
    description: "複数LLMを一括利用",
    placeholder: "sk-or-v1-xxxxxxxxxxxx",
  },
  {
    key: "OPENAI_API_KEY",
    name: "OpenAI",
    description: "GPT-5.4等を直接利用",
    placeholder: "sk-xxxxxxxxxxxx",
  },
  {
    key: "ANTHROPIC_API_KEY",
    name: "Anthropic",
    description: "Claude等を直接利用",
    placeholder: "sk-ant-xxxxxxxxxxxx",
  },
  {
    key: "GEMINI_API_KEY",
    name: "Google Gemini",
    description: "無料枠あり・クレカ不要",
    placeholder: "AIzaSy-xxxxxxxxxxxx",
  },
] as const

const EXECUTION_MODES = [
  { value: "quality", label: "高品質", labelEn: "Quality" },
  { value: "speed", label: "高速", labelEn: "Speed" },
  { value: "cost", label: "コスト効率", labelEn: "Cost" },
  { value: "free", label: "無料", labelEn: "Free" },
  { value: "subscription", label: "サブスク", labelEn: "Subscription" },
] as const

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
  const [executionMode, setExecutionMode] = useState("quality")
  const [autoApprove, setAutoApprove] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState("")

  // API Key states
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({})
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [providerStatus, setProviderStatus] = useState<Record<string, ProviderInfo>>({})
  const [_configLoading, setConfigLoading] = useState(true)

  const loadConfig = useCallback(async () => {
    try {
      setConfigLoading(true)
      const [configRes, providerRes] = await Promise.all([
        api.get("/config") as Promise<Record<string, unknown>>,
        api.get("/config/providers") as Promise<Record<string, unknown>>,
      ])
      if (configRes.execution_mode) {
        setExecutionMode(configRes.execution_mode as string)
      }
      if (providerRes.providers) {
        setProviderStatus(providerRes.providers as Record<string, ProviderInfo>)
      }
    } catch {
      // API may not be available yet
    } finally {
      setConfigLoading(false)
    }
  }, [])

  useEffect(() => {
    loadConfig()
  }, [loadConfig])

  const handleSaveApiKey = async (key: string) => {
    const value = apiKeys[key]
    if (!value) return

    setSaving(true)
    try {
      await api.put("/config", { key, value })
      setSaveMessage(`${key} を保存しました`)
      setApiKeys((prev) => ({ ...prev, [key]: "" }))
      await loadConfig()
      setTimeout(() => setSaveMessage(""), 3000)
    } catch {
      setSaveMessage("保存に失敗しました")
      setTimeout(() => setSaveMessage(""), 3000)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveMode = async (mode: string) => {
    setExecutionMode(mode)
    try {
      await api.put("/config", { key: "DEFAULT_EXECUTION_MODE", value: mode })
    } catch {
      // ignore
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      // TODO: PUT /settings (company settings)
      await new Promise((r) => setTimeout(r, 500))
      setSaveMessage("設定を保存しました")
      setTimeout(() => setSaveMessage(""), 3000)
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

        {saveMessage && (
          <div className="mb-4 flex items-center gap-2 px-3 py-2 rounded border border-[#4ec9b0] bg-[#1e3a2e] text-[12px] text-[#4ec9b0]">
            <Check size={14} />
            {saveMessage}
          </div>
        )}

        {/* LLM API Keys */}
        <SettingsSection icon={Key} title="LLM API キー設定">
          <div className="flex flex-col gap-1 mb-3">
            <div className="text-[11px] text-[#6a6a6a]">
              .env ファイルを直接編集する代わりに、ここから API キーを設定できます。
            </div>
            <div className="text-[11px] text-[#6a6a6a]">
              CLI からも設定可能: <code className="text-[#dcdcaa] bg-[#1e1e1e] px-1 rounded">zero-employee config set GEMINI_API_KEY</code>
            </div>
          </div>
          <div className="flex flex-col gap-3">
            {PROVIDER_KEYS.map((provider) => {
              const status = providerStatus[provider.key === "OPENROUTER_API_KEY" ? "openrouter"
                : provider.key === "OPENAI_API_KEY" ? "openai"
                : provider.key === "ANTHROPIC_API_KEY" ? "anthropic"
                : "gemini"]
              const isConfigured = status?.configured ?? false

              return (
                <div
                  key={provider.key}
                  className="rounded border border-[#3e3e42] bg-[#1e1e1e] px-3 py-3"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ background: isConfigured ? "#4ec9b0" : "#6a6a6a" }}
                      />
                      <span className="text-[13px] text-[#cccccc]">{provider.name}</span>
                      <span className="text-[11px] text-[#6a6a6a]">{provider.description}</span>
                    </div>
                    {isConfigured && (
                      <span className="text-[10px] text-[#4ec9b0] border border-[#4ec9b0] rounded px-1.5 py-0.5">
                        設定済み
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        type={showKeys[provider.key] ? "text" : "password"}
                        value={apiKeys[provider.key] || ""}
                        onChange={(e) =>
                          setApiKeys((prev) => ({
                            ...prev,
                            [provider.key]: e.target.value,
                          }))
                        }
                        placeholder={isConfigured ? "（新しいキーで上書き）" : provider.placeholder}
                        className="w-full px-3 py-1.5 pr-8 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] font-mono"
                      />
                      <button
                        onClick={() =>
                          setShowKeys((prev) => ({
                            ...prev,
                            [provider.key]: !prev[provider.key],
                          }))
                        }
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-[#6a6a6a] hover:text-[#cccccc]"
                      >
                        {showKeys[provider.key] ? (
                          <EyeOff size={14} />
                        ) : (
                          <Eye size={14} />
                        )}
                      </button>
                    </div>
                    <button
                      onClick={() => handleSaveApiKey(provider.key)}
                      disabled={!apiKeys[provider.key] || saving}
                      className="px-3 py-1.5 rounded text-[11px] bg-[#007acc] text-white disabled:opacity-40"
                    >
                      保存
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Ollama info */}
          <div className="mt-3 rounded border border-[#3e3e42] bg-[#1e1e1e] px-3 py-3">
            <div className="flex items-center gap-2 mb-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ background: providerStatus.ollama?.configured ? "#4ec9b0" : "#6a6a6a" }}
              />
              <span className="text-[13px] text-[#cccccc]">Ollama (ローカルLLM)</span>
              <span className="text-[11px] text-[#6a6a6a]">APIキー不要・オフライン・無制限</span>
            </div>
            <div className="text-[11px] text-[#6a6a6a] ml-4">
              Ollama がインストール済みであれば自動検出されます。
              CLI: <code className="text-[#dcdcaa] bg-[#252526] px-1 rounded">zero-employee models</code>
            </div>
          </div>
        </SettingsSection>

        {/* Execution Mode */}
        <SettingsSection icon={Cpu} title="実行モード">
          <div>
            <label className="text-[11px] text-[#6a6a6a] block mb-2">
              LLM の利用方法を選択
            </label>
            <div className="flex flex-wrap gap-2">
              {EXECUTION_MODES.map((mode) => (
                <button
                  key={mode.value}
                  onClick={() => handleSaveMode(mode.value)}
                  className="px-3 py-1.5 rounded text-[12px] border transition-colors"
                  style={{
                    background: executionMode === mode.value ? "#007acc" : "transparent",
                    color: executionMode === mode.value ? "#ffffff" : "#cccccc",
                    borderColor: executionMode === mode.value ? "#007acc" : "#3e3e42",
                  }}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            <div className="text-[11px] text-[#6a6a6a] mt-2">
              {executionMode === "quality" && "最高品質モデルを使用（APIキー必要）"}
              {executionMode === "speed" && "高速軽量モデルを使用（APIキー必要）"}
              {executionMode === "cost" && "コスト効率を最優先（APIキー必要）"}
              {executionMode === "free" && "Gemini無料枠 / Ollamaを使用"}
              {executionMode === "subscription" && "g4f経由でAPIキー不要（試用向け）"}
            </div>
          </div>
        </SettingsSection>

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
