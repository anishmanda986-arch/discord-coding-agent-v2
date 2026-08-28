import React, { useState } from "react";
import { ShieldCheck, AlertOctagon, Lock, EyeOff, Check, X, FileSearch } from "lucide-react";

export const SecurityInspector: React.FC = () => {
  // Test Path Traversal
  const [testPath, setTestPath] = useState("../../etc/passwd");
  const [pathResult, setPathResult] = useState<{ allowed: boolean; reason: string } | null>(null);

  // Test Command Execution
  const [testCommand, setTestCommand] = useState("rm -rf / --no-preserve-root");
  const [commandResult, setCommandResult] = useState<{ allowed: boolean; reason: string } | null>(null);

  // Test Secret Redaction
  const [testSecretText, setTestSecretText] = useState(
    "API failure with a redacted credential"
  );
  const [redactedOutput, setRedactedOutput] = useState("");

  const handleValidatePath = () => {
    // Client simulation of SecurityValidator logic
    const containsTraversal = testPath.includes("..") || testPath.startsWith("/") || testPath.includes("\0");
    if (containsTraversal) {
      setPathResult({
        allowed: false,
        reason: "Blocked by SecurityValidator: Path traversal (..) or root breakout detected.",
      });
    } else {
      setPathResult({
        allowed: true,
        reason: `Allowed: Jailed inside workspace /tmp/coding_agent_workspaces/${testPath}`,
      });
    }
  };

  const handleValidateCommand = () => {
    const dangerousPatterns = [/rm\s+-rf\s+\//, /:\(\)\{ :\|:& \};:/, />\s*\/dev\/sd/, /chmod\s+-R\s+777\s+\//];
    const isDangerous = dangerousPatterns.some((p) => p.test(testCommand));
    if (isDangerous) {
      setCommandResult({
        allowed: false,
        reason: "Blocked by SecurityValidator: Destructive system command detected in blacklist.",
      });
    } else {
      setCommandResult({
        allowed: true,
        reason: "Allowed: Safe non-destructive command.",
      });
    }
  };

  const handleRedactSecrets = () => {
    let text = testSecretText;
    text = text.replace(/sk-[a-zA-Z0-9_-]{20,}/g, "[REDACTED_API_KEY]");
    text = text.replace(/[A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}/g, "[REDACTED_DISCORD_TOKEN]");
    text = text.replace(/ghp_[a-zA-Z0-9]{36}/g, "[REDACTED_GITHUB_TOKEN]");
    setRedactedOutput(text);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-100 flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <span>Security & Sandbox Isolation Defense Engine</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Zero-trust containment: path traversal prevention, command blacklist sanitization, secret masking, and rate limiter protection.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 1. Path Traversal Jail */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
            <Lock className="w-4 h-4 text-blue-400" />
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Path Containment Jail</h3>
          </div>
          <div className="text-xs space-y-3">
            <p className="text-slate-400">Tests path resolution against directory traversal & symlink breakout.</p>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Test Path</label>
              <input
                type="text"
                value={testPath}
                onChange={(e) => setTestPath(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono text-xs"
              />
            </div>
            <button
              onClick={handleValidatePath}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium py-2 rounded-lg border border-slate-700 text-xs transition cursor-pointer"
            >
              Test Path Safety
            </button>
            {pathResult && (
              <div
                className={`p-3 rounded-lg border text-xs flex items-start space-x-2 ${
                  pathResult.allowed
                    ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
                    : "bg-rose-950/40 border-rose-800 text-rose-300"
                }`}
              >
                {pathResult.allowed ? <Check className="w-4 h-4 shrink-0 text-emerald-400" /> : <X className="w-4 h-4 shrink-0 text-rose-400" />}
                <span>{pathResult.reason}</span>
              </div>
            )}
          </div>
        </div>

        {/* 2. Dangerous Command Sanitizer */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Command Sanitizer</h3>
          </div>
          <div className="text-xs space-y-3">
            <p className="text-slate-400">Verifies system execution against destructive shell commands and fork bombs.</p>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Test Command</label>
              <input
                type="text"
                value={testCommand}
                onChange={(e) => setTestCommand(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono text-xs"
              />
            </div>
            <button
              onClick={handleValidateCommand}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium py-2 rounded-lg border border-slate-700 text-xs transition cursor-pointer"
            >
              Check Command Safety
            </button>
            {commandResult && (
              <div
                className={`p-3 rounded-lg border text-xs flex items-start space-x-2 ${
                  commandResult.allowed
                    ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
                    : "bg-rose-950/40 border-rose-800 text-rose-300"
                }`}
              >
                {commandResult.allowed ? <Check className="w-4 h-4 shrink-0 text-emerald-400" /> : <X className="w-4 h-4 shrink-0 text-rose-400" />}
                <span>{commandResult.reason}</span>
              </div>
            )}
          </div>
        </div>

        {/* 3. Automatic Secret Redactor */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
            <EyeOff className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Secret Redaction Filter</h3>
          </div>
          <div className="text-xs space-y-3">
            <p className="text-slate-400">Ensures API keys and bot tokens are masked before logs or Discord embeds are sent.</p>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Sample Log Message</label>
              <textarea
                rows={2}
                value={testSecretText}
                onChange={(e) => setTestSecretText(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono text-[11px]"
              />
            </div>
            <button
              onClick={handleRedactSecrets}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium py-2 rounded-lg border border-slate-700 text-xs transition cursor-pointer"
            >
              Apply Secret Masking
            </button>
            {redactedOutput && (
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-[11px] text-amber-300 break-all">
                {redactedOutput}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
