import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, Bug } from 'lucide-react';
import { AuditResult, AuditComparison, Project } from '../../types/audit';
import { Card } from '../ui/Card';
import { ComparisonHeader } from './ComparisonHeader';
import { ComparisonSummary, ComparisonTabFilter } from './ComparisonSummary';
import { ComparisonIssueCard } from './ComparisonIssueCard';
import { AuditProgress } from '../audit/AuditProgress';

export interface RetestComparisonWorkspaceProps {
  comparison: AuditComparison;
  baselineAudit?: AuditResult | null;
  retestAudit?: AuditResult | null;
  selectedProject?: Project | null;
  isRetesting?: boolean;
  retestStageIndex?: number;
  onSelectImage?: (imageUrl: string) => void;
  onBackToResults?: () => void;
}

export const RetestComparisonWorkspace: React.FC<RetestComparisonWorkspaceProps> = ({
  comparison,
  baselineAudit = null,
  retestAudit = null,
  selectedProject = null,
  isRetesting = false,
  retestStageIndex = 0,
  onSelectImage,
  onBackToResults,
}) => {
  const [filter, setFilter] = useState<ComparisonTabFilter>('all');

  const fixedIssues = comparison.fixed_issues || [];
  const remainingIssues = comparison.remaining_issues || [];
  const newIssues = comparison.new_issues || [];

  const totalFixed = fixedIssues.length;
  const totalRemaining = remainingIssues.length;
  const totalNew = newIssues.length;

  if (isRetesting) {
    return (
      <div className="flex flex-col gap-6">
        <AuditProgress
          isLoading={true}
          isRetesting={true}
          auditStageIndex={retestStageIndex}
          stages={[
            "1. Preparing audit configuration...",
            "2. Launching Playwright Chromium browser...",
            "3. Navigating target URL & auditing Desktop (1440x900)...",
            "4. Auditing Mobile viewport (390x844)...",
            "5. Collecting screenshots & browser traces...",
            "6. Comparing issues against baseline audit...",
            "7. Finalizing Before/After verification report..."
          ]}
          targetUrl={retestAudit?.target_url || retestAudit?.url || baselineAudit?.target_url || baselineAudit?.url || ''}
          auditMode={retestAudit?.mode || baselineAudit?.mode || 'remote'}
          selectedViewports={['desktop', 'mobile']}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Comparison Header */}
      <ComparisonHeader
        comparison={comparison}
        baselineAudit={baselineAudit}
        retestAudit={retestAudit}
        selectedProject={selectedProject}
        onBackToResults={onBackToResults}
      />

      {/* 2. Comparison Summary Metric Strip */}
      <ComparisonSummary
        comparison={comparison}
        selectedFilter={filter}
        onSelectFilter={(newFilter) => setFilter(newFilter)}
      />

      {/* 3. Comparison Content Sections */}
      <div className="flex flex-col gap-6">
        {/* FIXED ISSUES SECTION */}
        {(filter === 'all' || filter === 'fixed') && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-border font-mono">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-success" />
                <h3 className="text-xs font-bold text-status-success uppercase tracking-wider">
                  FIXED ISSUES ({totalFixed})
                </h3>
              </div>
              <span className="text-[11px] text-text-muted font-sans">
                Existed in baseline; absent & not detected in retest
              </span>
            </div>

            {totalFixed === 0 ? (
              <Card className="p-6 text-center text-xs font-mono text-text-muted border-dashed bg-surface/50">
                No fixed issues detected in this retest run.
              </Card>
            ) : (
              <div className="flex flex-col gap-3">
                {fixedIssues.map((issue) => (
                  <ComparisonIssueCard
                    key={issue.issue_id}
                    issue={issue}
                    categoryType="fixed"
                    baselineAudit={baselineAudit}
                    retestAudit={retestAudit}
                    onSelectImage={onSelectImage}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* REMAINING ISSUES SECTION */}
        {(filter === 'all' || filter === 'remaining') && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-border font-mono">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-status-warning" />
                <h3 className="text-xs font-bold text-status-warning uppercase tracking-wider">
                  REMAINING ISSUES ({totalRemaining})
                </h3>
              </div>
              <span className="text-[11px] text-text-muted font-sans">
                Existed in baseline; still detected on retest
              </span>
            </div>

            {totalRemaining === 0 ? (
              <Card className="p-6 text-center text-xs font-mono text-status-success font-semibold border-dashed border-status-success/30 bg-status-success/5">
                No remaining issues! All baseline issues resolved in retest.
              </Card>
            ) : (
              <div className="flex flex-col gap-3">
                {remainingIssues.map((issue) => (
                  <ComparisonIssueCard
                    key={issue.issue_id}
                    issue={issue}
                    categoryType="remaining"
                    baselineAudit={baselineAudit}
                    retestAudit={retestAudit}
                    onSelectImage={onSelectImage}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* NEW ISSUES SECTION */}
        {(filter === 'all' || filter === 'new') && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-border font-mono">
              <div className="flex items-center gap-2">
                <Bug className="w-4 h-4 text-status-info" />
                <h3 className="text-xs font-bold text-status-info uppercase tracking-wider">
                  NEW ISSUES ({totalNew})
                </h3>
              </div>
              <span className="text-[11px] text-text-muted font-sans">
                Absent in baseline; newly detected in retest run
              </span>
            </div>

            {totalNew === 0 ? (
              <Card className="p-6 text-center text-xs font-mono text-text-muted border-dashed bg-surface/50">
                No new issues introduced in this retest run.
              </Card>
            ) : (
              <div className="flex flex-col gap-3">
                {newIssues.map((issue) => (
                  <ComparisonIssueCard
                    key={issue.issue_id}
                    issue={issue}
                    categoryType="new"
                    baselineAudit={baselineAudit}
                    retestAudit={retestAudit}
                    onSelectImage={onSelectImage}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
