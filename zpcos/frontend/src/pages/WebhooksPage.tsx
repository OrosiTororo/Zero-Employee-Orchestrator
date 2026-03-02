import { useState, useEffect } from "react";
import {
  Webhook, Plus, Trash2, Play, CheckCircle, XCircle,
  ChevronRight, Copy, Eye, EyeOff,
} from "lucide-react";
import * as api from "@/lib/api";

const ALL_EVENTS = [
  "orchestration.started",
  "orchestration.completed",
  "orchestration.failed",
  "skill.generated",
  "skill.executed",
  "heal.attempt",
  "judge.completed",
  "interview.completed",
  "task.transition",
];

export function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<api.WebhookConfig[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newEvents, setNewEvents] = useState<string[]>([...ALL_EVENTS]);
  const [creating, setCreating] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deliveries, setDeliveries] = useState<api.WebhookDelivery[]>([]);
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set());

  const load = async () => {
    try {
      const data = await api.listWebhooks();
      setWebhooks(data);
    } catch (e) {
      console.error("Failed to load webhooks:", e);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!newUrl.trim()) return;
    setCreating(true);
    try {
      await api.createWebhook({
        name: newName || "Untitled",
        url: newUrl,
        events: newEvents,
      });
      setNewName("");
      setNewUrl("");
      setNewEvents([...ALL_EVENTS]);
      setShowCreate(false);
      await load();
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    await api.deleteWebhook(id);
    if (expandedId === id) setExpandedId(null);
    await load();
  };

  const handleTest = async (id: string) => {
    await api.testWebhook(id);
    if (expandedId === id) {
      const d = await api.getWebhookDeliveries(id);
      setDeliveries(d);
    }
    await load();
  };

  const handleToggle = async (wh: api.WebhookConfig) => {
    await api.updateWebhook(wh.id, { active: !wh.active });
    await load();
  };

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    const d = await api.getWebhookDeliveries(id);
    setDeliveries(d);
  };

  const toggleSecret = (id: string) => {
    setVisibleSecrets((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const copySecret = (secret: string) => {
    navigator.clipboard.writeText(secret);
  };

  const toggleEvent = (event: string) => {
    setNewEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[800px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Webhook size={16} style={{ color: '#007acc' }} />
            <h2 className="text-[14px] font-medium" style={{ color: '#cccccc' }}>
              Webhooks
            </h2>
            <span className="text-[11px] px-1.5 py-0.5 rounded" style={{ background: '#1a3a5c', color: '#9cdcfe' }}>
              n8n compatible
            </span>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px]"
            style={{ background: '#007acc', color: '#ffffff' }}
          >
            <Plus size={13} />
            New Webhook
          </button>
        </div>

        {/* n8n hint */}
        <div
          className="rounded p-3 mb-4 text-[12px]"
          style={{ background: '#252526', border: '1px solid #3e3e42', color: '#969696' }}
        >
          n8n連携: Webhook URLにn8nのWebhook Triggerノードのエンドポイントを設定してください。
          <span style={{ color: '#9cdcfe' }}> X-ZPCOS-Signature</span> ヘッダーでHMAC-SHA256署名を検証できます。
        </div>

        {/* Create Form */}
        {showCreate && (
          <div
            className="rounded p-4 mb-4"
            style={{ background: '#252526', border: '1px solid #007acc' }}
          >
            <div className="text-[11px] uppercase tracking-wider mb-3" style={{ color: '#6a6a6a' }}>
              New Webhook
            </div>

            <div className="flex flex-col gap-3">
              <div className="flex gap-3">
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Name (e.g., n8n Production)"
                  className="flex-1 px-3 py-1.5 rounded text-[12px] outline-none"
                  style={{ background: '#3c3c3c', color: '#cccccc', border: '1px solid #3e3e42' }}
                />
                <input
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  placeholder="https://your-n8n.example.com/webhook/..."
                  className="flex-[2] px-3 py-1.5 rounded text-[12px] font-mono outline-none"
                  style={{ background: '#3c3c3c', color: '#cccccc', border: '1px solid #3e3e42' }}
                />
              </div>

              {/* Event Selection */}
              <div>
                <div className="text-[11px] mb-1.5" style={{ color: '#6a6a6a' }}>Events</div>
                <div className="flex flex-wrap gap-1.5">
                  {ALL_EVENTS.map((event) => (
                    <button
                      key={event}
                      onClick={() => toggleEvent(event)}
                      className="px-2 py-1 rounded text-[11px] font-mono"
                      style={{
                        background: newEvents.includes(event) ? '#1a3a5c' : 'transparent',
                        color: newEvents.includes(event) ? '#9cdcfe' : '#6a6a6a',
                        border: `1px solid ${newEvents.includes(event) ? '#007acc' : '#3e3e42'}`,
                      }}
                    >
                      {event}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleCreate}
                  disabled={!newUrl.trim() || creating}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded text-[12px]"
                  style={{
                    background: newUrl.trim() && !creating ? '#007acc' : '#3e3e42',
                    color: '#ffffff',
                  }}
                >
                  {creating ? "Creating..." : "Create"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Webhook List */}
        <div className="flex flex-col gap-2">
          {webhooks.length === 0 && (
            <div className="text-[12px] py-8 text-center" style={{ color: '#6a6a6a' }}>
              No webhooks configured
            </div>
          )}

          {webhooks.map((wh) => (
            <div key={wh.id}>
              <div
                className="rounded px-3 py-2.5 flex items-center gap-3 cursor-pointer"
                style={{ background: '#252526', border: `1px solid ${expandedId === wh.id ? '#007acc' : '#3e3e42'}` }}
                onClick={() => handleExpand(wh.id)}
              >
                <ChevronRight
                  size={13}
                  className={`transition-transform ${expandedId === wh.id ? "rotate-90" : ""}`}
                  style={{ color: '#6a6a6a' }}
                />
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ background: wh.active ? '#4ec9b0' : '#6a6a6a' }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] truncate" style={{ color: '#cccccc' }}>
                      {wh.name}
                    </span>
                    {wh.failure_count > 0 && (
                      <span className="text-[10px] px-1 rounded" style={{ background: '#4a1a1a', color: '#f44747' }}>
                        {wh.failure_count} failures
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] font-mono truncate" style={{ color: '#6a6a6a' }}>
                    {wh.url}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={(e) => { e.stopPropagation(); handleTest(wh.id); }}
                    className="p-1 rounded"
                    style={{ color: '#969696' }}
                    title="Test"
                  >
                    <Play size={13} />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleToggle(wh); }}
                    className="p-1 rounded text-[11px]"
                    style={{ color: wh.active ? '#4ec9b0' : '#6a6a6a' }}
                    title={wh.active ? "Disable" : "Enable"}
                  >
                    {wh.active ? "ON" : "OFF"}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(wh.id); }}
                    className="p-1 rounded"
                    style={{ color: '#f44747' }}
                    title="Delete"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedId === wh.id && (
                <div
                  className="rounded-b px-4 py-3 -mt-px flex flex-col gap-3"
                  style={{ background: '#1e1e1e', border: '1px solid #007acc', borderTop: 'none' }}
                >
                  {/* Secret */}
                  <div>
                    <div className="text-[11px] mb-1" style={{ color: '#6a6a6a' }}>Secret (HMAC-SHA256)</div>
                    <div className="flex items-center gap-2">
                      <code
                        className="flex-1 text-[11px] px-2 py-1 rounded font-mono"
                        style={{ background: '#252526', color: '#ce9178' }}
                      >
                        {visibleSecrets.has(wh.id) ? wh.secret : "••••••••••••••••"}
                      </code>
                      <button onClick={() => toggleSecret(wh.id)} className="p-1" style={{ color: '#969696' }}>
                        {visibleSecrets.has(wh.id) ? <EyeOff size={13} /> : <Eye size={13} />}
                      </button>
                      <button onClick={() => copySecret(wh.secret)} className="p-1" style={{ color: '#969696' }}>
                        <Copy size={13} />
                      </button>
                    </div>
                  </div>

                  {/* Events */}
                  <div>
                    <div className="text-[11px] mb-1" style={{ color: '#6a6a6a' }}>Subscribed Events</div>
                    <div className="flex flex-wrap gap-1">
                      {wh.events.map((ev) => (
                        <span
                          key={ev}
                          className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                          style={{ background: '#1a3a5c', color: '#9cdcfe' }}
                        >
                          {ev}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Recent Deliveries */}
                  <div>
                    <div className="text-[11px] mb-1" style={{ color: '#6a6a6a' }}>Recent Deliveries</div>
                    {deliveries.length === 0 ? (
                      <div className="text-[11px]" style={{ color: '#6a6a6a' }}>No deliveries yet</div>
                    ) : (
                      <div className="flex flex-col gap-1">
                        {deliveries.slice(0, 10).map((d) => (
                          <div
                            key={d.id}
                            className="flex items-center gap-2 px-2 py-1 rounded text-[11px]"
                            style={{ background: '#252526' }}
                          >
                            {d.success
                              ? <CheckCircle size={12} style={{ color: '#4ec9b0' }} />
                              : <XCircle size={12} style={{ color: '#f44747' }} />
                            }
                            <span className="font-mono" style={{ color: '#9cdcfe' }}>{d.event}</span>
                            <span style={{ color: '#6a6a6a' }}>
                              {d.status_code ?? "—"} · attempt {d.attempt}
                            </span>
                            <span className="flex-1" />
                            <span style={{ color: '#6a6a6a' }}>
                              {new Date(d.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
