import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Package, Search } from "lucide-react";
import * as api from "@/lib/api";

interface Skill {
  name: string;
  description: string;
  version?: string;
}

export function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.listSkills().then(setSkills).catch(console.error);
  }, []);

  const filtered = skills.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[720px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[14px] font-medium" style={{ color: '#cccccc' }}>
            Skills
          </h2>
          <button
            onClick={() => navigate("/skills/create")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px]"
            style={{ background: '#007acc', color: '#ffffff' }}
          >
            <Plus size={14} />
            New Skill
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#6a6a6a' }} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search skills..."
            className="w-full pl-9 pr-3 py-2 rounded text-[12px] outline-none"
            style={{ background: '#3c3c3c', color: '#cccccc', border: '1px solid #3e3e42' }}
          />
        </div>

        {/* Skill List */}
        <div className="flex flex-col gap-2">
          {filtered.length === 0 ? (
            <div className="text-center py-8 text-[12px]" style={{ color: '#6a6a6a' }}>
              {skills.length === 0
                ? "No skills registered. Create one or use the system to auto-generate."
                : "No matching skills."}
            </div>
          ) : (
            filtered.map((skill) => (
              <div
                key={skill.name}
                className="rounded px-4 py-3 cursor-pointer transition-colors"
                style={{ background: '#252526', border: '1px solid #3e3e42' }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#007acc')}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = '#3e3e42')}
              >
                <div className="flex items-center gap-2">
                  <Package size={14} style={{ color: '#007acc' }} />
                  <span className="text-[13px] font-mono" style={{ color: '#9cdcfe' }}>
                    {skill.name}
                  </span>
                  {skill.version && (
                    <span className="text-[10px]" style={{ color: '#6a6a6a' }}>
                      v{skill.version}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-[12px] pl-6" style={{ color: '#969696' }}>
                  {skill.description}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
