import React from 'react';
import { Monitor, Smartphone, ChevronRight } from 'lucide-react';
import { Issue } from '../../types/audit';
import { Badge } from '../ui/Badge';

export interface IssueListItemProps {
  issue: Issue;
  isSelected: boolean;
  onSelect: (issueId: string) => void;
}

export const IssueListItem: React.FC<IssueListItemProps> = ({
  issue,
  isSelected,
  onSelect,
}) => {
  const isMobile = issue.viewport?.toLowerCase() === 'mobile';

  return (
    <button
      type="button"
      onClick={() => onSelect(issue.issue_id)}
      className={`w-full text-left p-3.5 rounded-lg border transition-all cursor-pointer flex flex-col gap-2 font-mono select-none ${
        isSelected
          ? 'bg-surface-raised border-accent shadow-subtle ring-1 ring-accent'
          : 'bg-surface border-border hover:border-border-strong hover:bg-surface-raised/40'
      }`}
    >
      {/* Top Header Strip: Severity, ID, Category */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={issue.severity.toLowerCase() as any}>
            {issue.severity.toUpperCase()}
          </Badge>
          <span className="text-xs font-bold text-text-primary bg-background px-2 py-0.5 rounded border border-border font-mono">
            {issue.issue_id}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Badge variant="neutral">{issue.category.toUpperCase()}</Badge>
          <ChevronRight className={`w-4 h-4 transition-transform ${isSelected ? 'text-accent translate-x-0.5' : 'text-text-muted'}`} />
        </div>
      </div>

      {/* Title & Description */}
      <div className="flex flex-col gap-0.5 font-sans">
        <h4 className="text-xs font-semibold text-text-primary flex items-center justify-between gap-2">
          <span className="truncate">{issue.title}</span>
        </h4>
        <p className="text-[11px] text-text-muted line-clamp-2 leading-relaxed">
          {issue.description}
        </p>
      </div>

      {/* Footer Metadata Tag */}
      {issue.viewport && (
        <div className="flex items-center justify-between pt-1 text-[10px] text-text-muted border-t border-border/50 font-mono">
          <span className="flex items-center gap-1">
            {isMobile ? <Smartphone className="w-3 h-3 text-accent" /> : <Monitor className="w-3 h-3 text-accent" />}
            <span className="text-text-secondary">{issue.viewport.toUpperCase()}</span>
          </span>
          {issue.selector && (
            <span className="truncate max-w-[160px] text-text-muted font-mono" title={issue.selector}>
              {issue.selector}
            </span>
          )}
        </div>
      )}
    </button>
  );
};
