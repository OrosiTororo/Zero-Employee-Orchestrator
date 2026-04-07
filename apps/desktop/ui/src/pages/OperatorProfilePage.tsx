import { useState, useEffect, useCallback } from "react"
import { UserCircle, Save, Loader2, FileText } from "lucide-react"
import { api } from "@/shared/api/client"
import { useToastStore } from "@/shared/ui/ErrorToast"

interface Profile {
  display_name: string
  role: string
  team: string
  industry: string
  responsibilities: string[]
  current_priorities: string[]
  work_style: string
  preferred_language: string
  timezone: string
}

interface Instructions {
  instructions: string
}

export function OperatorProfilePage() {
  const addToast = useToastStore((s) => s.addToast)
  const [tab, setTab] = useState<"profile" | "instructions">("profile")
  const [saving, setSaving] = useState(false)

  // Profile state
  const [profile, setProfile] = useState<Profile>({
    display_name: "",
    role: "",
    team: "",
    industry: "",
    responsibilities: [],
    current_priorities: [],
    work_style: "",
    preferred_language: "en",
    timezone: "",
  })

  // Instructions state
  const [instructions, setInstructions] = useState("")

  const loadData = useCallback(async () => {
    try {
      const [p, ins] = await Promise.all([
        api.get<Profile>("/operator-profile/profile").catch(() => null),
        api.get<Instructions>("/operator-profile/instructions").catch(() => null),
      ])
      if (p) setProfile(p)
      if (ins) setInstructions(ins.instructions)
    } catch {
      addToast("Could not load operator profile.")
    }
  }, [addToast])

  useEffect(() => { loadData() }, [loadData])

  const saveProfile = async () => {
    setSaving(true)
    try {
      await api.put("/operator-profile/profile", profile)
      addToast("Profile saved.")
    } catch {
      addToast("Could not save profile.")
    } finally {
      setSaving(false)
    }
  }

  const saveInstructions = async () => {
    setSaving(true)
    try {
      await api.put("/operator-profile/instructions", { instructions })
      addToast("Instructions saved.")
    } catch {
      addToast("Could not save instructions.")
    } finally {
      setSaving(false)
    }
  }

  const updateField = (field: keyof Profile, value: string) => {
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const updateList = (field: "responsibilities" | "current_priorities", value: string) => {
    setProfile((prev) => ({
      ...prev,
      [field]: value.split("\n").filter((l) => l.trim()),
    }))
  }

  const fieldRow = (label: string, field: keyof Profile, placeholder: string) => (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
        {label}
      </label>
      <input
        type="text"
        value={profile[field] as string}
        onChange={(e) => updateField(field, e.target.value)}
        placeholder={placeholder}
        className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-input)] text-[13px] text-[var(--text-primary)] outline-none focus:border-[var(--accent)]"
      />
    </div>
  )

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[700px] mx-auto px-6 py-6 space-y-5">
        {/* Header */}
        <div className="flex items-center gap-2">
          <UserCircle size={20} className="text-[var(--accent)]" />
          <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
            Operator Profile
          </h1>
          <span className="text-[11px] text-[var(--text-muted)] ml-2">
            Tell AI about yourself
          </span>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-[var(--border)]">
          <button
            onClick={() => setTab("profile")}
            className="flex items-center gap-1.5 px-3 py-2 text-[12px] font-medium border-b-2 transition-colors"
            style={{
              borderColor: tab === "profile" ? "var(--accent)" : "transparent",
              color: tab === "profile" ? "var(--text-primary)" : "var(--text-muted)",
            }}
          >
            <UserCircle size={13} /> About Me
          </button>
          <button
            onClick={() => setTab("instructions")}
            className="flex items-center gap-1.5 px-3 py-2 text-[12px] font-medium border-b-2 transition-colors"
            style={{
              borderColor: tab === "instructions" ? "var(--accent)" : "transparent",
              color: tab === "instructions" ? "var(--text-primary)" : "var(--text-muted)",
            }}
          >
            <FileText size={13} /> Global Instructions
          </button>
        </div>

        {/* Profile Tab */}
        {tab === "profile" && (
          <div className="space-y-4">
            <p className="text-[12px] text-[var(--text-secondary)]">
              AI agents read this profile to personalize responses. Fill in what's relevant — everything is optional.
            </p>

            <div className="grid grid-cols-2 gap-4">
              {fieldRow("Display Name", "display_name", "Your name")}
              {fieldRow("Role", "role", "e.g. Product Manager, CTO")}
              {fieldRow("Team", "team", "e.g. Engineering, Marketing")}
              {fieldRow("Industry", "industry", "e.g. SaaS, Healthcare")}
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
                Responsibilities (one per line)
              </label>
              <textarea
                value={profile.responsibilities.join("\n")}
                onChange={(e) => updateList("responsibilities", e.target.value)}
                placeholder={"Sprint planning\nCode reviews\nStakeholder communication"}
                rows={3}
                className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-input)] text-[13px] text-[var(--text-primary)] outline-none focus:border-[var(--accent)] resize-none"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
                Current Priorities (one per line)
              </label>
              <textarea
                value={profile.current_priorities.join("\n")}
                onChange={(e) => updateList("current_priorities", e.target.value)}
                placeholder={"Launch v2.0 by end of month\nReduce support ticket backlog"}
                rows={3}
                className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-input)] text-[13px] text-[var(--text-primary)] outline-none focus:border-[var(--accent)] resize-none"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
                Work Style
              </label>
              <textarea
                value={profile.work_style}
                onChange={(e) => updateField("work_style", e.target.value)}
                placeholder="e.g. I prefer concise answers. I work async and check messages in batches."
                rows={2}
                className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-input)] text-[13px] text-[var(--text-primary)] outline-none focus:border-[var(--accent)] resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              {fieldRow("Preferred Language", "preferred_language", "en")}
              {fieldRow("Timezone", "timezone", "Asia/Tokyo")}
            </div>

            <button
              onClick={saveProfile}
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 rounded text-[12px] font-medium text-white disabled:opacity-40"
              style={{ background: "var(--accent)" }}
            >
              {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
              Save Profile
            </button>
          </div>
        )}

        {/* Instructions Tab */}
        {tab === "instructions" && (
          <div className="space-y-4">
            <p className="text-[12px] text-[var(--text-secondary)]">
              These instructions are injected into every AI conversation. Use them for global preferences, formatting rules, or domain-specific context.
            </p>

            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder={`Example:\n- Always respond in Japanese unless asked otherwise\n- Use bullet points for lists\n- Include source links when citing data\n- Our fiscal year starts in April`}
              rows={12}
              className="w-full px-4 py-3 rounded border border-[var(--border)] bg-[var(--bg-input)] text-[13px] text-[var(--text-primary)] outline-none focus:border-[var(--accent)] resize-none font-mono"
            />

            <button
              onClick={saveInstructions}
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 rounded text-[12px] font-medium text-white disabled:opacity-40"
              style={{ background: "var(--accent)" }}
            >
              {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
              Save Instructions
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
