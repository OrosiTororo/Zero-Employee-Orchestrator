import { useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  ChevronRight,
  ChevronLeft,
  Building2,
  Bot,
  Key,
  Sparkles,
  Check,
  Info,
  CheckCircle,
  ClipboardList,
  Users,
  Loader2,
} from "lucide-react"
import { Logo } from "@/shared/ui/Logo"
import { useT, useI18n } from "@/shared/i18n"
import { api } from "@/shared/api/client"
import { useAuthStore } from "@/shared/hooks/use-auth"

type Step =
  | "welcome"
  | "organization"
  | "business_interview"
  | "provider"
  | "org_preview"
  | "complete"

const STEP_IDS: Step[] = [
  "welcome",
  "organization",
  "business_interview",
  "provider",
  "org_preview",
  "complete",
]

interface OrgPreview {
  departments: Array<{
    name: string
    code: string
    description: string
    teams: Array<{
      name: string
      purpose: string
      agents: Array<{ name: string; title: string; description: string }>
    }>
  }>
  total_departments: number
  total_teams: number
  total_agents: number
}

const BUSINESS_CATEGORIES = [
  { value: "tech_startup", label_ja: "\u30C6\u30C3\u30AF\u30B9\u30BF\u30FC\u30C8\u30A2\u30C3\u30D7", label_en: "Tech Startup" },
  { value: "ecommerce", label_ja: "EC / \u30AA\u30F3\u30E9\u30A4\u30F3\u30B7\u30E7\u30C3\u30D7", label_en: "E-commerce" },
  { value: "content_creator", label_ja: "\u30B3\u30F3\u30C6\u30F3\u30C4\u30AF\u30EA\u30A8\u30A4\u30BF\u30FC", label_en: "Content Creator" },
  { value: "consulting", label_ja: "\u30B3\u30F3\u30B5\u30EB\u30C6\u30A3\u30F3\u30B0", label_en: "Consulting" },
  { value: "saas", label_ja: "SaaS", label_en: "SaaS" },
  { value: "agency", label_ja: "\u4EE3\u7406\u5E97 / \u30A8\u30FC\u30B8\u30A7\u30F3\u30B7\u30FC", label_en: "Agency" },
  { value: "education", label_ja: "\u6559\u80B2", label_en: "Education" },
  { value: "other", label_ja: "\u305D\u306E\u4ED6", label_en: "Other" },
]

const PAIN_POINTS = [
  { value: "task_management", label_ja: "\u30BF\u30B9\u30AF\u7BA1\u7406", label_en: "Task Management" },
  { value: "customer_acquisition", label_ja: "\u96C6\u5BA2\u30FB\u9867\u5BA2\u7372\u5F97", label_en: "Customer Acquisition" },
  { value: "content_creation", label_ja: "\u30B3\u30F3\u30C6\u30F3\u30C4\u5236\u4F5C", label_en: "Content Creation" },
  { value: "data_analysis", label_ja: "\u30C7\u30FC\u30BF\u5206\u6790", label_en: "Data Analysis" },
  { value: "accounting", label_ja: "\u7D4C\u7406\u30FB\u4F1A\u8A08", label_en: "Accounting" },
  { value: "customer_support", label_ja: "\u30AB\u30B9\u30BF\u30DE\u30FC\u30B5\u30DD\u30FC\u30C8", label_en: "Customer Support" },
  { value: "research", label_ja: "\u30EA\u30B5\u30FC\u30C1\u30FB\u8ABF\u67FB", label_en: "Research" },
  { value: "development", label_ja: "\u958B\u767A", label_en: "Development" },
]

