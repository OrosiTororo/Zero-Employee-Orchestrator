import { useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  Wand2,
  CheckCircle,
  AlertTriangle,
  ArrowLeft,
  Save,
} from "lucide-react"

const API_BASE = "/api/v1/registry"

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

  const handleGenerate = async () => {
    if (!description.trim() || loading) return
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch(`${API_BASE}/skills/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: description.trim(),
          language: "ja",
          auto_register: false,
        }),
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${res.status}`)
      }
      const data: GenerateResult = await res.json()
      setResult(data)
    } catch (e) {
      console.error("Generation failed:", e)
      alert(`スキル生成に失敗しました: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!result || !result.safety_passed || registering) return
    setRegistering(true)
    try {
      const res = await fetch(`${API_BASE}/skills/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: description.trim(),
          language: "ja",
          auto_register: true,
        }),
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${res.status}`)
      }
      const data: GenerateResult = await res.json()
      setResult(data)
      if (data.registered) {
        navigate("/skills")
      }
    } catch (e) {
      console.error("Registration failed:", e)
      alert(`スキル登録に失敗しました: ${e instanceof Error ? e.message : String(e)}`)
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
            className="text-[#6a6a6a] hover:text-[#cccccc]"
          >
            <ArrowLeft size={16} />
          </button>
          <h2 className="text-[14px] font-medium text-[#cccccc]">
            スキル作成
          </h2>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#007acc20] text-[#007acc]">
            自然言語生成
          </span>
        </div>

        <p className="text-[12px] mb-4 text-[#969696]">
          自然言語でスキルの機能を説明してください。AIが自動的にスキルのマニフェストと実行コードを生成します。
          生成されたコードは安全性チェックを通過してから登録できます。
        </p>

        {/* Input */}
        <div className="rounded overflow-hidden mb-4 border border-[#3e3e42] bg-[#252526]">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={
              "例:\n" +
              "- 競合他社のWebサイトを定期的にスクレイピングして価格変動をレポートするスキル\n" +
              "- MarkdownファイルをHTMLに変換して目次を自動生成するスキル\n" +
              "- テキストの感情分析を行い、ポジティブ/ネガティブ/ニュートラルを判定するスキル"
            }
            className="w-full resize-none px-4 py-3 text-[13px] outline-none bg-transparent text-[#cccccc]"
            style={{ minHeight: "120px" }}
            rows={5}
          />
          <div className="flex items-center justify-between px-4 py-2 border-t border-[#3e3e42]">
            <span className="text-[11px] text-[#6a6a6a]">
              {description.length}/5000 文字
            </span>
            <button
              onClick={handleGenerate}
              disabled={!description.trim() || description.trim().length < 10 || loading}
              className="flex items-center gap-2 px-4 py-2 rounded text-[12px]"
              style={{
                background:
                  description.trim().length >= 10 && !loading
                    ? "#007acc"
                    : "#3e3e42",
                color: "#ffffff",
              }}
            >
              <Wand2 size={14} />
              {loading ? "生成中..." : "スキルを生成"}
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
                    <CheckCircle size={14} className="text-[#4ec9b0]" />
                    <span className="text-[12px] text-[#4ec9b0]">
                      安全性チェック合格
                    </span>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={14} className="text-[#f44747]" />
                    <span className="text-[12px] text-[#f44747]">
                      安全性の問題が検出されました
                    </span>
                  </>
                )}
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    background:
                      result.safety_report.risk_level === "low"
                        ? "#4ec9b020"
                        : result.safety_report.risk_level === "medium"
                          ? "#dcdcaa20"
                          : "#f4474720",
                    color:
                      result.safety_report.risk_level === "low"
                        ? "#4ec9b0"
                        : result.safety_report.risk_level === "medium"
                          ? "#dcdcaa"
                          : "#f44747",
                  }}
                >
                  リスク: {result.safety_report.risk_level}
                </span>
              </div>

              {result.safety_passed && !result.registered && (
                <button
                  onClick={handleRegister}
                  disabled={registering}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#4ec9b0] text-[#1e1e1e]"
                >
                  <Save size={12} />
                  {registering ? "登録中..." : "スキルを登録"}
                </button>
              )}
              {result.registered && (
                <span className="text-[11px] px-1.5 py-0.5 rounded bg-[#1b4332] text-[#4ec9b0]">
                  登録済
                </span>
              )}
            </div>

            {/* Safety Issues */}
            {result.safety_issues.length > 0 && (
              <div className="rounded p-3 bg-[#4a1a1a] border border-[#f44747]">
                {result.safety_issues.map((issue: string, i: number) => (
                  <div key={i} className="text-[12px] text-[#f44747]">
                    - {issue}
                  </div>
                ))}
              </div>
            )}

            {/* Safety Report */}
            <div className="rounded p-3 border border-[#3e3e42] bg-[#252526]">
              <div className="text-[11px] uppercase tracking-wider mb-2 text-[#6a6a6a]">
                安全性レポート
              </div>
              <div className="text-[12px] text-[#969696]">
                {result.safety_report.summary}
              </div>
            </div>

            {/* Skill JSON */}
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1 text-[#6a6a6a]">
                SKILL.json
              </div>
              <pre className="rounded p-3 text-[12px] overflow-auto border border-[#3e3e42] bg-[#252526] text-[#9cdcfe]">
                {JSON.stringify(result.skill_json, null, 2)}
              </pre>
            </div>

            {/* Executor Code */}
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1 text-[#6a6a6a]">
                executor.py
              </div>
              <pre className="rounded p-3 text-[12px] overflow-auto border border-[#3e3e42] bg-[#252526] text-[#d4d4d4] max-h-[400px]">
                {result.code}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
