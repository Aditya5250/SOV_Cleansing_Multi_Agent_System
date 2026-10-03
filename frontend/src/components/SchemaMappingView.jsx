import React, { useState } from 'react';
import { TARGET_FIELDS } from '../types/sov';
import { GitMerge, ArrowRight, Sparkles, AlertCircle } from 'lucide-react';

export function SchemaMappingView({
  mappingResult,
  onUpdateMapping,
}) {
  const [localOverrides, setLocalOverrides] = useState({});
  const [filterMode, setFilterMode] = useState('all');

  const mappingsList = Object.entries(mappingResult?.mappings || {});

  const handleTargetChange = (sourceCol, targetCol) => {
    const updated = {
      ...localOverrides,
      [sourceCol]: targetCol === 'unmapped' ? null : targetCol,
    };
    setLocalOverrides(updated);
    onUpdateMapping(updated);
  };

  const filteredMappings = mappingsList.filter(([, mapping]) => {
    if (filterMode === 'flagged') return mapping.flag_for_review || mapping.confidence < 0.85;
    if (filterMode === 'semantic') return mapping.method === 'semantic' || mapping.method === 'llm';
    return true;
  });

  const getMethodBadge = (method) => {
    switch (method) {
      case 'exact':
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Exact</span>;
      case 'fuzzy':
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">Fuzzy (RapidFuzz)</span>;
      case 'semantic':
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 flex items-center gap-1"><Sparkles className="w-2.5 h-2.5" /> Semantic Vector</span>;
      case 'llm':
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 flex items-center gap-1"><Sparkles className="w-2.5 h-2.5" /> LLM Reasoned</span>;
      case 'manual':
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">Manual Override</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-slate-800 text-slate-400 border border-slate-700">Unresolved</span>;
    }
  };

  const getConfidenceBadge = (conf) => {
    const pct = Math.round(conf * 100);
    if (pct >= 90) {
      return <span className="font-mono text-emerald-400 font-semibold">{pct}%</span>;
    } else if (pct >= 70) {
      return <span className="font-mono text-amber-400 font-semibold">{pct}%</span>;
    }
    return <span className="font-mono text-rose-400 font-semibold">{pct}%</span>;
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl space-y-6">
      {/* Header & Metrics */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
            <GitMerge className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-semibold text-white">Agent 2: Schema Mapping Agent</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-medium">
                Overall Accuracy {((mappingResult?.overall_confidence || 0) * 100).toFixed(0)}% (Target ≥ 74%)
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Two-Pass Matching: Pass 1 (Exact & RapidFuzz) → Pass 2 (Sentence-BERT Embeddings & LLM)
            </p>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center space-x-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 self-start sm:self-auto text-xs">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1 rounded-lg transition-all ${
              filterMode === 'all' ? 'bg-indigo-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            All Columns ({mappingsList.length})
          </button>
          <button
            onClick={() => setFilterMode('semantic')}
            className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
              filterMode === 'semantic' ? 'bg-indigo-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3 h-3 text-purple-300" /> Semantic / LLM
          </button>
          <button
            onClick={() => setFilterMode('flagged')}
            className={`px-3 py-1 rounded-lg transition-all ${
              filterMode === 'flagged' ? 'bg-indigo-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Flagged & Low Conf ({mappingResult?.unresolved_count || 0})
          </button>
        </div>
      </div>

      {/* Unmapped Target Fields Warning */}
      {mappingResult?.unmapped_target_fields && mappingResult.unmapped_target_fields.length > 0 && (
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex items-start space-x-3 text-xs">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-slate-300">
              Unmapped Standard Schema Fields ({mappingResult.unmapped_target_fields.length}):
            </span>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {mappingResult.unmapped_target_fields.map((field) => (
                <span key={field} className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[11px] font-mono border border-slate-700">
                  {field} (blank)
                </span>
              ))}
            </div>
            <p className="text-[11px] text-slate-500 pt-0.5">
              Unmapped target columns will be preserved as clean empty cells in Cleaned_SOV.xlsx (Rule C-02).
            </p>
          </div>
        </div>
      )}

      {/* Mappings Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="px-4 py-3">Source Header</th>
              <th className="px-2 py-3 text-center w-8"></th>
              <th className="px-4 py-3">Target Schema Field (17 Fields)</th>
              <th className="px-4 py-3 text-center">Confidence</th>
              <th className="px-4 py-3">Mapping Method</th>
              <th className="px-4 py-3">Explainable Rationale</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {filteredMappings.map(([srcCol, mapping]) => {
              const currentTarget = localOverrides[srcCol] !== undefined ? localOverrides[srcCol] : mapping.target_column;

              return (
                <tr key={srcCol} className="hover:bg-slate-900/50 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-200">
                    <span className="font-mono bg-slate-800/80 px-2 py-1 rounded text-cyan-300 border border-slate-700/60">
                      {srcCol}
                    </span>
                  </td>

                  <td className="px-2 py-3 text-center text-slate-600">
                    <ArrowRight className="w-3.5 h-3.5 inline" />
                  </td>

                  <td className="px-4 py-3">
                    <select
                      value={currentTarget || 'unmapped'}
                      onChange={(e) => handleTargetChange(srcCol, e.target.value)}
                      className={`bg-slate-900 border rounded-lg px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all ${
                        currentTarget ? 'text-white border-slate-700' : 'text-slate-500 border-rose-500/40 bg-rose-950/20'
                      }`}
                    >
                      <option value="unmapped">-- Unmapped / Skip --</option>
                      {TARGET_FIELDS.map((tf) => (
                        <option key={tf} value={tf}>
                          {tf}
                        </option>
                      ))}
                    </select>
                  </td>

                  <td className="px-4 py-3 text-center">
                    {getConfidenceBadge(mapping.confidence)}
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap">
                    {getMethodBadge(mapping.method)}
                  </td>

                  <td className="px-4 py-3 text-slate-400 max-w-sm">
                    <p className="line-clamp-2 leading-relaxed text-[11px]" title={mapping.reasoning}>
                      {mapping.reasoning}
                    </p>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
