import React from 'react';
import { ExternalLink, RefreshCw, Monitor, Smartphone } from 'lucide-react';
import { AuditResult, Project } from '../../types/audit';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export interface AuditResultsHeaderProps {
  audit: AuditResult;
  selectedProject?: Project | null;
  baselineAuditId?: string | null;
  onRetest?: () => void;
  isRetesting?: boolean;
}

export const AuditResultsHeader: React.FC<AuditResultsHeaderProps> = ({
  audit,
  selectedProject = null,
  baselineAuditId = null,
  onRetest,
  isRetesting = false,
}) => {
  const targetUrl = audit.target_url || audit.url;
  const isLocal = audit.mode === 'local';

  return (
    <div className="p-4 sm:p-5 rounded-lg border border-border bg-surface-raised/40 backdrop-blur flex flex-col gap-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* URL & Context Title */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
            <span className="text-text-muted uppercase tracking-wider font-semibold">Audit Results</span>
            <span className="text-text-muted">•</span>
            <span className="px-1.5 py-0.5 rounded bg-background border border-border text-text-primary">
              ID: {audit.audit_id.slice(0, 8)}
            </span>
            {baselineAuditId && (
              <>
                <span className="text-text-muted">•</span>
                <span className="px-1.5 py-0.5 rounded bg-accent/10 border border-accent/30 text-accent">
                  Baseline: {baselineAuditId.slice(0, 8)}
                </span>
              </>
            )}
            {selectedProject && (
              <>
                <span className="text-text-muted">•</span>
                <span className="text-text-secondary">Project: {selectedProject.name}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href={targetUrl}
              target="_blank"
              rel="noreferrer"
              className="text-base font-semibold text-text-primary hover:text-accent flex items-center gap-1.5 truncate max-w-xl transition-colors font-mono"
            >
              <span className="truncate">{targetUrl}</span>
              <ExternalLink className="w-4 h-4 shrink-0 text-text-muted" />
            </a>
            <Badge variant={isLocal ? 'success' : 'info'}>
              {isLocal ? 'LOCAL' : 'REMOTE'}
            </Badge>
          </div>
        </div>

        {/* Retest Action CTA */}
        {onRetest && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onRetest}
            isLoading={isRetesting}
            disabled={isRetesting}
            className="font-mono self-start md:self-auto shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isRetesting ? 'animate-spin' : ''}`} />
            <span>Re-test Audit</span>
          </Button>
        )}
      </div>

      {/* Audit Environment & Viewport Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border/80 font-mono text-xs text-text-muted">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] text-text-muted">Status:</span>
            <Badge variant={audit.status === 'completed' ? 'success' : audit.status === 'failed' ? 'critical' : 'warning'}>
              {audit.status.toUpperCase()}
            </Badge>
          </div>
          {audit.created_at && (
            <div className="hidden sm:flex items-center gap-1.5">
              <span className="text-[11px] text-text-muted">Executed:</span>
              <span className="text-text-secondary">{new Date(audit.created_at).toLocaleString()}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 text-[11px]">
          <span className="text-text-muted">Tested Viewports:</span>
          {audit.desktop && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-background border border-border text-text-primary">
              <Monitor className="w-3 h-3 text-accent" />
              <span>Desktop (1440×900)</span>
            </span>
          )}
          {audit.mobile && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-background border border-border text-text-primary">
              <Smartphone className="w-3 h-3 text-accent" />
              <span>Mobile (390×844)</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
