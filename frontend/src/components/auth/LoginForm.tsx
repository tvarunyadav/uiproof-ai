import React, { useState } from 'react';
import { loginUser, getMeProfile, ApiError } from '../../services/api';
import { User } from '../../types/auth';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Loader2, LogIn, AlertCircle } from 'lucide-react';

interface LoginFormProps {
  onSuccess: (user: User) => void;
  onSwitchToRegister: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setError('Enter a valid email address.');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const tokenRes = await loginUser({ email: cleanEmail, password });
      localStorage.setItem('uiproof_token', tokenRes.access_token);
      const userProfile = await getMeProfile();
      onSuccess(userProfile);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message || 'Invalid credentials.');
      } else {
        setError(err.message || 'Authentication failed. Please try again.');
      }
      localStorage.removeItem('uiproof_token');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-error/10 border border-error/20 text-error text-sm p-3 rounded-lg flex items-center gap-2.5 animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-error shrink-0" />
          <span className="text-xs sm:text-sm font-medium">{error}</span>
        </div>
      )}

      <div>
        <label htmlFor="login-email" className="block text-xs font-semibold uppercase tracking-wider text-text-muted mb-1.5">
          Email Address
        </label>
        <Input
          id="login-email"
          type="email"
          placeholder="developer@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isLoading}
          required
          autoComplete="email"
          className="w-full bg-surface-raised border-border text-text-primary placeholder-text-muted focus:border-primary focus:ring-1 focus:ring-primary"
        />
      </div>

      <div>
        <label htmlFor="login-password" className="block text-xs font-semibold uppercase tracking-wider text-text-muted mb-1.5">
          Password
        </label>
        <Input
          id="login-password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          required
          autoComplete="current-password"
          className="w-full bg-surface-raised border-border text-text-primary placeholder-text-muted focus:border-primary focus:ring-1 focus:ring-primary"
        />
      </div>

      <Button
        type="submit"
        disabled={isLoading}
        className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white font-medium rounded-lg shadow-sm transition-all duration-150 flex items-center justify-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-white" />
            <span>Signing in...</span>
          </>
        ) : (
          <>
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </>
        )}
      </Button>

      <div className="pt-2 text-center">
        <p className="text-xs text-text-muted">
          Don't have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            disabled={isLoading}
            className="text-accent hover:underline font-medium transition-colors ml-1 focus:outline-none focus:ring-1 focus:ring-primary rounded"
          >
            Create account
          </button>
        </p>
      </div>
    </form>
  );
};
