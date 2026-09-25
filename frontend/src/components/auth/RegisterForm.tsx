import React, { useState } from 'react';
import { registerUser, loginUser, getMeProfile, ApiError } from '../../services/api';
import { User } from '../../types/auth';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Loader2, UserPlus, AlertCircle } from 'lucide-react';

interface RegisterFormProps {
  onSuccess: (user: User) => void;
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setError('Please enter a valid email address.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);

    try {
      // 1. Register new user
      await registerUser({ email: cleanEmail, password });

      // 2. Automatically login after successful registration
      const tokenRes = await loginUser({ email: cleanEmail, password });
      localStorage.setItem('uiproof_token', tokenRes.access_token);

      // 3. Fetch user profile
      const userProfile = await getMeProfile();
      onSuccess(userProfile);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'Registration failed. Please try again.');
      }
      localStorage.removeItem('uiproof_token');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-rose-950/40 border border-rose-800/50 text-rose-300 text-sm p-3 rounded-lg flex items-center gap-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
          Email Address
        </label>
        <Input
          type="email"
          placeholder="developer@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isLoading}
          required
          autoComplete="email"
          className="w-full bg-slate-900 border-slate-800 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
          Password (min. 8 characters)
        </label>
        <Input
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          required
          minLength={8}
          autoComplete="new-password"
          className="w-full bg-slate-900 border-slate-800 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
          Confirm Password
        </label>
        <Input
          type="password"
          placeholder="••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          disabled={isLoading}
          required
          minLength={8}
          autoComplete="new-password"
          className="w-full bg-slate-900 border-slate-800 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <Button
        type="submit"
        disabled={isLoading}
        className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg shadow-sm transition-all duration-150 flex items-center justify-center gap-2 text-sm"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-white" />
            <span>Creating account...</span>
          </>
        ) : (
          <>
            <UserPlus className="w-4 h-4" />
            <span>Create Account</span>
          </>
        )}
      </Button>

      <div className="pt-2 text-center">
        <p className="text-xs text-slate-400">
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            disabled={isLoading}
            className="text-indigo-400 hover:text-indigo-300 font-medium underline underline-offset-2 transition-colors ml-1"
          >
            Sign in
          </button>
        </p>
      </div>
    </form>
  );
};
