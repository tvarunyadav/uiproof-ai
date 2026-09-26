import React, { useState } from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { AuditResult, Issue, IssueSeverity, Project } from '../../types/audit';
import { Card } from '../ui/Card';
import { AuditResultsHeader } from './AuditResultsHeader';
import { ResultsSummary } from './ResultsSummary';
import { IssueListItem } from './IssueListItem';
import { IssueDetailPanel } from './IssueDetailPanel';

export interface AuditResultsWorkspaceProps {
  audit: AuditResult;
  selectedProject?: Project | null;
  baselineAuditId?: string | null;
  onRetest?: () => void;
  isRetesting?: boolean;
  onSelectImage?: (imageUrl: string) => void;
  renderAIAndPromptSection?: (issue: Issue) => React.ReactNode;
}

export const AuditResultsWorkspace: React.FC<AuditResultsWorkspaceProps> = ({
  audit,
  selectedProject = null,
  baselineAuditId = null,
  onRetest,
  isRetesting = false,
  onSelectImage,
  renderAIAndPromptSection,
}) => {
  const [severityFilter, setSeverityFilter] = useState<'all' | IssueSeverity>('all');
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);

  const allIssues = audit.issues?.length > 0 ? audit.issues : (audit.findings || []);

  const filteredIssues = severityFilter === 'all'
    ? allIssues
    : allIssues.filter((i) => i.severity.toLowerCase() === severityFilter.toLowerCase());

  // Default select first issue if available
  const activeIssue = filteredIssues.find((i) => i.issue_id === selectedIssueId)
    || (filteredIssues.length > 0 ? filteredIssues[0] : null);

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Results Header */}
      <AuditResultsHeader
        audit={audit}
        selectedProject={selectedProject}
        baselineAuditId={baselineAuditId}
        onRetest={onRetest}
        isRetesting={isRetesting}
      />

      {/* 2. Severity Summary Bar */}
      <ResultsSummary
        stats={audit.stats}
        selectedFilter={severityFilter}
        onSelectFilter={(filter) => {
          setSeverityFilter(filter);
          setSelectedIssueId(null);
        }}
      />

      {/* 3. Main Workspace: 2-Column Split (List on Left, Detail on Right) */}
      {allIssues.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-12 px-6 text-center border-dashed border-status-success/40 bg-status-success/5 font-mono">
          <CheckCircle2 className="w-10 h-10 text-status-success mb-3 opacity-90" />
          <h4 className="text-base font-semibold text-text-primary">No Issues Detected</h4>
          <p className="text-xs text-text-muted max-w-lg mt-1 font-sans leading-relaxed">
            Playwright inspected the target application cleanly across all enabled viewports. Zero missing metadata, broken resources, console errors, network failures, or horizontal layout overflows were detected.
          </p>
        </Card>
      ) : filteredIssues.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-10 px-6 text-center border-dashed border-border bg-surface font-mono">
          <AlertCircle className="w-8 h-8 text-text-muted mb-2" />
          <h4 className="text-sm font-medium text-text-primary">No issues match filter "{severityFilter}"</h4>
          <button
            type="button"
            onClick={() => setSeverityFilter('all')}
            className="mt-3 text-xs font-mono text-accent underline hover:text-accent/80 cursor-pointer"
          >
            Clear Filter
          </button>
        </Card>
      ) : (
        <div className="flex flex-col lg:flex-row items-start gap-6">
          {/* Left Column: Issue List (40% width on Desktop) */}
          <div className="w-full lg:w-[40%] flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted px-1">
              <span>FOUND ISSUES ({filteredIssues.length})</span>
              <span>Click issue to view evidence</span>
            </div>

            <div className="flex flex-col gap-2.5 max-h-[750px] overflow-y-auto pr-1">
              {filteredIssues.map((issue) => (
                <IssueListItem
                  key={issue.issue_id}
                  issue={issue}
                  isSelected={activeIssue?.issue_id === issue.issue_id}
                  onSelect={(id) => setSelectedIssueId(id)}
                />
              ))}
            </div>
          </div>

          {/* Right Column: Selected Issue Detail & Evidence (60% width on Desktop) */}
          <div className="w-full lg:w-[60%] flex flex-col gap-4 sticky top-20">
            <IssueDetailPanel
              issue={activeIssue}
              audit={audit}
              onSelectImage={onSelectImage}
              onRetest={onRetest}
              isRetesting={isRetesting}
              renderAIAndPromptSection={renderAIAndPromptSection}
            />
          </div>
        </div>
      )}
    </div>
  );
};
