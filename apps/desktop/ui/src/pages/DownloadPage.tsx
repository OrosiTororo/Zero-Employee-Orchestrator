import {
  Download,
  Monitor,
  Apple,
  Terminal,
  HardDrive,
  ExternalLink,
  Copy,
  Check,
  Package,
  Cpu,
  RefreshCw,
} from "lucide-react"
import { useState, useEffect, useCallback } from "react"

const REPO = "OrosiTororo/Zero-Employee-Orchestrator"
const CURRENT_VERSION = "v0.1.5"

interface ReleaseAsset {
  name: string
  browser_download_url: string
}

interface Release {
  tag_name: string
  prerelease: boolean
  assets: ReleaseAsset[]
}

type OsKey = "windows" | "macos" | "linux"

function isGuiAsset(name: string, os: OsKey): boolean {
  const lower = name.toLowerCase()
  if (os === "windows") return lower.endsWith(".msi") || lower.endsWith(".exe")
  if (os === "macos") return lower.endsWith(".dmg")
  if (os === "linux") return lower.endsWith(".appimage") || lower.endsWith(".deb")
  return false
}

function findAssetUrl(releases: Release[], os: OsKey): string | null {
  for (const release of releases) {
    if (release.prerelease) continue
    for (const asset of release.assets) {
      if (isGuiAsset(asset.name, os)) return asset.browser_download_url
    }
  }
  return null
}

function findLatestVersion(releases: Release[]): string | null {
  return releases.find((r) => !r.prerelease)?.tag_name ?? null
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="p-1.5 rounded hover:bg-[#3e3e42] transition-colors"
      title="コピー"
    >
      {copied ? (
        <Check size={13} className="text-[#4ec9b0]" />
      ) : (
        <Copy size={13} className="text-[#6a6a6a]" />
      )}
    </button>
  )
}

function CommandBlock({ command, label }: { command: string; label?: string }) {
  return (
    <div className="rounded border border-[#3e3e42] bg-[#1e1e1e] px-3 py-2 flex items-center justify-between gap-2">
      <div className="flex-1 min-w-0">
        {label && (
          <div className="text-[11px] text-[#6a6a6a] mb-1">{label}</div>
        )}
        <code className="text-[12px] text-[#ce9178] block truncate">
          {command}
        </code>
      </div>
      <CopyButton text={command} />
    </div>
  )
}

