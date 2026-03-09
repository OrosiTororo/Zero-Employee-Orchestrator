import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "@/shared/hooks/use-auth"
import { LogIn, UserPlus, Mail, Lock, User, ArrowRight } from "lucide-react"
import { Logo } from "@/shared/ui/Logo"
import { useT } from "@/shared/i18n"
import { api } from "@/shared/api/client"

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
    navigate("/", { replace: true })
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
      const res = await api.post<{ access_token: string }>("/auth/login", {
        email,
        password,
      })
      setToken(res.access_token)
      navigate("/")
    } catch (e: any) {
      setError(e.message || t.auth.loginFailed)
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
    } catch (e: any) {
      setError(e.message || t.auth.registerFailed)
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleAuth = async () => {
    setLoading(true)
    setError("")
    try {
      const res = await api.get<{ url: string }>("/auth/google/authorize")
      window.location.href = res.url
    } catch {
      setError(t.auth.loginFailed)
      setLoading(false)
    }
  }

  const inputClass =
    "w-full pl-10 pr-4 py-2.5 rounded-md text-[13px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] placeholder:text-[var(--text-muted)]"

  return (
    <div className="h-screen w-screen flex bg-[var(--bg-base)]">
      {/* Left brand panel */}
      <div
        className="hidden lg:flex flex-col justify-between w-[420px] shrink-0 p-10"
        style={{
          background: "linear-gradient(160deg, #0078d4 0%, #5b21b6 100%)",
        }}
      >
        <div>
          <Logo size={48} />
          <h1 className="mt-8 text-[28px] font-bold leading-tight text-white">
            Zero-Employee
            <br />
            Orchestrator
          </h1>
          <p className="mt-3 text-[14px] leading-relaxed text-white/70">
            {t.common.appTagline}
          </p>
        </div>

        <div className="space-y-6">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 w-8 h-8 rounded-md bg-white/15 flex items-center justify-center shrink-0">
              <ArrowRight size={16} className="text-white/90" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-white/90">
                {t.brand.feature1Title}
              </p>
              <p className="text-[12px] text-white/50 mt-0.5">
                {t.brand.feature1Desc}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 w-8 h-8 rounded-md bg-white/15 flex items-center justify-center shrink-0">
              <ArrowRight size={16} className="text-white/90" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-white/90">
                {t.brand.feature2Title}
              </p>
              <p className="text-[12px] text-white/50 mt-0.5">
                {t.brand.feature2Desc}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 w-8 h-8 rounded-md bg-white/15 flex items-center justify-center shrink-0">
              <ArrowRight size={16} className="text-white/90" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-white/90">
                {t.brand.feature3Title}
              </p>
              <p className="text-[12px] text-white/50 mt-0.5">
                {t.brand.feature3Desc}
              </p>
            </div>
          </div>
        </div>

        <p className="text-[11px] text-white/30">{t.common.version}</p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-[380px]">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <Logo size={36} />
            <div>
              <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
                {t.common.appName}
              </h1>
              <p className="text-[11px] text-[var(--text-muted)]">
                {t.common.appTagline}
              </p>
            </div>
          </div>

          <h2 className="text-[20px] font-semibold text-[var(--text-primary)] mb-1">
            {mode === "login" ? t.auth.loginTitle : t.auth.registerTitle}
          </h2>
          <p className="text-[13px] text-[var(--text-secondary)] mb-6">
            {mode === "login" ? t.auth.loginSubtitle : t.auth.registerSubtitle}
          </p>

          {/* Google OAuth */}
          <button
            onClick={handleGoogleAuth}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-md text-[13px] font-medium border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors mb-4"
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
          <div className="flex flex-col gap-3.5">
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
              <div className="flex items-center gap-2 px-3 py-2 rounded-md text-[12px] text-[var(--error)] bg-[#f4474712] border border-[#f4474730]">
                {error}
              </div>
            )}

            <button
              onClick={mode === "login" ? handleLogin : handleRegister}
              disabled={loading}
              className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-md text-[13px] font-medium text-white"
              style={{
                background: loading
                  ? "var(--bg-active)"
                  : "linear-gradient(135deg, #0078d4, #6d28d9)",
              }}
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

          {/* Toggle */}
          <div className="mt-6 pt-6 border-t border-[var(--border)] text-center">
            <p className="text-[12px] text-[var(--text-muted)]">
              {mode === "login" ? (
                <>
                  {t.auth.noAccount}{" "}
                  <button
                    onClick={() => {
                      setMode("register")
                      setError("")
                    }}
                    className="text-[var(--accent)] hover:underline font-medium"
                  >
                    {t.auth.register}
                  </button>
                </>
              ) : (
                <>
                  {t.auth.hasAccount}{" "}
                  <button
                    onClick={() => {
                      setMode("login")
                      setError("")
                    }}
                    className="text-[var(--accent)] hover:underline font-medium"
                  >
                    {t.auth.login}
                  </button>
                </>
              )}
            </p>
            <p className="text-[11px] text-[var(--text-muted)] mt-2">
              {t.auth.apiKeyNote}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
