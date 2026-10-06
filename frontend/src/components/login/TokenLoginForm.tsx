import React from 'react';
import { formatTimeRemaining, type DecodedTapisJWT } from '../../utils/jwt';

interface TokenLoginFormProps {
  tokenInput: string;
  setTokenInput: (val: string) => void;
  decodedInfo: DecodedTapisJWT | null;
  errorMsg: string | null;
  onSubmit: (e: React.FormEvent) => void;
}

export const TokenLoginForm: React.FC<TokenLoginFormProps> = ({
  tokenInput,
  setTokenInput,
  decodedInfo,
  errorMsg,
  onSubmit,
}) => {
  return (
    <form onSubmit={onSubmit}>
      <div style={{ marginBottom: '1.25rem' }}>
        <label
          htmlFor="tapis-token-input"
          style={{
            display: 'block',
            fontSize: '0.85rem',
            fontWeight: 600,
            marginBottom: '0.35rem',
            color: 'var(--text-primary)',
          }}
        >
          Tapis JWT Access Token
        </label>
        <p
          style={{
            fontSize: '0.78rem',
            color: 'var(--text-secondary)',
            marginBottom: '0.6rem',
            lineHeight: 1.4,
          }}
        >
          Sign in via University Accounts (CILogon) on the{' '}
          <a
            href="https://icicleai.tapis.io/#/login"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}
          >
            ICICLE Tapis Portal
          </a>
          , copy your active token, and paste it below.
        </p>
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
            borderColor: errorMsg
              ? 'var(--accent-rose)'
              : decodedInfo?.isValid
              ? 'var(--accent-emerald)'
              : undefined,
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
            User: <strong>{decodedInfo.payload['tapis/username'] || decodedInfo.payload.sub || 'Unknown'}</strong>{' '}
            | Tenant: <strong>{decodedInfo.payload['tapis/tenant_id'] || 'icicleai'}</strong>
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
  );
};
