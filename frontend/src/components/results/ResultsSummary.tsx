import React from 'react';
import { AuditSummaryStats, IssueSeverity } from '../../types/audit';
import { Badge } from '../ui/Badge';

export interface ResultsSummaryProps {
  stats: AuditSummaryStats;
  selectedFilter: 'all' | IssueSeverity;
  onSelectFilter: (filter: 'all' | IssueSeverity) => void;
}

export const ResultsSummary: React.FC<ResultsSummaryProps> = ({
  stats,
  selectedFilter,
  onSelectFilter,
}) => {
  const filterItems = [
    { id: 'all', label: 'All Issues', count: stats.total_issues, badgeVariant: 'neutral' },
    { id: 'critical', label: 'Critical', count: stats.critical_count, badgeVariant: 'critical' },
    { id: 'high', label: 'High', count: stats.high_count, badgeVariant: 'high' },
    { id: 'medium', label: 'Medium', count: stats.medium_count, badgeVariant: 'medium' },
    { id: 'low', label: 'Low', count: stats.low_count, badgeVariant: 'low' },
  ] as const;

  return (
    <div className="flex flex-col gap-3 p-4 rounded-lg border border-border bg-surface font-mono">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-text-primary uppercase tracking-wider">Severity Summary</span>
        <span className="text-text-muted text-[11px]">{stats.total_issues} Total Findings Detected</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {filterItems.map((item) => {
          const isSelected = selectedFilter === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectFilter(item.id as any)}
              className={`p-2.5 rounded border text-left flex flex-col gap-1 transition-all cursor-pointer ${
                isSelected
                  ? 'bg-surface-raised border-accent text-text-primary shadow-subtle ring-1 ring-accent'
                  : 'bg-background border-border text-text-muted hover:text-text-primary hover:border-border-strong'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold">{item.label}</span>
                <Badge variant={item.badgeVariant as any}>{item.count}</Badge>
              </div>
              <span className={`text-base font-bold font-mono ${
                item.id === 'critical' && item.count > 0 ? 'text-status-error' :
                item.id === 'high' && item.count > 0 ? 'text-status-warning' :
                item.id === 'medium' && item.count > 0 ? 'text-yellow-400' :
                item.id === 'low' && item.count > 0 ? 'text-status-info' : 'text-text-primary'
              }`}>
                {item.count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
