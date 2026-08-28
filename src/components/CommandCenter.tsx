import React, { useState, useEffect } from "react";
import { Terminal, Key, Shield, Radio, Power, Check, AlertCircle, RefreshCw, Layers, Search, Cpu, CheckCircle2, XCircle, Clock } from "lucide-react";

export const CommandCenter: React.FC = () => {
  const [activeCommand, setActiveCommand] = useState<"/api" | "/models" | "/test" | "/connect" | "/disable">("/api");

  // /api state
  const [provider, setProvider] = useState("OpenRouter");
  const [baseUrl, setBaseUrl] = useState("https://openrouter.ai/api/v1");
  const [apiKey, setApiKey] = useState("");
  const [modelOverride, setModelOverride] = useState("anthropic/claude-3.5-sonnet");
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredModels, setDiscoveredModels] = useState<any[]>([]);

  // /models state
  const [modelSearchQuery, setModelSearchQuery] = useState("");
  const [modelsFilterList, setModelsFilterList] = useState<any[]>([]);

  // Command Execution State
  const [isExecuting, setIsExecuting] = useState(false);
  const [commandOutput, setCommandOutput] = useState<any>(null);

  // /test state
  const [testMode, setTestMode] = useState<"system_diagnostic" | "workspace_test">("system_diagnostic");
  const [workspacePath, setWorkspacePath] = useState(".");

  // /connect state
  const [agentId, setAgentId] = useState("coding_agent_primary");
  const [endpoint, setEndpoint] = useState("http://127.0.0.1:3000");

  // /disable state
  const [channelId, setChannelId] = useState("general-dev");

  // Auto-discover models on mount if empty
  useEffect(() => {
    if (discoveredModels.length === 0) {
      handleDiscoverModels();
    }
  }, []);

  const handleDiscoverModels = async () => {
    setIsDiscovering(true);
    try {
      const res = await fetch("/api/models/discover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: baseUrl, api_key: apiKey }),
      });
      const data = await res.json();
      if (data.models && data.models.length > 0) {
        setDiscoveredModels(data.models);
        setModelsFilterList(data.models);
        if (!modelOverride) {
          setModelOverride(data.models[0].id);
        }
      }
    } catch (e: any) {
      console.error("Model discovery error:", e);
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleRunCommand = async () => {
    setIsExecuting(true);
    setCommandOutput(null);

    let args: any = {};
    if (activeCommand === "/api") {
      args = {
        provider,
        base_url: baseUrl,
        api_key: apiKey,
        model_override: modelOverride,
        scope_id: `channel:${channelId}`,
      };
    } else if (activeCommand === "/models") {
      args = {
        query: modelSearchQuery,
        scope_id: `channel:${channelId}`,
      };
    } else if (activeCommand === "/test") {
      args = {
        workspace_path: testMode === "workspace_test" ? workspacePath : null,
        run_full_diagnostics: testMode === "system_diagnostic",
      };
    } else if (activeCommand === "/connect") {
      args = { agent_id: agentId, endpoint };
    } else if (activeCommand === "/disable") {
      args = { channel_id: channelId };
    }

    try {
      const res = await fetch("/api/bot/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: activeCommand, args }),
      });
      const data = await res.json();
      setCommandOutput(data);
    } catch (e: any) {
      setCommandOutput({ success: false, error: e.message });
    } finally {
      setIsExecuting(false);
    }
  };

  const filteredModels = discoveredModels.filter((m) => {
    if (!modelSearchQuery) return true;
    const q = modelSearchQuery.toLowerCase();
    return (m.id && m.id.toLowerCase().includes(q)) || (m.name && m.name.toLowerCase().includes(q));
  });

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-blue-400" />
              <span>Discord Slash Command Center</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Strictly the 4 core Discord commands plus model discovery: configure endpoints, inspect models, run 21-point system diagnostics, and isolate channels.
            </p>
          </div>
          {/* Command Switcher Buttons */}
          <div className="flex items-center space-x-1.5 bg-slate-800 p-1 rounded-lg border border-slate-700">
            {(["/api", "/models", "/test", "/connect", "/disable"] as const).map((cmd) => (
              <button
                key={cmd}
                onClick={() => {
                  setActiveCommand(cmd);
                  setCommandOutput(null);
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition cursor-pointer ${
                  activeCommand === cmd
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {cmd}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Command Playground Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input Parameters */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              {activeCommand} Configuration Parameters
            </span>
            <span className="text-[11px] text-blue-400 font-mono">
              {activeCommand === "/api" && "Endpoint Discovery & Encryption"}
              {activeCommand === "/models" && "Model Discovery & Filtering"}
              {activeCommand === "/test" && "21-Point System & API Diagnostics"}
              {activeCommand === "/connect" && "HMAC Gateway Registration"}
              {activeCommand === "/disable" && "Channel Isolation Toggle"}
            </span>
          </div>

          {/* /api FORM */}
          {activeCommand === "/api" && (
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Provider Name</label>
                <input
                  type="text"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                  placeholder="OpenRouter, OpenAI, Groq, Ollama"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Base URL (OpenAI-Compatible)</label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
                  placeholder="https://openrouter.ai/api/v1"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">
                  Auto-normalizes trailing slashes and avoids duplicate /v1 endpoints.
                </span>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">API Key (AES-Encrypted at Rest)</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
                  placeholder="sk-..."
                />
                <span className="text-[10px] text-emerald-400 mt-0.5 flex items-center space-x-1">
                  <Shield className="w-3 h-3 inline" />
                  <span>Key is encrypted with master secret and never leaked in logs.</span>
                </span>
              </div>

              <div className="pt-2">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-medium">Selected Model</label>
                  <button
                    onClick={handleDiscoverModels}
                    disabled={isDiscovering}
                    className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center space-x-1 cursor-pointer"
                  >
                    <RefreshCw className={`w-3 h-3 ${isDiscovering ? "animate-spin" : ""}`} />
                    <span>Query GET /models</span>
                  </button>
                </div>
                <input
                  type="text"
                  value={modelOverride}
                  onChange={(e) => setModelOverride(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
                  placeholder="anthropic/claude-3.5-sonnet"
                />
              </div>

              {discoveredModels.length > 0 && (
                <div className="bg-slate-800/70 p-2.5 rounded-lg border border-slate-700 space-y-1.5">
                  <span className="text-[11px] text-slate-400 font-semibold block">Discovered Models ({discoveredModels.length}):</span>
                  <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
                    {discoveredModels.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => setModelOverride(m.id)}
                        className={`text-[10px] px-2 py-0.5 rounded font-mono border transition ${
                          modelOverride === m.id
                            ? "bg-blue-600 text-white border-blue-500"
                            : "bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-500"
                        }`}
                      >
                        {m.id}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* /models FORM */}
          {activeCommand === "/models" && (
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <label className="text-slate-400 font-medium">Search & Inspect Available Models</label>
                <button
                  onClick={handleDiscoverModels}
                  disabled={isDiscovering}
                  className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center space-x-1 cursor-pointer"
                >
                  <RefreshCw className={`w-3 h-3 ${isDiscovering ? "animate-spin" : ""}`} />
                  <span>Refresh /models</span>
                </button>
              </div>

              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
                <input
                  type="text"
                  value={modelSearchQuery}
                  onChange={(e) => setModelSearchQuery(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-8 pr-3 py-2 text-slate-200 font-mono"
                  placeholder="Filter models (e.g. claude, gpt-4o, flash, coder)..."
                />
              </div>

              <div className="bg-slate-950 rounded-lg border border-slate-800 max-h-64 overflow-y-auto divide-y divide-slate-800">
                {filteredModels.map((m) => (
                  <div
                    key={m.id}
                    className="p-2.5 flex items-center justify-between hover:bg-slate-900/60 transition"
                  >
                    <div>
                      <div className="font-mono text-[11px] text-slate-200 font-semibold">{m.id}</div>
                      <div className="text-[10px] text-slate-400 flex items-center space-x-2 mt-0.5">
                        <span>Context: {m.context_length ? `${Math.round(m.context_length / 1000)}k` : "128k"}</span>
                        <span>•</span>
                        <span className="text-slate-500">{m.owned_by || "OpenAI-compatible"}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => setModelOverride(m.id)}
                      className={`text-[10px] px-2.5 py-1 rounded font-medium transition cursor-pointer ${
                        modelOverride === m.id
                          ? "bg-emerald-600 text-white"
                          : "bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                      }`}
                    >
                      {modelOverride === m.id ? "Active" : "Select"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* /test FORM */}
          {activeCommand === "/test" && (
            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1.5">Diagnostic Scope</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setTestMode("system_diagnostic")}
                    className={`px-3 py-2 rounded-lg border text-left cursor-pointer transition ${
                      testMode === "system_diagnostic"
                        ? "bg-blue-950/60 border-blue-600 text-blue-200"
                        : "bg-slate-800 border-slate-700 text-slate-400"
                    }`}
                  >
                    <div className="font-semibold text-slate-200">21-Point System Diagnostic</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">API, models, sandbox, rollback, budget</div>
                  </button>
                  <button
                    onClick={() => setTestMode("workspace_test")}
                    className={`px-3 py-2 rounded-lg border text-left cursor-pointer transition ${
                      testMode === "workspace_test"
                        ? "bg-blue-950/60 border-blue-600 text-blue-200"
                        : "bg-slate-800 border-slate-700 text-slate-400"
                    }`}
                  >
                    <div className="font-semibold text-slate-200">Workspace Project Tests</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Runs npm test, pytest, cargo test</div>
                  </button>
                </div>
              </div>

              {testMode === "workspace_test" && (
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Target Workspace Directory</label>
                  <input
                    type="text"
                    value={workspacePath}
                    onChange={(e) => setWorkspacePath(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
                    placeholder="."
                  />
                </div>
              )}
            </div>
          )}

          {/* /connect FORM */}
          {activeCommand === "/connect" && (
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Agent Identifier</label>
                <input
                  type="text"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-medium mb-1">Gateway Endpoint</label>
                <input
                  type="text"
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
                />
              </div>
            </div>
          )}

          {/* /disable FORM */}
          {activeCommand === "/disable" && (
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Discord Channel ID / Name</label>
                <input
                  type="text"
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Toggles the bot in this channel only. All other server channels continue operating without disruption.
                </span>
              </div>
            </div>
          )}

          {/* Execute Command Button */}
          <button
            onClick={handleRunCommand}
            disabled={isExecuting}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-4 py-2.5 rounded-lg flex items-center justify-center space-x-2 transition cursor-pointer mt-4"
          >
            {isExecuting ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Terminal className="w-4 h-4" />
                <span>Execute {activeCommand}</span>
              </>
            )}
          </button>
        </div>

        {/* Right: Response Output */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Discord Interaction Response
            </span>
            {commandOutput && (
              <span
                className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                  commandOutput.success || commandOutput.overall_status === "PASS"
                    ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    : "bg-rose-950 text-rose-400 border border-rose-800"
                }`}
              >
                {commandOutput.overall_status || (commandOutput.success ? "SUCCESS" : "FAILURE")}
              </span>
            )}
          </div>

          {commandOutput ? (
            <div className="space-y-3">
              {/* Latency Banner for /test */}
              {commandOutput.latency_breakdown && (
                <div className="bg-slate-800/80 border border-slate-700 p-2.5 rounded-lg flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1.5 text-blue-400 font-mono">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Models: {commandOutput.latency_breakdown.models_endpoint_ms}ms</span>
                  </div>
                  <div className="text-slate-400 font-mono">
                    Completion: {commandOutput.latency_breakdown.completion_endpoint_ms}ms
                  </div>
                  <div className="text-emerald-400 font-semibold font-mono">
                    Total: {commandOutput.latency_breakdown.total_seconds}s
                  </div>
                </div>
              )}

              {/* ASCII Diagnostic Box if present */}
              {commandOutput.ascii_report ? (
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-[11px] leading-relaxed text-emerald-400 overflow-x-auto">
                  <pre>{commandOutput.ascii_report}</pre>
                </div>
              ) : (
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-slate-300 max-h-80 overflow-y-auto">
                  <pre>{JSON.stringify(commandOutput, null, 2)}</pre>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-10 text-center text-slate-500 text-xs">
              <Layers className="w-8 h-8 mx-auto text-slate-700 mb-2" />
              <p>Click "Execute {activeCommand}" to dispatch the command.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
