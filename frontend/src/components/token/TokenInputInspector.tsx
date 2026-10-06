import React from 'react';
import { formatTimeRemaining, type DecodedTapisJWT } from '../../utils/jwt';

interface TokenInputInspectorProps {
  inputJwt: string;
  setInputJwt: (val: string) => void;
  decodedInfo: DecodedTapisJWT | null;
}

export const TokenInputInspector: React.FC<TokenInputInspectorProps> = ({
  inputJwt,
  setInputJwt,
  decodedInfo,
}) => {
  return (
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
                <span className="meta-val">
                  {decodedInfo.payload['tapis/username'] || decodedInfo.payload.sub || 'N/A'}
                </span>
              </div>
              <div className="meta-item">
                <span className="meta-key">Token Type</span>
                <span className="meta-val" style={{ textTransform: 'uppercase' }}>
                  {decodedInfo.payload['tapis/token_type'] || 'access'}
                </span>
              </div>
              <div className="meta-item">
                <span className="meta-key">Expires At</span>
                <span className="meta-val" style={{ fontSize: '0.75rem' }}>
                  {decodedInfo.formattedExpiresAt}
                </span>
              </div>
            </div>
          </div>

          <details style={{ marginTop: '0.5rem' }}>
            <summary
              style={{
                cursor: 'pointer',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
              }}
            >
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
  );
};
