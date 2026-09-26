import React from 'react';
import { CheckCircle2, AlertTriangle, Bug } from 'lucide-react';
import { AuditComparison } from '../../types/audit';

export type ComparisonTabFilter = 'fixed' | 'remaining' | 'new' | 'all';

export interface ComparisonSummaryProps {
  comparison: AuditComparison;
  selectedFilter: ComparisonTabFilter;
  onSelectFilter: (filter: ComparisonTabFilter) => void;
}

export const ComparisonSummary: React.FC<ComparisonSummaryProps> = ({
  comparison,
  selectedFilter,
  onSelectFilter,
}) => {
  const fixedCount = comparison.fixed_issues?.length || 0;
  const remainingCount = comparison.remaining_issues?.length || 0;
  const newCount = comparison.new_issues?.length || 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono">
      {/* FIXED Card */}
      <button
        type="button"
        onClick={() => onSelectFilter('fixed')}
        className={`p-4 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-3 ${
          selectedFilter === 'fixed'
            ? 'bg-status-success/15 border-status-success ring-1 ring-status-success'
            : 'bg-surface border-border hover:border-status-success/50'
        }`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-status-success uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-status-success" />
            FIXED ISSUES
          </span>
          <span className="text-lg font-bold text-status-success bg-status-success/10 px-2.5 py-0.5 rounded-md border border-status-success/30">
            {fixedCount}
          </span>
        </div>
        <p className="text-[11px] font-sans text-text-muted leading-snug">
          Existed in baseline; absent & not detected in retest.
        </p>
      </button>

      {/* REMAINING Card */}
      <button
        type="button"
        onClick={() => onSelectFilter('remaining')}
        className={`p-4 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-3 ${
          selectedFilter === 'remaining'
            ? 'bg-status-warning/15 border-status-warning ring-1 ring-status-warning'
            : 'bg-surface border-border hover:border-status-warning/50'
        }`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-status-warning uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-status-warning" />
            REMAINING ISSUES
          </span>
          <span className="text-lg font-bold text-status-warning bg-status-warning/10 px-2.5 py-0.5 rounded-md border border-status-warning/30">
            {remainingCount}
          </span>
        </div>
        <p className="text-[11px] font-sans text-text-muted leading-snug">
          Existed in baseline; still detected on retest.
        </p>
      </button>

      {/* NEW Card */}
      <button
        type="button"
        onClick={() => onSelectFilter('new')}
        className={`p-4 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-3 ${
          selectedFilter === 'new'
            ? 'bg-status-info/15 border-status-info ring-1 ring-status-info'
            : 'bg-surface border-border hover:border-status-info/50'
        }`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-status-info uppercase tracking-wider flex items-center gap-1.5">
            <Bug className="w-4 h-4 text-status-info" />
            NEW ISSUES
          </span>
          <span className="text-lg font-bold text-status-info bg-status-info/10 px-2.5 py-0.5 rounded-md border border-status-info/30">
            {newCount}
          </span>
        </div>
        <p className="text-[11px] font-sans text-text-muted leading-snug">
          Absent in baseline; newly detected in retest run.
        </p>
      </button>
    </div>
  );
};
