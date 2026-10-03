import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, Sparkles, ArrowRight, Loader2 } from 'lucide-react';

export function UploadSection({
  onFileUpload,
  onSampleSelect,
  isLoading = false,
  statusMessage = '',
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const samples = [
    {
      id: "Sample_SOV_1_Standard.xlsx",
      title: "Sample 1: Baseline Clean",
      badge: "Baseline Test",
      desc: "Single sheet, headers in row 1, standard column naming conventions.",
      tagColor: "border-emerald-500/30 text-emerald-400 bg-emerald-500/10",
    },
    {
      id: "Sample_SOV_2_Complex_Semantic.xlsx",
      title: "Sample 2: Complex Semantic",
      badge: "Semantic Test",
      desc: "Abbreviated headers ('Bldg Repl Cost', 'Fire Prot.'), currency symbols, negative values.",
      tagColor: "border-indigo-500/30 text-indigo-300 bg-indigo-500/10",
    },
    {
      id: "Sample_SOV_3_MultiSheet_Messy.xlsx",
      title: "Sample 3: Multi-Sheet & Dispersed",
      badge: "Structural Test",
      desc: "3 sheets, title banner on rows 1-3, header row 4, instructions sheet to reject.",
      tagColor: "border-amber-500/30 text-amber-300 bg-amber-500/10",
    },
  ];

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Drag & Drop Card */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isLoading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center transition-all cursor-pointer ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-950/30 scale-[1.01]'
            : 'border-slate-700/80 bg-slate-900/60 hover:border-slate-600 hover:bg-slate-900/90'
        } ${isLoading ? 'opacity-80 pointer-events-none' : ''}`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          accept=".xlsx,.xls,.csv"
          className="hidden"
        />

        <div className="max-w-md mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mx-auto flex items-center justify-center shadow-inner">
            {isLoading ? (
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            ) : (
              <UploadCloud className="w-8 h-8" />
            )}
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white">
              {isLoading ? 'Autonomous Agents Processing...' : 'Upload Statement of Values (SOV)'}
            </h3>
            <p className="text-sm text-slate-400 mt-1">
              {isLoading
                ? statusMessage || 'Agent 1, Agent 2, and Agent 3 analyzing dataset...'
                : 'Drag and drop your Excel (.xlsx) or CSV file here, or click to browse'}
            </p>
          </div>

          {!isLoading && (
            <div className="flex items-center justify-center space-x-3 text-xs text-slate-400 pt-2">
              <span className="flex items-center">
                <FileSpreadsheet className="w-3.5 h-3.5 mr-1 text-emerald-400" /> Excel (.xlsx, .xls)
              </span>
              <span>•</span>
              <span className="flex items-center">
                <FileSpreadsheet className="w-3.5 h-3.5 mr-1 text-cyan-400" /> CSV (.csv)
              </span>
              <span>•</span>
              <span>Multi-sheet capable</span>
            </div>
          )}
        </div>
      </div>

      {/* 1-Click Test Samples */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
              Instant 1-Click Evaluation Samples
            </h4>
          </div>
          <span className="text-xs text-slate-400">Official Benchmark Datasets</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {samples.map((sample) => (
            <div
              key={sample.id}
              onClick={() => !isLoading && onSampleSelect(sample.id)}
              className={`p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-800/60 hover:border-indigo-500/40 transition-all cursor-pointer group flex flex-col justify-between ${
                isLoading ? 'opacity-50 pointer-events-none' : ''
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${sample.tagColor}`}>
                    {sample.badge}
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                </div>
                <h5 className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
                  {sample.title}
                </h5>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {sample.desc}
                </p>
              </div>

              <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-indigo-400 font-mono flex items-center justify-between">
                <span>Load Dataset</span>
                <span className="text-slate-600">.xlsx</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
