import React from 'react';
import { Globe, Monitor, Play, Sparkles, Folder, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';
import { ViewportSelector } from './ViewportSelector';
import { Project } from '../../types/audit';

export interface NewAuditFormProps {
  url: string;
  onUrlChange: (url: string) => void;
  auditMode: 'remote' | 'local';
  onAuditModeChange: (mode: 'remote' | 'local') => void;
  selectedViewports: string[];
  onToggleViewport: (viewport: string) => void;
  isLoading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  selectedProject?: Project | null;
}

export const NewAuditForm: React.FC<NewAuditFormProps> = ({
  url,
  onUrlChange,
  auditMode,
  onAuditModeChange,
  selectedViewports,
  onToggleViewport,
  isLoading,
  onSubmit,
  selectedProject = null,
}) => {
  return (
    <Card className="border border-border bg-surface-raised/40 backdrop-blur p-5 flex flex-col gap-5">
      {/* Header & Subtitle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded bg-accent/10 border border-accent/30 text-accent">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Configure Browser Audit</h2>
            <p className="text-xs text-text-muted">Run real Playwright multi-viewport automated testing</p>
          </div>
        </div>

        {selectedProject ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface border border-border text-xs font-mono">
            <Folder className="w-3.5 h-3.5 text-accent" />
            <span className="text-text-muted">Project:</span>
            <span className="text-text-primary font-semibold truncate max-w-[140px]">{selectedProject.name}</span>
          </div>
        ) : (
          <span className="text-[11px] font-mono text-text-muted">Global Audit (Unassigned)</span>
        )}
      </div>

      <form onSubmit={onSubmit} className="flex flex-col gap-5">
        {/* Audit Target Mode Selection */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-text-primary uppercase tracking-wider font-mono">
              Audit Target Mode
            </label>
            <span className="text-[10px] font-mono text-text-muted">
              {auditMode === 'local' ? 'Localhost Development Target' : 'Public Deployed Target'}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Remote Mode Option */}
            <button
              type="button"
              disabled={isLoading}
              onClick={() => onAuditModeChange('remote')}
              className={`p-3 rounded border text-left flex items-start gap-3 transition-all cursor-pointer ${
                auditMode === 'remote'
                  ? 'bg-surface-raised border-accent text-text-primary shadow-subtle'
                  : 'bg-background border-border text-text-muted hover:text-text-primary hover:border-border-strong'
              }`}
            >
              <div className={`mt-0.5 w-4 h-4 rounded-full border flex items-center justify-center shrink-0 ${
                auditMode === 'remote' ? 'border-accent bg-accent' : 'border-border-strong'
              }`}>
                {auditMode === 'remote' && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
              </div>
              <div className="flex flex-col gap-1 font-mono flex-1">
                <div className="flex items-center justify-between gap-1 font-semibold text-xs text-text-primary">
                  <div className="flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-accent" />
                    <span>Remote Website</span>
                  </div>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-accent/20 text-accent border border-accent/30 uppercase font-semibold">REMOTE</span>
                </div>
                <span className="text-[11px] text-text-muted font-sans leading-tight">
                  Publicly accessible web application URL.
                </span>
              </div>
            </button>

            {/* Local Mode Option */}
            <button
              type="button"
              disabled={isLoading}
              onClick={() => onAuditModeChange('local')}
              className={`p-3 rounded border text-left flex items-start gap-3 transition-all cursor-pointer ${
                auditMode === 'local'
                  ? 'bg-surface-raised border-status-success text-text-primary shadow-subtle'
                  : 'bg-background border-border text-text-muted hover:text-text-primary hover:border-border-strong'
              }`}
            >
              <div className={`mt-0.5 w-4 h-4 rounded-full border flex items-center justify-center shrink-0 ${
                auditMode === 'local' ? 'border-status-success bg-status-success' : 'border-border-strong'
              }`}>
                {auditMode === 'local' && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
              </div>
              <div className="flex flex-col gap-1 font-mono flex-1">
                <div className="flex items-center justify-between gap-1 font-semibold text-xs text-text-primary">
                  <div className="flex items-center gap-1.5">
                    <Monitor className="w-3.5 h-3.5 text-status-success" />
                    <span>Local Website</span>
                  </div>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-status-success/20 text-status-success border border-status-success/30 uppercase font-semibold">LOCAL</span>
                </div>
                <span className="text-[11px] text-text-muted font-sans leading-tight">
                  Test a locally running application (<code className="text-status-success">localhost</code> / <code className="text-status-success">127.0.0.1</code>).
                </span>
              </div>
            </button>
          </div>

          {/* Mode Guidance Subtext */}
          <div className="text-[11px] text-text-muted font-mono flex items-center gap-1.5 px-1 pt-0.5">
            <AlertCircle className="w-3.5 h-3.5 text-text-muted shrink-0" />
            <span>
              {auditMode === 'local'
                ? 'Local Mode allows testing localhost & 127.0.0.1 targets. 0.0.0.0 and public URLs are disallowed.'
                : 'Remote Mode audits public URLs. Localhost and private IP targets are strictly restricted.'}
            </span>
          </div>
        </div>

        {/* Target URL Input & Viewport Selector Bar */}
        <div className="flex flex-col lg:flex-row items-stretch lg:items-end gap-3">
          {/* Target URL Input */}
          <div className="flex-1 flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-muted flex items-center justify-between">
              <span>Target URL</span>
              <span className="text-[10px] font-mono text-text-muted">Must include http:// or https://</span>
            </label>
            <div className="relative w-full">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
                {auditMode === 'local' ? (
                  <Monitor className="w-4 h-4 text-status-success" />
                ) : (
                  <Globe className="w-4 h-4 text-accent" />
                )}
              </div>
              <Input
                type="text"
                placeholder={auditMode === 'local' ? 'http://localhost:5173' : 'https://example.com'}
                value={url}
                onChange={(e) => onUrlChange(e.target.value)}
                disabled={isLoading}
                className="pl-9 font-mono text-sm bg-background border-border hover:border-border-strong"
              />
            </div>
          </div>

          {/* Viewport Selectors */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-muted">Viewports</label>
            <ViewportSelector
              selectedViewports={selectedViewports}
              onToggleViewport={onToggleViewport}
              disabled={isLoading}
            />
          </div>

          {/* Submit Action */}
          <Button
            type="submit"
            isLoading={isLoading}
            disabled={isLoading || !url.trim()}
            size="md"
            className="font-mono h-[38px] px-6 text-xs font-semibold shrink-0"
          >
            <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
            Run Audit
          </Button>
        </div>
      </form>
    </Card>
  );
};
