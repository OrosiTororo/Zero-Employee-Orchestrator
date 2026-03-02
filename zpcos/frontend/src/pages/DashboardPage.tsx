import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Send, Sparkles } from "lucide-react";
import * as api from "@/lib/api";

export function DashboardPage() {
  const [input, setInput] = useState("");
  const [qualityMode, setQualityMode] = useState("balanced");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    try {
      const session = await api.interviewStart(input) as { id: string };
      navigate("/interview", { state: { session, qualityMode } });
    } catch (e) {
      console.error("Failed to start interview:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Editor-like content area */}
      <div className="flex-1 flex flex-col items-center justify-center px-8">
        <div className="w-full max-w-[640px] flex flex-col gap-6">
          {/* Welcome */}
          <div className="flex flex-col items-center gap-2 mb-4">
            <Sparkles size={32} style={{ color: '#007acc' }} />
            <h2 className="text-lg font-light" style={{ color: '#cccccc' }}>
              What would you like to accomplish?
            </h2>
            <p className="text-[12px]" style={{ color: '#6a6a6a' }}>
              自然言語で目的を伝えてください。AI組織が計画を立てて実行します。
            </p>
          </div>

          {/* Input Area - VSCode Command Palette style */}
          <div
            className="rounded overflow-hidden"
            style={{ border: '1px solid #3e3e42', background: '#252526' }}
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="例: YouTubeチャンネルを伸ばしたい"
              className="w-full resize-none px-4 py-3 text-[13px] outline-none"
              style={{
                background: 'transparent',
                color: '#cccccc',
                minHeight: '80px',
              }}
              rows={3}
            />
            <div
              className="flex items-center justify-between px-4 py-2"
              style={{ borderTop: '1px solid #3e3e42' }}
            >
              {/* Quality Mode Selector */}
              <div className="flex items-center gap-3">
                {(["fastest", "balanced", "high_quality"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setQualityMode(mode)}
                    className="px-2 py-0.5 rounded text-[11px] transition-colors"
                    style={{
                      background: qualityMode === mode ? '#007acc' : 'transparent',
                      color: qualityMode === mode ? '#ffffff' : '#969696',
                      border: qualityMode === mode ? 'none' : '1px solid #3e3e42',
                    }}
                  >
                    {mode === "fastest" && "Fast"}
                    {mode === "balanced" && "Balanced"}
                    {mode === "high_quality" && "Quality"}
                  </button>
                ))}
              </div>

              <button
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className="flex items-center gap-1.5 px-3 py-1 rounded text-[12px] transition-colors"
                style={{
                  background: input.trim() && !loading ? '#007acc' : '#3e3e42',
                  color: '#ffffff',
                  cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                }}
              >
                <Send size={13} />
                {loading ? "Starting..." : "Start"}
              </button>
            </div>
          </div>

          {/* Recent Tasks */}
          <div>
            <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6a6a6a' }}>
              Recent
            </div>
            <div
              className="rounded px-4 py-6 text-center text-[12px]"
              style={{ border: '1px solid #3e3e42', color: '#6a6a6a' }}
            >
              No recent orchestrations. Start by describing what you want to accomplish.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
