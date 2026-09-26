import React from 'react';
import { GitCompare, Globe, Shield, Calendar, ArrowRight, ArrowLeft } from 'lucide-react';
import { AuditResult, AuditComparison, Project } from '../../types/audit';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export interface ComparisonHeaderProps {
  comparison: AuditComparison;
  baselineAudit?: AuditResult | null;
  retestAudit?: AuditResult | null;
  selectedProject?: Project | null;
  onBackToResults?: () => void;
}

export const ComparisonHeader: React.FC<ComparisonHeaderProps> = ({
  comparison,
  baselineAudit = null,
  retestAudit = null,
  selectedProject = null,
  onBackToResults,
}) => {
  const targetUrl = retestAudit?.target_url || retestAudit?.url || baselineAudit?.target_url || baselineAudit?.url || '';
  const mode = retestAudit?.mode || baselineAudit?.mode || 'remote';
  const baselineId = comparison.baseline_audit_id || baselineAudit?.audit_id || 'Baseline';
  const retestId = comparison.new_audit_id || retestAudit?.audit_id || 'Retest';

  const formatShortId = (id: string) => (id.length > 8 ? `#${id.slice(0, 8)}` : `#${id}`);

  return (
    <div className="flex flex-col gap-4 p-5 rounded-xl border border-border bg-surface font-sans">
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Title & Mode */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10 border border-accent/30 text-accent">
            <GitCompare className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-text-primary tracking-wide font-mono uppercase">
                BEFORE / AFTER VERIFICATION
              </h2>
              <Badge variant={mode === 'local' ? 'warning' : 'neutral'}>
                {mode.toUpperCase()} MODE
              </Badge>
            </div>
            <p className="text-xs text-text-muted mt-0.5">
              Automated re-audit comparison against baseline finding set
            </p>
          </div>
        </div>

        {/* Action button to return to single audit view if needed */}
        {onBackToResults && (
          <Button
            variant="outline"
            size="sm"
            onClick={onBackToResults}
            className="font-mono text-xs flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Audit Results</span>
          </Button>
        )}
      </div>

      {/* Target & Audit references breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-3 border-t border-border font-mono text-xs">
        {/* Target URL & Project */}
        <div className="flex flex-col gap-1 p-2.5 rounded-lg bg-background border border-border">
          <span className="text-[10px] text-text-muted uppercase tracking-wider flex items-center gap-1">
            <Globe className="w-3 h-3 text-accent" />
            Target URL
          </span>
          <span className="font-semibold text-text-primary truncate" title={targetUrl}>
            {targetUrl}
          </span>
          {selectedProject && (
            <span className="text-[10px] text-text-muted flex items-center gap-1 mt-0.5">
              <Shield className="w-3 h-3 text-accent/70" />
              Project: {selectedProject.name}
            </span>
          )}
        </div>

        {/* Baseline Reference */}
        <div className="flex flex-col gap-1 p-2.5 rounded-lg bg-background border border-border">
          <span className="text-[10px] text-text-muted uppercase tracking-wider flex items-center gap-1">
            <Calendar className="w-3 h-3 text-text-muted" />
            Baseline Audit
          </span>
          <span className="font-bold text-text-primary text-xs">
            {formatShortId(baselineId)}
          </span>
          {baselineAudit?.created_at && (
            <span className="text-[10px] text-text-muted">
              {new Date(baselineAudit.created_at).toLocaleString()}
            </span>
          )}
        </div>

        {/* Retest Reference */}
        <div className="flex flex-col gap-1 p-2.5 rounded-lg bg-background border border-border">
          <span className="text-[10px] text-status-success uppercase tracking-wider flex items-center gap-1">
            <ArrowRight className="w-3 h-3 text-status-success" />
            Retest Audit
          </span>
          <span className="font-bold text-status-success text-xs">
            {formatShortId(retestId)}
          </span>
          {retestAudit?.created_at && (
            <span className="text-[10px] text-text-muted">
              {new Date(retestAudit.created_at).toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
