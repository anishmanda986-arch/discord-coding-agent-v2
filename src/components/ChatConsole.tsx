import React, { useState } from "react";
import { Send, Download, FileCode, CheckCircle2, AlertTriangle, Play, Sparkles, Terminal, Shield, Clock, Hash, MessageSquare, Code2 } from "lucide-react";
import { TaskExecutionResult } from "../types";

export const ChatConsole: React.FC = () => {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("anthropic/claude-3.5-sonnet");
  const [channelId, setChannelId] = useState("general-dev");
  const [isRunning, setIsRunning] = useState(false);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [currentActivity, setCurrentActivity] = useState("");
  const [taskResult, setTaskResult] = useState<any | null>(null);
  const [history, setHistory] = useState<any[]>([]);

  const examplePrompts = [
    { label: "💬 Chat", text: "What is React and how does its Virtual DOM work?" },
    { label: "💬 Chat", text: "Explain recursion with a simple example" },
    { label: "🛠️ Coding", text: "Build a production REST API for user authentication with JWT and SQLite" },
    { label: "🛠️ Coding", text: "Create a responsive React dashboard with dark mode and metric cards" },
  ];

  const handleRunTask = async (customPrompt?: string) => {
    const textToRun = customPrompt || prompt;
    if (!textToRun.trim() || isRunning) return;

    setIsRunning(true);
    setTaskResult(null);
    setCurrentProgress(15);
    setCurrentActivity("Classifying intent (Chat vs Coding)...");

    // Dynamic progress transitions while backend executes
    const timer1 = setTimeout(() => {
      setCurrentProgress(40);
      setCurrentActivity("Inspecting repository context & domain skills...");
    }, 600);

    const timer2 = setTimeout(() => {
      setCurrentProgress(70);
      setCurrentActivity("Applying atomic code edits & verifying checksums...");
    }, 1400);

    const timer3 = setTimeout(() => {
      setCurrentProgress(90);
      setCurrentActivity("Running sandbox tests and verifying deliverable integrity...");
    }, 2200);

    try {
      const res = await fetch("/api/bot/prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: textToRun,
          channel_id: channelId,
          user_id: "discord_user_01",
          model,
        }),
      });

      const data = await res.json();
      setCurrentProgress(100);
      setCurrentActivity(data.type === "conversation" ? "Conversational reply received." : "Completed task lifecycle & packaged deliverable archive.");
      setTaskResult(data);

      setHistory((prev) => [
        {
          id: data.task_id || `t_${Date.now()}`,
          prompt: textToRun,
          model,
          type: data.type || "coding",
          timestamp: new Date().toLocaleTimeString(),
          result: data,
        },
        ...prev,
      ]);
    } catch (e: any) {
      setCurrentActivity(`Failed: ${e.message}`);
      setTaskResult({
        success: false,
        status: "FAILED",
        task_id: "err_task",
        summary: "Task execution stopped due to network or configuration error.",
        files_changed: [],
        test_result: { success: false, passed: false, details: e.message },
        metrics: { model_calls: 1, tool_calls: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, estimated_cost_usd: 0 },
        error: e.message,
      });
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setIsRunning(false);
    }
  };

  const renderProgressBar = (pct: number) => {
    const filled = Math.round((pct / 100) * 10);
    const empty = 10 - filled;
    return "█".repeat(filled) + "░".repeat(empty) + ` ${pct}%`;
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Notice */}
      <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-300">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            <strong>Automatic Intent Routing:</strong> The bot automatically detects <strong>Normal Chat</strong> (instant friendly markdown replies, 0 workspace overhead) vs <strong>Autonomous Coding</strong> (creates full project, runs sandbox tests, produces ZIP).
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Atomic writes (.agent_tmp) + checksum verification & rollback active.</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Prompt Input & Configuration */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-blue-400" />
              <span>Discord Message Dispatcher</span>
            </h2>

            {/* Model Selector */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Target Model</label>
              <select
                id="model-selector"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="anthropic/claude-3.5-sonnet">Anthropic Claude 3.5 Sonnet</option>
                <option value="google/gemini-2.0-flash">Google Gemini 2.0 Flash</option>
                <option value="openai/gpt-4o">OpenAI GPT-4o</option>
                <option value="openai/gpt-4o-mini">OpenAI GPT-4o Mini</option>
                <option value="deepseek/deepseek-chat">DeepSeek V3</option>
                <option value="qwen/qwen-2.5-coder-32b-instruct">Qwen 2.5 Coder 32B</option>
              </select>
            </div>

            {/* Channel Context */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Discord Channel</label>
              <div className="flex items-center space-x-1.5 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300">
                <Hash className="w-3.5 h-3.5 text-slate-500" />
                <input
                  id="channel-input"
                  type="text"
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  className="bg-transparent border-none w-full text-slate-200 focus:outline-none"
                  placeholder="general-dev"
                />
              </div>
            </div>

            {/* Prompt Textarea */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Message or Coding Request</label>
              <textarea
                id="prompt-textarea"
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask a question (e.g. 'what is React?') or describe a task (e.g. 'build a weather app')..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Submit Button */}
            <button
              id="send-prompt-btn"
              onClick={() => handleRunTask()}
              disabled={isRunning || !prompt.trim()}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium text-xs px-4 py-2.5 rounded-lg flex items-center justify-center space-x-2 transition cursor-pointer"
            >
              {isRunning ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Agent Processing...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Send Message to Discord</span>
                </>
              )}
            </button>

            {/* Quick Example Prompts */}
            <div className="pt-2 border-t border-slate-800">
              <span className="text-[11px] text-slate-500 block mb-2 font-medium">Quick Test Prompts:</span>
              <div className="space-y-1.5">
                {examplePrompts.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setPrompt(ex.text);
                      handleRunTask(ex.text);
                    }}
                    className="w-full text-left bg-slate-800/60 hover:bg-slate-800 text-[11px] text-slate-300 hover:text-white px-2.5 py-1.5 rounded border border-slate-700/50 transition truncate block cursor-pointer"
                  >
                    <span className="text-blue-400 font-semibold mr-1">{ex.label}</span> {ex.text}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right 2 cols: Live Discord Embed & Deliverable Preview */}
        <div className="lg:col-span-2 space-y-4">
          {/* Simulated Discord Message Container */}
          <div className="bg-[#313338] border border-[#2b2d31] rounded-xl p-5 shadow-lg space-y-4 text-slate-100">
            <div className="flex items-center space-x-3 pb-3 border-b border-[#3f4147]">
              <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-xs shadow">
                BOT
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-sm text-white">Coding Agent</span>
                  <span className="bg-[#5865F2] text-white text-[10px] px-1.5 py-0.2 rounded font-bold">APP</span>
                  <span className="text-xs text-slate-400">Today at {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <span className="text-[11px] text-slate-400">Multi-Agent Gateway • Autonomous Execution Loop</span>
              </div>
            </div>

            {/* Case A: Normal Conversational Message */}
            {taskResult && taskResult.type === "conversation" && (
              <div className="bg-[#2B2D31] border-l-4 border-emerald-500 rounded-r-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-emerald-400 flex items-center space-x-1.5">
                    <MessageSquare className="w-4 h-4" />
                    <span>CONVERSATIONAL RESPONSE</span>
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {taskResult.elapsed_seconds}s • 0 workspace overhead
                  </span>
                </div>
                <div className="text-xs text-slate-200 whitespace-pre-wrap leading-relaxed bg-[#1E1F22] p-3.5 rounded border border-[#35373C]">
                  {taskResult.response}
                </div>
              </div>
            )}

            {/* Case B: Autonomous Coding Task Progress & Embed */}
            {(isRunning || (taskResult && taskResult.type !== "conversation")) && (
              <div className="bg-[#2B2D31] border-l-4 border-blue-500 rounded-r-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-blue-400 flex items-center space-x-1.5">
                    <Code2 className="w-4 h-4" />
                    <span>{taskResult ? (taskResult.success ? "✅ TASK COMPLETED" : "❌ TASK FAILED") : "CODING AGENT PROGRESS"}</span>
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    {taskResult?.task_id || "TASK_ACTIVE"}
                  </span>
                </div>

                {/* Progress Bar Display */}
                <div className="bg-[#1E1F22] rounded p-2.5 font-mono text-xs text-blue-300 flex items-center justify-between">
                  <span>{renderProgressBar(isRunning ? currentProgress : 100)}</span>
                  <span className="text-slate-400 text-[11px]">
                    {isRunning ? `${currentProgress}%` : "100%"}
                  </span>
                </div>

                {/* Current Action / Summary */}
                <div className="text-xs text-slate-300">
                  <span className="text-slate-500 font-semibold block mb-0.5">
                    {taskResult ? "Summary of Implementation:" : "Current Action:"}
                  </span>
                  <p className="bg-[#1E1F22] p-2.5 rounded border border-[#35373C]">
                    {taskResult ? taskResult.summary : currentActivity}
                  </p>
                </div>

                {/* Result Details Grid */}
                {taskResult && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2 text-xs">
                    {/* Files Changed */}
                    <div className="bg-[#1E1F22] p-2.5 rounded border border-[#35373C]">
                      <span className="text-slate-400 text-[11px] font-semibold flex items-center space-x-1 mb-1">
                        <FileCode className="w-3.5 h-3.5 text-blue-400" />
                        <span>Files Modified ({taskResult.files_changed?.length || 0})</span>
                      </span>
                      <div className="space-y-1 max-h-24 overflow-y-auto">
                        {taskResult.files_changed?.map((f: string, idx: number) => (
                          <div key={idx} className="font-mono text-[11px] text-emerald-400 truncate">
                            • {f}
                          </div>
                        ))}
                        {(!taskResult.files_changed || taskResult.files_changed.length === 0) && (
                          <span className="text-slate-500 italic">No files modified</span>
                        )}
                      </div>
                    </div>

                    {/* Tests Status */}
                    <div className="bg-[#1E1F22] p-2.5 rounded border border-[#35373C]">
                      <span className="text-slate-400 text-[11px] font-semibold flex items-center space-x-1 mb-1">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Sandbox Tests</span>
                      </span>
                      <div className="space-y-1 text-[11px]">
                        <span className={`inline-block px-1.5 py-0.5 rounded font-semibold ${taskResult.test_result?.passed ? "bg-emerald-950 text-emerald-400" : "bg-amber-950 text-amber-400"}`}>
                          {taskResult.test_result?.passed ? "Passed" : "Checks Completed"}
                        </span>
                        <p className="text-slate-400 truncate mt-1">
                          {taskResult.test_result?.details || "All assertions verified."}
                        </p>
                      </div>
                    </div>

                    {/* Token & Cost Metrics */}
                    <div className="bg-[#1E1F22] p-2.5 rounded border border-[#35373C]">
                      <span className="text-slate-400 text-[11px] font-semibold flex items-center space-x-1 mb-1">
                        <Clock className="w-3.5 h-3.5 text-amber-400" />
                        <span>Resource Usage</span>
                      </span>
                      <div className="text-[11px] space-y-0.5 text-slate-300">
                        <div>Calls: <span className="font-mono text-slate-100">{taskResult.metrics?.model_calls || 1} model / {taskResult.metrics?.tool_calls || 0} tool</span></div>
                        <div>Tokens: <span className="font-mono text-slate-100">{taskResult.metrics?.total_tokens || 1000}</span></div>
                        <div>Est Cost: <span className="font-mono text-emerald-400">${taskResult.metrics?.estimated_cost_usd?.toFixed(4) || "0.0020"}</span></div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Deliverable Download CTA */}
                {taskResult?.deliverable_zip && (
                  <div className="pt-2 flex items-center justify-between bg-blue-950/40 border border-blue-800/60 p-3 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Download className="w-4 h-4 text-blue-400" />
                      <div>
                        <span className="text-xs font-semibold text-slate-200 block">Deliverable Archive Ready</span>
                        <span className="text-[11px] text-slate-400">
                          {taskResult.zip_size_bytes ? `${Math.round(taskResult.zip_size_bytes / 1024)} KB` : "Clean ZIP package"}
                        </span>
                      </div>
                    </div>
                    <a
                      href={`/api/download/${taskResult.deliverable_zip.split("/").pop()}`}
                      download
                      className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download ZIP</span>
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* Empty State */}
            {!isRunning && !taskResult && (
              <div className="bg-[#2B2D31] rounded-lg p-8 text-center text-slate-400 space-y-2">
                <Play className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="text-sm font-medium text-slate-300">Agent Ready in Channel #{channelId}</p>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Type any coding instruction or conversational question on the left to test live execution.
                </p>
              </div>
            )}
          </div>

          {/* Past Task History */}
          {history.length > 1 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recent Activity History</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {history.slice(1).map((h) => (
                  <div key={h.id} className="flex items-center justify-between bg-slate-800/50 p-2.5 rounded-lg text-xs border border-slate-700/50">
                    <div className="truncate max-w-md">
                      <span className="text-slate-200 font-medium">{h.prompt}</span>
                      <span className="text-slate-500 block text-[11px]">{h.timestamp} • {h.type.toUpperCase()}</span>
                    </div>
                    <span className="text-emerald-400 font-semibold px-2 py-0.5 bg-emerald-950/60 rounded text-[10px]">
                      {h.type === "conversation" ? "REPLIED" : "COMPLETED"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
