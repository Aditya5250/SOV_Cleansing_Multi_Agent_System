import React, { useState } from 'react';
import { 
  FileSearch, 
  GitMerge, 
  Activity, 
  UserCheck, 
  FileCheck2, 
  ChevronDown, 
  ChevronUp, 
  Terminal, 
  CheckCircle2, 
  Clock 
} from 'lucide-react';

export function AgentPipeline({ currentStage = 1, agentLogs = [], currentAgent = 'Awaiting Upload' }) {
  const [logsOpen, setLogsOpen] = useState(false);

  const steps = [
    {
      num: 1,
      title: "Agent 1",
      subtitle: "Sheet Intelligence",
      desc: "Tabular structure & header detection",
      icon: FileSearch,
      stage: 1,
    },
    {
      num: 2,
      title: "Agent 2",
      subtitle: "Schema Mapping",
      desc: "Pass 1 Fuzzy + Pass 2 Semantic",
      icon: GitMerge,
      stage: 1,
    },
    {
      num: 3,
      title: "Agent 3",
      subtitle: "Quality & Reasoning",
      desc: "Anomaly detection & explainability",
      icon: Activity,
      stage: 1,
    },
    {
      num: 4,
      title: "Human Review",
      subtitle: "HITL Approval Gateway",
      desc: "Accept / Reject / Re-reason",
      icon: UserCheck,
      stage: 2,
    },
    {
      num: 5,
      title: "Agent 4",
      subtitle: "Controlled Transform",
      desc: "Audit log & 17-col validation",
      icon: FileCheck2,
      stage: 3,
    },
  ];

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Four-Agent Collaborative Workflow
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Active Agent Stage: <span className="text-indigo-400 font-medium">{currentAgent}</span>
          </p>
        </div>

        <button
          onClick={() => setLogsOpen(!logsOpen)}
          className="flex items-center space-x-2 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 px-3 py-1.5 rounded-lg border border-slate-700 transition-all self-start md:self-auto cursor-pointer"
        >
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>Execution Telemetry ({agentLogs.length})</span>
          {logsOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Agent Workflow Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {steps.map((step) => {
          const Icon = step.icon;
          const isComplete = currentStage > step.stage;
          const isActive = currentStage === step.stage;

          return (
            <div
              key={step.num}
              className={`relative p-3.5 rounded-xl border transition-all ${
                isActive
                  ? 'bg-indigo-950/40 border-indigo-500/50 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/30'
                  : isComplete
                  ? 'bg-slate-800/40 border-emerald-500/30 text-slate-300'
                  : 'bg-slate-900/40 border-slate-800/80 text-slate-500'
              }`}
            >
              <div className="flex items-start justify-between">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    isActive
                      ? 'bg-indigo-600 text-white'
                      : isComplete
                      ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-slate-800 text-slate-500'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div className="text-right">
                  {isComplete ? (
                    <span className="inline-flex items-center text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Done
                    </span>
                  ) : isActive ? (
                    <span className="inline-flex items-center text-[10px] font-medium text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded-full border border-indigo-500/30 animate-pulse">
                      <Clock className="w-3 h-3 mr-1" /> Active
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500">Standby</span>
                  )}
                </div>
              </div>

              <div className="mt-3">
                <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">{step.title}</div>
                <div className="text-sm font-semibold text-slate-200">{step.subtitle}</div>
                <div className="text-[11px] text-slate-400 mt-1 leading-snug">{step.desc}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Collapsible Telemetry / Agent Logs Console */}
      {logsOpen && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <div className="bg-slate-950 rounded-xl p-3.5 border border-slate-800 font-mono text-xs max-h-48 overflow-y-auto space-y-1.5">
            {agentLogs.length === 0 ? (
              <p className="text-slate-500 italic">No agent logs recorded yet.</p>
            ) : (
              agentLogs.map((log, idx) => (
                <div key={idx} className="flex items-start space-x-2 text-[11px]">
                  <span className="text-slate-500 shrink-0">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span
                    className={`font-semibold shrink-0 ${
                      log.status === 'success'
                        ? 'text-emerald-400'
                        : log.status === 'warning'
                        ? 'text-amber-400'
                        : log.status === 'error'
                        ? 'text-rose-400'
                        : 'text-indigo-400'
                    }`}
                  >
                    [{log.agent}]
                  </span>
                  <span className="text-slate-300">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
