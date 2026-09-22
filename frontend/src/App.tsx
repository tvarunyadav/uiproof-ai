import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { Card } from './components/ui/Card';
import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { Badge } from './components/ui/Badge';
import { AuditResult, DeveloperFixPrompt, AuditComparison } from './types/audit';
import { createAudit, getFixPrompt, compareAudits } from './services/api';
import {
  Globe,
  Play,
  Monitor,
  Smartphone,
  Tablet,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Layers,
  Sparkles,
  GitCompare,
  Terminal,
  FileCode,
} from 'lucide-react';

export const App: React.FC = () => {
  const [url, setUrl] = useState('');
  const [selectedViewports, setSelectedViewports] = useState<string[]>(['desktop', 'mobile']);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'audit' | 'compare' | 'prompt'>('audit');
  
  // State for real API response data
  const [currentAudit, setCurrentAudit] = useState<AuditResult | null>(null);
  const [baselineAudit, setBaselineAudit] = useState<AuditResult | null>(null);
  const [comparisonResult, setComparisonResult] = useState<AuditComparison | null>(null);
  const [fixPromptData, setFixPromptData] = useState<DeveloperFixPrompt | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const toggleViewport = (vp: string) => {
    if (selectedViewports.includes(vp)) {
      if (selectedViewports.length > 1) {
        setSelectedViewports(selectedViewports.filter((v) => v !== vp));
      }
    } else {
      setSelectedViewports([...selectedViewports, vp]);
    }
  };

  const handleRunAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    let targetUrl = url.trim();
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = `https://${targetUrl}`;
      setUrl(targetUrl);
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      // If an existing audit was already completed, store it as baseline for comparison
      if (currentAudit && currentAudit.status === 'completed') {
        setBaselineAudit(currentAudit);
      }

      const result = await createAudit({
        url: targetUrl,
        viewports: selectedViewports,
      });

      setCurrentAudit(result);

      // Fetch fix prompt interface if issues exist
      const prompt = await getFixPrompt(result.audit_id);
      setFixPromptData(prompt);

      // If we have a baseline, run automatic comparison endpoint
      if (baselineAudit) {
        const comp = await compareAudits(baselineAudit.audit_id, result.audit_id);
        setComparisonResult(comp);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Audit execution failed. Ensure backend API is running.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        {/* URL Entry & Test Config Bar */}
        <Card className="border border-border bg-surface-raised/40 backdrop-blur">
          <form onSubmit={handleRunAudit} className="flex flex-col gap-4">
            <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
              <Sparkles className="w-3.5 h-3.5 text-accent" />
              <span>TEST ENGINE DISPATCHER</span>
            </div>

            <div className="flex flex-col md:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
                  <Globe className="w-4 h-4" />
                </div>
                <Input
                  type="text"
                  placeholder="Enter application URL (e.g. https://myapp.com)"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="pl-9 font-mono text-sm bg-background"
                />
              </div>

              {/* Viewport Selectors */}
              <div className="flex items-center gap-1.5 bg-background border border-border rounded p-1">
                <button
                  type="button"
                  onClick={() => toggleViewport('desktop')}
                  className={`px-2.5 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-colors ${
                    selectedViewports.includes('desktop')
                      ? 'bg-surface-raised text-text-primary border border-border'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  <Monitor className="w-3.5 h-3.5" />
                  Desktop
                </button>
                <button
                  type="button"
                  onClick={() => toggleViewport('mobile')}
                  className={`px-2.5 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-colors ${
                    selectedViewports.includes('mobile')
                      ? 'bg-surface-raised text-text-primary border border-border'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  <Smartphone className="w-3.5 h-3.5" />
                  Mobile
                </button>
                <button
                  type="button"
                  onClick={() => toggleViewport('tablet')}
                  className={`px-2.5 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-colors ${
                    selectedViewports.includes('tablet')
                      ? 'bg-surface-raised text-text-primary border border-border'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  <Tablet className="w-3.5 h-3.5" />
                  Tablet
                </button>
              </div>

              <Button type="submit" isLoading={isLoading} className="w-full md:w-auto font-mono">
                <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
                Run Audit
              </Button>
            </div>
          </form>

          {errorMessage && (
            <div className="mt-4 p-3 rounded bg-status-error/10 border border-status-error/20 text-status-error text-xs font-mono flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </Card>

        {/* Audit Navigation Tabs */}
        {currentAudit && (
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('audit')}
                className={`px-3 py-1.5 rounded text-xs font-mono font-medium flex items-center gap-2 transition-colors ${
                  activeTab === 'audit'
                    ? 'bg-surface-raised text-text-primary border border-border'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                Audit Evidence & Issues
              </button>

              <button
                onClick={() => setActiveTab('prompt')}
                className={`px-3 py-1.5 rounded text-xs font-mono font-medium flex items-center gap-2 transition-colors ${
                  activeTab === 'prompt'
                    ? 'bg-surface-raised text-text-primary border border-border'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                <Code2 className="w-3.5 h-3.5 text-accent" />
                Developer Fix Prompt
              </button>

              {baselineAudit && (
                <button
                  onClick={() => setActiveTab('compare')}
                  className={`px-3 py-1.5 rounded text-xs font-mono font-medium flex items-center gap-2 transition-colors ${
                    activeTab === 'compare'
                      ? 'bg-surface-raised text-text-primary border border-border'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  <GitCompare className="w-3.5 h-3.5 text-status-success" />
                  Before/After Verification
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
              <span>Audit ID:</span>
              <span className="text-text-primary font-semibold">{currentAudit.audit_id.slice(0, 8)}...</span>
            </div>
          </div>
        )}

        {/* Tab Content 1: Main Audit View */}
        {activeTab === 'audit' && currentAudit && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Stats Summary Sidebar */}
            <Card className="flex flex-col gap-4">
              <h3 className="text-xs font-mono text-text-muted uppercase tracking-wider">Audit Summary</h3>
              
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between p-2.5 rounded bg-background border border-border">
                  <span className="text-xs text-text-muted">Total Issues</span>
                  <span className="font-mono text-sm font-bold text-text-primary">{currentAudit.stats.total_issues}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-background border border-border">
                  <span className="text-xs text-text-muted">Critical</span>
                  <Badge variant="critical">{currentAudit.stats.critical_count}</Badge>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-background border border-border">
                  <span className="text-xs text-text-muted">High</span>
                  <Badge variant="high">{currentAudit.stats.high_count}</Badge>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-background border border-border">
                  <span className="text-xs text-text-muted">Medium</span>
                  <Badge variant="medium">{currentAudit.stats.medium_count}</Badge>
                </div>
              </div>

              <div className="border-t border-border pt-3 flex flex-col gap-2">
                <span className="text-xs font-mono text-text-muted">Tested Viewports</span>
                {currentAudit.evidence?.viewports_tested.map((vp, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs font-mono text-text-muted">
                    <span>{vp.name}</span>
                    <span>{vp.width}x{vp.height}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Main Issues List */}
            <div className="md:col-span-3 flex flex-col gap-4">
              {currentAudit.issues.length === 0 ? (
                <Card className="flex flex-col items-center justify-center py-12 text-center border-dashed">
                  <CheckCircle2 className="w-8 h-8 text-status-success mb-3 opacity-80" />
                  <h4 className="text-sm font-medium text-text-primary">No Issues Detected in Baseline Schema</h4>
                  <p className="text-xs text-text-muted max-w-sm mt-1">
                    The deterministic evidence engine collected initial browser traces cleanly.
                  </p>
                </Card>
              ) : (
                currentAudit.issues.map((issue) => (
                  <Card key={issue.issue_id} className="flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={issue.severity as any}>{issue.severity}</Badge>
                        <span className="font-mono text-xs text-text-muted">{issue.issue_id}</span>
                      </div>
                      <Badge variant="neutral">{issue.category}</Badge>
                    </div>

                    <h4 className="text-sm font-semibold text-text-primary">{issue.title}</h4>
                    <p className="text-xs text-text-muted">{issue.description}</p>

                    {issue.selector && (
                      <div className="p-2 rounded bg-background border border-border font-mono text-xs text-text-muted flex items-center gap-2">
                        <Terminal className="w-3.5 h-3.5 text-accent" />
                        <span>Selector:</span>
                        <code className="text-text-primary">{issue.selector}</code>
                      </div>
                    )}
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tab Content 2: Developer Fix Prompt */}
        {activeTab === 'prompt' && fixPromptData && (
          <Card className="flex flex-col gap-4 font-mono">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-accent" />
                <span className="text-sm font-medium">Context-Aware Developer Fix Prompt</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigator.clipboard.writeText(fixPromptData.fix_prompt)}
              >
                Copy Prompt
              </Button>
            </div>

            <pre className="p-4 rounded bg-background border border-border text-xs text-text-secondary overflow-x-auto whitespace-pre-wrap">
              {fixPromptData.fix_prompt}
            </pre>
          </Card>
        )}

        {/* Tab Content 3: Before / After Comparison */}
        {activeTab === 'compare' && comparisonResult && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="flex flex-col gap-3 border-status-success/30 bg-status-success/5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-medium text-status-success">FIXED ISSUES</span>
                <Badge variant="success">{comparisonResult.fixed_issues.length}</Badge>
              </div>
              <p className="text-xs text-text-muted">Resolved between baseline and re-test audit.</p>
            </Card>

            <Card className="flex flex-col gap-3 border-status-warning/30 bg-status-warning/5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-medium text-status-warning">REMAINING ISSUES</span>
                <Badge variant="high">{comparisonResult.remaining_issues.length}</Badge>
              </div>
              <p className="text-xs text-text-muted">Unresolved issues requiring attention.</p>
            </Card>

            <Card className="flex flex-col gap-3 border-status-error/30 bg-status-error/5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-medium text-status-error">NEW ISSUES / REGRESSIONS</span>
                <Badge variant="critical">{comparisonResult.new_issues.length}</Badge>
              </div>
              <p className="text-xs text-text-muted">Newly detected issues introduced post-fix.</p>
            </Card>
          </div>
        )}

        {/* Empty State when no audit has been run */}
        {!currentAudit && (
          <Card className="flex flex-col items-center justify-center py-20 text-center border-dashed">
            <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center text-accent mb-4">
              <Globe className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-text-primary mb-1">
              Ready to Audit Application Quality
            </h3>
            <p className="text-xs text-text-muted max-w-md mb-6">
              Enter a web application URL above to collect objective browser evidence, identify responsive & accessibility bugs, and generate context-aware developer fix prompts.
            </p>
            <div className="flex items-center gap-3 text-xs font-mono text-text-muted">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-accent" />
                Playwright Automation
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-status-success" />
                Stable Issue Hash IDs
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-status-info" />
                Before/After Retests
              </span>
            </div>
          </Card>
        )}
      </main>
    </div>
  );
};

export default App;
