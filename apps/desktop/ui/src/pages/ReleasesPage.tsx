import { useState, useEffect, useCallback } from "react"
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
  RefreshCw,
  Star,
  BarChart3,
} from "lucide-react"

interface ReleaseAsset {
  name: string
  size: number
  browser_download_url: string
  download_count: number
}

interface Release {
  tag_name: string
  name: string
  published_at: string
  body: string
  html_url: string
  prerelease: boolean
  assets: ReleaseAsset[]
}

const REPO = "TroroOrosi/Zero-Employee-Orchestrator"

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDownloads(count: number): string {
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`
  return `${count}`
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

type OsFilter = "all" | "windows" | "macos" | "linux"

function matchesOsFilter(name: string, filter: OsFilter): boolean {
  if (filter === "all") return true
  const label = getOsLabel(name).toLowerCase()
  if (filter === "windows") return label === "windows"
  if (filter === "macos") return label === "macos"
  if (filter === "linux") return label === "linux"
  return false
}

function findLatestAssetUrl(releases: Release[], os: OsFilter): string | null {
  for (const release of releases) {
    if (release.prerelease) continue
    for (const asset of release.assets) {
      if (matchesOsFilter(asset.name, os)) {
        return asset.browser_download_url
      }
    }
  }
  return null
}

function renderMarkdownBasic(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, '<span class="text-[#4ec9b0] font-medium">$1</span>')
    .replace(/^## (.+)$/gm, '<span class="text-[#569cd6] font-semibold text-[13px]">$1</span>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-[#cccccc]">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="bg-[#333333] px-1 rounded text-[#ce9178]">$1</code>')
    .replace(/^- (.+)$/gm, '<span class="text-[#6a6a6a]">•</span> $1')
    .replace(/\n/g, "<br />")
}

export function ReleasesPage() {
  const [releases, setReleases] = useState<Release[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchReleases = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `https://api.github.com/repos/${REPO}/releases`,
        {
          headers: { Accept: "application/vnd.github.v3+json" },
        }
      )
      if (res.status === 403) {
        throw new Error("GitHub API レート制限に達しました。しばらく待ってから再度お試しください。")
      }
      if (!res.ok) throw new Error("リリース情報を取得できませんでした。")
      const data = await res.json()
      setReleases(data)
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "リリース情報を取得できませんでした。後でもう一度お試しください。"
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchReleases()
  }, [fetchReleases])

  const latestStable = releases.find((r) => !r.prerelease)
  const latestVersion = latestStable?.tag_name ?? null

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Download size={22} className="text-[#007acc]" />
            <div>
              <h1 className="text-[18px] font-semibold text-[#cccccc]">
                Releases
              </h1>
              <p className="text-[12px] text-[#6a6a6a]">
                Zero-Employee Orchestrator のダウンロード
                {latestVersion && (
                  <span className="ml-2 text-[#4ec9b0]">
                    最新: {latestVersion}
                  </span>
                )}
              </p>
            </div>
          </div>
          <button
            onClick={fetchReleases}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] text-[#cccccc] bg-[#333333] hover:bg-[#3e3e42] transition-colors disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            更新
          </button>
        </div>

        {/* Quick Download Section */}
        <div className="mb-8 rounded border border-[#3e3e42] bg-[#252526] p-5">
          <h2 className="text-[14px] font-medium text-[#cccccc] mb-4">
            クイックダウンロード
            {latestVersion && (
              <span className="ml-2 text-[11px] text-[#6a6a6a] font-normal">
                ({latestVersion})
              </span>
            )}
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <DownloadCard
              icon={Monitor}
              os="Windows"
              format=".msi / .exe"
              description="インストーラーをダウンロード"
              href={findLatestAssetUrl(releases, "windows")}
            />
            <DownloadCard
              icon={Apple}
              os="macOS"
              format=".dmg"
              description="ディスクイメージをダウンロード"
              href={findLatestAssetUrl(releases, "macos")}
            />
            <DownloadCard
              icon={HardDrive}
              os="Linux"
              format=".AppImage / .deb"
              description="パッケージをダウンロード"
              href={findLatestAssetUrl(releases, "linux")}
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
            <RefreshCw size={16} className="animate-spin mx-auto mb-2" />
            リリース情報を読み込み中...
          </div>
        )}

        {error && (
          <div className="rounded border border-[#f44747]/30 bg-[#f44747]/10 px-4 py-3 mb-4">
            <p className="text-[13px] text-[#f44747] mb-2">{error}</p>
            <button
              onClick={fetchReleases}
              className="flex items-center gap-1.5 text-[12px] text-[#007acc] hover:underline"
            >
              <RefreshCw size={11} />
              再試行
            </button>
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

        {!loading &&
          releases.map((release, index) => {
            const isLatest = index === 0 && !release.prerelease
            const totalDownloads = release.assets.reduce(
              (sum, a) => sum + a.download_count,
              0
            )

            return (
              <div
                key={release.tag_name}
                className={`mb-4 rounded border overflow-hidden ${
                  isLatest
                    ? "border-[#007acc]/50 bg-[#252526]"
                    : "border-[#3e3e42] bg-[#252526]"
                }`}
              >
                {/* Release Header */}
                <div className="px-4 py-3 border-b border-[#3e3e42]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Tag size={14} className="text-[#007acc]" />
                      <span className="text-[14px] font-medium text-[#cccccc]">
                        {release.name || release.tag_name}
                      </span>
                      {isLatest && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#007acc]/20 text-[#007acc] flex items-center gap-1">
                          <Star size={9} />
                          Latest
                        </span>
                      )}
                      {release.prerelease && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#dcdcaa]/20 text-[#dcdcaa]">
                          Pre-release
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-[#6a6a6a]">
                      {totalDownloads > 0 && (
                        <span className="flex items-center gap-1" title="総ダウンロード数">
                          <BarChart3 size={11} />
                          {formatDownloads(totalDownloads)}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock size={11} />
                        {formatDate(release.published_at)}
                      </span>
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
                              <Icon
                                size={14}
                                className="text-[#6a6a6a] group-hover:text-[#007acc]"
                              />
                              <span className="text-[12px] text-[#cccccc]">
                                {asset.name}
                              </span>
                              <span className="text-[11px] text-[#6a6a6a]">
                                ({getOsLabel(asset.name)})
                              </span>
                            </div>
                            <div className="flex items-center gap-3">
                              {asset.download_count > 0 && (
                                <span
                                  className="text-[11px] text-[#6a6a6a] flex items-center gap-1"
                                  title="ダウンロード数"
                                >
                                  <BarChart3 size={10} />
                                  {formatDownloads(asset.download_count)}
                                </span>
                              )}
                              <span className="text-[11px] text-[#6a6a6a]">
                                {formatSize(asset.size)}
                              </span>
                              <Download
                                size={13}
                                className="text-[#6a6a6a] group-hover:text-[#007acc]"
                              />
                            </div>
                          </a>
                        )
                      })}
                    </div>
                  </div>
                )}

                {release.assets.length === 0 && (
                  <div className="px-4 py-3 text-[12px] text-[#6a6a6a]">
                    このリリースにはダウンロード可能なアセットがありません。
                    <a
                      href={release.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#007acc] hover:underline ml-1"
                    >
                      GitHub で確認
                    </a>
                  </div>
                )}

                {/* Release Notes */}
                {release.body && (
                  <div className="px-4 py-3 border-t border-[#3e3e42]">
                    <details>
                      <summary className="text-[12px] text-[#007acc] cursor-pointer hover:underline">
                        リリースノートを表示
                      </summary>
                      <div
                        className="mt-2 text-[12px] text-[#9a9a9a] leading-relaxed"
                        dangerouslySetInnerHTML={{
                          __html: renderMarkdownBasic(release.body),
                        }}
                      />
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
            )
          })}
      </div>
    </div>
  )
}

function DownloadCard({
  icon: Icon,
  os,
  format,
  description,
  href,
}: {
  icon: React.ComponentType<{ size?: number }>
  os: string
  format: string
  description: string
  href: string | null
}) {
  const baseClasses =
    "rounded border border-[#3e3e42] bg-[#1e1e1e] px-4 py-3 transition-colors block"

  if (href) {
    return (
      <a
        href={href}
        className={`${baseClasses} hover:border-[#007acc] cursor-pointer no-underline`}
      >
        <div className="flex items-center gap-2 mb-1">
          <Icon size={16} className="text-[#007acc]" />
          <span className="text-[13px] font-medium text-[#cccccc]">{os}</span>
        </div>
        <div className="text-[11px] text-[#6a6a6a]">{format}</div>
        <div className="text-[11px] text-[#6a6a6a] mt-1">{description}</div>
      </a>
    )
  }

  return (
    <div
      className={`${baseClasses} opacity-60`}
      title="リリースが公開されるとダウンロードできます"
    >
      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} className="text-[#6a6a6a]" />
        <span className="text-[13px] font-medium text-[#cccccc]">{os}</span>
      </div>
      <div className="text-[11px] text-[#6a6a6a]">{format}</div>
      <div className="text-[11px] text-[#6a6a6a] mt-1">準備中</div>
    </div>
  )
}
