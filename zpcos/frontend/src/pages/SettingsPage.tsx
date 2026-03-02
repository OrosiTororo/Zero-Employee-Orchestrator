import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { Link2, Unlink, FolderOpen, Save } from "lucide-react";
import * as api from "@/lib/api";

export function SettingsPage() {
  const { connections, fetchConnections } = useAuth();
  const [qualityMode, setQualityMode] = useState("balanced");
  const [allowedDirs, setAllowedDirs] = useState<string[]>([]);
  const [newDir, setNewDir] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConnections();
    api.getSettings().then((s: unknown) => {
      const settings = s as { quality_mode?: string; allowed_dirs?: string[] };
      if (settings.quality_mode) setQualityMode(settings.quality_mode);
      if (settings.allowed_dirs) setAllowedDirs(settings.allowed_dirs);
    }).catch(console.error);
  }, [fetchConnections]);

  const handleConnect = async (service: string) => {
    try {
      await api.authConnect(service);
      await fetchConnections();
    } catch (e) {
      console.error("Connect failed:", e);
    }
  };

  const handleDisconnect = async (service: string) => {
    try {
      await api.authDisconnect(service);
      await fetchConnections();
    } catch (e) {
      console.error("Disconnect failed:", e);
    }
  };

  const addDir = () => {
    if (newDir.trim() && !allowedDirs.includes(newDir.trim())) {
      setAllowedDirs([...allowedDirs, newDir.trim()]);
      setNewDir("");
    }
  };

  const removeDir = (dir: string) => {
    setAllowedDirs(allowedDirs.filter((d) => d !== dir));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateSettings({ quality_mode: qualityMode, allowed_dirs: allowedDirs });
    } catch (e) {
      console.error("Save failed:", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[640px] mx-auto px-6 py-6">
        {/* Line numbers gutter - VSCode style */}
        <div className="font-mono text-[13px]" style={{ color: '#cccccc' }}>
          {/* Comment header */}
          <div style={{ color: '#6a9955' }}>{"// Settings"}</div>
          <div className="h-4" />

          {/* Connections */}
          <div style={{ color: '#569cd6' }}>{"export"}</div>
          <div className="mb-4">
            <span style={{ color: '#569cd6' }}>const </span>
            <span style={{ color: '#9cdcfe' }}>connections</span>
            <span style={{ color: '#d4d4d4' }}> = {"{"}</span>
          </div>

          <div className="pl-6 mb-6">
            {connections.map((conn) => (
              <div
                key={conn.service}
                className="flex items-center justify-between rounded px-3 py-2 mb-2"
                style={{ background: '#252526', border: '1px solid #3e3e42' }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ background: conn.connected ? '#4ec9b0' : '#6a6a6a' }}
                  />
                  <div>
                    <div className="text-[13px]" style={{ color: '#cccccc' }}>
                      {conn.display_name}
                    </div>
                    <div className="text-[11px]" style={{ color: '#6a6a6a' }}>
                      {conn.service}
                    </div>
                  </div>
                </div>
                {conn.connected ? (
                  <button
                    onClick={() => handleDisconnect(conn.service)}
                    className="flex items-center gap-1 px-2 py-1 rounded text-[11px]"
                    style={{ border: '1px solid #3e3e42', color: '#f44747' }}
                  >
                    <Unlink size={12} />
                    Disconnect
                  </button>
                ) : (
                  <button
                    onClick={() => handleConnect(conn.service)}
                    className="flex items-center gap-1 px-2 py-1 rounded text-[11px]"
                    style={{ background: '#007acc', color: '#ffffff' }}
                  >
                    <Link2 size={12} />
                    Connect
                  </button>
                )}
              </div>
            ))}
          </div>

          <div style={{ color: '#d4d4d4' }}>{"}"}</div>
          <div className="h-4" />

          {/* Quality Mode */}
          <div style={{ color: '#569cd6' }}>const </div>
          <div className="mb-2">
            <span style={{ color: '#9cdcfe' }}>qualityMode</span>
            <span style={{ color: '#d4d4d4' }}> = </span>
          </div>
          <div className="pl-6 flex gap-2 mb-6">
            {(["fastest", "balanced", "high_quality"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setQualityMode(mode)}
                className="px-3 py-1.5 rounded text-[12px]"
                style={{
                  background: qualityMode === mode ? '#007acc' : 'transparent',
                  color: qualityMode === mode ? '#ffffff' : '#cccccc',
                  border: `1px solid ${qualityMode === mode ? '#007acc' : '#3e3e42'}`,
                }}
              >
                {mode === "fastest" ? "Fastest" : mode === "balanced" ? "Balanced" : "High Quality"}
              </button>
            ))}
          </div>

          {/* Allowed Directories */}
          <div style={{ color: '#569cd6' }}>const </div>
          <div className="mb-2">
            <span style={{ color: '#9cdcfe' }}>allowedDirectories</span>
            <span style={{ color: '#d4d4d4' }}> = [</span>
          </div>
          <div className="pl-6 mb-2">
            {allowedDirs.map((dir) => (
              <div
                key={dir}
                className="flex items-center justify-between rounded px-3 py-1.5 mb-1"
                style={{ background: '#252526', border: '1px solid #3e3e42' }}
              >
                <div className="flex items-center gap-2">
                  <FolderOpen size={13} style={{ color: '#dcdcaa' }} />
                  <span className="text-[12px] font-mono" style={{ color: '#ce9178' }}>
                    "{dir}"
                  </span>
                </div>
                <button
                  onClick={() => removeDir(dir)}
                  className="text-[11px] px-1.5"
                  style={{ color: '#f44747' }}
                >
                  ×
                </button>
              </div>
            ))}
            <div className="flex gap-2 mt-2">
              <input
                value={newDir}
                onChange={(e) => setNewDir(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addDir()}
                placeholder="C:\Users\you\Documents"
                className="flex-1 px-3 py-1.5 rounded text-[12px] font-mono outline-none"
                style={{ background: '#3c3c3c', color: '#cccccc', border: '1px solid #3e3e42' }}
              />
              <button
                onClick={addDir}
                className="px-3 py-1.5 rounded text-[12px]"
                style={{ border: '1px solid #3e3e42', color: '#cccccc' }}
              >
                Add
              </button>
            </div>
          </div>
          <div style={{ color: '#d4d4d4' }}>]</div>
          <div className="h-6" />

          {/* Save */}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 rounded text-[12px]"
            style={{ background: '#007acc', color: '#ffffff' }}
          >
            <Save size={14} />
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}
