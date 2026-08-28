import React from "react";
import { ShieldCheck, Cpu, Database, Activity, RefreshCw, Zap } from "lucide-react";
import { GatewayHealth } from "../types";

interface HeaderProps {
  health: GatewayHealth | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onRefreshHealth: () => void;
  isLoadingHealth: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  activeTab,
  setActiveTab,
  onRefreshHealth,
  isLoadingHealth,
}) => {
  const tabs = [
    { id: "chat", label: "Discord Agent Console" },
    { id: "commands", label: "Command Center (/api, /test)" },
    { id: "skills", label: "Skill Blueprints (30)" },
    { id: "security", label: "Security & Sandbox" },
    { id: "tests", label: "Test Suite (31 Tests)" },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-slate-100 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-white">CODING AGENT</h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
                  v1.0.0
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-950 text-blue-400 border border-blue-800">
                  Multi-Agent Gateway
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Autonomous Discord assistant with smart context indexing, 5x cost reduction, and sandbox isolation
              </p>
            </div>
          </div>

          {/* Quick Telemetry Badges */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            <div className="flex items-center space-x-1.5 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-slate-400">Cost Savings:</span>
              <span className="font-semibold text-amber-300">
                {health?.metrics.estimated_cost_reduction_ratio || "5.01x"}
              </span>
            </div>

            <div className="flex items-center space-x-1.5 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-400">Security:</span>
              <span className="font-semibold text-emerald-300">Redaction + Jail Active</span>
            </div>

            <button
              id="refresh-health-btn"
              onClick={onRefreshHealth}
              disabled={isLoadingHealth}
              className="flex items-center space-x-1 bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1.5 rounded-lg border border-slate-700 transition cursor-pointer"
              title="Refresh System Health"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingHealth ? "animate-spin text-blue-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 sm:space-x-2 mt-4 pt-3 border-t border-slate-800/80 overflow-x-auto scrollbar-none">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-2 text-xs sm:text-sm font-medium rounded-lg whitespace-nowrap transition cursor-pointer ${
                activeTab === tab.id
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
};
