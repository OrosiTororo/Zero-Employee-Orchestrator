import { useCallback, useEffect, useState } from "react"
import { RefreshCw, Send, Users, UsersRound } from "lucide-react"
import { useT } from "@/shared/i18n"
import { api, ApiError } from "@/shared/api/client"
import { useToastStore } from "@/shared/ui/ErrorToast"
import { PresetCard } from "@/shared/ui/PresetCard"
import { Modal } from "@/shared/ui/Modal"

interface PresetRole {
  name: string
  description: string
}

interface CrewMember {
  role: string
  preferred_model: string
  description: string
  status: string
  tokens_used: number
}

interface Crew {
  id: string
  name: string
  execution_mode: string
  created_at: string
  last_run_at: string | null
  members: CrewMember[]
  last_run_results: Array<{ role: string; status: string; content?: string; error?: string }>
}

export function CrewsPage() {
  const t = useT()
  const addToast = useToastStore((s) => s.addToast)
  const [presets, setPresets] = useState<Record<string, PresetRole[]>>({})
  const [crews, setCrews] = useState<Crew[]>([])
  const [loading, setLoading] = useState(true)

  const [spawnPreset, setSpawnPreset] = useState<string | null>(null)
  const [crewName, setCrewName] = useState("")
  const [spawning, setSpawning] = useState(false)

  const [dispatchCrew, setDispatchCrew] = useState<Crew | null>(null)
  const [instruction, setInstruction] = useState("")
  const [dispatching, setDispatching] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [presetsRes, crewsRes] = await Promise.all([
        api.get<{ presets: Record<string, PresetRole[]> }>("/crews/presets"),
        api.get<{ crews: Crew[] }>("/crews"),
      ])
      setPresets(presetsRes.presets ?? {})
      setCrews(crewsRes.crews ?? [])
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : t.crews.loadFailed ?? "Could not load crews."
      addToast(msg)
    } finally {
      setLoading(false)
    }
  }, [addToast, t.crews.loadFailed])

  useEffect(() => {
    load()
  }, [load])

  const openSpawn = (preset: string) => {
    setSpawnPreset(preset)
    setCrewName(`${preset} crew`)
  }

  const submitSpawn = async () => {
    if (!spawnPreset) return
    if (!crewName.trim()) {
      addToast(t.crews.nameRequired ?? "Crew name is required.")
      return
    }
    setSpawning(true)
    try {
      await api.post("/crews", { name: crewName.trim(), preset: spawnPreset })
      setSpawnPreset(null)
      await load()
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : t.crews.spawnFailed ?? "Spawn failed."
      addToast(msg)
    } finally {
      setSpawning(false)
    }
  }

  const openDispatch = (crew: Crew) => {
    setDispatchCrew(crew)
    setInstruction("")
  }

  const submitDispatch = async () => {
    if (!dispatchCrew) return
    if (!instruction.trim()) {
      addToast(t.crews.instructionRequired ?? "Instruction is required.")
      return
    }
    setDispatching(true)
    try {
      await api.post(`/crews/${dispatchCrew.id}/dispatch`, {
        instruction: instruction.trim(),
        per_role_context: {},
      })
      setDispatchCrew(null)
      await load()
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : t.crews.dispatchFailed ?? "Dispatch failed."
      addToast(msg)
    } finally {
      setDispatching(false)
    }
  }

  const disband = async (id: string) => {
    try {
      await api.delete(`/crews/${id}`)
      await load()
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : t.crews.disbandFailed ?? "Disband failed."
      addToast(msg)
    }
  }

  const presetEntries = Object.entries(presets)

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[900px] mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <UsersRound size={18} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-medium text-[var(--text-primary)]">{t.crews.title}</h2>
            <span className="text-[11px] text-[var(--text-muted)]">
              {crews.length} {t.crews.active}
            </span>
          </div>
          <button
            onClick={load}
            aria-label={t.crews.refresh}
            className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-[var(--accent)]"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            {t.crews.refresh}
          </button>
        </div>
        <p className="text-[12px] text-[var(--text-muted)] mb-5">{t.crews.subtitle}</p>

        <section className="mb-8">
          <h3 className="text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
            {t.crews.presetsHeading}
          </h3>
          {loading ? (
            <div className="py-6 text-center text-[12px] text-[var(--text-muted)]">
              <RefreshCw size={16} className="mx-auto mb-1 animate-spin text-[var(--accent)]" />
              {t.common.loading ?? "Loading..."}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {presetEntries.map(([slug, roles]) => (
                <PresetCard
                  key={slug}
                  title={slug}
                  subtitle={`${roles.length} ${t.crews.roles}`}
                  description={roles.map((r) => r.name).join(" • ")}
                  badges={[t.crews.preset]}
                  icon={<Users size={14} />}
                  actionLabel={t.crews.spawn}
                  ariaLabel={`${t.crews.spawn}: ${slug}`}
                  onAction={() => openSpawn(slug)}
                />
              ))}
            </div>
          )}
        </section>

        <section>
          <h3 className="text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
            {t.crews.activeHeading}
          </h3>
          {crews.length === 0 ? (
            <div className="rounded px-4 py-10 text-center border border-[var(--border)]">
              <p className="text-[12px] text-[var(--text-muted)]">{t.crews.empty}</p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {crews.map((crew) => (
                <div
                  key={crew.id}
                  className="rounded border border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <UsersRound size={14} className="text-[var(--accent)] shrink-0" />
                      <span className="text-[13px] text-[var(--text-primary)] truncate">
                        {crew.name}
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)]">
                        {crew.execution_mode}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openDispatch(crew)}
                        aria-label={`${t.crews.dispatch}: ${crew.name}`}
                        className="flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-[var(--accent)] text-[var(--accent-fg)]"
                      >
                        <Send size={11} />
                        {t.crews.dispatch}
                      </button>
                      <button
                        onClick={() => disband(crew.id)}
                        aria-label={`${t.crews.disband}: ${crew.name}`}
                        className="px-2 py-1 rounded text-[11px] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                      >
                        {t.crews.disband}
                      </button>
                    </div>
                  </div>
                  <ul className="text-[11px] text-[var(--text-secondary)] space-y-0.5">
                    {crew.members.map((m) => (
                      <li key={m.role} className="flex items-center gap-2">
                        <span className="text-[var(--text-primary)]">{m.role}</span>
                        <span className="text-[var(--text-muted)]">← {m.preferred_model}</span>
                        <span className="text-[var(--text-muted)]">({m.status})</span>
                      </li>
                    ))}
                  </ul>
                  {crew.last_run_results.length > 0 ? (
                    <div className="mt-2 text-[11px] text-[var(--text-muted)]">
                      {t.crews.lastRun}: {crew.last_run_results.length}{" "}
                      {t.crews.membersResponded}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <Modal
        open={spawnPreset !== null}
        onClose={() => setSpawnPreset(null)}
        title={spawnPreset ? `${t.crews.spawn}: ${spawnPreset}` : ""}
        footer={
          <>
            <button
              onClick={() => setSpawnPreset(null)}
              className="px-3 py-1.5 rounded text-[12px] border border-[var(--border)] text-[var(--text-secondary)]"
            >
              {t.common.cancel ?? "Cancel"}
            </button>
            <button
              onClick={submitSpawn}
              disabled={spawning}
              className="px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)] disabled:opacity-50"
            >
              {spawning ? t.common.working ?? "Working..." : t.crews.spawn}
            </button>
          </>
        }
      >
        <label className="flex flex-col gap-1">
          <span className="text-[11px] text-[var(--text-muted)]">{t.crews.crewName}</span>
          <input
            autoFocus
            value={crewName}
            onChange={(e) => setCrewName(e.target.value)}
            placeholder={t.crews.crewNamePlaceholder}
            className="px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
          />
        </label>
        {spawnPreset && presets[spawnPreset] ? (
          <div className="mt-3">
            <div className="text-[11px] text-[var(--text-muted)] mb-1">{t.crews.rolesInPreset}</div>
            <ul className="text-[12px] text-[var(--text-secondary)] space-y-0.5">
              {presets[spawnPreset].map((r) => (
                <li key={r.name}>
                  <span className="text-[var(--text-primary)]">{r.name}</span>
                  {r.description ? (
                    <span className="text-[var(--text-muted)]"> — {r.description}</span>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Modal>

      <Modal
        open={dispatchCrew !== null}
        onClose={() => setDispatchCrew(null)}
        title={dispatchCrew ? `${t.crews.dispatch}: ${dispatchCrew.name}` : ""}
        footer={
          <>
            <button
              onClick={() => setDispatchCrew(null)}
              className="px-3 py-1.5 rounded text-[12px] border border-[var(--border)] text-[var(--text-secondary)]"
            >
              {t.common.cancel ?? "Cancel"}
            </button>
            <button
              onClick={submitDispatch}
              disabled={dispatching}
              className="px-3 py-1.5 rounded text-[12px] bg-[var(--accent)] text-[var(--accent-fg)] disabled:opacity-50"
            >
              {dispatching ? t.common.working ?? "Working..." : t.crews.dispatch}
            </button>
          </>
        }
      >
        <label className="flex flex-col gap-1">
          <span className="text-[11px] text-[var(--text-muted)]">{t.crews.instruction}</span>
          <textarea
            autoFocus
            rows={4}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder={t.crews.instructionPlaceholder}
            className="px-3 py-2 rounded text-[12px] outline-none bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent)]"
          />
        </label>
      </Modal>
    </div>
  )
}
