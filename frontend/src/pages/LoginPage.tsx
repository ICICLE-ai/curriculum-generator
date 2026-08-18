import React, { useState, useEffect } from 'react';
import { parseJwt, formatTimeRemaining, type DecodedTapisJWT } from '../utils/jwt';
import { setStoredToken, setStoredRefreshToken } from '../utils/storage';
import { getTapisApiUrl } from '../utils/tapisJobs';

interface LoginPageProps {
  onLoginSuccess: (token: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [tokenInput, setTokenInput] = useState<string>('');
  const [decodedInfo, setDecodedInfo] = useState<DecodedTapisJWT | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Quick Generator State
  const [showGenerator, setShowGenerator] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('seh.1@osu.edu');
  const [password, setPassword] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Auto-decode input token
  useEffect(() => {
    if (!tokenInput.trim()) {
      setDecodedInfo(null);
      setErrorMsg(null);
      return;
    }

    const parsed = parseJwt(tokenInput);
    setDecodedInfo(parsed);
    if (!parsed || !parsed.isValid) {
      setErrorMsg('Invalid JWT format. Must contain 3 base64-encoded segments.');
    } else if (parsed.isExpired) {
      setErrorMsg(`Token is expired (${parsed.formattedExpiresAt}). Please provide an active token.`);
    } else {
      setErrorMsg(null);
    }
  }, [tokenInput]);

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim()) {
      setErrorMsg('Please enter a Tapis access token.');
      return;
    }

    const parsed = parseJwt(tokenInput);
    if (!parsed || !parsed.isValid) {
      setErrorMsg('Invalid JWT token format.');
      return;
    }

    if (parsed.isExpired) {
      setErrorMsg('Cannot connect with an expired token. Please refresh or regenerate.');
      return;
    }

    // Persist token
    setStoredToken(tokenInput.trim());
    onLoginSuccess(tokenInput.trim());
  };

  const handleGenerateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenError(null);
    setIsGenerating(true);

    try {
      const requestUrl = getTapisApiUrl('/v3/tokens');

      const payload = {
        username: username.trim(),
        password: password,
        grant_type: 'password',
        access_token_ttl_utc: 14400, // 4 hours
        generate_refresh_token: true,
        refresh_token_ttl_utc: 2592000, // 30 days
      };

      const resp = await fetch(requestUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const errorText = await resp.text();
        throw new Error(`Authentication failed (${resp.status}): ${errorText}`);
      }

      const resJson = await resp.json();
      const newAccess = resJson?.result?.access_token?.access_token;
      const newRefresh = resJson?.result?.refresh_token?.refresh_token;

      if (!newAccess) {
        throw new Error('Response did not contain an access_token.');
      }

      setTokenInput(newAccess);
      setStoredToken(newAccess);
      if (newRefresh) {
        setStoredRefreshToken(newRefresh);
      }

      onLoginSuccess(newAccess);
    } catch (err: unknown) {
      setGenError(err instanceof Error ? err.message : 'Unknown generation error occurred.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem 1rem',
        background: 'var(--bg-main)',
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '560px',
          padding: '2.5rem 2rem',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--border-strong)',
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--accent-primary-subtle)',
              color: 'var(--accent-primary)',
              marginBottom: '1rem',
            }}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
            DigitalAgEdu Portal
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
            Connect to ICICLE Tapis Supercomputing Infrastructure
          </p>
        </div>

        {/* Token Input Form */}
        <form onSubmit={handleConnect}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label
              htmlFor="tapis-token-input"
              style={{
                display: 'block',
                fontSize: '0.85rem',
                fontWeight: 600,
                marginBottom: '0.5rem',
                color: 'var(--text-primary)',
              }}
            >
              Tapis JWT Access Token
            </label>
            <textarea
              id="tapis-token-input"
              rows={4}
              className="code-textarea"
              placeholder="Paste your active eyJhbGci... Tapis access token here"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              style={{
                width: '100%',
                fontSize: '0.8rem',
                lineHeight: '1.4',
                borderColor: errorMsg ? 'var(--accent-rose)' : decodedInfo?.isValid ? 'var(--accent-emerald)' : undefined,
              }}
            />
          </div>

          {/* Validation Feedback Card */}
          {decodedInfo && decodedInfo.isValid && !decodedInfo.isExpired && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-emerald-subtle)',
                border: '1px solid var(--accent-emerald-border)',
                marginBottom: '1.25rem',
                fontSize: '0.8rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>Valid Tapis Session</span>
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
                  {formatTimeRemaining(decodedInfo.expiresInSeconds)}
                </span>
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                User: <strong>{decodedInfo.payload['tapis/username'] || decodedInfo.payload.sub || 'Unknown'}</strong> | Tenant: <strong>{decodedInfo.payload['tapis/tenant_id'] || 'icicleai'}</strong>
              </div>
            </div>
          )}

          {errorMsg && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-rose-subtle)',
                border: '1px solid var(--accent-rose)',
                color: 'var(--accent-rose)',
                fontSize: '0.8rem',
                marginBottom: '1.25rem',
              }}
            >
              {errorMsg}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.75rem', fontSize: '0.95rem', fontWeight: 600 }}
            disabled={!tokenInput.trim() || !!errorMsg}
          >
            Connect & Enter Portal
          </button>
        </form>

        {/* Divider / Toggle Generator */}
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
            <form onSubmit={handleGenerateToken} style={{ marginTop: '1.25rem' }}>
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
                  placeholder="e.g. seh.1@osu.edu"
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
      </div>
    </div>
  );
};
