import React, { useState, useEffect } from 'react';
import { ShieldCheck, RefreshCw, Database, Server, Check, X, AlertTriangle } from 'lucide-react';
import { getApiBase, setCustomBackendUrl, checkBackendHealth } from '../services/api';

export function Header({ sessionId, filename, onReset, isConfigOpen, setIsConfigOpen }) {
  const [internalConfigOpen, setInternalConfigOpen] = useState(false);
  const showModal = isConfigOpen !== undefined ? isConfigOpen : internalConfigOpen;
  const setShowModal = setIsConfigOpen || setInternalConfigOpen;

  const [inputUrl, setInputUrl] = useState(() => getApiBase());
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [testResult, setTestResult] = useState(null);
  const [isTesting, setIsTesting] = useState(false);

  const refreshHealth = async (target) => {
    const res = await checkBackendHealth(target);
    setBackendStatus(res.online ? 'online' : 'offline');
    return res;
  };

  useEffect(() => {
    let isMounted = true;
    let timer = null;

    const pollBackend = async () => {
      const res = await checkBackendHealth(getApiBase());
      if (!isMounted) return;
      if (res.online) {
        setBackendStatus('online');
      } else {
        setBackendStatus('offline');
        // Auto-retry in 5 seconds to gracefully handle Render free-tier instance wakeups
        timer = setTimeout(pollBackend, 5000);
      }
    };

    pollBackend();

    return () => {
      isMounted = false;
      if (timer) clearTimeout(timer);
    };
  }, []);

  const handleOpenModal = () => {
    setInputUrl(getApiBase());
    setTestResult(null);
    setShowModal(true);
  };

  const handleSaveAndTest = async () => {
    setIsTesting(true);
    setTestResult(null);

    const testRes = await checkBackendHealth(inputUrl);
    setIsTesting(false);
    setTestResult(testRes);

    if (testRes.online) {
      setCustomBackendUrl(inputUrl);
      setBackendStatus('online');
      setTimeout(() => setShowModal(false), 900);
    }
  };

  const handleResetToDefault = () => {
    setCustomBackendUrl('');
    const base = getApiBase();
    setInputUrl(base);
    refreshHealth(base);
    setShowModal(false);
  };

  return (
    <>
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-white tracking-tight">Agentic SOV Cleansing</h1>
              </div>
              <p className="text-xs text-slate-400">Statement of Values Standardisation · 4-Agent Autonomous System with HITL</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Backend Connectivity Status Button */}
            <button
              onClick={handleOpenModal}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer ${
                backendStatus === 'online'
                  ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/50'
                  : backendStatus === 'checking'
                  ? 'bg-slate-800/80 border-slate-700 text-slate-400'
                  : 'bg-rose-950/40 border-rose-500/40 text-rose-300 hover:bg-rose-900/50 animate-pulse'
              }`}
              title="Click to check or configure Backend API URL"
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus === 'online'
                    ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                    : backendStatus === 'checking'
                    ? 'bg-slate-400'
                    : 'bg-rose-400'
                }`}
              />
              <span className="hidden sm:inline">
                {backendStatus === 'online'
                  ? 'Backend Connected'
                  : backendStatus === 'checking'
                  ? 'Checking Server...'
                  : 'Backend Disconnected (Set URL)'}
              </span>
            </button>

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
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-300 hover:text-white transition-all shadow-sm cursor-pointer"
                title="Reset and upload new file"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>New File</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Backend URL Configuration Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2.5">
                <Server className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-semibold text-white">Backend API Connection</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300">
              <p>
                Configure the public URL of your deployed FastAPI backend service (e.g. from Render).
              </p>

              <div className="space-y-1.5">
                <label className="font-medium text-slate-200 block">
                  Backend API URL (Render Web Service):
                </label>
                <input
                  type="text"
                  value={inputUrl}
                  onChange={(e) => setInputUrl(e.target.value)}
                  placeholder="https://sov-cleansing-backend-xxxx.onrender.com"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
                <span className="text-[11px] text-slate-400">
                  Must be your <strong>public</strong> Render Web Service URL (ending in <code>.onrender.com</code>). Do not use private internal hostnames.
                </span>
              </div>

              {testResult && (
                <div
                  className={`p-3 rounded-xl border text-xs flex items-start space-x-2 ${
                    testResult.online
                      ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                      : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
                  }`}
                >
                  {testResult.online ? (
                    <>
                      <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <strong>Connection Successful!</strong> Connected to {testResult.data?.service || 'SOV Backend'}.
                      </div>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      <div>
                        <strong>Connection Failed:</strong> Could not connect to {inputUrl || 'endpoint'}.<br />
                        <span className="text-slate-400 text-[11px]">
                          Note: Render free services sleep after inactivity and take ~30-50 seconds to wake up on the first request.
                        </span>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={handleResetToDefault}
                className="text-xs text-slate-400 hover:text-white underline cursor-pointer"
              >
                Reset to Default
              </button>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveAndTest}
                  disabled={isTesting}
                  className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                >
                  {isTesting ? <span>Testing...</span> : <span>Save & Connect</span>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
