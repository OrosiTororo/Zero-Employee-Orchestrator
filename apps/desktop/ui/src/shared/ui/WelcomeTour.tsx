/**
 * Welcome Tour — 3-step overlay for first-time users.
 *
 * Inspired by Claude Code's step-by-step quickstart and
 * Smashing Magazine's agentic UX progressive disclosure pattern.
 *
 * Shows once per user (localStorage flag). Dismissible at any step.
 */
import { useState } from "react"
import { LayoutDashboard, Activity, Gauge, X, ArrowRight } from "lucide-react"

const STORAGE_KEY = "zeo_welcome_tour_completed"

interface TourStep {
  icon: React.ElementType
  title: string
  description: string
}

const STEPS: TourStep[] = [
  {
    icon: LayoutDashboard,
    title: "Describe tasks in natural language",
    description:
      "The Dashboard is your starting point. Type what you need — ZEO's AI agents will plan, execute, and verify the work. No menus to navigate, just describe the task.",
  },
  {
    icon: Activity,
    title: "Monitor your AI agents",
    description:
      "The Monitor page shows live execution traces, approval queues, and agent status. Every AI action is logged with full reasoning traces for transparency.",
  },
  {
    icon: Gauge,
    title: "Control AI autonomy",
    description:
      "The Autonomy Dial in the status bar lets you set how independently AI acts: Observe (watch only), Assist (suggestions), Semi-Auto (execute after approval), or Autonomous (auto-execute safe tasks).",
  },
]

export function WelcomeTour() {
  const [step, setStep] = useState(0)
  const [visible, setVisible] = useState(() => {
    return !localStorage.getItem(STORAGE_KEY)
  })

  if (!visible) return null

  const dismiss = () => {
    localStorage.setItem(STORAGE_KEY, "1")
    setVisible(false)
  }

  const next = () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1)
    } else {
      dismiss()
    }
  }

  const current = STEPS[step]

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
      <div
        className="relative w-[420px] rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] shadow-xl"
        style={{ boxShadow: "var(--shadow-modal)" }}
      >
        {/* Close button */}
        <button
          onClick={dismiss}
          className="absolute top-3 right-3 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          aria-label="Close tour"
        >
          <X size={16} />
        </button>

        {/* Content */}
        <div className="px-6 pt-6 pb-4">
          {/* Step indicator */}
          <div className="flex items-center gap-1 mb-4">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className="h-[3px] flex-1 rounded-full transition-colors"
                style={{
                  background: i <= step ? "var(--accent)" : "var(--border)",
                }}
              />
            ))}
          </div>

          {/* Icon */}
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
            style={{ background: "var(--accent-subtle)" }}
          >
            <current.icon size={20} className="text-[var(--accent)]" />
          </div>

          {/* Text */}
          <h2 className="text-[15px] font-semibold text-[var(--text-primary)] mb-2">
            {current.title}
          </h2>
          <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
            {current.description}
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-[var(--border)]">
          <button
            onClick={dismiss}
            className="text-[12px] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            Skip tour
          </button>
          <button
            onClick={next}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded text-[12px] font-medium text-white"
            style={{ background: "var(--accent)" }}
          >
            {step < STEPS.length - 1 ? (
              <>
                Next <ArrowRight size={12} />
              </>
            ) : (
              "Get started"
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
