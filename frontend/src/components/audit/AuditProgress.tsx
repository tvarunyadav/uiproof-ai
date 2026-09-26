import React from 'react';
import {
  Loader2,
  CheckCircle2,
  Circle,
  AlertTriangle,
  RefreshCw,
  Monitor,
  Smartphone,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

export interface AuditProgressProps {
  isLoading: boolean;
  auditStageIndex: number;
  stages: string[];
  targetUrl: string;
  auditMode: 'remote' | 'local';
  selectedViewports: string[];
  isRetesting?: boolean;
  retestAuditId?: string;
  errorMessage?: string | null;
}

export const AuditProgress: React.FC<AuditProgressProps> = ({
  isLoading,
  auditStageIndex,
  stages,
  targetUrl,
  auditMode,
  selectedViewports,
  isRetesting = false,
  retestAuditId,
  errorMessage = null,
}) => {
  if (!isLoading && !isRetesting && !errorMessage) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Active Execution Timeline */}
      {isLoading && (
        <Card className="border border-accent/40 bg-surface-raised/80 p-5 flex flex-col gap-4 shadow-glow">
          {/* Progress Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded bg-accent/20 border border-accent/40 text-accent animate-pulse">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-text-primary">Playwright Chromium Browser Run</h3>
                  <Badge variant={auditMode === 'local' ? 'success' : 'info'}>
                    {auditMode === 'local' ? 'LOCAL MODE' : 'REMOTE MODE'}
                  </Badge>
                </div>
                <span className="text-xs font-mono text-text-muted truncate max-w-md" title={targetUrl}>
                  {targetUrl}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="text-text-muted">Progress:</span>
              <span className="px-2 py-0.5 rounded bg-accent/20 text-accent border border-accent/30 font-semibold">
                Stage {auditStageIndex + 1} of {stages.length}
              </span>
            </div>
          </div>

          {/* Viewport Tested Indicators */}
          <div className="flex items-center gap-3 font-mono text-xs text-text-muted bg-background p-2.5 rounded border border-border">
            <span className="text-[11px] font-semibold uppercase text-text-primary">Viewports Enabled:</span>
            <div className="flex items-center gap-2">
              {selectedViewports.includes('desktop') && (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-raised border border-border text-text-primary">
                  <Monitor className="w-3.5 h-3.5 text-accent" />
                  <span>Desktop (1440×900)</span>
                </span>
              )}
              {selectedViewports.includes('mobile') && (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-raised border border-border text-text-primary">
                  <Smartphone className="w-3.5 h-3.5 text-accent" />
                  <span>Mobile (390×844)</span>
                </span>
              )}
            </div>
          </div>

          {/* Horizontal Step Bar */}
          <div className="flex items-center gap-1.5 py-1">
            {stages.map((stg, idx) => {
              const isCompleted = idx < auditStageIndex;
              const isCurrent = idx === auditStageIndex;
              return (
                <div
                  key={idx}
                  className={`h-2 flex-1 rounded-full transition-all duration-300 ${
                    isCompleted
                      ? 'bg-status-success'
                      : isCurrent
                      ? 'bg-accent animate-pulse shadow-glow'
                      : 'bg-surface-hover border border-border/50'
                  }`}
                  title={stg}
                />
              );
            })}
          </div>

          {/* Vertical Detailed Step Checklist */}
          <div className="flex flex-col gap-2 pt-1 font-mono text-xs">
            {stages.map((stageText, idx) => {
              const isCompleted = idx < auditStageIndex;
              const isCurrent = idx === auditStageIndex;

              return (
                <div
                  key={idx}
                  className={`flex items-center justify-between px-3 py-2 rounded transition-all ${
                    isCurrent
                      ? 'bg-accent/10 border border-accent/40 text-text-primary font-semibold'
                      : isCompleted
                      ? 'bg-surface/50 border border-transparent text-text-muted'
                      : 'text-text-muted/50 border border-transparent opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-status-success shrink-0" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 text-accent animate-spin shrink-0" />
                    ) : (
                      <Circle className="w-4 h-4 text-text-muted/40 shrink-0" />
                    )}
                    <span>{stageText}</span>
                  </div>
                  {isCurrent && (
                    <span className="text-[10px] uppercase font-semibold text-accent animate-pulse">
                      In Progress...
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-[10px] text-status-success font-semibold">
                      Complete
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Retesting Status Container */}
      {isRetesting && (
        <Card className="border border-accent/30 bg-accent/5 p-4 flex items-center gap-3 text-xs font-mono animate-pulse">
          <RefreshCw className="w-4 h-4 animate-spin text-accent shrink-0" />
          <div className="flex flex-col gap-0.5">
            <span className="font-semibold text-text-primary">Executing Automated Retest Audit...</span>
            <span className="text-text-muted text-[11px]">
              Re-testing target application against baseline audit run ({retestAuditId ? retestAuditId.slice(0, 8) : 'Baseline'}).
            </span>
          </div>
        </Card>
      )}

      {/* Error Alert Container */}
      {errorMessage && (
        <Card className="border border-status-error/40 bg-status-error/10 p-4 text-status-error text-xs font-mono flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 shrink-0 text-status-error" />
          <div className="flex flex-col gap-0.5 flex-1">
            <span className="font-semibold">Audit Execution Rejection</span>
            <span className="text-status-error/90 font-sans leading-relaxed">{errorMessage}</span>
          </div>
        </Card>
      )}
    </div>
  );
};
