import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "@/shared/hooks/use-auth"
import { LogIn, Zap, Mail } from "lucide-react"

const providers = [
  { id: "openrouter", name: "OpenRouter", description: "OAuth PKCE 認証" },
  { id: "google", name: "Google", description: "Google OAuth" },
]

export function LoginPage() {
  const { login, authenticated } = useAuthStore()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [selectedProvider, setSelectedProvider] = useState("openrouter")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  if (authenticated) {
    navigate("/", { replace: true })
    return null
  }

  const handleLogin = async () => {
    if (!email.trim()) {
      setError("メールアドレスを入力してください")
      return
    }
    setLoading(true)
    setError("")
    try {
      await login(email, selectedProvider)
      navigate("/")
    } catch {
      setError("ログインに失敗しました。再試行してください。")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#1e1e1e]">
      <div className="flex flex-col items-center gap-8 max-w-[400px] px-8">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded flex items-center justify-center bg-[#007acc]">
            <Zap size={28} color="#ffffff" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[#cccccc]">
              Zero-Employee Orchestrator
            </h1>
            <p className="text-[12px] text-[#6a6a6a]">
              AI従業員ゼロ人オーケストレーター
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-center text-[13px] leading-relaxed text-[#969696]">
          AIエージェントが自律的に業務を遂行する、ゼロ従業員組織運営プラットフォーム。
        </p>

        {/* Email Input */}
        <div className="w-full flex flex-col gap-3">
          <div className="relative">
            <Mail
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6a6a]"
            />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              placeholder="メールアドレス"
              className="w-full pl-9 pr-3 py-2.5 rounded text-[13px] outline-none bg-[#3c3c3c] text-[#cccccc] border border-[#3e3e42] focus:border-[#007acc]"
            />
          </div>

          {/* Provider Selection */}
          <div className="flex flex-col gap-2">
            <span className="text-[11px] uppercase tracking-wider text-[#6a6a6a]">
              認証プロバイダー
            </span>
            <div className="flex gap-2">
              {providers.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedProvider(p.id)}
                  className="flex-1 px-3 py-2 rounded text-[12px] text-left border transition-colors"
                  style={{
                    background:
                      selectedProvider === p.id ? "#007acc20" : "transparent",
                    borderColor:
                      selectedProvider === p.id ? "#007acc" : "#3e3e42",
                    color: "#cccccc",
                  }}
                >
                  <div className="font-medium">{p.name}</div>
                  <div className="text-[10px] text-[#6a6a6a]">
                    {p.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="text-[12px] text-[#f44747] text-center">
              {error}
            </div>
          )}

          {/* Login Button */}
          <button
            onClick={handleLogin}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-6 py-2.5 rounded text-[13px] font-medium transition-colors"
            style={{
              background: loading ? "#3e3e42" : "#007acc",
              color: "#ffffff",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            <LogIn size={16} />
            {loading ? "接続中..." : "ログイン"}
          </button>
        </div>

        <p className="text-[11px] text-center text-[#6a6a6a]">
          選択したプロバイダーのOAuth認証でログインします。
        </p>
      </div>
    </div>
  )
}
