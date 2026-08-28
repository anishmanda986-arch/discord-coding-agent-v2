import React, { useState, useEffect } from "react";
import { Search, BookOpen, CheckSquare, ShieldCheck, Code, Layers } from "lucide-react";
import { SkillItem } from "../types";

export const SkillsBrowser: React.FC = () => {
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [search, setSearch] = useState("");
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>("software-engineering");
  const [skillContent, setSkillContent] = useState<string>("");
  const [loadingContent, setLoadingContent] = useState(false);

  useEffect(() => {
    fetch("/api/skills")
      .then((r) => r.json())
      .then((d) => {
        if (d.skills) {
          setSkills(d.skills);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedSkillId) {
      setLoadingContent(true);
      fetch(`/api/skills/${selectedSkillId}`)
        .then((r) => r.json())
        .then((d) => {
          setSkillContent(d.content || "");
        })
        .catch(console.error)
        .finally(() => setLoadingContent(false));
    }
  }, [selectedSkillId]);

  const filteredSkills = skills.filter(
    (s) =>
      s.title.toLowerCase().includes(search.toLowerCase()) ||
      s.id.toLowerCase().includes(search.toLowerCase()) ||
      s.summary.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center space-x-2">
              <BookOpen className="w-5 h-5 text-blue-400" />
              <span>Autonomous Domain Skills Catalog ({skills.length} Loaded)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Dynamic domain instructions injected into model context based on task requirements with keyword matching and verification checklists.
            </p>
          </div>
          {/* Search Box */}
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skills (e.g. react, python, security)..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Two Column Layout: Skills List & Skill Detail Blueprint */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Skills List */}
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2 max-h-[600px] overflow-y-auto">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block px-2 mb-2">
            Loaded System Skills ({filteredSkills.length})
          </span>
          {filteredSkills.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedSkillId(s.id)}
              className={`w-full text-left p-3 rounded-lg border transition cursor-pointer ${
                selectedSkillId === s.id
                  ? "bg-blue-950/60 border-blue-600 text-white shadow-sm"
                  : "bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-slate-100">{s.title}</span>
                <span className="text-[10px] font-mono text-blue-400 bg-blue-950 px-1.5 py-0.5 rounded border border-blue-900">
                  {s.id}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 line-clamp-2">{s.summary}</p>
            </button>
          ))}
          {filteredSkills.length === 0 && (
            <div className="p-8 text-center text-slate-500 text-xs">
              No skills match "{search}".
            </div>
          )}
        </div>

        {/* Right 2 cols: Skill Detail Blueprint */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Code className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Skill Specification & Blueprint: <code className="text-blue-400 font-mono font-normal">/app/skills/definitions/{selectedSkillId}/SKILL.md</code>
              </span>
            </div>
            <span className="text-xs font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
              Active in Context Engine
            </span>
          </div>

          {loadingContent ? (
            <div className="p-16 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-2">
              <div className="w-5 h-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
              <span>Loading skill definition...</span>
            </div>
          ) : (
            <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-5 font-mono text-xs text-slate-200 max-h-[500px] overflow-y-auto leading-relaxed whitespace-pre-wrap">
              {skillContent || "Select a skill from the list on the left to inspect its instructions and checklists."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
