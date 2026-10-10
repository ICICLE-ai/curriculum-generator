import React, { useState, useEffect, useRef } from 'react';
import { parseJwt, formatTimeRemaining, type DecodedTapisJWT } from '../utils/jwt';
import {
  getStoredToken,
  getStoredRefreshToken,
  setStoredToken,
  setStoredRefreshToken,
  clearStoredTokens,
} from '../utils/storage';
import { getTapisApiUrl } from '../services/tapis';
import { UserTokenMenuCard } from './navbar';

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

  const handleLogoutAction = () => {
    clearStoredTokens();
    setIsOpen(false);
    onLogout();
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

      {/* Dropdown Menu Card */}
      {isOpen && (
        <UserTokenMenuCard
          username={username}
          tenant={tenant}
          decodedInfo={decodedInfo}
          isExpired={isExpired}
          accessRemaining={accessRemaining}
          refreshToken={refreshToken}
          refreshRemaining={refreshRemaining}
          statusMessage={statusMessage}
          isGeneratingRefresh={isGeneratingRefresh}
          isRenewingAccess={isRenewingAccess}
          copiedAccess={copiedAccess}
          copiedRefresh={copiedRefresh}
          token={token}
          onGenerateRefreshToken={handleGenerateRefreshToken}
          onRenewAccessToken={handleRenewAccessToken}
          onCopyAccess={handleCopyAccess}
          onCopyRefresh={handleCopyRefresh}
          onLogout={handleLogoutAction}
        />
      )}
    </div>
  );
};
