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
  Globe,
  Plus,
  X,
} from "lucide-react"
import { api } from "../shared/api/client"
import { useT, useI18n, LOCALE_LABELS, BUILTIN_LOCALES, type Locale } from "@/shared/i18n"

interface ProviderInfo {
  name: string
  description: string
  configured: boolean
}

interface CustomProvider {
  key: string
  name: string
  placeholder: string
}

const DEFAULT_PROVIDER_KEYS = [
  {
    key: "OPENROUTER_API_KEY",
    name: "OpenRouter",
    placeholder: "sk-or-v1-xxxxxxxxxxxx",
  },
  {
    key: "OPENAI_API_KEY",
    name: "OpenAI",
    placeholder: "sk-xxxxxxxxxxxx",
  },
  {
    key: "ANTHROPIC_API_KEY",
    name: "Anthropic",
    placeholder: "sk-ant-xxxxxxxxxxxx",
  },
  {
    key: "GEMINI_API_KEY",
    name: "Google Gemini",
    placeholder: "AIzaSy-xxxxxxxxxxxx",
  },
]

const EXECUTION_MODES = [
  { value: "quality", labelKey: "modeQuality" as const, descKey: "modeQualityDesc" as const },
  { value: "speed", labelKey: "modeSpeed" as const, descKey: "modeSpeedDesc" as const },
  { value: "cost", labelKey: "modeCost" as const, descKey: "modeCostDesc" as const },
  { value: "free", labelKey: "modeFree" as const, descKey: "modeFreeDesc" as const },
  { value: "subscription", labelKey: "modeSubscription" as const, descKey: "modeSubscriptionDesc" as const },
] as const

