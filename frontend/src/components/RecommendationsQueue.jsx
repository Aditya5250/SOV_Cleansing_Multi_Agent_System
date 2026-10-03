import React, { useState } from 'react';
import { 
  UserCheck, 
  Check, 
  X, 
  Edit3, 
  Sparkles, 
  CheckCheck, 
  MessageSquare, 
  Loader2, 
  HelpCircle, 
  ArrowRight,
  ShieldCheck 
} from 'lucide-react';

export function RecommendationsQueue({
  recommendations = [],
  decisions = {},
  onUpdateDecision,
  onApproveAllHighConfidence,
  onReReason,
  onTriggerTransformation,
  isTransforming = false,
}) {
  const [rejectingRecId, setRejectingRecId] = useState(null);
  const [rejectFeedback, setRejectFeedback] = useState('');
  const [editingRecId, setEditingRecId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [isReReasoning, setIsReReasoning] = useState(false);

  // High confidence items count (>= 0.90)
  const highConfidenceCount = recommendations.filter((r) => r.confidence >= 0.90).length;

  // Unreviewed items count
  const unreviewedCount = recommendations.filter((r) => !decisions[r.id]).length;
  const acceptedCount = Object.values(decisions).filter((d) => d.status === 'accepted').length;
  const rejectedCount = Object.values(decisions).filter((d) => d.status === 'rejected').length;

  const handleOpenRejectModal = (recId) => {
    setRejectingRecId(recId);
    setRejectFeedback('');
  };

  const handleConfirmReject = async () => {
    if (!rejectingRecId) return;

    if (rejectFeedback.trim()) {
      setIsReReasoning(true);
      try {
        await onReReason(rejectingRecId, rejectFeedback.trim());
      } catch (e) {
        console.error('Re-reasoning error:', e);
      } finally {
        setIsReReasoning(false);
      }
    }

    onUpdateDecision(rejectingRecId, 'rejected', undefined, rejectFeedback.trim());
    setRejectingRecId(null);
  };

  const handleOpenEditModal = (rec) => {
    setEditingRecId(rec.id);
    setEditValue(rec.proposed_after || '');
  };

  const handleConfirmEdit = () => {
    if (!editingRecId) return;
    onUpdateDecision(editingRecId, 'accepted', editValue);
    setEditingRecId(null);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-semibold text-white">Human-in-the-Loop Review Queue</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-medium">
                {recommendations.length} AI Recommendations
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Mandatory Gatekeeper: No data mutation occurs without explicit human approval (Rule C-01)
            </p>
          </div>
        </div>

        {/* Global Batch Action */}
        <div className="flex items-center space-x-3 self-start sm:self-auto">
          <button
            onClick={onApproveAllHighConfidence}
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <CheckCheck className="w-4 h-4" />
            <span>Approve All High Confidence (≥ 90%) ({highConfidenceCount})</span>
          </button>
        </div>
      </div>

      {/* Review Progress Status Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
        <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <span className="text-slate-400">Total Recommendations:</span>
          <span className="font-mono font-semibold text-white">{recommendations.length}</span>
        </div>
        <div className="p-3 rounded-xl border border-emerald-900/30 bg-emerald-950/10 flex items-center justify-between">
          <span className="text-emerald-400">Approved by Human:</span>
          <span className="font-mono font-semibold text-emerald-400">{acceptedCount}</span>
        </div>
        <div className="p-3 rounded-xl border border-rose-900/30 bg-rose-950/10 flex items-center justify-between">
          <span className="text-rose-400">Rejected / Feedback:</span>
          <span className="font-mono font-semibold text-rose-400">{rejectedCount}</span>
        </div>
        <div className="p-3 rounded-xl border border-amber-900/30 bg-amber-950/10 flex items-center justify-between">
          <span className="text-amber-400">Pending Human Action:</span>
          <span className="font-mono font-semibold text-amber-400">{unreviewedCount}</span>
        </div>
      </div>

      {/* Recommendation Cards Queue */}
      <div className="space-y-3.5">
        {recommendations.length === 0 ? (
          <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
            No pending data quality recommendations for this dataset.
          </div>
        ) : (
          recommendations.map((rec) => {
            const decision = decisions[rec.id];
            const isAccepted = decision?.status === 'accepted';
            const isRejected = decision?.status === 'rejected';
            const hasUserValue = decision?.user_value !== undefined;
            const displayValue = hasUserValue ? decision.user_value : rec.proposed_after;

            return (
              <div
                key={rec.id}
                className={`p-4 rounded-xl border transition-all ${
                  isAccepted
                    ? 'bg-emerald-950/15 border-emerald-500/40 shadow-sm'
                    : isRejected
                    ? 'bg-rose-950/15 border-rose-500/40 opacity-75'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left: Metadata & Value Transformation */}
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-semibold text-cyan-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        {rec.field}
                      </span>
                      <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        {rec.action_type.replace('_', ' ')}
                      </span>
                      <span className="font-mono text-xs text-slate-400">
                        Conf: <span className={rec.confidence >= 0.9 ? 'text-emerald-400' : 'text-amber-400'}>{(rec.confidence * 100).toFixed(0)}%</span>
                      </span>

                      {rec.status === 'modified' && (
                        <span className="px-2 py-0.5 text-[10px] font-semibold text-purple-300 bg-purple-950/40 rounded-full border border-purple-800 flex items-center gap-1">
                          <Sparkles className="w-2.5 h-2.5" /> AI Re-reasoned
                        </span>
                      )}
                    </div>

                    {/* Before -> After Transformation Pill */}
                    <div className="flex items-center space-x-2 text-xs pt-1">
                      <span className="text-slate-400">Current:</span>
                      <span className="font-mono bg-rose-950/30 text-rose-300 px-2 py-0.5 rounded border border-rose-900/40">
                        {rec.before_value || '<empty>'}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                      <span className="text-slate-400">Proposed:</span>
                      <span className="font-mono bg-emerald-950/40 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800/40 font-semibold">
                        {displayValue || '<blank>'}
                      </span>
                      {hasUserValue && (
                        <span className="text-[10px] text-amber-400 italic">(User Override)</span>
                      )}
                    </div>

                    {/* Explainable Rationale */}
                    <p className="text-xs text-slate-300 pt-1 leading-relaxed">
                      {rec.reasoning}
                    </p>

                    {/* Uncertainty Note if present */}
                    {rec.uncertainty && (
                      <div className="text-[11px] text-amber-400/90 flex items-start space-x-1.5 pt-0.5">
                        <HelpCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <span>Uncertainty: {rec.uncertainty}</span>
                      </div>
                    )}

                    {/* Rejection Feedback Note if rejected */}
                    {decision?.feedback && (
                      <div className="text-[11px] text-rose-300 bg-rose-950/30 p-2 rounded-lg border border-rose-900/30 mt-1">
                        <span className="font-semibold">Reviewer Note:</span> {decision.feedback}
                      </div>
                    )}
                  </div>

                  {/* Right: Human Actions */}
                  <div className="flex items-center space-x-2 shrink-0 self-end lg:self-center">
                    <button
                      onClick={() => onUpdateDecision(rec.id, 'accepted', hasUserValue ? decision.user_value : rec.proposed_after)}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                        isAccepted
                          ? 'bg-emerald-600 text-white shadow-md'
                          : 'bg-slate-800 hover:bg-emerald-600/30 text-slate-300 hover:text-emerald-300 border border-slate-700'
                      }`}
                      title="Accept recommendation"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Accept</span>
                    </button>

                    <button
                      onClick={() => handleOpenEditModal(rec)}
                      className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-all cursor-pointer"
                      title="Modify proposed value"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Edit</span>
                    </button>

                    <button
                      onClick={() => handleOpenRejectModal(rec.id)}
                      className={`flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs transition-all cursor-pointer ${
                        isRejected
                          ? 'bg-rose-600 text-white'
                          : 'bg-slate-800 hover:bg-rose-600/30 text-slate-300 hover:text-rose-300 border border-slate-700'
                      }`}
                      title="Reject and provide feedback for AI re-reasoning"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Execution Call to Action */}
      <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>
            {unreviewedCount === 0
              ? 'All recommendations reviewed. Ready for Agent 4 controlled execution.'
              : `${unreviewedCount} unreviewed item(s). You can approve all high-confidence or review individually.`}
          </span>
        </div>

        <button
          onClick={onTriggerTransformation}
          disabled={isTransforming || acceptedCount === 0}
          className="flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
        >
          {isTransforming ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin mr-1" />
              <span>Agent 4 Executing Controlled Transformations...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4" />
              <span>Execute Controlled Transformation ({acceptedCount} Approved)</span>
            </>
          )}
        </button>
      </div>

      {/* Rejection & Re-reasoning Modal */}
      {rejectingRecId && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-indigo-400" />
                <span>Reviewer Feedback & AI Re-reasoning</span>
              </h4>
              <button
                onClick={() => setRejectingRecId(null)}
                className="text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Provide instructions or justification for rejecting this recommendation.
              The AI agent will iteratively re-reason based on your feedback.
            </p>

            <textarea
              value={rejectFeedback}
              onChange={(e) => setRejectFeedback(e.target.value)}
              placeholder="e.g., Do not convert negative amount; underwriter confirmed policy exclusion. Or: Standardize state to CA."
              rows={3}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setRejectingRecId(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                disabled={isReReasoning}
                className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold disabled:opacity-50 cursor-pointer"
              >
                {isReReasoning && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Reject & Re-reason</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Value Modal */}
      {editingRecId && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-sm w-full shadow-2xl space-y-4">
            <h4 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Edit3 className="w-4 h-4 text-indigo-400" />
              <span>Modify Proposed Transformation</span>
            </h4>

            <div>
              <label className="text-xs text-slate-400 block mb-1">New Target Value:</label>
              <input
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setEditingRecId(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmEdit}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold cursor-pointer"
              >
                Save & Approve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
