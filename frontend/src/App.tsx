import React, { useState, useEffect } from 'react';
import { AppShell } from './components/layout/AppShell';
import { NewAuditForm } from './components/audit/NewAuditForm';
import { AuditProgress } from './components/audit/AuditProgress';
import { AuditResultsWorkspace } from './components/results/AuditResultsWorkspace';
import { AIAnalysisPanel } from './components/ai/AIAnalysisPanel';
import { RetestComparisonWorkspace } from './components/compare/RetestComparisonWorkspace';
import { DashboardWorkspace } from './components/dashboard/DashboardWorkspace';
import { AuditHistoryWorkspace } from './components/history/AuditHistoryWorkspace';
import { ProjectsWorkspace } from './components/projects/ProjectsWorkspace';
import { Card } from './components/ui/Card';
import { Button } from './components/ui/Button';
import {
  AuditResult,
  DeveloperFixPrompt,
  AuditComparison,
  Issue,
  IssueAnalysisResponse,
  Project,
  AuditSummaryItem,
} from './types/audit';
import { User } from './types/auth';
import {
  createAudit,
  getFixPrompt,
  compareAudits,
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
  Code2,
  Layers,
  GitCompare,
  FileCode,
  Loader2,
  ShieldCheck,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  X,
} from 'lucide-react';

const ZOOM_LEVELS = [50, 75, 100, 125, 150, 200, 250, 300];

const AUDIT_STAGES = [
  "1. Preparing audit configuration...",
  "2. Launching Playwright Chromium browser...",
  "3. Navigating target URL & auditing Desktop (1440x900)...",
  "4. Auditing Mobile viewport (390x844)...",
  "5. Collecting DOM metrics & screenshot evidence...",
  "6. Running deterministic issue analysis...",
  "7. Finalizing audit results..."
];

