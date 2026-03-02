import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  Play, RotateCcw, CheckCircle, XCircle, AlertTriangle,
  ChevronRight, Clock, DollarSign, Zap,
} from "lucide-react";
import * as api from "@/lib/api";

interface Step {
  step_id: string;
  skill_name: string;
  status: string;
  output?: Record<string, unknown>;
}

interface HealAttempt {
  attempt_number: number;
  strategy: string;
  original_error: string;
  result: string;
  timestamp: string;
}

export function OrchestrationPage() {
  const { id } = useParams<{ id: string }>();
  const [orch, setOrch] = useState<Record<string, unknown> | null>(null);
  const [healHistory, setHealHistory] = useState<HealAttempt[]>([]);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    const fetch = async () => {
      try {
        const data = await api.getOrchestration(id) as Record<string, unknown>;
        setOrch(data);
        const history = await api.getHealHistory(id) as HealAttempt[];
        setHealHistory(history);
      } catch (e) {
        console.error("Failed to fetch:", e);
      }
    };
    fetch();
    const interval = setInterval(fetch, 3000);
    return () => clearInterval(interval);
  }, [id]);

  if (!orch) {
    return (
      <div className="h-full flex items-center justify-center">
        <div style={{ color: '#6a6a6a' }}>Loading orchestration...</div>
      </div>
    );
  }

  const plan = orch.plan as { intent: string; steps: Step[] } | null;
  const status = orch.status as string;
  const cost = orch.cost_estimate as Record<string, unknown> | null;

  const handleApprove = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const updated = await api.approvePlan(id) as Record<string, unknown>;
      setOrch(updated);
    } finally {
      setLoading(false);
    }
  };

  const handleRepropose = async () => {
    if (!id || !feedback.trim()) return;
    setLoading(true);
    try {
      await api.repropose(id, feedback);
      const updated = await api.getOrchestration(id) as Record<string, unknown>;
      setOrch(updated);
      setFeedback("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[800px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <StatusBadge status={status} />
              <span className="text-[11px]" style={{ color: '#6a6a6a' }}>
                {id?.slice(0, 8)}
              </span>
            </div>
            <h2 className="text-[14px]" style={{ color: '#cccccc' }}>
              {plan?.intent || "Orchestration"}
            </h2>
          </div>
        </div>

        {/* Cost Estimate */}
        {cost != null && (
          <div
            className="rounded p-3 mb-4 flex items-center gap-6 text-[12px]"
            style={{ background: '#252526', border: '1px solid #3e3e42' }}
          >
            <div className="flex items-center gap-1.5" style={{ color: '#969696' }}>
              <DollarSign size={13} />
              <span>${Number(cost.estimated_cost_usd || 0).toFixed(4)}</span>
            </div>
            <div className="flex items-center gap-1.5" style={{ color: '#969696' }}>
              <Clock size={13} />
              <span>{String(cost.estimated_time_seconds)}s</span>
            </div>
            <div className="flex items-center gap-1.5" style={{ color: '#969696' }}>
              <Zap size={13} />
              <span>{String(cost.total_api_calls)} API calls</span>
            </div>
            {Boolean(cost.budget_exceeded) && (
              <div className="flex items-center gap-1.5" style={{ color: '#dcdcaa' }}>
                <AlertTriangle size={13} />
                <span>Budget exceeded</span>
              </div>
            )}
          </div>
        )}

        {/* Plan DAG */}
        {plan != null && (
          <div className="mb-6">
            <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6a6a6a' }}>
              Execution Plan
            </div>
            <div className="flex flex-col gap-2">
              {plan.steps.map((step: Step, i: number) => (
                <div
                  key={step.step_id}
                  className="flex items-center gap-3 rounded px-3 py-2"
                  style={{ background: '#252526', border: '1px solid #3e3e42' }}
                >
                  <div className="text-[11px] font-mono w-6 text-center" style={{ color: '#6a6a6a' }}>
                    {i + 1}
                  </div>
                  <ChevronRight size={12} style={{ color: '#3e3e42' }} />
                  <div className="flex-1">
                    <span className="text-[13px]" style={{ color: '#9cdcfe' }}>
                      {step.skill_name}
                    </span>
                  </div>
                  <StepStatusIcon status={step.status} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        {status === "awaiting_approval" && (
          <div className="flex flex-col gap-3 mb-6">
            <div className="flex gap-3">
              <button
                onClick={handleApprove}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 rounded text-[12px]"
                style={{ background: '#007acc', color: '#ffffff' }}
              >
                <Play size={14} />
                {loading ? "Executing..." : "Approve & Execute"}
              </button>
            </div>

            {/* Repropose */}
            <div
              className="rounded p-3"
              style={{ border: '1px solid #3e3e42', background: '#252526' }}
            >
              <div className="text-[11px] mb-2" style={{ color: '#6a6a6a' }}>
                Want changes? Describe what to modify:
              </div>
              <div className="flex gap-2">
                <input
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="e.g., Add trend analysis step"
                  className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none"
                  style={{ background: '#3c3c3c', color: '#cccccc', border: '1px solid #3e3e42' }}
                />
                <button
                  onClick={handleRepropose}
                  disabled={!feedback.trim() || loading}
                  className="flex items-center gap-1 px-3 py-1.5 rounded text-[12px]"
                  style={{
                    border: '1px solid #3e3e42',
                    color: feedback.trim() ? '#cccccc' : '#6a6a6a',
                  }}
                >
                  <RotateCcw size={12} />
                  Re-propose
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {status === "completed" && orch.results != null && (
          <div className="mb-6">
            <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: '#4ec9b0' }}>
              Results
            </div>
            <div
              className="rounded p-4 text-[12px] whitespace-pre-wrap"
              style={{ background: '#252526', border: '1px solid #3e3e42', color: '#cccccc' }}
            >
              {JSON.stringify(orch.results, null, 2)}
            </div>
          </div>
        )}

        {/* Self-Healing Panel */}
        {healHistory.length > 0 && (
          <div className="mb-6">
            <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: '#dcdcaa' }}>
              Self-Healing History
            </div>
            <div className="flex flex-col gap-2">
              {healHistory.map((attempt: HealAttempt) => (
                <div
                  key={attempt.attempt_number}
                  className="flex items-center gap-3 rounded px-3 py-2"
                  style={{ background: '#252526', border: '1px solid #3e3e42' }}
                >
                  <div className="text-[11px] font-mono" style={{ color: '#6a6a6a' }}>
                    #{attempt.attempt_number}
                  </div>
                  <span
                    className="text-[11px] px-1.5 py-0.5 rounded"
                    style={{
                      background: attempt.result === "success" ? '#1b4332'
                        : attempt.result === "escalated" ? '#5c4a1a'
                        : '#4a1a1a',
                      color: attempt.result === "success" ? '#4ec9b0'
                        : attempt.result === "escalated" ? '#dcdcaa'
                        : '#f44747',
                    }}
                  >
                    {attempt.strategy}
                  </span>
                  <span className="text-[11px]" style={{ color: '#969696' }}>
                    {attempt.original_error.slice(0, 60)}
                  </span>
                  <div className="flex-1" />
                  <HealResultBadge result={attempt.result} />
                </div>
              ))}
            </div>
          </div>
        )}

        {status === "executing" && (
          <div
            className="rounded p-4 flex items-center gap-3 animate-pulse-glow"
            style={{ background: '#252526', border: '1px solid #007acc' }}
          >
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#007acc' }} />
            <span className="text-[12px]" style={{ color: '#cccccc' }}>
              AI組織が実行中...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    planning: { bg: '#1a3a5c', text: '#9cdcfe' },
    awaiting_approval: { bg: '#5c4a1a', text: '#dcdcaa' },
    executing: { bg: '#1a3a5c', text: '#007acc' },
    completed: { bg: '#1b4332', text: '#4ec9b0' },
    failed: { bg: '#4a1a1a', text: '#f44747' },
  };
  const c = colors[status] || colors.planning;
  return (
    <span className="text-[11px] px-1.5 py-0.5 rounded" style={{ background: c.bg, color: c.text }}>
      {status}
    </span>
  );
}

function StepStatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle size={14} style={{ color: '#4ec9b0' }} />;
  if (status === "failed") return <XCircle size={14} style={{ color: '#f44747' }} />;
  if (status === "running") return <div className="w-3 h-3 rounded-full animate-pulse" style={{ background: '#007acc' }} />;
  return <div className="w-3 h-3 rounded-full" style={{ background: '#3e3e42' }} />;
}

function HealResultBadge({ result }: { result: string }) {
  if (result === "success") return <CheckCircle size={14} style={{ color: '#4ec9b0' }} />;
  if (result === "escalated") return <AlertTriangle size={14} style={{ color: '#dcdcaa' }} />;
  return <XCircle size={14} style={{ color: '#f44747' }} />;
}
