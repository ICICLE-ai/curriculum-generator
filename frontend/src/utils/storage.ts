const ACCESS_TOKEN_KEY = 'tapis_access_token';
const REFRESH_TOKEN_KEY = 'tapis_refresh_token';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    if (token) {
      localStorage.setItem(ACCESS_TOKEN_KEY, token.trim());
    } else {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
    }
  } catch (err) {
    console.error('Failed to store access token:', err);
  }
}

export function getStoredRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredRefreshToken(token: string): void {
  try {
    if (token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, token.trim());
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  } catch (err) {
    console.error('Failed to store refresh token:', err);
  }
}

export function clearStoredTokens(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch (err) {
    console.error('Failed to clear tokens:', err);
  }
}
