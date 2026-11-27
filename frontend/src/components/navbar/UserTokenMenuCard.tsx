import React from 'react';
import { KeyRound, RefreshCw, Copy, Check, LogOut } from 'lucide-react';
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
    <div className="token-menu">
      <div className="token-menu-header">
        <div className="token-menu-eyebrow">Active Tapis Identity</div>
        <div className="token-menu-user">{username}</div>
        <div className="token-menu-meta">
          Tenant: <strong>{tenant}</strong> · IDP:{' '}
          <strong>{(decodedInfo?.payload['tapis/idp_id'] as string) || 'globus'}</strong>
        </div>
      </div>

      <div className="stack-sm">
        <div className="row-between">
          <span className="muted">Access Token</span>
          <strong style={{ color: isExpired ? 'var(--danger)' : 'var(--success)', fontSize: 'var(--text-sm)' }}>
            {accessRemaining}
          </strong>
        </div>
        <div className="row-between">
          <span className="muted">Refresh Token</span>
          <strong style={{ color: refreshToken ? 'var(--text)' : 'var(--text-3)', fontSize: 'var(--text-sm)' }}>
            {refreshRemaining || (refreshToken ? 'Active (30d)' : 'Not generated')}
          </strong>
        </div>
      </div>

      {statusMessage && (
        <div className={`alert ${statusMessage.type === 'success' ? 'alert-success' : 'alert-error'}`}>
          {statusMessage.text}
        </div>
      )}

      <div className="stack-sm">
        <button
          type="button"
          className="btn btn-primary btn-sm btn-full"
          onClick={onGenerateRefreshToken}
          disabled={isGeneratingRefresh || !token}
        >
          <KeyRound size={14} aria-hidden="true" />
          <span>{isGeneratingRefresh ? 'Generating Refresh Token...' : 'Generate 30-Day Refresh Token'}</span>
        </button>

        <button
          type="button"
          className="btn btn-secondary btn-sm btn-full"
          onClick={onRenewAccessToken}
          disabled={isRenewingAccess || !refreshToken}
        >
          <RefreshCw size={14} className={isRenewingAccess ? 'spin' : undefined} aria-hidden="true" />
          <span>{isRenewingAccess ? 'Renewing...' : 'Renew Access Token (+4 Hours)'}</span>
        </button>

        <div className="grid-2" style={{ gap: 'var(--space-2)' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onCopyAccess}
            disabled={!token}
          >
            {copiedAccess ? <Check size={13} aria-hidden="true" /> : <Copy size={13} aria-hidden="true" />}
            <span>{copiedAccess ? 'Copied' : 'Copy Access'}</span>
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onCopyRefresh}
            disabled={!refreshToken}
          >
            {copiedRefresh ? <Check size={13} aria-hidden="true" /> : <Copy size={13} aria-hidden="true" />}
            <span>{copiedRefresh ? 'Copied' : 'Copy Refresh'}</span>
          </button>
        </div>
      </div>

      <div className="token-menu-footer">
        <button
          type="button"
          className="btn btn-danger btn-sm btn-full"
          onClick={onLogout}
        >
          <LogOut size={14} aria-hidden="true" />
          <span>Log Out</span>
        </button>
      </div>
    </div>
  );
};
