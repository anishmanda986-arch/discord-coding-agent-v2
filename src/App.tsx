/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { ChatConsole } from "./components/ChatConsole";
import { CommandCenter } from "./components/CommandCenter";
import { SkillsBrowser } from "./components/SkillsBrowser";
import { SecurityInspector } from "./components/SecurityInspector";
import { TestRunner } from "./components/TestRunner";
import { GatewayHealth } from "./types";

export default function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [health, setHealth] = useState<GatewayHealth | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(false);

  const fetchHealth = async () => {
    setIsLoadingHealth(true);
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      setHealth(data);
    } catch (e) {
      console.error("Health check error:", e);
    } finally {
      setIsLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Header & Navigation */}
      <Header
        health={health}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onRefreshHealth={fetchHealth}
        isLoadingHealth={isLoadingHealth}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "chat" && <ChatConsole />}
        {activeTab === "commands" && <CommandCenter />}
        {activeTab === "skills" && <SkillsBrowser />}
        {activeTab === "security" && <SecurityInspector />}
        {activeTab === "tests" && <TestRunner />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 text-slate-500 text-xs py-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>CODING AGENT • Multi-Agent Gateway Active</span>
          </div>
          <div className="flex items-center space-x-4">
            <span>Context Optimization: Enabled</span>
            <span>Secret Masking: Enabled</span>
            <span>Sandbox Isolation: Active</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
