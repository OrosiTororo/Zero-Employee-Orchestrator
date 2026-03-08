import { useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  Zap,
  ChevronRight,
  ChevronLeft,
  Building2,
  Bot,
  Key,
  Sparkles,
  Check,
} from "lucide-react"

type Step = "welcome" | "organization" | "provider" | "first_agent" | "complete"

const steps: { id: Step; label: string }[] = [
  { id: "welcome", label: "ようこそ" },
  { id: "organization", label: "組織設定" },
  { id: "provider", label: "AI接続" },
  { id: "first_agent", label: "最初のエージェント" },
  { id: "complete", label: "完了" },
]

export function SetupPage() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<Step>("welcome")
  const [orgName, setOrgName] = useState("")
  const [orgMission, setOrgMission] = useState("")
  const [providerType, setProviderType] = useState("openrouter")
  const [executionMode, setExecutionMode] = useState("quality")
  const [firstAgentName, setFirstAgentName] = useState("アシスタント")

  const stepIndex = steps.findIndex((s) => s.id === currentStep)

  const next = () => {
    if (stepIndex < steps.length - 1) {
      setCurrentStep(steps[stepIndex + 1].id)
    }
  }
  const prev = () => {
    if (stepIndex > 0) {
      setCurrentStep(steps[stepIndex - 1].id)
    }
  }

  const finishSetup = () => {
    // TODO: Save settings via API
    navigate("/")
  }

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#1e1e1e]">
      <div className="max-w-[600px] w-full px-8">
        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          {steps.map((step, i) => (
            <div key={step.id} className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-medium"
                style={{
                  background: i <= stepIndex ? "#007acc" : "#3e3e42",
                  color: i <= stepIndex ? "#fff" : "#6a6a6a",
                }}
              >
                {i < stepIndex ? <Check size={14} /> : i + 1}
              </div>
              {i < steps.length - 1 && (
                <div
                  className="w-8 h-[2px]"
                  style={{
                    background: i < stepIndex ? "#007acc" : "#3e3e42",
                  }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="min-h-[300px]">
          {currentStep === "welcome" && (
            <div className="flex flex-col items-center gap-6 text-center">
              <div className="w-16 h-16 rounded-lg flex items-center justify-center bg-[#007acc]">
                <Zap size={36} color="#fff" />
              </div>
              <h2 className="text-2xl font-semibold text-[#cccccc]">
                Zero-Employee Orchestrator へようこそ
              </h2>
              <p className="text-[14px] text-[#969696] leading-relaxed max-w-[450px]">
                このウィザードでは、AI組織の基本設定を行います。
                <br />
                <br />
                自然言語で業務を依頼するだけで、AIチームが計画・実行・検証を行い、
                あなたの承認のもとで業務を遂行します。
                <br />
                <br />
                専門知識は不要です。一つずつ設定していきましょう。
              </p>
            </div>
          )}

          {currentStep === "organization" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-3">
                <Building2 size={24} className="text-[#007acc]" />
                <h2 className="text-xl font-semibold text-[#cccccc]">
                  組織の設定
                </h2>
              </div>
              <p className="text-[13px] text-[#969696]">
                AI組織の名前とミッションを設定します。後から変更できます。
              </p>
              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-[12px] text-[#969696] mb-1 block">
                    組織名
                  </label>
                  <input
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="例: マイカンパニー"
                    className="w-full px-3 py-2.5 rounded text-[13px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] outline-none"
                  />
                </div>
                <div>
                  <label className="text-[12px] text-[#969696] mb-1 block">
                    ミッション（任意）
                  </label>
                  <textarea
                    value={orgMission}
                    onChange={(e) => setOrgMission(e.target.value)}
                    placeholder="例: AIを活用して効率的な業務運営を実現する"
                    rows={3}
                    className="w-full px-3 py-2.5 rounded text-[13px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] outline-none resize-none"
                  />
                </div>
              </div>
            </div>
          )}

          {currentStep === "provider" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-3">
                <Key size={24} className="text-[#007acc]" />
                <h2 className="text-xl font-semibold text-[#cccccc]">
                  AI接続の設定
                </h2>
              </div>
              <p className="text-[13px] text-[#969696]">
                AIモデルへの接続方法を選択します。後で設定画面から変更・追加できます。
                <br />
                APIキーがなくても、まずはスキップして体験できます。
              </p>

              <div className="flex flex-col gap-3">
                {[
                  {
                    id: "openrouter",
                    name: "OpenRouter",
                    desc: "多数のAIモデルを一括利用（推奨）",
                  },
                  {
                    id: "openai",
                    name: "OpenAI",
                    desc: "GPT-4o等を直接利用",
                  },
                  {
                    id: "anthropic",
                    name: "Anthropic",
                    desc: "Claude等を直接利用",
                  },
                  {
                    id: "local",
                    name: "ローカルモデル",
                    desc: "Ollama等でAPI不要・完全無料",
                  },
                  {
                    id: "skip",
                    name: "後で設定する",
                    desc: "まずはUI体験から始める",
                  },
                ].map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setProviderType(p.id)}
                    className="flex items-center gap-3 px-4 py-3 rounded border text-left transition-colors"
                    style={{
                      background:
                        providerType === p.id ? "#007acc15" : "transparent",
                      borderColor:
                        providerType === p.id ? "#007acc" : "#3e3e42",
                    }}
                  >
                    <div
                      className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                      style={{
                        borderColor:
                          providerType === p.id ? "#007acc" : "#6a6a6a",
                      }}
                    >
                      {providerType === p.id && (
                        <div className="w-2 h-2 rounded-full bg-[#007acc]" />
                      )}
                    </div>
                    <div>
                      <div className="text-[13px] text-[#cccccc] font-medium">
                        {p.name}
                      </div>
                      <div className="text-[11px] text-[#6a6a6a]">{p.desc}</div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex flex-col gap-3 mt-2">
                <span className="text-[12px] text-[#969696]">実行モード</span>
                <div className="flex gap-2">
                  {[
                    { id: "quality", label: "品質重視" },
                    { id: "speed", label: "速度重視" },
                    { id: "cost", label: "コスト重視" },
                    { id: "free", label: "無料枠優先" },
                  ].map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setExecutionMode(m.id)}
                      className="flex-1 px-3 py-2 rounded text-[12px] border transition-colors"
                      style={{
                        background:
                          executionMode === m.id ? "#007acc20" : "transparent",
                        borderColor:
                          executionMode === m.id ? "#007acc" : "#3e3e42",
                        color: "#cccccc",
                      }}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {currentStep === "first_agent" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-3">
                <Bot size={24} className="text-[#007acc]" />
                <h2 className="text-xl font-semibold text-[#cccccc]">
                  最初のAIエージェント
                </h2>
              </div>
              <p className="text-[13px] text-[#969696]">
                最初のAIエージェントを作成します。このエージェントが業務の窓口となり、
                必要に応じて他のエージェントを組織します。
              </p>
              <div>
                <label className="text-[12px] text-[#969696] mb-1 block">
                  エージェント名
                </label>
                <input
                  value={firstAgentName}
                  onChange={(e) => setFirstAgentName(e.target.value)}
                  placeholder="例: アシスタント"
                  className="w-full px-3 py-2.5 rounded text-[13px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] outline-none"
                />
              </div>
              <div className="bg-[#252526] border border-[#3e3e42] rounded p-4 text-[12px] text-[#969696] space-y-2">
                <p className="text-[#cccccc] font-medium">このエージェントができること:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>自然言語での業務依頼の受付</li>
                  <li>要件の深掘り（Design Interview）</li>
                  <li>実行計画の策定</li>
                  <li>タスクの実行と品質確認</li>
                  <li>承認が必要な操作の申請</li>
                </ul>
                <p className="text-[#6a6a6a] mt-2">
                  ※ 外部送信、公開、課金などの重要操作は必ずあなたの承認が必要です
                </p>
              </div>
            </div>
          )}

          {currentStep === "complete" && (
            <div className="flex flex-col items-center gap-6 text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center bg-[#16825d]">
                <Sparkles size={32} color="#fff" />
              </div>
              <h2 className="text-2xl font-semibold text-[#cccccc]">
                セットアップ完了！
              </h2>
              <p className="text-[14px] text-[#969696] leading-relaxed max-w-[450px]">
                AI組織の準備が整いました。
                <br />
                <br />
                ダッシュボードの入力欄に自然言語で業務を依頼してみましょう。
                AIチームが計画を立て、あなたの承認のもとで実行します。
              </p>
              <div className="bg-[#252526] border border-[#3e3e42] rounded p-4 text-[12px] text-[#969696] text-left max-w-[400px] w-full">
                <p className="text-[#cccccc] font-medium mb-2">試してみましょう:</p>
                <ul className="space-y-2">
                  <li>「競合分析をして、レポートにまとめて」</li>
                  <li>「今月のSNS投稿計画を作って」</li>
                  <li>「このプロジェクトの進捗を整理して」</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8">
          {stepIndex > 0 && currentStep !== "complete" ? (
            <button
              onClick={prev}
              className="flex items-center gap-1 px-4 py-2 rounded text-[13px] text-[#cccccc] border border-[#3e3e42] hover:bg-[#2a2d2e]"
            >
              <ChevronLeft size={16} />
              戻る
            </button>
          ) : (
            <div />
          )}

          {currentStep === "complete" ? (
            <button
              onClick={finishSetup}
              className="flex items-center gap-2 px-6 py-2.5 rounded text-[13px] font-medium bg-[#007acc] text-white"
            >
              <Sparkles size={16} />
              ダッシュボードへ
            </button>
          ) : (
            <button
              onClick={next}
              className="flex items-center gap-1 px-6 py-2.5 rounded text-[13px] font-medium bg-[#007acc] text-white"
            >
              次へ
              <ChevronRight size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
