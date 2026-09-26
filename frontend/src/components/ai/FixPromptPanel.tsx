import React from 'react';
import { Code2, Copy, CheckCircle2, FileCode } from 'lucide-react';
import { Button } from '../ui/Button';

export interface FixPromptPanelProps {
  fixPrompt: string;
  onCopy: () => void;
  isCopied: boolean;
  suggestedFiles?: string[];
  title?: string;
}

export const FixPromptPanel: React.FC<FixPromptPanelProps> = ({
  fixPrompt,
  onCopy,
  isCopied,
  suggestedFiles = [],
  title = 'DEVELOPER FIX PROMPT',
}) => {
  if (!fixPrompt) return null;

  return (
    <div className="flex flex-col gap-3 pt-4 border-t border-border font-sans">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex flex-col gap-0.5">
          <span className="font-mono font-bold text-xs text-accent uppercase tracking-wider flex items-center gap-1.5">
            <Code2 className="w-4 h-4 text-accent" />
            {title}
          </span>
          <span className="text-[11px] font-mono text-text-muted">
            Ready to paste into Antigravity, Claude, Cursor, Copilot, or coding agent
          </span>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onCopy}
          className="text-xs h-8 px-3 flex items-center gap-1.5 font-mono border-accent/30 hover:bg-accent/10"
        >
          {isCopied ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
              <span className="text-status-success font-semibold">✓ Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-accent" />
              <span>Copy Prompt</span>
            </>
          )}
        </Button>
      </div>

      {/* Suggested files list if present */}
      {suggestedFiles.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap font-mono text-[11px] bg-background p-2 rounded border border-border">
          <span className="text-text-muted flex items-center gap-1">
            <FileCode className="w-3 h-3 text-accent" />
            Suggested files:
          </span>
          {suggestedFiles.map((file, idx) => (
            <code key={idx} className="bg-surface px-1.5 py-0.5 rounded text-accent text-[10px] border border-border">
              {file}
            </code>
          ))}
        </div>
      )}

      {/* Code Prompt Box */}
      <div className="relative group">
        <pre className="p-4 rounded-lg bg-background border border-border text-xs text-text-secondary overflow-x-auto whitespace-pre-wrap leading-relaxed font-mono max-h-[360px] select-all scrollbar-thin">
          {fixPrompt}
        </pre>
      </div>
    </div>
  );
};
