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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center p-4 sm:p-6 font-sans antialiased relative overflow-hidden">
      {/* Background ambient lighting glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/2 -translate-x-1/2 translate-y-1/2 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl mb-4 text-indigo-400 shadow-inner">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
            UIProof AI
            <Sparkles className="w-4 h-4 text-indigo-400" />
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Automated Visual QA & IDOR-Protected Endpoint Verification
          </p>
        </div>

        {/* External session / auth error banner */}
        {externalError && (
          <div className="mb-4 bg-amber-950/40 border border-amber-800/50 text-amber-300 text-sm p-3.5 rounded-xl flex items-center gap-3 animate-fadeIn">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
            <span className="text-xs sm:text-sm">{externalError}</span>
          </div>
        )}

        {/* Auth Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl shadow-2xl p-6 sm:p-8 backdrop-blur-md">
          {/* Mode Selector Tabs */}
          <div className="flex border-b border-slate-800 mb-6 pb-2">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`flex-1 py-2 text-sm font-medium transition-colors border-b-2 text-center -mb-2.5 ${
                mode === 'login'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={`flex-1 py-2 text-sm font-medium transition-colors border-b-2 text-center -mb-2.5 ${
                mode === 'register'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
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
        <div className="mt-8 text-center text-xs text-slate-500">
          UIProof AI &copy; 2026 &bull; Secure JWT Authentication & Ownership Checks
        </div>
      </div>
    </div>
  );
};
