import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastContainer, useToastStore } from './ErrorToast'

describe('ErrorToast', () => {
  beforeEach(() => {
    // Reset store between tests
    useToastStore.setState({ toasts: [] })
  })

  it('renders nothing when no toasts', () => {
    const { container } = render(<ToastContainer />)
    expect(container.innerHTML).toBe('')
  })

  it('renders toast message when added via store', () => {
    useToastStore.getState().addToast('Something went wrong', 'error')
    render(<ToastContainer />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders multiple toasts', () => {
    useToastStore.getState().addToast('Error 1', 'error')
    useToastStore.getState().addToast('Warning 1', 'warning')
    render(<ToastContainer />)
    expect(screen.getByText('Error 1')).toBeInTheDocument()
    expect(screen.getByText('Warning 1')).toBeInTheDocument()
  })

  it('dismisses toast on button click', async () => {
    const user = userEvent.setup()
    useToastStore.getState().addToast('Dismissable', 'error')
    render(<ToastContainer />)

    expect(screen.getByText('Dismissable')).toBeInTheDocument()
    const dismissBtn = screen.getByLabelText('Dismiss')
    await user.click(dismissBtn)
    expect(screen.queryByText('Dismissable')).not.toBeInTheDocument()
  })

  it('limits to 5 toasts', () => {
    const store = useToastStore.getState()
    for (let i = 0; i < 7; i++) {
      store.addToast(`Toast ${i}`)
    }
    // Store keeps max 5 (slice -4 + new = 5)
    expect(useToastStore.getState().toasts.length).toBeLessThanOrEqual(5)
  })
})
