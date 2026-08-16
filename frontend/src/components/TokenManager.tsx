import React, { useState, useEffect } from 'react';
import { parseJwt, formatTimeRemaining, type DecodedTapisJWT } from '../utils/jwt';

export const TokenManager: React.FC = () => {
  const [inputJwt, setInputJwt] = useState<string>('');
  const [decodedInfo, setDecodedInfo] = useState<DecodedTapisJWT | null>(null);

  // Configuration options (Strictly ICICLE AI)
  const [accessTokenTtl, setAccessTokenTtl] = useState<number>(14400); // 4 hours
  const [refreshTokenTtl, setRefreshTokenTtl] = useState<number>(2592000); // 30 days
  const [generateRefreshToken, setGenerateRefreshToken] = useState<boolean>(true);

  // Request State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Response Data
  const [resultAccessToken, setResultAccessToken] = useState<string | null>(null);
  const [resultRefreshToken, setResultRefreshToken] = useState<string | null>(null);
  const [decodedResultAccess, setDecodedResultAccess] = useState<DecodedTapisJWT | null>(null);

  // Copy Feedback
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Auto-decode input JWT on change
  useEffect(() => {
    if (!inputJwt.trim()) {
      setDecodedInfo(null);
      return;
    }
    const parsed = parseJwt(inputJwt);
    setDecodedInfo(parsed);
  }, [inputJwt]);

  // Decode result access token
  useEffect(() => {
    if (resultAccessToken) {
      setDecodedResultAccess(parseJwt(resultAccessToken));
    } else {
      setDecodedResultAccess(null);
    }
  }, [resultAccessToken]);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleCreateOrRefreshToken = async () => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    const isRefreshTokenInput = decodedInfo?.payload['tapis/token_type'] === 'refresh';

    try {
      const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const requestUrl = isLocalDev
        ? `/tapis-proxy/v3/tokens`
        : `https://icicleai.tapis.io/v3/tokens`;

      let response: Response;

      if (isRefreshTokenInput) {
        // Refresh token grant via PUT /v3/tokens
        const payload = {
          refresh_token: inputJwt.trim(),
        };

        response = await fetch(requestUrl, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
      } else {
        // Create token grant via POST /v3/tokens using current access token
        const payload = {
          token_tenant_id: 'icicleai',
          token_username: decodedInfo?.payload['tapis/username'],
          account_type: 'user',
          access_token_ttl: Number(accessTokenTtl),
          refresh_token_ttl: Number(refreshTokenTtl),
          generate_refresh_token: generateRefreshToken,
        };

        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };

        if (inputJwt.trim()) {
          headers['X-Tapis-Token'] = inputJwt.trim();
        }

        response = await fetch(requestUrl, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
        });
      }

      const resData = await response.json();

      if (!response.ok || resData.status !== 'success') {
        const message = resData.message || `HTTP ${response.status}: Failed to generate token.`;
        throw new Error(message);
      }

      const result = resData.result;
      const newAccessToken = result.access_token?.access_token || result.access_token;
      const newRefreshToken = result.refresh_token?.refresh_token || result.refresh_token;

      setResultAccessToken(newAccessToken || null);
      setResultRefreshToken(newRefreshToken || null);
      setSuccessMsg('Successfully generated new Tapis authentication tokens!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(
        `${msg} (Note: If this is a cross-origin CORS restriction, make sure you are running via Vite proxy at http://localhost:5173)`
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="token-manager-view">
      <div style={{ marginBottom: '0.75rem' }}>
        <h1 className="page-title">Tapis Tokens & Refresh Service</h1>
        <p className="page-description" style={{ marginBottom: '0.75rem' }}>
          Inspect existing ICICLE Tapis JWTs and mint long-lived Access & Refresh Tokens for cluster jobs.
        </p>
      </div>

      <div className="grid-2" style={{ alignItems: 'stretch' }}>
        {/* Left Column: Input & Live Inspection */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', marginBottom: 0 }}>
          <div className="card-header" style={{ marginBottom: '0.75rem' }}>
            <div>
              <h2 className="card-title">1. Input Existing Token</h2>
              <p className="card-subtitle">Paste an active Access or Refresh Token</p>
            </div>
            {decodedInfo && (
              <span
                className={`status-badge ${
                  decodedInfo.isExpired ? 'status-badge' : 'status-badge online'
                }`}
                style={{
                  background: decodedInfo.isExpired ? 'var(--accent-rose-subtle)' : undefined,
                  color: decodedInfo.isExpired ? 'var(--accent-rose)' : undefined,
                }}
              >
                <span className="status-dot" />
                {decodedInfo.isExpired ? 'Expired' : formatTimeRemaining(decodedInfo.expiresInSeconds)}
              </span>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: '0.75rem' }}>
            <textarea
              className="mono-input"
              rows={3}
              placeholder="eyJhbGciOiJSUzI1NiIsImtpZCI6..."
              value={inputJwt}
              onChange={(e) => setInputJwt(e.target.value)}
              style={{ minHeight: '75px' }}
            />
            {inputJwt && (
              <div style={{ textAlign: 'right', marginTop: '0.25rem' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => setInputJwt('')}
                  style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {/* Decoded JWT Metadata */}
          {decodedInfo ? (
            <div
              style={{
                flex: 1,
                background: 'var(--bg-card-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '0.75rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <h3 style={{ fontSize: '0.825rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Decoded Token Metadata
                </h3>
                <div className="grid-2" style={{ gap: '0.5rem' }}>
                  <div className="meta-item">
                    <span className="meta-key">Tenant</span>
                    <span className="meta-val">{decodedInfo.payload['tapis/tenant_id'] || 'icicleai'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-key">Username</span>
                    <span className="meta-val">{decodedInfo.payload['tapis/username'] || decodedInfo.payload.sub || 'N/A'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-key">Token Type</span>
                    <span className="meta-val" style={{ textTransform: 'uppercase' }}>
                      {decodedInfo.payload['tapis/token_type'] || 'access'}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-key">Expires At</span>
                    <span className="meta-val" style={{ fontSize: '0.75rem' }}>{decodedInfo.formattedExpiresAt}</span>
                  </div>
                </div>
              </div>

              <details style={{ marginTop: '0.5rem' }}>
                <summary style={{ cursor: 'pointer', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  View Raw Claims JSON
                </summary>
                <pre
                  style={{
                    marginTop: '0.35rem',
                    fontSize: '0.7rem',
                    fontFamily: 'var(--font-mono)',
                    background: 'var(--bg-card)',
                    padding: '0.5rem',
                    borderRadius: 'var(--radius-sm)',
                    maxHeight: '110px',
                    overflowY: 'auto',
                  }}
                >
                  {JSON.stringify(decodedInfo.payload, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <div
              style={{
                flex: 1,
                border: '1px dashed var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.825rem',
                minHeight: '140px',
              }}
            >
              Paste a token above to see decoded claims live
            </div>
          )}
        </div>

        {/* Right Column: Mint / Refresh Actions & Output */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div className="card" style={{ marginBottom: 0, padding: '1.25rem' }}>
            <div className="card-header" style={{ marginBottom: '0.75rem' }}>
              <div>
                <h2 className="card-title">2. Mint or Refresh Token</h2>
                <p className="card-subtitle">Generate fresh credentials from ICICLE Tapis API</p>
              </div>
            </div>

            <div className="grid-2" style={{ gap: '0.75rem', marginBottom: '0.75rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>Access TTL</label>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button
                    type="button"
                    className={`btn btn-sm ${accessTokenTtl === 14400 ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setAccessTokenTtl(14400)}
                    style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    4h
                  </button>
                  <button
                    type="button"
                    className={`btn btn-sm ${accessTokenTtl === 28800 ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setAccessTokenTtl(28800)}
                    style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    8h
                  </button>
                  <button
                    type="button"
                    className={`btn btn-sm ${accessTokenTtl === 86400 ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setAccessTokenTtl(86400)}
                    style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    24h
                  </button>
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>Refresh TTL</label>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button
                    type="button"
                    className={`btn btn-sm ${refreshTokenTtl === 604800 ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setRefreshTokenTtl(604800)}
                    disabled={!generateRefreshToken}
                    style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    7d
                  </button>
                  <button
                    type="button"
                    className={`btn btn-sm ${refreshTokenTtl === 2592000 ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setRefreshTokenTtl(2592000)}
                    disabled={!generateRefreshToken}
                    style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    30d
                  </button>
                  <button
                    type="button"
                    className={`btn btn-sm ${refreshTokenTtl === 5184000 ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setRefreshTokenTtl(5184000)}
                    disabled={!generateRefreshToken}
                    style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    60d
                  </button>
                </div>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', height: '28px' }}>
                <input
                  type="checkbox"
                  id="generate_refresh_token"
                  checked={generateRefreshToken}
                  onChange={(e) => setGenerateRefreshToken(e.target.checked)}
                  style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                />
                <label htmlFor="generate_refresh_token" style={{ fontSize: '0.8rem', cursor: 'pointer' }}>
                  Generate Long-Lived Refresh Token
                </label>
              </div>
            </div>

            {errorMsg && (
              <div className="alert alert-error" style={{ padding: '0.5rem 0.75rem', fontSize: '0.775rem', marginBottom: '0.5rem' }}>
                {errorMsg}
              </div>
            )}
            {successMsg && (
              <div className="alert alert-success" style={{ padding: '0.5rem 0.75rem', fontSize: '0.775rem', marginBottom: '0.5rem' }}>
                {successMsg}
              </div>
            )}

            <button
              type="button"
              className="btn btn-primary"
              onClick={handleCreateOrRefreshToken}
              disabled={isLoading || !inputJwt.trim()}
              style={{ width: '100%', padding: '0.65rem', fontSize: '0.85rem' }}
            >
              {isLoading ? 'Requesting Tokens...' : 'Generate / Refresh Tapis Token'}
            </button>
          </div>

          {/* Newly Minted Results */}
          {resultAccessToken && (
            <div className="card" style={{ marginBottom: 0, padding: '1rem 1.25rem' }}>
              <div className="card-header" style={{ marginBottom: '0.5rem' }}>
                <h2 className="card-title" style={{ fontSize: '0.95rem' }}>3. Newly Minted Tokens</h2>
                {decodedResultAccess && (
                  <span className="status-badge online" style={{ fontSize: '0.7rem' }}>
                    <span className="status-dot" />
                    {formatTimeRemaining(decodedResultAccess.expiresInSeconds)}
                  </span>
                )}
              </div>

              <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                <div className="code-box-header" style={{ marginBottom: '0.25rem' }}>
                  <label className="form-label" style={{ marginBottom: 0, fontSize: '0.775rem' }}>Access Token (JWT)</label>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleCopy(resultAccessToken, 'access')}
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.725rem' }}
                  >
                    {copiedKey === 'access' ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="code-box" style={{ padding: '0.4rem 0.65rem', maxHeight: '50px', fontSize: '0.75rem' }}>
                  {resultAccessToken}
                </div>
              </div>

              {resultRefreshToken && (
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <div className="code-box-header" style={{ marginBottom: '0.25rem' }}>
                    <label className="form-label" style={{ marginBottom: 0, fontSize: '0.775rem' }}>Refresh Token</label>
                    <button
                      type="button"
                      className="btn btn-sm btn-secondary"
                      onClick={() => handleCopy(resultRefreshToken, 'refresh')}
                      style={{ padding: '0.2rem 0.5rem', fontSize: '0.725rem' }}
                    >
                      {copiedKey === 'refresh' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <div className="code-box" style={{ padding: '0.4rem 0.65rem', maxHeight: '50px', fontSize: '0.75rem' }}>
                    {resultRefreshToken}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
