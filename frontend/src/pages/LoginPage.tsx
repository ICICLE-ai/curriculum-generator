import React, { useState, useEffect } from 'react';
import { parseJwt, type DecodedTapisJWT } from '../utils/jwt';
import { setStoredToken, setStoredRefreshToken } from '../utils/storage';
import { getTapisApiUrl } from '../utils/tapisJobs';
import { TokenLoginForm, CredentialsLoginForm } from '../components/login';

interface LoginPageProps {
  onLoginSuccess: (token: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [tokenInput, setTokenInput] = useState<string>('');
  const [decodedInfo, setDecodedInfo] = useState<DecodedTapisJWT | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Quick Generator State
  const [showGenerator, setShowGenerator] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('');
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
            Smart Curriculum Designer Portal
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
            Connect with your ICICLE Tapis session or institutional CILogon token
          </p>
        </div>

        {/* Token Input Form */}
        <TokenLoginForm
          tokenInput={tokenInput}
          setTokenInput={setTokenInput}
          decodedInfo={decodedInfo}
          errorMsg={errorMsg}
          onSubmit={handleConnect}
        />

        {/* Divider / Toggle Generator */}
        <CredentialsLoginForm
          showGenerator={showGenerator}
          setShowGenerator={setShowGenerator}
          username={username}
          setUsername={setUsername}
          password={password}
          setPassword={setPassword}
          isGenerating={isGenerating}
          genError={genError}
          onSubmit={handleGenerateToken}
        />
      </div>
    </div>
  );
};
