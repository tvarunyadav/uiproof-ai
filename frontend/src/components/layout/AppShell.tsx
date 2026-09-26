import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { Project } from '../../types/audit';
import { User } from '../../types/auth';

export interface AppShellProps {
  children: React.ReactNode;
  activeNav?: 'dashboard' | 'audits' | 'projects' | 'history';
  onNavSelect?: (nav: 'dashboard' | 'audits' | 'projects' | 'history') => void;
  onNewAudit?: () => void;
  projects?: Project[];
  selectedProject?: Project | null;
  onSelectProject?: (project: Project | null) => void;
  onOpenCreateProjectModal?: () => void;
  historyCount?: number;
  onToggleHistory?: () => void;
  isHistoryOpen?: boolean;
  currentUser?: User | null;
  onLogout?: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeNav = 'audits',
  onNavSelect,
  onNewAudit,
  projects = [],
  selectedProject = null,
  onSelectProject,
  onOpenCreateProjectModal,
  historyCount = 0,
  onToggleHistory,
  isHistoryOpen = false,
  currentUser = null,
  onLogout,
}) => {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const navTitles: Record<string, string> = {
    audits: 'Audit Workspace',
    dashboard: 'Dashboard Overview',
    projects: 'Project Management',
    history: 'Audit History',
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-row font-sans antialiased">
      {/* Sidebar */}
      <Sidebar
        activeNav={activeNav}
        onNavSelect={onNavSelect}
        onNewAudit={onNewAudit}
        projects={projects}
        selectedProject={selectedProject}
        onSelectProject={onSelectProject}
        onOpenCreateProjectModal={onOpenCreateProjectModal}
        historyCount={historyCount}
        currentUser={currentUser}
        onLogout={onLogout}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* TopBar */}
        <TopBar
          title={navTitles[activeNav] || 'Audit Workspace'}
          projects={projects}
          selectedProject={selectedProject}
          onSelectProject={onSelectProject}
          onOpenCreateProjectModal={onOpenCreateProjectModal}
          historyCount={historyCount}
          onToggleHistory={onToggleHistory}
          isHistoryOpen={isHistoryOpen}
          currentUser={currentUser}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
        />

        {/* Page Content Container */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
