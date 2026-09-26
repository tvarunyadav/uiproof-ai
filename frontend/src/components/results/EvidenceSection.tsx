import React from 'react';
import { Maximize2, Image as ImageIcon, ShieldAlert, Code } from 'lucide-react';
import { Issue, ViewportAuditResult, AuditResult } from '../../types/audit';
import { getArtifactUrl } from '../../services/api';
import { Badge } from '../ui/Badge';

export interface EvidenceSectionProps {
  issue: Issue;
  audit?: AuditResult | null;
  onSelectImage?: (imageUrl: string) => void;
}

export const EvidenceSection: React.FC<EvidenceSectionProps> = ({
  issue,
  audit = null,
  onSelectImage,
}) => {
  const isMobile = issue.viewport?.toLowerCase() === 'mobile';
  const vpResult: ViewportAuditResult | undefined = isMobile ? audit?.mobile : audit?.desktop;

  const screenshotUrl = vpResult?.screenshot_artifact_id && audit
    ? getArtifactUrl(audit.audit_id, vpResult.screenshot_artifact_id)
    : null;

  const isConsole = issue.category === 'console_error' || issue.category === 'console';
  const isNetwork = issue.category === 'network_failure' || issue.category === 'broken_resource';
  const isResponsive = issue.category === 'responsive' || issue.category === 'layout';

  return (
    <div className="flex flex-col gap-4 font-mono">
      {/* Verified Evidence Header Badge */}
      <div className="flex items-center justify-between pb-2 border-b border-border">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-accent" />
          <span className="text-xs font-bold uppercase tracking-wider text-text-primary">
            Verified Browser Evidence
          </span>
        </div>
        <span className="text-[10px] text-text-muted">Captured directly by Playwright</span>
      </div>

      {/* Selector / Target Element */}
      {issue.selector && (
        <div className="flex flex-col gap-1.5 p-3 rounded bg-background border border-border">
          <span className="text-[10px] text-text-muted uppercase font-semibold flex items-center gap-1.5">
            <Code className="w-3.5 h-3.5 text-accent" />
            Target Element / DOM Selector
          </span>
          <code className="text-xs font-mono text-accent bg-accent/10 p-2 rounded border border-accent/20 break-all">
            {issue.selector}
          </code>
        </div>
      )}

      {/* DOM / Responsive Metrics */}
      {isResponsive && vpResult?.responsive && (
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div className="p-2.5 rounded bg-background border border-border flex flex-col">
            <span className="text-text-muted text-[10px] uppercase font-semibold">Viewport Width</span>
            <span className="font-bold text-text-primary mt-0.5">{vpResult.responsive.viewport_width}px</span>
          </div>
          <div className="p-2.5 rounded bg-background border border-border flex flex-col">
            <span className="text-text-muted text-[10px] uppercase font-semibold">Doc Scroll Width</span>
            <span className="font-bold text-text-primary mt-0.5">{vpResult.responsive.document_scroll_width}px</span>
          </div>
          <div className="p-2.5 rounded bg-background border border-border flex flex-col">
            <span className="text-text-muted text-[10px] uppercase font-semibold">Horizontal Overflow</span>
            <span className={`font-bold mt-0.5 ${vpResult.responsive.horizontal_overflow > 0 ? 'text-status-error' : 'text-status-success'}`}>
              {vpResult.responsive.horizontal_overflow}px
            </span>
          </div>
        </div>
      )}

      {/* Console Log Trace */}
      {isConsole && vpResult?.console_errors && vpResult.console_errors.length > 0 && (
        <div className="p-3 rounded bg-background border border-border flex flex-col gap-2">
          <span className="text-[10px] text-status-error uppercase font-semibold">Browser Console Error Logs</span>
          <div className="flex flex-col gap-1.5">
            {vpResult.console_errors.map((err, idx) => (
              <div key={idx} className="p-2 rounded bg-status-error/5 border border-status-error/20 text-status-error text-[11px] break-all">
                <div className="font-semibold">{err.text}</div>
                {err.location && <div className="text-[10px] text-text-muted mt-1 font-mono">Location: {err.location}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Network Failures Trace */}
      {isNetwork && vpResult?.network_failures && vpResult.network_failures.length > 0 && (
        <div className="p-3 rounded bg-background border border-border flex flex-col gap-2">
          <span className="text-[10px] text-status-error uppercase font-semibold">Network Request Failures</span>
          <div className="flex flex-col gap-1.5">
            {vpResult.network_failures.map((net, idx) => (
              <div key={idx} className="p-2 rounded bg-status-error/5 border border-status-error/20 text-status-error text-[11px] break-all flex flex-col gap-1">
                <div className="flex items-center justify-between font-semibold">
                  <span className="truncate">{net.url}</span>
                  {net.status_code && <Badge variant="critical">HTTP {net.status_code}</Badge>}
                </div>
                <div className="text-[10px] text-text-muted">Method: {net.method} | Error: {net.error_text}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence References List */}
      {issue.evidence_references && issue.evidence_references.length > 0 && (
        <div className="flex flex-col gap-1.5 p-3 rounded bg-background border border-border">
          <span className="text-[10px] text-text-muted uppercase font-semibold">Evidence References</span>
          <div className="flex flex-wrap gap-1.5">
            {issue.evidence_references.map((ref, idx) => (
              <span key={idx} className="px-2 py-1 rounded bg-surface border border-border text-[11px] text-text-secondary font-mono">
                {ref}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Screenshot Artifact Preview */}
      {screenshotUrl ? (
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] text-text-muted uppercase font-semibold">Viewport Screenshot Artifact</span>
          <div className="relative rounded overflow-hidden border border-border bg-background group">
            <img
              src={screenshotUrl}
              alt="Viewport Evidence Screenshot"
              className="w-full h-52 object-cover object-top transition-transform group-hover:scale-105"
            />
            {onSelectImage && (
              <button
                type="button"
                onClick={() => onSelectImage(screenshotUrl)}
                className="absolute inset-0 bg-background/70 backdrop-blur-sm opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 text-xs font-mono text-text-primary transition-opacity cursor-pointer"
              >
                <Maximize2 className="w-4 h-4 text-accent" />
                <span>Inspect Full Screenshot Lightbox</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded border border-dashed border-border bg-background text-center text-xs text-text-muted">
          <ImageIcon className="w-4 h-4 inline mr-2" />
          No screenshot artifact available for this issue.
        </div>
      )}
    </div>
  );
};