export function DownloadPage() {
  const [releases, setReleases] = useState<Release[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchReleases = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `https://api.github.com/repos/${REPO}/releases`,
        { headers: { Accept: "application/vnd.github.v3+json" } }
      )
      if (res.status === 403) {
        throw new Error("GitHub API レート制限に達しました。しばらく待ってから再度お試しください。")
      }
      if (!res.ok) throw new Error("リリース情報を取得できませんでした。")
      setReleases(await res.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : "リリース情報を取得できませんでした。")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchReleases() }, [fetchReleases])

  const latestVersion = findLatestVersion(releases) ?? CURRENT_VERSION
  const winHref = findAssetUrl(releases, "windows")
  const macHref = findAssetUrl(releases, "macos")
  const linuxHref = findAssetUrl(releases, "linux")
  const hasAnyAsset = winHref !== null || macHref !== null || linuxHref !== null

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-2">
          <Download size={22} className="text-[#007acc]" />
          <h1 className="text-[18px] font-semibold text-[#cccccc]">
            ダウンロード
          </h1>
        </div>
        <p className="text-[12px] text-[#6a6a6a] mb-6 ml-[34px]">
          Zero-Employee Orchestrator を入手する
        </p>

        {/* GUI Desktop App */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Package size={16} className="text-[#569cd6]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              デスクトップアプリ（GUI）
            </h2>
            {latestVersion && (
              <span className="text-[11px] text-[#4ec9b0] ml-1">
                {latestVersion}
              </span>
            )}
          </div>
          <div className="rounded border border-[#3e3e42] bg-[#252526] p-5">
            <p className="text-[12px] text-[#9a9a9a] mb-4">
              Tauri ベースのネイティブデスクトップアプリケーション。
              Windows / macOS / Linux 対応。
            </p>

            {loading ? (
              <div className="flex items-center gap-2 py-4 text-[12px] text-[#6a6a6a]">
                <RefreshCw size={13} className="animate-spin" />
                リリース情報を取得中...
              </div>
            ) : error ? (
              <div className="rounded border border-[#f44747]/30 bg-[#f44747]/10 px-3 py-2 mb-4">
                <p className="text-[12px] text-[#f44747] mb-1">{error}</p>
                <button
                  onClick={fetchReleases}
                  className="flex items-center gap-1 text-[11px] text-[#007acc] hover:underline"
                >
                  <RefreshCw size={10} />
                  再試行
                </button>
              </div>
            ) : null}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <PlatformCard
                icon={Monitor}
                os="Windows"
                format=".exe"
                href={winHref}
              />
              <PlatformCard
                icon={Apple}
                os="macOS"
                format=".dmg"
                href={macHref}
              />
              <PlatformCard
                icon={HardDrive}
                os="Linux"
                format=".AppImage / .deb"
                href={linuxHref}
              />
            </div>

            <div className="rounded border border-[#3e3e42] bg-[#1e1e1e] p-3">
              <div className="text-[12px] text-[#cccccc] font-medium mb-2">
                ソースからビルド
              </div>
              <div className="flex flex-col gap-2">
                <CommandBlock command="git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git" />
                <CommandBlock command="cd Zero-Employee-Orchestrator/apps/desktop" />
                <CommandBlock
                  command="pnpm install && pnpm tauri build"
                  label="ビルド実行（Rust ツールチェーンが必要）"
                />
              </div>
            </div>

            {!loading && !error && !hasAnyAsset && (
              <p className="text-[11px] text-[#6a6a6a] mt-3">
                ビルド済みバイナリは、GitHub Releases に公開され次第ここからダウンロードできるようになります。
              </p>
            )}
          </div>
        </section>

        {/* CLI / TUI */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Terminal size={16} className="text-[#4ec9b0]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              CLI / TUI 版
            </h2>
          </div>
          <div className="rounded border border-[#3e3e42] bg-[#252526] p-5">
            <p className="text-[12px] text-[#9a9a9a] mb-4">
              ターミナルから操作するエンジニア向けインターフェース。
              Python 3.12 以上が必要です。
            </p>

            <div className="flex flex-col gap-3">
              <CommandBlock
                command="pip install zero-employee-orchestrator"
                label="pip でインストール"
              />
              <CommandBlock
                command="uv pip install zero-employee-orchestrator"
                label="uv でインストール（推奨）"
              />
            </div>

            <div className="mt-4 rounded border border-[#3e3e42] bg-[#1e1e1e] p-3">
              <div className="text-[12px] text-[#cccccc] font-medium mb-2">
                ソースから実行
              </div>
              <div className="flex flex-col gap-2">
                <CommandBlock command="git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git" />
                <CommandBlock command="cd Zero-Employee-Orchestrator" />
                <CommandBlock
                  command="uv sync && uv run python -m apps.api.app.main"
                  label="API サーバーを起動"
                />
              </div>
            </div>
          </div>
        </section>

        {/* System Requirements */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Cpu size={16} className="text-[#dcdcaa]" />
            <h2 className="text-[14px] font-medium text-[#cccccc]">
              動作要件
            </h2>
          </div>
          <div className="rounded border border-[#3e3e42] bg-[#252526] p-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-[12px] text-[#569cd6] font-medium mb-2">
                  デスクトップアプリ（GUI）
                </div>
                <ul className="text-[12px] text-[#9a9a9a] space-y-1">
                  <li>
                    <span className="text-[#6a6a6a]">•</span> Windows 10 以降 /
                    macOS 12 以降 / Linux（glibc 2.31+）
                  </li>
                  <li>
                    <span className="text-[#6a6a6a]">•</span> メモリ: 4 GB 以上
                  </li>
                  <li>
                    <span className="text-[#6a6a6a]">•</span> ディスク: 500 MB
                    以上
                  </li>
                </ul>
              </div>
              <div>
                <div className="text-[12px] text-[#4ec9b0] font-medium mb-2">
                  CLI / TUI 版
                </div>
                <ul className="text-[12px] text-[#9a9a9a] space-y-1">
                  <li>
                    <span className="text-[#6a6a6a]">•</span> Python 3.12+
                  </li>
                  <li>
                    <span className="text-[#6a6a6a]">•</span> メモリ: 2 GB 以上
                  </li>
                  <li>
                    <span className="text-[#6a6a6a]">•</span> uv（推奨）または
                    pip
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Link to GitHub */}
        <div className="text-center pb-6">
          <a
            href={`https://github.com/${REPO}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-[12px] text-[#007acc] hover:underline"
          >
            GitHub リポジトリを確認
            <ExternalLink size={11} />
          </a>
        </div>
      </div>
    </div>
  )
}

function PlatformCard({
  icon: Icon,
  os,
  format,
  href,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  os: string
  format: string
  href: string | null
}) {
  const available = href !== null
  const baseClasses = `rounded border border-[#3e3e42] bg-[#1e1e1e] px-4 py-3 transition-colors`

  const content = (
    <>
      <div className="flex items-center gap-2 mb-1">
        <Icon
          size={16}
          className={available ? "text-[#007acc]" : "text-[#6a6a6a]"}
        />
        <span className="text-[13px] font-medium text-[#cccccc]">{os}</span>
      </div>
      <div className="text-[11px] text-[#6a6a6a]">{format}</div>
      <div className={`text-[11px] mt-1 flex items-center gap-1 ${available ? "text-[#4ec9b0]" : "text-[#6a6a6a]"}`}>
        {available ? (
          <>
            <Download size={10} />
            ダウンロード
          </>
        ) : (
          "準備中"
        )}
      </div>
    </>
  )

  if (available) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={`${baseClasses} hover:border-[#007acc] block no-underline`}
      >
        {content}
      </a>
    )
  }

  return (
    <div className={`${baseClasses} opacity-60`}>
      {content}
    </div>
  )
}
