import { useState, useEffect, useRef } from "react"
import {
  MessageSquare,
  Send,
  Loader2,
  Plus,
  Sparkles,
  GitCompare,
  Users,
  Settings,
  Type,
  ChevronDown,
  X,
} from "lucide-react"
import { api } from "@/shared/api/client"
import { useT } from "@/shared/i18n"

interface BrainstormSession {
  id: string
  title: string
  topic: string | null
  session_type: string
  model_ids: string[] | null
  status: string
  message_count: number
  total_chars: number
  is_multi_model: boolean
  created_at: string
}

interface Message {
  role: string
  content: string
  char_count?: number
  timestamp: number
  metadata?: Record<string, unknown>
}

interface ComparisonResult {
  id: string
  input_text: string
  input_char_count: number
  models_requested: string[]
  responses: Record<string, {
    text: string
    tokens: number
    latency_ms: number
    char_count: number
    char_analysis: Record<string, number>
    error: string | null
  }> | null
  status: string
}

interface TextAnalysis {
  analysis: {
    total: number
    total_excluding_spaces: number
    hiragana: number
    katakana: number
    kanji: number
    ascii: number
    digits: number
    spaces: number
    newlines: number
    other: number
    words_estimate: number
  }
}

interface RoleModelConfig {
  id: string
  role_name: string
  model_id: string
  fallback_model_id: string | null
  max_tokens: number | null
  temperature: number | null
  is_active: boolean
}

interface AvailableRole {
  role_key: string
  name: string
  title: string
  description: string
  is_preset: boolean
}

const SESSION_TYPES = [
  { key: "brainstorm", labelKey: "typeBrainstorm" as const },
  { key: "debate", labelKey: "typeDebate" as const },
  { key: "review", labelKey: "typeReview" as const },
  { key: "ideation", labelKey: "typeIdeation" as const },
  { key: "strategy", labelKey: "typeStrategy" as const },
]

const PRESET_MODELS = [
  "anthropic/claude-opus",
  "anthropic/claude-sonnet",
  "openai/gpt",
  "openai/gpt-mini",
  "google/gemini-pro",
  "google/gemini-flash",
  "deepseek/deepseek-chat",
]