export const App: React.FC = () => {
  // Milestone 7F: Auth & User Session State
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authStatus, setAuthStatus] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading');
  const [authError, setAuthError] = useState<string | null>(null);
  // Navigation shell section state
  const [activeNav, setActiveNav] = useState<'dashboard' | 'audits' | 'projects' | 'history'>('audits');

  const [url, setUrl] = useState('');
  const [auditMode, setAuditMode] = useState<'remote' | 'local'>('remote');
  const [selectedViewports, setSelectedViewports] = useState<string[]>(['desktop', 'mobile']);
  const [isLoading, setIsLoading] = useState(false);
  const [auditStageIndex, setAuditStageIndex] = useState<number>(0);
  const [isRetesting, setIsRetesting] = useState(false);
  const [activeTab, setActiveTab] = useState<'audit' | 'compare' | 'prompt'>('audit');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [zoomIndex, setZoomIndex] = useState<number>(2); // Default 100%

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

  // Keyboard listener for screenshot lightbox zoom and escape key
  useEffect(() => {
    if (!selectedImage) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedImage(null);
        setZoomIndex(2);
      } else if (e.key === '+' || e.key === '=') {
        setZoomIndex((prev) => Math.min(ZOOM_LEVELS.length - 1, prev + 1));
      } else if (e.key === '-') {
        setZoomIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === '0') {
        setZoomIndex(2);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedImage]);



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

  const handleRetestApplication = async () => {
    if (!currentAudit || isRetesting || isLoading) return;
    setIsRetesting(true);
    setErrorMessage(null);
    setAuditStageIndex(0);

    const stageInterval = setInterval(() => {
      setAuditStageIndex((prev) => (prev < AUDIT_STAGES.length - 1 ? prev + 1 : prev));
    }, 1400);

    try {
      const res = await retestAudit(currentAudit.audit_id);
      setBaselineAudit(currentAudit);
      setCurrentAudit(res.retest_audit);
      setComparisonResult(res.comparison);
      setActiveTab('compare');

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
      clearInterval(stageInterval);
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
      const prefix = auditMode === 'local' ? 'http://' : 'https://';
      targetUrl = `${prefix}${targetUrl}`;
      setUrl(targetUrl);
    }

    setIsLoading(true);
    setAuditStageIndex(0);
    setErrorMessage(null);

    const stageInterval = setInterval(() => {
      setAuditStageIndex((prev) => (prev < AUDIT_STAGES.length - 1 ? prev + 1 : prev));
    }, 1400);

    try {
      if (currentAudit && currentAudit.status === 'completed') {
        setBaselineAudit(currentAudit);
      }

      const result = await createAudit({
        url: targetUrl,
        mode: auditMode,
        viewports: selectedViewports,
        project_id: selectedProject?.project_id,
      });

      setCurrentAudit(result);

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
      clearInterval(stageInterval);
      setIsLoading(false);
    }
  };

  const renderAIFixPromptSection = (issue: Issue) => {
    return (
      <AIAnalysisPanel
        issue={issue}
        analysisResponse={issueAnalyses[issue.issue_id]}
        isAnalyzing={analyzingIssueId === issue.issue_id}
        analysisError={issueAnalysisErrors[issue.issue_id]}
        onAnalyze={handleAnalyzeIssue}
        onCopyPrompt={handleCopyPrompt}
        isCopied={copiedPromptIssueId === issue.issue_id}
      />
    );
  };




  const allIssues = currentAudit ? (currentAudit.issues?.length > 0 ? currentAudit.issues : (currentAudit.findings || [])) : [];

  if (authStatus === 'loading') {
    return (
      <div className="min-h-screen bg-background text-text-primary flex flex-col justify-center items-center font-sans antialiased">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-inner">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <span className="font-bold text-lg tracking-tight text-text-primary">UIProof AI</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-text-muted font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-primary" />
          <span>Restoring session...</span>
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
    <AppShell
      activeNav={activeNav}
      onNavSelect={(nav) => {
        setActiveNav(nav);
        if (nav === 'history') {
          setIsHistoryOpen(true);
        } else if (nav === 'projects') {
          setIsCreateProjectOpen(true);
        }
      }}
      onNewAudit={() => {
        setCurrentAudit(null);
        setBaselineAudit(null);
        setComparisonResult(null);
        setActiveTab('audit');
        setActiveNav('audits');
      }}
      projects={projects}
      selectedProject={selectedProject}
      onSelectProject={setSelectedProject}
      onOpenCreateProjectModal={() => setIsCreateProjectOpen(true)}
      historyCount={historyAudits.length}
      onToggleHistory={() => setIsHistoryOpen((prev) => !prev)}
      isHistoryOpen={isHistoryOpen}
      currentUser={currentUser}
      onLogout={handleLogout}
    >
      {/* DASHBOARD VIEW */}
      {activeNav === 'dashboard' && (
        <DashboardWorkspace
          projects={projects}
          selectedProject={selectedProject}
          historyAudits={historyAudits}
          isLoading={isLoading}
          errorMessage={errorMessage}
          onNewAudit={() => setActiveNav('audits')}
          onSelectAudit={(auditId) => {
            handleSelectHistoricalAudit(auditId);
            setActiveNav('audits');
          }}
          onViewHistory={() => setActiveNav('history')}
          onViewProjects={() => setActiveNav('projects')}
          onSelectProject={setSelectedProject}
          onOpenCreateProjectModal={() => setIsCreateProjectOpen(true)}
          onRetry={() => {
            loadProjects();
            loadHistory(selectedProject?.project_id);
          }}
        />
      )}

      {/* AUDIT HISTORY VIEW */}
      {activeNav === 'history' && (
        <AuditHistoryWorkspace
          historyAudits={historyAudits}
          projects={projects}
          selectedProject={selectedProject}
          isLoading={isLoading}
          errorMessage={errorMessage}
          onSelectAudit={(auditId) => {
            handleSelectHistoricalAudit(auditId);
            setActiveNav('audits');
          }}
          onNewAudit={() => setActiveNav('audits')}
          onSelectProject={setSelectedProject}
          onRetry={() => loadHistory(selectedProject?.project_id)}
        />
      )}

      {/* PROJECTS VIEW */}
      {activeNav === 'projects' && (
        <ProjectsWorkspace
          projects={projects}
          selectedProject={selectedProject}
          isLoading={isLoading}
          errorMessage={errorMessage}
          onSelectProject={setSelectedProject}
          onOpenCreateProjectModal={() => setIsCreateProjectOpen(true)}
          onNewAudit={() => setActiveNav('audits')}
          onRetry={loadProjects}
        />
      )}

      {/* AUDIT WORKSPACE VIEW */}
      {activeNav === 'audits' && (
        <div className="max-w-7xl w-full mx-auto px-4 lg:px-6 py-6 flex flex-col gap-6">
          {/* New Audit Form */}
          <NewAuditForm
            url={url}
            onUrlChange={setUrl}
            auditMode={auditMode}
            onAuditModeChange={setAuditMode}
            selectedViewports={selectedViewports}
            onToggleViewport={toggleViewport}
            isLoading={isLoading}
            onSubmit={handleRunAudit}
            selectedProject={selectedProject}
          />

          {/* Audit Progress Execution & Lifecycle */}
          <AuditProgress
            isLoading={isLoading}
            auditStageIndex={auditStageIndex}
            stages={AUDIT_STAGES}
            targetUrl={url}
            auditMode={auditMode}
            selectedViewports={selectedViewports}
            isRetesting={isRetesting}
            retestAuditId={currentAudit?.audit_id}
            errorMessage={errorMessage}
          />

          {/* Audit Navigation Tabs */}
          {currentAudit && (
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`px-3 py-1.5 rounded text-xs font-mono font-medium flex items-center gap-2 transition-colors ${
                    activeTab === 'audit'
                      ? 'bg-surface-raised text-text-primary border border-border shadow-subtle'
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
                      ? 'bg-surface-raised text-text-primary border border-border shadow-subtle'
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
                        ? 'bg-surface-raised text-text-primary border border-border shadow-subtle'
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

          {/* Tab Content 1: Main Audit View (Phase 3 Workspace) */}
          {activeTab === 'audit' && currentAudit && (
            <AuditResultsWorkspace
              audit={currentAudit}
              selectedProject={selectedProject}
              baselineAuditId={baselineAudit?.audit_id}
              onRetest={handleRetestApplication}
              isRetesting={isRetesting}
              onSelectImage={(imageUrl) => {
                setSelectedImage(imageUrl);
                setZoomIndex(2);
              }}
              renderAIAndPromptSection={renderAIFixPromptSection}
            />
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
          {activeTab === 'compare' && (comparisonResult || isRetesting) && (
            <RetestComparisonWorkspace
              comparison={comparisonResult || {
                baseline_audit_id: baselineAudit?.audit_id || '',
                new_audit_id: currentAudit?.audit_id || '',
                created_at: new Date().toISOString(),
                fixed_issues: [],
                remaining_issues: [],
                new_issues: [],
                regressions: [],
              }}
              baselineAudit={baselineAudit}
              retestAudit={currentAudit}
              selectedProject={selectedProject}
              isRetesting={isRetesting}
              retestStageIndex={auditStageIndex}
              onSelectImage={(imageUrl) => {
                setSelectedImage(imageUrl);
                setZoomIndex(2);
              }}
              onBackToResults={() => setActiveTab('audit')}
            />
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
        </div>
      )}

      {/* Screenshot Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 bg-background/90 backdrop-blur-md flex flex-col items-center justify-center p-4 md:p-6"
          onClick={() => setSelectedImage(null)}
        >
          {/* Lightbox Container */}
          <div
            className="relative max-w-5xl w-full max-h-[90vh] bg-surface-raised border border-border rounded-lg p-3 flex flex-col overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Floating Zoom Toolbar Header */}
            <div className="flex items-center justify-between gap-3 pb-3 mb-2 border-b border-border text-xs font-mono">
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setZoomIndex((prev) => Math.max(0, prev - 1))}
                  disabled={zoomIndex === 0}
                  className="p-1.5 rounded bg-surface hover:bg-background border border-border text-text-primary disabled:opacity-40 disabled:hover:bg-surface transition-colors flex items-center gap-1"
                  title="Zoom Out (-)"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="px-2.5 py-1 rounded bg-background border border-border font-bold text-accent min-w-[54px] text-center">
                  {ZOOM_LEVELS[zoomIndex]}%
                </span>
                <button
                  type="button"
                  onClick={() => setZoomIndex((prev) => Math.min(ZOOM_LEVELS.length - 1, prev + 1))}
                  disabled={zoomIndex === ZOOM_LEVELS.length - 1}
                  className="p-1.5 rounded bg-surface hover:bg-background border border-border text-text-primary disabled:opacity-40 disabled:hover:bg-surface transition-colors flex items-center gap-1"
                  title="Zoom In (+)"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setZoomIndex(2)}
                  className="p-1.5 px-2.5 rounded bg-surface hover:bg-background border border-border text-text-muted hover:text-text-primary transition-colors flex items-center gap-1.5 ml-1"
                  title="Reset Zoom (0)"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reset</span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[11px] text-text-muted hidden sm:inline">Use +/-/0 or Esc</span>
                <button
                  type="button"
                  onClick={() => setSelectedImage(null)}
                  className="p-1.5 rounded bg-surface hover:bg-background border border-border text-text-muted hover:text-text-primary transition-colors"
                  title="Close Lightbox (Esc)"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Scrollable Image Area */}
            <div className="overflow-auto flex-1 flex items-center justify-center p-2 min-h-[300px]">
              <img
                src={selectedImage}
                alt="Full Screenshot"
                className="max-w-none rounded transition-transform duration-150 ease-out origin-top-left"
                style={{
                  transform: `scale(${ZOOM_LEVELS[zoomIndex] / 100})`,
                }}
              />
            </div>
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
    </AppShell>
  );
};

export default App;
