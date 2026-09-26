import React from 'react';
import { Monitor, Smartphone, AlertCircle, RefreshCw } from 'lucide-react';
import { Issue, AuditResult } from '../../types/audit';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { EvidenceSection } from './EvidenceSection';

export interface IssueDetailPanelProps {
  issue: Issue | null;
  audit?: AuditResult | null;
  onSelectImage?: (imageUrl: string) => void;
  onRetest?: () => void;
  isRetesting?: boolean;
  renderAIAndPromptSection?: (issue: Issue) => React.ReactNode;
}

export const IssueDetailPanel: React.FC<IssueDetailPanelProps> = ({
  issue,
  audit = null,
  onSelectImage,
  onRetest,
  isRetesting = false,
  renderAIAndPromptSection,
}) => {
  if (!issue) {
    return (
      <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed border-border bg-surface text-text-muted font-mono">
        <AlertCircle className="w-8 h-8 mb-2 text-text-muted/60" />
        <span className="text-xs font-semibold text-text-primary">No Issue Selected</span>
        <span className="text-[11px] text-text-muted mt-1 max-w-xs">
          Select an issue from the list on the left to inspect browser evidence and details.
        </span>
      </Card>
    );
  }

  const isMobile = issue.viewport?.toLowerCase() === 'mobile';

  return (
    <Card className="p-5 flex flex-col gap-5 border-border bg-surface font-sans">
      {/* Issue Detail Header */}
      <div className="flex flex-col gap-3 pb-4 border-b border-border">
        <div className="flex items-center justify-between gap-3 flex-wrap font-mono">
          <div className="flex items-center gap-2">
            <Badge variant={issue.severity.toLowerCase() as any}>
              {issue.severity.toUpperCase()}
            </Badge>
            <span className="text-sm font-bold text-text-primary bg-background px-2.5 py-1 rounded border border-border">
              {issue.issue_id}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="neutral">{issue.category.toUpperCase()}</Badge>
            {issue.viewport && (
              <span className="px-2.5 py-0.5 rounded bg-background border border-border text-xs font-mono text-accent flex items-center gap-1.5 font-semibold">
                {isMobile ? <Smartphone className="w-3.5 h-3.5" /> : <Monitor className="w-3.5 h-3.5" />}
                {issue.viewport.toUpperCase()}
              </span>
            )}
          </div>
        </div>

        {/* Title & Description */}
        <div className="flex flex-col gap-1 mt-1">
          <h3 className="text-base font-semibold text-text-primary leading-snug">
            {issue.title}
          </h3>
          <p className="text-xs text-text-secondary leading-relaxed font-normal">
            {issue.description}
          </p>
        </div>
      </div>

      {/* Verified Browser Evidence Section */}
      <EvidenceSection
        issue={issue}
        audit={audit}
        onSelectImage={onSelectImage}
      />

      {/* AI Analysis & Developer Fix Prompt Section */}
      {renderAIAndPromptSection && renderAIAndPromptSection(issue)}

      {/* Retest Action Footer */}
      {onRetest && (
        <div className="pt-4 border-t border-border flex items-center justify-between gap-3 font-mono text-xs">
          <span className="text-text-muted text-[11px]">
            Made code changes? Re-verify this issue with an automated retest run.
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={onRetest}
            isLoading={isRetesting}
            disabled={isRetesting}
            className="shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isRetesting ? 'animate-spin' : ''}`} />
            <span>Re-test Audit</span>
          </Button>
        </div>
      )}
    </Card>
  );
};
