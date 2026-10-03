import React from 'react';
import { ShieldCheck, RefreshCw, Database } from 'lucide-react';

export function Header({ sessionId, filename, onReset }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-white tracking-tight">Agentic SOV Cleansing</h1>
              <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Adrosonic Build
              </span>
            </div>
            <p className="text-xs text-slate-400">Statement of Values Standardisation · 4-Agent Autonomous System with HITL</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {sessionId && (
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span>Session:</span>
              <span className="font-mono font-medium text-cyan-300">{sessionId}</span>
              {filename && (
                <>
                  <span className="text-slate-600">|</span>
                  <span className="text-slate-300 truncate max-w-[160px]">{filename}</span>
                </>
              )}
            </div>
          )}

          {sessionId && onReset && (
            <button
              onClick={onReset}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-300 hover:text-white transition-all shadow-sm"
              title="Reset and upload new file"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>New File</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
