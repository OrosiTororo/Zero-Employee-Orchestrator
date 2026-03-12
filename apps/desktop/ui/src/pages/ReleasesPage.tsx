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
  MessageSquare,
  FileText,
  GitBranch,
  Shield,
  ScrollText,
  Blocks,
  Activity,
  BrainCircuit,
} from "lucide-react"

type Lang = "ja" | "en" | "zh"

const t: Record<Lang, Record<string, string>> = {
  ja: {
    downloadTitle: "Zero-Employee Orchestrator のダウンロード",
    latest: "最新:",
    refresh: "更新",
    keyFeatures: "主な機能",
    quickDownload: "クイックダウンロード",
    downloadInstaller: "インストーラーをダウンロード",
    downloadDiskImage: "ディスクイメージをダウンロード",
    downloadPackage: "パッケージをダウンロード",
    cliTui: "CLI / TUI 版（エンジニア向け）",
    loading: "リリース情報を読み込み中...",
    rateLimitError: "GitHub API レート制限に達しました。しばらく待ってから再度お試しください。",
    fetchError: "リリース情報を取得できませんでした。後でもう一度お試しください。",
    fetchErrorShort: "リリース情報を取得できませんでした。",
    retry: "再試行",
    availableAssets: "ダウンロード可能なアセット",
    allAssets: "全アセット",
    releaseNotes: "リリースノート",
    showReleaseNotes: "リリースノートを表示",
    keyNewFeatures: "主な新機能・改善",
    viewOnGithub: "GitHub で表示",
    noAssets: "このリリースにはダウンロード可能なアセットがありません。",
    checkOnGithub: "GitHub で確認",
    comingSoon: "準備中",
    guiInstaller: "GUI インストーラー",
    totalDownloads: "総ダウンロード数",
    downloads: "ダウンロード数",
    availableWhenPublished: "リリースが公開されるとダウンロードできます",
    featureDesignInterview: "自然言語で業務を依頼し、AI が要件を深掘り",
    featureSpecPlan: "中間成果物を構造化保存、再利用・監査・差し戻し",
    featureTaskOrchestrator: "DAG ベースの計画生成、コスト見積り、品質モード切替",
    featureJudgeLayer: "ルール一次判定 + Cross-Model 高精度検証",
    featureSelfHealing: "障害時の自動再計画・再提案で業務を止めない",
    featureSkillPlugin: "3層の拡張体系で業務機能を自由に追加",
    featureApproval: "投稿・課金・削除など危険操作は人間承認を要求",
    featureAuditLog: "誰が何をなぜ実行したかを全て追跡可能",
    approvalLabel: "承認フロー",
    auditLogLabel: "監査ログ",
  },
  en: {
    downloadTitle: "Download Zero-Employee Orchestrator",
    latest: "Latest:",
    refresh: "Refresh",
    keyFeatures: "Key Features",
    quickDownload: "Quick Download",
    downloadInstaller: "Download installer",
    downloadDiskImage: "Download disk image",
    downloadPackage: "Download package",
    cliTui: "CLI / TUI (For Engineers)",
    loading: "Loading release information...",
    rateLimitError: "GitHub API rate limit reached. Please try again later.",
    fetchError: "Could not fetch release information. Please try again later.",
    fetchErrorShort: "Could not fetch release information.",
    retry: "Retry",
    availableAssets: "Available Assets",
    allAssets: "All Assets",
    releaseNotes: "Release Notes",
    showReleaseNotes: "Show Release Notes",
    keyNewFeatures: "Key New Features & Improvements",
    viewOnGithub: "View on GitHub",
    noAssets: "No downloadable assets for this release.",
    checkOnGithub: "Check on GitHub",
    comingSoon: "Coming soon",
    guiInstaller: "GUI Installer",
    totalDownloads: "Total downloads",
    downloads: "Downloads",
    availableWhenPublished: "Available when release is published",
    featureDesignInterview: "Define tasks in natural language, AI deepens requirements",
    featureSpecPlan: "Structured intermediate artifacts, reusable, auditable, reversible",
    featureTaskOrchestrator: "DAG-based plan generation, cost estimation, quality mode switching",
    featureJudgeLayer: "Rule-based first check + Cross-Model high-precision verification",
    featureSelfHealing: "Auto re-planning on failure keeps operations running",
    featureSkillPlugin: "3-layer extension system to freely add business capabilities",
    featureApproval: "Dangerous operations require human approval",
    featureAuditLog: "Full traceability of who did what and why",
    approvalLabel: "Approval Flow",
    auditLogLabel: "Audit Log",
  },
  zh: {
    downloadTitle: "下载 Zero-Employee Orchestrator",
    latest: "最新:",
    refresh: "刷新",
    keyFeatures: "主要功能",
    quickDownload: "快速下载",
    downloadInstaller: "下载安装程序",
    downloadDiskImage: "下载磁盘映像",
    downloadPackage: "下载软件包",
    cliTui: "CLI / TUI 版（面向工程师）",
    loading: "正在加载发布信息...",
    rateLimitError: "已达到 GitHub API 速率限制。请稍后重试。",
    fetchError: "无法获取发布信息。请稍后重试。",
    fetchErrorShort: "无法获取发布信息。",
    retry: "重试",
    availableAssets: "可下载资源",
    allAssets: "全部资源",
    releaseNotes: "发布说明",
    showReleaseNotes: "显示发布说明",
    keyNewFeatures: "主要新功能与改进",
    viewOnGithub: "在 GitHub 上查看",
    noAssets: "此版本没有可下载的资源。",
    checkOnGithub: "在 GitHub 上确认",
    comingSoon: "准备中",
    guiInstaller: "GUI 安装程序",
    totalDownloads: "总下载次数",
    downloads: "下载次数",
    availableWhenPublished: "发布后可下载",
    featureDesignInterview: "用自然语言委托业务，AI 深入挖掘需求",
    featureSpecPlan: "结构化保存中间成果物，可复用、审计、退回",
    featureTaskOrchestrator: "基于 DAG 的计划生成、成本估算、质量模式切换",
    featureJudgeLayer: "规则一次判定 + 跨模型高精度验证",
    featureSelfHealing: "故障时自动重新规划，业务不中断",
    featureSkillPlugin: "三层扩展体系，自由添加业务功能",
    featureApproval: "发布、计费、删除等危险操作需人工审批",
    featureAuditLog: "完整追踪谁执行了什么以及原因",
    approvalLabel: "审批流程",
    auditLogLabel: "审计日志",
  },
}

