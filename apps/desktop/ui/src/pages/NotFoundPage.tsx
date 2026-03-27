import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
      <div className="text-center">
        <h1 className="text-[48px] font-bold text-[var(--text-primary)] mb-2">404</h1>
        <p className="text-[14px] text-[var(--text-secondary)] mb-6">
          Page not found
        </p>
        <Link
          to="/"
          className="px-4 py-2 text-[13px] rounded-md bg-[var(--accent)] text-white hover:opacity-90 transition-opacity"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  )
}
