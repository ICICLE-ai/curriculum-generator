import React from 'react';
import type { DecodedTapisJWT } from '../../utils/jwt';

interface UserTokenMenuCardProps {
  username: string;
  tenant: string;
  decodedInfo: DecodedTapisJWT | null;
  isExpired: boolean;
  accessRemaining: string;
  refreshToken: string | null;
  refreshRemaining: string | null;
  statusMessage: { text: string; type: 'success' | 'error' } | null;
  isGeneratingRefresh: boolean;
  isRenewingAccess: boolean;
  copiedAccess: boolean;
  copiedRefresh: boolean;
  token: string | null;
  onGenerateRefreshToken: () => void;
  onRenewAccessToken: () => void;
  onCopyAccess: () => void;
  onCopyRefresh: () => void;
  onLogout: () => void;
}

export const UserTokenMenuCard: React.FC<UserTokenMenuCardProps> = ({
  username,
  tenant,
  decodedInfo,
  isExpired,
  accessRemaining,
  refreshToken,
  refreshRemaining,
  statusMessage,
  isGeneratingRefresh,
  isRenewingAccess,
  copiedAccess,
  copiedRefresh,
  token,
  onGenerateRefreshToken,
  onRenewAccessToken,
  onCopyAccess,
  onCopyRefresh,
  onLogout,
}) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: 'calc(100% + 8px)',
        right: 0,
        width: '350px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-strong)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        padding: '1.25rem',
        zIndex: 1000,
      }}
    >
      {/* Header */}
      <div
        style={{
          paddingBottom: '0.75rem',
          borderBottom: '1px solid var(--border-subtle)',
          marginBottom: '0.75rem',
        }}
      >
        <div
          style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            fontWeight: 700,
          }}
        >
          Active Tapis Identity
        </div>
        <div
          style={{
            fontSize: '0.9rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginTop: '0.2rem',
            wordBreak: 'break-all',
          }}
        >
          {username}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
          Tenant: <strong>{tenant}</strong> | IDP:{' '}
          <strong>{(decodedInfo?.payload['tapis/idp_id'] as string) || 'globus'}</strong>
        </div>
      </div>

      {/* Token Lifespans */}
      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.85rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
          <span>Access Token:</span>
          <strong style={{ color: isExpired ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
            {accessRemaining}
          </strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Refresh Token:</span>
          <strong style={{ color: refreshToken ? 'var(--text-primary)' : 'var(--text-muted)' }}>
            {refreshRemaining || (refreshToken ? 'Active (30d)' : 'Not generated')}
          </strong>
        </div>
      </div>

      {/* Feedback message banner */}
      {statusMessage && (
        <div
          style={{
            padding: '0.45rem 0.65rem',
            borderRadius: 'var(--radius-sm)',
            background:
              statusMessage.type === 'success'
                ? 'var(--accent-emerald-subtle)'
                : 'var(--accent-rose-subtle)',
            color:
              statusMessage.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
            border: `1px solid ${
              statusMessage.type === 'success'
                ? 'var(--accent-emerald-border)'
                : 'var(--accent-rose)'
            }`,
            fontSize: '0.75rem',
            marginBottom: '0.75rem',
            textAlign: 'center',
          }}
        >
          {statusMessage.text}
        </div>
      )}

      {/* Direct Actions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', marginBottom: '0.85rem' }}>
        {/* Generate Refresh Token using JWT */}
        <button
          type="button"
          className="btn btn-primary"
          onClick={onGenerateRefreshToken}
          disabled={isGeneratingRefresh || !token}
          style={{ fontSize: '0.8rem', padding: '0.45rem', justifyContent: 'center' }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ animation: isGeneratingRefresh ? 'spin 1s linear infinite' : 'none' }}
          >
            <path d="M21 2l-2 2m-1-1l-3 3M3 13h1m3-3h1m3-3h1m5 5l2 2" />
            <path d="M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18z" />
          </svg>
          {isGeneratingRefresh ? 'Generating Refresh Token...' : 'Generate 30-Day Refresh Token'}
        </button>

        {/* Renew Access Token using stored Refresh Token */}
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onRenewAccessToken}
          disabled={isRenewingAccess || !refreshToken}
          style={{ fontSize: '0.8rem', padding: '0.45rem', justifyContent: 'center' }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ animation: isRenewingAccess ? 'spin 1s linear infinite' : 'none' }}
          >
            <path d="M23 4v6h-6" />
            <path d="M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          {isRenewingAccess ? 'Renewing...' : 'Renew Access Token (+4 Hours)'}
        </button>

        {/* Copy Button Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', marginTop: '0.2rem' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCopyAccess}
            disabled={!token}
            style={{ fontSize: '0.78rem', padding: '0.4rem', justifyContent: 'center' }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            {copiedAccess ? 'Copied!' : 'Copy Access'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCopyRefresh}
            disabled={!refreshToken}
            style={{ fontSize: '0.78rem', padding: '0.4rem', justifyContent: 'center' }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            {copiedRefresh ? 'Copied!' : 'Copy Refresh'}
          </button>
        </div>
      </div>

      {/* Logout Action */}
      <div style={{ paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)' }}>
        <button
          type="button"
          onClick={onLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.4rem',
            padding: '0.45rem',
            width: '100%',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            background: 'var(--bg-card-subtle)',
            color: 'var(--accent-rose)',
            cursor: 'pointer',
            fontSize: '0.78rem',
            fontWeight: 600,
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Log Out
        </button>
      </div>
    </div>
  );
};
