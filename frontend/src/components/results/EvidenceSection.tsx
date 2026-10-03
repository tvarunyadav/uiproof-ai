import React, { useState, useEffect } from 'react';
import { Maximize2, Image as ImageIcon, Code } from 'lucide-react';
import { Issue, ViewportAuditResult, AuditResult } from '../../types/audit';
import { fetchArtifactBlob } from '../../services/api';
import { Badge } from '../ui/Badge';

export interface EvidenceSectionProps {
  issue: Issue;
  audit?: AuditResult | null;
  onSelectImage?: (imageUrl: string) => void;
}

export const EvidenceSection: React.FC<EvidenceSectionProps> = ({
  issue,
  audit,
  onSelectImage,
}) => {
  const vpName = (issue.viewport || '').toLowerCase();
  const isMobile = vpName === 'mobile' || issue.issue_id?.toLowerCase().includes('mobile') || (issue.evidence_references?.some(r => r.toLowerCase().includes('mobile')) ?? false);
  const vpResult: ViewportAuditResult | undefined = isMobile ? (audit?.mobile || audit?.desktop) : (audit?.desktop || audit?.mobile);

  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isLoadingBlob, setIsLoadingBlob] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    let activeUrl: string | null = null;

    if (audit && vpResult?.screenshot_artifact_id) {
      setIsLoadingBlob(true);
      fetchArtifactBlob(audit.audit_id, vpResult.screenshot_artifact_id)
        .then((url) => {
          if (isMounted) {
            activeUrl = url;
            setBlobUrl(url);
            setIsLoadingBlob(false);
          } else {
            URL.revokeObjectURL(url);
          }
        })
        .catch(() => {
          if (isMounted) {
            setBlobUrl(null);
            setIsLoadingBlob(false);
          }
        });
    } else {
      setBlobUrl(null);
      setIsLoadingBlob(false);
    }

    return () => {
      isMounted = false;
      if (activeUrl) {
        URL.revokeObjectURL(activeUrl);
      }
    };
  }, [audit?.audit_id, vpResult?.screenshot_artifact_id]);

  return (
    <div className="flex flex-col gap-4 text-xs font-mono">
      {/* Evidence References Pill List */}
      {issue.evidence_references && issue.evidence_references.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] text-text-muted uppercase font-semibold">Empirical Evidence References</span>
          <div className="flex flex-wrap gap-1.5">
            {issue.evidence_references.map((ref, idx) => (
              <Badge key={idx} variant="neutral" className="text-[11px] bg-surface text-text-secondary border-border font-normal py-1 px-2.5 break-all">
                {ref}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Target Element Selector */}
      {issue.selector && (
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] text-text-muted uppercase font-semibold">Target Element Selector</span>
          <div className="p-2.5 rounded bg-surface border border-border text-accent flex items-center gap-2 overflow-x-auto">
            <Code className="w-3.5 h-3.5 shrink-0 text-text-muted" />
            <code className="text-[11px] select-all font-semibold">{issue.selector}</code>
          </div>
        </div>
      )}

      {/* Screenshot Artifact Preview Container */}
      {blobUrl ? (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-text-muted uppercase font-semibold">
              {isMobile ? 'Mobile Viewport Screenshot (390×844)' : 'Desktop Viewport Screenshot (1440×900)'}
            </span>
            <span className="text-[10px] text-text-muted font-mono">{issue.viewport || (isMobile ? 'Mobile' : 'Desktop')}</span>
          </div>
          <div className="relative rounded overflow-hidden border border-border bg-surface-dark p-2 flex items-center justify-center min-h-[220px] max-h-[340px] group">
            <img
              src={blobUrl}
              alt={`${issue.viewport || 'Viewport'} Screenshot Artifact`}
              className="max-h-[320px] w-auto max-w-full object-contain mx-auto rounded shadow-sm transition-transform group-hover:scale-[1.01]"
            />
            {onSelectImage && (
              <button
                type="button"
                onClick={() => onSelectImage(blobUrl)}
                className="absolute inset-0 bg-background/70 backdrop-blur-sm opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 text-xs font-mono text-text-primary transition-opacity cursor-pointer"
              >
                <Maximize2 className="w-4 h-4 text-accent" />
                <span>Open Full Viewport Evidence</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded border border-dashed border-border bg-background text-center text-xs text-text-muted">
          <ImageIcon className="w-4 h-4 inline mr-2" />
          {isLoadingBlob ? 'Loading screenshot evidence...' : 'No screenshot artifact available for this issue.'}
        </div>
      )}
    </div>
  );
};
