import React from 'react';
import { X, History, Clock, CheckCircle2, AlertTriangle, GitCompare } from 'lucide-react';
import { AuditSummaryItem } from '../types/audit';

interface AuditHistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  audits: AuditSummaryItem[];
  currentAuditId: string | null;
  onSelectAudit: (auditId: string) => void;
  projectName?: string;
}

export const AuditHistorySidebar: React.FC<AuditHistorySidebarProps> = ({
  isOpen,
  onClose,
  audits,
  currentAuditId,
  onSelectAudit,
  projectName,
}) => {
  if (!isOpen) return null;

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs">
      <div className="w-full max-w-md bg-slate-950 border-l border-slate-800 shadow-2xl flex flex-col h-full animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Audit History</h2>
              <p className="text-[11px] text-slate-400">
                {projectName ? `Project: ${projectName}` : 'All persistent audit runs'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Audit List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {audits.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No audit runs found for this view.
            </div>
          ) : (
            audits.map((item) => {
              const isSelected = currentAuditId === item.audit_id;
              return (
                <div
                  key={item.audit_id}
                  onClick={() => {
                    onSelectAudit(item.audit_id);
                    onClose();
                  }}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-500/10 border-indigo-500/40 ring-1 ring-indigo-500/20'
                      : 'bg-slate-900/80 border-slate-800/90 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-xs font-mono font-medium text-slate-200 truncate">
                        {item.target_url.replace(/^https?:\/\//, '')}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {item.baseline_audit_id && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          <GitCompare className="w-2.5 h-2.5" />
                          Retest
                        </span>
                      )}

                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-full ${
                          item.status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-400 border border-red-500/20'
                        }`}
                      >
                        {item.status === 'completed' ? (
                          <CheckCircle2 className="w-2.5 h-2.5" />
                        ) : (
                          <AlertTriangle className="w-2.5 h-2.5" />
                        )}
                        {item.status}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60 mt-2">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{formatDate(item.created_at)}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.critical_count > 0 && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-mono">
                          {item.critical_count} critical
                        </span>
                      )}
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono">
                        {item.total_issues} issues
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
