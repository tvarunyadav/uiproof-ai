import React from 'react';
import { Monitor, Smartphone, Check } from 'lucide-react';

export interface ViewportSelectorProps {
  selectedViewports: string[];
  onToggleViewport: (viewport: string) => void;
  disabled?: boolean;
}

export const ViewportSelector: React.FC<ViewportSelectorProps> = ({
  selectedViewports,
  onToggleViewport,
  disabled = false,
}) => {
  const viewports = [
    {
      id: 'desktop',
      label: 'Desktop',
      dimensions: '1440 × 900',
      icon: Monitor,
    },
    {
      id: 'mobile',
      label: 'Mobile',
      dimensions: '390 × 844',
      icon: Smartphone,
    },
  ];

  return (
    <div className="flex items-center gap-2">
      {viewports.map((vp) => {
        const isSelected = selectedViewports.includes(vp.id);
        const Icon = vp.icon;

        return (
          <button
            key={vp.id}
            type="button"
            disabled={disabled}
            onClick={() => onToggleViewport(vp.id)}
            className={`px-3 py-2 rounded text-xs font-mono flex items-center gap-2.5 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none ${
              isSelected
                ? 'bg-surface-raised text-text-primary border border-accent/50 shadow-subtle'
                : 'bg-background text-text-muted hover:text-text-primary border border-border hover:border-border-strong'
            }`}
          >
            <div className={`p-1 rounded ${isSelected ? 'bg-accent/20 text-accent' : 'bg-surface-raised text-text-muted'}`}>
              <Icon className="w-3.5 h-3.5" />
            </div>
            <div className="flex flex-col text-left">
              <div className="flex items-center gap-1.5 font-semibold leading-tight">
                <span>{vp.label}</span>
                {isSelected && <Check className="w-3 h-3 text-accent" />}
              </div>
              <span className="text-[10px] text-text-muted leading-tight font-mono">
                {vp.dimensions}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
};
