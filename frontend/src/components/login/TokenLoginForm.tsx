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
  const inputClass = errorMsg
    ? 'mono-input input-error'
    : decodedInfo?.isValid
    ? 'mono-input input-success'
    : 'mono-input';

  return (
    <form onSubmit={onSubmit} className="stack">
      <div className="form-group">
        <label htmlFor="tapis-token-input" className="form-label">
          Tapis Access Token
        </label>
        <p className="muted" style={{ marginBottom: 'var(--space-2)' }}>
          Sign in via University Accounts (CILogon) on the{' '}
          <a
            href="https://icicleai.tapis.io/#/login"
            target="_blank"
            rel="noopener noreferrer"
            className="link-btn"
          >
            ICICLE Tapis Portal
          </a>
          , copy your active token, and paste it below.
        </p>
        <textarea
          id="tapis-token-input"
          rows={4}
          className={inputClass}
          placeholder="Paste your active eyJhbGci... Tapis access token"
          value={tokenInput}
          onChange={(e) => setTokenInput(e.target.value)}
        />
      </div>

      {decodedInfo && decodedInfo.isValid && !decodedInfo.isExpired && (
        <div className="alert alert-success alert-col">
          <div className="row-between">
            <strong>Valid Tapis Session</strong>
            <strong>{formatTimeRemaining(decodedInfo.expiresInSeconds)}</strong>
          </div>
          <div>
            User: <strong>{decodedInfo.payload['tapis/username'] || decodedInfo.payload.sub || 'Unknown'}</strong>
            {' · '}
            Tenant: <strong>{(decodedInfo.payload['tapis/tenant_id'] as string) || 'icicleai'}</strong>
          </div>
        </div>
      )}

      {errorMsg && (
        <div role="alert" className="alert alert-error">
          {errorMsg}
        </div>
      )}

      <button
        type="submit"
        className="btn btn-primary btn-full"
        disabled={!tokenInput.trim() || !!errorMsg}
      >
        Connect to Portal
      </button>
    </form>
  );
};
