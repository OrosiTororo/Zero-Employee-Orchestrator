import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "@/shared/hooks/use-auth"
import { LogIn, UserPlus, Zap, Mail, Lock, User } from "lucide-react"
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

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#1e1e1e]">
      <div className="flex flex-col items-center gap-6 max-w-[420px] w-full px-8">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded flex items-center justify-center bg-[#007acc]">
            <Zap size={28} color="#ffffff" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[#cccccc]">
              Zero-Employee Orchestrator
            </h1>
            <p className="text-[12px] text-[#6a6a6a]">
              AI業務オーケストレーション基盤
            </p>
          </div>
        </div>

        <p className="text-center text-[13px] leading-relaxed text-[#969696]">
          自然言語で業務を設計し、複数AIを組織的に協働させる
          <br />
          人間の承認と監査可能性を備えた業務実行基盤
        </p>

        {/* Mode Toggle */}
        <div className="flex w-full rounded overflow-hidden border border-[#3e3e42]">
          <button
            onClick={() => { setMode("login"); setError("") }}
            className="flex-1 py-2 text-[13px] font-medium transition-colors"
            style={{
              background: mode === "login" ? "#007acc" : "transparent",
              color: mode === "login" ? "#fff" : "#969696",
            }}
          >
            ログイン
          </button>
          <button
            onClick={() => { setMode("register"); setError("") }}
            className="flex-1 py-2 text-[13px] font-medium transition-colors"
            style={{
              background: mode === "register" ? "#007acc" : "transparent",
              color: mode === "register" ? "#fff" : "#969696",
            }}
          >
            新規登録
          </button>
        </div>

        {/* Form */}
        <div className="w-full flex flex-col gap-3">
          {mode === "register" && (
            <div className="relative">
              <User
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
              />
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="表示名（組織名または氏名）"
                className="w-full pl-9 pr-3 py-2.5 rounded text-[13px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc]"
              />
            </div>
          )}

          <div className="relative">
            <Mail
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
            />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="メールアドレス"
              className="w-full pl-9 pr-3 py-2.5 rounded text-[13px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc]"
            />
          </div>

          <div className="relative">
            <Lock
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
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
              className="w-full pl-9 pr-3 py-2.5 rounded text-[13px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc]"
            />
          </div>

          {error && (
            <div className="text-[12px] text-[#f44747] text-center">{error}</div>
          )}

          <button
            onClick={mode === "login" ? handleLogin : handleRegister}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-6 py-2.5 rounded text-[13px] font-medium transition-colors"
            style={{
              background: loading ? "#3e3e42" : "#007acc",
              color: "#ffffff",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {mode === "login" ? (
              <>
                <LogIn size={16} />
                {loading ? "接続中..." : "ログイン"}
              </>
            ) : (
              <>
                <UserPlus size={16} />
                {loading ? "登録中..." : "アカウント作成"}
              </>
            )}
          </button>
        </div>

        <div className="text-[11px] text-center text-[#6a6a6a] space-y-1">
          <p>
            {mode === "login"
              ? "アカウントをお持ちでない方は「新規登録」タブから登録できます。"
              : "登録後、初期セットアップウィザードで簡単に設定できます。"}
          </p>
          <p>APIキーの手動入力は不要です。設定画面から後で追加できます。</p>
        </div>
      </div>
    </div>
  )
}
