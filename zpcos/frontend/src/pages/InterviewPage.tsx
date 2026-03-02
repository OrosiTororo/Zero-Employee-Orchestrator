import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { CheckCircle, HelpCircle, ChevronDown, ArrowRight } from "lucide-react";
import * as api from "@/lib/api";

interface Question {
  id: string;
  question: string;
  why: string;
  options: string[];
}

export function InterviewPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const session = location.state?.session as { id: string; questions: Question[] } | undefined;
  const qualityMode = location.state?.qualityMode || "balanced";

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [spec, setSpec] = useState<Record<string, string[]> | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedWhy, setExpandedWhy] = useState<Set<string>>(new Set());

  if (!session) {
    return (
      <div className="h-full flex items-center justify-center">
        <p style={{ color: '#6a6a6a' }}>
          No interview session. <button onClick={() => navigate("/")} style={{ color: '#007acc' }}>Go back</button>
        </p>
      </div>
    );
  }

  const questions = session.questions || [];
  const answeredCount = Object.keys(answers).length;
  const progress = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0;

  const handleFinalize = async () => {
    setLoading(true);
    try {
      await api.interviewRespond(session.id, answers);
      const specResult = await api.interviewFinalize(session.id) as Record<string, string[]>;
      setSpec(specResult);
    } catch (e) {
      console.error("Finalize failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveSpec = async () => {
    setLoading(true);
    try {
      const orch = await api.orchestrate(
        (location.state?.session as { user_input: string })?.user_input || "",
        qualityMode
      ) as { id: string };
      navigate(`/orchestrate/${orch.id}`);
    } catch (e) {
      console.error("Orchestrate failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const toggleWhy = (id: string) => {
    setExpandedWhy((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] px-1.5 py-0.5 rounded" style={{ background: '#007acc', color: '#fff' }}>
              INTERVIEW
            </span>
            <span className="text-[11px]" style={{ color: '#6a6a6a' }}>
              {answeredCount}/{questions.length} answered
            </span>
          </div>
          {/* Progress bar */}
          <div className="h-[2px] rounded-full mt-2" style={{ background: '#3e3e42' }}>
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${progress}%`, background: '#007acc' }}
            />
          </div>
        </div>

        {!spec ? (
          <>
            {/* Questions */}
            <div className="flex flex-col gap-4">
              {questions.map((q: Question) => (
                <div
                  key={q.id}
                  className="rounded p-4"
                  style={{ border: '1px solid #3e3e42', background: '#252526' }}
                >
                  <div className="flex items-start gap-2 mb-3">
                    <HelpCircle size={16} className="mt-0.5 shrink-0" style={{ color: '#007acc' }} />
                    <div className="flex-1">
                      <p className="text-[13px]" style={{ color: '#cccccc' }}>{q.question}</p>
                      {q.why && (
                        <button
                          onClick={() => toggleWhy(q.id)}
                          className="flex items-center gap-1 mt-1 text-[11px]"
                          style={{ color: '#6a6a6a' }}
                        >
                          <ChevronDown size={12} className={expandedWhy.has(q.id) ? "rotate-180" : ""} />
                          Why this question?
                        </button>
                      )}
                      {expandedWhy.has(q.id) && (
                        <p className="mt-1 text-[11px] pl-4" style={{ color: '#969696', borderLeft: '2px solid #3e3e42' }}>
                          {q.why}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Options */}
                  {q.options.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2 pl-6">
                      {q.options.map((opt: string) => (
                        <button
                          key={opt}
                          onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                          className="px-3 py-1 rounded text-[12px] transition-colors"
                          style={{
                            background: answers[q.id] === opt ? '#007acc' : 'transparent',
                            color: answers[q.id] === opt ? '#ffffff' : '#cccccc',
                            border: `1px solid ${answers[q.id] === opt ? '#007acc' : '#3e3e42'}`,
                          }}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Free text */}
                  <div className="pl-6">
                    <input
                      type="text"
                      placeholder="Or type your answer..."
                      value={answers[q.id] || ""}
                      onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                      className="w-full px-3 py-1.5 rounded text-[12px] outline-none"
                      style={{
                        background: '#3c3c3c',
                        color: '#cccccc',
                        border: '1px solid #3e3e42',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Finalize */}
            <div className="mt-6 flex justify-end">
              <button
                onClick={handleFinalize}
                disabled={loading || answeredCount === 0}
                className="flex items-center gap-2 px-4 py-2 rounded text-[12px] transition-colors"
                style={{
                  background: answeredCount > 0 && !loading ? '#007acc' : '#3e3e42',
                  color: '#ffffff',
                }}
              >
                <CheckCircle size={14} />
                {loading ? "Generating spec..." : "Generate Spec"}
              </button>
            </div>
          </>
        ) : (
          /* Spec Preview */
          <div>
            <h3 className="text-[14px] font-medium mb-4" style={{ color: '#cccccc' }}>
              Generated Specification
            </h3>
            {Object.entries(spec).map(([key, values]) => (
              <div key={key} className="mb-4">
                <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: '#007acc' }}>
                  {key.replace(/_/g, " ")}
                </div>
                <div className="rounded p-3" style={{ background: '#252526', border: '1px solid #3e3e42' }}>
                  {Array.isArray(values) ? (
                    values.map((v: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 py-0.5">
                        <span style={{ color: '#6a6a6a' }}>•</span>
                        <span className="text-[12px]" style={{
                          color: key === "ai_assumptions" ? '#dcdcaa' : '#cccccc',
                        }}>
                          {v}
                        </span>
                      </div>
                    ))
                  ) : (
                    <span className="text-[12px]" style={{ color: '#cccccc' }}>{String(values)}</span>
                  )}
                </div>
              </div>
            ))}

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleApproveSpec}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 rounded text-[12px]"
                style={{ background: '#007acc', color: '#ffffff' }}
              >
                <ArrowRight size={14} />
                {loading ? "Creating plan..." : "Execute with this spec"}
              </button>
              <button
                onClick={() => setSpec(null)}
                className="px-4 py-2 rounded text-[12px]"
                style={{ border: '1px solid #3e3e42', color: '#cccccc' }}
              >
                Revise
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
