import { useState, useEffect, useCallback } from "react"
import {
  Settings,
  Link2,
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
  Palette,
  ChevronDown,
  Bot,
  Monitor,
  FolderOpen,
  Cloud,
} from "lucide-react"
import { api } from "../shared/api/client"
import { useT, useI18n, LOCALE_LABELS, BUILTIN_LOCALES, type Locale } from "@/shared/i18n"
import { useTheme, THEME_LABELS, type Theme } from "@/shared/hooks/use-theme"

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

/** All known LLM providers. Users can also add custom ones. */
const ALL_PROVIDER_KEYS = [
  { key: "OPENROUTER_API_KEY", name: "OpenRouter", placeholder: "sk-or-v1-xxxxxxxxxxxx", category: "gateway" },
  { key: "OPENAI_API_KEY", name: "OpenAI", placeholder: "sk-xxxxxxxxxxxx", category: "direct" },
  { key: "ANTHROPIC_API_KEY", name: "Anthropic", placeholder: "sk-ant-xxxxxxxxxxxx", category: "direct" },
  { key: "GEMINI_API_KEY", name: "Google Gemini", placeholder: "AIzaSy-xxxxxxxxxxxx", category: "direct" },
  { key: "DEEPSEEK_API_KEY", name: "DeepSeek", placeholder: "sk-xxxxxxxxxxxx", category: "direct" },
  { key: "MISTRAL_API_KEY", name: "Mistral", placeholder: "xxxxxxxxxxxx", category: "direct" },
  { key: "COHERE_API_KEY", name: "Cohere", placeholder: "xxxxxxxxxxxx", category: "direct" },
  { key: "GROQ_API_KEY", name: "Groq", placeholder: "gsk_xxxxxxxxxxxx", category: "direct" },
  { key: "TOGETHER_API_KEY", name: "Together AI", placeholder: "xxxxxxxxxxxx", category: "direct" },
  { key: "PERPLEXITY_API_KEY", name: "Perplexity", placeholder: "pplx-xxxxxxxxxxxx", category: "direct" },
  { key: "XAI_API_KEY", name: "xAI (Grok)", placeholder: "xai-xxxxxxxxxxxx", category: "direct" },
]

