import React, { useState, useEffect } from 'react';
import { parseJwt, type DecodedTapisJWT } from '../utils/jwt';
import { TokenInputInspector, TokenMintForm } from './token';

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
        <TokenInputInspector
          inputJwt={inputJwt}
          setInputJwt={setInputJwt}
          decodedInfo={decodedInfo}
        />

        {/* Right Column: Mint / Refresh Actions & Output */}
        <TokenMintForm
          accessTokenTtl={accessTokenTtl}
          setAccessTokenTtl={setAccessTokenTtl}
          refreshTokenTtl={refreshTokenTtl}
          setRefreshTokenTtl={setRefreshTokenTtl}
          generateRefreshToken={generateRefreshToken}
          setGenerateRefreshToken={setGenerateRefreshToken}
          isLoading={isLoading}
          inputJwt={inputJwt}
          errorMsg={errorMsg}
          successMsg={successMsg}
          onSubmit={handleCreateOrRefreshToken}
          resultAccessToken={resultAccessToken}
          resultRefreshToken={resultRefreshToken}
          decodedResultAccess={decodedResultAccess}
          copiedKey={copiedKey}
          onCopy={handleCopy}
        />
      </div>
    </div>
  );
};
