import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { MessageSquare, Send, Check, ArrowRight, Loader2 } from "lucide-react"
import { api } from "../shared/api/client"
import { useT } from "@/shared/i18n"
import { useToastStore } from "@/shared/ui/ErrorToast"

interface Question {
  question: string
  category: string
  required: boolean
  answered: boolean
  answer: string
}

function getDefaultQuestions(t: Record<string, any>): Question[] {
  return [
    {
      question: t.interview?.qObjective ?? "What is the ultimate goal of this task?",
      category: "objective",
      required: true,
      answered: false,
      answer: "",
    },
    {
      question: t.interview?.qConstraints ?? "Are there any constraints to follow? (budget, deadline, quality standards, etc.)",
      category: "constraint",
      required: true,
      answered: false,
      answer: "",
    },
    {
      question: t.interview?.qAcceptance ?? "What are the completion criteria (acceptance criteria)?",
      category: "acceptance",
      required: true,
      answered: false,
      answer: "",
    },
    {
      question: t.interview?.qRisk ?? "Are there any anticipated risks or concerns?",
      category: "risk",
      required: false,
      answered: false,
      answer: "",
    },
    {
      question: t.interview?.qPriority ?? "What is the priority level? (High / Medium / Low)",
      category: "priority",
      required: true,
      answered: false,
      answer: "",
    },
    {
      question: t.interview?.qExternalService ?? "Is connection or transmission to external services required?",
      category: "constraint",
      required: true,
      answered: false,
      answer: "",
    },
    {
      question: t.interview?.qApproval ?? "Are there any steps that require human approval?",
      category: "acceptance",
      required: true,
      answered: false,
      answer: "",
    },
  ]
}

export function InterviewPage() {
  const { id: ticketId } = useParams()
  const navigate = useNavigate()
  const t = useT()
  const addToast = useToastStore((s) => s.addToast)
  const [questions, setQuestions] = useState<Question[]>(() => getDefaultQuestions(t))
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
      // Save interview answers to backend
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
      // Trigger spec generation
      try {
        await api.post(`/companies/${companyId}/tickets/${ticketId}/generate-spec`, {})
      } catch {
        // Spec generation failure is non-fatal
      }
    } catch (e) {
      addToast((t as Record<string, Record<string, string>>).errors?.interviewSaveFailed ?? "Could not save interview answers.")
    } finally {
      setSubmitting(false)
    }
    navigate(`/tickets/${ticketId}/spec-plan`)
  }

  return (
    <div className="p-6 max-w-[800px] mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <MessageSquare size={24} className="text-[var(--accent)]" />
        <div>
          <h1 className="text-lg font-semibold text-[var(--text-primary)]">
            {t.interview?.title ?? "Design Interview"}
          </h1>
          <p className="text-[12px] text-[var(--text-muted)]">
            {t.interview?.subtitle ?? "Deep-dive into requirements to build a foundation for the execution plan"}
          </p>
        </div>
      </div>

      {/* Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-[12px] text-[var(--text-muted)] mb-2">
          <span>
            {t.interview?.answered ?? "Answered"}: {answeredCount} / {questions.length}
          </span>
          <span>
            {requiredRemaining > 0
              ? `${t.interview?.requiredRemaining ?? "Required remaining"}: ${requiredRemaining}`
              : (t.interview?.requiredComplete ?? "All required complete")}
          </span>
        </div>
        <div className="h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--accent)] rounded-full transition-all"
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
              borderColor: i === currentIndex ? "var(--accent)" : "var(--border)",
              background: i === currentIndex ? "color-mix(in srgb, var(--accent) 6%, transparent)" : "transparent",
            }}
          >
            <div
              className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
              style={{
                background: q.answered ? "var(--success-fg)" : "var(--border)",
              }}
            >
              {q.answered ? (
                <Check size={12} color="#fff" />
              ) : (
                <span className="text-[10px] text-[var(--text-muted)]">{i + 1}</span>
              )}
            </div>
            <div className="flex-1">
              <p className="text-[13px] text-[var(--text-primary)]">
                {q.question}
                {q.required && (
                  <span className="text-[var(--error)] ml-1">*</span>
                )}
              </p>
              {q.answered && (
                <p className="text-[12px] text-[var(--text-muted)] mt-1">{q.answer}</p>
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
            className="flex-1 px-3 py-2.5 rounded text-[13px] bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] outline-none"
          />
          <button
            onClick={handleAnswer}
            className="px-4 py-2.5 rounded bg-[var(--accent)] text-white"
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
          className="flex items-center justify-center gap-2 w-full px-6 py-3 rounded text-[14px] font-medium bg-[var(--success-fg)] text-white disabled:opacity-50"
        >
          {submitting ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
          {submitting ? (t.interview?.saving ?? "Saving...") : (t.interview?.proceedToSpec ?? "Proceed to Spec / Plan generation")}
        </button>
      )}
    </div>
  )
}
