import React, { useState } from 'react';
import {
  CheckCircle2,
  Monitor,
  Smartphone,
  ChevronDown,
  ChevronRight,
  Maximize2,
  FileCode,
} from 'lucide-react';
import { Issue, AuditResult } from '../../types/audit';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { getArtifactUrl } from '../../services/api';

export type ComparisonCategoryType = 'fixed' | 'remaining' | 'new';

export interface ComparisonIssueCardProps {
  issue: Issue;
  categoryType: ComparisonCategoryType;
  baselineAudit?: AuditResult | null;
  retestAudit?: AuditResult | null;
  onSelectImage?: (imageUrl: string) => void;
}

export const ComparisonIssueCard: React.FC<ComparisonIssueCardProps> = ({
  issue,
  categoryType,
  baselineAudit = null,
  retestAudit = null,
  onSelectImage,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const isMobile = issue.viewport?.toLowerCase() === 'mobile';
  const vpName = issue.viewport?.toLowerCase();

  const baselineVpData = vpName === 'mobile' ? baselineAudit?.mobile : (vpName === 'desktop' ? baselineAudit?.desktop : null);
  const retestVpData = vpName === 'mobile' ? retestAudit?.mobile : (vpName === 'desktop' ? retestAudit?.desktop : null);

  const baselineScreenshotPath = baselineVpData?.screenshot_url || baselineVpData?.screenshot_artifact_id;
  const retestScreenshotPath = retestVpData?.screenshot_url || retestVpData?.screenshot_artifact_id;

  const baselineScreenshotUrl = baselineAudit && baselineScreenshotPath
    ? getArtifactUrl(baselineAudit.audit_id, baselineScreenshotPath)
    : '';

  const retestScreenshotUrl = retestAudit && retestScreenshotPath
    ? getArtifactUrl(retestAudit.audit_id, retestScreenshotPath)
    : '';

  const getCategoryBadge = () => {
    switch (categoryType) {
      case 'fixed':
        return <Badge variant="success">FIXED</Badge>;
      case 'remaining':
        return <Badge variant="high">STILL DETECTED</Badge>;
      case 'new':
        return <Badge variant="neutral">NEW ISSUE</Badge>;
    }
  };

  const getBorderColor = () => {
    switch (categoryType) {
      case 'fixed':
        return 'border-status-success/30 bg-status-success/5';
      case 'remaining':
        return 'border-status-warning/30 bg-status-warning/5';
      case 'new':
        return 'border-status-info/30 bg-status-info/5';
    }
  };

  return (
    <Card className={`flex flex-col gap-4 font-sans ${getBorderColor()}`}>
      {/* Issue Card Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap font-mono">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded hover:bg-background text-text-muted hover:text-text-primary transition-colors cursor-pointer"
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>

          {getCategoryBadge()}

          <Badge variant={issue.severity.toLowerCase() as any}>
            {issue.severity.toUpperCase()}
          </Badge>

          <span className="text-xs font-bold text-text-primary bg-background px-2.5 py-1 rounded border border-border">
            {issue.issue_id}
          </span>

          <Badge variant="neutral">{issue.category.toUpperCase()}</Badge>

          {issue.viewport && (
            <span className="px-2 py-0.5 rounded bg-background border border-border text-xs text-accent flex items-center gap-1 font-semibold">
              {isMobile ? <Smartphone className="w-3.5 h-3.5" /> : <Monitor className="w-3.5 h-3.5" />}
              {issue.viewport.toUpperCase()}
            </span>
          )}
        </div>

        {/* Status text pill */}
        <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-background border border-border">
          {categoryType === 'fixed' && <span className="text-status-success">Not detected in retest</span>}
          {categoryType === 'remaining' && <span className="text-status-warning">Still detected on retest</span>}
          {categoryType === 'new' && <span className="text-status-info">Detected in retest; not present in baseline</span>}
        </span>
      </div>

      {/* Title & Description */}
      <div className="flex flex-col gap-1">
        <h4 className="text-sm font-semibold text-text-primary leading-snug">{issue.title}</h4>
        <p className="text-xs text-text-secondary leading-relaxed">{issue.description}</p>
      </div>

      {/* Expanded Before / After Comparison Detail */}
      {isExpanded && (
        <div className="pt-3 border-t border-border/80 flex flex-col gap-4 font-mono text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* BEFORE COLUMN */}
            <div className="flex flex-col gap-2 p-3 rounded-lg bg-background border border-border">
              <div className="flex items-center justify-between pb-2 border-b border-border">
                <span className="font-bold text-text-secondary uppercase text-[11px] tracking-wider">
                  BEFORE (BASELINE)
                </span>
                <span className="text-[10px] text-text-muted">
                  {categoryType === 'new' ? 'Absent in baseline' : 'Baseline evidence'}
                </span>
              </div>

              {categoryType === 'new' ? (
                <div className="py-6 text-center text-text-muted text-xs font-sans italic flex flex-col items-center gap-1">
                  <CheckCircle2 className="w-5 h-5 text-status-success/70" />
                  <span>Not present in baseline audit.</span>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {issue.selector && (
                    <div className="flex items-center gap-1.5 text-[11px]">
                      <FileCode className="w-3 h-3 text-accent shrink-0" />
                      <code className="bg-surface px-1.5 py-0.5 rounded text-accent truncate border border-border">
                        {issue.selector}
                      </code>
                    </div>
                  )}

                  {/* Baseline screenshot artifact */}
                  {baselineScreenshotUrl && onSelectImage && (
                    <div className="relative group rounded border border-border overflow-hidden bg-surface-raised mt-1">
                      <img
                        src={baselineScreenshotUrl}
                        alt="Baseline Screenshot"
                        className="w-full h-32 object-cover object-top opacity-90 group-hover:opacity-100 transition-opacity"
                      />
                      <button
                        type="button"
                        onClick={() => onSelectImage(baselineScreenshotUrl)}
                        className="absolute bottom-2 right-2 p-1.5 rounded bg-background/80 hover:bg-background text-text-primary border border-border text-[10px] flex items-center gap-1 backdrop-blur-sm cursor-pointer"
                      >
                        <Maximize2 className="w-3 h-3" />
                        <span>Baseline Screenshot</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* AFTER COLUMN */}
            <div className="flex flex-col gap-2 p-3 rounded-lg bg-background border border-border">
              <div className="flex items-center justify-between pb-2 border-b border-border">
                <span className="font-bold uppercase text-[11px] tracking-wider text-text-primary">
                  AFTER (RETEST)
                </span>
                <span className="text-[10px]">
                  {categoryType === 'fixed' ? (
                    <span className="text-status-success font-semibold">Resolved</span>
                  ) : (
                    <span className="text-status-warning font-semibold">Detected</span>
                  )}
                </span>
              </div>

              {categoryType === 'fixed' ? (
                <div className="py-6 text-center text-status-success text-xs font-sans font-semibold flex flex-col items-center gap-1">
                  <CheckCircle2 className="w-6 h-6 text-status-success" />
                  <span>Issue absent & not detected in retest.</span>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {issue.selector && (
                    <div className="flex items-center gap-1.5 text-[11px]">
                      <FileCode className="w-3 h-3 text-accent shrink-0" />
                      <code className="bg-surface px-1.5 py-0.5 rounded text-accent truncate border border-border">
                        {issue.selector}
                      </code>
                    </div>
                  )}

                  {/* Retest screenshot artifact */}
                  {retestScreenshotUrl && onSelectImage && (
                    <div className="relative group rounded border border-border overflow-hidden bg-surface-raised mt-1">
                      <img
                        src={retestScreenshotUrl}
                        alt="Retest Screenshot"
                        className="w-full h-32 object-cover object-top opacity-90 group-hover:opacity-100 transition-opacity"
                      />
                      <button
                        type="button"
                        onClick={() => onSelectImage(retestScreenshotUrl)}
                        className="absolute bottom-2 right-2 p-1.5 rounded bg-background/80 hover:bg-background text-text-primary border border-border text-[10px] flex items-center gap-1 backdrop-blur-sm cursor-pointer"
                      >
                        <Maximize2 className="w-3 h-3" />
                        <span>Retest Screenshot</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
