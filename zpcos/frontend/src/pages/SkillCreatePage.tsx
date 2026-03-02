import { useState } from "react";
import { Wand2, CheckCircle, AlertTriangle } from "lucide-react";
import * as api from "@/lib/api";

export function SkillCreatePage() {
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!description.trim() || loading) return;
    setLoading(true);
    try {
      const res = await api.generateSkill(description) as Record<string, unknown>;
      setResult(res);
    } catch (e) {
      console.error("Generation failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        <h2 className="text-[14px] font-medium mb-4" style={{ color: '#cccccc' }}>
          Skill Generator
        </h2>

        <p className="text-[12px] mb-4" style={{ color: '#969696' }}>
          自然言語でSkillの機能を説明してください。AIが自動的にSkillを生成します。
        </p>

        {/* Input */}
        <div
          className="rounded overflow-hidden mb-4"
          style={{ border: '1px solid #3e3e42', background: '#252526' }}
        >
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="例: YouTube動画のタイトルとサムネイルをA/Bテストするための候補を生成するSkill"
            className="w-full resize-none px-4 py-3 text-[13px] outline-none"
            style={{ background: 'transparent', color: '#cccccc', minHeight: '120px' }}
            rows={5}
          />
          <div
            className="flex items-center justify-end px-4 py-2"
            style={{ borderTop: '1px solid #3e3e42' }}
          >
            <button
              onClick={handleGenerate}
              disabled={!description.trim() || loading}
              className="flex items-center gap-2 px-4 py-2 rounded text-[12px]"
              style={{
                background: description.trim() && !loading ? '#007acc' : '#3e3e42',
                color: '#ffffff',
              }}
            >
              <Wand2 size={14} />
              {loading ? "Generating..." : "Generate Skill"}
            </button>
          </div>
        </div>

        {/* Result */}
        {result && (
          <div className="flex flex-col gap-4">
            {/* Safety Check */}
            <div className="flex items-center gap-2">
              {result.safety_passed ? (
                <>
                  <CheckCircle size={14} style={{ color: '#4ec9b0' }} />
                  <span className="text-[12px]" style={{ color: '#4ec9b0' }}>
                    Safety check passed
                  </span>
                </>
              ) : (
                <>
                  <AlertTriangle size={14} style={{ color: '#f44747' }} />
                  <span className="text-[12px]" style={{ color: '#f44747' }}>
                    Safety issues detected
                  </span>
                </>
              )}
              {Boolean(result.registered) && (
                <span className="text-[11px] px-1.5 py-0.5 rounded" style={{ background: '#1b4332', color: '#4ec9b0' }}>
                  Registered
                </span>
              )}
            </div>

            {/* Safety Issues */}
            {Array.isArray(result.safety_issues) && (result.safety_issues as string[]).length > 0 && (
              <div className="rounded p-3" style={{ background: '#4a1a1a', border: '1px solid #f44747' }}>
                {(result.safety_issues as string[]).map((issue: string, i: number) => (
                  <div key={i} className="text-[12px]" style={{ color: '#f44747' }}>
                    • {issue}
                  </div>
                ))}
              </div>
            )}

            {/* SKILL.json */}
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: '#6a6a6a' }}>
                SKILL.json
              </div>
              <pre
                className="rounded p-3 text-[12px] overflow-auto"
                style={{ background: '#252526', border: '1px solid #3e3e42', color: '#9cdcfe' }}
              >
                {JSON.stringify(result.skill_json, null, 2)}
              </pre>
            </div>

            {/* Code */}
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: '#6a6a6a' }}>
                executor.py
              </div>
              <pre
                className="rounded p-3 text-[12px] overflow-auto"
                style={{ background: '#252526', border: '1px solid #3e3e42', color: '#d4d4d4', maxHeight: '400px' }}
              >
                {result.code as string}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
