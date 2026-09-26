import React, { useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { User } from '../../types/auth';
import { ShieldCheck, Sparkles, AlertCircle } from 'lucide-react';

interface AuthContainerProps {
  onSuccess: (user: User) => void;
  initialMode?: 'login' | 'register';
  externalError?: string | null;
}

export const AuthContainer: React.FC<AuthContainerProps> = ({
  onSuccess,
  initialMode = 'login',
  externalError = null,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col justify-center items-center p-4 sm:p-6 font-sans antialiased relative overflow-hidden">
      {/* Background ambient lighting glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/2 -translate-x-1/2 translate-y-1/2 w-80 h-80 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3 bg-primary/10 border border-primary/20 rounded-2xl mb-4 text-primary shadow-inner">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary flex items-center justify-center gap-2">
            UIProof AI
            <Sparkles className="w-4 h-4 text-primary" />
          </h1>
          <p className="text-sm text-text-muted mt-1.5">
            Continue to your website QA workspace.
          </p>
        </div>

        {/* External session / auth error banner */}
        {externalError && (
          <div className="mb-4 bg-warning/10 border border-warning/20 text-warning text-sm p-3.5 rounded-xl flex items-center gap-3 animate-fadeIn">
            <AlertCircle className="w-5 h-5 text-warning shrink-0" />
            <span className="text-xs sm:text-sm font-medium">{externalError}</span>
          </div>
        )}

        {/* Auth Card */}
        <div className="bg-surface border border-border rounded-2xl shadow-2xl p-6 sm:p-8 backdrop-blur-md">
          {/* Mode Selector Tabs */}
          <div className="flex border-b border-border mb-6 pb-2">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`flex-1 py-2 text-sm font-medium transition-colors border-b-2 text-center -mb-2.5 ${
                mode === 'login'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={`flex-1 py-2 text-sm font-medium transition-colors border-b-2 text-center -mb-2.5 ${
                mode === 'register'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Form Content */}
          {mode === 'login' ? (
            <LoginForm
              onSuccess={onSuccess}
              onSwitchToRegister={() => setMode('register')}
            />
          ) : (
            <RegisterForm
              onSuccess={onSuccess}
              onSwitchToLogin={() => setMode('login')}
            />
          )}
        </div>

        {/* Footer info */}
        <div className="mt-8 text-center text-xs text-text-muted font-mono">
          UIProof AI &copy; 2026 &bull; Secure JWT Authentication
        </div>
      </div>
    </div>
  );
};