/** All known service integrations */
const ALL_CONNECTIONS = [
  { id: "openrouter", name: "OpenRouter", description: "LLM Gateway", category: "ai" },
  { id: "google", name: "Google Workspace", description: "Docs, Sheets, Drive, Calendar, Gmail", category: "productivity" },
  { id: "github", name: "GitHub", description: "Repository & CI/CD", category: "dev" },
  { id: "gitlab", name: "GitLab", description: "Repository & CI/CD", category: "dev" },
  { id: "slack", name: "Slack", description: "Team messaging", category: "communication" },
  { id: "discord", name: "Discord", description: "Community chat", category: "communication" },
  { id: "notion", name: "Notion", description: "Knowledge base", category: "productivity" },
  { id: "obsidian", name: "Obsidian", description: "Local knowledge base", category: "productivity" },
  { id: "jira", name: "Jira", description: "Project management", category: "productivity" },
  { id: "linear", name: "Linear", description: "Issue tracking", category: "productivity" },
  { id: "n8n", name: "n8n", description: "Workflow automation", category: "automation" },
  { id: "zapier", name: "Zapier", description: "App integration", category: "automation" },
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
  const { theme, setTheme } = useTheme()

  const [companyName, setCompanyName] = useState("")
  const [mission, setMission] = useState("")
  const [executionMode, setExecutionMode] = useState("quality")
  const [autoApprove, setAutoApprove] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState("")
  const [languageChanged, setLanguageChanged] = useState(false)

  // API Key states
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({})
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [providerStatus, setProviderStatus] = useState<Record<string, ProviderInfo>>({})
  const [_configLoading, setConfigLoading] = useState(true)

  // Provider selector
  const [showProviderPicker, setShowProviderPicker] = useState(false)
  const [enabledProviders, setEnabledProviders] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem("enabled_providers")
      if (stored) return new Set(JSON.parse(stored))
    } catch { /* noop */ }
    return new Set(ALL_PROVIDER_KEYS.slice(0, 4).map(p => p.key))
  })

  // Custom provider states
  const [customProviders, setCustomProviders] = useState<CustomProvider[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [newProviderName, setNewProviderName] = useState("")
  const [newProviderKey, setNewProviderKey] = useState("")
  const [newProviderPlaceholder, setNewProviderPlaceholder] = useState("")

  // Connection filter
  const [connectionFilter, setConnectionFilter] = useState("all")

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

  const saveEnabledProviders = (set: Set<string>) => {
    setEnabledProviders(set)
    try { localStorage.setItem("enabled_providers", JSON.stringify([...set])) } catch { /* noop */ }
  }

  const toggleProvider = (key: string) => {
    const next = new Set(enabledProviders)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    saveEnabledProviders(next)
  }

  const visibleProviders = [
    ...ALL_PROVIDER_KEYS.filter(p => enabledProviders.has(p.key)),
    ...customProviders,
  ]

  const loadConfig = useCallback(async () => {
    try {
      setConfigLoading(true)
      const [configRes, providerRes] = await Promise.all([
        api.get("/config") as Promise<Record<string, unknown>>,
        api.get("/config/providers") as Promise<Record<string, unknown>>,
      ])
      if (configRes.execution_mode) setExecutionMode(configRes.execution_mode as string)
      if (providerRes.providers) setProviderStatus(providerRes.providers as Record<string, ProviderInfo>)
    } catch { /* API may not be available yet */ }
    finally { setConfigLoading(false) }
  }, [])

  useEffect(() => { loadConfig() }, [loadConfig])

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
    } finally { setSaving(false) }
  }

  const handleSaveMode = async (mode: string) => {
    setExecutionMode(mode)
    try { await api.put("/config", { key: "DEFAULT_EXECUTION_MODE", value: mode }) }
    catch { /* ignore */ }
  }

  const handleLanguageChange = async (newLocale: Locale) => {
    setLocale(newLocale)
    setLanguageChanged(true)
    try { await api.put("/config", { key: "LANGUAGE", value: newLocale }) }
    catch { /* Backend may not be available; frontend change still applies */ }
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
    } finally { setSaving(false) }
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

  const isCustomProvider = (key: string) => customProviders.some((p) => p.key === key)

  const connectionCategories = [
    { key: "all", label: t.common.all },
    { key: "ai", label: "AI" },
    { key: "productivity", label: t.settings.catProductivity },
    { key: "dev", label: t.settings.catDev },
    { key: "communication", label: t.settings.catCommunication },
    { key: "automation", label: t.settings.catAutomation },
  ]

  const filteredConnections = connectionFilter === "all"
    ? ALL_CONNECTIONS
    : ALL_CONNECTIONS.filter(c => c.category === connectionFilter)

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-6">
          <Settings size={18} className="text-[var(--accent)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.settings.title}</h2>
        </div>

        {saveMessage && (
          <div className="mb-4 flex items-center gap-2 px-3 py-2 rounded border border-[var(--success-fg)] bg-[var(--success)] text-[12px] text-white">
            <Check size={14} />
            {saveMessage}
          </div>
        )}

        {/* Theme Settings */}
        <SettingsSection icon={Palette} title={t.settings.themeSettings}>
          <div className="flex flex-wrap gap-2">
            {(Object.keys(THEME_LABELS) as Theme[]).map((th) => (
              <button
                key={th}
                onClick={() => setTheme(th)}
                className="px-4 py-2 rounded text-[12px] border transition-colors"
                style={{
                  background: theme === th ? "var(--accent)" : "transparent",
                  color: theme === th ? "var(--accent-fg)" : "var(--text-primary)",
                  borderColor: theme === th ? "var(--accent)" : "var(--border)",
                }}
                aria-pressed={theme === th}
              >
                {THEME_LABELS[th]}
              </button>
            ))}
          </div>
        </SettingsSection>

        {/* Language Settings */}
        <SettingsSection icon={Globe} title={t.settings.languageSettings}>
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-[11px] text-[var(--text-muted)] block mb-2">
                {t.settings.uiLanguage}
              </label>
              <div className="flex flex-wrap gap-2">
                {(Object.keys(LOCALE_LABELS) as Locale[]).map((loc) => (
                  <button
                    key={loc}
                    onClick={() => handleLanguageChange(loc)}
                    className="px-4 py-2 rounded text-[12px] border transition-colors relative"
                    style={{
                      background: locale === loc ? "var(--accent)" : "transparent",
                      color: locale === loc ? "var(--accent-fg)" : "var(--text-primary)",
                      borderColor: locale === loc ? "var(--accent)" : "var(--border)",
                    }}
                    aria-pressed={locale === loc}
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
            <div className="text-[11px] text-[var(--text-muted)] flex items-start gap-1.5">
              <Globe size={12} className="mt-0.5 shrink-0" />
              {t.settings.languageAiNote}
            </div>
            {languageChanged && (
              <div className="flex items-center gap-2 px-3 py-2 rounded border border-[var(--warning)] bg-[var(--bg-active)] text-[11px] text-[var(--warning)]">
                {t.settings.languageRestartHint}
              </div>
            )}
          </div>
        </SettingsSection>

        {/* LLM API Keys */}
        <SettingsSection icon={Key} title={t.settings.apiKeys}>
          <div className="flex flex-col gap-1 mb-3">
            <div className="text-[11px] text-[var(--text-muted)]">{t.settings.apiKeysDesc}</div>
            <div className="text-[11px] text-[var(--text-muted)]">
              {t.settings.apiKeysCli} <code className="text-[var(--warning)] bg-[var(--bg-base)] px-1 rounded">zero-employee config set GEMINI_API_KEY</code>
            </div>
          </div>

          {/* Visible provider keys */}
          <div className="flex flex-col gap-3">
            {visibleProviders.map((provider) => {
              const statusKey = provider.key.toLowerCase().replace(/_api_key$/, "")
              const isConfigured = providerStatus[statusKey]?.configured ?? false
              const isCustom = isCustomProvider(provider.key)

              return (
                <div key={provider.key} className="rounded border border-[var(--border)] bg-[var(--bg-base)] px-3 py-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: isConfigured ? "var(--success-fg)" : "var(--text-muted)" }} />
                      <span className="text-[13px] text-[var(--text-primary)]">{provider.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {isConfigured && (
                        <span className="text-[10px] text-[var(--success-fg)] border border-[var(--success-fg)] rounded px-1.5 py-0.5">
                          {t.settings.configured}
                        </span>
                      )}
                      {isCustom && (
                        <button onClick={() => handleRemoveCustomProvider(provider.key)}
                          className="text-[var(--text-muted)] hover:text-[var(--error)] transition-colors"
                          aria-label={t.settings.removeProvider}>
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
                        onChange={(e) => setApiKeys((prev) => ({ ...prev, [provider.key]: e.target.value }))}
                        placeholder={isConfigured ? t.settings.overwrite : provider.placeholder}
                        className="w-full px-3 py-1.5 pr-8 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] font-mono"
                        aria-label={`${provider.name} API Key`}
                      />
                      <button
                        onClick={() => setShowKeys((prev) => ({ ...prev, [provider.key]: !prev[provider.key] }))}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                        aria-label={showKeys[provider.key] ? "Hide key" : "Show key"}
                      >
                        {showKeys[provider.key] ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                    <button
                      onClick={() => handleSaveApiKey(provider.key)}
                      disabled={!apiKeys[provider.key] || saving}
                      className="px-3 py-1.5 rounded text-[11px] bg-[var(--accent)] text-[var(--accent-fg)] disabled:opacity-40"
                    >
                      {t.common.save}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Provider picker dropdown */}
          <div className="mt-3">
            <button
              onClick={() => setShowProviderPicker(!showProviderPicker)}
              className="flex items-center gap-1.5 px-3 py-2 rounded text-[12px] border border-dashed border-[var(--border)] hover:border-[var(--accent)] transition-colors w-full justify-center text-[var(--text-muted)]"
            >
              <ChevronDown size={14} style={{ transform: showProviderPicker ? "rotate(180deg)" : "none", transition: "transform 150ms" }} />
              {t.settings.selectProviders}
            </button>
            {showProviderPicker && (
              <div className="mt-1 border border-[var(--border)] rounded bg-[var(--bg-surface)] p-2 max-h-[200px] overflow-auto">
                {ALL_PROVIDER_KEYS.map(p => (
                  <label key={p.key} className="flex items-center gap-2 px-2 py-1.5 rounded text-[12px] cursor-pointer hover:bg-[var(--bg-hover)] text-[var(--text-primary)]">
                    <input type="checkbox" checked={enabledProviders.has(p.key)}
                      onChange={() => toggleProvider(p.key)} className="accent-[var(--accent)]" />
                    <span>{p.name}</span>
                    <span className="text-[10px] text-[var(--text-muted)] ml-auto">{p.category}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Add custom provider */}
          {!showAddForm ? (
            <button onClick={() => setShowAddForm(true)}
              className="mt-2 flex items-center gap-1.5 px-3 py-2 rounded text-[12px] text-[var(--accent)] border border-dashed border-[var(--border)] hover:border-[var(--accent)] transition-colors w-full justify-center">
              <Plus size={14} />
              {t.settings.addCustomProvider}
            </button>
          ) : (
            <div className="mt-2 rounded border border-[var(--accent)] bg-[var(--bg-base)] px-3 py-3">
              <div className="flex flex-col gap-2">
                <div className="flex gap-2">
                  <input value={newProviderName} onChange={(e) => setNewProviderName(e.target.value)}
                    placeholder={t.settings.customProviderName}
                    className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]" />
                  <input value={newProviderKey} onChange={(e) => setNewProviderKey(e.target.value)}
                    placeholder={t.settings.customProviderKey}
                    className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] font-mono" />
                </div>
                <div className="flex gap-2">
                  <input value={newProviderPlaceholder} onChange={(e) => setNewProviderPlaceholder(e.target.value)}
                    placeholder={t.settings.customProviderPlaceholder}
                    className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] font-mono" />
                  <button onClick={handleAddCustomProvider} disabled={!newProviderName || !newProviderKey}
                    className="px-3 py-1.5 rounded text-[11px] bg-[var(--accent)] text-[var(--accent-fg)] disabled:opacity-40">
                    {t.settings.addProvider}
                  </button>
                  <button onClick={() => setShowAddForm(false)}
                    className="px-3 py-1.5 rounded text-[11px] text-[var(--text-primary)] border border-[var(--border)]">
                    {t.common.cancel}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Ollama info */}
          <div className="mt-3 rounded border border-[var(--border)] bg-[var(--bg-base)] px-3 py-3">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full" style={{ background: providerStatus.ollama?.configured ? "var(--success-fg)" : "var(--text-muted)" }} />
              <span className="text-[13px] text-[var(--text-primary)]">{t.settings.ollamaLocal}</span>
              <span className="text-[11px] text-[var(--text-muted)]">{t.settings.ollamaDesc}</span>
            </div>
            <div className="text-[11px] text-[var(--text-muted)] ml-4">
              {t.settings.ollamaAutoDetect}{" "}
              CLI: <code className="text-[var(--warning)] bg-[var(--bg-surface)] px-1 rounded">zero-employee models</code>
            </div>
          </div>
        </SettingsSection>

        {/* Execution Mode */}
        <SettingsSection icon={Cpu} title={t.settings.executionMode}>
          <div>
            <label className="text-[11px] text-[var(--text-muted)] block mb-2">{t.settings.executionModeDesc}</label>
            <div className="flex flex-wrap gap-2">
              {EXECUTION_MODES.map((mode) => (
                <button key={mode.value} onClick={() => handleSaveMode(mode.value)}
                  className="px-3 py-1.5 rounded text-[12px] border transition-colors"
                  style={{
                    background: executionMode === mode.value ? "var(--accent)" : "transparent",
                    color: executionMode === mode.value ? "var(--accent-fg)" : "var(--text-primary)",
                    borderColor: executionMode === mode.value ? "var(--accent)" : "var(--border)",
                  }}
                  aria-pressed={executionMode === mode.value}>
                  {t.settings[mode.labelKey]}
                </button>
              ))}
            </div>
            <div className="text-[11px] text-[var(--text-muted)] mt-2">
              {EXECUTION_MODES.find((m) => m.value === executionMode)
                ? t.settings[EXECUTION_MODES.find((m) => m.value === executionMode)!.descKey]
                : ""}
            </div>
          </div>
        </SettingsSection>

        {/* Agent Behavior */}
        <SettingsSection icon={Bot} title={t.settings.agentBehavior}>
          <div className="flex flex-col gap-4">
            {/* Autonomy Level */}
            <div>
              <label className="text-[11px] text-[var(--text-muted)] block mb-2">{t.settings.autonomyLevel}</label>
              <div className="flex flex-wrap gap-2">
                {(["observe", "assist", "semi_auto", "autonomous"] as const).map(level => (
                  <button key={level}
                    className="px-3 py-1.5 rounded text-[12px] border transition-colors"
                    style={{
                      background: level === "semi_auto" ? "var(--accent)" : "transparent",
                      color: level === "semi_auto" ? "var(--accent-fg)" : "var(--text-primary)",
                      borderColor: level === "semi_auto" ? "var(--accent)" : "var(--border)",
                    }}>
                    {t.settings[`autonomy_${level}` as keyof typeof t.settings] as string}
                  </button>
                ))}
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-1">{t.settings.autonomyDesc}</div>
            </div>

            {/* Browser Automation */}
            <div className="rounded border border-[var(--border)] bg-[var(--bg-base)] p-3">
              <div className="flex items-center gap-2 mb-2">
                <Monitor size={14} className="text-[var(--accent)]" />
                <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.settings.browserAutomation}</span>
              </div>
              <div className="flex flex-col gap-2 text-[12px]">
                <label className="flex items-center justify-between">
                  <span className="text-[var(--text-secondary)]">{t.settings.browserEnabled}</span>
                  <span className="text-[var(--success-fg)] text-[11px]">ON</span>
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-[var(--text-secondary)]">{t.settings.webAiSession}</span>
                  <span className="text-[var(--success-fg)] text-[11px]">ON</span>
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-[var(--text-secondary)]">{t.settings.siteInteraction}</span>
                  <span className="text-[var(--text-muted)] text-[11px]">{t.settings.requiresApproval}</span>
                </label>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-2">{t.settings.browserDesc}</div>
            </div>

            {/* Workspace Access */}
            <div className="rounded border border-[var(--border)] bg-[var(--bg-base)] p-3">
              <div className="flex items-center gap-2 mb-2">
                <FolderOpen size={14} className="text-[var(--accent)]" />
                <span className="text-[12px] font-medium text-[var(--text-primary)]">{t.settings.workspaceAccess}</span>
              </div>
              <div className="flex flex-col gap-2 text-[12px]">
                <label className="flex items-center justify-between">
                  <span className="text-[var(--text-secondary)]">{t.settings.localFileAccess}</span>
                  <span className="text-[var(--text-muted)] text-[11px]">OFF</span>
                </label>
                <label className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Cloud size={12} className="text-[var(--text-muted)]" />
                    <span className="text-[var(--text-secondary)]">{t.settings.cloudAccess}</span>
                  </div>
                  <span className="text-[var(--text-muted)] text-[11px]">OFF</span>
                </label>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-2">{t.settings.workspaceDesc}</div>
            </div>
          </div>
        </SettingsSection>

        {/* Company Settings */}
        <SettingsSection icon={Building2} title={t.settings.companySettings}>
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-[11px] text-[var(--text-muted)] block mb-1">{t.settings.companyName}</label>
              <input value={companyName} onChange={(e) => setCompanyName(e.target.value)}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]" />
            </div>
            <div>
              <label className="text-[11px] text-[var(--text-muted)] block mb-1">{t.settings.companyMission}</label>
              <textarea value={mission} onChange={(e) => setMission(e.target.value)}
                className="w-full px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] resize-none" rows={3} />
            </div>
          </div>
        </SettingsSection>

        {/* Provider Connections */}
        <SettingsSection icon={Link2} title={t.settings.providerConnections}>
          {/* Category filter */}
          <div className="flex flex-wrap gap-1 mb-3">
            {connectionCategories.map(cat => (
              <button key={cat.key} onClick={() => setConnectionFilter(cat.key)}
                className="px-2.5 py-1 rounded text-[11px] transition-colors"
                style={{
                  background: connectionFilter === cat.key ? "var(--accent)" : "var(--bg-input)",
                  color: connectionFilter === cat.key ? "var(--accent-fg)" : "var(--text-secondary)",
                }}>
                {cat.label}
              </button>
            ))}
          </div>
          <div className="flex flex-col gap-2">
            {filteredConnections.map((p) => (
              <div key={p.id} className="flex items-center justify-between rounded px-3 py-2 border border-[var(--border)] bg-[var(--bg-base)]">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-[var(--text-muted)]" />
                  <div>
                    <div className="text-[13px] text-[var(--text-primary)]">{p.name}</div>
                    <div className="text-[11px] text-[var(--text-muted)]">{p.description}</div>
                  </div>
                </div>
                <button className="flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-[var(--accent)] text-[var(--accent-fg)]"
                  aria-label={`${t.settings.connect} ${p.name}`}>
                  <Link2 size={12} />
                  {t.settings.connect}
                </button>
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* Policies */}
        <SettingsSection icon={Shield} title={t.settings.policies}>
          <div className="flex items-center justify-between">
            <div className="text-[13px] text-[var(--text-primary)]">{t.settings.autoApprove}</div>
            <button onClick={() => setAutoApprove(!autoApprove)}
              className="text-[12px] font-medium"
              style={{ color: autoApprove ? "var(--success-fg)" : "var(--text-muted)" }}
              aria-pressed={autoApprove} role="switch">
              {autoApprove ? "ON" : "OFF"}
            </button>
          </div>
        </SettingsSection>

        {/* Save */}
        <button onClick={handleSave} disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)] mt-4">
          <Save size={14} />
          {saving ? t.settings.saving : t.common.save}
        </button>
      </div>
    </div>
  )
}

function SettingsSection({ icon: Icon, title, children }: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="mb-6 rounded border border-[var(--border)] bg-[var(--bg-surface)]">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)]">
        <Icon size={14} className="text-[var(--accent)]" />
        <span className="text-[12px] font-medium text-[var(--text-primary)]">{title}</span>
      </div>
      <div className="px-4 py-4">{children}</div>
    </section>
  )
}
