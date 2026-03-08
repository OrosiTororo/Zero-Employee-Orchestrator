import { useState } from "react"
import { Wand2, CheckCircle, AlertTriangle } from "lucide-react"

export function SkillCreatePage() {
  const [description, setDescription] = useState("")
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    if (!description.trim() || loading) return
    setLoading(true)
    try {
      // TODO: POST to /skills/generate
      setResult({ safety_passed: true, registered: false, skill_json: {}, code: "" })
    } catch (e) {
      console.error("Generation failed:", e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        <h2 className="text-[14px] font-medium mb-4 text-[#cccccc]">
          スキル作成
        </h2>

        <p className="text-[12px] mb-4 text-[#969696]">
          自然言語でスキルの機能を説明してください。AIが自動的にスキルを生成します。
        </p>

        {/* Input */}
        <div className="rounded overflow-hidden mb-4 border border-[#3e3e42] bg-[#252526]">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="例: 競合他社のWebサイトを定期的にスクレイピングして価格変動をレポートするスキル"
            className="w-full resize-none px-4 py-3 text-[13px] outline-none bg-transparent text-[#cccccc]"
            style={{ minHeight: "120px" }}
            rows={5}
          />
          <div className="flex items-center justify-end px-4 py-2 border-t border-[#3e3e42]">
            <button
              onClick={handleGenerate}
              disabled={!description.trim() || loading}
              className="flex items-center gap-2 px-4 py-2 rounded text-[12px]"
              style={{
                background:
                  description.trim() && !loading ? "#007acc" : "#3e3e42",
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
              {Boolean(result.registered) && (
                <span className="text-[11px] px-1.5 py-0.5 rounded bg-[#1b4332] text-[#4ec9b0]">
                  登録済
                </span>
              )}
            </div>

            {Array.isArray(result.safety_issues) &&
              (result.safety_issues as string[]).length > 0 && (
                <div className="rounded p-3 bg-[#4a1a1a] border border-[#f44747]">
                  {(result.safety_issues as string[]).map(
                    (issue: string, i: number) => (
                      <div key={i} className="text-[12px] text-[#f44747]">
                        - {issue}
                      </div>
                    ),
                  )}
                </div>
              )}

            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1 text-[#6a6a6a]">
                SKILL.json
              </div>
              <pre className="rounded p-3 text-[12px] overflow-auto border border-[#3e3e42] bg-[#252526] text-[#9cdcfe]">
                {JSON.stringify(result.skill_json, null, 2)}
              </pre>
            </div>

            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1 text-[#6a6a6a]">
                executor.py
              </div>
              <pre className="rounded p-3 text-[12px] overflow-auto border border-[#3e3e42] bg-[#252526] text-[#d4d4d4] max-h-[400px]">
                {result.code as string}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
