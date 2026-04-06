import { Workflow } from "lucide-react"

interface LogoProps {
  size?: number
  className?: string
}

/**
 * Logo using Lucide Workflow icon — no custom SVG.
 * Color: VSCode accent #007ACC.
 */
export function Logo({ size = 32, className }: LogoProps) {
  return (
    <div className={`flex items-center gap-2.5 ${className ?? ""}`}>
      <Workflow size={size} color="#007ACC" strokeWidth={1.8} />
      <span
        style={{
          fontSize: size * 0.6,
          fontWeight: 700,
          color: "#D4D4D4",
          fontFamily: "var(--font-sans)",
          letterSpacing: "-0.02em",
        }}
      >
        Zero-Employee Orchestrator
      </span>
    </div>
  )
}

/**
 * Small logo mark — Lucide Workflow icon only.
 */
export function LogoMark({ size = 16, className }: LogoProps) {
  return <Workflow size={size} color="#007ACC" strokeWidth={1.8} className={className} />
}
