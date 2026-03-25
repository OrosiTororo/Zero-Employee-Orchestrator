import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { MessageSquare, Send, Check, ArrowRight, Loader2 } from "lucide-react"
import { api } from "../shared/api/client"

interface Question {
  question: string
  category: string
  required: boolean
  answered: boolean
  answer: string
}

const defaultQuestions: Question[] = [
  {
    question: "この業務の最終的な目的は何ですか？",
    category: "objective",
    required: true,
    answered: false,
    answer: "",
  },
  {
    question: "守るべき制約条件はありますか？（予算、期限、品質基準など）",
    category: "constraint",
    required: true,
    answered: false,
    answer: "",
  },
  {
    question: "完了条件（受け入れ基準）は何ですか？",
    category: "acceptance",
    required: true,
    answered: false,
    answer: "",
  },
  {
    question: "想定されるリスクや注意点はありますか？",
    category: "risk",
    required: false,
    answered: false,
    answer: "",
  },
  {
    question: "優先順位はどの程度ですか？（高/中/低）",
    category: "priority",
    required: true,
    answered: false,
    answer: "",
  },
  {
    question: "外部サービスへの接続や送信は必要ですか？",
    category: "constraint",
    required: true,
    answered: false,
    answer: "",
  },
  {
    question: "人間の承認が必要な工程はありますか？",
    category: "acceptance",
    required: true,
    answered: false,
    answer: "",
  },
]

export function InterviewPage() {
  const { id: ticketId } = useParams()
  const navigate = useNavigate()
  const [questions, setQuestions] = useState<Question[]>(defaultQuestions)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [inputValue, setInputValue] = useState("")

  const current = questions[currentIndex]
  const answeredCount = questions.filter((q) => q.answered).length
  const requiredRemaining = questions.filter(
    (q) => q.required && !q.answered
  ).length

  const handleAnswer = () => {
    if (!inputValue.trim()) return
    const updated = [...questions]
    updated[currentIndex] = {
      ...updated[currentIndex],
      answered: true,
      answer: inputValue,
    }
    setQuestions(updated)
    setInputValue("")

    // Move to next unanswered question
    const nextUnanswered = updated.findIndex(
      (q, i) => i > currentIndex && !q.answered
    )
    if (nextUnanswered >= 0) {
      setCurrentIndex(nextUnanswered)
    }
  }

  const [submitting, setSubmitting] = useState(false)

  const handleComplete = async () => {
    setSubmitting(true)
    try {
      const companyId = localStorage.getItem("company_id") || ""
      // インタビュー回答をバックエンドに保存
      const answers = questions.reduce(
        (acc, q) => {
          if (q.answered) {
            acc[q.category] = q.answer
          }
          return acc
        },
        {} as Record<string, string>
      )
      await api.post(`/companies/${companyId}/tickets/${ticketId}/interview/complete`, {
        answers,
      })
      // 仕様生成をトリガー
      try {
        await api.post(`/companies/${companyId}/tickets/${ticketId}/generate-spec`, {})
      } catch {
        // spec 生成失敗は非致命的
      }
    } catch (e) {
      console.error("Interview save failed:", e)
    } finally {
      setSubmitting(false)
    }
    navigate(`/tickets/${ticketId}/spec-plan`)
  }

  return (
    <div className="p-6 max-w-[800px] mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <MessageSquare size={24} className="text-[#007acc]" />
        <div>
          <h1 className="text-lg font-semibold text-[#cccccc]">
            Design Interview
          </h1>
          <p className="text-[12px] text-[#6a6a6a]">
            要件を深掘りして、実行計画の基礎を作ります
          </p>
        </div>
      </div>

      {/* Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-[12px] text-[#6a6a6a] mb-2">
          <span>
            回答済み: {answeredCount} / {questions.length}
          </span>
          <span>
            {requiredRemaining > 0
              ? `必須残り: ${requiredRemaining}件`
              : "必須項目完了"}
          </span>
        </div>
        <div className="h-1.5 bg-[#3e3e42] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#007acc] rounded-full transition-all"
            style={{
              width: `${(answeredCount / questions.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Question List */}
      <div className="flex flex-col gap-3 mb-6">
        {questions.map((q, i) => (
          <div
            key={i}
            onClick={() => setCurrentIndex(i)}
            className="flex items-start gap-3 p-3 rounded border cursor-pointer transition-colors"
            style={{
              borderColor: i === currentIndex ? "#007acc" : "#3e3e42",
              background: i === currentIndex ? "#007acc10" : "transparent",
            }}
          >
            <div
              className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
              style={{
                background: q.answered ? "#16825d" : "#3e3e42",
              }}
            >
              {q.answered ? (
                <Check size={12} color="#fff" />
              ) : (
                <span className="text-[10px] text-[#6a6a6a]">{i + 1}</span>
              )}
            </div>
            <div className="flex-1">
              <p className="text-[13px] text-[#cccccc]">
                {q.question}
                {q.required && (
                  <span className="text-[#f44747] ml-1">*</span>
                )}
              </p>
              {q.answered && (
                <p className="text-[12px] text-[#969696] mt-1">{q.answer}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Current Question Input */}
      {current && !current.answered && (
        <div className="flex gap-2 mb-6">
          <input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAnswer()}
            placeholder={`Q${currentIndex + 1}: ${current.question}`}
            className="flex-1 px-3 py-2.5 rounded text-[13px] bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc] outline-none"
          />
          <button
            onClick={handleAnswer}
            className="px-4 py-2.5 rounded bg-[#007acc] text-white"
          >
            <Send size={16} />
          </button>
        </div>
      )}

      {/* Complete Button */}
      {requiredRemaining === 0 && (
        <button
          onClick={handleComplete}
          disabled={submitting}
          className="flex items-center justify-center gap-2 w-full px-6 py-3 rounded text-[14px] font-medium bg-[#16825d] text-white disabled:opacity-50"
        >
          {submitting ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
          {submitting ? "保存中..." : "Spec / Plan の生成に進む"}
        </button>
      )}
    </div>
  )
}
