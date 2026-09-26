import React from 'react';
import {
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  HelpCircle,
  FileText,
  Target,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Issue, IssueAnalysisResponse } from '../../types/audit';
import { Button } from '../ui/Button';
import { FixPromptPanel } from './FixPromptPanel';

export interface AIAnalysisPanelProps {
  issue: Issue;
  analysisResponse?: IssueAnalysisResponse | null;
  isAnalyzing?: boolean;
  analysisError?: string | null;
  onAnalyze: (issueId: string) => void;
  onCopyPrompt: (issueId: string, promptText: string) => void;
  isCopied?: boolean;
}

export const AIAnalysisPanel: React.FC<AIAnalysisPanelProps> = ({
  issue,
  analysisResponse = null,
  isAnalyzing = false,
  analysisError = null,
  onAnalyze,
  onCopyPrompt,
  isCopied = false,
}) => {
  const analysis = analysisResponse?.analysis;
  const hasAnalysis = Boolean(analysis);

  return (
    <div className="flex flex-col gap-4 p-4 rounded-xl border border-accent/25 bg-surface-raised/40 font-sans mt-4">
      {/* Panel Top Header Bar */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-border/70">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-accent/10 border border-accent/30 text-accent">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-mono font-bold text-xs text-text-primary uppercase tracking-wider flex items-center gap-1.5">
              AI ANALYSIS
            </h4>
            <span className="text-[10px] text-text-muted">Structured engineering diagnosis</span>
          </div>
        </div>

        {/* Grounding Badge */}
        {hasAnalysis && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-background border border-border font-mono text-[11px] text-text-secondary">
            <ShieldCheck className="w-3.5 h-3.5 text-status-success shrink-0" />
            <span>Grounded in verified browser evidence</span>
          </div>
        )}
      </div>

      {/* Unanalyzed Action State */}
      {!hasAnalysis && !isAnalyzing && !analysisError && (
        <div className="flex flex-col items-center justify-center p-6 text-center gap-3 bg-background/50 rounded-lg border border-dashed border-border font-mono">
          <Sparkles className="w-6 h-6 text-accent/70 animate-pulse" />
          <div className="flex flex-col gap-1 max-w-sm">
            <span className="text-xs font-semibold text-text-primary">AI Engineering Analysis Available</span>
            <span className="text-[11px] text-text-muted font-sans leading-relaxed">
              Generate structured root cause hypotheses, investigation hints, and an AI fix prompt grounded in Playwright browser facts.
            </span>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onAnalyze(issue.issue_id)}
            className="font-mono text-xs flex items-center gap-1.5 mt-1"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Analyze with AI</span>
          </Button>
        </div>
      )}

      {/* Loading State */}
      {isAnalyzing && (
        <div className="flex flex-col items-center justify-center p-8 gap-3 bg-accent/5 rounded-lg border border-accent/20 font-mono text-accent">
          <Loader2 className="w-6 h-6 animate-spin text-accent" />
          <div className="flex flex-col items-center gap-1 text-center">
            <span className="text-xs font-bold uppercase tracking-wide text-text-primary">ANALYZING ISSUE</span>
            <span className="text-[11px] text-text-muted font-sans">Reviewing collected browser evidence and diagnostic traces...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {analysisError && !isAnalyzing && (
        <div className="p-4 rounded-lg bg-status-error/10 border border-status-error/20 flex flex-col gap-3 font-mono text-xs text-status-error">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1">
              <span className="font-bold">AI Analysis Failed</span>
              <p className="text-[11px] text-text-secondary font-sans leading-relaxed">{analysisError}</p>
            </div>
          </div>
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onAnalyze(issue.issue_id)}
              className="text-xs h-7 px-3 border-status-error/40 text-status-error hover:bg-status-error/10"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Retry Analysis
            </Button>
          </div>
        </div>
      )}

      {/* Main Analysis Content */}
      {hasAnalysis && analysis && !isAnalyzing && (
        <div className="flex flex-col gap-5 text-xs">
          {/* Summary */}
          {analysis.summary && (
            <div className="flex flex-col gap-1.5">
              <span className="font-mono font-semibold text-accent text-[11px] uppercase tracking-wider flex items-center gap-1">
                <FileText className="w-3.5 h-3.5" />
                Summary
              </span>
              <p className="text-text-primary leading-relaxed bg-background p-3 rounded-lg border border-border">
                {analysis.summary}
              </p>
            </div>
          )}

          {/* Likely Causes (Explicitly labeled as Hypotheses) */}
          {analysis.likely_causes && analysis.likely_causes.length > 0 && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-semibold text-text-secondary text-[11px] uppercase tracking-wider flex items-center gap-1">
                  <HelpCircle className="w-3.5 h-3.5 text-status-warning" />
                  Likely Causes
                </span>
                <span className="text-[10px] font-mono text-text-muted italic">
                  AI-generated hypotheses
                </span>
              </div>
              <ul className="space-y-1.5 pl-1">
                {analysis.likely_causes.map((cause, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-text-primary bg-background/60 p-2 rounded border border-border/60">
                    <span className="text-status-warning font-mono font-bold shrink-0 text-[10px] mt-0.5">•</span>
                    <span className="leading-normal">{cause}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Investigation Hints */}
          {analysis.investigation_hints && analysis.investigation_hints.length > 0 && (
            <div className="flex flex-col gap-2">
              <span className="font-mono font-semibold text-text-secondary text-[11px] uppercase tracking-wider flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-accent" />
                Investigation Hints
              </span>
              <div className="grid grid-cols-1 gap-1.5">
                {analysis.investigation_hints.map((hint, idx) => (
                  <div key={idx} className="flex items-start gap-2 bg-background/80 p-2.5 rounded border border-border font-mono text-[11px] text-text-secondary">
                    <span className="text-accent font-bold"># {idx + 1}</span>
                    <span className="font-sans text-xs text-text-primary leading-normal">{hint}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Expected Result */}
          {analysis.expected_result && (
            <div className="flex flex-col gap-1.5">
              <span className="font-mono font-semibold text-status-success text-[11px] uppercase tracking-wider flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Expected Result
              </span>
              <p className="text-text-primary leading-relaxed bg-background p-3 rounded-lg border border-border font-sans">
                {analysis.expected_result}
              </p>
            </div>
          )}

          {/* Constraints */}
          {analysis.constraints && analysis.constraints.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <span className="font-mono font-semibold text-text-muted text-[11px] uppercase tracking-wider flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                Constraints
              </span>
              <ul className="space-y-1 bg-background p-2.5 rounded-lg border border-border">
                {analysis.constraints.map((constraint, idx) => (
                  <li key={idx} className="text-text-muted font-mono text-[11px] flex items-center gap-2">
                    <span className="text-text-muted/60">—</span>
                    <span>{constraint}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Verification Steps */}
          {analysis.verification_steps && analysis.verification_steps.length > 0 && (
            <div className="flex flex-col gap-2">
              <span className="font-mono font-semibold text-accent text-[11px] uppercase tracking-wider flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-accent" />
                Verification Steps
              </span>
              <ol className="space-y-1.5">
                {analysis.verification_steps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-background/60 p-2 rounded border border-border/60 font-mono text-[11px]">
                    <span className="px-1.5 py-0.5 rounded bg-surface border border-border text-accent font-bold shrink-0 text-[10px]">
                      {idx + 1}
                    </span>
                    <span className="font-sans text-xs text-text-primary leading-normal mt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Re-analyze Action Button */}
          <div className="flex justify-end pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onAnalyze(issue.issue_id)}
              className="font-mono text-xs text-text-muted hover:text-text-primary h-7 px-2.5"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Re-analyze
            </Button>
          </div>

          {/* Developer Fix Prompt Section */}
          {analysis.fix_prompt && (
            <FixPromptPanel
              fixPrompt={analysis.fix_prompt}
              onCopy={() => onCopyPrompt(issue.issue_id, analysis.fix_prompt)}
              isCopied={isCopied}
            />
          )}
        </div>
      )}
    </div>
  );
};
