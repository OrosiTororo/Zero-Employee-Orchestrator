import { useId } from "react"

interface LogoProps {
  size?: number
  className?: string
}

export function Logo({ size = 32, className }: LogoProps) {
  const id = useId()
  const bgId = `${id}-logo-bg`
  const glowId = `${id}-logo-glow`

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 256 256"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id={bgId} x1="0" y1="0" x2="256" y2="256" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0078d4" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
        <linearGradient id={glowId} x1="128" y1="40" x2="128" y2="216" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffffff" stopOpacity="1" />
          <stop offset="1" stopColor="#e0e7ff" stopOpacity="0.85" />
        </linearGradient>
      </defs>
      {/* Rounded background */}
      <rect x="8" y="8" width="240" height="240" rx="52" fill={`url(#${bgId})`} />
      {/* Orchestration nodes — triangle network */}
      <line x1="128" y1="72" x2="76" y2="180" stroke={`url(#${glowId})`} strokeWidth="7" strokeLinecap="round" />
      <line x1="128" y1="72" x2="180" y2="180" stroke={`url(#${glowId})`} strokeWidth="7" strokeLinecap="round" />
      <line x1="76" y1="180" x2="180" y2="180" stroke={`url(#${glowId})`} strokeWidth="7" strokeLinecap="round" />
      {/* Center dot connecting all */}
      <circle cx="128" cy="132" r="12" fill={`url(#${glowId})`} />
      <line x1="128" y1="72" x2="128" y2="120" stroke={`url(#${glowId})`} strokeWidth="5" strokeLinecap="round" />
      <line x1="128" y1="144" x2="76" y2="180" stroke={`url(#${glowId})`} strokeWidth="5" strokeLinecap="round" />
      <line x1="128" y1="144" x2="180" y2="180" stroke={`url(#${glowId})`} strokeWidth="5" strokeLinecap="round" />
      {/* Outer nodes */}
      <circle cx="128" cy="68" r="18" fill={`url(#${glowId})`} />
      <circle cx="72" cy="184" r="18" fill={`url(#${glowId})`} />
      <circle cx="184" cy="184" r="18" fill={`url(#${glowId})`} />
    </svg>
  )
}

export function LogoMark({ size = 16, className }: LogoProps) {
  const id = useId()
  const bgId = `${id}-mark-bg`

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 256 256"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id={bgId} x1="0" y1="0" x2="256" y2="256" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0078d4" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
      <rect x="8" y="8" width="240" height="240" rx="52" fill={`url(#${bgId})`} />
      <line x1="128" y1="72" x2="76" y2="180" stroke="white" strokeWidth="7" strokeLinecap="round" />
      <line x1="128" y1="72" x2="180" y2="180" stroke="white" strokeWidth="7" strokeLinecap="round" />
      <line x1="76" y1="180" x2="180" y2="180" stroke="white" strokeWidth="7" strokeLinecap="round" />
      <circle cx="128" cy="132" r="12" fill="white" />
      <line x1="128" y1="72" x2="128" y2="120" stroke="white" strokeWidth="5" strokeLinecap="round" />
      <line x1="128" y1="144" x2="76" y2="180" stroke="white" strokeWidth="5" strokeLinecap="round" />
      <line x1="128" y1="144" x2="180" y2="180" stroke="white" strokeWidth="5" strokeLinecap="round" />
      <circle cx="128" cy="68" r="18" fill="white" />
      <circle cx="72" cy="184" r="18" fill="white" />
      <circle cx="184" cy="184" r="18" fill="white" />
    </svg>
  )
}