export function SettingsPage() {
  const t = useT()
  const { locale, setLocale } = useI18n()

  const [companyName, setCompanyName] = useState("")
  const [mission, setMission] = useState("")
  const [executionMode, setExecutionMode] = useState("quality")
  const [autoApprove, setAutoApprove] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState("")

  // Language change tracking
  const [languageChanged, setLanguageChanged] = useState(false)

  // API Key states
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({})
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [providerStatus, setProviderStatus] = useState<Record<string, ProviderInfo>>({})
  const [_configLoading, setConfigLoading] = useState(true)

  // Custom provider states
  const [customProviders, setCustomProviders] = useState<CustomProvider[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [newProviderName, setNewProviderName] = useState("")
  const [newProviderKey, setNewProviderKey] = useState("")
  const [newProviderPlaceholder, setNewProviderPlaceholder] = useState("")

  // Load custom providers from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("custom_providers")
      if (stored) setCustomProviders(JSON.parse(stored))
    } catch { /* noop */ }
  }, [])

  const saveCustomProviders = (providers: CustomProvider[]) => {
    setCustomProviders(providers)
    try { localStorage.setItem("custom_providers", JSON.stringify(providers)) } catch { /* noop */ }
  }

  const allProviderKeys = [
    ...DEFAULT_PROVIDER_KEYS,
    ...customProviders,
  ]

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
      setSaveMessage(t.settings.saved)
      setApiKeys((prev) => ({ ...prev, [key]: "" }))
      await loadConfig()
      setTimeout(() => setSaveMessage(""), 3000)
    } catch {
      setSaveMessage(t.settings.saveFailed)
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

  const handleLanguageChange = async (newLocale: Locale) => {
    setLocale(newLocale)
    setLanguageChanged(true)
    try {
      await api.put("/config", { key: "LANGUAGE", value: newLocale })
    } catch {
      // Backend may not be available; frontend change still applies
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put("/config", { key: "COMPANY_NAME", value: companyName })
      await api.put("/config", { key: "COMPANY_MISSION", value: mission })
      await api.put("/config", { key: "AUTO_APPROVE", value: String(autoApprove) })
      setSaveMessage(t.settings.saved)
      setTimeout(() => setSaveMessage(""), 3000)
    } catch {
      setSaveMessage(t.settings.saveFailed)
      setTimeout(() => setSaveMessage(""), 3000)
    } finally {
      setSaving(false)
    }
  }

  const handleAddCustomProvider = () => {
    if (!newProviderName || !newProviderKey) return
    const envKey = newProviderKey.toUpperCase().replace(/[^A-Z0-9_]/g, "_")
    const provider: CustomProvider = {
      key: envKey,
      name: newProviderName,
      placeholder: newProviderPlaceholder || `${envKey.toLowerCase()}-xxxxxxxxxxxx`,
    }
    saveCustomProviders([...customProviders, provider])
    setNewProviderName("")
    setNewProviderKey("")
    setNewProviderPlaceholder("")
    setShowAddForm(false)
  }

  const handleRemoveCustomProvider = (key: string) => {
    saveCustomProviders(customProviders.filter((p) => p.key !== key))
  }

  const providers = [
    {
      id: "openrouter",
      name: "OpenRouter",
      description: "LLM Gateway",
      connected: false,
    },
    {
      id: "google",
      name: "Google",
      description: "Google Workspace",
      connected: false,
    },
    {
      id: "github",
      name: "GitHub",
      description: "Repository",
      connected: false,
    },
    {
      id: "slack",
      name: "Slack",
      description: "Notifications",
      connected: false,
    },
  ]

  const isCustomProvider = (key: string) =>
    customProviders.some((p) => p.key === key)

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <Settings size={18} className="text-[#007acc]" />
          <h2 className="text-[14px] font-medium text-[#cccccc]">{t.settings.title}</h2>
        </div>

        {saveMessage && (
          <div className="mb-4 flex items-center gap-2 px-3 py-2 rounded border border-[#4ec9b0] bg-[#1e3a2e] text-[12px] text-[#4ec9b0]">
            <Check size={14} />
            {saveMessage}
          </div>
        )}

        {/* Language Settings */}
        <SettingsSection icon={Globe} title={t.settings.languageSettings}>
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-[11px] text-[#6a6a6a] block mb-2">
                {t.settings.uiLanguage}
              </label>
              <div className="flex flex-wrap gap-2">
                {(Object.keys(LOCALE_LABELS) as Locale[]).map((loc) => (
                  <button
                    key={loc}
                    onClick={() => handleLanguageChange(loc)}
                    className="px-4 py-2 rounded text-[12px] border transition-colors relative"
                    style={{
                      background: locale === loc ? "#007acc" : "transparent",
                      color: locale === loc ? "#ffffff" : "#cccccc",
                      borderColor: locale === loc ? "#007acc" : "#3e3e42",
                    }}
                  >
                    {LOCALE_LABELS[loc]}
                    {BUILTIN_LOCALES.has(loc) && (
                      <span className="ml-1.5 text-[9px] opacity-60">
                        ({t.settings.languageBuiltin})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-[11px] text-[#6a6a6a] block mb-1">
                {t.settings.aiLanguage}
              </label>
              <div className="text-[11px] text-[#6a6a6a]">
                {t.settings.aiLanguageDesc}
              </div>
            </div>
            <div className="text-[11px] text-[#6a6a6a] flex items-start gap-1.5">
              <Globe size={12} className="mt-0.5 shrink-0" />
              {t.settings.languageAiNote}
            </div>
            {languageChanged && (
              <div className="flex items-center gap-2 px-3 py-2 rounded border border-[#cca700] bg-[#3a3000] text-[11px] text-[#cca700]">
                {t.settings.languageRestartHint}
              </div>
            )}
          </div>
        </SettingsSection>

        {/* LLM API Keys */}
        <SettingsSection icon={Key} title={t.settings.apiKeys}>
          <div className="flex flex-col gap-1 mb-3">
            <div className="text-[11px] text-[#6a6a6a]">
              {t.settings.apiKeysDesc}
            </div>
            <div className="text-[11px] text-[#6a6a6a]">
              {t.settings.apiKeysCli} <code className="text-[#dcdcaa] bg-[#1e1e1e] px-1 rounded">zero-employee config set GEMINI_API_KEY</code>
            </div>
          </div>
          <div className="flex flex-col gap-3">
            {allProviderKeys.map((provider) => {
              const status = providerStatus[provider.key === "OPENROUTER_API_KEY" ? "openrouter"
                : provider.key === "OPENAI_API_KEY" ? "openai"
                : provider.key === "ANTHROPIC_API_KEY" ? "anthropic"
                : provider.key === "GEMINI_API_KEY" ? "gemini"
                : provider.key.toLowerCase().replace(/_api_key$/, "")]
              const isConfigured = status?.configured ?? false
              const isCustom = isCustomProvider(provider.key)

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
                    </div>
                    <div className="flex items-center gap-2">
                      {isConfigured && (
                        <span className="text-[10px] text-[#4ec9b0] border border-[#4ec9b0] rounded px-1.5 py-0.5">
                          {t.settings.configured}
                        </span>
                      )}
                      {isCustom && (
                        <button
                          onClick={() => handleRemoveCustomProvider(provider.key)}
                          className="text-[#6a6a6a] hover:text-[#f44747] transition-colors"
                          title={t.settings.removeProvider}
                        >
                          <X size={14} />
                        </button>
                      )}
                    </div>
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
                        placeholder={isConfigured ? t.settings.overwrite : provider.placeholder}
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
                      {t.common.save}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Add custom provider */}
          {!showAddForm ? (
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-3 flex items-center gap-1.5 px-3 py-2 rounded text-[12px] text-[#007acc] border border-dashed border-[#3e3e42] hover:border-[#007acc] transition-colors w-full justify-center"
            >
              <Plus size={14} />
              {t.settings.addCustomProvider}
            </button>
          ) : (
            <div className="mt-3 rounded border border-[#007acc] bg-[#1e1e1e] px-3 py-3">
              <div className="flex flex-col gap-2">
                <div className="flex gap-2">
                  <input
                    value={newProviderName}
                    onChange={(e) => setNewProviderName(e.target.value)}
                    placeholder={t.settings.customProviderName}
                    className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc]"
                  />
                  <input
                    value={newProviderKey}
                    onChange={(e) => setNewProviderKey(e.target.value)}
                    placeholder={t.settings.customProviderKey}
                    className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] font-mono"
                  />
                </div>
                <div className="flex gap-2">
                  <input
                    value={newProviderPlaceholder}
                    onChange={(e) => setNewProviderPlaceholder(e.target.value)}
                    placeholder={t.settings.customProviderPlaceholder}
                    className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] font-mono"
                  />
                  <button
                    onClick={handleAddCustomProvider}
                    disabled={!newProviderName || !newProviderKey}
                    className="px-3 py-1.5 rounded text-[11px] bg-[#007acc] text-white disabled:opacity-40"
                  >
                    {t.settings.addProvider}
                  </button>
                  <button
                    onClick={() => setShowAddForm(false)}
                    className="px-3 py-1.5 rounded text-[11px] text-[#cccccc] border border-[#3e3e42]"
                  >
                    {t.common.cancel}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Ollama info */}
          <div className="mt-3 rounded border border-[#3e3e42] bg-[#1e1e1e] px-3 py-3">
            <div className="flex items-center gap-2 mb-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ background: providerStatus.ollama?.configured ? "#4ec9b0" : "#6a6a6a" }}
              />
              <span className="text-[13px] text-[#cccccc]">{t.settings.ollamaLocal}</span>
              <span className="text-[11px] text-[#6a6a6a]">{t.settings.ollamaDesc}</span>
            </div>
            <div className="text-[11px] text-[#6a6a6a] ml-4">
              {t.settings.ollamaAutoDetect}{" "}
              CLI: <code className="text-[#dcdcaa] bg-[#252526] px-1 rounded">zero-employee models</code>
            </div>
          </div>
        </SettingsSection>

        {/* Execution Mode */}
        <SettingsSection icon={Cpu} title={t.settings.executionMode}>
          <div>
            <label className="text-[11px] text-[#6a6a6a] block mb-2">
              {t.settings.executionModeDesc}
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
                  {t.settings[mode.labelKey]}
                </button>
              ))}
            </div>
            <div className="text-[11px] text-[#6a6a6a] mt-2">
              {EXECUTION_MODES.find((m) => m.value === executionMode)
                ? t.settings[EXECUTION_MODES.find((m) => m.value === executionMode)!.descKey]
                : ""}
            </div>
          </div>
        </SettingsSection>

        {/* Company Settings */}
        <SettingsSection icon={Building2} title={t.settings.companySettings}>
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-[11px] text-[#6a6a6a] block mb-1">
                {t.settings.companyName}
              </label>
              <input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc]"
              />
            </div>
            <div>
              <label className="text-[11px] text-[#6a6a6a] block mb-1">
                {t.settings.companyMission}
              </label>
              <textarea
                value={mission}
                onChange={(e) => setMission(e.target.value)}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] resize-none"
                rows={3}
              />
            </div>
          </div>
        </SettingsSection>

        {/* Provider Connections */}
        <SettingsSection icon={Link2} title={t.settings.providerConnections}>
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
                    {t.settings.disconnect}
                  </button>
                ) : (
                  <button className="flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-[#007acc] text-white">
                    <Link2 size={12} />
                    {t.settings.connect}
                  </button>
                )}
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* Policies */}
        <SettingsSection icon={Shield} title={t.settings.policies}>
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[13px] text-[#cccccc]">{t.settings.autoApprove}</div>
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
          {saving ? t.settings.saving : t.common.save}
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
