import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "@/shared/hooks/use-auth"
import { LogIn, UserPlus, Mail, Lock, User, ArrowRight } from "lucide-react"
import { Logo } from "@/shared/ui/Logo"
import { api } from "@/shared/api/client"

export function LoginPage() {
  const { setToken, authenticated } = useAuthStore()
  const navigate = useNavigate()
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
      setError("メールアドレスとパスワードを入力してください")
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
      setError(e.message || "ログインに失敗しました")
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!email.trim() || !password.trim() || !displayName.trim()) {
      setError("全ての項目を入力してください")
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
      setError(e.message || "登録に失敗しました")
    } finally {
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
            AI業務オーケストレーション基盤
          </p>
        </div>

        <div className="space-y-6">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 w-8 h-8 rounded-md bg-white/15 flex items-center justify-center shrink-0">
              <ArrowRight size={16} className="text-white/90" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-white/90">
                自然言語で業務を設計
              </p>
              <p className="text-[12px] text-white/50 mt-0.5">
                複数AIを組織的に協働させる
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 w-8 h-8 rounded-md bg-white/15 flex items-center justify-center shrink-0">
              <ArrowRight size={16} className="text-white/90" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-white/90">
                人間の承認と監査可能性
              </p>
              <p className="text-[12px] text-white/50 mt-0.5">
                危険操作は必ず承認を経て実行
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 w-8 h-8 rounded-md bg-white/15 flex items-center justify-center shrink-0">
              <ArrowRight size={16} className="text-white/90" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-white/90">
                Self-Healing DAG
              </p>
              <p className="text-[12px] text-white/50 mt-0.5">
                障害時に自動的に再計画・復旧
              </p>
            </div>
          </div>
        </div>

        <p className="text-[11px] text-white/30">v0.1.0</p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-[380px]">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <Logo size={36} />
            <div>
              <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
                Zero-Employee Orchestrator
              </h1>
              <p className="text-[11px] text-[var(--text-muted)]">
                AI業務オーケストレーション基盤
              </p>
            </div>
          </div>

          <h2 className="text-[20px] font-semibold text-[var(--text-primary)] mb-1">
            {mode === "login" ? "ログイン" : "アカウント作成"}
          </h2>
          <p className="text-[13px] text-[var(--text-secondary)] mb-6">
            {mode === "login"
              ? "メールアドレスとパスワードでサインインしてください。"
              : "新しいアカウントを作成して始めましょう。"}
          </p>

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
                  placeholder="表示名（組織名または氏名）"
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
                placeholder="メールアドレス"
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
                placeholder="パスワード"
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
                  {loading ? "接続中..." : "ログイン"}
                </>
              ) : (
                <>
                  <UserPlus size={15} />
                  {loading ? "登録中..." : "アカウント作成"}
                </>
              )}
            </button>
          </div>

          {/* Toggle */}
          <div className="mt-6 pt-6 border-t border-[var(--border)] text-center">
            <p className="text-[12px] text-[var(--text-muted)]">
              {mode === "login" ? (
                <>
                  アカウントをお持ちでない方は{" "}
                  <button
                    onClick={() => {
                      setMode("register")
                      setError("")
                    }}
                    className="text-[var(--accent)] hover:underline font-medium"
                  >
                    新規登録
                  </button>
                </>
              ) : (
                <>
                  すでにアカウントをお持ちの方は{" "}
                  <button
                    onClick={() => {
                      setMode("login")
                      setError("")
                    }}
                    className="text-[var(--accent)] hover:underline font-medium"
                  >
                    ログイン
                  </button>
                </>
              )}
            </p>
            <p className="text-[11px] text-[var(--text-muted)] mt-2">
              APIキーの手動入力は不要です。設定画面から後で追加できます。
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
