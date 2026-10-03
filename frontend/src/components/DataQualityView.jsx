import React, { useState } from 'react';
import { TARGET_FIELDS } from '../types/sov';
import { Activity, AlertTriangle, AlertOctagon } from 'lucide-react';

export function DataQualityView({ dataQuality }) {
  const [activeTab, setActiveTab] = useState('overview');

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'critical':
        return <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1"><AlertOctagon className="w-3 h-3" /> Critical</span>;
      case 'high':
        return <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/30 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> High</span>;
      case 'medium':
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">Medium</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/30">Low</span>;
    }
  };

  const getHealthColor = (score) => {
    if (score >= 85) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10';
    if (score >= 70) return 'text-amber-400 border-amber-500/40 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10';
  };

  if (!dataQuality) return null;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-semibold text-white">Agent 3: Data Quality & Reasoning Agent</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-medium">
                {dataQuality.total_anomalies} Anomalies Detected (Recall ≥ 90%)
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Deterministic profiling & business rule verification across P&C risk criteria
            </p>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center space-x-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeTab === 'overview' ? 'bg-cyan-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('anomalies')}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeTab === 'anomalies' ? 'bg-cyan-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Anomalies ({dataQuality.issues.length})
          </button>
          <button
            onClick={() => setActiveTab('completeness')}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeTab === 'completeness' ? 'bg-cyan-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Completeness
          </button>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        {/* Overall Intake Score */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 col-span-2 md:col-span-1 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Intake Quality Score
          </div>
          <div className="my-2 flex items-baseline space-x-1">
            <span className="text-3xl font-bold font-mono text-white">
              {dataQuality.overall_quality_score}
            </span>
            <span className="text-xs text-slate-500 font-mono">/100</span>
          </div>
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border self-start ${getHealthColor(dataQuality.overall_quality_score)}`}>
            {dataQuality.overall_quality_score >= 80 ? 'Good Integrity' : 'Requires Human Review'}
          </span>
        </div>

        {/* Critical */}
        <div className="p-3.5 rounded-xl border border-rose-900/30 bg-rose-950/10 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-rose-300">Critical</div>
          <div className="text-2xl font-bold font-mono text-rose-400 my-1">{dataQuality.critical_anomalies}</div>
          <div className="text-[10px] text-rose-400/80">Negative sums, etc.</div>
        </div>

        {/* High */}
        <div className="p-3.5 rounded-xl border border-orange-900/30 bg-orange-950/10 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-orange-300">High</div>
          <div className="text-2xl font-bold font-mono text-orange-400 my-1">{dataQuality.high_anomalies}</div>
          <div className="text-[10px] text-orange-400/80">Future dates, sprinkler codes</div>
        </div>

        {/* Medium */}
        <div className="p-3.5 rounded-xl border border-amber-900/30 bg-amber-950/10 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-amber-300">Medium</div>
          <div className="text-2xl font-bold font-mono text-amber-300 my-1">{dataQuality.medium_anomalies}</div>
          <div className="text-[10px] text-amber-400/80">Currency formatting, state codes</div>
        </div>

        {/* Low / Info */}
        <div className="p-3.5 rounded-xl border border-blue-900/30 bg-blue-950/10 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-blue-300">Low / Missing</div>
          <div className="text-2xl font-bold font-mono text-blue-300 my-1">{dataQuality.low_anomalies}</div>
          <div className="text-[10px] text-blue-400/80">Blank fields preserved</div>
        </div>
      </div>

      {/* Tab: Overview & Key Findings */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Priority Anomaly Highlights ({dataQuality.issues.filter(i => i.severity === 'critical' || i.severity === 'high').length})
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {dataQuality.issues.slice(0, 6).map((issue) => (
              <div key={issue.id} className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition-all flex flex-col justify-between space-y-2">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold text-cyan-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      {issue.field}
                    </span>
                    {getSeverityBadge(issue.severity)}
                  </div>
                  <p className="text-xs text-slate-300 mt-2 font-medium">
                    {issue.reasoning}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                  <span>
                    Affected Rows: <span className="font-mono text-slate-200">{issue.affected_rows.length > 0 ? issue.affected_rows.join(', ') : `${issue.affected_count} rows`}</span>
                  </span>
                  {issue.current_value && (
                    <span className="font-mono text-rose-300 bg-rose-950/40 px-1.5 py-0.5 rounded border border-rose-900/40">
                      {issue.current_value}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: All Detected Anomalies */}
      {activeTab === 'anomalies' && (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Target Field</th>
                <th className="px-4 py-3">Issue Type</th>
                <th className="px-4 py-3">Sample Value</th>
                <th className="px-4 py-3">Affected Rows</th>
                <th className="px-4 py-3">Agent Diagnostic & Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {dataQuality.issues.map((issue) => (
                <tr key={issue.id} className="hover:bg-slate-900/50">
                  <td className="px-4 py-3 whitespace-nowrap">{getSeverityBadge(issue.severity)}</td>
                  <td className="px-4 py-3 font-semibold text-white">{issue.field}</td>
                  <td className="px-4 py-3 font-mono text-[11px] text-slate-400">{issue.issue_type}</td>
                  <td className="px-4 py-3 font-mono text-[11px] text-rose-300">{issue.current_value || '-'}</td>
                  <td className="px-4 py-3 font-mono text-[11px] text-slate-400">
                    {issue.affected_rows.length > 0 ? issue.affected_rows.slice(0, 5).join(', ') : issue.affected_count}
                  </td>
                  <td className="px-4 py-3 text-slate-300 text-[11px] max-w-sm">
                    <p className="line-clamp-2">{issue.reasoning}</p>
                    <p className="text-cyan-400 text-[10px] mt-0.5">Action: {issue.recommended_action}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab: Per-field Completeness Rates */}
      {activeTab === 'completeness' && (
        <div className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Per-Field Completeness Rates (% Non-Null across all {dataQuality.total_rows} rows)
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {TARGET_FIELDS.map((field) => {
              const comp = dataQuality.completeness_by_field[field] || { completeness_pct: 0, non_null_count: 0, total_rows: dataQuality.total_rows };
              const pct = comp.completeness_pct;
              const isFull = pct === 100;
              const isMissing = pct === 0;

              return (
                <div key={field} className="p-3 rounded-xl border border-slate-800 bg-slate-950/50 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-medium text-slate-300 truncate" title={field}>{field}</span>
                    <span className={`font-mono text-xs font-semibold ${isFull ? 'text-emerald-400' : isMissing ? 'text-slate-500' : 'text-amber-400'}`}>
                      {pct}%
                    </span>
                  </div>

                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        isFull ? 'bg-emerald-500' : isMissing ? 'bg-slate-700' : 'bg-amber-500'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1.5">
                    <span>{comp.non_null_count} / {comp.total_rows} records</span>
                    <span>{comp.total_rows - comp.non_null_count} blank</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
