import React, { useState } from 'react';
import { FileSearch, CheckCircle2, Layers, Table2 } from 'lucide-react';

export function SheetDiscoveryView({
  sheets = [],
  selectedSheet,
  onSelectSheet,
}) {
  const [customHeaderRow, setCustomHeaderRow] = useState(
    selectedSheet?.header_row || 1
  );

  const handleHeaderRowChange = (newRow) => {
    setCustomHeaderRow(newRow);
    if (selectedSheet) {
      onSelectSheet(selectedSheet.sheet_name, newRow);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <FileSearch className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-semibold text-white">Agent 1: Sheet Intelligence & Discovery</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium">
                {sheets.length} Sheets Analyzed
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Evaluated structural characteristics, header quality, and non-null distribution
            </p>
          </div>
        </div>

        {selectedSheet && (
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400">Header Row:</span>
            <div className="flex items-center space-x-1.5 bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1">
              <span className="font-mono text-cyan-300 font-medium">Row {selectedSheet.header_row}</span>
              <input
                type="number"
                min="1"
                max="25"
                value={customHeaderRow}
                onChange={(e) => handleHeaderRowChange(parseInt(e.target.value) || 1)}
                className="w-12 bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-xs text-white text-center ml-1"
                title="Override header row position"
              />
            </div>
          </div>
        )}
      </div>

      {/* Sheets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sheets.map((sheet) => {
          const isSelected = selectedSheet?.sheet_name === sheet.sheet_name;
          const isPrimary = sheet.classification === 'Primary';
          const isReject = sheet.classification === 'Reject';

          return (
            <div
              key={sheet.sheet_name}
              onClick={() => onSelectSheet(sheet.sheet_name, sheet.header_row)}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-slate-800/80 border-indigo-500 shadow-md ring-1 ring-indigo-500/40'
                  : 'bg-slate-950/50 border-slate-800 hover:border-slate-700 hover:bg-slate-900/50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-1.5 truncate pr-2">
                    <Layers className="w-4 h-4 text-slate-400 shrink-0" />
                    <span className="text-sm font-semibold text-slate-200 truncate" title={sheet.sheet_name}>
                      {sheet.sheet_name}
                    </span>
                  </div>

                  <span
                    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border shrink-0 ${
                      isPrimary
                        ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10'
                        : isReject
                        ? 'border-rose-500/30 text-rose-400 bg-rose-500/10'
                        : 'border-cyan-500/30 text-cyan-400 bg-cyan-500/10'
                    }`}
                  >
                    {sheet.classification}
                  </span>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 my-3 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                  <div>
                    <span className="text-slate-500">Rows:</span>{' '}
                    <span className="font-mono text-slate-200 font-medium">{sheet.row_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Cols:</span>{' '}
                    <span className="font-mono text-slate-200 font-medium">{sheet.column_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Fill Ratio:</span>{' '}
                    <span className="font-mono text-slate-200 font-medium">
                      {(sheet.non_null_ratio * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Confidence:</span>{' '}
                    <span className="font-mono text-cyan-300 font-medium">
                      {(sheet.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Reasoning */}
                <div className="space-y-1">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Agent Rationale
                  </div>
                  {sheet.reasoning.map((r, i) => (
                    <div key={i} className="text-xs text-slate-400 flex items-start space-x-1.5">
                      <span className="text-indigo-400 shrink-0">•</span>
                      <span className="leading-snug">{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-2.5 border-t border-slate-800 text-[11px] flex items-center justify-between">
                <span className="text-slate-500">Header at Row {sheet.header_row}</span>
                {isSelected && (
                  <span className="text-indigo-400 font-medium flex items-center">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Active Schedule
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Raw Preview Table of Selected Sheet */}
      {selectedSheet && selectedSheet.preview_rows && selectedSheet.preview_rows.length > 0 && (
        <div className="space-y-2 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center">
              <Table2 className="w-3.5 h-3.5 mr-1.5 text-cyan-400" /> Raw Sheet Preview (Rows {selectedSheet.header_row} - {selectedSheet.header_row + selectedSheet.preview_rows.length - 1})
            </span>
            <span className="text-[11px] text-slate-500">Row {selectedSheet.header_row} detected as Header</span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70 max-h-56">
            <table className="w-full text-left text-xs text-slate-300">
              <tbody>
                {selectedSheet.preview_rows.map((row, rIdx) => {
                  const isHeader = rIdx === 0;
                  return (
                    <tr
                      key={rIdx}
                      className={`border-b border-slate-800/80 ${
                        isHeader ? 'bg-indigo-950/40 text-cyan-300 font-semibold' : 'hover:bg-slate-900/40'
                      }`}
                    >
                      <td className="px-3 py-2 font-mono text-[10px] text-slate-500 bg-slate-900/50 w-12 text-center border-r border-slate-800">
                        R{selectedSheet.header_row + rIdx}
                      </td>
                      {row.map((cell, cIdx) => (
                        <td key={cIdx} className="px-3 py-2 whitespace-nowrap font-mono text-[11px] max-w-[180px] truncate">
                          {cell !== null && cell !== "" ? String(cell) : <span className="text-slate-600 italic">null</span>}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
