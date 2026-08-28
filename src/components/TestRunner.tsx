import React, { useState } from "react";
import { CheckCircle2, XCircle, Play, RefreshCw, Layers } from "lucide-react";

export const TestRunner: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [testOutput, setTestOutput] = useState<string>("");
  const [passed, setPassed] = useState<boolean | null>(null);

  const handleRunTests = async () => {
    setIsRunning(true);
    setTestOutput("");
    setPassed(null);

    try {
      const res = await fetch("/api/tests/run");
      const data = await res.json();
      setTestOutput(data.output || "Tests completed.");
      setPassed(data.tests_passed);
    } catch (e: any) {
      setTestOutput(`Error executing tests: ${e.message}`);
      setPassed(false);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-blue-400" />
              <span>Full System Verification Test Suite (31 Tests)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Verifies all 12 subsystems: URL Normalization, Model Discovery, Security Validator, Rate Limiter, Budget Manager, SmartRepoIndex, Coding Lifecycle, Agent Router, Diff Patcher, Skills System, Cleanup Worker, and Discord Commands.
            </p>
          </div>
          <button
            onClick={handleRunTests}
            disabled={isRunning}
            className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center space-x-2 transition cursor-pointer shrink-0"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running 31 Tests...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Execute All 31 Tests</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Test Output Console */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Test Runner Stdout / Stderr
          </span>
          {passed !== null && (
            <span
              className={`text-xs font-semibold px-2.5 py-0.5 rounded flex items-center space-x-1 ${
                passed
                  ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                  : "bg-rose-950 text-rose-400 border border-rose-800"
              }`}
            >
              {passed ? <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" /> : <XCircle className="w-3.5 h-3.5 inline mr-1" />}
              <span>{passed ? "ALL 31 TESTS PASSED (100% OK)" : "TEST FAILURES DETECTED"}</span>
            </span>
          )}
        </div>

        {testOutput ? (
          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 font-mono text-xs text-slate-300 max-h-[450px] overflow-y-auto leading-relaxed whitespace-pre-wrap">
            {testOutput}
          </div>
        ) : (
          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-12 text-center text-slate-500 text-xs">
            <Layers className="w-8 h-8 mx-auto text-slate-700 mb-2" />
            <p>Click "Execute All 31 Tests" to run the complete automated test suite.</p>
          </div>
        )}
      </div>
    </div>
  );
};
