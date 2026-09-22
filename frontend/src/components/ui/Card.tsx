import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'raised' | 'interactive';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default: 'bg-surface border border-border',
    raised: 'bg-surface-raised border border-border shadow-subtle',
    interactive: 'bg-surface border border-border hover:border-accent/40 transition-colors duration-200 cursor-pointer',
  };

  return (
    <div
      className={`rounded-md p-5 text-text-primary ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