const RELEASE_HIGHLIGHTS: Record<Lang, string[]> = {
  ja: [
    "9層アーキテクチャの完全実装（User Layer〜Skill Registry）",
    "ZEO-Bench — 200問テストセットによる Judge Layer 定量評価ベンチマーク",
    "Cross-Model Verification 改善（セマンティック類似度・矛盾検出・信頼度加重）",
    "汎用ドメイン Skill テンプレート（コンテンツ・競合分析・トレンド・KPI・戦略）",
    "Artifact Bridge 強化 — 成果物の自動連携・型変換・パイプライン設計",
    "Self-Healing DAG カオステスト（20+ フォルト注入・復旧率計測）",
    "ランタイム設定管理 — .env 不要で API キーを設定可能",
    "ナレッジストア — ユーザー設定・ファイル権限の永続記憶 + 変更検知",
    "自然言語スキル生成エンジン（16種の安全性チェック付き）",
    "Dynamic Model Registry（コード変更なしにモデル入替可能）",
    "分身AI / 秘書AI / チャットツール連携 Plugin",
    "MCP サーバー（8ツール・4リソース・2プロンプト）",
    "Tauri v2 デスクトップアプリ（Windows / macOS / Linux）",
    "Cloudflare Workers デプロイ対応",
  ],
  en: [
    "Full implementation of 9-layer architecture (User Layer to Skill Registry)",
    "ZEO-Bench — 200-question test set for Judge Layer quantitative evaluation benchmark",
    "Cross-Model Verification improvements (semantic similarity, contradiction detection, confidence weighting)",
    "General-purpose domain Skill templates (content, competitive analysis, trends, KPI, strategy)",
    "Artifact Bridge enhancements — automated artifact linking, type conversion, pipeline design",
    "Self-Healing DAG chaos tests (20+ fault injection, recovery rate measurement)",
    "Runtime configuration management — set API keys without .env",
    "Knowledge Store — persistent memory for user settings, file permissions + change detection",
    "Natural language Skill generation engine (with 16 safety checks)",
    "Dynamic Model Registry (swap models without code changes)",
    "Avatar AI / Secretary AI / Chat tool integration Plugins",
    "MCP Server (8 tools, 4 resources, 2 prompts)",
    "Tauri v2 desktop app (Windows / macOS / Linux)",
    "Cloudflare Workers deployment support",
  ],
  zh: [
    "9层架构完整实现（User Layer 至 Skill Registry）",
    "ZEO-Bench — 200题测试集 Judge Layer 定量评估基准",
    "Cross-Model Verification 改进（语义相似度、矛盾检测、置信度加权）",
    "通用领域 Skill 模板（内容、竞争分析、趋势、KPI、策略）",
    "Artifact Bridge 强化 — 成果物自动关联、类型转换、流水线设计",
    "Self-Healing DAG 混沌测试（20+ 故障注入、恢复率测量）",
    "运行时配置管理 — 无需 .env 即可设置 API 密钥",
    "知识存储 — 用户设置、文件权限的持久记忆 + 变更检测",
    "自然语言 Skill 生成引擎（含 16 种安全检查）",
    "Dynamic Model Registry（无需代码更改即可替换模型）",
    "分身AI / 秘书AI / 聊天工具集成插件",
    "MCP 服务器（8 个工具、4 个资源、2 个提示）",
    "Tauri v2 桌面应用（Windows / macOS / Linux）",
    "Cloudflare Workers 部署支持",
  ],
}

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

