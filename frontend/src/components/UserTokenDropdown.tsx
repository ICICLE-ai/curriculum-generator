import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';
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

  const [copiedAccess, setCopiedAccess] = useState<boolean>(false);
  const [copiedRefresh, setCopiedRefresh] = useState<boolean>(false);

  const [isGeneratingRefresh, setIsGeneratingRefresh] = useState<boolean>(false);
  const [isRenewingAccess, setIsRenewingAccess] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateDecoded = () => {
      const activeAccess = getStoredToken();
      const activeRefresh = getStoredRefreshToken();

      setToken(activeAccess);
      setRefreshToken(activeRefresh);
      setDecodedInfo(activeAccess ? parseJwt(activeAccess) : null);
      setDecodedRefresh(activeRefresh ? parseJwt(activeRefresh) : null);
    };

    updateDecoded();
    const interval = setInterval(updateDecoded, 15000);
    return () => clearInterval(interval);
  }, []);

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

      const resp = await fetch(requestUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tapis-Token': token.trim(),
        },
        body: JSON.stringify({
          token_tenant_id: tenantId,
          token_username: username,
          account_type: 'user',
          access_token_ttl: 14400,
          refresh_token_ttl: 2592000,
          generate_refresh_token: true,
        }),
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

      showFeedback('Generated and stored 30-day refresh token', 'success');
    } catch (err) {
      showFeedback(err instanceof Error ? err.message : 'Failed to generate refresh token', 'error');
    } finally {
      setIsGeneratingRefresh(false);
    }
  };

  const handleRenewAccessToken = async () => {
    const activeRefresh = getStoredRefreshToken();
    if (!activeRefresh) {
      showFeedback('No stored refresh token. Generate one first.', 'error');
      return;
    }

    setIsRenewingAccess(true);
    setStatusMessage(null);

    try {
      const resp = await fetch(getTapisApiUrl('/v3/tokens'), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: activeRefresh }),
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
        showFeedback('Access token renewed (+4 hours)', 'success');
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
    <div ref={dropdownRef} className="token-dropdown">
      <button
        type="button"
        className="token-trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className={`token-dot ${isExpired ? 'is-expired' : ''}`} aria-hidden="true" />
        <span>{username}</span>
        <span className={`token-ttl-pill ${isExpired ? 'is-expired' : ''}`}>
          {accessRemaining}
        </span>
        <ChevronDown
          size={14}
          aria-hidden="true"
          style={{ transform: isOpen ? 'rotate(180deg)' : undefined, transition: 'transform 150ms ease' }}
        />
      </button>

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
