import { useState, useEffect } from "react"
import {
  Download,
  Monitor,
  Apple,
  Terminal,
  Package,
  ExternalLink,
  Clock,
  Tag,
  HardDrive,
} from "lucide-react"

interface Release {
  tag_name: string
  name: string
  published_at: string
  body: string
  html_url: string
  prerelease: boolean
  assets: {
    name: string
    size: number
    browser_download_url: string
    download_count: number
  }[]
}

const REPO = "TroroOrosi/Zero-Employee-Orchestrator"

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })
}

function getOsIcon(name: string) {
  const lower = name.toLowerCase()
  if (lower.includes("windows") || lower.endsWith(".msi") || lower.endsWith(".exe"))
    return Monitor
  if (lower.includes("macos") || lower.endsWith(".dmg"))
    return Apple
  if (lower.includes("linux") || lower.endsWith(".appimage") || lower.endsWith(".deb"))
    return HardDrive
  return Package
}

function getOsLabel(name: string): string {
  const lower = name.toLowerCase()
  if (lower.includes("windows") || lower.endsWith(".msi") || lower.endsWith(".exe"))
    return "Windows"
  if (lower.includes("macos") || lower.endsWith(".dmg"))
    return "macOS"
  if (lower.includes("linux") || lower.endsWith(".appimage") || lower.endsWith(".deb"))
    return "Linux"
  if (lower.endsWith(".tar.gz") || lower.endsWith(".whl"))
    return "CLI / TUI"
  return "Other"
}

