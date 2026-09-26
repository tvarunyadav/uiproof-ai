import React from 'react';
import {
  ShieldCheck,
  Plus,
  LayoutDashboard,
  PlaySquare,
  FolderKanban,
  History,
  User as UserIcon,
  LogOut,
  X,
  ChevronRight,
  FolderPlus,
} from 'lucide-react';
import { Project } from '../../types/audit';
import { User } from '../../types/auth';

export interface SidebarProps {
  activeNav?: 'dashboard' | 'audits' | 'projects' | 'history';
  onNavSelect?: (nav: 'dashboard' | 'audits' | 'projects' | 'history') => void;
  onNewAudit?: () => void;
  projects?: Project[];
  selectedProject?: Project | null;
  onSelectProject?: (project: Project | null) => void;
  onOpenCreateProjectModal?: () => void;
  historyCount?: number;
  currentUser?: User | null;
  onLogout?: () => void;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

interface NavItem {
  id: 'dashboard' | 'audits' | 'projects' | 'history';
  label: string;
  icon: React.ElementType;
  count?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeNav = 'audits',
  onNavSelect,
  onNewAudit,
  projects = [],
  selectedProject = null,
  onSelectProject,
  onOpenCreateProjectModal,
  historyCount = 0,
  currentUser = null,
  onLogout,
  isOpenMobile = false,
  onCloseMobile,
}) => {
  const navItems: NavItem[] = [
    { id: 'audits', label: 'Audits', icon: PlaySquare },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'projects', label: 'Projects', icon: FolderKanban, count: projects.length },
    { id: 'history', label: 'Audit History', icon: History, count: historyCount },
  ];

  const sidebarContent = (
    <aside className="w-60 h-full bg-surface border-r border-border flex flex-col justify-between shrink-0 select-none">
      {/* Top Header & Branding */}
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-accent/10 border border-accent/30 flex items-center justify-center text-accent shadow-subtle">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-sm tracking-tight text-text-primary">UIProof</span>
                <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-accent/20 text-accent font-semibold">AI</span>
              </div>
              <span className="text-[10px] font-mono text-text-muted">QA & Fix Verification</span>
            </div>
          </div>
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-1 rounded text-text-muted hover:text-text-primary hover:bg-surface-raised"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Primary Action Button */}
        {onNewAudit && (
          <button
            onClick={() => {
              onNewAudit();
              if (onNavSelect) onNavSelect('audits');
              if (onCloseMobile) onCloseMobile();
            }}
            className="w-full h-9 px-3 rounded bg-accent hover:bg-accent-hover text-white text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-subtle border border-accent-hover/30 active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>New Audit</span>
          </button>
        )}

        {/* Active Project Context */}
        {selectedProject ? (
          <div className="p-2.5 rounded bg-surface-raised border border-border/80 flex flex-col gap-1">
            <div className="flex items-center justify-between text-[10px] font-mono text-text-muted">
              <span>ACTIVE PROJECT</span>
              <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
            </div>
            <div className="flex items-center justify-between text-xs font-medium text-text-primary truncate">
              <span className="truncate">{selectedProject.name}</span>
              {onSelectProject && (
                <button
                  onClick={() => onSelectProject(null)}
                  className="text-[10px] text-accent hover:underline font-mono ml-1 shrink-0"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        ) : (
          onOpenCreateProjectModal && (
            <button
              onClick={onOpenCreateProjectModal}
              className="w-full px-2.5 py-1.5 rounded border border-dashed border-border text-text-muted hover:text-text-primary hover:border-border-strong text-xs font-mono flex items-center justify-center gap-2 transition-colors"
            >
              <FolderPlus className="w-3.5 h-3.5 text-accent" />
              <span>+ Create Project</span>
            </button>
          )
        )}

        {/* Navigation List */}
        <nav className="flex flex-col gap-1 mt-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (onNavSelect) onNavSelect(item.id);
                  if (onCloseMobile) onCloseMobile();
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-surface-raised text-text-primary border border-border-strong shadow-subtle'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-raised/50 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-accent' : 'text-text-muted'}`} />
                  <span>{item.label}</span>
                </div>
                {item.count !== undefined && item.count > 0 && (
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-accent/20 text-accent font-semibold' : 'bg-surface-raised text-text-muted'
                  }`}>
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Footer Area */}
      <div className="p-4 border-t border-border flex flex-col gap-2 bg-surface-raised/20">
        {currentUser ? (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 px-2 py-1.5 rounded bg-surface-raised border border-border text-xs">
              <UserIcon className="w-3.5 h-3.5 text-accent shrink-0" />
              <span className="font-mono text-[11px] text-text-primary truncate" title={currentUser.email}>
                {currentUser.email}
              </span>
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-text-muted hover:text-status-error hover:bg-status-error/10 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </div>
                <ChevronRight className="w-3 h-3" />
              </button>
            )}
          </div>
        ) : (
          <div className="text-[11px] font-mono text-text-muted text-center py-1">
            Not Authenticated
          </div>
        )}
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <div className="hidden lg:block h-screen sticky top-0 z-40">
        {sidebarContent}
      </div>

      {/* Mobile Slide-over Drawer */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobile}
          />
          <div className="relative z-10 h-full">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