const TEAM_SIZES = [
  { value: "minimal", label_ja: "\u30DF\u30CB\u30DE\u30EB\uFF08\u79D8\u66F8\uFF0B\u5FC5\u8981\u6700\u5C0F\u9650\uFF09", label_en: "Minimal (secretary + essentials)" },
  { value: "standard", label_ja: "\u30B9\u30BF\u30F3\u30C0\u30FC\u30C9\uFF08\u63A8\u5968\u69CB\u6210\uFF09", label_en: "Standard (recommended)" },
  { value: "full", label_ja: "\u30D5\u30EB\uFF08\u5168\u90E8\u7F72\uFF09", label_en: "Full (all departments)" },
]

export function SetupPage() {
  const navigate = useNavigate()
  const t = useT()
  const { locale } = useI18n()

  const [currentStep, setCurrentStep] = useState<Step>("welcome")
  const [orgName, setOrgName] = useState("")
  const [orgMission, setOrgMission] = useState("")
  const [providerType, setProviderType] = useState("openrouter")
  const [executionMode, setExecutionMode] = useState("quality")

  // Business interview state
  const [businessDesc, setBizDesc] = useState("")
  const [businessCategory, setBizCat] = useState("other")
  const [painPoints, setPainPoints] = useState<string[]>([])
  const [teamSize, setTeamSize] = useState("minimal")
  const [secretaryOnly, setSecretaryOnly] = useState(false)

  // Org generation state
  const [orgPreview, setOrgPreview] = useState<OrgPreview | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isGenerated, setIsGenerated] = useState(false)

  const stepLabels: Record<Step, string> = {
    welcome: t.setup.steps.welcome,
    organization: t.setup.steps.organization,
    business_interview: t.setup.steps.businessInterview,
    provider: t.setup.steps.provider,
    org_preview: t.setup.steps.orgPreview,
    complete: t.setup.steps.complete,
  }

  const stepIndex = STEP_IDS.indexOf(currentStep)

  const next = () => {
    if (stepIndex < STEP_IDS.length - 1) {
      setCurrentStep(STEP_IDS[stepIndex + 1])
    }
  }
  const prev = () => {
    if (stepIndex > 0) {
      setCurrentStep(STEP_IDS[stepIndex - 1])
    }
  }

  const togglePainPoint = (value: string) => {
    setPainPoints((prev) =>
      prev.includes(value)
        ? prev.filter((p) => p !== value)
        : [...prev, value]
    )
  }

  const handlePreview = async () => {
    try {
      const result = await api.post<OrgPreview>("/org-setup/preview", {
        business_description: businessDesc,
        business_category: businessCategory,
        pain_points: painPoints,
        team_size_preference: teamSize,
        start_with_secretary_only: secretaryOnly,
      })
      setOrgPreview(result)
    } catch {
      setOrgPreview(null)
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      const slug = orgName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "my-org"
      const company = await api.post<{ id: string }>("/companies", {
        name: orgName || "My Organization",
        slug,
        mission: orgMission,
        description: businessDesc,
      })

      await api.post("/org-setup/generate", {
        company_id: company.id,
        interview: {
          business_description: businessDesc,
          business_category: businessCategory,
          pain_points: painPoints,
          team_size_preference: teamSize,
          start_with_secretary_only: secretaryOnly,
        },
        provider_name: providerType === "skip" ? "openrouter" : providerType,
      })

      setIsGenerated(true)
    } catch (err) {
      console.error("Failed to generate org:", err)
    } finally {
      setIsGenerating(false)
    }
  }

  const finishSetup = async () => {
    try {
      await api.post("/auth/setup-complete", {})
    } catch {
      // Mark locally even if backend call fails
    }
    useAuthStore.getState().setSetupCompleted()
    navigate("/")
  }

  const providers = [
    { id: "openrouter", name: t.setup.provider.openrouter, desc: t.setup.provider.openrouterDesc },
    { id: "openai", name: t.setup.provider.openai, desc: t.setup.provider.openaiDesc },
    { id: "anthropic", name: t.setup.provider.anthropic, desc: t.setup.provider.anthropicDesc },
    { id: "local", name: t.setup.provider.local, desc: t.setup.provider.localDesc },
    { id: "skip", name: t.setup.provider.skip, desc: t.setup.provider.skipDesc },
  ]

  const executionModes = [
    { id: "quality", label: t.setup.provider.quality },
    { id: "speed", label: t.setup.provider.speed },
    { id: "cost", label: t.setup.provider.cost },
    { id: "free", label: t.setup.provider.free },
  ]

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
      <div className="max-w-[600px] w-full px-8">
        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          {STEP_IDS.map((id, i) => (
            <div key={id} className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-medium transition-colors"
                style={{
                  background: i <= stepIndex ? "var(--accent)" : "var(--border)",
                  color: i <= stepIndex ? "#fff" : "var(--text-muted)",
                }}
                title={stepLabels[id]}
              >
                {i < stepIndex ? <Check size={14} /> : i + 1}
              </div>
              {i < STEP_IDS.length - 1 && (
                <div
                  className="w-6 h-[2px] transition-colors"
                  style={{
                    background: i < stepIndex ? "var(--accent)" : "var(--border)",
                  }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="min-h-[300px] max-h-[calc(100vh-200px)] overflow-auto">
          {/* Welcome Step */}
          {currentStep === "welcome" && (
            <div className="flex flex-col items-center gap-6 text-center">
              <Logo size={64} />
              <h2 className="text-2xl font-semibold text-[var(--text-primary)]">
                {t.setup.welcome.title}
              </h2>
              <p className="text-[14px] text-[var(--text-secondary)] leading-relaxed max-w-[450px] whitespace-pre-line">
                {t.setup.welcome.description}
              </p>
              <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-4 text-left max-w-[450px] w-full">
                <p className="text-[13px] text-[var(--text-primary)] font-medium mb-2">
                  {t.setup.welcome.highlightsTitle}
                </p>
                <ul className="space-y-2">
                  {t.setup.welcome.highlights.map((item, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-[12px] text-[var(--text-secondary)]"
                    >
                      <CheckCircle
                        size={14}
                        className="mt-0.5 shrink-0"
                        style={{ color: "var(--success)" }}
                      />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Organization Step */}
          {currentStep === "organization" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-3">
                <Building2 size={24} className="text-[var(--accent)]" />
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                  {t.setup.organization.title}
                </h2>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)]">
                {t.setup.organization.description}
              </p>
              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-[12px] text-[var(--text-secondary)] mb-1 block">
                    {t.setup.organization.orgName}
                  </label>
                  <input
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder={t.setup.organization.orgNamePlaceholder}
                    className="w-full px-3 py-2.5 rounded-md text-[13px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none"
                  />
                </div>
                <div>
                  <label className="text-[12px] text-[var(--text-secondary)] mb-1 block">
                    {t.setup.organization.mission}
                  </label>
                  <textarea
                    value={orgMission}
                    onChange={(e) => setOrgMission(e.target.value)}
                    placeholder={t.setup.organization.missionPlaceholder}
                    rows={3}
                    className="w-full px-3 py-2.5 rounded-md text-[13px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none resize-none"
                  />
                </div>
              </div>
              <div
                className="flex items-start gap-3 rounded-md p-4 border"
                style={{
                  background: "rgba(0, 120, 212, 0.05)",
                  borderColor: "var(--accent)",
                }}
              >
                <Info size={18} className="mt-0.5 shrink-0" style={{ color: "var(--accent)" }} />
                <div>
                  <p className="text-[13px] text-[var(--text-primary)] font-medium">
                    {t.setup.organization.tipTitle}
                  </p>
                  <p className="text-[12px] text-[var(--text-secondary)] mt-1">
                    {t.setup.organization.tipDescription}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Business Interview Step */}
          {currentStep === "business_interview" && (
            <div className="flex flex-col gap-5">
              <div className="flex items-center gap-3">
                <ClipboardList size={24} className="text-[var(--accent)]" />
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                  {t.orgSetup.interviewTitle}
                </h2>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)]">
                {t.orgSetup.businessDescPlaceholder}
              </p>

              <div>
                <label className="text-[12px] text-[var(--text-secondary)] mb-1 block">
                  {t.orgSetup.businessDesc}
                </label>
                <textarea
                  value={businessDesc}
                  onChange={(e) => setBizDesc(e.target.value)}
                  placeholder={t.orgSetup.businessDescPlaceholder}
                  rows={3}
                  className="w-full px-3 py-2.5 rounded-md text-[13px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none resize-none"
                />
              </div>

              <div>
                <label className="text-[12px] text-[var(--text-secondary)] mb-1 block">
                  {t.orgSetup.businessCategory}
                </label>
                <div className="flex flex-wrap gap-2">
                  {BUSINESS_CATEGORIES.map((cat) => (
                    <button
                      key={cat.value}
                      onClick={() => setBizCat(cat.value)}
                      className="px-3 py-1.5 rounded-md text-[12px] border transition-colors"
                      style={{
                        background: businessCategory === cat.value ? "rgba(0, 120, 212, 0.12)" : "transparent",
                        borderColor: businessCategory === cat.value ? "var(--accent)" : "var(--border)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {locale === "en" ? cat.label_en : locale === "zh" ? cat.label_en : cat.label_ja}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[12px] text-[var(--text-secondary)] mb-1 block">
                  {t.orgSetup.painPoints}
                </label>
                <div className="flex flex-wrap gap-2">
                  {PAIN_POINTS.map((pp) => (
                    <button
                      key={pp.value}
                      onClick={() => togglePainPoint(pp.value)}
                      className="px-3 py-1.5 rounded-md text-[12px] border transition-colors"
                      style={{
                        background: painPoints.includes(pp.value) ? "rgba(0, 120, 212, 0.12)" : "transparent",
                        borderColor: painPoints.includes(pp.value) ? "var(--accent)" : "var(--border)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {locale === "en" ? pp.label_en : locale === "zh" ? pp.label_en : pp.label_ja}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[12px] text-[var(--text-secondary)] mb-1 block">
                  {t.orgSetup.teamSize}
                </label>
                <div className="flex flex-col gap-2">
                  {TEAM_SIZES.map((ts) => (
                    <button
                      key={ts.value}
                      onClick={() => { setTeamSize(ts.value); if (ts.value !== "minimal") setSecretaryOnly(false) }}
                      className="flex items-center gap-3 px-4 py-2.5 rounded-md border text-left transition-colors"
                      style={{
                        background: teamSize === ts.value ? "rgba(0, 120, 212, 0.08)" : "transparent",
                        borderColor: teamSize === ts.value ? "var(--accent)" : "var(--border)",
                      }}
                    >
                      <div
                        className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                        style={{ borderColor: teamSize === ts.value ? "var(--accent)" : "var(--text-muted)" }}
                      >
                        {teamSize === ts.value && <div className="w-2 h-2 rounded-full bg-[var(--accent)]" />}
                      </div>
                      <span className="text-[13px] text-[var(--text-primary)]">
                        {locale === "en" ? ts.label_en : locale === "zh" ? ts.label_en : ts.label_ja}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div
                className="flex items-start gap-3 rounded-md p-4 border cursor-pointer"
                style={{
                  background: secretaryOnly ? "rgba(0, 120, 212, 0.05)" : "transparent",
                  borderColor: secretaryOnly ? "var(--accent)" : "var(--border)",
                }}
                onClick={() => { setSecretaryOnly(!secretaryOnly); if (!secretaryOnly) setTeamSize("minimal") }}
              >
                <div
                  className="w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 shrink-0"
                  style={{ borderColor: secretaryOnly ? "var(--accent)" : "var(--text-muted)" }}
                >
                  {secretaryOnly && <Check size={14} style={{ color: "var(--accent)" }} />}
                </div>
                <div>
                  <p className="text-[13px] text-[var(--text-primary)] font-medium">
                    {t.orgSetup.secretaryOnly}
                  </p>
                  <p className="text-[12px] text-[var(--text-secondary)] mt-1">
                    {t.orgSetup.secretaryOnlyTip}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Provider Step */}
          {currentStep === "provider" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-3">
                <Key size={24} className="text-[var(--accent)]" />
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                  {t.setup.provider.title}
                </h2>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)] whitespace-pre-line">
                {t.setup.provider.description}
              </p>

              <div className="flex flex-col gap-3">
                {providers.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setProviderType(p.id)}
                    className="flex items-center gap-3 px-4 py-3 rounded-md border text-left transition-colors"
                    style={{
                      background: providerType === p.id ? "rgba(0, 120, 212, 0.08)" : "transparent",
                      borderColor: providerType === p.id ? "var(--accent)" : "var(--border)",
                    }}
                  >
                    <div
                      className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                      style={{ borderColor: providerType === p.id ? "var(--accent)" : "var(--text-muted)" }}
                    >
                      {providerType === p.id && <div className="w-2 h-2 rounded-full bg-[var(--accent)]" />}
                    </div>
                    <div>
                      <div className="text-[13px] text-[var(--text-primary)] font-medium">{p.name}</div>
                      <div className="text-[11px] text-[var(--text-muted)]">{p.desc}</div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex flex-col gap-3 mt-2">
                <span className="text-[12px] text-[var(--text-secondary)]">{t.setup.provider.executionMode}</span>
                <div className="flex gap-2">
                  {executionModes.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setExecutionMode(m.id)}
                      className="flex-1 px-3 py-2 rounded-md text-[12px] border transition-colors"
                      style={{
                        background: executionMode === m.id ? "rgba(0, 120, 212, 0.12)" : "transparent",
                        borderColor: executionMode === m.id ? "var(--accent)" : "var(--border)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Org Preview & Generate Step */}
          {currentStep === "org_preview" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-3">
                <Users size={24} className="text-[var(--accent)]" />
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                  {t.orgSetup.generate}
                </h2>
              </div>

              {!isGenerated ? (
                <>
                  {!orgPreview && (
                    <div className="text-center py-4">
                      <button
                        onClick={handlePreview}
                        className="px-6 py-2.5 rounded-md text-[13px] font-medium text-white"
                        style={{ background: "var(--gradient-primary)" }}
                      >
                        {t.orgSetup.previewStructure}
                      </button>
                    </div>
                  )}

                  {orgPreview && (
                    <>
                      <div className="flex gap-4 text-center">
                        <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-3">
                          <div className="text-2xl font-bold text-[var(--accent)]">{orgPreview.total_departments}</div>
                          <div className="text-[11px] text-[var(--text-secondary)]">{t.orgSetup.deptCount}</div>
                        </div>
                        <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-3">
                          <div className="text-2xl font-bold text-[var(--accent)]">{orgPreview.total_teams}</div>
                          <div className="text-[11px] text-[var(--text-secondary)]">{t.orgSetup.teamCount}</div>
                        </div>
                        <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-3">
                          <div className="text-2xl font-bold text-[var(--accent)]">{orgPreview.total_agents}</div>
                          <div className="text-[11px] text-[var(--text-secondary)]">{t.orgSetup.agentCount}</div>
                        </div>
                      </div>

                      <div className="flex flex-col gap-2">
                        {orgPreview.departments.map((dept, i) => (
                          <div key={i} className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-3">
                            <div className="flex items-center gap-2">
                              <Building2 size={14} className="text-[var(--accent)]" />
                              <span className="text-[13px] font-medium text-[var(--text-primary)]">{dept.name}</span>
                              <span className="text-[11px] text-[var(--text-muted)]">{dept.code}</span>
                            </div>
                            <p className="text-[11px] text-[var(--text-secondary)] mt-1 ml-5">{dept.description}</p>
                            {dept.teams.map((team, j) => (
                              <div key={j} className="ml-5 mt-2">
                                {team.agents.map((agent, k) => (
                                  <div key={k} className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)]">
                                    <Bot size={12} className="text-[var(--accent)]" />
                                    <span className="text-[var(--text-primary)]">{agent.name}</span>
                                    <span className="text-[var(--text-muted)]">- {agent.title}</span>
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>

                      <button
                        onClick={handleGenerate}
                        disabled={isGenerating}
                        className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-md text-[13px] font-medium text-white disabled:opacity-60"
                        style={{ background: "var(--gradient-primary)" }}
                      >
                        {isGenerating ? (
                          <>
                            <Loader2 size={16} className="animate-spin" />
                            {t.orgSetup.generating}
                          </>
                        ) : (
                          <>
                            <Sparkles size={16} />
                            {t.orgSetup.buildOrg}
                          </>
                        )}
                      </button>
                    </>
                  )}
                </>
              ) : (
                <div className="flex flex-col items-center gap-4 py-8 text-center">
                  <div className="w-16 h-16 rounded-full flex items-center justify-center bg-[var(--success)]">
                    <Check size={32} color="#fff" />
                  </div>
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                    {t.orgSetup.generated}
                  </h3>
                  <p className="text-[13px] text-[var(--text-secondary)] max-w-[400px]">
                    {t.orgSetup.generatedDesc}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Complete Step */}
          {currentStep === "complete" && (
            <div className="flex flex-col items-center gap-6 text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center bg-[var(--success)]">
                <Sparkles size={32} color="#fff" />
              </div>
              <h2 className="text-2xl font-semibold text-[var(--text-primary)]">
                {t.setup.complete.title}
              </h2>
              <p className="text-[14px] text-[var(--text-secondary)] leading-relaxed max-w-[450px] whitespace-pre-line">
                {t.setup.complete.description}
              </p>
              <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-4 text-[12px] text-[var(--text-secondary)] text-left max-w-[400px] w-full">
                <p className="text-[var(--text-primary)] font-medium mb-2">{t.setup.complete.tryTitle}</p>
                <ul className="space-y-2">
                  <li>{t.setup.complete.try1}</li>
                  <li>{t.setup.complete.try2}</li>
                  <li>{t.setup.complete.try3}</li>
                </ul>
              </div>
              <div
                className="flex items-start gap-3 rounded-md p-4 border max-w-[400px] w-full text-left"
                style={{ background: "rgba(0, 120, 212, 0.05)", borderColor: "var(--accent)" }}
              >
                <Info size={18} className="mt-0.5 shrink-0" style={{ color: "var(--accent)" }} />
                <div>
                  <p className="text-[13px] text-[var(--text-primary)] font-medium">
                    {t.orgSetup.trySecretary}
                  </p>
                  <p className="text-[12px] text-[var(--text-secondary)] mt-1">
                    {t.orgSetup.trySecretaryDesc}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8">
          {stepIndex > 0 && currentStep !== "complete" ? (
            <button
              onClick={prev}
              className="flex items-center gap-1 px-4 py-2 rounded-md text-[13px] text-[var(--text-primary)] border border-[var(--border)] hover:bg-[var(--bg-hover)]"
            >
              <ChevronLeft size={16} />
              {t.common.back}
            </button>
          ) : (
            <div />
          )}

          {currentStep === "complete" ? (
            <button
              onClick={finishSetup}
              className="flex items-center gap-2 px-6 py-2.5 rounded-md text-[13px] font-medium text-white"
              style={{ background: "var(--gradient-primary)" }}
            >
              <Sparkles size={16} />
              {t.setup.complete.goToDashboard}
            </button>
          ) : (
            <button
              onClick={() => {
                if (currentStep === "business_interview") {
                  handlePreview()
                }
                next()
              }}
              className="flex items-center gap-1 px-6 py-2.5 rounded-md text-[13px] font-medium text-white"
              style={{ background: "var(--gradient-primary)" }}
            >
              {t.common.next}
              <ChevronRight size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
