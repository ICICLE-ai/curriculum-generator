export interface DecodedTapisJWT {
  raw: string;
  header: Record<string, unknown>;
  payload: {
    jti?: string;
    iss?: string;
    sub?: string;
    exp?: number;
    nbf?: number;
    iat?: number;
    'tapis/tenant_id'?: string;
    'tapis/token_type'?: 'access' | 'refresh' | string;
    'tapis/delegation'?: boolean;
    'tapis/delegation_sub'?: string | null;
    'tapis/username'?: string;
    'tapis/account_type'?: string;
    'tapis/client_id'?: string;
    'tapis/grant_type'?: string;
    'tapis/idp_id'?: string;
    [key: string]: unknown;
  };
  isValid: boolean;
  isExpired: boolean;
  expiresInSeconds: number;
  formattedExpiresAt: string;
  formattedIssuedAt?: string;
}

export function parseJwt(token: string): DecodedTapisJWT | null {
  const trimmed = token.trim();
  if (!trimmed) return null;

  try {
    const parts = trimmed.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const decodeBase64Url = (str: string) => {
      const base64 = str.replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
      return decodeURIComponent(
        atob(padded)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
    };

    const header = JSON.parse(decodeBase64Url(parts[0]));
    const payload = JSON.parse(decodeBase64Url(parts[1]));

    const now = Math.floor(Date.now() / 1000);
    const exp = payload.exp || 0;
    const isExpired = exp > 0 && exp <= now;
    const expiresInSeconds = exp > 0 ? exp - now : 0;

    const formattedExpiresAt = exp > 0 ? new Date(exp * 1000).toLocaleString() : 'Never / Unknown';
    const formattedIssuedAt = payload.iat ? new Date(payload.iat * 1000).toLocaleString() : undefined;

    return {
      raw: trimmed,
      header,
      payload,
      isValid: true,
      isExpired,
      expiresInSeconds,
      formattedExpiresAt,
      formattedIssuedAt,
    };
  } catch {
    return null;
  }
}

export function formatTimeRemaining(seconds: number): string {
  if (seconds <= 0) return 'Expired';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h remaining`;
  if (hours > 0) return `${hours}h ${minutes}m remaining`;
  return `${minutes}m remaining`;
}
