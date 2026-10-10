import React from 'react';
import { formatTimeRemaining, type DecodedTapisJWT } from '../../utils/jwt';

interface TokenMintFormProps {
  accessTokenTtl: number;
  setAccessTokenTtl: (val: number) => void;
  refreshTokenTtl: number;
  setRefreshTokenTtl: (val: number) => void;
  generateRefreshToken: boolean;
  setGenerateRefreshToken: (val: boolean) => void;
  isLoading: boolean;
  inputJwt: string;
  errorMsg: string | null;
  successMsg: string | null;
  onSubmit: () => void;
  resultAccessToken: string | null;
  resultRefreshToken: string | null;
  decodedResultAccess: DecodedTapisJWT | null;
  copiedKey: string | null;
  onCopy: (text: string, key: string) => void;
}

export const TokenMintForm: React.FC<TokenMintFormProps> = ({
  accessTokenTtl,
  setAccessTokenTtl,
  refreshTokenTtl,
  setRefreshTokenTtl,
  generateRefreshToken,
  setGenerateRefreshToken,
  isLoading,
  inputJwt,
  errorMsg,
  successMsg,
  onSubmit,
  resultAccessToken,
  resultRefreshToken,
  decodedResultAccess,
  copiedKey,
  onCopy,
}) => {
  return (
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
            <label className="form-label" style={{ fontSize: '0.8rem' }}>
              Access TTL
            </label>
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
            <label className="form-label" style={{ fontSize: '0.8rem' }}>
              Refresh TTL
            </label>
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
          <div
            className="alert alert-error"
            style={{ padding: '0.5rem 0.75rem', fontSize: '0.775rem', marginBottom: '0.5rem' }}
          >
            {errorMsg}
          </div>
        )}
        {successMsg && (
          <div
            className="alert alert-success"
            style={{ padding: '0.5rem 0.75rem', fontSize: '0.775rem', marginBottom: '0.5rem' }}
          >
            {successMsg}
          </div>
        )}

        <button
          type="button"
          className="btn btn-primary"
          onClick={onSubmit}
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
            <h2 className="card-title" style={{ fontSize: '0.95rem' }}>
              3. Newly Minted Tokens
            </h2>
            {decodedResultAccess && (
              <span className="status-badge online" style={{ fontSize: '0.7rem' }}>
                <span className="status-dot" />
                {formatTimeRemaining(decodedResultAccess.expiresInSeconds)}
              </span>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: '0.5rem' }}>
            <div className="code-box-header" style={{ marginBottom: '0.25rem' }}>
              <label className="form-label" style={{ marginBottom: 0, fontSize: '0.775rem' }}>
                Access Token (JWT)
              </label>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => onCopy(resultAccessToken, 'access')}
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
                <label className="form-label" style={{ marginBottom: 0, fontSize: '0.775rem' }}>
                  Refresh Token
                </label>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => onCopy(resultRefreshToken, 'refresh')}
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
  );
};
