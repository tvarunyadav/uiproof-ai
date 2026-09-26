import React from 'react';
import {
  LayoutDashboard,
  Plus,
  PlaySquare,
  History,
  FolderKanban,
  Globe,
  Shield,
  Calendar,
  AlertCircle,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { AuditSummaryItem, Project } from '../../types/audit';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export interface DashboardWorkspaceProps {
  projects: Project[];
  selectedProject?: Project | null;
  historyAudits: AuditSummaryItem[];
  isLoading?: boolean;
  errorMessage?: string | null;
  onNewAudit: () => void;
  onSelectAudit: (auditId: string) => void;
  onViewHistory: () => void;
  onViewProjects: () => void;
  onSelectProject: (project: Project | null) => void;
  onOpenCreateProjectModal: () => void;
  onRetry?: () => void;
}

export const DashboardWorkspace: React.FC<DashboardWorkspaceProps> = ({
  projects,
  selectedProject = null,
  historyAudits,
  isLoading = false,
  errorMessage = null,
  onNewAudit,
  onSelectAudit,
  onViewHistory,
  onViewProjects,
  onSelectProject,
  onOpenCreateProjectModal,
  onRetry,
}) => {
  const recentAudits = historyAudits.slice(0, 5);

  const formatShortId = (id: string) => (id.length > 8 ? `#${id.slice(0, 8)}` : `#${id}`);

  if (errorMessage) {
    return (
      <div className="p-6 max-w-6xl mx-auto font-sans">
        <Card className="p-8 border-status-error/30 bg-status-error/10 text-status-error flex flex-col items-center justify-center text-center gap-3 font-mono">
          <AlertCircle className="w-8 h-8 text-status-error" />
          <h3 className="text-sm font-bold uppercase">Unable to load dashboard data</h3>
          <p className="text-xs text-text-secondary max-w-md font-sans leading-relaxed">
            {errorMessage}
          </p>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="mt-2 text-xs font-mono border-status-error/40 text-status-error hover:bg-status-error/10"
            >
              Retry
            </Button>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto flex flex-col gap-6 font-sans">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10 border border-accent/30 text-accent">
            <LayoutDashboard className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-text-primary tracking-wide font-mono uppercase">
              DASHBOARD OVERVIEW
            </h1>
            <p className="text-xs text-text-muted mt-0.5">
              Monitor recent audits and quickly launch website quality verification runs
            </p>
          </div>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={onNewAudit}
          className="font-mono text-xs flex items-center gap-2 shadow-glow"
        >
          <Plus className="w-4 h-4" />
          <span>New Audit</span>
        </Button>
      </div>

      {/* Loading Skeleton */}
      {isLoading ? (
        <div className="flex flex-col gap-4 font-mono text-xs">
          <div className="p-4 rounded-xl border border-border bg-surface animate-pulse flex items-center justify-between">
            <div className="h-4 w-48 bg-surface-raised rounded" />
            <div className="h-4 w-24 bg-surface-raised rounded" />
          </div>
          <div className="p-6 rounded-xl border border-border bg-surface animate-pulse flex flex-col gap-3">
            <div className="h-4 w-32 bg-surface-raised rounded" />
            <div className="h-10 w-full bg-surface-raised rounded" />
            <div className="h-10 w-full bg-surface-raised rounded" />
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Current Active Project Card */}
          <Card className="p-5 border-border bg-surface flex flex-col gap-3">
            <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-border">
              <span className="font-mono font-bold text-xs text-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                <Shield className="w-4 h-4 text-accent" />
                ACTIVE PROJECT CONTEXT
              </span>
              <div className="flex items-center gap-2 font-mono text-xs">
                {projects.length > 0 && (
                  <button
                    type="button"
                    onClick={onViewProjects}
                    className="text-accent hover:underline text-[11px] cursor-pointer"
                  >
                    Manage Projects ({projects.length})
                  </button>
                )}
              </div>
            </div>

            {selectedProject ? (
              <div className="flex items-center justify-between flex-wrap gap-4 font-mono text-xs">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-text-primary">{selectedProject.name}</h3>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-status-success/10 text-status-success border border-status-success/30 font-semibold">
                      ACTIVE
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-text-muted text-[11px]">
                    <span className="flex items-center gap-1">
                      <Globe className="w-3 h-3 text-accent" />
                      Target: <code className="text-text-primary">{selectedProject.target_url}</code>
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-text-muted" />
                      Created: {new Date(selectedProject.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-muted bg-background px-3 py-1.5 rounded border border-border font-semibold">
                    {selectedProject.audit_count ?? historyAudits.length} Project Audits
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSelectProject(null)}
                    className="text-[11px] h-7 px-2 font-mono"
                  >
                    Clear Filter
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between flex-wrap gap-3 font-mono text-xs py-1">
                <div className="flex items-center gap-2 text-text-muted">
                  <span>No specific project selected (showing all workspace audits)</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onOpenCreateProjectModal}
                  className="text-xs h-7 px-2.5 font-mono text-accent border-accent/30 hover:bg-accent/10"
                >
                  + Create Project
                </Button>
              </div>
            )}
          </Card>

          {/* Recent Audits Section */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between font-mono">
              <span className="font-bold text-xs text-text-primary uppercase tracking-wider flex items-center gap-1.5">
                <History className="w-4 h-4 text-accent" />
                RECENT AUDITS ({recentAudits.length})
              </span>
              {historyAudits.length > 0 && (
                <button
                  type="button"
                  onClick={onViewHistory}
                  className="text-xs font-mono text-accent hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <span>View All History ({historyAudits.length})</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>

            {historyAudits.length === 0 ? (
              <Card className="flex flex-col items-center justify-center p-10 text-center gap-3 border-dashed border-border bg-surface font-mono">
                <PlaySquare className="w-8 h-8 text-text-muted/60" />
                <h4 className="text-sm font-semibold text-text-primary">No Audits Executed Yet</h4>
                <p className="text-xs text-text-muted max-w-sm font-sans leading-relaxed">
                  Run your first automated Playwright website audit to collect browser evidence, detect layout issues, and track quality verification history.
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onNewAudit}
                  className="mt-1 font-mono text-xs flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Run New Audit</span>
                </Button>
              </Card>
            ) : (
              <div className="flex flex-col gap-2">
                {recentAudits.map((audit) => (
                  <Card
                    key={audit.audit_id}
                    onClick={() => onSelectAudit(audit.audit_id)}
                    className="p-3.5 border-border bg-surface hover:bg-surface-raised transition-all cursor-pointer flex items-center justify-between flex-wrap gap-3 font-mono text-xs group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="font-bold text-text-primary bg-background px-2.5 py-1 rounded border border-border shrink-0 group-hover:border-accent/40">
                        {formatShortId(audit.audit_id)}
                      </span>

                      <div className="flex flex-col min-w-0">
                        <span className="text-text-primary font-bold truncate max-w-md" title={audit.target_url}>
                          {audit.target_url}
                        </span>
                        <div className="flex items-center gap-2 text-[10px] text-text-muted mt-0.5">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(audit.created_at).toLocaleString()}
                          </span>
                          {audit.mode && (
                            <span className="uppercase text-accent">[{audit.mode}]</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <Badge variant={audit.status === 'completed' ? 'success' : audit.status === 'failed' ? 'critical' : 'warning'}>
                        {audit.status.toUpperCase()}
                      </Badge>

                      <div className="flex items-center gap-1.5 bg-background px-2.5 py-1 rounded border border-border text-[11px]">
                        <span className="text-text-muted">Issues:</span>
                        <span className="font-bold text-text-primary">{audit.total_issues ?? 0}</span>
                        {(audit.critical_count ?? 0) > 0 && (
                          <span className="text-status-error font-semibold text-[10px]">
                            ({audit.critical_count} critical)
                          </span>
                        )}
                      </div>

                      <ArrowRight className="w-4 h-4 text-text-muted group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Quick Actions Panel */}
          <div className="flex flex-col gap-3 pt-2">
            <span className="font-mono font-bold text-xs text-text-primary uppercase tracking-wider">
              QUICK ACTIONS
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
              <button
                type="button"
                onClick={onNewAudit}
                className="p-4 rounded-xl border border-border bg-surface hover:bg-surface-raised hover:border-accent/40 transition-all text-left flex flex-col gap-2 cursor-pointer group"
              >
                <div className="flex items-center justify-between">
                  <PlaySquare className="w-4 h-4 text-accent" />
                  <ArrowRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent transition-colors" />
                </div>
                <span className="font-bold text-text-primary">Launch New Audit</span>
                <span className="text-[11px] font-sans text-text-muted">Run Playwright Chromium against any target URL.</span>
              </button>

              <button
                type="button"
                onClick={onViewHistory}
                className="p-4 rounded-xl border border-border bg-surface hover:bg-surface-raised hover:border-accent/40 transition-all text-left flex flex-col gap-2 cursor-pointer group"
              >
                <div className="flex items-center justify-between">
                  <History className="w-4 h-4 text-accent" />
                  <ArrowRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent transition-colors" />
                </div>
                <span className="font-bold text-text-primary">Audit History</span>
                <span className="text-[11px] font-sans text-text-muted">Filter, search, and inspect past audit runs.</span>
              </button>

              <button
                type="button"
                onClick={onViewProjects}
                className="p-4 rounded-xl border border-border bg-surface hover:bg-surface-raised hover:border-accent/40 transition-all text-left flex flex-col gap-2 cursor-pointer group"
              >
                <div className="flex items-center justify-between">
                  <FolderKanban className="w-4 h-4 text-accent" />
                  <ArrowRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent transition-colors" />
                </div>
                <span className="font-bold text-text-primary">Manage Projects</span>
                <span className="text-[11px] font-sans text-text-muted">Organize audits by project targets and baseline runs.</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
