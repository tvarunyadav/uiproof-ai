import React, { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Card } from './components/ui/Card';
import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { Badge } from './components/ui/Badge';
import {
  AuditResult,
  DeveloperFixPrompt,
  AuditComparison,
  ViewportAuditResult,
  Issue,
  IssueSeverity,
  IssueAnalysisResponse,
  Project,
  AuditSummaryItem,
} from './types/audit';
import { User } from './types/auth';
import {
  createAudit,
  getFixPrompt,
  compareAudits,
  getArtifactUrl,
  analyzeIssue,
  retestAudit,
  listProjects,
  listProjectAudits,
  listAudits,
  getAudit,
  getMeProfile,
  logoutUser,
  ApiError,
} from './services/api';
import { CreateProjectModal } from './components/CreateProjectModal';
import { AuditHistorySidebar } from './components/AuditHistorySidebar';
import { AuthContainer } from './components/auth/AuthContainer';
import {
  Globe,
  Play,
  Monitor,
  Smartphone,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Layers,
  Sparkles,
  GitCompare,
  FileCode,
  Image as ImageIcon,
  ExternalLink,
  Loader2,
  Bug,
  Maximize2,
  ChevronDown,
  ChevronRight,
  Filter,
  FileText,
  AlertCircle,
  Copy,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

export const App: React.FC = () => {
  // Milestone 7F: Auth & User Session State
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authStatus, setAuthStatus] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading');
  const [authError, setAuthError] = useState<string | null>(null);

  const [url, setUrl] = useState('');
  const [selectedViewports, setSelectedViewports] = useState<string[]>(['desktop', 'mobile']);
  const [isLoading, setIsLoading] = useState(false);
  const [isRetesting, setIsRetesting] = useState(false);
  const [activeTab, setActiveTab] = useState<'audit' | 'compare' | 'prompt'>('audit');
  const [compareCategoryTab, setCompareCategoryTab] = useState<'fixed' | 'remaining' | 'new'>('remaining');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<'all' | IssueSeverity>('all');
  const [expandedIssueIds, setExpandedIssueIds] = useState<Record<string, boolean>>({});

  // State for real API response data
  const [currentAudit, setCurrentAudit] = useState<AuditResult | null>(null);
  const [baselineAudit, setBaselineAudit] = useState<AuditResult | null>(null);
  const [comparisonResult, setComparisonResult] = useState<AuditComparison | null>(null);
  const [fixPromptData, setFixPromptData] = useState<DeveloperFixPrompt | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Milestone 5B: Issue AI Analysis State
  const [analyzingIssueId, setAnalyzingIssueId] = useState<string | null>(null);
  const [issueAnalyses, setIssueAnalyses] = useState<Record<string, IssueAnalysisResponse>>({});
  const [issueAnalysisErrors, setIssueAnalysisErrors] = useState<Record<string, string>>({});
  const [copiedPromptIssueId, setCopiedPromptIssueId] = useState<string | null>(null);

  // Milestone 6E: Project & History State
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [historyAudits, setHistoryAudits] = useState<AuditSummaryItem[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);

  // Session restoration on initial mount
  useEffect(() => {
    const token = localStorage.getItem('uiproof_token');
    if (!token) {
      setAuthStatus('unauthenticated');
      return;
    }

    getMeProfile()
      .then((user) => {
        setCurrentUser(user);
        setAuthStatus('authenticated');
      })
      .catch((err) => {
        localStorage.removeItem('uiproof_token');
        setCurrentUser(null);
        setAuthStatus('unauthenticated');
        if (err instanceof ApiError && err.status === 401) {
          setAuthError('Your session has expired. Please log in again.');
        }
      });
  }, []);

  // Load projects & history when authenticated or selectedProject changes
  useEffect(() => {
    if (authStatus === 'authenticated') {
      loadProjects();
      if (selectedProject) {
        loadHistory(selectedProject.project_id);
        if (!url.trim() && selectedProject.target_url) {
          setUrl(selectedProject.target_url);
        }
      } else {
        loadHistory();
      }
    }
  }, [authStatus, selectedProject]);

  const handleSessionExpired = (msg = 'Your session has expired. Please log in again.') => {
    localStorage.removeItem('uiproof_token');
    setCurrentUser(null);
    setProjects([]);
    setSelectedProject(null);
    setHistoryAudits([]);
    setCurrentAudit(null);
    setBaselineAudit(null);
    setComparisonResult(null);
    setFixPromptData(null);
    setIssueAnalyses({});
    setIssueAnalysisErrors({});
    setErrorMessage(null);
    setUrl('');
    setAuthError(msg);
    setAuthStatus('unauthenticated');
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      // Ignore network errors on logout
    }
    localStorage.removeItem('uiproof_token');
    setCurrentUser(null);
    setProjects([]);
    setSelectedProject(null);
    setHistoryAudits([]);
    setCurrentAudit(null);
    setBaselineAudit(null);
    setComparisonResult(null);
    setFixPromptData(null);
    setIssueAnalyses({});
    setIssueAnalysisErrors({});
    setErrorMessage(null);
    setUrl('');
    setAuthError(null);
    setAuthStatus('unauthenticated');
  };

  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    setAuthError(null);
    setAuthStatus('authenticated');
  };

  const loadProjects = async () => {
    try {
      const projs = await listProjects();
      setProjects(projs);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired();
        return;
      }
      console.warn('Could not load projects:', err);
    }
  };

  const loadHistory = async (projectId?: string) => {
    try {
      const items = projectId ? await listProjectAudits(projectId) : await listAudits();
      setHistoryAudits(items);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired();
        return;
      }
      console.warn('Could not load audit history:', err);
    }
  };

  const handleProjectCreated = (newProject: Project) => {
    setProjects((prev) => [newProject, ...prev]);
    setSelectedProject(newProject);
    setUrl(newProject.target_url);
    loadHistory(newProject.project_id);
  };

  const handleSelectHistoricalAudit = async (auditId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const audit = await getAudit(auditId);
      setCurrentAudit(audit);
      setActiveTab('audit');
      setSeverityFilter('all');

      const initialExpanded: Record<string, boolean> = {};
      const allIssues = audit.issues?.length > 0 ? audit.issues : (audit.findings || []);
      allIssues.forEach((issue) => {
        initialExpanded[issue.issue_id] = true;
      });
      setExpandedIssueIds(initialExpanded);

      try {
        const prompt = await getFixPrompt(audit.audit_id);
        setFixPromptData(prompt);
      } catch {
        setFixPromptData(null);
      }
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired();
        return;
      }
      setErrorMessage(err.message || 'Failed to load historical audit.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleViewport = (vp: string) => {
    if (selectedViewports.includes(vp)) {
      if (selectedViewports.length > 1) {
        setSelectedViewports(selectedViewports.filter((v) => v !== vp));
      }
    } else {
      setSelectedViewports([...selectedViewports, vp]);
    }
  };

  const toggleIssueExpansion = (issueId: string) => {
    setExpandedIssueIds((prev) => ({
      ...prev,
      [issueId]: !prev[issueId],
    }));
  };

  const handleRetestApplication = async () => {
    if (!currentAudit || isRetesting || isLoading) return;
    setIsRetesting(true);
    setErrorMessage(null);

    try {
      const res = await retestAudit(currentAudit.audit_id);
      setBaselineAudit(currentAudit);
      setCurrentAudit(res.retest_audit);
      setComparisonResult(res.comparison);
      setActiveTab('compare');

      if (res.comparison.fixed_issues.length > 0) {
        setCompareCategoryTab('fixed');
      } else if (res.comparison.remaining_issues.length > 0) {
        setCompareCategoryTab('remaining');
      } else {
        setCompareCategoryTab('new');
      }

      // Auto-expand issue details for retest audit
      const initialExpanded: Record<string, boolean> = {};
      const allIssues = res.retest_audit.issues?.length > 0 ? res.retest_audit.issues : (res.retest_audit.findings || []);
      allIssues.forEach((issue) => {
        initialExpanded[issue.issue_id] = true;
      });
      setExpandedIssueIds(initialExpanded);

      // Refresh history & project list
      loadHistory(selectedProject?.project_id);
      loadProjects();
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired();
        return;
      }
      setErrorMessage(err.message || 'Retest failed. Ensure backend API is running.');
    } finally {
      setIsRetesting(false);
    }
  };

  const handleAnalyzeIssue = async (issueId: string) => {
    if (!currentAudit) return;
    setAnalyzingIssueId(issueId);
    setIssueAnalysisErrors((prev) => {
      const next = { ...prev };
      delete next[issueId];
      return next;
    });

    try {
      const res = await analyzeIssue(currentAudit.audit_id, issueId);
      setIssueAnalyses((prev) => ({
        ...prev,
        [issueId]: res,
      }));
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired();
        return;
      }
      setIssueAnalysisErrors((prev) => ({
        ...prev,
        [issueId]: err.message || 'Failed to analyze issue.',
      }));
    } finally {
      setAnalyzingIssueId(null);
    }
  };

  const handleCopyPrompt = (issueId: string, promptText: string) => {
    navigator.clipboard.writeText(promptText);
    setCopiedPromptIssueId(issueId);
    setTimeout(() => {
      setCopiedPromptIssueId((prev) => (prev === issueId ? null : prev));
    }, 2000);
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
      if (currentAudit && currentAudit.status === 'completed') {
        setBaselineAudit(currentAudit);
      }

      const result = await createAudit({
        url: targetUrl,
        viewports: selectedViewports,
        project_id: selectedProject?.project_id,
      });

      setCurrentAudit(result);
      setSeverityFilter('all');
      
      // Auto-expand all issues by default for immediate visibility
      const initialExpanded: Record<string, boolean> = {};
      const allIssues = result.issues?.length > 0 ? result.issues : (result.findings || []);
      allIssues.forEach((issue) => {
        initialExpanded[issue.issue_id] = true;
      });
      setExpandedIssueIds(initialExpanded);

      try {
        const prompt = await getFixPrompt(result.audit_id);
        setFixPromptData(prompt);
      } catch (promptErr) {
        console.warn('Fix prompt not generated yet:', promptErr);
      }

      if (baselineAudit) {
        try {
          const comp = await compareAudits(baselineAudit.audit_id, result.audit_id);
          setComparisonResult(comp);
        } catch (compErr) {
          console.warn('Comparison failed:', compErr);
        }
      }

      // Refresh history & project list
      loadHistory(selectedProject?.project_id);
      loadProjects();
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired();
        return;
      }
      setErrorMessage(err.message || 'Audit execution failed. Ensure backend API is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderViewportEvidenceCard = (vpName: string, icon: React.ReactNode, vpResult?: ViewportAuditResult) => {
    if (!vpResult) return null;

    const screenshotUrl = vpResult.screenshot_artifact_id && currentAudit
      ? getArtifactUrl(currentAudit.audit_id, vpResult.screenshot_artifact_id)
      : null;

    const hasOverflow = vpResult.responsive && vpResult.responsive.horizontal_overflow > 0;

    return (
      <Card className="flex flex-col gap-4 border-border bg-surface-raised/30">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded bg-background border border-border text-accent">
              {icon}
            </span>
            <div>
              <h4 className="text-sm font-semibold text-text-primary">{vpName} Viewport</h4>
              <p className="text-xs font-mono text-text-muted">
                {vpResult.viewport.width} × {vpResult.viewport.height}
              </p>
            </div>
          </div>
          <Badge variant={vpResult.page.page_load_success ? "success" : "critical"}>
            {vpResult.page.page_load_success ? (
              `HTTP ${vpResult.page.http_status || 200}`
            ) : (
              "Load Failed"
            )}
          </Badge>
        </div>

        {/* Page Metadata Summary */}
        <div className="flex flex-col gap-2 font-mono text-xs">
          <div className="flex items-center justify-between text-text-muted">
            <span>Title:</span>
            <span className="text-text-primary font-medium truncate max-w-[200px]" title={vpResult.page.title}>
              {vpResult.page.title || "N/A"}
            </span>
          </div>
          <div className="flex items-center justify-between text-text-muted">
            <span>Final URL:</span>
            <a
              href={vpResult.page.final_url}
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline truncate max-w-[200px] flex items-center gap-1"
            >
              <span className="truncate">{vpResult.page.final_url}</span>
              <ExternalLink className="w-3 h-3 shrink-0" />
            </a>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-2 text-center font-mono text-xs">
          <div className="p-2 rounded bg-background border border-border flex flex-col">
            <span className="text-text-muted text-[10px]">Console Errors</span>
            <span className={`font-bold ${vpResult.console_errors.length > 0 ? "text-status-error" : "text-status-success"}`}>
              {vpResult.console_errors.length}
            </span>
          </div>
          <div className="p-2 rounded bg-background border border-border flex flex-col">
            <span className="text-text-muted text-[10px]">Network Failures</span>
            <span className={`font-bold ${vpResult.network_failures.length > 0 ? "text-status-error" : "text-status-success"}`}>
              {vpResult.network_failures.length}
            </span>
          </div>
          <div className="p-2 rounded bg-background border border-border flex flex-col">
            <span className="text-text-muted text-[10px]">Overflow</span>
            <span className={`font-bold ${hasOverflow ? "text-status-warning" : "text-status-success"}`}>
              {vpResult.responsive.horizontal_overflow}px
            </span>
          </div>
        </div>

        {/* Screenshot Preview */}
        {screenshotUrl ? (
          <div className="relative rounded overflow-hidden border border-border bg-background group">
            <img
              src={screenshotUrl}
              alt={`${vpName} Screenshot`}
              className="w-full h-48 object-cover object-top transition-transform group-hover:scale-105"
            />
            <button
              onClick={() => setSelectedImage(screenshotUrl)}
              className="absolute inset-0 bg-background/60 backdrop-blur-sm opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 text-xs font-mono text-text-primary transition-opacity"
            >
              <Maximize2 className="w-4 h-4 text-accent" />
              View Full Screenshot
            </button>
          </div>
        ) : (
          <div className="h-48 rounded border border-dashed border-border bg-background flex items-center justify-center text-xs text-text-muted font-mono">
            <ImageIcon className="w-4 h-4 mr-2" />
            No Screenshot Captured
          </div>
        )}
      </Card>
    );
  };

  const renderAIFixPromptSection = (issue: Issue) => {
    const isAnalyzing = analyzingIssueId === issue.issue_id;
    const aiAnalysisResponse = issueAnalyses[issue.issue_id];
    const aiAnalysis = aiAnalysisResponse?.analysis;
    const analysisError = issueAnalysisErrors[issue.issue_id];

    return (
      <div className="mt-3 pt-3 border-t border-border/80 flex flex-col gap-3">
        {!aiAnalysis && !isAnalyzing && (
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAnalyzeIssue(issue.issue_id)}
              className="font-mono text-xs flex items-center gap-1.5 border-accent/40 text-accent hover:bg-accent/10"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Generate AI Fix Prompt
            </Button>
          </div>
        )}

        {isAnalyzing && (
          <div className="p-3 rounded bg-accent/5 border border-accent/20 text-accent text-xs font-mono flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin shrink-0 text-accent" />
            <span>Analyzing issue...</span>
          </div>
        )}

        {analysisError && !isAnalyzing && (
          <div className="p-3 rounded bg-status-error/10 border border-status-error/20 text-status-error text-xs font-mono flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{analysisError}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAnalyzeIssue(issue.issue_id)}
              className="text-[11px] h-7 px-2"
            >
              Retry
            </Button>
          </div>
        )}

        {aiAnalysis && !isAnalyzing && (
          <div className="p-4 rounded-lg border border-accent/30 bg-surface-raised/60 flex flex-col gap-4 font-sans text-xs">
            {/* Header with grounding badge */}
            <div className="flex items-center justify-between pb-2 border-b border-border/80">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-accent" />
                <h4 className="font-mono font-bold text-xs text-text-primary uppercase tracking-wide">
                  AI Analysis
                </h4>
              </div>
              <span className="text-[10px] font-mono text-text-muted flex items-center gap-1 bg-background px-2 py-0.5 rounded border border-border">
                <ShieldCheck className="w-3 h-3 text-status-success" />
                Generated from collected browser evidence
              </span>
            </div>

            {/* Summary */}
            {aiAnalysis.summary && (
              <div className="flex flex-col gap-1">
                <span className="font-mono font-semibold text-text-secondary text-[10px] uppercase tracking-wider">
                  Summary
                </span>
                <p className="text-text-primary leading-relaxed">{aiAnalysis.summary}</p>
              </div>
            )}

            {/* Likely Causes */}
            {aiAnalysis.likely_causes && aiAnalysis.likely_causes.length > 0 && (
              <div className="flex flex-col gap-1">
                <span className="font-mono font-semibold text-text-secondary text-[10px] uppercase tracking-wider">
                  Likely Causes
                </span>
                <ul className="list-disc list-inside space-y-1 text-text-muted pl-1">
                  {aiAnalysis.likely_causes.map((cause, idx) => (
                    <li key={idx} className="text-text-primary">{cause}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Investigation Hints */}
            {aiAnalysis.investigation_hints && aiAnalysis.investigation_hints.length > 0 && (
              <div className="flex flex-col gap-1">
                <span className="font-mono font-semibold text-text-secondary text-[10px] uppercase tracking-wider">
                  Investigation Hints
                </span>
                <ul className="list-disc list-inside space-y-1 text-text-muted pl-1">
                  {aiAnalysis.investigation_hints.map((hint, idx) => (
                    <li key={idx} className="text-text-primary">{hint}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Expected Result */}
            {aiAnalysis.expected_result && (
              <div className="flex flex-col gap-1">
                <span className="font-mono font-semibold text-text-secondary text-[10px] uppercase tracking-wider">
                  Expected Result
                </span>
                <p className="text-text-primary leading-relaxed">{aiAnalysis.expected_result}</p>
              </div>
            )}

            {/* Constraints */}
            {aiAnalysis.constraints && aiAnalysis.constraints.length > 0 && (
              <div className="flex flex-col gap-1">
                <span className="font-mono font-semibold text-text-secondary text-[10px] uppercase tracking-wider">
                  Constraints
                </span>
                <ul className="list-disc list-inside space-y-1 text-text-muted pl-1">
                  {aiAnalysis.constraints.map((constraint, idx) => (
                    <li key={idx} className="text-text-primary">{constraint}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Verification Steps */}
            {aiAnalysis.verification_steps && aiAnalysis.verification_steps.length > 0 && (
              <div className="flex flex-col gap-1">
                <span className="font-mono font-semibold text-text-secondary text-[10px] uppercase tracking-wider">
                  Verification Steps
                </span>
                <ol className="list-decimal list-inside space-y-1 text-text-muted pl-1">
                  {aiAnalysis.verification_steps.map((step, idx) => (
                    <li key={idx} className="text-text-primary">{step}</li>
                  ))}
                </ol>
              </div>
            )}

            {/* Developer Fix Prompt */}
            {aiAnalysis.fix_prompt && (
              <div className="mt-2 pt-3 border-t border-border flex flex-col gap-2 font-mono">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-accent uppercase tracking-wider flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-accent" />
                    Developer Fix Prompt
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopyPrompt(issue.issue_id, aiAnalysis.fix_prompt)}
                    className="text-xs h-7 px-2.5 flex items-center gap-1.5 font-mono"
                  >
                    {copiedPromptIssueId === issue.issue_id ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Copy Prompt
                      </>
                    )}
                  </Button>
                </div>
                <pre className="p-3 rounded bg-background border border-border text-xs text-text-secondary overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-96">
                  {aiAnalysis.fix_prompt}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderIssueEvidenceDetails = (issue: Issue) => {
    const isResponsive = issue.category === 'responsive' || issue.category === 'layout' || issue.title.toLowerCase().includes('overflow');
    const isConsole = issue.category === 'console' || issue.category === 'console_error';
    const isBrokenResource = issue.category === 'broken_resource' || issue.category === 'network_failure';
    const vpName = issue.viewport?.toLowerCase();
    const vpData = vpName === 'mobile' ? currentAudit?.mobile : (vpName === 'desktop' ? currentAudit?.desktop : null);

    return (
      <div className="mt-3 pt-3 border-t border-border/60 flex flex-col gap-3 font-mono text-xs">
        <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-accent" />
          <span>Collected Evidence & Diagnostic Data</span>
        </div>

        {/* Responsive / Overflow evidence breakdown */}
        {isResponsive && vpData?.responsive && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 bg-background p-2.5 rounded border border-border">
            <div>
              <span className="text-[10px] text-text-muted block">Viewport</span>
              <span className="font-semibold text-text-primary">{vpData.responsive.viewport_width} × {vpData.responsive.viewport_height}</span>
            </div>
            <div>
              <span className="text-[10px] text-text-muted block">Document width</span>
              <span className="font-semibold text-text-primary">{vpData.responsive.document_scroll_width}px</span>
            </div>
            <div>
              <span className="text-[10px] text-text-muted block">Viewport width</span>
              <span className="font-semibold text-text-primary">{vpData.responsive.viewport_width}px</span>
            </div>
            <div>
              <span className="text-[10px] text-text-muted block">Overflow</span>
              <span className="font-semibold text-status-warning">{vpData.responsive.horizontal_overflow}px</span>
            </div>
          </div>
        )}

        {/* Target Selector & Target URL */}
        {(issue.selector || currentAudit?.target_url || currentAudit?.url) && (
          <div className="flex flex-col gap-1 bg-background p-2.5 rounded border border-border">
            {currentAudit && (
              <div className="flex items-center gap-2 text-text-muted">
                <span className="shrink-0 text-[11px]">Target URL:</span>
                <span className="text-text-primary truncate font-mono">{issue.viewport ? `${currentAudit.target_url || currentAudit.url}` : (currentAudit.target_url || currentAudit.url)}</span>
              </div>
            )}
            {issue.selector && (
              <div className="flex items-center gap-2 text-text-muted">
                <span className="shrink-0 text-[11px]">Target Element / Selector:</span>
                <code className="text-accent truncate font-mono bg-accent/10 px-1.5 py-0.5 rounded">{issue.selector}</code>
              </div>
            )}
          </div>
        )}

        {/* Console / Network Log Details */}
        {(isConsole || isBrokenResource) && vpData && (
          <div className="bg-background p-2.5 rounded border border-border flex flex-col gap-1.5">
            <span className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Browser Log Trace</span>
            {vpData.console_errors.map((err, idx) => (
              <div key={idx} className="text-status-error font-mono text-[11px] bg-status-error/5 p-1.5 rounded border border-status-error/20">
                Message: {err.text}
                {err.location && <div className="text-[10px] text-text-muted mt-0.5">Location: {err.location}</div>}
              </div>
            ))}
            {vpData.network_failures.map((net, idx) => (
              <div key={idx} className="text-status-error font-mono text-[11px] bg-status-error/5 p-1.5 rounded border border-status-error/20">
                URL: {net.url}
                {net.status_code && <div>HTTP Status: {net.status_code}</div>}
                <div>Error: {net.error_text}</div>
              </div>
            ))}
          </div>
        )}

        {/* Evidence References Array */}
        {issue.evidence_references && issue.evidence_references.length > 0 && (
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Evidence References</span>
            <div className="flex flex-wrap gap-1.5">
              {issue.evidence_references.map((ref, idx) => (
                <span key={idx} className="px-2 py-0.5 rounded bg-background border border-border text-[11px] font-mono text-text-secondary">
                  {ref}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* AI Fix Prompt & Analysis Section */}
        {renderAIFixPromptSection(issue)}
      </div>
    );
  };


  const allIssues = currentAudit ? (currentAudit.issues?.length > 0 ? currentAudit.issues : (currentAudit.findings || [])) : [];
  const filteredIssues = severityFilter === 'all'
    ? allIssues
    : allIssues.filter((i) => i.severity.toLowerCase() === severityFilter.toLowerCase());

  if (authStatus === 'loading') {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center font-sans antialiased">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-inner">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <span className="font-bold text-lg tracking-tight text-white">UIProof AI</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400 font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
          <span>Restoring user session...</span>
        </div>
      </div>
    );
  }

  if (authStatus === 'unauthenticated') {
    return (
      <AuthContainer
        onSuccess={handleAuthSuccess}
        externalError={authError}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col font-sans">
      <Header
        projects={projects}
        selectedProject={selectedProject}
        onSelectProject={setSelectedProject}
        onOpenCreateProjectModal={() => setIsCreateProjectOpen(true)}
        historyCount={historyAudits.length}
        onOpenHistory={() => setIsHistoryOpen((prev) => !prev)}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        {/* URL Entry & Test Config Bar */}
        <Card className="border border-border bg-surface-raised/40 backdrop-blur">
          <form onSubmit={handleRunAudit} className="flex flex-col gap-4">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted">
              <div className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-accent" />
                <span>REAL PLAYWRIGHT AUDIT ENGINE</span>
              </div>
              <span className="text-[10px] text-text-muted">Desktop (1440x900) & Mobile (390x844)</span>
            </div>

            <div className="flex flex-col md:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
                  <Globe className="w-4 h-4" />
                </div>
                <Input
                  type="text"
                  placeholder="Enter application URL (e.g. https://example.com)"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={isLoading}
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
              </div>

              <Button type="submit" isLoading={isLoading} disabled={isLoading} className="w-full md:w-auto font-mono">
                <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
                Run Audit
              </Button>
            </div>
          </form>

          {/* Loading Indicator */}
          {isLoading && (
            <div className="mt-4 p-4 rounded bg-accent/5 border border-accent/20 text-accent text-xs font-mono flex items-center gap-3 animate-pulse">
              <Loader2 className="w-4 h-4 animate-spin shrink-0 text-accent" />
              <div>
                <span className="font-semibold">Launching Playwright Chromium Engine...</span>
                <p className="text-[11px] text-text-muted mt-0.5">
                  Visiting {url}, recording console logs, inspecting network responses, checking images/links, and calculating horizontal overflow.
                </p>
              </div>
            </div>
          )}

          {isRetesting && (
            <div className="mt-4 p-4 rounded bg-accent/5 border border-accent/20 text-accent text-xs font-mono flex items-center gap-3 animate-pulse">
              <RefreshCw className="w-4 h-4 animate-spin shrink-0 text-accent" />
              <div>
                <span className="font-semibold">Re-running Playwright audit...</span>
                <p className="text-[11px] text-text-muted mt-0.5">
                  Re-testing {currentAudit?.target_url || currentAudit?.url} against baseline audit ({currentAudit?.audit_id.slice(0, 8)}).
                </p>
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="mt-4 p-3 rounded bg-status-error/10 border border-status-error/20 text-status-error text-xs font-mono flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </Card>

        {/* Audit Summary Header Bar */}
        {currentAudit && (
          <Card className="border border-border bg-surface-raised/50 flex flex-col md:flex-row md:items-center justify-between gap-4 py-4 px-6 font-mono">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <span>AUDIT SUMMARY</span>
                <span>•</span>
                <span className="text-[11px]">ID: {currentAudit.audit_id.slice(0, 8)}</span>
                {baselineAudit && (
                  <>
                    <span>•</span>
                    <span className="text-[11px] text-accent">Baseline: {baselineAudit.audit_id.slice(0, 8)}</span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={currentAudit.target_url || currentAudit.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-semibold text-text-primary hover:text-accent flex items-center gap-1.5 truncate max-w-md"
                >
                  <span className="truncate">{currentAudit.target_url || currentAudit.url}</span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                </a>
                <Badge variant={currentAudit.status === 'completed' ? 'success' : 'critical'}>
                  {currentAudit.status.toUpperCase()}
                </Badge>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs flex-wrap">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-background border border-border">
                <span className="text-text-muted">Total:</span>
                <span className="font-bold text-text-primary">{currentAudit.stats?.total_issues ?? allIssues.length}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-status-error/10 border border-status-error/20 text-status-error">
                <span>Critical:</span>
                <span className="font-bold">{currentAudit.stats?.critical_count ?? 0}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-status-warning/10 border border-status-warning/20 text-status-warning">
                <span>High:</span>
                <span className="font-bold">{currentAudit.stats?.high_count ?? 0}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-yellow-500/10 border border-yellow-500/20 text-yellow-400">
                <span>Medium:</span>
                <span className="font-bold">{currentAudit.stats?.medium_count ?? 0}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-status-info/10 border border-status-info/20 text-status-info">
                <span>Low:</span>
                <span className="font-bold">{currentAudit.stats?.low_count ?? 0}</span>
              </div>

              {/* Retest Application Action Button */}
              {currentAudit.status === 'completed' && (
                <Button
                  onClick={handleRetestApplication}
                  isLoading={isRetesting}
                  disabled={isRetesting || isLoading}
                  variant="outline"
                  size="sm"
                  className="font-mono text-xs flex items-center gap-1.5 border-accent/40 text-accent hover:bg-accent/10 ml-2"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRetesting ? 'animate-spin' : ''}`} />
                  {isRetesting ? 'Re-running Playwright audit...' : 'Retest Application'}
                </Button>
              )}
            </div>
          </Card>
        )}

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
                Audit Evidence & Issues ({allIssues.length})
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
          </div>
        )}

        {/* Tab Content 1: Main Audit View */}
        {activeTab === 'audit' && currentAudit && (
          <div className="flex flex-col gap-6">
            {/* Viewport Browser Evidence Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {renderViewportEvidenceCard("Desktop", <Monitor className="w-4 h-4" />, currentAudit.desktop || currentAudit.evidence?.desktop)}
              {renderViewportEvidenceCard("Mobile", <Smartphone className="w-4 h-4" />, currentAudit.mobile || currentAudit.evidence?.mobile)}
            </div>

            {/* Issues Found Section Header */}
            <div className="flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Bug className="w-4 h-4 text-accent" />
                  <h3 className="text-sm font-mono font-bold text-text-primary uppercase tracking-wider">
                    Issues Found ({allIssues.length})
                  </h3>
                </div>

                {/* Severity Filter Buttons Bar */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs font-mono text-text-muted flex items-center gap-1 mr-1">
                    <Filter className="w-3 h-3 text-accent" /> Filter:
                  </span>
                  <button
                    onClick={() => setSeverityFilter('all')}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      severityFilter === 'all'
                        ? 'bg-accent text-background font-bold'
                        : 'bg-background border border-border text-text-muted hover:text-text-primary'
                    }`}
                  >
                    All ({allIssues.length})
                  </button>
                  <button
                    onClick={() => setSeverityFilter('critical')}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      severityFilter === 'critical'
                        ? 'bg-status-error text-white font-bold'
                        : 'bg-background border border-border text-status-error/80 hover:text-status-error'
                    }`}
                  >
                    Critical ({currentAudit.stats?.critical_count ?? 0})
                  </button>
                  <button
                    onClick={() => setSeverityFilter('high')}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      severityFilter === 'high'
                        ? 'bg-status-warning text-white font-bold'
                        : 'bg-background border border-border text-status-warning/80 hover:text-status-warning'
                    }`}
                  >
                    High ({currentAudit.stats?.high_count ?? 0})
                  </button>
                  <button
                    onClick={() => setSeverityFilter('medium')}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      severityFilter === 'medium'
                        ? 'bg-yellow-500 text-black font-bold'
                        : 'bg-background border border-border text-yellow-400 hover:text-yellow-300'
                    }`}
                  >
                    Medium ({currentAudit.stats?.medium_count ?? 0})
                  </button>
                  <button
                    onClick={() => setSeverityFilter('low')}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      severityFilter === 'low'
                        ? 'bg-status-info text-white font-bold'
                        : 'bg-background border border-border text-status-info/80 hover:text-status-info'
                    }`}
                  >
                    Low ({currentAudit.stats?.low_count ?? 0})
                  </button>
                </div>
              </div>

              {/* Clean Audit State: issues.length === 0 */}
              {allIssues.length === 0 ? (
                <Card className="flex flex-col items-center justify-center py-12 text-center border-dashed border-status-success/30 bg-status-success/5">
                  <CheckCircle2 className="w-10 h-10 text-status-success mb-3 opacity-90" />
                  <h4 className="text-base font-semibold text-text-primary">No issues detected</h4>
                  <p className="text-xs text-text-muted max-w-md mt-1 font-mono">
                    Playwright inspected the site cleanly across all viewports. No missing metadata, broken images, broken links, console errors, network request failures, or horizontal layout overflows were detected.
                  </p>
                </Card>
              ) : filteredIssues.length === 0 ? (
                <Card className="flex flex-col items-center justify-center py-10 text-center border-dashed">
                  <AlertCircle className="w-8 h-8 text-text-muted mb-2" />
                  <h4 className="text-sm font-medium text-text-primary">No issues match filter "{severityFilter}"</h4>
                  <button
                    onClick={() => setSeverityFilter('all')}
                    className="mt-3 text-xs font-mono text-accent underline hover:text-accent/80"
                  >
                    Clear Filter
                  </button>
                </Card>
              ) : (
                <div className="flex flex-col gap-4">
                  {filteredIssues.map((issue) => {
                    const isExpanded = expandedIssueIds[issue.issue_id] ?? true;

                    return (
                      <Card key={issue.issue_id} className="flex flex-col gap-3 border-border bg-surface-raised/20 hover:border-border/80 transition-colors">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-2 flex-wrap">
                            <button
                              onClick={() => toggleIssueExpansion(issue.issue_id)}
                              className="p-1 rounded hover:bg-background text-text-muted hover:text-text-primary transition-colors"
                              title={isExpanded ? "Collapse Details" : "Expand Details"}
                            >
                              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            </button>

                            <Badge variant={issue.severity.toLowerCase() as any}>
                              {issue.severity.toUpperCase()}
                            </Badge>

                            <span className="font-mono text-xs font-bold text-text-primary bg-background px-2 py-0.5 rounded border border-border">
                              {issue.issue_id}
                            </span>

                            {issue.viewport && (
                              <span className="px-2 py-0.5 rounded bg-background border border-border text-[10px] font-mono text-accent flex items-center gap-1">
                                {issue.viewport.toLowerCase() === 'mobile' ? (
                                  <Smartphone className="w-3 h-3" />
                                ) : (
                                  <Monitor className="w-3 h-3" />
                                )}
                                {issue.viewport.toUpperCase()}
                              </span>
                            )}
                          </div>

                          <Badge variant="neutral">{issue.category.toUpperCase()}</Badge>
                        </div>

                        <div>
                          <h4 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                            {issue.title}
                          </h4>
                          <p className="text-xs text-text-muted mt-1 leading-relaxed">{issue.description}</p>
                        </div>

                        {/* Expandable Details & Evidence */}
                        {isExpanded && renderIssueEvidenceDetails(issue)}
                      </Card>
                    );
                  })}
                </div>
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
          <div className="flex flex-col gap-6">
            {/* Comparison Summary Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg bg-surface-raised/40 border border-border font-mono text-xs">
              <div className="flex items-center gap-2">
                <GitCompare className="w-4 h-4 text-accent" />
                <span className="font-semibold text-text-primary uppercase">Verification Flow:</span>
                <span className="text-text-muted">
                  Baseline ({comparisonResult.baseline_audit_id.slice(0, 8)}) → Retest ({comparisonResult.new_audit_id.slice(0, 8)})
                </span>
              </div>
              <span className="text-[11px] text-text-muted">
                Deterministic ID Matching ({comparisonResult.fixed_issues.length + comparisonResult.remaining_issues.length + comparisonResult.new_issues.length} total issues analyzed)
              </span>
            </div>

            {/* Category Cards (Clickable) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
              <button
                onClick={() => setCompareCategoryTab('fixed')}
                className={`text-left p-4 rounded-lg border transition-colors flex flex-col gap-2 ${
                  compareCategoryTab === 'fixed'
                    ? 'border-status-success bg-status-success/15 ring-1 ring-status-success'
                    : 'border-status-success/30 bg-status-success/5 hover:border-status-success/60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-status-success">FIXED ISSUES</span>
                  <Badge variant="success">{comparisonResult.fixed_issues.length}</Badge>
                </div>
                <p className="text-xs text-text-muted">Resolved between baseline and re-test audit.</p>
              </button>

              <button
                onClick={() => setCompareCategoryTab('remaining')}
                className={`text-left p-4 rounded-lg border transition-colors flex flex-col gap-2 ${
                  compareCategoryTab === 'remaining'
                    ? 'border-status-warning bg-status-warning/15 ring-1 ring-status-warning'
                    : 'border-status-warning/30 bg-status-warning/5 hover:border-status-warning/60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-status-warning">REMAINING ISSUES</span>
                  <Badge variant="high">{comparisonResult.remaining_issues.length}</Badge>
                </div>
                <p className="text-xs text-text-muted">Unresolved issues still detected on re-test.</p>
              </button>

              <button
                onClick={() => setCompareCategoryTab('new')}
                className={`text-left p-4 rounded-lg border transition-colors flex flex-col gap-2 ${
                  compareCategoryTab === 'new'
                    ? 'border-status-info bg-status-info/15 ring-1 ring-status-info'
                    : 'border-status-info/30 bg-status-info/5 hover:border-status-info/60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-status-info">NEW ISSUES</span>
                  <Badge variant="neutral">{comparisonResult.new_issues.length}</Badge>
                </div>
                <p className="text-xs text-text-muted">Newly detected in retest but not in baseline.</p>
              </button>
            </div>

            {/* Issue Cards for Selected Category */}
            <div className="flex flex-col gap-4">
              {compareCategoryTab === 'fixed' && (
                <>
                  <div className="flex items-center justify-between border-b border-border pb-2 font-mono">
                    <span className="text-xs font-bold text-status-success uppercase flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-status-success" />
                      Fixed Issues ({comparisonResult.fixed_issues.length})
                    </span>
                    <span className="text-[11px] text-text-muted">Not detected in retest</span>
                  </div>
                  {comparisonResult.fixed_issues.length === 0 ? (
                    <Card className="py-8 text-center text-xs font-mono text-text-muted border-dashed">
                      No fixed issues detected in retest.
                    </Card>
                  ) : (
                    comparisonResult.fixed_issues.map((issue) => {
                      const isExpanded = expandedIssueIds[issue.issue_id] ?? true;
                      return (
                        <Card key={issue.issue_id} className="flex flex-col gap-3 border-status-success/30 bg-status-success/5">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-center gap-2 flex-wrap">
                              <button
                                onClick={() => toggleIssueExpansion(issue.issue_id)}
                                className="p-1 rounded hover:bg-background text-text-muted hover:text-text-primary transition-colors"
                              >
                                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                              </button>
                              <Badge variant="success">FIXED</Badge>
                              <span className="font-mono text-xs font-bold text-text-primary bg-background px-2 py-0.5 rounded border border-border">
                                {issue.issue_id}
                              </span>
                              {issue.viewport && (
                                <span className="px-2 py-0.5 rounded bg-background border border-border text-[10px] font-mono text-accent">
                                  {issue.viewport.toUpperCase()}
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] font-mono text-status-success font-medium">Not detected in retest</span>
                          </div>
                          <div>
                            <h4 className="text-sm font-semibold text-text-primary">{issue.title}</h4>
                            <p className="text-xs text-text-muted mt-1 leading-relaxed">{issue.description}</p>
                          </div>
                          {isExpanded && renderIssueEvidenceDetails(issue)}
                        </Card>
                      );
                    })
                  )}
                </>
              )}

              {compareCategoryTab === 'remaining' && (
                <>
                  <div className="flex items-center justify-between border-b border-border pb-2 font-mono">
                    <span className="text-xs font-bold text-status-warning uppercase flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-status-warning" />
                      Remaining Issues ({comparisonResult.remaining_issues.length})
                    </span>
                    <span className="text-[11px] text-text-muted">Still detected in retest</span>
                  </div>
                  {comparisonResult.remaining_issues.length === 0 ? (
                    <Card className="py-8 text-center text-xs font-mono text-text-muted border-dashed">
                      No remaining issues found. All baseline issues resolved!
                    </Card>
                  ) : (
                    comparisonResult.remaining_issues.map((issue) => {
                      const isExpanded = expandedIssueIds[issue.issue_id] ?? true;
                      return (
                        <Card key={issue.issue_id} className="flex flex-col gap-3 border-status-warning/30 bg-status-warning/5">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-center gap-2 flex-wrap">
                              <button
                                onClick={() => toggleIssueExpansion(issue.issue_id)}
                                className="p-1 rounded hover:bg-background text-text-muted hover:text-text-primary transition-colors"
                              >
                                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                              </button>
                              <Badge variant="high">STILL DETECTED</Badge>
                              <span className="font-mono text-xs font-bold text-text-primary bg-background px-2 py-0.5 rounded border border-border">
                                {issue.issue_id}
                              </span>
                              {issue.viewport && (
                                <span className="px-2 py-0.5 rounded bg-background border border-border text-[10px] font-mono text-accent">
                                  {issue.viewport.toUpperCase()}
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] font-mono text-status-warning font-medium">Still detected</span>
                          </div>
                          <div>
                            <h4 className="text-sm font-semibold text-text-primary">{issue.title}</h4>
                            <p className="text-xs text-text-muted mt-1 leading-relaxed">{issue.description}</p>
                          </div>
                          {isExpanded && renderIssueEvidenceDetails(issue)}
                        </Card>
                      );
                    })
                  )}
                </>
              )}

              {compareCategoryTab === 'new' && (
                <>
                  <div className="flex items-center justify-between border-b border-border pb-2 font-mono">
                    <span className="text-xs font-bold text-status-info uppercase flex items-center gap-1.5">
                      <Bug className="w-4 h-4 text-status-info" />
                      New Issues ({comparisonResult.new_issues.length})
                    </span>
                    <span className="text-[11px] text-text-muted">Detected in retest but not present in baseline</span>
                  </div>
                  {comparisonResult.new_issues.length === 0 ? (
                    <Card className="py-8 text-center text-xs font-mono text-text-muted border-dashed">
                      No new issues introduced in retest.
                    </Card>
                  ) : (
                    comparisonResult.new_issues.map((issue) => {
                      const isExpanded = expandedIssueIds[issue.issue_id] ?? true;
                      return (
                        <Card key={issue.issue_id} className="flex flex-col gap-3 border-status-info/30 bg-status-info/5">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-center gap-2 flex-wrap">
                              <button
                                onClick={() => toggleIssueExpansion(issue.issue_id)}
                                className="p-1 rounded hover:bg-background text-text-muted hover:text-text-primary transition-colors"
                              >
                                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                              </button>
                              <Badge variant="neutral">NEW ISSUE</Badge>
                              <span className="font-mono text-xs font-bold text-text-primary bg-background px-2 py-0.5 rounded border border-border">
                                {issue.issue_id}
                              </span>
                              {issue.viewport && (
                                <span className="px-2 py-0.5 rounded bg-background border border-border text-[10px] font-mono text-accent">
                                  {issue.viewport.toUpperCase()}
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] font-mono text-status-info font-medium">Detected in retest but not present in baseline</span>
                          </div>
                          <div>
                            <h4 className="text-sm font-semibold text-text-primary">{issue.title}</h4>
                            <p className="text-xs text-text-muted mt-1 leading-relaxed">{issue.description}</p>
                          </div>
                          {isExpanded && renderIssueEvidenceDetails(issue)}
                        </Card>
                      );
                    })
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* Empty State when no audit has been run */}
        {!currentAudit && !isLoading && (
          <Card className="flex flex-col items-center justify-center py-20 text-center border-dashed">
            <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center text-accent mb-4">
              <Globe className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-text-primary mb-1">
              Ready to Audit Application Quality
            </h3>
            <p className="text-xs text-text-muted max-w-md mb-6">
              Enter a web application URL above to launch Playwright Chromium, collect real browser traces, identify responsive layout overflows, missing meta descriptions, broken resources, and console errors.
            </p>
            <div className="flex items-center gap-3 text-xs font-mono text-text-muted">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-accent" />
                Playwright Chromium Engine
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-status-success" />
                Desktop (1440x900) & Mobile (390x844)
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-status-info" />
                Deterministic Issue Hash IDs
              </span>
            </div>
          </Card>
        )}
      </main>

      {/* Screenshot Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 bg-background/90 backdrop-blur-md flex items-center justify-center p-6"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-5xl w-full max-h-[90vh] bg-surface-raised border border-border rounded-lg p-2 overflow-auto">
            <img src={selectedImage} alt="Full Screenshot" className="w-full h-auto rounded" />
          </div>
        </div>
      )}

      {/* Audit History Sidebar Drawer */}
      <AuditHistorySidebar
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        audits={historyAudits}
        currentAuditId={currentAudit?.audit_id || null}
        onSelectAudit={(auditId) => {
          handleSelectHistoricalAudit(auditId);
          setIsHistoryOpen(false);
        }}
        projectName={selectedProject ? selectedProject.name : undefined}
      />

      {/* Create Project Modal Dialog */}
      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onProjectCreated={handleProjectCreated}
      />
    </div>
  );
};

export default App;
