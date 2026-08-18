import React, { useState, useEffect, useRef } from 'react';
import { parseJwt, formatTimeRemaining, type DecodedTapisJWT } from '../utils/jwt';
import {
  getStoredToken,
  getStoredRefreshToken,
  setStoredToken,
  setStoredRefreshToken,
  clearStoredTokens,
} from '../utils/storage';
import { getTapisApiUrl } from '../utils/tapisJobs';

interface UserTokenDropdownProps {
  onLogout: () => void;
}

export const UserTokenDropdown: React.FC<UserTokenDropdownProps> = ({ onLogout }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [refreshToken, setRefreshToken] = useState<string | null>(getStoredRefreshToken());
  const [decodedInfo, setDecodedInfo] = useState<DecodedTapisJWT | null>(null);
  const [decodedRefresh, setDecodedRefresh] = useState<DecodedTapisJWT | null>(null);

  // Copy states
  const [copiedAccess, setCopiedAccess] = useState<boolean>(false);
  const [copiedRefresh, setCopiedRefresh] = useState<boolean>(false);

  // Action states
  const [isGeneratingRefresh, setIsGeneratingRefresh] = useState<boolean>(false);
  const [isRenewingAccess, setIsRenewingAccess] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const dropdownRef = useRef<HTMLDivElement>(null);

  // Sync token state and decode JWT
  useEffect(() => {
    const updateDecoded = () => {
      const activeAccess = getStoredToken();
      const activeRefresh = getStoredRefreshToken();

      setToken(activeAccess);
      setRefreshToken(activeRefresh);

      if (activeAccess) {
        setDecodedInfo(parseJwt(activeAccess));
      } else {
        setDecodedInfo(null);
      }

      if (activeRefresh) {
        setDecodedRefresh(parseJwt(activeRefresh));
      } else {
        setDecodedRefresh(null);
      }
    };

    updateDecoded();
    const interval = setInterval(updateDecoded, 15000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const showFeedback = (text: string, type: 'success' | 'error' = 'success') => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 3500);
  };

  const handleCopyAccess = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopiedAccess(true);
      setTimeout(() => setCopiedAccess(false), 2000);
    }
  };

  const handleCopyRefresh = () => {
    if (refreshToken) {
      navigator.clipboard.writeText(refreshToken);
      setCopiedRefresh(true);
      setTimeout(() => setCopiedRefresh(false), 2000);
    }
  };

  /**
   * 1-Click Generate Refresh Token using the user's active JWT in headers
   */
  const handleGenerateRefreshToken = async () => {
    if (!token) {
      showFeedback('No active access token found.', 'error');
      return;
    }

    setIsGeneratingRefresh(true);
    setStatusMessage(null);

    try {
      const requestUrl = getTapisApiUrl('/v3/tokens');

      const username = decodedInfo?.payload['tapis/username'] || decodedInfo?.payload.sub;
      const tenantId = (decodedInfo?.payload['tapis/tenant_id'] as string) || 'icicleai';

      const payload = {
        token_tenant_id: tenantId,
        token_username: username,
        account_type: 'user',
        access_token_ttl: 14400, // 4 hours
        refresh_token_ttl: 2592000, // 30 days
        generate_refresh_token: true,
      };

      const resp = await fetch(requestUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tapis-Token': token.trim(),
        },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const errText = await resp.text();
        throw new Error(`Generation failed (${resp.status}): ${errText}`);
      }

      const resJson = await resp.json();
      const result = resJson?.result;
      const newAccess = result?.access_token?.access_token || result?.access_token;
      const newRefresh = result?.refresh_token?.refresh_token || result?.refresh_token;

      if (newRefresh) {
        setStoredRefreshToken(newRefresh);
        setRefreshToken(newRefresh);
        setDecodedRefresh(parseJwt(newRefresh));
      }

      if (newAccess) {
        setStoredToken(newAccess);
        setToken(newAccess);
        setDecodedInfo(parseJwt(newAccess));
      }

      showFeedback('Generated and stored 30-day Refresh Token!', 'success');
    } catch (err) {
      showFeedback(err instanceof Error ? err.message : 'Failed to generate refresh token', 'error');
    } finally {
      setIsGeneratingRefresh(false);
    }
  };

  /**
   * Renew Access Token using stored Refresh Token
   */
  const handleRenewAccessToken = async () => {
    const activeRefresh = getStoredRefreshToken();
    if (!activeRefresh) {
      showFeedback('No stored refresh token. Click "Generate Refresh Token" first.', 'error');
      return;
    }

    setIsRenewingAccess(true);
    setStatusMessage(null);

    try {
      const requestUrl = getTapisApiUrl('/v3/tokens');

      const resp = await fetch(requestUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          refresh_token: activeRefresh,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Token renewal failed (${resp.status})`);
      }

      const data = await resp.json();
      const newAccess = data?.result?.access_token?.access_token || data?.result?.access_token;
      if (newAccess) {
        setStoredToken(newAccess);
        setToken(newAccess);
        setDecodedInfo(parseJwt(newAccess));
        showFeedback('Access token renewed (+4 hours)!', 'success');
      }
    } catch (err) {
      showFeedback(err instanceof Error ? err.message : 'Renewal failed', 'error');
    } finally {
      setIsRenewingAccess(false);
    }
  };

  const username =
    decodedInfo?.payload['tapis/username'] ||
    decodedInfo?.payload.sub ||
    'Authenticated User';

  const tenant = (decodedInfo?.payload['tapis/tenant_id'] as string) || 'icicleai';
  const isExpired = decodedInfo?.isExpired ?? false;
  const accessRemaining = decodedInfo ? formatTimeRemaining(decodedInfo.expiresInSeconds) : 'No token';
  const refreshRemaining = decodedRefresh ? formatTimeRemaining(decodedRefresh.expiresInSeconds) : null;

  return (
    <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-block' }}>
      {/* Navbar Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.45rem 0.85rem',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-card-subtle)',
          border: '1px solid var(--border-strong)',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          fontSize: '0.82rem',
          fontWeight: 600,
          transition: 'all 0.15s ease',
        }}
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: isExpired ? 'var(--accent-rose)' : 'var(--accent-emerald)',
            display: 'inline-block',
          }}
        />
        <span>{username}</span>
        <span
          style={{
            fontSize: '0.72rem',
            padding: '0.15rem 0.4rem',
            borderRadius: 'var(--radius-sm)',
            background: isExpired ? 'var(--accent-rose-subtle)' : 'var(--accent-primary-subtle)',
            color: isExpired ? 'var(--accent-rose)' : 'var(--accent-primary)',
            fontWeight: 600,
          }}
        >
          {accessRemaining}
        </span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.15s ease',
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
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
          <div style={{ paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
              Active Tapis Identity
            </div>
            <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem', wordBreak: 'break-all' }}>
              {username}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
              Tenant: <strong>{tenant}</strong> | IDP: <strong>{(decodedInfo?.payload['tapis/idp_id'] as string) || 'globus'}</strong>
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
                background: statusMessage.type === 'success' ? 'var(--accent-emerald-subtle)' : 'var(--accent-rose-subtle)',
                color: statusMessage.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                border: `1px solid ${statusMessage.type === 'success' ? 'var(--accent-emerald-border)' : 'var(--accent-rose)'}`,
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
              onClick={handleGenerateRefreshToken}
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
              onClick={handleRenewAccessToken}
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
                onClick={handleCopyAccess}
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
                onClick={handleCopyRefresh}
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
              onClick={() => {
                clearStoredTokens();
                setIsOpen(false);
                onLogout();
              }}
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
      )}
    </div>
  );
};
