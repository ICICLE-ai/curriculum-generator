import React, { useState, useEffect } from 'react';
import { GraduationCap } from 'lucide-react';
import { parseJwt, type DecodedTapisJWT } from '../utils/jwt';
import { setStoredToken, setStoredRefreshToken } from '../utils/storage';
import { getTapisApiUrl } from '../services/tapis';
import { TokenLoginForm, CredentialsLoginForm } from '../components/login';

interface LoginPageProps {
  onLoginSuccess: (token: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [tokenInput, setTokenInput] = useState<string>('');
  const [decodedInfo, setDecodedInfo] = useState<DecodedTapisJWT | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [showGenerator, setShowGenerator] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [genError, setGenError] = useState<string | null>(null);

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

    setStoredToken(tokenInput.trim());
    onLoginSuccess(tokenInput.trim());
  };

  const handleGenerateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenError(null);
    setIsGenerating(true);

    try {
      const resp = await fetch(getTapisApiUrl('/v3/tokens'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.trim(),
          password,
          grant_type: 'password',
          access_token_ttl_utc: 14400,
          generate_refresh_token: true,
          refresh_token_ttl_utc: 2592000,
        }),
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
    <div className="login-shell">
      <div className="card login-card">
        <div className="login-header">
          <div className="login-mark" aria-hidden="true">
            <GraduationCap size={24} />
          </div>
          <h1 className="page-title">Smart Curriculum Designer</h1>
          <p className="muted">
            Sign in with your ICICLE Tapis session or institutional CILogon token.
          </p>
        </div>

        <TokenLoginForm
          tokenInput={tokenInput}
          setTokenInput={setTokenInput}
          decodedInfo={decodedInfo}
          errorMsg={errorMsg}
          onSubmit={handleConnect}
        />

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