export default function BrainstormPage() {
  const companyId = localStorage.getItem("company_id") || "default"
  const t = useT()

  const [activeTab, setActiveTab] = useState<"brainstorm" | "compare" | "roles" | "agents">("brainstorm")

  // Brainstorm state
  const [sessions, setSessions] = useState<BrainstormSession[]>([])
  const [currentSession, setCurrentSession] = useState<BrainstormSession | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [showNewSession, setShowNewSession] = useState(false)
  const [newTitle, setNewTitle] = useState("")
  const [newTopic, setNewTopic] = useState("")
  const [newType, setNewType] = useState("brainstorm")
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [isMultiModel, setIsMultiModel] = useState(false)
  const [customModelInput, setCustomModelInput] = useState("")

  // Compare state
  const [compareInput, setCompareInput] = useState("")
  const [compareModels, setCompareModels] = useState<string[]>([])
  const [compareResult, setCompareResult] = useState<ComparisonResult | null>(null)
  const [comparing, setComparing] = useState(false)
  const [compareCustomModel, setCompareCustomModel] = useState("")

  // Text analysis
  const [textAnalysis, setTextAnalysis] = useState<TextAnalysis | null>(null)

  // Role model configs
  const [roleModels, setRoleModels] = useState<RoleModelConfig[]>([])
  const [availableRoles, setAvailableRoles] = useState<AvailableRole[]>([])

  // Agent management
  const [featureRequest, setFeatureRequest] = useState("")

  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions()
    loadRoleModels()
    loadAvailableRoles()
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function loadSessions() {
    try {
      const data = await api.get<BrainstormSession[]>(`/companies/${companyId}/brainstorm/sessions`)
      setSessions(data)
    } catch { setSessions([]) }
  }

  async function loadRoleModels() {
    try {
      const data = await api.get<RoleModelConfig[]>(`/companies/${companyId}/role-models`)
      setRoleModels(data)
    } catch { setRoleModels([]) }
  }

  async function loadAvailableRoles() {
    try {
      const data = await api.get<AvailableRole[]>(`/companies/${companyId}/available-roles`)
      setAvailableRoles(data)
    } catch { setAvailableRoles([]) }
  }

  async function createSession() {
    try {
      const data = await api.post<BrainstormSession>(`/companies/${companyId}/brainstorm`, {
        title: newTitle || undefined,
        topic: newTopic || undefined,
        session_type: newType,
        model_ids: selectedModels.length > 0 ? selectedModels : undefined,
        is_multi_model: isMultiModel,
      })
      setSessions([data, ...sessions])
      setCurrentSession(data)
      setMessages([])
      setShowNewSession(false)
      setNewTitle("")
      setNewTopic("")
    } catch (e) { console.error("Failed to create session:", e) }
  }

  async function loadSessionMessages(sessionId: string) {
    try {
      const data = await api.get<{ conversation_history: { messages: Message[] } | null }>(`/brainstorm/${sessionId}`)
      setMessages(data.conversation_history?.messages || [])
    } catch { setMessages([]) }
  }

  async function sendMessage() {
    if (!input.trim() || !currentSession) return
    setLoading(true)
    try {
      const data = await api.post<{ latest_messages: Message[]; message_count: number; total_chars: number }>(
        `/brainstorm/${currentSession.id}/message`, { role: "user", content: input }
      )
      setInput("")
      await loadSessionMessages(currentSession.id)
      if (data.message_count !== undefined) {
        setCurrentSession(prev => prev ? { ...prev, message_count: data.message_count, total_chars: data.total_chars } : null)
      }
      analyzeText(input)
    } catch (e) { console.error("Failed to send message:", e) }
    finally { setLoading(false) }
  }

  async function analyzeText(text: string) {
    try {
      const data = await api.post<TextAnalysis>("/text/analyze", { text })
      setTextAnalysis(data)
    } catch { /* ignore */ }
  }

  async function runMultiModelComparison() {
    if (!compareInput.trim() || compareModels.length < 2) return
    setComparing(true)
    try {
      const data = await api.post<ComparisonResult>(`/companies/${companyId}/multi-model/compare`, {
        input_text: compareInput, model_ids: compareModels,
      })
      setCompareResult(data)
    } catch (e) { console.error("Failed to compare:", e) }
    finally { setComparing(false) }
  }

  async function submitFeatureRequest() {
    if (!featureRequest.trim()) return
    try {
      await api.post(`/companies/${companyId}/feature-requests`, { request_text: featureRequest, auto_execute: true })
      setFeatureRequest("")
      loadAvailableRoles()
    } catch (e) { console.error("Failed to submit request:", e) }
  }

  async function addAgentByRole(role: string) {
    try { await api.post(`/companies/${companyId}/agents/by-role`, { role }) }
    catch (e) { console.error("Failed to add agent:", e) }
  }

  function addCustomModel(modelId: string, target: "session" | "compare") {
    const trimmed = modelId.trim()
    if (!trimmed) return
    if (target === "session") {
      if (!selectedModels.includes(trimmed)) setSelectedModels([...selectedModels, trimmed])
      setCustomModelInput("")
    } else {
      if (!compareModels.includes(trimmed)) setCompareModels([...compareModels, trimmed])
      setCompareCustomModel("")
    }
  }

  function toggleModel(modelId: string, target: "session" | "compare") {
    if (target === "session") {
      setSelectedModels(prev => prev.includes(modelId) ? prev.filter(m => m !== modelId) : [...prev, modelId])
    } else {
      setCompareModels(prev => prev.includes(modelId) ? prev.filter(m => m !== modelId) : [...prev, modelId])
    }
  }

  const tabs = [
    { key: "brainstorm" as const, icon: MessageSquare, label: t.brainstorm.tabBrainstorm },
    { key: "compare" as const, icon: GitCompare, label: t.brainstorm.tabCompare },
    { key: "roles" as const, icon: Settings, label: t.brainstorm.tabRoles },
    { key: "agents" as const, icon: Users, label: t.brainstorm.tabAgents },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1100px] mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-5">
          <MessageSquare size={16} className="text-[var(--accent)]" />
          <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.brainstorm.title}</h2>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-5 border-b border-[var(--border)]">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="flex items-center gap-1.5 px-4 py-2 text-[12px] transition-colors"
              style={{
                color: activeTab === tab.key ? "var(--text-primary)" : "var(--text-muted)",
                borderBottom: activeTab === tab.key ? "2px solid var(--accent)" : "2px solid transparent",
              }}
            >
              <tab.icon size={14} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Brainstorm Tab */}
        {activeTab === "brainstorm" && (
          <div className="flex gap-4" style={{ minHeight: 500 }}>
            {/* Session list */}
            <div className="w-[260px] shrink-0 flex flex-col gap-2">
              <button
                onClick={() => setShowNewSession(true)}
                className="w-full px-3 py-2 rounded text-[12px] border border-dashed border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent)] hover:text-[var(--text-primary)] flex items-center justify-center gap-1.5 transition-colors"
              >
                <Plus size={14} /> {t.brainstorm.newSession}
              </button>

              {showNewSession && (
                <div className="p-3 border border-[var(--border)] rounded bg-[var(--bg-surface)]">
                  <input value={newTitle} onChange={e => setNewTitle(e.target.value)} placeholder={t.brainstorm.sessionTitle}
                    className="w-full px-3 py-1.5 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] mb-2" />
                  <textarea value={newTopic} onChange={e => setNewTopic(e.target.value)} placeholder={t.brainstorm.sessionTopic} rows={2}
                    className="w-full px-3 py-1.5 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] resize-none mb-2" />
                  <select value={newType} onChange={e => setNewType(e.target.value)}
                    className="w-full px-3 py-1.5 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] mb-2">
                    {SESSION_TYPES.map(st => <option key={st.key} value={st.key}>{t.brainstorm[st.labelKey]}</option>)}
                  </select>
                  <label className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)] mb-2 cursor-pointer">
                    <input type="checkbox" checked={isMultiModel} onChange={e => setIsMultiModel(e.target.checked)}
                      className="accent-[var(--accent)]" />
                    {t.brainstorm.multiModel}
                  </label>
                  {isMultiModel && (
                    <ModelSelector models={selectedModels} onToggle={m => toggleModel(m, "session")}
                      customValue={customModelInput} onCustomChange={setCustomModelInput}
                      onCustomAdd={() => addCustomModel(customModelInput, "session")} t={t} />
                  )}
                  <div className="flex gap-2 mt-2">
                    <button onClick={createSession}
                      className="flex-1 px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-white">{t.common.create}</button>
                    <button onClick={() => setShowNewSession(false)}
                      className="px-3 py-1.5 rounded text-[12px] text-[var(--text-muted)] border border-[var(--border)]">{t.common.cancel}</button>
                  </div>
                </div>
              )}

              {sessions.map(s => (
                <button key={s.id} onClick={() => { setCurrentSession(s); loadSessionMessages(s.id) }}
                  className="px-3 py-2.5 rounded text-left border transition-colors"
                  style={{
                    borderColor: currentSession?.id === s.id ? "var(--accent)" : "var(--border)",
                    background: currentSession?.id === s.id ? "var(--bg-active)" : "var(--bg-surface)",
                  }}>
                  <div className="text-[13px] font-medium text-[var(--text-primary)] truncate">{s.title || t.brainstorm.untitled}</div>
                  <div className="text-[11px] text-[var(--text-muted)] mt-0.5">
                    {s.session_type} · {s.message_count} msg · {s.total_chars.toLocaleString()} chars
                  </div>
                </button>
              ))}
            </div>

            {/* Chat area */}
            <div className="flex-1 flex flex-col">
              {currentSession ? (
                <>
                  <div className="px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border)] rounded mb-3">
                    <span className="text-[13px] font-medium text-[var(--text-primary)]">{currentSession.title}</span>
                    {currentSession.is_multi_model && (
                      <span className="ml-2 px-2 py-0.5 text-[10px] rounded bg-[var(--accent)] text-white">{t.brainstorm.multiModel}</span>
                    )}
                  </div>

                  <div className="flex-1 overflow-auto border border-[var(--border)] rounded p-4 mb-3 bg-[var(--bg-base)]" style={{ minHeight: 300 }}>
                    {messages.map((msg, i) => (
                      <div key={i} className="mb-3 flex flex-col" style={{ alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
                        <div className="text-[10px] text-[var(--text-muted)] mb-1">
                          {msg.role.startsWith("model:") ? msg.role.replace("model:", "") : msg.role}
                        </div>
                        <div className="px-3 py-2 rounded-lg max-w-[80%] text-[13px] whitespace-pre-wrap"
                          style={{
                            background: msg.role === "user" ? "var(--accent)" : "var(--bg-surface)",
                            color: msg.role === "user" ? "#fff" : "var(--text-primary)",
                          }}>
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>

                  {textAnalysis && (
                    <div className="flex gap-3 text-[11px] text-[var(--text-muted)] mb-2 flex-wrap">
                      <span><Type size={11} className="inline" /> {textAnalysis.analysis.total}</span>
                      <span>{t.brainstorm.kanji}: {textAnalysis.analysis.kanji}</span>
                      <span>{t.brainstorm.hiragana}: {textAnalysis.analysis.hiragana}</span>
                      <span>{t.brainstorm.katakana}: {textAnalysis.analysis.katakana}</span>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <textarea value={input}
                      onChange={e => { setInput(e.target.value); if (e.target.value.length > 0) analyzeText(e.target.value) }}
                      onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
                      placeholder={t.brainstorm.inputPlaceholder} rows={3}
                      className="flex-1 px-3 py-2 rounded text-[13px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] resize-none" />
                    <button onClick={sendMessage} disabled={loading || !input.trim()}
                      className="px-4 rounded bg-[var(--accent)] text-white disabled:opacity-40 flex items-center">
                      {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-[var(--text-muted)]">
                  <MessageSquare size={40} className="mb-3 opacity-40" />
                  <p className="text-[12px]">{t.brainstorm.selectOrCreate}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Compare Tab */}
        {activeTab === "compare" && (
          <div>
            <p className="text-[12px] text-[var(--text-muted)] mb-4">{t.brainstorm.compareDesc}</p>

            <div className="mb-4">
              <label className="text-[12px] text-[var(--text-secondary)] block mb-2">{t.brainstorm.selectModels}</label>
              <ModelSelector models={compareModels} onToggle={m => toggleModel(m, "compare")}
                customValue={compareCustomModel} onCustomChange={setCompareCustomModel}
                onCustomAdd={() => addCustomModel(compareCustomModel, "compare")} t={t} />
            </div>

            <textarea value={compareInput} onChange={e => setCompareInput(e.target.value)}
              placeholder={t.brainstorm.compareInputPlaceholder} rows={5}
              className="w-full px-3 py-2 rounded text-[13px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] resize-none mb-3" />

            <div className="flex gap-3 items-center mb-6">
              <button onClick={runMultiModelComparison} disabled={comparing || compareModels.length < 2 || !compareInput.trim()}
                className="flex items-center gap-1.5 px-4 py-2 rounded text-[12px] bg-[var(--accent)] text-white disabled:opacity-40">
                {comparing ? <Loader2 size={14} className="animate-spin" /> : <GitCompare size={14} />}
                {t.brainstorm.runCompare}
              </button>
              <span className="text-[11px] text-[var(--text-muted)]">{compareInput.length.toLocaleString()} chars</span>
            </div>

            {compareResult?.responses && (
              <div>
                <div className="text-[11px] text-[var(--text-muted)] mb-3">
                  {t.brainstorm.compareStatus}: {compareResult.status}
                </div>
                <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${Math.min(Object.keys(compareResult.responses).length, 3)}, 1fr)` }}>
                  {Object.entries(compareResult.responses).map(([modelId, resp]) => (
                    <div key={modelId} className="border border-[var(--border)] rounded p-3 bg-[var(--bg-surface)]">
                      <div className="text-[13px] font-mono font-medium text-[var(--info)] mb-2">{modelId.split("/")[1] || modelId}</div>
                      {resp.error ? (
                        <div className="text-[12px] text-[var(--error)]">{resp.error}</div>
                      ) : (
                        <>
                          <div className="text-[13px] text-[var(--text-primary)] whitespace-pre-wrap mb-2 max-h-[300px] overflow-auto">{resp.text}</div>
                          <div className="text-[11px] text-[var(--text-muted)] border-t border-[var(--border)] pt-2">
                            {resp.char_count.toLocaleString()} chars · {resp.tokens} tokens · {resp.latency_ms}ms
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Roles Tab */}
        {activeTab === "roles" && (
          <div>
            <p className="text-[12px] text-[var(--text-muted)] mb-4">{t.brainstorm.rolesDesc}</p>

            {roleModels.length > 0 ? (
              <div className="border border-[var(--border)] rounded overflow-hidden mb-6">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="bg-[var(--bg-surface)] border-b border-[var(--border)]">
                      <th className="text-left px-3 py-2 text-[var(--text-secondary)] font-medium">{t.brainstorm.role}</th>
                      <th className="text-left px-3 py-2 text-[var(--text-secondary)] font-medium">{t.brainstorm.model}</th>
                      <th className="text-left px-3 py-2 text-[var(--text-secondary)] font-medium">{t.brainstorm.fallback}</th>
                      <th className="text-left px-3 py-2 text-[var(--text-secondary)] font-medium">{t.brainstorm.status}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {roleModels.map(rm => (
                      <tr key={rm.id} className="border-b border-[var(--border)]">
                        <td className="px-3 py-2 text-[var(--text-primary)]">{rm.role_name}</td>
                        <td className="px-3 py-2 font-mono text-[var(--info)]">{rm.model_id}</td>
                        <td className="px-3 py-2 font-mono text-[var(--text-muted)]">{rm.fallback_model_id || "-"}</td>
                        <td className="px-3 py-2">
                          <span className="text-[10px] px-1.5 py-0.5 rounded" style={{
                            background: rm.is_active ? "#16825d30" : "#f4474730",
                            color: rm.is_active ? "var(--success-fg)" : "var(--error)",
                          }}>{rm.is_active ? t.brainstorm.enabled : t.brainstorm.disabled}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="rounded px-4 py-8 text-center text-[12px] border border-[var(--border)] text-[var(--text-muted)] mb-6">
                {t.brainstorm.noRoleModels}
              </div>
            )}

            <h3 className="text-[13px] font-medium text-[var(--text-primary)] mb-3">{t.brainstorm.availableRoles}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {availableRoles.map(r => (
                <div key={r.role_key} className="p-3 border border-[var(--border)] rounded bg-[var(--bg-surface)]">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[13px] font-medium text-[var(--text-primary)]">{r.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded" style={{
                      background: r.is_preset ? "var(--accent)" + "20" : "#dcdcaa20",
                      color: r.is_preset ? "var(--accent)" : "var(--warning)",
                    }}>{r.is_preset ? t.brainstorm.preset : t.brainstorm.custom}</span>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] mb-2">{r.description.slice(0, 120)}{r.description.length > 120 ? "..." : ""}</div>
                  <button onClick={() => addAgentByRole(r.role_key)}
                    className="flex items-center gap-1 text-[11px] px-2 py-1 rounded border border-[var(--accent)] text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white transition-colors">
                    <Plus size={12} /> {t.brainstorm.addAgent}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agents Tab */}
        {activeTab === "agents" && (
          <div>
            <p className="text-[12px] text-[var(--text-muted)] mb-4">{t.brainstorm.agentsDesc}</p>

            <div className="p-4 bg-[var(--bg-surface)] border border-[var(--border)] rounded mb-6">
              <label className="flex items-center gap-1.5 text-[12px] font-medium text-[var(--text-primary)] mb-2">
                <Sparkles size={14} className="text-[var(--accent)]" />
                {t.brainstorm.orgRequest}
              </label>
              <textarea value={featureRequest} onChange={e => setFeatureRequest(e.target.value)}
                placeholder={t.brainstorm.orgRequestPlaceholder} rows={3}
                className="w-full px-3 py-2 rounded text-[13px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] resize-none mb-3" />
              <button onClick={submitFeatureRequest} disabled={!featureRequest.trim()}
                className="flex items-center gap-1.5 px-4 py-2 rounded text-[12px] bg-[var(--accent)] text-white disabled:opacity-40">
                <Send size={14} /> {t.brainstorm.submitRequest}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 border border-[var(--border)] rounded bg-[var(--bg-surface)]">
                <h3 className="text-[13px] font-medium text-[var(--text-primary)] mb-2">{t.brainstorm.secretaryRole}</h3>
                <p className="text-[12px] text-[var(--text-secondary)]">{t.brainstorm.secretaryDesc}</p>
              </div>
              <div className="p-3 border border-[var(--border)] rounded bg-[var(--bg-surface)]">
                <h3 className="text-[13px] font-medium text-[var(--text-primary)] mb-2">{t.brainstorm.consultantRole}</h3>
                <p className="text-[12px] text-[var(--text-secondary)]">{t.brainstorm.consultantDesc}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/** Reusable model selector with presets + custom input */
function ModelSelector({ models, onToggle, customValue, onCustomChange, onCustomAdd, t }: {
  models: string[]
  onToggle: (m: string) => void
  customValue: string
  onCustomChange: (v: string) => void
  onCustomAdd: () => void
  t: ReturnType<typeof useT>
}) {
  const [open, setOpen] = useState(false)

  return (
    <div>
      {/* Selected models display */}
      <div className="flex flex-wrap gap-1.5 mb-2">
        {models.map(m => (
          <span key={m} className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-[var(--bg-active)] text-[var(--text-primary)] border border-[var(--border)]">
            {m.split("/").pop()}
            <button onClick={() => onToggle(m)} className="text-[var(--text-muted)] hover:text-[var(--error)]"><X size={10} /></button>
          </span>
        ))}
      </div>

      {/* Dropdown toggle */}
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)] transition-colors w-full justify-between">
        <span>{t.brainstorm.selectModelsBtn}</span>
        <ChevronDown size={14} style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 150ms" }} />
      </button>

      {open && (
        <div className="mt-1 border border-[var(--border)] rounded bg-[var(--bg-surface)] p-2 max-h-[200px] overflow-auto">
          {PRESET_MODELS.map(m => (
            <label key={m} className="flex items-center gap-2 px-2 py-1.5 rounded text-[12px] cursor-pointer hover:bg-[var(--bg-hover)] text-[var(--text-primary)]">
              <input type="checkbox" checked={models.includes(m)} onChange={() => onToggle(m)} className="accent-[var(--accent)]" />
              <span className="font-mono">{m}</span>
            </label>
          ))}
          {/* Custom model input */}
          <div className="flex gap-1.5 mt-2 pt-2 border-t border-[var(--border)]">
            <input value={customValue} onChange={e => onCustomChange(e.target.value)}
              placeholder={t.brainstorm.customModelPlaceholder}
              onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); onCustomAdd() } }}
              className="flex-1 px-2 py-1 rounded text-[11px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] font-mono" />
            <button onClick={onCustomAdd} disabled={!customValue.trim()}
              className="px-2 py-1 rounded text-[11px] bg-[var(--accent)] text-white disabled:opacity-40">
              <Plus size={12} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
