import React from 'react';
import { ChevronDown } from 'lucide-react';

interface CredentialsLoginFormProps {
  showGenerator: boolean;
  setShowGenerator: (val: boolean) => void;
  username: string;
  setUsername: (val: string) => void;
  password: string;
  setPassword: (val: string) => void;
  isGenerating: boolean;
  genError: string | null;
  onSubmit: (e: React.FormEvent) => void;
}

export const CredentialsLoginForm: React.FC<CredentialsLoginFormProps> = ({
  showGenerator,
  setShowGenerator,
  username,
  setUsername,
  password,
  setPassword,
  isGenerating,
  genError,
  onSubmit,
}) => {
  return (
    <div className="divider-top" style={{ marginTop: 'var(--space-6)' }}>
      <button
        type="button"
        className="btn btn-ghost btn-full"
        onClick={() => setShowGenerator(!showGenerator)}
      >
        <span>{showGenerator ? 'Hide Credentials Login' : 'Sign in with ICICLE Credentials'}</span>
        <ChevronDown
          size={16}
          aria-hidden="true"
          style={{ transform: showGenerator ? 'rotate(180deg)' : undefined, transition: 'transform 150ms ease' }}
        />
      </button>

      {showGenerator && (
        <form onSubmit={onSubmit} className="stack" style={{ marginTop: 'var(--space-4)' }}>
          <div className="form-group">
            <label htmlFor="gen-username" className="form-label">
              Tapis / Globus Username
            </label>
            <input
              id="gen-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. username@institution.edu"
            />
          </div>

          <div className="form-group">
            <label htmlFor="gen-password" className="form-label">
              Password
            </label>
            <input
              id="gen-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your Tapis account password"
            />
          </div>

          {genError && (
            <div role="alert" className="alert alert-error">
              {genError}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-secondary btn-full"
            disabled={isGenerating || !username.trim() || !password}
          >
            {isGenerating ? 'Authenticating with Tapis...' : 'Generate Access Token'}
          </button>
        </form>
      )}
    </div>
  );
};
