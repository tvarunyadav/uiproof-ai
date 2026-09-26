import React, { useEffect, useState } from 'react';
import { Activity, Menu, History, User as UserIcon } from 'lucide-react';
import { checkBackendHealth } from '../../services/api';
import { Project } from '../../types/audit';
import { User } from '../../types/auth';
import { ProjectSelector } from '../ProjectSelector';

export interface TopBarProps {
  title?: string;
  projects?: Project[];
  selectedProject?: Project | null;
  onSelectProject?: (project: Project | null) => void;
  onOpenCreateProjectModal?: () => void;
  historyCount?: number;
  onToggleHistory?: () => void;
  isHistoryOpen?: boolean;
  currentUser?: User | null;
  onOpenMobileSidebar?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  title = 'Audit Workspace',
  projects = [],
  selectedProject = null,
  onSelectProject,
  onOpenCreateProjectModal,
  historyCount = 0,
  onToggleHistory,
  isHistoryOpen = false,
  currentUser = null,
  onOpenMobileSidebar,
}) => {
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  useEffect(() => {
    checkBackendHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  return (
    <header className="h-14 border-b border-border bg-surface/80 backdrop-blur-md px-4 lg:px-6 flex items-center justify-between sticky top-0 z-30 shrink-0">
      <div className="flex items-center gap-3">
        {onOpenMobileSidebar && (
          <button
            onClick={onOpenMobileSidebar}
            className="lg:hidden p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-raised border border-border"
            title="Open Menu"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <div className="flex items-center gap-2">
          <h1 className="text-xs font-semibold uppercase tracking-wider text-text-primary font-mono">
            {title}
          </h1>
        </div>

        {onSelectProject && onOpenCreateProjectModal && (
          <div className="hidden sm:block pl-3 border-l border-border">
            <ProjectSelector
              projects={projects}
              selectedProject={selectedProject}
              onSelectProject={onSelectProject}
              onOpenCreateModal={onOpenCreateProjectModal}
            />
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 text-xs">
        {onToggleHistory && (
          <button
            onClick={onToggleHistory}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border transition-all ${
              isHistoryOpen
                ? 'bg-accent/15 text-accent border-accent/40 font-medium'
                : 'bg-surface-raised border-border text-text-secondary hover:text-text-primary hover:border-border-strong'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">History</span>
            {historyCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-accent/20 text-accent text-[10px] font-mono font-semibold">
                {historyCount}
              </span>
            )}
          </button>
        )}

        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-surface-raised border border-border">
          <span className="text-text-muted text-[11px] hidden md:inline">API:</span>
          {backendStatus === 'online' && (
            <span className="flex items-center gap-1.5 text-status-success font-mono font-medium text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse" />
              Online
            </span>
          )}
          {backendStatus === 'offline' && (
            <span className="flex items-center gap-1.5 text-status-error font-mono font-medium text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-status-error" />
              Offline
            </span>
          )}
          {backendStatus === 'checking' && (
            <span className="flex items-center gap-1.5 text-text-muted font-mono text-[11px]">
              <Activity className="w-3 h-3 animate-spin text-accent" />
              Checking...
            </span>
          )}
        </div>

        {currentUser && (
          <div className="hidden xl:flex items-center gap-1.5 px-2 py-1 rounded bg-surface-raised border border-border text-[11px] font-mono text-text-muted">
            <UserIcon className="w-3 h-3 text-accent" />
            <span className="truncate max-w-[120px]">{currentUser.email}</span>
          </div>
        )}
      </div>
    </header>
  );
};
