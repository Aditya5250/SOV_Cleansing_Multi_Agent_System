import React, { useState } from 'react';
import { Header } from './components/Header';
import { AgentPipeline } from './components/AgentPipeline';
import { UploadSection } from './components/UploadSection';
import { SheetDiscoveryView } from './components/SheetDiscoveryView';
import { SchemaMappingView } from './components/SchemaMappingView';
import { DataQualityView } from './components/DataQualityView';
import { RecommendationsQueue } from './components/RecommendationsQueue';
import { TransformationPreview } from './components/TransformationPreview';
import { 
  uploadSOVFile, 
  loadSampleSOV, 
  overrideSheetSelection, 
  updateMappingOverrides, 
  submitReReasoning, 
  executeTransformation 
} from './services/api';
import { 
  AlertCircle, 
  CheckCircle2, 
  Layers, 
  GitMerge, 
  Activity, 
  UserCheck, 
  FileCheck2
} from 'lucide-react';

export function App() {
  const [pipelineState, setPipelineState] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  // Human Review State
  const [decisions, setDecisions] = useState({});
  const [mappingOverrides, setMappingOverrides] = useState({});

  // Transformation Result
  const [transformationResult, setTransformationResult] = useState(null);
  const [isTransforming, setIsTransforming] = useState(false);

  // Active section tab
  const [activeTab, setActiveTab] = useState('discovery');

  // Compute Current Stage: 1 = Ingestion/Agents 1-3, 2 = HITL Review, 3 = Agent 4 Complete
  const currentStage = transformationResult ? 3 : pipelineState ? 2 : 1;

  // Handle File Upload
  const handleFileUpload = async (file) => {
    setIsLoading(true);
    setErrorMessage(null);
    setStatusMessage('Agent 1 scanning sheets, Agent 2 matching schema, Agent 3 evaluating quality...');

    try {
      const state = await uploadSOVFile(file);
      setPipelineState(state);
      setTransformationResult(null);
      setDecisions({});
      setMappingOverrides({});
      setActiveTab('discovery');
    } catch (err) {
      setErrorMessage(err.message || 'Failed to process SOV file');
    } finally {
      setIsLoading(false);
      setStatusMessage('');
    }
  };

  // Handle Sample File Load
  const handleSampleSelect = async (sampleName) => {
    setIsLoading(true);
    setErrorMessage(null);
    setStatusMessage(`Loading benchmark sample '${sampleName}' across 4-agent pipeline...`);

    try {
      const state = await loadSampleSOV(sampleName);
      setPipelineState(state);
      setTransformationResult(null);
      setDecisions({});
      setMappingOverrides({});
      setActiveTab('discovery');
    } catch (err) {
      setErrorMessage(err.message || 'Failed to load test sample');
    } finally {
      setIsLoading(false);
      setStatusMessage('');
    }
  };

  // Handle Sheet / Header Override
  const handleSelectSheet = async (sheetName, headerRow) => {
    if (!pipelineState) return;
    setIsLoading(true);
    try {
      const updated = await overrideSheetSelection(pipelineState.session_id, sheetName, headerRow);
      setPipelineState(updated);
    } catch (err) {
      setErrorMessage(err.message || 'Failed to update sheet');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Column Mapping Override
  const handleUpdateMapping = async (overrides) => {
    if (!pipelineState) return;
    setMappingOverrides(overrides);
    try {
      await updateMappingOverrides(pipelineState.session_id, overrides);
    } catch (err) {
      console.error('Failed to save mapping override:', err);
    }
  };

  // Handle Recommendation Decisions (Accept/Reject/Edit)
  const handleUpdateDecision = (recId, status, userValue, feedback) => {
    setDecisions((prev) => ({
      ...prev,
      [recId]: { status, user_value: userValue, feedback },
    }));
  };

  // Handle "Approve All High Confidence" (>= 90%)
  const handleApproveAllHighConfidence = () => {
    if (!pipelineState) return;
    const newDecisions = { ...decisions };
    pipelineState.recommendations.forEach((rec) => {
      if (rec.confidence >= 0.90) {
        newDecisions[rec.id] = { status: 'accepted', user_value: rec.proposed_after };
      }
    });
    setDecisions(newDecisions);
  };

  // Handle Re-reasoning on Rejection Feedback (Bonus Feature)
  const handleReReason = async (recId, feedback) => {
    if (!pipelineState) return;
    const updatedItem = await submitReReasoning(pipelineState.session_id, recId, feedback);

    setPipelineState((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        recommendations: prev.recommendations.map((r) => (r.id === recId ? updatedItem : r)),
      };
    });
  };

  // Trigger Controlled Transformation (Agent 4)
  const handleTriggerTransformation = async () => {
    if (!pipelineState) return;
    setIsTransforming(true);
    setErrorMessage(null);

    try {
      // Map overrides format
      const overridesClean = {};
      Object.entries(mappingOverrides).forEach(([k, v]) => {
        if (v) overridesClean[k] = v;
      });

      const result = await executeTransformation(
        pipelineState.session_id,
        decisions,
        overridesClean,
        'Senior Exposure Analyst (Human Reviewer)'
      );

      setTransformationResult(result);
      setActiveTab('export');
    } catch (err) {
      setErrorMessage(err.message || 'Transformation failed');
    } finally {
      setIsTransforming(false);
    }
  };

  // Reset to Upload Stage
  const handleReset = () => {
    setPipelineState(null);
    setTransformationResult(null);
    setDecisions({});
    setMappingOverrides({});
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-white">
      {/* Top Header */}
      <Header
        sessionId={pipelineState?.session_id}
        filename={pipelineState?.file_info?.filename}
        onReset={pipelineState ? handleReset : undefined}
        isConfigOpen={isConfigOpen}
        setIsConfigOpen={setIsConfigOpen}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Error Alert Banner */}
        {errorMessage && (
          <div className="bg-rose-950/40 border border-rose-500/50 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm text-rose-300 shadow-lg">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="whitespace-pre-line">
                <span className="font-semibold">Error:</span> {errorMessage}
              </div>
            </div>
            <div className="flex items-center space-x-3 shrink-0 self-end sm:self-auto">
              <button
                onClick={() => setIsConfigOpen(true)}
                className="px-3 py-1.5 rounded-lg bg-rose-900/60 hover:bg-rose-800 text-xs font-semibold text-white border border-rose-600/50 transition-all cursor-pointer shadow-sm"
              >
                Configure Backend URL
              </button>
              <button
                onClick={() => setErrorMessage(null)}
                className="text-xs text-rose-400 hover:text-white underline cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Four-Agent Pipeline Workflow Diagram */}
        <AgentPipeline
          currentStage={currentStage}
          agentLogs={pipelineState?.agent_logs || []}
          currentAgent={pipelineState?.current_agent || 'Awaiting Upload'}
        />

        {/* View Switcher if File Loaded */}
        {!pipelineState ? (
          <UploadSection
            onFileUpload={handleFileUpload}
            onSampleSelect={handleSampleSelect}
            isLoading={isLoading}
            statusMessage={statusMessage}
          />
        ) : (
          <div className="space-y-6">
            {/* Section Navigation Tabs */}
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 overflow-x-auto text-xs sm:text-sm">
              <button
                onClick={() => setActiveTab('discovery')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'discovery'
                    ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>1. Sheet Intelligence</span>
              </button>

              <button
                onClick={() => setActiveTab('mapping')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'mapping'
                    ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <GitMerge className="w-4 h-4" />
                <span>2. Schema Mapping</span>
              </button>

              <button
                onClick={() => setActiveTab('quality')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'quality'
                    ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Activity className="w-4 h-4" />
                <span>3. Data Quality & Profiling</span>
              </button>

              <button
                onClick={() => setActiveTab('review')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'review'
                    ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <UserCheck className="w-4 h-4" />
                <span>4. Human Approval Queue</span>
                {pipelineState.recommendations.length > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-amber-500/20 text-amber-300 font-mono">
                    {pipelineState.recommendations.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveTab('export')}
                disabled={!transformationResult}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap ${
                  activeTab === 'export'
                    ? 'bg-emerald-600 text-white font-semibold shadow-md shadow-emerald-600/20'
                    : transformationResult
                    ? 'text-emerald-400 hover:text-white hover:bg-slate-800/60 cursor-pointer'
                    : 'text-slate-600 cursor-not-allowed opacity-60'
                }`}
              >
                <FileCheck2 className="w-4 h-4" />
                <span>5. Cleaned SOV & Audit</span>
                {transformationResult && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                )}
              </button>
            </div>

            {/* Tab Views */}
            {activeTab === 'discovery' && (
              <SheetDiscoveryView
                sheets={pipelineState.sheets}
                selectedSheet={pipelineState.selected_sheet}
                onSelectSheet={handleSelectSheet}
              />
            )}

            {activeTab === 'mapping' && pipelineState.schema_mapping && (
              <SchemaMappingView
                mappingResult={pipelineState.schema_mapping}
                onUpdateMapping={handleUpdateMapping}
              />
            )}

            {activeTab === 'quality' && pipelineState.data_quality && (
              <DataQualityView
                dataQuality={pipelineState.data_quality}
              />
            )}

            {activeTab === 'review' && (
              <RecommendationsQueue
                recommendations={pipelineState.recommendations}
                decisions={decisions}
                onUpdateDecision={handleUpdateDecision}
                onApproveAllHighConfidence={handleApproveAllHighConfidence}
                onReReason={handleReReason}
                onTriggerTransformation={handleTriggerTransformation}
                isTransforming={isTransforming}
              />
            )}

            {activeTab === 'export' && transformationResult && (
              <TransformationPreview
                result={transformationResult}
                auditLog={pipelineState.audit_log}
              />
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-5 text-center text-xs text-slate-500 bg-slate-950/60">
        <p>
          Agentic SOV Cleansing & Intelligence System · Built for Adrosonic Build Hackathon · 17-Column Target Schema Standard
        </p>
      </footer>
    </div>
  );
}

export default App;
