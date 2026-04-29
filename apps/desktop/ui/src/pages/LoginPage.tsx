import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "@/shared/hooks/use-auth"
import { LogIn, UserPlus, Mail, Lock, User, ArrowRight } from "lucide-react"
import { LogoMark } from "@/shared/ui/Logo"
import { useT } from "@/shared/i18n"
import { api, NetworkError } from "@/shared/api/client"

function GoogleIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  )
}

export function LoginPage() {
  const { setToken, authenticated } = useAuthStore()
  const navigate = useNavigate()
  const t = useT()
  const [mode, setMode] = useState<"login" | "register">("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  if (authenticated) {
    const { setupCompleted } = useAuthStore.getState()
    navigate(setupCompleted ? "/" : "/setup", { replace: true })
    return null
  }

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      setError(t.auth.emailPasswordRequired)
      return
    }
    setLoading(true)
    setError("")
    try {
      const res = await api.post<{ access_token: string; setup_completed?: boolean }>("/auth/login", {
        email,
        password,
      })
      setToken(res.access_token)
      if (res.setup_completed) {
        useAuthStore.getState().setSetupCompleted()
        navigate("/")
      } else {
        navigate("/setup")
      }
    } catch (e: unknown) {
      if (e instanceof NetworkError) {
        setError(t.auth.connectionFailed)
      } else if (e instanceof Error) {
        setError(e.message || t.auth.loginFailed)
      } else {
        setError(t.auth.loginFailed)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!email.trim() || !password.trim() || !displayName.trim()) {
      setError(t.auth.allFieldsRequired)
      return
    }
    setLoading(true)
    setError("")
    try {
      const res = await api.post<{ access_token: string }>("/auth/register", {
        email,
        password,
        display_name: displayName,
      })
      setToken(res.access_token)
      navigate("/setup")
    } catch (e: unknown) {
      if (e instanceof NetworkError) {
        setError(t.auth.connectionFailed)
      } else if (e instanceof Error) {
        setError(e.message || t.auth.registerFailed)
      } else {
        setError(t.auth.registerFailed)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleAuth = async () => {
    setLoading(true)
    setError("")
    try {
      const res = await api.get<{ url: string; state: string }>("/auth/google/authorize")
      window.open(res.url, "_blank", "noopener")

      const state = res.state
      const maxAttempts = 120
      for (let i = 0; i < maxAttempts; i++) {
        await new Promise((r) => setTimeout(r, 1000))
        try {
          const poll = await api.get<{
            status: string
            access_token?: string
            setup_completed?: boolean
          }>(`/auth/google/poll?state=${state}`)
          if (poll.status === "complete" && poll.access_token) {
            setToken(poll.access_token)
            if (poll.setup_completed) {
              useAuthStore.getState().setSetupCompleted()
              navigate("/")
            } else {
              navigate("/setup")
            }
            return
          }
        } catch {
          break
        }
      }
      setError(t.auth.googleOAuthTimeout)
    } catch (e: unknown) {
      if (e instanceof NetworkError) {
        setError(t.auth.connectionFailed)
      } else if (e instanceof Error && e.message.includes("not configured")) {
        setError(t.auth.googleOAuthNotConfigured)
      } else {
        setError(t.auth.googleOAuthNotReady)
      }
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    "w-full pl-10 pr-4 py-2.5 rounded text-[13px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] placeholder:text-[var(--text-muted)]"

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
      <div className="w-full max-w-[380px] px-6">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-8">
          <LogoMark size={28} />
          <div>
            <h1 className="text-[15px] font-semibold text-[var(--text-primary)]">
              {t.common.appName}
            </h1>
            <p className="text-[11px] text-[var(--text-muted)]">
              {t.common.appTagline}
            </p>
          </div>
        </div>

        <h2 className="text-[18px] font-semibold text-[var(--text-primary)] mb-1">
          {mode === "login" ? t.auth.loginTitle : t.auth.registerTitle}
        </h2>
        <p className="text-[12px] text-[var(--text-secondary)] mb-5">
          {mode === "login" ? t.auth.loginSubtitle : t.auth.registerSubtitle}
        </p>

        {/* Google OAuth */}
        <button
          onClick={handleGoogleAuth}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 rounded text-[13px] font-medium border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors mb-4"
        >
          <GoogleIcon size={18} />
          {t.auth.continueWithGoogle}
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider">
            {t.auth.orDivider}
          </span>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        {/* Form */}
        <div className="flex flex-col gap-3">
          {mode === "register" && (
            <div className="relative">
              <User
                size={15}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
              />
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t.auth.displayName}
                className={inputClass}
              />
            </div>
          )}

          <div className="relative">
            <Mail
              size={15}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
            />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t.auth.email}
              className={inputClass}
            />
          </div>

          <div className="relative">
            <Lock
              size={15}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" &&
                (mode === "login" ? handleLogin() : handleRegister())
              }
              placeholder={t.auth.password}
              className={inputClass}
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 px-3 py-2 rounded text-[12px] text-[var(--error)] bg-[var(--bg-surface)] border border-[var(--border)] animate-slide-in">
              {error}
            </div>
          )}

          <button
            onClick={mode === "login" ? handleLogin : handleRegister}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-6 py-2.5 rounded text-[13px] font-medium text-[var(--accent-fg)] disabled:opacity-50"
            style={{ background: loading ? "var(--bg-active)" : "var(--accent)" }}
          >
            {mode === "login" ? (
              <>
                <LogIn size={15} />
                {loading ? t.auth.loggingIn : t.auth.loginButton}
              </>
            ) : (
              <>
                <UserPlus size={15} />
                {loading ? t.auth.registering : t.auth.registerButton}
              </>
            )}
          </button>
        </div>

        {/* Anonymous session */}
        <div className="mt-4">
          <button
            onClick={async () => {
              setLoading(true)
              setError("")
              try {
                const { startAnonymous } = useAuthStore.getState()
                await startAnonymous()
                navigate("/setup")
              } catch (e: unknown) {
                if (e instanceof NetworkError) {
                  setError(t.auth.connectionFailed)
                } else if (e instanceof Error) {
                  setError(e.message || t.auth.anonymousFailed)
                } else {
                  setError(t.auth.anonymousFailed)
                }
              } finally {
                setLoading(false)
              }
            }}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded text-[12px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors disabled:opacity-50"
          >
            <ArrowRight size={13} />
            {t.auth.startWithoutLogin}
          </button>
          <p className="text-[10px] text-[var(--text-muted)] mt-1 text-center">
            {t.auth.startWithoutLoginNote}
          </p>
        </div>

        {/* Toggle */}
        <div className="mt-6 pt-5 border-t border-[var(--border)] text-center">
          <p className="text-[12px] text-[var(--text-muted)]">
            {mode === "login" ? (
              <>
                {t.auth.noAccount}{" "}
                <button
                  onClick={() => { setMode("register"); setError("") }}
                  className="text-[var(--accent)] hover:underline font-medium"
                >
                  {t.auth.register}
                </button>
              </>
            ) : (
              <>
                {t.auth.hasAccount}{" "}
                <button
                  onClick={() => { setMode("login"); setError("") }}
                  className="text-[var(--accent)] hover:underline font-medium"
                >
                  {t.auth.login}
                </button>
              </>
            )}
          </p>
        </div>

        {/* Footnote */}
        <p className="text-[11px] text-[var(--text-muted)] mt-4 text-center leading-relaxed">
          {t.auth.apiKeyNote}
        </p>
      </div>
    </div>
  )
}
