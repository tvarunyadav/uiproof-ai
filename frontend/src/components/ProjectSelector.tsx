import React, { useState, useRef, useEffect } from 'react';
import { Folder, ChevronDown, Plus, Check, Globe } from 'lucide-react';
import { Project } from '../types/audit';

interface ProjectSelectorProps {
  projects: Project[];
  selectedProject: Project | null;
  onSelectProject: (project: Project | null) => void;
  onOpenCreateModal: () => void;
}

export const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  projects,
  selectedProject,
  onSelectProject,
  onOpenCreateModal,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-200 hover:text-white hover:border-slate-700 transition-all"
      >
        <Folder className="w-3.5 h-3.5 text-indigo-400" />
        <span className="max-w-[140px] truncate">
          {selectedProject ? selectedProject.name : 'All Projects'}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl z-50 py-1.5 overflow-hidden">
          <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
            Workspace Projects
          </div>

          <div className="max-h-60 overflow-y-auto">
            <button
              onClick={() => {
                onSelectProject(null);
                setIsOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-slate-800/60 transition-colors ${
                selectedProject === null ? 'text-indigo-400 bg-indigo-500/10 font-medium' : 'text-slate-300'
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <Globe className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="truncate">All Projects</span>
              </div>
              {selectedProject === null && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />}
            </button>

            {projects.map((proj) => {
              const isSelected = selectedProject?.project_id === proj.project_id;
              return (
                <button
                  key={proj.project_id}
                  onClick={() => {
                    onSelectProject(proj);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-slate-800/60 transition-colors ${
                    isSelected ? 'text-indigo-400 bg-indigo-500/10 font-medium' : 'text-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate pr-2">
                    <Folder className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span className="truncate">{proj.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="px-1.5 py-0.5 text-[10px] rounded bg-slate-800 text-slate-400 font-mono">
                      {proj.audit_count}
                    </span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                  </div>
                </button>
              );
            })}
          </div>

          <div className="border-t border-slate-800/80 mt-1 pt-1 px-1.5">
            <button
              onClick={() => {
                setIsOpen(false);
                onOpenCreateModal();
              }}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 rounded-lg transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create New Project</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
