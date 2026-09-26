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
    <div className="fixed inset-0 z-50 flex justify-end bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-surface border-l border-border shadow-2xl flex flex-col h-full animate-in slide-in-from-right duration-200 font-sans">
        {/* Header */}
        <div className="px-5 py-4 border-b border-border flex items-center justify-between bg-surface-raised/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">Audit History</h2>
              <p className="text-[11px] text-text-muted">
                {projectName ? `Project: ${projectName}` : 'All persistent audit runs'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary p-1 rounded-lg hover:bg-surface-raised transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Audit List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
          {audits.length === 0 ? (
            <div className="text-center py-12 text-text-muted text-xs">
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
                      ? 'bg-accent/10 border-accent/40 ring-1 ring-accent/20'
                      : 'bg-surface-raised/80 border-border hover:border-border-strong hover:bg-surface-raised'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-xs font-mono font-medium text-text-primary truncate">
                        {item.target_url.replace(/^https?:\/\//, '')}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {item.baseline_audit_id && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium rounded bg-accent/10 text-accent border border-accent/20">
                          <GitCompare className="w-2.5 h-2.5" />
                          Retest
                        </span>
                      )}

                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-full ${
                          item.status === 'completed'
                            ? 'bg-status-success/10 text-status-success border border-status-success/20'
                            : 'bg-status-error/10 text-status-error border border-status-error/20'
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

                  <div className="flex items-center justify-between text-[11px] text-text-muted pt-1 border-t border-border/60 mt-2">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-text-muted" />
                      <span>{formatDate(item.created_at)}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.critical_count > 0 && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-status-error/10 text-status-error border border-status-error/20 font-mono">
                          {item.critical_count} critical
                        </span>
                      )}
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-background text-text-secondary font-mono border border-border">
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
