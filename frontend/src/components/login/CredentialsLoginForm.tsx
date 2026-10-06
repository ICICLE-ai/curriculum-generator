import React from 'react';

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
    <div style={{ marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
      <button
        type="button"
        onClick={() => setShowGenerator(!showGenerator)}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--accent-primary)',
          fontSize: '0.85rem',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          gap: '0.5rem',
        }}
      >
        {showGenerator ? 'Hide Credentials Generator' : 'Generate Token via ICICLE Credentials'}
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{
            transform: showGenerator ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s ease',
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {showGenerator && (
        <form onSubmit={onSubmit} style={{ marginTop: '1.25rem' }}>
          <div style={{ marginBottom: '0.75rem' }}>
            <label
              htmlFor="gen-username"
              style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}
            >
              Tapis / Globus Username
            </label>
            <input
              id="gen-username"
              type="text"
              className="text-input"
              style={{ width: '100%' }}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. username@institution.edu"
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label
              htmlFor="gen-password"
              style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}
            >
              Password
            </label>
            <input
              id="gen-password"
              type="password"
              className="text-input"
              style={{ width: '100%' }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your Tapis account password"
            />
          </div>

          {genError && (
            <div
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-rose-subtle)',
                color: 'var(--accent-rose)',
                fontSize: '0.75rem',
                marginBottom: '0.75rem',
              }}
            >
              {genError}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-secondary"
            style={{ width: '100%' }}
            disabled={isGenerating || !username.trim() || !password}
          >
            {isGenerating ? 'Authenticating with Tapis...' : 'Generate 4-Hour Access Token'}
          </button>
        </form>
      )}
    </div>
  );
};
