import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import {
  ChevronRight,
  ChevronLeft,
  Building2,
  Bot,
  Key,
  Sparkles,
  Check,
  Globe,
  Info,
  CheckCircle,
} from "lucide-react"
import { Logo } from "@/shared/ui/Logo"
import { useT, useI18n, LOCALE_LABELS, type Locale } from "@/shared/i18n"

type Step =
  | "language"
  | "welcome"
  | "organization"
  | "provider"
  | "first_agent"
  | "complete"

const STEP_IDS: Step[] = [
  "language",
  "welcome",
  "organization",
  "provider",
  "first_agent",
  "complete",
]

const LOCALE_FLAGS: Record<Locale, string> = {
  ja: "🇯🇵",
  en: "🇬🇧",
}

export function SetupPage() {
  const navigate = useNavigate()
  const t = useT()
  const { locale, setLocale } = useI18n()

  const [currentStep, setCurrentStep] = useState<Step>("language")
  const [orgName, setOrgName] = useState("")
  const [orgMission, setOrgMission] = useState("")
  const [providerType, setProviderType] = useState("openrouter")
  const [executionMode, setExecutionMode] = useState("quality")
  const [firstAgentName, setFirstAgentName] = useState(t.setup.agent.defaultName)
  const prevDefaultName = useRef(t.setup.agent.defaultName)

  useEffect(() => {
    const newDefault = t.setup.agent.defaultName
    if (prevDefaultName.current !== newDefault && firstAgentName === prevDefaultName.current) {
      setFirstAgentName(newDefault)
    }
    prevDefaultName.current = newDefault
  }, [t.setup.agent.defaultName, firstAgentName])

  const stepLabels: Record<Step, string> = {
    language: t.setup.steps.language,
    welcome: t.setup.steps.welcome,
    organization: t.setup.steps.organization,
    provider: t.setup.steps.provider,
    first_agent: t.setup.steps.firstAgent,
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

  const finishSetup = () => {
    // TODO: Save settings via API
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
                  className="w-8 h-[2px] transition-colors"
                  style={{
                    background: i < stepIndex ? "var(--accent)" : "var(--border)",
                  }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="min-h-[300px]">
          {/* Language Step */}
          {currentStep === "language" && (
            <div className="flex flex-col items-center gap-6 text-center">
              <Globe size={48} className="text-[var(--accent)]" />
              <h2 className="text-2xl font-semibold text-[var(--text-primary)]">
                {t.setup.language.title}
              </h2>
              <p className="text-[14px] text-[var(--text-secondary)] leading-relaxed max-w-[450px]">
                {t.setup.language.description}
              </p>
              <div className="flex gap-6 mt-2">
                {(Object.keys(LOCALE_LABELS) as Locale[]).map((loc) => (
                  <button
                    key={loc}
                    onClick={() => setLocale(loc)}
                    className="relative flex flex-col items-center gap-3 px-8 py-6 rounded-md border-2 transition-colors cursor-pointer"
                    style={{
                      background:
                        locale === loc
                          ? "rgba(0, 120, 212, 0.08)"
                          : "var(--bg-surface)",
                      borderColor:
                        locale === loc ? "var(--accent)" : "var(--border)",
                    }}
                  >
                    <span className="text-4xl">{LOCALE_FLAGS[loc]}</span>
                    <span className="text-[14px] font-medium text-[var(--text-primary)]">
                      {LOCALE_LABELS[loc]}
                    </span>
                    {locale === loc && (
                      <CheckCircle
                        size={20}
                        className="absolute top-2 right-2"
                        style={{ color: "var(--accent)" }}
                      />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

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
                      background:
                        providerType === p.id
                          ? "rgba(0, 120, 212, 0.08)"
                          : "transparent",
                      borderColor:
                        providerType === p.id
                          ? "var(--accent)"
                          : "var(--border)",
                    }}
                  >
                    <div
                      className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                      style={{
                        borderColor:
                          providerType === p.id
                            ? "var(--accent)"
                            : "var(--text-muted)",
                      }}
                    >
                      {providerType === p.id && (
                        <div className="w-2 h-2 rounded-full bg-[var(--accent)]" />
                      )}
                    </div>
                    <div>
                      <div className="text-[13px] text-[var(--text-primary)] font-medium">
                        {p.name}
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)]">
                        {p.desc}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex flex-col gap-3 mt-2">
                <span className="text-[12px] text-[var(--text-secondary)]">
                  {t.setup.provider.executionMode}
                </span>
                <div className="flex gap-2">
                  {executionModes.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setExecutionMode(m.id)}
                      className="flex-1 px-3 py-2 rounded-md text-[12px] border transition-colors"
                      style={{
                        background:
                          executionMode === m.id
                            ? "rgba(0, 120, 212, 0.12)"
                            : "transparent",
                        borderColor:
                          executionMode === m.id
                            ? "var(--accent)"
                            : "var(--border)",
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

          {/* First Agent Step */}
          {currentStep === "first_agent" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-3">
                <Bot size={24} className="text-[var(--accent)]" />
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                  {t.setup.agent.title}
                </h2>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)]">
                {t.setup.agent.description}
              </p>
              <div>
                <label className="text-[12px] text-[var(--text-secondary)] mb-1 block">
                  {t.setup.agent.agentName}
                </label>
                <input
                  value={firstAgentName}
                  onChange={(e) => setFirstAgentName(e.target.value)}
                  placeholder={t.setup.agent.agentNamePlaceholder}
                  className="w-full px-3 py-2.5 rounded-md text-[13px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none"
                />
              </div>
              <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-md p-4 text-[12px] text-[var(--text-secondary)] space-y-2">
                <p className="text-[var(--text-primary)] font-medium">
                  {t.setup.agent.capabilities}
                </p>
                <ul className="list-disc list-inside space-y-1">
                  <li>{t.setup.agent.cap1}</li>
                  <li>{t.setup.agent.cap2}</li>
                  <li>{t.setup.agent.cap3}</li>
                  <li>{t.setup.agent.cap4}</li>
                  <li>{t.setup.agent.cap5}</li>
                </ul>
                <p className="text-[var(--text-muted)] mt-2">
                  {t.setup.agent.safetyNote}
                </p>
              </div>
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
                <p className="text-[var(--text-primary)] font-medium mb-2">
                  {t.setup.complete.tryTitle}
                </p>
                <ul className="space-y-2">
                  <li>{t.setup.complete.try1}</li>
                  <li>{t.setup.complete.try2}</li>
                  <li>{t.setup.complete.try3}</li>
                </ul>
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
              style={{
                background: "linear-gradient(135deg, #0078d4, #6d28d9)",
              }}
            >
              <Sparkles size={16} />
              {t.setup.complete.goToDashboard}
            </button>
          ) : (
            <button
              onClick={next}
              className="flex items-center gap-1 px-6 py-2.5 rounded-md text-[13px] font-medium text-white"
              style={{
                background: "linear-gradient(135deg, #0078d4, #6d28d9)",
              }}
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
