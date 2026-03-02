import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { LogIn, Zap } from "lucide-react";

export function LoginPage() {
  const { login, authenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  if (authenticated) {
    navigate("/", { replace: true });
    return null;
  }

  const handleLogin = async () => {
    setLoading(true);
    try {
      await login();
      navigate("/");
    } catch {
      // error handled in hook
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="h-screen w-screen flex items-center justify-center"
      style={{ background: '#1e1e1e' }}
    >
      <div className="flex flex-col items-center gap-8 max-w-[400px] px-8">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded flex items-center justify-center"
            style={{ background: '#007acc' }}
          >
            <Zap size={28} color="#ffffff" />
          </div>
          <div>
            <h1 className="text-xl font-semibold" style={{ color: '#cccccc' }}>
              ZPCOS
            </h1>
            <p className="text-[12px]" style={{ color: '#6a6a6a' }}>
              Zero-Prompt Cross-model Orchestration System
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-center text-[13px] leading-relaxed" style={{ color: '#969696' }}>
          AI を道具から組織に進化させるローカル常駐型デスクトップ OS。
          自然言語で目的を伝えるだけで、AI 組織が自律的に実行します。
        </p>

        {/* Login Button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 rounded text-[13px] font-medium transition-colors"
          style={{
            background: loading ? '#3e3e42' : '#007acc',
            color: '#ffffff',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
          onMouseEnter={(e) => {
            if (!loading) e.currentTarget.style.background = '#1a8ad4';
          }}
          onMouseLeave={(e) => {
            if (!loading) e.currentTarget.style.background = '#007acc';
          }}
        >
          <LogIn size={16} />
          {loading ? "Connecting..." : "Connect with OpenRouter"}
        </button>

        <p className="text-[11px] text-center" style={{ color: '#6a6a6a' }}>
          OpenRouter OAuth で認証します。API 利用料はあなたのアカウントに課金されます。
        </p>
      </div>
    </div>
  );
}
