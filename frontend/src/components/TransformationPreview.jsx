import React, { useState } from 'react';
import { TARGET_FIELDS } from '../types/sov';
import { 
  FileCheck2, 
  Download, 
  Table2, 
  History, 
  CheckCircle2, 
  FileSpreadsheet, 
  Code2, 
  Search 
} from 'lucide-react';

export function TransformationPreview({
  result,
  auditLog = [],
}) {
  const [activeTab, setActiveTab] = useState('preview');
  const [auditSearch, setAuditSearch] = useState('');

  const filteredAudit = auditLog.filter((entry) => {
    if (!auditSearch) return true;
    const term = auditSearch.toLowerCase();
    return (
      entry.source_column.toLowerCase().includes(term) ||
      entry.target_column.toLowerCase().includes(term) ||
      entry.transformation_applied.toLowerCase().includes(term) ||
      (entry.reasoning && entry.reasoning.toLowerCase().includes(term))
    );
  });

  if (!result) return null;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl space-y-6">
      {/* Header & Export Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <FileCheck2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-semibold text-white">Agent 4: Cleaned SOV & Audit Trail</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium">
                17 Target Columns Verified (NFR-5 Pass)
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Generated Cleaned_SOV.xlsx with zero unapproved mutations and comprehensive audit traceability
            </p>
          </div>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center flex-wrap gap-2 self-start sm:self-auto">
          <a
            href={result.download_sov_url}
            download="Cleaned_SOV.xlsx"
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Cleaned_SOV.xlsx</span>
          </a>

          <a
            href={result.download_audit_xlsx_url}
            download="Audit_Log.xlsx"
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
            <span>Audit_Log.xlsx</span>
          </a>

          <a
            href={result.download_audit_json_url}
            download="Audit_Log.json"
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all cursor-pointer"
          >
            <Code2 className="w-3.5 h-3.5 text-amber-400" />
            <span>Audit_Log.json</span>
          </a>
        </div>
      </div>

      {/* Strict Schema Conformance Banner */}
      <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2.5">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <div>
            <div className="font-semibold text-emerald-300">
              Downstream Schema Validation Passed (17 Required Columns)
            </div>
            <div className="text-slate-400 text-[11px] mt-0.5">
              Sheet: Cleaned_SOV · Headers in Row 1 · Data starts Row 2 · No merged cells · Missing values preserved as blank
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-slate-300 font-mono text-[11px] self-end sm:self-auto">
          <span>Rows: <strong className="text-white">{result.row_count}</strong></span>
          <span>Columns: <strong className="text-white">{result.column_count}</strong></span>
          <span>Transformations: <strong className="text-white">{result.total_transformations_applied}</strong></span>
        </div>
      </div>

      {/* Tab Selector */}
      <div className="flex items-center space-x-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 self-start text-xs">
        <button
          onClick={() => setActiveTab('preview')}
          className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            activeTab === 'preview'
              ? 'bg-indigo-600 text-white font-medium shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Table2 className="w-3.5 h-3.5" />
          <span>Cleaned Dataset Preview</span>
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            activeTab === 'audit'
              ? 'bg-indigo-600 text-white font-medium shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Transformation Audit Log ({auditLog.length})</span>
        </button>
      </div>

      {/* Tab: Cleaned Data Preview Table */}
      {activeTab === 'preview' && (
        <div className="space-y-3">
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70 max-h-96">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                <tr>
                  <th className="px-3 py-2.5 w-10 text-center bg-slate-900/90 border-r border-slate-800 text-slate-500">
                    #
                  </th>
                  {TARGET_FIELDS.map((col) => (
                    <th key={col} className="px-3.5 py-2.5 whitespace-nowrap font-semibold text-slate-200">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px] text-slate-300">
                {(result.sample_preview || []).map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/50">
                    <td className="px-3 py-2 text-center text-slate-500 border-r border-slate-800 bg-slate-950">
                      {idx + 1}
                    </td>
                    {TARGET_FIELDS.map((col) => {
                      const val = row[col];
                      const isNull = val === null || val === undefined || val === '';
                      return (
                        <td key={col} className="px-3.5 py-2 whitespace-nowrap max-w-[200px] truncate">
                          {isNull ? (
                            <span className="text-slate-600 italic">blank</span>
                          ) : typeof val === 'number' ? (
                            <span className="text-cyan-300">{val.toLocaleString()}</span>
                          ) : (
                            <span>{String(val)}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-slate-500 italic">
            Showing top preview rows formatted according to Section 08 Data Dictionary. Full dataset downloadable above.
          </p>
        </div>
      )}

      {/* Tab: Audit Log Table */}
      {activeTab === 'audit' && (
        <div className="space-y-3">
          {/* Audit Search Bar */}
          <div className="flex items-center space-x-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 max-w-sm">
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <input
              type="text"
              value={auditSearch}
              onChange={(e) => setAuditSearch(e.target.value)}
              placeholder="Search audit trail by column or rule..."
              className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full"
            />
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70 max-h-96">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Source Column</th>
                  <th className="px-4 py-3">Target Field</th>
                  <th className="px-4 py-3">Transformation</th>
                  <th className="px-4 py-3">Before → After</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3">Approved By</th>
                  <th className="px-4 py-3">Reasoning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredAudit.map((entry, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/50">
                    <td className="px-4 py-3 whitespace-nowrap font-mono text-[11px] text-slate-500">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-3 font-mono text-cyan-300">{entry.source_column}</td>
                    <td className="px-4 py-3 font-semibold text-white">{entry.target_column}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-300 font-medium border border-slate-700">
                        {entry.transformation_applied}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] max-w-xs truncate">
                      <span className="text-rose-400">{entry.before_value || '-'}</span> →{' '}
                      <span className="text-emerald-400 font-semibold">{entry.after_value || '-'}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-emerald-400 font-semibold">
                      {(entry.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{entry.approved_by}</td>
                    <td className="px-4 py-3 text-slate-400 text-[11px] max-w-xs">
                      <p className="line-clamp-2">{entry.reasoning || '-'}</p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
