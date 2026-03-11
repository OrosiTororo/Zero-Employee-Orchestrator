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
  Archive,
  Search,
  Type,
  Trash2,
} from "lucide-react"
import { api } from "@/shared/api/client"

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
  validation?: {
    length: number
    min_required: number
    max_allowed: number | null
    is_valid: boolean
    over_by: number
    under_by: number
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
  { key: "brainstorm", label: "ブレインストーミング", labelEn: "Brainstorm" },
  { key: "debate", label: "ディベート", labelEn: "Debate" },
  { key: "review", label: "レビュー", labelEn: "Review" },
  { key: "ideation", label: "アイデア出し", labelEn: "Ideation" },
  { key: "strategy", label: "戦略検討", labelEn: "Strategy" },
]

const AVAILABLE_MODELS = [
  "anthropic/claude-opus-4-6",
  "anthropic/claude-sonnet-4-6",
  "openai/gpt-5.4",
  "openai/gpt-5-mini",
  "google/gemini-2.5-pro",
  "google/gemini-2.5-flash",
  "deepseek/deepseek-v3",
]

export default function BrainstormPage() {
  const companyId = localStorage.getItem("company_id") || "default"

  // Tabs
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

  // Compare state
  const [compareInput, setCompareInput] = useState("")
  const [compareModels, setCompareModels] = useState<string[]>([])
  const [compareResult, setCompareResult] = useState<ComparisonResult | null>(null)
  const [comparing, setComparing] = useState(false)

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
      const data = await api.get<BrainstormSession[]>(
        `/companies/${companyId}/brainstorm/sessions`
      )
      setSessions(data)
    } catch {
      setSessions([])
    }
  }

  async function loadRoleModels() {
    try {
      const data = await api.get<RoleModelConfig[]>(
        `/companies/${companyId}/role-models`
      )
      setRoleModels(data)
    } catch {
      setRoleModels([])
    }
  }

  async function loadAvailableRoles() {
    try {
      const data = await api.get<AvailableRole[]>(
        `/companies/${companyId}/available-roles`
      )
      setAvailableRoles(data)
    } catch {
      setAvailableRoles([])
    }
  }

  async function createSession() {
    try {
      const data = await api.post<BrainstormSession>(
        `/companies/${companyId}/brainstorm`,
        {
          title: newTitle || undefined,
          topic: newTopic || undefined,
          session_type: newType,
          model_ids: selectedModels.length > 0 ? selectedModels : undefined,
          is_multi_model: isMultiModel,
        }
      )
      setSessions([data, ...sessions])
      setCurrentSession(data)
      setMessages([])
      setShowNewSession(false)
      setNewTitle("")
      setNewTopic("")
    } catch (e) {
      console.error("Failed to create session:", e)
    }
  }

  async function loadSessionMessages(sessionId: string) {
    try {
      const data = await api.get<{
        conversation_history: { messages: Message[] } | null
      }>(`/brainstorm/${sessionId}`)
      setMessages(data.conversation_history?.messages || [])
    } catch {
      setMessages([])
    }
  }

  async function sendMessage() {
    if (!input.trim() || !currentSession) return
    setLoading(true)
    try {
      const data = await api.post<{
        latest_messages: Message[]
        message_count: number
        total_chars: number
      }>(`/brainstorm/${currentSession.id}/message`, {
        role: "user",
        content: input,
      })
      setMessages(prev => [
        ...prev,
        { role: "user", content: input, timestamp: Date.now() / 1000 },
      ])
      setInput("")

      // Auto-analyze text
      analyzeText(input)
    } catch (e) {
      console.error("Failed to send message:", e)
    } finally {
      setLoading(false)
    }
  }

  async function analyzeText(text: string) {
    try {
      const data = await api.post<TextAnalysis>("/text/analyze", { text })
      setTextAnalysis(data)
    } catch {
      // ignore
    }
  }

  async function runMultiModelComparison() {
    if (!compareInput.trim() || compareModels.length < 2) return
    setComparing(true)
    try {
      const data = await api.post<ComparisonResult>(
        `/companies/${companyId}/multi-model/compare`,
        {
          input_text: compareInput,
          model_ids: compareModels,
        }
      )
      setCompareResult(data)
    } catch (e) {
      console.error("Failed to compare:", e)
    } finally {
      setComparing(false)
    }
  }

  async function submitFeatureRequest() {
    if (!featureRequest.trim()) return
    try {
      await api.post(`/companies/${companyId}/feature-requests`, {
        request_text: featureRequest,
        auto_execute: true,
      })
      setFeatureRequest("")
      loadAvailableRoles()
    } catch (e) {
      console.error("Failed to submit request:", e)
    }
  }

  async function addAgentByRole(role: string) {
    try {
      await api.post(`/companies/${companyId}/agents/by-role`, { role })
    } catch (e) {
      console.error("Failed to add agent:", e)
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: "0 auto" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        <Sparkles size={24} style={{ display: "inline", marginRight: 8 }} />
        壁打ち・マルチモデル比較 / Brainstorm & Multi-Model Compare
      </h1>
      <p style={{ color: "#6b7280", marginBottom: 24 }}>
        AI と壁打ちし、複数モデルの回答を比較。エージェントの役割とモデルを自由に設定。
      </p>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24, borderBottom: "1px solid #e5e7eb", paddingBottom: 8 }}>
        {[
          { key: "brainstorm" as const, icon: MessageSquare, label: "壁打ち" },
          { key: "compare" as const, icon: GitCompare, label: "モデル比較" },
          { key: "roles" as const, icon: Settings, label: "役割設定" },
          { key: "agents" as const, icon: Users, label: "組織管理" },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              background: activeTab === tab.key ? "#3b82f6" : "transparent",
              color: activeTab === tab.key ? "#fff" : "#6b7280",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontWeight: activeTab === tab.key ? 600 : 400,
            }}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Brainstorm Tab */}
      {activeTab === "brainstorm" && (
        <div style={{ display: "flex", gap: 16 }}>
          {/* Session list */}
          <div style={{ width: 280, flexShrink: 0 }}>
            <button
              onClick={() => setShowNewSession(true)}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: 8,
                border: "1px dashed #d1d5db",
                background: "#f9fafb",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
                marginBottom: 12,
              }}
            >
              <Plus size={16} /> 新しい壁打ち
            </button>

            {showNewSession && (
              <div style={{ padding: 12, border: "1px solid #e5e7eb", borderRadius: 8, marginBottom: 12, background: "#fff" }}>
                <input
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  placeholder="タイトル"
                  style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #d1d5db", marginBottom: 8 }}
                />
                <textarea
                  value={newTopic}
                  onChange={e => setNewTopic(e.target.value)}
                  placeholder="トピック（任意）"
                  rows={2}
                  style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #d1d5db", marginBottom: 8, resize: "vertical" }}
                />
                <select
                  value={newType}
                  onChange={e => setNewType(e.target.value)}
                  style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #d1d5db", marginBottom: 8 }}
                >
                  {SESSION_TYPES.map(t => (
                    <option key={t.key} value={t.key}>{t.label}</option>
                  ))}
                </select>
                <label style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, fontSize: 14 }}>
                  <input
                    type="checkbox"
                    checked={isMultiModel}
                    onChange={e => setIsMultiModel(e.target.checked)}
                  />
                  マルチモデル壁打ち
                </label>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    onClick={createSession}
                    style={{ flex: 1, padding: 8, borderRadius: 4, border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer" }}
                  >
                    作成
                  </button>
                  <button
                    onClick={() => setShowNewSession(false)}
                    style={{ padding: 8, borderRadius: 4, border: "1px solid #d1d5db", background: "#fff", cursor: "pointer" }}
                  >
                    キャンセル
                  </button>
                </div>
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {sessions.map(s => (
                <button
                  key={s.id}
                  onClick={() => {
                    setCurrentSession(s)
                    loadSessionMessages(s.id)
                  }}
                  style={{
                    padding: 10,
                    borderRadius: 8,
                    border: currentSession?.id === s.id ? "2px solid #3b82f6" : "1px solid #e5e7eb",
                    background: currentSession?.id === s.id ? "#eff6ff" : "#fff",
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>
                    {s.title || "無題"}
                  </div>
                  <div style={{ fontSize: 12, color: "#6b7280" }}>
                    {s.session_type} · {s.message_count} msgs · {s.total_chars.toLocaleString()} chars
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Chat area */}
          <div style={{ flex: 1 }}>
            {currentSession ? (
              <>
                <div style={{ padding: 12, background: "#f9fafb", borderRadius: 8, marginBottom: 12 }}>
                  <strong>{currentSession.title}</strong>
                  {currentSession.topic && (
                    <span style={{ color: "#6b7280", marginLeft: 12 }}>
                      トピック: {currentSession.topic}
                    </span>
                  )}
                  {currentSession.is_multi_model && (
                    <span style={{ marginLeft: 12, padding: "2px 8px", background: "#dbeafe", borderRadius: 12, fontSize: 12 }}>
                      マルチモデル
                    </span>
                  )}
                </div>

                <div style={{
                  height: 400,
                  overflowY: "auto",
                  border: "1px solid #e5e7eb",
                  borderRadius: 8,
                  padding: 16,
                  marginBottom: 12,
                  background: "#fff",
                }}>
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      style={{
                        marginBottom: 12,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: msg.role === "user" ? "flex-end" : "flex-start",
                      }}
                    >
                      <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>
                        {msg.role.startsWith("model:") ? msg.role.replace("model:", "") : msg.role}
                        {msg.char_count ? ` (${msg.char_count.toLocaleString()} chars)` : ""}
                      </div>
                      <div
                        style={{
                          padding: "10px 14px",
                          borderRadius: 12,
                          background: msg.role === "user" ? "#3b82f6" : "#f3f4f6",
                          color: msg.role === "user" ? "#fff" : "#1f2937",
                          maxWidth: "80%",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>

                {/* Text analysis display */}
                {textAnalysis && (
                  <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 8, display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <span><Type size={12} style={{ display: "inline" }} /> 合計: {textAnalysis.analysis.total}</span>
                    <span>漢字: {textAnalysis.analysis.kanji}</span>
                    <span>ひらがな: {textAnalysis.analysis.hiragana}</span>
                    <span>カタカナ: {textAnalysis.analysis.katakana}</span>
                    <span>英字: {textAnalysis.analysis.ascii}</span>
                  </div>
                )}

                <div style={{ display: "flex", gap: 8 }}>
                  <textarea
                    value={input}
                    onChange={e => {
                      setInput(e.target.value)
                      if (e.target.value.length > 0) analyzeText(e.target.value)
                    }}
                    onKeyDown={e => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        sendMessage()
                      }
                    }}
                    placeholder="メッセージを入力... (Shift+Enter で改行)"
                    rows={3}
                    style={{
                      flex: 1,
                      padding: 12,
                      borderRadius: 8,
                      border: "1px solid #d1d5db",
                      resize: "vertical",
                    }}
                  />
                  <button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    style={{
                      padding: "12px 20px",
                      borderRadius: 8,
                      border: "none",
                      background: "#3b82f6",
                      color: "#fff",
                      cursor: loading ? "wait" : "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                  </button>
                </div>
              </>
            ) : (
              <div style={{ textAlign: "center", padding: 60, color: "#9ca3af" }}>
                <MessageSquare size={48} style={{ margin: "0 auto 16px" }} />
                <p>壁打ちセッションを選択または作成してください</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Multi-Model Comparison Tab */}
      {activeTab === "compare" && (
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
            <GitCompare size={20} style={{ display: "inline", marginRight: 8 }} />
            マルチモデル比較 / Multi-Model Compare
          </h2>
          <p style={{ color: "#6b7280", marginBottom: 16, fontSize: 14 }}>
            同じ入力を複数のモデル（GPT / Gemini / Claude 等）に送信し、回答を見比べることができます。
          </p>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontWeight: 500, marginBottom: 6 }}>比較するモデルを選択（2つ以上）</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {AVAILABLE_MODELS.map(m => (
                <label key={m} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 14, padding: "4px 8px", border: "1px solid #d1d5db", borderRadius: 6, cursor: "pointer", background: compareModels.includes(m) ? "#dbeafe" : "#fff" }}>
                  <input
                    type="checkbox"
                    checked={compareModels.includes(m)}
                    onChange={e => {
                      if (e.target.checked) setCompareModels([...compareModels, m])
                      else setCompareModels(compareModels.filter(x => x !== m))
                    }}
                  />
                  {m.split("/")[1]}
                </label>
              ))}
            </div>
          </div>

          <textarea
            value={compareInput}
            onChange={e => setCompareInput(e.target.value)}
            placeholder="比較したい入力テキストを入力..."
            rows={5}
            style={{ width: "100%", padding: 12, borderRadius: 8, border: "1px solid #d1d5db", marginBottom: 12, resize: "vertical" }}
          />

          <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
            <button
              onClick={runMultiModelComparison}
              disabled={comparing || compareModels.length < 2 || !compareInput.trim()}
              style={{ padding: "10px 20px", borderRadius: 8, border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}
            >
              {comparing ? <Loader2 size={16} className="animate-spin" /> : <GitCompare size={16} />}
              比較実行
            </button>
            <span style={{ fontSize: 14, color: "#6b7280", alignSelf: "center" }}>
              文字数: {compareInput.length.toLocaleString()}
            </span>
          </div>

          {compareResult && (
            <div>
              <h3 style={{ fontWeight: 600, marginBottom: 12 }}>比較結果 (ID: {compareResult.id.slice(0, 8)}...)</h3>
              <div style={{ fontSize: 14, color: "#6b7280", marginBottom: 12 }}>
                入力文字数: {compareResult.input_char_count.toLocaleString()} · ステータス: {compareResult.status}
              </div>
              {compareResult.responses && (
                <div style={{ display: "grid", gridTemplateColumns: `repeat(${Object.keys(compareResult.responses).length}, 1fr)`, gap: 12 }}>
                  {Object.entries(compareResult.responses).map(([modelId, resp]) => (
                    <div key={modelId} style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 16, background: "#fff" }}>
                      <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 14 }}>{modelId.split("/")[1] || modelId}</div>
                      {resp.error ? (
                        <div style={{ color: "#ef4444" }}>エラー: {resp.error}</div>
                      ) : (
                        <>
                          <div style={{ whiteSpace: "pre-wrap", fontSize: 14, marginBottom: 8, maxHeight: 300, overflowY: "auto" }}>
                            {resp.text}
                          </div>
                          <div style={{ fontSize: 12, color: "#6b7280", borderTop: "1px solid #f3f4f6", paddingTop: 8 }}>
                            文字数: {resp.char_count.toLocaleString()} · トークン: {resp.tokens} · レイテンシ: {resp.latency_ms}ms
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Role Model Settings Tab */}
      {activeTab === "roles" && (
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
            <Settings size={20} style={{ display: "inline", marginRight: 8 }} />
            役割別モデル設定 / Role Model Settings
          </h2>
          <p style={{ color: "#6b7280", marginBottom: 16, fontSize: 14 }}>
            エージェントの役割ごとに使用する AI モデルを設定できます。
          </p>

          {roleModels.length > 0 ? (
            <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 24 }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
                  <th style={{ textAlign: "left", padding: 8 }}>役割</th>
                  <th style={{ textAlign: "left", padding: 8 }}>モデル</th>
                  <th style={{ textAlign: "left", padding: 8 }}>フォールバック</th>
                  <th style={{ textAlign: "left", padding: 8 }}>Max Tokens</th>
                  <th style={{ textAlign: "left", padding: 8 }}>状態</th>
                </tr>
              </thead>
              <tbody>
                {roleModels.map(rm => (
                  <tr key={rm.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: 8 }}>{rm.role_name}</td>
                    <td style={{ padding: 8, fontFamily: "monospace", fontSize: 13 }}>{rm.model_id}</td>
                    <td style={{ padding: 8, fontFamily: "monospace", fontSize: 13 }}>{rm.fallback_model_id || "-"}</td>
                    <td style={{ padding: 8 }}>{rm.max_tokens || "default"}</td>
                    <td style={{ padding: 8 }}>
                      <span style={{ padding: "2px 8px", borderRadius: 12, fontSize: 12, background: rm.is_active ? "#d1fae5" : "#fee2e2", color: rm.is_active ? "#065f46" : "#991b1b" }}>
                        {rm.is_active ? "有効" : "無効"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ textAlign: "center", padding: 32, color: "#9ca3af", border: "1px dashed #d1d5db", borderRadius: 8, marginBottom: 24 }}>
              モデル設定はまだありません。API 経由で設定してください。
            </div>
          )}

          <h3 style={{ fontWeight: 600, marginBottom: 12 }}>利用可能な役割</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: 12 }}>
            {availableRoles.map(r => (
              <div key={r.role_key} style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 8, background: "#fff" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <strong>{r.name}</strong>
                  <span style={{ fontSize: 11, padding: "2px 6px", borderRadius: 8, background: r.is_preset ? "#dbeafe" : "#fef3c7" }}>
                    {r.is_preset ? "プリセット" : "カスタム"}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 8 }}>{r.title}</div>
                <div style={{ fontSize: 13, color: "#4b5563" }}>{r.description.slice(0, 100)}{r.description.length > 100 ? "..." : ""}</div>
                <button
                  onClick={() => addAgentByRole(r.role_key)}
                  style={{ marginTop: 8, padding: "4px 12px", borderRadius: 4, border: "1px solid #3b82f6", background: "#fff", color: "#3b82f6", cursor: "pointer", fontSize: 12 }}
                >
                  <Plus size={12} style={{ display: "inline" }} /> エージェント追加
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Management Tab */}
      {activeTab === "agents" && (
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
            <Users size={20} style={{ display: "inline", marginRight: 8 }} />
            AI 組織管理 / AI Organization Management
          </h2>
          <p style={{ color: "#6b7280", marginBottom: 16, fontSize: 14 }}>
            自然言語で AI 組織に要望を伝えるだけで、エージェントの追加・削除・役割変更ができます。
          </p>

          <div style={{ padding: 20, background: "#f9fafb", borderRadius: 12, marginBottom: 24 }}>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 8 }}>
              <Sparkles size={16} style={{ display: "inline", marginRight: 6 }} />
              AI 組織への要望（自然言語）
            </label>
            <textarea
              value={featureRequest}
              onChange={e => setFeatureRequest(e.target.value)}
              placeholder="例: 「相談役のエージェントを追加して」「秘書のモデルをClaude Opusに変更して」「マーケティング担当を削除して」"
              rows={3}
              style={{ width: "100%", padding: 12, borderRadius: 8, border: "1px solid #d1d5db", marginBottom: 12, resize: "vertical" }}
            />
            <button
              onClick={submitFeatureRequest}
              disabled={!featureRequest.trim()}
              style={{ padding: "10px 20px", borderRadius: 8, border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer" }}
            >
              <Send size={16} style={{ display: "inline", marginRight: 6 }} />
              要望を送信
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            <div>
              <h3 style={{ fontWeight: 600, marginBottom: 12 }}>秘書の役割</h3>
              <div style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 8, background: "#fff" }}>
                <p style={{ fontSize: 14, color: "#4b5563" }}>
                  AI組織とユーザーの繋ぎ役。システムの情報の保管庫やファイル、
                  ユーザーとAI組織との会話からナレッジを貯め、ユーザーのお手伝いをする。
                </p>
              </div>
            </div>
            <div>
              <h3 style={{ fontWeight: 600, marginBottom: 12 }}>相談役の役割</h3>
              <div style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 8, background: "#fff" }}>
                <p style={{ fontSize: 14, color: "#4b5563" }}>
                  ユーザーが困った時にサポートしたり壁打ち相手になり、
                  秘書とユーザーを繋ぐ。多角的な視点からアドバイスを提供。
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