export function ReleasesPage() {
  const [releases, setReleases] = useState<Release[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchReleases() {
      try {
        const res = await fetch(
          `https://api.github.com/repos/${REPO}/releases`
        )
        if (!res.ok) throw new Error("Failed to fetch releases")
        const data = await res.json()
        setReleases(data)
      } catch (e) {
        setError("リリース情報を取得できませんでした。後でもう一度お試しください。")
      } finally {
        setLoading(false)
      }
    }
    fetchReleases()
  }, [])

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Download size={22} className="text-[#007acc]" />
          <div>
            <h1 className="text-[18px] font-semibold text-[#cccccc]">
              Releases
            </h1>
            <p className="text-[12px] text-[#6a6a6a]">
              Zero-Employee Orchestrator のダウンロード
            </p>
          </div>
        </div>

        {/* Quick Download Section */}
        <div className="mb-8 rounded border border-[#3e3e42] bg-[#252526] p-5">
          <h2 className="text-[14px] font-medium text-[#cccccc] mb-4">
            クイックダウンロード
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <DownloadCard
              icon={Monitor}
              os="Windows"
              format=".msi / .exe"
              description="インストーラーをダウンロード"
            />
            <DownloadCard
              icon={Apple}
              os="macOS"
              format=".dmg"
              description="ディスクイメージをダウンロード"
            />
            <DownloadCard
              icon={HardDrive}
              os="Linux"
              format=".AppImage / .deb"
              description="パッケージをダウンロード"
            />
          </div>

          <div className="rounded border border-[#3e3e42] bg-[#1e1e1e] p-3">
            <div className="flex items-center gap-2 mb-2">
              <Terminal size={14} className="text-[#4ec9b0]" />
              <span className="text-[12px] text-[#cccccc] font-medium">
                CLI / TUI 版（エンジニア向け）
              </span>
            </div>
            <code className="text-[12px] text-[#ce9178] block bg-[#252526] rounded px-3 py-2">
              pip install zero-employee-orchestrator
            </code>
          </div>
        </div>

        {/* Release List */}
        {loading && (
          <div className="text-center py-12 text-[#6a6a6a] text-[13px]">
            リリース情報を読み込み中...
          </div>
        )}

        {error && (
          <div className="rounded border border-[#f44747]/30 bg-[#f44747]/10 px-4 py-3 mb-4">
            <p className="text-[13px] text-[#f44747]">{error}</p>
          </div>
        )}

        {!loading && !error && releases.length === 0 && (
          <div className="rounded border border-[#3e3e42] bg-[#252526] px-6 py-12 text-center">
            <Package size={32} className="mx-auto mb-3 text-[#6a6a6a]" />
            <p className="text-[14px] text-[#cccccc] mb-2">
              まだリリースがありません
            </p>
            <p className="text-[12px] text-[#6a6a6a]">
              最初のリリースが公開されるとここに表示されます。
            </p>
            <a
              href={`https://github.com/${REPO}/releases`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 mt-4 text-[12px] text-[#007acc] hover:underline"
            >
              GitHub Releases を確認
              <ExternalLink size={11} />
            </a>
          </div>
        )}

        {releases.map((release) => (
          <div
            key={release.tag_name}
            className="mb-4 rounded border border-[#3e3e42] bg-[#252526] overflow-hidden"
          >
            {/* Release Header */}
            <div className="px-4 py-3 border-b border-[#3e3e42]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Tag size={14} className="text-[#007acc]" />
                  <span className="text-[14px] font-medium text-[#cccccc]">
                    {release.name || release.tag_name}
                  </span>
                  {release.prerelease && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#dcdcaa]/20 text-[#dcdcaa]">
                      Pre-release
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 text-[11px] text-[#6a6a6a]">
                  <Clock size={11} />
                  {formatDate(release.published_at)}
                </div>
              </div>
            </div>

            {/* Assets */}
            {release.assets.length > 0 && (
              <div className="px-4 py-3">
                <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-2">
                  ダウンロード
                </div>
                <div className="flex flex-col gap-1.5">
                  {release.assets.map((asset) => {
                    const Icon = getOsIcon(asset.name)
                    return (
                      <a
                        key={asset.name}
                        href={asset.browser_download_url}
                        className="flex items-center justify-between px-3 py-2 rounded bg-[#1e1e1e] hover:bg-[#2a2d2e] transition-colors group"
                      >
                        <div className="flex items-center gap-2">
                          <Icon size={14} className="text-[#6a6a6a] group-hover:text-[#007acc]" />
                          <span className="text-[12px] text-[#cccccc]">
                            {asset.name}
                          </span>
                          <span className="text-[11px] text-[#6a6a6a]">
                            ({getOsLabel(asset.name)})
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-[11px] text-[#6a6a6a]">
                            {formatSize(asset.size)}
                          </span>
                          <Download size={13} className="text-[#6a6a6a] group-hover:text-[#007acc]" />
                        </div>
                      </a>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Release Notes */}
            {release.body && (
              <div className="px-4 py-3 border-t border-[#3e3e42]">
                <details>
                  <summary className="text-[12px] text-[#007acc] cursor-pointer hover:underline">
                    リリースノートを表示
                  </summary>
                  <pre className="mt-2 text-[12px] text-[#cccccc] whitespace-pre-wrap leading-relaxed">
                    {release.body}
                  </pre>
                </details>
              </div>
            )}

            {/* Link to GitHub */}
            <div className="px-4 py-2 border-t border-[#3e3e42]">
              <a
                href={release.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[11px] text-[#6a6a6a] hover:text-[#007acc]"
              >
                GitHub で表示
                <ExternalLink size={10} />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function DownloadCard({
  icon: Icon,
  os,
  format,
  description,
}: {
  icon: React.ComponentType<{ size?: number }>
  os: string
  format: string
  description: string
}) {
  return (
    <div className="rounded border border-[#3e3e42] bg-[#1e1e1e] px-4 py-3 hover:border-[#007acc] transition-colors cursor-pointer">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} className="text-[#007acc]" />
        <span className="text-[13px] font-medium text-[#cccccc]">{os}</span>
      </div>
      <div className="text-[11px] text-[#6a6a6a]">{format}</div>
      <div className="text-[11px] text-[#6a6a6a] mt-1">{description}</div>
    </div>
  )
}
