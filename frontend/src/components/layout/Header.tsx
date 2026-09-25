import React, { useEffect, useState } from 'react';
import { ShieldCheck, Activity, Terminal, History } from 'lucide-react';
import { checkBackendHealth } from '../../services/api';
import { Project } from '../../types/audit';
import { ProjectSelector } from '../ProjectSelector';

interface HeaderProps {
  projects?: Project[];
  selectedProject?: Project | null;
  onSelectProject?: (project: Project | null) => void;
  onOpenCreateProjectModal?: () => void;
  onOpenHistory?: () => void;
  historyCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  projects = [],
  selectedProject = null,
  onSelectProject,
  onOpenCreateProjectModal,
  onOpenHistory,
  historyCount = 0,
}) => {
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  useEffect(() => {
    checkBackendHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  return (
    <header className="h-14 border-b border-border bg-surface/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-accent/10 border border-accent/30 flex items-center justify-center text-accent">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm tracking-tight text-text-primary">UIProof</span>
            <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-accent/20 text-accent font-medium">AI</span>
          </div>
        </div>

        {onSelectProject && onOpenCreateProjectModal && (
          <div className="hidden sm:block pl-2 border-l border-slate-800">
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
        {onOpenHistory && (
          <button
            onClick={onOpenHistory}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-colors"
          >
            <History className="w-3.5 h-3.5 text-indigo-400" />
            <span>History</span>
            {historyCount > 0 && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-indigo-500/20 text-indigo-300 text-[10px] font-mono font-semibold">
                {historyCount}
              </span>
            )}
          </button>
        )}

        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-surface-raised border border-border">
          <span className="text-text-muted">API Status:</span>
          {backendStatus === 'online' && (
            <span className="flex items-center gap-1.5 text-status-success font-mono font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse" />
              Online (v0.1.0)
            </span>
          )}
          {backendStatus === 'offline' && (
            <span className="flex items-center gap-1.5 text-status-error font-mono font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-status-error" />
              Offline
            </span>
          )}
          {backendStatus === 'checking' && (
            <span className="flex items-center gap-1.5 text-text-muted font-mono">
              <Activity className="w-3 h-3 animate-spin" />
              Checking...
            </span>
          )}
        </div>

        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-text-muted hover:text-text-primary transition-colors font-mono"
        >
          <Terminal className="w-3.5 h-3.5" />
          Docs
        </a>
      </div>
    </header>
  );
};
