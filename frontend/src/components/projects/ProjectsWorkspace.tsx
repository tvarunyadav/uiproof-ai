import React from 'react';
import {
  FolderKanban,
  Plus,
  Globe,
  Calendar,
  AlertCircle,
  PlaySquare,
  CheckCircle2,
} from 'lucide-react';
import { Project } from '../../types/audit';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

export interface ProjectsWorkspaceProps {
  projects: Project[];
  selectedProject?: Project | null;
  isLoading?: boolean;
  errorMessage?: string | null;
  onSelectProject: (project: Project | null) => void;
  onOpenCreateProjectModal: () => void;
  onNewAudit?: () => void;
  onRetry?: () => void;
}

export const ProjectsWorkspace: React.FC<ProjectsWorkspaceProps> = ({
  projects,
  selectedProject = null,
  isLoading = false,
  errorMessage = null,
  onSelectProject,
  onOpenCreateProjectModal,
  onRetry,
}) => {
  const formatShortId = (id: string) => (id.length > 8 ? `#${id.slice(0, 8)}` : `#${id}`);

  if (errorMessage) {
    return (
      <div className="p-6 max-w-6xl mx-auto font-sans">
        <Card className="p-8 border-status-error/30 bg-status-error/10 text-status-error flex flex-col items-center justify-center text-center gap-3 font-mono">
          <AlertCircle className="w-8 h-8 text-status-error" />
          <h3 className="text-sm font-bold uppercase">Unable to load project list</h3>
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
            <FolderKanban className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-text-primary tracking-wide font-mono uppercase">
              PROJECTS MANAGEMENT
            </h1>
            <p className="text-xs text-text-muted mt-0.5">
              Organize target web applications, baseline audits, and verification runs by project
            </p>
          </div>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={onOpenCreateProjectModal}
          className="font-mono text-xs flex items-center gap-2 shadow-glow"
        >
          <Plus className="w-4 h-4" />
          <span>Create Project</span>
        </Button>
      </div>

      {/* Default Workspace Pill Card */}
      <Card className="p-4 border-border bg-surface flex items-center justify-between flex-wrap gap-3 font-mono text-xs">
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded bg-background border border-border text-text-muted">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-text-primary">Default Workspace</span>
              <span className="text-[10px] text-text-muted">Global / Standalone Audits</span>
            </div>
            <span className="text-[11px] text-text-muted font-sans">
              Includes standalone audits and legacy audits with no assigned project ID.
            </span>
          </div>
        </div>

        <Button
          variant={selectedProject === null ? 'secondary' : 'outline'}
          size="sm"
          onClick={() => onSelectProject(null)}
          disabled={selectedProject === null}
          className="font-mono text-xs"
        >
          {selectedProject === null ? (
            <span className="flex items-center gap-1.5 text-status-success font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Active Workspace
            </span>
          ) : (
            <span>Select Workspace</span>
          )}
        </Button>
      </Card>

      {/* Projects List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-5 rounded-xl border border-border bg-surface animate-pulse flex flex-col gap-3">
              <div className="h-4 w-32 bg-surface-raised rounded" />
              <div className="h-4 w-48 bg-surface-raised rounded" />
              <div className="h-8 w-24 bg-surface-raised rounded mt-2" />
            </div>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center gap-3 border-dashed border-border bg-surface font-mono">
          <FolderKanban className="w-8 h-8 text-text-muted/60" />
          <h4 className="text-sm font-semibold text-text-primary">No Projects Created Yet</h4>
          <p className="text-xs text-text-muted max-w-sm font-sans leading-relaxed">
            Create a project to group related audits for specific target URLs, enable baseline comparison, and track team QA verification.
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={onOpenCreateProjectModal}
            className="mt-1 font-mono text-xs flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create First Project</span>
          </Button>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs font-mono text-text-muted px-1">
            <span>REGISTERED PROJECTS ({projects.length})</span>
            <span>Click project to filter audits</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((project) => {
              const isSelected = selectedProject?.project_id === project.project_id;

              return (
                <Card
                  key={project.project_id}
                  className={`p-5 flex flex-col gap-4 font-mono text-xs transition-all ${
                    isSelected
                      ? 'border-accent/40 bg-accent/5 ring-1 ring-accent/30'
                      : 'border-border bg-surface hover:bg-surface-raised'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-text-primary">{project.name}</h3>
                        <span className="text-[10px] text-text-muted bg-background px-2 py-0.5 rounded border border-border">
                          {formatShortId(project.project_id)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-text-secondary text-[11px] mt-0.5">
                        <Globe className="w-3.5 h-3.5 text-accent shrink-0" />
                        <code className="text-accent truncate font-mono" title={project.target_url}>
                          {project.target_url}
                        </code>
                      </div>
                    </div>

                    {isSelected && (
                      <span className="px-2 py-0.5 rounded bg-status-success/15 border border-status-success/30 text-status-success text-[10px] font-bold">
                        ACTIVE
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-text-muted pt-3 border-t border-border/80">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Created {new Date(project.created_at).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1 font-semibold text-text-primary bg-background px-2 py-0.5 rounded border border-border">
                      <PlaySquare className="w-3 h-3 text-accent" />
                      {project.audit_count ?? 0} Audits
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-1">
                    <Button
                      variant={isSelected ? 'secondary' : 'outline'}
                      size="sm"
                      onClick={() => onSelectProject(isSelected ? null : project)}
                      className="w-full font-mono text-xs justify-center"
                    >
                      {isSelected ? 'Selected (Click to Clear Filter)' : 'Select Project'}
                    </Button>
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
