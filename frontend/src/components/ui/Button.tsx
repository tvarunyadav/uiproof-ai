import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-150 rounded cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-accent focus:ring-offset-1 focus:ring-offset-background active:scale-[0.98]';
  
  const sizeStyles = {
    sm: 'px-2.5 py-1 text-xs gap-1.5 h-7',
    md: 'px-3.5 py-1.5 text-xs font-semibold gap-2 h-9',
    lg: 'px-5 py-2.5 text-sm font-semibold gap-2.5 h-11',
  };

  const variantStyles = {
    primary: 'bg-accent text-white hover:bg-accent-hover shadow-subtle border border-accent-hover/30',
    secondary: 'bg-surface-raised text-text-primary hover:bg-surface-hover border border-border hover:border-border-strong',
    outline: 'bg-transparent text-text-primary hover:bg-surface-raised border border-border hover:border-border-strong',
    ghost: 'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-raised',
    danger: 'bg-status-error/10 text-status-error hover:bg-status-error/20 border border-status-error/30',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <svg className="w-3.5 h-3.5 animate-spin text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading...
        </span>
      ) : (
        children
      )}
    </button>
  );
};
