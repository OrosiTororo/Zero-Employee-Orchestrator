import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] Uncaught error:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
          <div className="max-w-md mx-auto p-6 text-center">
            <div className="text-[32px] mb-4">!</div>
            <h1 className="text-[18px] font-semibold text-[var(--text-primary)] mb-2">
              Something went wrong
            </h1>
            <p className="text-[13px] text-[var(--text-secondary)] mb-4">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.href = '/'
              }}
              className="px-4 py-2 text-[13px] rounded-md bg-[var(--accent)] text-white hover:opacity-90 transition-opacity"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
