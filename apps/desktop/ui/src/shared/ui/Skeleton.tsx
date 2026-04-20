import type { CSSProperties, HTMLAttributes } from 'react'

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  /** Width in CSS units (default '100%'). */
  w?: string
  /** Height in CSS units (default '14px' — matches --text-md). */
  h?: string
  /** Visual variant: flat rectangle, rounded pill, or circular (for avatars). */
  variant?: 'rect' | 'pill' | 'circle'
}

/**
 * Content placeholder that fills the same box as the real component.
 *
 * Use instead of a spinner for any list / table / dashboard cell that has a
 * predictable shape — the shimmer keeps the layout from jumping when real
 * data arrives. Honours ``prefers-reduced-motion`` via the global CSS
 * override (the shimmer collapses to a static fill).
 */
export function Skeleton({
  w = '100%',
  h = '14px',
  variant = 'rect',
  style,
  className = '',
  ...rest
}: SkeletonProps) {
  const radius =
    variant === 'circle' ? '50%' : variant === 'pill' ? '999px' : 'var(--radius-sm)'
  const combined: CSSProperties = {
    width: w,
    height: h,
    borderRadius: radius,
    background:
      'linear-gradient(90deg, var(--bg-hover) 0%, var(--bg-raised) 50%, var(--bg-hover) 100%)',
    backgroundSize: '200% 100%',
    animation: 'skeleton-shimmer 1.2s var(--motion-ease) infinite',
    ...style,
  }
  return (
    <div
      aria-hidden="true"
      className={className}
      style={combined}
      {...rest}
    />
  )
}
