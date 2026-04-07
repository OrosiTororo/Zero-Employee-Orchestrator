import { useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  Wand2,
  CheckCircle,
  AlertTriangle,
  ArrowLeft,
  Save,
} from "lucide-react"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

interface GenerateResult {
  skill_json: Record<string, unknown>
  code: string
  safety_report: {
    has_dangerous_code: boolean
    has_external_communication: boolean
    has_credential_access: boolean
    has_destructive_operations: boolean
    risk_level: string
    summary: string
  }
  safety_passed: boolean
  safety_issues: string[]
  registered: boolean
  skill_id: string | null
}

export function SkillCreatePage() {
  const [description, setDescription] = useState("")
  const [result, setResult] = useState<GenerateResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [registering, setRegistering] = useState(false)
  const navigate = useNavigate()
  const t = useT()

  const handleGenerate = async () => {
    if (!description.trim() || loading) return
    setLoading(true)
    setResult(null)
    try {
      const data = await api.post<GenerateResult>("/registry/skills/generate", {
        description: description.trim(),
        language: "ja",
        auto_register: false,
      })
      setResult(data)
    } catch (e: unknown) {
      alert(`${t.skillCreate?.generateFailed ?? "Skill generation failed"}: ${e instanceof Error ? e.message : String(e) || String(e)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!result || !result.safety_passed || registering) return
    setRegistering(true)
    try {
      const data = await api.post<GenerateResult>("/registry/skills/generate", {
        description: description.trim(),
        language: "ja",
        auto_register: true,
      })
      setResult(data)
      if (data.registered) {
        navigate("/skills")
      }
    } catch (e: unknown) {
      alert(`${t.skillCreate?.registerFailed ?? "Skill registration failed"}: ${e instanceof Error ? e.message : String(e) || String(e)}`)
    } finally {
      setRegistering(false)
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={() => navigate("/skills")}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            <ArrowLeft size={16} />
          </button>
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">
            {t.nav.skillCreate}
          </h2>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent)]/20 text-[var(--accent)]">
            {t.skillCreate?.naturalLanguageGen ?? "Natural Language Generation"}
          </span>
        </div>

        <p className="text-[12px] mb-4 text-[var(--text-muted)]">
          {t.skillCreate?.description ?? "Describe the skill's functionality in natural language. AI will automatically generate the skill manifest and execution code. Generated code can be registered after passing safety checks."}
        </p>

        {/* Input */}
        <div className="rounded overflow-hidden mb-4 border border-[var(--border)] bg-[var(--bg-surface)]">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={
              t.skillCreate?.placeholder ??
              "Examples:\n" +
              "- A skill that periodically scrapes competitor websites and reports price changes\n" +
              "- A skill that converts Markdown files to HTML and auto-generates a table of contents\n" +
              "- A skill that performs sentiment analysis on text and classifies it as positive/negative/neutral"
            }
            className="w-full resize-none px-4 py-3 text-[13px] outline-none bg-transparent text-[var(--text-primary)]"
            style={{ minHeight: "120px" }}
            rows={5}
          />
          <div className="flex items-center justify-between px-4 py-2 border-t border-[var(--border)]">
            <span className="text-[11px] text-[var(--text-muted)]">
              {description.length}/5000 {t.skillCreate?.characters ?? "chars"}
            </span>
            <button
              onClick={handleGenerate}
              disabled={!description.trim() || description.trim().length < 10 || loading}
              className="flex items-center gap-2 px-4 py-2 rounded text-[12px]"
              style={{
                background:
                  description.trim().length >= 10 && !loading
                    ? "var(--accent)"
                    : "var(--border)",
                color: "var(--bg-base)",
              }}
            >
              <Wand2 size={14} />
              {loading
                ? (t.skillCreate?.generating ?? "Generating...")
                : (t.skillCreate?.generateSkill ?? "Generate Skill")}
            </button>
          </div>
        </div>

        {/* Result */}
        {result && (
          <div className="flex flex-col gap-4">
            {/* Safety Check */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {result.safety_passed ? (
                  <>
                    <CheckCircle size={14} className="text-[var(--success-fg)]" />
                    <span className="text-[12px] text-[var(--success-fg)]">
                      {t.skillCreate?.safetyPassed ?? "Safety check passed"}
                    </span>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={14} className="text-[var(--error)]" />
                    <span className="text-[12px] text-[var(--error)]">
                      {t.skillCreate?.safetyIssuesDetected ?? "Safety issues detected"}
                    </span>
                  </>
                )}
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    background:
                      result.safety_report.risk_level === "low"
                        ? "color-mix(in srgb, var(--success-fg) 12%, transparent)"
                        : result.safety_report.risk_level === "medium"
                          ? "color-mix(in srgb, var(--warning-fg) 12%, transparent)"
                          : "color-mix(in srgb, var(--error) 12%, transparent)",
                    color:
                      result.safety_report.risk_level === "low"
                        ? "var(--success-fg)"
                        : result.safety_report.risk_level === "medium"
                          ? "var(--warning-fg)"
                          : "var(--error)",
                  }}
                >
                  {t.skillCreate?.risk ?? "Risk"}: {result.safety_report.risk_level}
                </span>
              </div>

              {result.safety_passed && !result.registered && (
                <button
                  onClick={handleRegister}
                  disabled={registering}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[var(--success-fg)] text-[var(--bg-base)]"
                >
                  <Save size={12} />
                  {registering
                    ? (t.skillCreate?.registering ?? "Registering...")
                    : (t.skillCreate?.registerSkill ?? "Register Skill")}
                </button>
              )}
              {result.registered && (
                <span className="text-[11px] px-1.5 py-0.5 rounded bg-[color-mix(in_srgb,var(--success-fg)_20%,transparent)] text-[var(--success-fg)]">
                  {t.skillCreate?.registered ?? "Registered"}
                </span>
              )}
            </div>

            {/* Safety Issues */}
            {result.safety_issues.length > 0 && (
              <div className="rounded p-3 bg-[color-mix(in_srgb,var(--error)_20%,transparent)] border border-[var(--error)]">
                {result.safety_issues.map((issue: string, i: number) => (
                  <div key={i} className="text-[12px] text-[var(--error)]">
                    - {issue}
                  </div>
                ))}
              </div>
            )}

            {/* Safety Report */}
            <div className="rounded p-3 border border-[var(--border)] bg-[var(--bg-surface)]">
              <div className="text-[11px] uppercase tracking-wider mb-2 text-[var(--text-muted)]">
                {t.skillCreate?.safetyReport ?? "Safety Report"}
              </div>
              <div className="text-[12px] text-[var(--text-muted)]">
                {result.safety_report.summary}
              </div>
            </div>

            {/* Skill JSON */}
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1 text-[var(--text-muted)]">
                SKILL.json
              </div>
              <pre className="rounded p-3 text-[12px] overflow-auto border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--accent-secondary)]">
                {JSON.stringify(result.skill_json, null, 2)}
              </pre>
            </div>

            {/* Executor Code */}
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1 text-[var(--text-muted)]">
                executor.py
              </div>
              <pre className="rounded p-3 text-[12px] overflow-auto border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-primary)] max-h-[400px]">
                {result.code}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