const REPO = "OrosiTororo/Zero-Employee-Orchestrator"

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDownloads(count: number): string {
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`
  return `${count}`
}

const DATE_LOCALES: Record<Lang, string> = {
  ja: "ja-JP",
  en: "en-US",
  zh: "zh-CN",
}

function formatDate(iso: string, lang: Lang): string {
  return new Date(iso).toLocaleDateString(DATE_LOCALES[lang], {
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

function getGuiAsset(assets: ReleaseAsset[], os: "windows" | "macos" | "linux"): ReleaseAsset | null {
  for (const a of assets) {
    const lower = a.name.toLowerCase()
    if (os === "windows" && (lower.endsWith(".msi") || lower.endsWith(".exe"))) return a
    if (os === "macos" && lower.endsWith(".dmg")) return a
    if (os === "linux" && (lower.endsWith(".appimage") || lower.endsWith(".deb"))) return a
  }
  return null
}

function GuiInstallerGrid({ assets, lang }: { assets: ReleaseAsset[]; lang: Lang }) {
  const winAsset = getGuiAsset(assets, "windows")
  const macAsset = getGuiAsset(assets, "macos")
  const linuxAsset = getGuiAsset(assets, "linux")

  if (!winAsset && !macAsset && !linuxAsset) return null

  const platforms: Array<{
    icon: React.ComponentType<{ size?: number; className?: string }>
    os: string
    asset: ReleaseAsset | null
  }> = [
    { icon: Monitor, os: "Windows", asset: winAsset },
    { icon: Apple, os: "macOS", asset: macAsset },
    { icon: HardDrive, os: "Linux", asset: linuxAsset },
  ]

  return (
    <div className="px-4 pt-3 pb-1">
      <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-2">
        {t[lang].guiInstaller}
      </div>
      <div className="grid grid-cols-3 gap-2">
        {platforms.map(({ icon: Icon, os, asset }) =>
          asset ? (
            <a
              key={os}
              href={asset.browser_download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col gap-1 px-3 py-2.5 rounded border border-[#3e3e42] bg-[#1e1e1e] hover:border-[#007acc] transition-colors no-underline group"
              title={asset.name}
            >
              <div className="flex items-center gap-1.5">
                <Icon size={13} className="text-[#007acc] shrink-0" />
                <span className="text-[12px] font-medium text-[#cccccc]">{os}</span>
              </div>
              <div className="flex items-center justify-between gap-1">
                <span className="text-[10px] text-[#6a6a6a] truncate">
                  {asset.name}
                </span>
                <Download size={11} className="text-[#6a6a6a] group-hover:text-[#007acc] shrink-0" />
              </div>
            </a>
          ) : (
            <div
              key={os}
              className="flex flex-col gap-1 px-3 py-2.5 rounded border border-[#3e3e42] bg-[#1e1e1e] opacity-40"
            >
              <div className="flex items-center gap-1.5">
                <Icon size={13} className="text-[#6a6a6a] shrink-0" />
                <span className="text-[12px] font-medium text-[#cccccc]">{os}</span>
              </div>
              <div className="text-[10px] text-[#6a6a6a]">{t[lang].comingSoon}</div>
            </div>
          )
        )}
      </div>
    </div>
  )
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

function getFeatures(lang: Lang) {
  return [
    { icon: MessageSquare, label: "Design Interview", desc: t[lang].featureDesignInterview },
    { icon: FileText, label: "Spec / Plan / Tasks", desc: t[lang].featureSpecPlan },
    { icon: GitBranch, label: "Task Orchestrator", desc: t[lang].featureTaskOrchestrator },
    { icon: BrainCircuit, label: "Judge Layer", desc: t[lang].featureJudgeLayer },
    { icon: Activity, label: "Self-Healing", desc: t[lang].featureSelfHealing },
    { icon: Blocks, label: "Skill / Plugin / Extension", desc: t[lang].featureSkillPlugin },
    { icon: Shield, label: t[lang].approvalLabel, desc: t[lang].featureApproval },
    { icon: ScrollText, label: t[lang].auditLogLabel, desc: t[lang].featureAuditLog },
  ]
}

const CURRENT_VERSION = "v0.1.0"
const CURRENT_DATE = "2026-03-11"

interface BuiltinAsset {
  name: string
  os: string
  description: string
}

const EXPECTED_ASSETS: BuiltinAsset[] = [
  { name: `Zero-Employee-Orchestrator_0.1.0_x64_en-US.msi`, os: "Windows", description: "Windows インストーラー (.msi)" },
  { name: `Zero-Employee-Orchestrator_0.1.0_x64-setup.exe`, os: "Windows", description: "Windows インストーラー (.exe / NSIS)" },
  { name: `Zero-Employee-Orchestrator_0.1.0_aarch64.dmg`, os: "macOS", description: "macOS (Apple Silicon)" },
  { name: `Zero-Employee-Orchestrator_0.1.0_amd64.AppImage`, os: "Linux", description: "Portable (インストール不要)" },
  { name: `Zero-Employee-Orchestrator_0.1.0_amd64.deb`, os: "Linux", description: "Debian / Ubuntu" },
  { name: `Zero-Employee-Orchestrator_0.1.0_x86_64.rpm`, os: "Linux", description: "Fedora / RHEL" },
]

const LANG_TABS: Array<{ key: Lang; label: string }> = [
  { key: "ja", label: "日本語" },
  { key: "en", label: "English" },
  { key: "zh", label: "中文" },
]

export function ReleasesPage() {
  const [releases, setReleases] = useState<Release[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lang, setLang] = useState<Lang>("ja")

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
        throw new Error("__RATE_LIMIT__")
      }
      if (!res.ok) throw new Error("__FETCH_ERROR__")
      const data = await res.json()
      setReleases(data)
    } catch (e) {
      if (e instanceof Error && e.message === "__RATE_LIMIT__") {
        setError("__RATE_LIMIT__")
      } else if (e instanceof Error && e.message === "__FETCH_ERROR__") {
        setError("__FETCH_ERROR__")
      } else {
        setError("__FETCH_ERROR_FULL__")
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchReleases()
  }, [fetchReleases])

  const latestStable = releases.find((r) => !r.prerelease)
  const latestVersion = latestStable?.tag_name ?? null

  function getErrorMessage(errorKey: string): string {
    if (errorKey === "__RATE_LIMIT__") return t[lang].rateLimitError
    if (errorKey === "__FETCH_ERROR__") return t[lang].fetchErrorShort
    return t[lang].fetchError
  }

  const features = getFeatures(lang)

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        {/* Language Switcher */}
        <div className="flex items-center gap-1 mb-4">
          {LANG_TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setLang(key)}
              className={`px-3 py-1 rounded text-[12px] transition-colors ${
                lang === key
                  ? "bg-[#007acc] text-white"
                  : "bg-[#333333] text-[#cccccc] hover:bg-[#3e3e42]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Download size={22} className="text-[#007acc]" />
            <div>
              <h1 className="text-[18px] font-semibold text-[#cccccc]">
                Releases
              </h1>
              <p className="text-[12px] text-[#6a6a6a]">
                {t[lang].downloadTitle}
                <span className="ml-2 text-[#4ec9b0]">
                  {t[lang].latest} {latestVersion ?? CURRENT_VERSION}
                </span>
              </p>
            </div>
          </div>
          <button
            onClick={fetchReleases}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] text-[#cccccc] bg-[#333333] hover:bg-[#3e3e42] transition-colors disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            {t[lang].refresh}
          </button>
        </div>

        {/* Features */}
        <div className="mb-8 rounded border border-[#3e3e42] bg-[#252526] p-5">
          <h2 className="text-[14px] font-medium text-[#cccccc] mb-4">
            {t[lang].keyFeatures}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {features.map(({ icon: Icon, label, desc }) => (
              <div
                key={label}
                className="flex items-start gap-2.5 px-3 py-2.5 rounded bg-[#1e1e1e] border border-[#3e3e42]"
              >
                <Icon size={14} className="text-[#007acc] mt-0.5 shrink-0" />
                <div>
                  <div className="text-[12px] font-medium text-[#cccccc]">{label}</div>
                  <div className="text-[11px] text-[#6a6a6a]">{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Download Section */}
        <div className="mb-8 rounded border border-[#3e3e42] bg-[#252526] p-5">
          <h2 className="text-[14px] font-medium text-[#cccccc] mb-4">
            {t[lang].quickDownload}
            <span className="ml-2 text-[11px] text-[#6a6a6a] font-normal">
              ({latestVersion ?? CURRENT_VERSION})
            </span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <DownloadCard
              icon={Monitor}
              os="Windows"
              format=".msi / .exe"
              description={t[lang].downloadInstaller}
              href={findLatestAssetUrl(releases, "windows")}
              lang={lang}
            />
            <DownloadCard
              icon={Apple}
              os="macOS"
              format=".dmg"
              description={t[lang].downloadDiskImage}
              href={findLatestAssetUrl(releases, "macos")}
              lang={lang}
            />
            <DownloadCard
              icon={HardDrive}
              os="Linux"
              format=".AppImage / .deb"
              description={t[lang].downloadPackage}
              href={findLatestAssetUrl(releases, "linux")}
              lang={lang}
            />
          </div>

          <div className="rounded border border-[#3e3e42] bg-[#1e1e1e] p-3">
            <div className="flex items-center gap-2 mb-2">
              <Terminal size={14} className="text-[#4ec9b0]" />
              <span className="text-[12px] text-[#cccccc] font-medium">
                {t[lang].cliTui}
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
            {t[lang].loading}
          </div>
        )}

        {error && (
          <div className="rounded border border-[#f44747]/30 bg-[#f44747]/10 px-4 py-3 mb-4">
            <p className="text-[13px] text-[#f44747] mb-2">{getErrorMessage(error)}</p>
            <button
              onClick={fetchReleases}
              className="flex items-center gap-1.5 text-[12px] text-[#007acc] hover:underline"
            >
              <RefreshCw size={11} />
              {t[lang].retry}
            </button>
          </div>
        )}

        {!loading && !error && releases.length === 0 && (
          <div className="mb-4 rounded border border-[#007acc]/50 bg-[#252526] overflow-hidden">
            {/* Release Header */}
            <div className="px-4 py-3 border-b border-[#3e3e42]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Tag size={14} className="text-[#007acc]" />
                  <span className="text-[14px] font-medium text-[#cccccc]">
                    Zero-Employee Orchestrator {CURRENT_VERSION} — Platform v0.1 (Consolidated Release)
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#007acc]/20 text-[#007acc] flex items-center gap-1">
                    <Star size={9} />
                    Latest
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-[#6a6a6a]">
                  <span className="flex items-center gap-1">
                    <Clock size={11} />
                    {formatDate(CURRENT_DATE, lang)}
                  </span>
                </div>
              </div>
            </div>

            {/* Expected Assets */}
            <div className="px-4 pt-3 pb-1">
              <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-2">
                {t[lang].availableAssets}
              </div>
              <div className="grid grid-cols-3 gap-2 mb-3">
                {(["Windows", "macOS", "Linux"] as const).map((os) => {
                  const Icon = os === "Windows" ? Monitor : os === "macOS" ? Apple : HardDrive
                  const assets = EXPECTED_ASSETS.filter((a) => a.os === os)
                  return (
                    <div
                      key={os}
                      className="flex flex-col gap-1 px-3 py-2.5 rounded border border-[#3e3e42] bg-[#1e1e1e]"
                    >
                      <div className="flex items-center gap-1.5">
                        <Icon size={13} className="text-[#007acc] shrink-0" />
                        <span className="text-[12px] font-medium text-[#cccccc]">{os}</span>
                      </div>
                      {assets.map((a) => (
                        <div key={a.name} className="text-[10px] text-[#6a6a6a] truncate" title={a.name}>
                          {a.name}
                        </div>
                      ))}
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="px-4 py-3">
              <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-2">
                {t[lang].allAssets}
              </div>
              <div className="flex flex-col gap-1.5">
                {EXPECTED_ASSETS.map((asset) => {
                  const Icon = asset.os === "Windows" ? Monitor : asset.os === "macOS" ? Apple : HardDrive
                  return (
                    <div
                      key={asset.name}
                      className="flex items-center justify-between px-3 py-2 rounded bg-[#1e1e1e]"
                    >
                      <div className="flex items-center gap-2">
                        <Icon size={14} className="text-[#6a6a6a]" />
                        <span className="text-[12px] text-[#cccccc]">{asset.name}</span>
                        <span className="text-[11px] text-[#6a6a6a]">({asset.os})</span>
                      </div>
                      <span className="text-[11px] text-[#6a6a6a]">{asset.description}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Release Highlights */}
            <div className="px-4 py-3 border-t border-[#3e3e42]">
              <details open>
                <summary className="text-[12px] text-[#007acc] cursor-pointer hover:underline">
                  {t[lang].releaseNotes}
                </summary>
                <div className="mt-2 text-[12px] text-[#9a9a9a] leading-relaxed space-y-1">
                  <div className="text-[#569cd6] font-semibold text-[13px] mb-2">
                    v0.1.0 — Platform v0.1 (Consolidated Release)
                  </div>
                  <div className="text-[#4ec9b0] font-medium mb-1">{t[lang].keyNewFeatures}</div>
                  {RELEASE_HIGHLIGHTS[lang].map((item, i) => (
                    <div key={i}>
                      <span className="text-[#6a6a6a]">•</span> {item}
                    </div>
                  ))}
                </div>
              </details>
            </div>

            {/* Link to GitHub */}
            <div className="px-4 py-2 border-t border-[#3e3e42]">
              <a
                href={`https://github.com/${REPO}/releases`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[11px] text-[#6a6a6a] hover:text-[#007acc]"
              >
                {t[lang].viewOnGithub}
                <ExternalLink size={10} />
              </a>
            </div>
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
                        <span className="flex items-center gap-1" title={t[lang].totalDownloads}>
                          <BarChart3 size={11} />
                          {formatDownloads(totalDownloads)}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock size={11} />
                        {formatDate(release.published_at, lang)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Assets */}
                {release.assets.length > 0 && (
                  <div>
                    {/* GUI Installer cards */}
                    <GuiInstallerGrid assets={release.assets} lang={lang} />

                    {/* Full asset list */}
                    <div className="px-4 py-3">
                      <div className="text-[11px] uppercase tracking-wider text-[#6a6a6a] mb-2">
                        {t[lang].allAssets}
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
                                  title={t[lang].downloads}
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
                  </div>
                )}

                {release.assets.length === 0 && (
                  <div className="px-4 py-3 text-[12px] text-[#6a6a6a]">
                    {t[lang].noAssets}
                    <a
                      href={release.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#007acc] hover:underline ml-1"
                    >
                      {t[lang].checkOnGithub}
                    </a>
                  </div>
                )}

                {/* Release Notes */}
                {release.body && (
                  <div className="px-4 py-3 border-t border-[#3e3e42]">
                    <details>
                      <summary className="text-[12px] text-[#007acc] cursor-pointer hover:underline">
                        {t[lang].showReleaseNotes}
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
                    {t[lang].viewOnGithub}
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
  lang,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  os: string
  format: string
  description: string
  href: string | null
  lang: Lang
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
      title={t[lang].availableWhenPublished}
    >
      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} className="text-[#6a6a6a]" />
        <span className="text-[13px] font-medium text-[#cccccc]">{os}</span>
      </div>
      <div className="text-[11px] text-[#6a6a6a]">{format}</div>
      <div className="text-[11px] text-[#6a6a6a] mt-1">{t[lang].comingSoon}</div>
    </div>
  )
}
