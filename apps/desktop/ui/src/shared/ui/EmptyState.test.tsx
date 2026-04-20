import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { EmptyState } from './EmptyState'

describe('EmptyState', () => {
  it('renders only a title when no extras are supplied', () => {
    render(<EmptyState title="Nothing here yet" />)
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Nothing here yet')).toBeInTheDocument()
  })

  it('renders description and icon when provided', () => {
    render(
      <EmptyState
        title="No tickets"
        description="Drop a spec to get started."
        icon={<span aria-hidden>📋</span>}
      />,
    )
    expect(screen.getByText('Drop a spec to get started.')).toBeInTheDocument()
  })

  it('fires the primary action handler on click', () => {
    const handler = vi.fn()
    render(
      <EmptyState
        title="Quiet queue"
        action={{ label: 'Create ticket', onClick: handler }}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Create ticket' }))
    expect(handler).toHaveBeenCalledOnce()
  })

  it('fires the secondary action handler on click', () => {
    const primary = vi.fn()
    const secondary = vi.fn()
    render(
      <EmptyState
        title="Quiet queue"
        action={{ label: 'Primary', onClick: primary }}
        secondaryAction={{ label: 'Learn more', onClick: secondary }}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Learn more' }))
    expect(secondary).toHaveBeenCalledOnce()
    expect(primary).not.toHaveBeenCalled()
  })

  it('uses polite aria-live so screen readers announce the state', () => {
    render(<EmptyState title="Nothing" />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')
  })
})
