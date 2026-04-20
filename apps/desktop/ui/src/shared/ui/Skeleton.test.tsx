import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton } from './Skeleton'

describe('Skeleton', () => {
  it('is hidden from assistive tech by default', () => {
    const { container } = render(<Skeleton />)
    const el = container.firstChild as HTMLElement
    expect(el.getAttribute('aria-hidden')).toBe('true')
  })

  it('applies dimension tokens inline', () => {
    const { container } = render(<Skeleton w="240px" h="28px" />)
    const el = container.firstChild as HTMLElement
    expect(el.style.width).toBe('240px')
    expect(el.style.height).toBe('28px')
  })

  it('renders a circle variant with 50% border radius', () => {
    const { container } = render(<Skeleton variant="circle" w="32px" h="32px" />)
    const el = container.firstChild as HTMLElement
    expect(el.style.borderRadius).toBe('50%')
  })

  it('renders a pill variant with fully rounded radius', () => {
    const { container } = render(<Skeleton variant="pill" />)
    const el = container.firstChild as HTMLElement
    expect(el.style.borderRadius).toBe('999px')
  })

  it('accepts additional className + style props', () => {
    const { container } = render(
      <Skeleton className="test-class" style={{ opacity: 0.5 }} />,
    )
    const el = container.firstChild as HTMLElement
    expect(el.classList.contains('test-class')).toBe(true)
    expect(el.style.opacity).toBe('0.5')
  })
})
