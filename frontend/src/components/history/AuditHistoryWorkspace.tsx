import React, { useState } from 'react';
import {
  History,
  Search,
  ArrowRight,
  AlertCircle,
  Plus,
  X,
} from 'lucide-react';
import { AuditSummaryItem, Project } from '../../types/audit';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export interface AuditHistoryWorkspaceProps {
  historyAudits: AuditSummaryItem[];
  projects: Project[];
  selectedProject?: Project | null;
  isLoading?: boolean;
  errorMessage?: string | null;
  onSelectAudit: (auditId: string) => void;
  onNewAudit: () => void;
  onSelectProject: (project: Project | null) => void;
  onRetry?: () => void;
}

export const AuditHistoryWorkspace: React.FC<AuditHistoryWorkspaceProps> = ({
  historyAudits,
  projects,
  selectedProject = null,
  isLoading = false,
  errorMessage = null,
  onSelectAudit,
  onNewAudit,
  onSelectProject,
  onRetry,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [modeFilter, setModeFilter] = useState<'all' | 'remote' | 'local'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'running' | 'failed'>('all');

  const formatShortId = (id: string) => (id.length > 8 ? `#${id.slice(0, 8)}` : `#${id}`);

  // Client-side filtering on real API history response
  const filteredAudits = historyAudits.filter((audit) => {
    // 1. Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchId = audit.audit_id.toLowerCase().includes(q);
      const matchUrl = audit.target_url.toLowerCase().includes(q);
      if (!matchId && !matchUrl) return false;
    }

    // 2. Mode Filter
    if (modeFilter !== 'all' && audit.mode?.toLowerCase() !== modeFilter) {
      return false;
    }

    // 3. Status Filter
    if (statusFilter !== 'all' && audit.status?.toLowerCase() !== statusFilter) {
      return false;
    }

    return true;
  });

  const hasActiveFilters = searchQuery.trim() !== '' || modeFilter !== 'all' || statusFilter !== 'all';

  if (errorMessage) {
    return (
      <div className="p-6 max-w-6xl mx-auto font-sans">
        <Card className="p-8 border-status-error/30 bg-status-error/10 text-status-error flex flex-col items-center justify-center text-center gap-3 font-mono">
          <AlertCircle className="w-8 h-8 text-status-error" />
          <h3 className="text-sm font-bold uppercase">Unable to load audit history</h3>
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
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10 border border-accent/30 text-accent">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-text-primary tracking-wide font-mono uppercase">
              AUDIT HISTORY
            </h1>
            <p className="text-xs text-text-muted mt-0.5">
              Review and inspect previous website audits, Playwright evidence, and verification runs
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

      {/* Filter Toolbar */}
      <Card className="p-4 border-border bg-surface flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 font-mono text-xs">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by URL or Audit ID..."
            className="w-full pl-9 pr-8 py-2 rounded bg-background border border-border text-xs text-text-primary placeholder:text-text-muted/60 focus:outline-none focus:border-accent font-mono"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Dropdowns */}
        <div className="flex items-center gap-2 flex-wrap shrink-0">
          {/* Project Filter */}
          {projects.length > 0 && (
            <select
              value={selectedProject?.project_id || ''}
              onChange={(e) => {
                const proj = projects.find((p) => p.project_id === e.target.value) || null;
                onSelectProject(proj);
              }}
              className="bg-background text-text-primary text-xs font-mono rounded px-2.5 py-2 border border-border focus:outline-none focus:border-accent cursor-pointer max-w-[200px] truncate"
            >
              <option value="">All Projects</option>
              {projects.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}

          {/* Mode Filter */}
          <select
            value={modeFilter}
            onChange={(e) => setModeFilter(e.target.value as any)}
            className="bg-background text-text-primary text-xs font-mono rounded px-2.5 py-2 border border-border focus:outline-none focus:border-accent cursor-pointer"
          >
            <option value="all">All Modes</option>
            <option value="remote">Remote Mode</option>
            <option value="local">Local Mode</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="bg-background text-text-primary text-xs font-mono rounded px-2.5 py-2 border border-border focus:outline-none focus:border-accent cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="running">Running</option>
            <option value="failed">Failed</option>
          </select>

          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery('');
                setModeFilter('all');
                setStatusFilter('all');
              }}
              className="text-[11px] h-9 px-2.5 font-mono text-text-muted hover:text-text-primary"
            >
              Reset Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Audit History Table / List */}
      {isLoading ? (
        <div className="flex flex-col gap-3 font-mono text-xs">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="p-4 rounded-xl border border-border bg-surface animate-pulse flex items-center justify-between">
              <div className="h-4 w-40 bg-surface-raised rounded" />
              <div className="h-4 w-64 bg-surface-raised rounded" />
              <div className="h-4 w-20 bg-surface-raised rounded" />
            </div>
          ))}
        </div>
      ) : filteredAudits.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center gap-3 border-dashed border-border bg-surface font-mono">
          <History className="w-8 h-8 text-text-muted/60" />
          <h4 className="text-sm font-semibold text-text-primary">No Matching Audits Found</h4>
          <p className="text-xs text-text-muted max-w-sm font-sans leading-relaxed">
            {hasActiveFilters
              ? 'No audit history records match your search or filter parameters.'
              : 'Zero website audits have been recorded in the database history.'}
          </p>
          {hasActiveFilters ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery('');
                setModeFilter('all');
                setStatusFilter('all');
              }}
              className="mt-1 font-mono text-xs"
            >
              Clear Active Filters
            </Button>
          ) : (
            <Button
              variant="primary"
              size="sm"
              onClick={onNewAudit}
              className="mt-1 font-mono text-xs flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Run New Audit</span>
            </Button>
          )}
        </Card>
      ) : (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs font-mono text-text-muted px-2 py-1">
            <span>SHOWING {filteredAudits.length} AUDIT RECORD{filteredAudits.length !== 1 ? 'S' : ''}</span>
            <span>Sorted by newest created</span>
          </div>

          {/* Dense Developer Table Header (Desktop) */}
          <div className="hidden lg:grid grid-cols-12 gap-3 px-4 py-2 text-[11px] font-mono font-bold text-text-muted uppercase tracking-wider bg-surface-raised/40 rounded-t-lg border border-border border-b-0">
            <span className="col-span-2">Audit ID</span>
            <span className="col-span-4">Target URL</span>
            <span className="col-span-2">Mode & Status</span>
            <span className="col-span-2">Issues Detected</span>
            <span className="col-span-2 text-right">Created</span>
          </div>

          <div className="flex flex-col gap-2 lg:gap-1.5">
            {filteredAudits.map((audit) => {
              const proj = projects.find((p) => p.project_id === audit.project_id);

              return (
                <Card
                  key={audit.audit_id}
                  onClick={() => onSelectAudit(audit.audit_id)}
                  className="p-3.5 border-border bg-surface hover:bg-surface-raised transition-all cursor-pointer flex flex-col lg:grid lg:grid-cols-12 gap-3 items-start lg:items-center font-mono text-xs group"
                >
                  {/* Audit ID */}
                  <div className="lg:col-span-2 flex items-center gap-2">
                    <span className="font-bold text-text-primary bg-background px-2.5 py-1 rounded border border-border group-hover:border-accent/40">
                      {formatShortId(audit.audit_id)}
                    </span>
                  </div>

                  {/* Target URL & Project */}
                  <div className="lg:col-span-4 flex flex-col min-w-0 w-full">
                    <span className="text-text-primary font-bold truncate max-w-lg" title={audit.target_url}>
                      {audit.target_url}
                    </span>
                    {proj && (
                      <span className="text-[10px] text-accent font-semibold truncate mt-0.5">
                        Project: {proj.name}
                      </span>
                    )}
                  </div>

                  {/* Mode & Status */}
                  <div className="lg:col-span-2 flex items-center gap-2 flex-wrap">
                    <Badge variant={audit.status === 'completed' ? 'success' : audit.status === 'failed' ? 'critical' : 'warning'}>
                      {audit.status.toUpperCase()}
                    </Badge>
                    {audit.mode && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-background border border-border text-text-muted uppercase">
                        {audit.mode}
                      </span>
                    )}
                  </div>

                  {/* Issue Counts */}
                  <div className="lg:col-span-2 flex items-center gap-1.5">
                    <span className="text-text-muted text-[11px]">Total:</span>
                    <span className="font-bold text-text-primary bg-background px-2 py-0.5 rounded border border-border">
                      {audit.total_issues ?? 0}
                    </span>
                    {(audit.critical_count ?? 0) > 0 && (
                      <span className="text-status-error font-semibold text-[10px]">
                        ({audit.critical_count} critical)
                      </span>
                    )}
                  </div>

                  {/* Date & Action */}
                  <div className="lg:col-span-2 flex items-center justify-between lg:justify-end gap-2 w-full lg:w-auto border-t lg:border-t-0 border-border/60 pt-2 lg:pt-0">
                    <span className="text-[10px] text-text-muted shrink-0">
                      {new Date(audit.created_at).toLocaleDateString()}
                    </span>
                    <ArrowRight className="w-4 h-4 text-text-muted group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
