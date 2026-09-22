import React from 'react';

interface BadgeProps {
  variant?: 'critical' | 'high' | 'medium' | 'low' | 'info' | 'success' | 'neutral';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  className = '',
}) => {
  const variantStyles = {
    critical: 'bg-status-error/10 text-status-error border-status-error/20',
    high: 'bg-status-warning/10 text-status-warning border-status-warning/20',
    medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    low: 'bg-status-info/10 text-status-info border-status-info/20',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    success: 'bg-status-success/10 text-status-success border-status-success/20',
    neutral: 'bg-surface-raised text-text-muted border-border',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium rounded border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
