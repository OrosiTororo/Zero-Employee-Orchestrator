import { useState, useEffect, useCallback } from "react"
import {
  Shield,
  FolderOpen,
  FileText,
  RefreshCw,
  Plus,
  Check,
  Bell,
  Eye,
} from "lucide-react"
import { api } from "../shared/api/client"

interface Permission {
  id: string
  path: string
  permission: string
}

interface FolderLocation {
  id: string
  name: string
  path: string
}

interface Change {
  id: string
  entity_type: string
  change_type: string
  old_value: string | null
  new_value: string | null
  detected_at: string
  acknowledged: boolean
}

export function PermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [folders, setFolders] = useState<FolderLocation[]>([])
  const [changes, setChanges] = useState<Change[]>([])
  const [tab, setTab] = useState<"permissions" | "folders" | "changes">("permissions")
  const [newPath, setNewPath] = useState("")
  const [newPerm, setNewPerm] = useState("read")
  const [newFolderName, setNewFolderName] = useState("")
  const [newFolderPath, setNewFolderPath] = useState("")

  const fetchData = useCallback(async () => {
    try {
      const [perms, fldrs, chgs] = await Promise.all([
        api.get<{ permissions: Permission[] }>("/knowledge/permissions").catch((e) => { console.warn("Permissions:", e); return { permissions: [] } }),
        api.get<{ folders: FolderLocation[] }>("/knowledge/folders").catch((e) => { console.warn("Folders:", e); return { folders: [] } }),
        api.get<{ changes: Change[] }>("/knowledge/changes").catch((e) => { console.warn("Changes:", e); return { changes: [] } }),
      ])
      setPermissions(perms.permissions)
      setFolders(fldrs.folders)
      setChanges(chgs.changes)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const addPermission = async () => {
    if (!newPath.trim()) return
    await api.post("/knowledge/file-permission", { path: newPath, permission: newPerm })
    setNewPath("")
    fetchData()
  }

  const addFolder = async () => {
    if (!newFolderName.trim() || !newFolderPath.trim()) return
    await api.post("/knowledge/folder-location", { name: newFolderName, path: newFolderPath })
    setNewFolderName("")
    setNewFolderPath("")
    fetchData()
  }

  const acknowledgeChange = async (id: string) => {
    await api.post(`/knowledge/changes/${id}/acknowledge`)
    fetchData()
  }

  const tabs = [
    { key: "permissions" as const, label: "ファイル権限", icon: Shield },
    { key: "folders" as const, label: "フォルダ位置", icon: FolderOpen },
    { key: "changes" as const, label: "変更検知", icon: Bell },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[16px] font-semibold text-[var(--text-primary)]">
              権限とナレッジ管理
            </h1>
            <p className="text-[12px] text-[var(--text-muted)] mt-0.5">
              AIエージェントのファイルアクセス権限と業務フォルダの記憶管理
            </p>
          </div>
          <button onClick={fetchData} className="p-2 rounded-md hover:bg-[var(--bg-hover)]">
            <RefreshCw size={14} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-[var(--border)]">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 px-4 py-2 text-[12px] border-b-2 transition-colors ${
                tab === key
                  ? "border-[var(--accent)] text-[var(--accent)]"
                  : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              <Icon size={13} />
              {label}
              {key === "changes" && changes.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-[var(--error)] text-white text-[10px]">
                  {changes.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Permissions Tab */}
        {tab === "permissions" && (
          <div>
            <div className="flex gap-2 mb-4">
              <input
                value={newPath}
                onChange={e => setNewPath(e.target.value)}
                placeholder="ファイル/フォルダパス"
                className="flex-1 px-3 py-2 text-[12px] rounded-md border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] outline-none"
              />
              <select
                value={newPerm}
                onChange={e => setNewPerm(e.target.value)}
                className="px-3 py-2 text-[12px] rounded-md border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)]"
              >
                <option value="read">読み取り</option>
                <option value="write">書き込み</option>
                <option value="execute">実行</option>
                <option value="full">フルアクセス</option>
              </select>
              <button onClick={addPermission} className="px-3 py-2 rounded-md bg-[var(--accent)] text-white text-[12px] flex items-center gap-1">
                <Plus size={12} /> 追加
              </button>
            </div>

            {permissions.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                まだ権限が設定されていません
              </div>
            ) : (
              <div className="space-y-2">
                {permissions.map(p => (
                  <div key={p.id} className="flex items-center gap-3 px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                    <FileText size={14} className="text-[var(--text-muted)]" />
                    <span className="flex-1 text-[12px] text-[var(--text-primary)] font-mono">{p.path}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                      p.permission === "full" ? "bg-green-100 text-green-700" :
                      p.permission === "write" ? "bg-blue-100 text-blue-700" :
                      p.permission === "read" ? "bg-gray-100 text-gray-700" :
                      "bg-yellow-100 text-yellow-700"
                    }`}>
                      {p.permission}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Folders Tab */}
        {tab === "folders" && (
          <div>
            <div className="flex gap-2 mb-4">
              <input
                value={newFolderName}
                onChange={e => setNewFolderName(e.target.value)}
                placeholder="フォルダ名（例: 業務資料）"
                className="w-1/3 px-3 py-2 text-[12px] rounded-md border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] outline-none"
              />
              <input
                value={newFolderPath}
                onChange={e => setNewFolderPath(e.target.value)}
                placeholder="パス（例: /Documents/Work）"
                className="flex-1 px-3 py-2 text-[12px] rounded-md border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] outline-none"
              />
              <button onClick={addFolder} className="px-3 py-2 rounded-md bg-[var(--accent)] text-white text-[12px] flex items-center gap-1">
                <Plus size={12} /> 追加
              </button>
            </div>

            {folders.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                まだフォルダ位置が登録されていません
              </div>
            ) : (
              <div className="space-y-2">
                {folders.map(f => (
                  <div key={f.id} className="flex items-center gap-3 px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                    <FolderOpen size={14} className="text-[var(--accent)]" />
                    <span className="text-[12px] font-medium text-[var(--text-primary)]">{f.name}</span>
                    <span className="flex-1 text-[12px] text-[var(--text-muted)] font-mono">{f.path}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Changes Tab */}
        {tab === "changes" && (
          <div>
            {changes.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-[var(--text-muted)]">
                未確認の変更はありません
              </div>
            ) : (
              <div className="space-y-2">
                {changes.map(c => (
                  <div key={c.id} className="flex items-start gap-3 px-4 py-3 rounded-md border border-[var(--border)] bg-[var(--bg-surface)]">
                    <Eye size={14} className="text-[var(--warning)] mt-0.5" />
                    <div className="flex-1">
                      <div className="text-[12px] text-[var(--text-primary)]">
                        <span className="font-medium">{c.entity_type}</span>
                        <span className={`ml-2 px-1.5 py-0.5 rounded text-[10px] ${
                          c.change_type === "created" ? "bg-green-100 text-green-700" :
                          c.change_type === "updated" ? "bg-blue-100 text-blue-700" :
                          "bg-red-100 text-red-700"
                        }`}>{c.change_type}</span>
                      </div>
                      {c.old_value && (
                        <div className="text-[11px] text-[var(--text-muted)] mt-1">
                          変更前: <span className="line-through">{c.old_value}</span>
                        </div>
                      )}
                      {c.new_value && (
                        <div className="text-[11px] text-[var(--text-primary)] mt-0.5">
                          変更後: {c.new_value}
                        </div>
                      )}
                      <div className="text-[10px] text-[var(--text-muted)] mt-1">{c.detected_at}</div>
                    </div>
                    <button
                      onClick={() => acknowledgeChange(c.id)}
                      className="px-2 py-1 rounded text-[10px] border border-[var(--border)] hover:bg-[var(--bg-hover)]"
                    >
                      <Check size={11} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
